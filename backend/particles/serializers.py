from rest_framework import serializers
from django.db import transaction, IntegrityError
from .models import PartiallyPickedAssembly, PartiallyPickedProduct


class PartiallyPickedProductSerializer(serializers.ModelSerializer):
    """Сериализатор для несобранных товаров"""

    class Meta:
        model = PartiallyPickedProduct
        fields = [
            'id', 'lm_code', 'department_id', 'title',
            'image_url', 'quantity', 'collected_quantity',
            'missing_quantity', 'source', 'is_critical',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['missing_quantity', 'is_critical', 'created_at', 'updated_at']


class PartiallyPickedAssemblySerializer(serializers.ModelSerializer):
    """Сериализатор для сборок с вложенными товарами"""

    products = PartiallyPickedProductSerializer(many=True, read_only=True)
    assembler_short = serializers.SerializerMethodField()

    class Meta:
        model = PartiallyPickedAssembly
        fields = [
            'id', 'order_number', 'task_id', 'status_str',
            'assembly_zone', 'assembler', 'assembler_short',
            'timestamp', 'source_system', 'products_count',
            'total_missing_quantity', 'created_at', 'updated_at', 'products'
        ]
        read_only_fields = [
            'products_count', 'total_missing_quantity',
            'created_at', 'updated_at', 'products'
        ]

    def get_assembler_short(self, obj):
        if obj.assembler:
            parts = obj.assembler.split()
            return parts[-1] if parts else obj.assembler
        return ""


class PartiallyPickedAssemblyCreateSerializer(serializers.Serializer):
    """Сериализатор для создания записей с проверкой дубликатов"""

    timestamp = serializers.DateTimeField(required=True)
    assemblies_count = serializers.IntegerField(required=True)
    assemblies = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
    system_info = serializers.DictField(required=False)

    def create_or_update_assembly(self, assembly_data, timestamp, system_info):
        """Создает или обновляет сборку (upsert)"""
        order_number = assembly_data.get('order', '')
        task_id = assembly_data.get('taskId', '')

        # Ищем существующую сборку
        try:
            assembly = PartiallyPickedAssembly.objects.get(
                order_number=order_number,
                task_id=task_id
            )
            # Обновляем поля, если сборка уже существует
            assembly.status_str = assembly_data.get('status_str', assembly.status_str)
            assembly.assembly_zone = assembly_data.get('assembly_zone', assembly.assembly_zone)
            assembly.assembler = assembly_data.get('assembler', assembly.assembler)
            assembly.timestamp = timestamp
            assembly.save()
            return assembly, False  # False = не новая сборка

        except PartiallyPickedAssembly.DoesNotExist:
            # Создаем новую сборку
            assembly = PartiallyPickedAssembly.objects.create(
                order_number=order_number,
                task_id=task_id,
                status_str=assembly_data.get('status_str', 'PARTIALLY_PICKED'),
                assembly_zone=assembly_data.get('assembly_zone'),
                assembler=assembly_data.get('assembler'),
                timestamp=timestamp,
                source_system=system_info.get('database', 'assembly_tracker')
            )
            return assembly, True  # True = новая сборка

    def create_or_update_product(self, assembly, product_data):
        """Создает или пропускает товар если он уже существует"""
        try:
            # Пробуем найти существующий товар
            product = PartiallyPickedProduct.objects.get(
                assembly=assembly,
                lm_code=product_data.get('lmCode', ''),
                quantity=product_data.get('quantity', 0),
                collected_quantity=product_data.get('collected_quantity', 0)
            )
            # Если нашли - обновляем остальные поля
            product.title = product_data.get('title', product.title)
            product.department_id = product_data.get('departmentId', product.department_id)
            product.image_url = product_data.get('image', product.image_url)
            product.source = product_data.get('source', product.source)
            product.save()
            return product, False  # False = не новый товар

        except PartiallyPickedProduct.DoesNotExist:
            # Создаем новый товар
            product = PartiallyPickedProduct.objects.create(
                assembly=assembly,
                lm_code=product_data.get('lmCode', ''),
                department_id=product_data.get('departmentId'),
                title=product_data.get('title'),
                image_url=product_data.get('image'),
                quantity=product_data.get('quantity', 0),
                collected_quantity=product_data.get('collected_quantity', 0),
                missing_quantity=product_data.get('missing_quantity', 0),
                source=product_data.get('source')
            )
            return product, True  # True = новый товар

    def create(self, validated_data):
        """Создает записи с проверкой дубликатов"""
        assemblies = validated_data['assemblies']
        timestamp = validated_data['timestamp']
        system_info = validated_data.get('system_info', {})

        created_assemblies = 0
        created_products = 0
        updated_assemblies = 0
        updated_products = 0
        skipped_products = 0

        with transaction.atomic():
            for assembly_data in assemblies:
                try:
                    # Создаем или обновляем сборку
                    assembly, is_new_assembly = self.create_or_update_assembly(
                        assembly_data, timestamp, system_info
                    )

                    if is_new_assembly:
                        created_assemblies += 1
                    else:
                        updated_assemblies += 1

                    # Обрабатываем товары
                    products_data = assembly_data.get('products', [])
                    for product_data in products_data:
                        try:
                            product, is_new_product = self.create_or_update_product(
                                assembly, product_data
                            )

                            if is_new_product:
                                created_products += 1
                            else:
                                updated_products += 1

                        except IntegrityError:
                            # Если все же возникла ошибка уникальности - пропускаем
                            skipped_products += 1
                            continue

                except IntegrityError as e:
                    # Пропускаем сборку с ошибкой уникальности
                    print(f"Ошибка при обработке сборки {assembly_data.get('order')}: {e}")
                    continue
                except Exception as e:
                    print(f"Ошибка при обработке сборки {assembly_data.get('order')}: {e}")
                    continue

        return {
            'success': True,
            'stats': {
                'assemblies': {
                    'created': created_assemblies,
                    'updated': updated_assemblies,
                    'total_processed': len(assemblies)
                },
                'products': {
                    'created': created_products,
                    'updated': updated_products,
                    'skipped': skipped_products
                }
            }
        }