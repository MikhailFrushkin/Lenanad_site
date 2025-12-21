from django.db.models import Count
from .models import PartiallyPickedAssembly, PartiallyPickedProduct


def find_duplicate_assemblies():
    """Находит дублирующиеся сборки (до применения уникального constraint)"""
    duplicates = PartiallyPickedAssembly.objects.values(
        'order_number', 'task_id'
    ).annotate(
        count=Count('id')
    ).filter(
        count__gt=1
    )

    result = []
    for dup in duplicates:
        assemblies = PartiallyPickedAssembly.objects.filter(
            order_number=dup['order_number'],
            task_id=dup['task_id']
        )
        result.append({
            'order_number': dup['order_number'],
            'task_id': dup['task_id'],
            'count': dup['count'],
            'ids': list(assemblies.values_list('id', flat=True))
        })

    return result


def find_duplicate_products():
    """Находит дублирующиеся товары в сборках"""
    duplicates = PartiallyPickedProduct.objects.values(
        'assembly', 'lm_code', 'quantity', 'collected_quantity'
    ).annotate(
        count=Count('id')
    ).filter(
        count__gt=1
    )

    result = []
    for dup in duplicates:
        products = PartiallyPickedProduct.objects.filter(
            assembly_id=dup['assembly'],
            lm_code=dup['lm_code'],
            quantity=dup['quantity'],
            collected_quantity=dup['collected_quantity']
        )
        result.append({
            'assembly_id': dup['assembly'],
            'lm_code': dup['lm_code'],
            'quantity': dup['quantity'],
            'collected_quantity': dup['collected_quantity'],
            'count': dup['count'],
            'ids': list(products.values_list('id', flat=True))
        })

    return result


def cleanup_duplicates():
    """Удаляет дублирующиеся записи, оставляя только самую свежую"""
    from django.db import connection

    # Для сборок: оставляем самую свежую по updated_at
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM particles_partiallypickedassembly 
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, 
                           ROW_NUMBER() OVER (
                               PARTITION BY order_number, task_id 
                               ORDER BY updated_at DESC
                           ) as row_num
                    FROM particles_partiallypickedassembly
                ) as ranked
                WHERE row_num > 1
            )
        """)

    # Для товаров: оставляем самую свежую по updated_at
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM particles_partiallypickedproduct 
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, 
                           ROW_NUMBER() OVER (
                               PARTITION BY assembly_id, lm_code, quantity, collected_quantity 
                               ORDER BY updated_at DESC
                           ) as row_num
                    FROM particles_partiallypickedproduct
                ) as ranked
                WHERE row_num > 1
            )
        """)

    return {
        'message': 'Дубликаты очищены. Теперь можно применить уникальные constraints.'
    }