from pprint import pprint

import pandas as pd
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView
from loguru import logger
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PartiallyPickedAssembly, PartiallyPickedProduct
from .serializers import (
    PartiallyPickedAssemblyCreateSerializer,
)


class ReceivePartiallyPickedAssembliesView(APIView):
    """
    Простой эндпоинт для приема данных о частично собранных сборках
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Принимает данные о частично собранных сборках и сохраняет их в БД
        """
        serializer = PartiallyPickedAssemblyCreateSerializer(data=request.data)

        if serializer.is_valid():
            result = serializer.save()

            # Извлекаем данные из новой структуры с 'stats'
            stats = result.get('stats', {})
            assemblies_stats = stats.get('assemblies', {})
            products_stats = stats.get('products', {})

            created_assemblies = assemblies_stats.get('created', 0)
            updated_assemblies = assemblies_stats.get('updated', 0)
            created_products = products_stats.get('created', 0)
            updated_products = products_stats.get('updated', 0)

            total_assemblies = created_assemblies + updated_assemblies
            total_products = created_products + updated_products

            # Логируем результат
            logger.info(
                f"Приняты данные о частично собранных сборках: "
                f"создано сборок: {created_assemblies}, "
                f"обновлено сборок: {updated_assemblies}, "
                f"создано товаров: {created_products}, "
                f"обновлено товаров: {updated_products}"
            )

            return Response({
                'status': 'success',
                'message': (
                    f'Обработано {total_assemblies} сборок '
                    f'({created_assemblies} новых, {updated_assemblies} обновлено), '
                    f'{total_products} товаров '
                    f'({created_products} новых, {updated_products} обновлено)'
                ),
                'stats': {
                    'assemblies': {
                        'created': created_assemblies,
                        'updated': updated_assemblies,
                        'total': total_assemblies,
                        'total_received': assemblies_stats.get('total_processed', 0)
                    },
                    'products': {
                        'created': created_products,
                        'updated': updated_products,
                        'total': total_products,
                        'skipped': products_stats.get('skipped', 0)
                    }
                }
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ParticlesTable(LoginRequiredMixin, TemplateView):
    template_name = "particles.html"
    login_url = "home:login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.request.user.username

        # Получаем параметры фильтрации из запроса
        assembler = self.request.GET.get('assembler')
        order_number = self.request.GET.get('order_number')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        department_id = self.request.GET.get('department_id')
        assembly_zone = self.request.GET.get('assembly_zone')  # НОВЫЙ ПАРАМЕТР: зона сборки

        # Получаем сборки с связанными товарами (optimized query)
        assemblies = PartiallyPickedAssembly.objects.prefetch_related('products').all()

        # Применяем фильтры
        if assembler:
            assemblies = assemblies.filter(assembler__icontains=assembler)

        if order_number:
            assemblies = assemblies.filter(order_number=order_number)

        if date_from:
            assemblies = assemblies.filter(timestamp__date__gte=date_from)

        if date_to:
            assemblies = assemblies.filter(timestamp__date__lte=date_to)

        if department_id:
            assemblies = assemblies.filter(products__department_id=department_id).distinct()

        # НОВЫЙ ФИЛЬТР: по зоне сборки
        if assembly_zone:
            assemblies = assemblies.filter(assembly_zone__icontains=assembly_zone)

        # Создаем плоский список для таблицы
        table_data = []
        for assembly in assemblies.order_by("-created_at", "order_number", "task_id"):
            products = assembly.products.all()

            # Если есть фильтр по отделу - фильтруем продукты тоже
            if department_id:
                products = products.filter(department_id=department_id)

            if products.exists():
                # Если есть товары - создаем строку для каждого
                for product in products:
                    table_data.append({
                        'assembly': assembly,
                        'product': product,
                        'is_first_product': True,
                    })
            else:
                # Если нет товаров - все равно показываем сборку
                if not department_id:
                    table_data.append({
                        'assembly': assembly,
                        'product': None,
                        'is_first_product': True,
                    })

        context['table_data'] = table_data
        context['total_rows'] = len(table_data)
        context['total_assemblies'] = assemblies.count()

        # Статистика для фильтров
        context['unique_assemblers'] = assemblies.values('assembler').distinct()
        context['unique_zones'] = assemblies.values('assembly_zone').distinct().order_by('assembly_zone')
        context['unique_departments'] = PartiallyPickedProduct.objects.values('department_id').exclude(
            department_id__isnull=True
        ).exclude(department_id='').distinct().order_by('department_id')

        # Параметры фильтров для отображения
        context['filter_assembler'] = assembler
        context['filter_order'] = order_number
        context['filter_date_from'] = date_from
        context['filter_date_to'] = date_to
        context['filter_department'] = department_id
        context['filter_zone'] = assembly_zone

        return context


class AssemblyDetailView(LoginRequiredMixin, TemplateView):
    template_name = "assembly_detail.html"
    login_url = "home:login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.request.user.username

        assembly_id = self.kwargs.get('pk')

        try:
            assembly = PartiallyPickedAssembly.objects.prefetch_related('products').get(id=assembly_id)
            context['assembly'] = assembly

            # Статистика по товарам
            products = assembly.products.all()
            context['products'] = products
            context['critical_products'] = products.filter(is_critical=True)
            context['total_missing'] = sum(p.missing_quantity for p in products)

        except PartiallyPickedAssembly.DoesNotExist:
            context['error'] = "Сборка не найдена"

        return context


def export_assemblies_to_excel(request):
    """Экспорт в Excel с использованием pandas"""

    # Получаем и фильтруем данные аналогично
    assembler = request.GET.get('assembler', '')
    order_number = request.GET.get('order_number', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    queryset = PartiallyPickedAssembly.objects.all()

    if assembler:
        queryset = queryset.filter(assembler=assembler)

    if order_number:
        queryset = queryset.filter(order_number__icontains=order_number)

    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)

    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    # Подготовка данных
    data = []
    for assembly in queryset:
        products = assembly.products.all()

        if products.exists():
            for product in products:
                data.append({
                    '№': len(data) + 1,
                    'Номер заказа': assembly.order_number,
                    'ID задачи': assembly.task_id,
                    'Зона сборки': assembly.assembly_zone or '-',
                    'Сборщик': assembly.assembler or 'Не указан',
                    'Дата создания': assembly.created_at.strftime('%d.%m.%Y'),
                    'Время создания': assembly.created_at.strftime('%H:%M'),
                    'LM код': product.lm_code or '-',
                    'Отдел': product.department_id or '-',
                    'Название товара': product.title or 'Без названия',
                    'Не хватает': product.missing_quantity or 0,
                    'Статус': assembly.status_str,
                    'Количество товаров': products.count()
                })
        else:
            data.append({
                '№': len(data) + 1,
                'Номер заказа': assembly.order_number,
                'ID задачи': assembly.task_id,
                'Зона сборки': assembly.assembly_zone or '-',
                'Сборщик': assembly.assembler or 'Не указан',
                'Дата создания': assembly.created_at.strftime('%d.%m.%Y'),
                'Время создания': assembly.created_at.strftime('%H:%M'),
                'LM код': '-',
                'Отдел': '-',
                'Название товара': 'Нет товаров',
                'Не хватает': 0,
                'Статус': assembly.status_str,
                'Количество товаров': 0
            })

    # Создаем DataFrame
    df = pd.DataFrame(data)

    # Создаем HttpResponse с Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response[
        'Content-Disposition'] = f'attachment; filename=assemblies_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    # Записываем в Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Сборки', index=False)

        # Настраиваем ширину колонок (опционально)
        worksheet = writer.sheets['Сборки']
        for column in df:
            column_width = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_width + 2, 50)

    return response
