from django.contrib import admin
from django.utils.html import format_html
from .models import PartiallyPickedAssembly, PartiallyPickedProduct
from .utils import find_duplicate_assemblies, find_duplicate_products, cleanup_duplicates


@admin.action(description='Проверить дубликаты сборок')
def check_assembly_duplicates(modeladmin, request, queryset):
    duplicates = find_duplicate_assemblies()
    if duplicates:
        msg = f"Найдено {len(duplicates)} дублирующихся сборок"
    else:
        msg = "Дубликатов не найдено"
    modeladmin.message_user(request, msg)


@admin.action(description='Проверить дубликаты товаров')
def check_product_duplicates(modeladmin, request, queryset):
    duplicates = find_duplicate_products()
    if duplicates:
        msg = f"Найдено {len(duplicates)} дублирующихся товаров"
    else:
        msg = "Дубликатов не найдено"
    modeladmin.message_user(request, msg)


class PartiallyPickedProductInline(admin.TabularInline):
    model = PartiallyPickedProduct
    extra = 0
    readonly_fields = ['missing_quantity', 'is_critical', 'created_at', 'updated_at']
    fields = ['lm_code', 'title', 'quantity', 'collected_quantity',
              'missing_quantity', 'is_critical', 'source']


@admin.register(PartiallyPickedAssembly)
class PartiallyPickedAssemblyAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'task_id', 'assembler_short',
                    'assembly_zone', 'products_count',
                    'total_missing_quantity', 'black_list', 'updated_at']
    list_filter = ['assembly_zone', 'black_list', 'updated_at']
    search_fields = ['order_number', 'task_id', 'assembler']
    readonly_fields = ['created_at', 'updated_at', 'products_count', 'total_missing_quantity']

    inlines = [PartiallyPickedProductInline]
    actions = [check_assembly_duplicates]

    fieldsets = (
        ('Основная информация', {
            'fields': ('order_number', 'task_id', 'status_str')
        }),
        ('Дополнительная информация', {
            'fields': ('assembly_zone', 'assembler', 'timestamp', 'black_list')
        }),
        ('Статистика', {
            'fields': ('products_count', 'total_missing_quantity')
        }),
        ('Метаданные', {
            'fields': ('source_system', 'created_at', 'updated_at')
        }),
    )

    def assembler_short(self, obj):
        return obj.assembler.split()[-1] if obj.assembler else ''

    assembler_short.short_description = 'Сборщик (фамилия)'


@admin.register(PartiallyPickedProduct)
class PartiallyPickedProductAdmin(admin.ModelAdmin):
    list_display = ['lm_code', 'title_short', 'assembly_link',
                    'quantity', 'collected_quantity',
                    'missing_quantity', 'black_list', 'updated_at']
    list_filter = ['black_list', 'department_id', 'created_at', 'updated_at']
    search_fields = ['lm_code', 'title', 'assembly__order_number']
    readonly_fields = ['missing_quantity', 'created_at', 'updated_at']

    actions = [check_product_duplicates]

    fieldsets = (
        ('Основная информация', {
            'fields': ('assembly', 'lm_code', 'title', 'department_id', 'black_list')
        }),
        ('Количественные показатели', {
            'fields': ('quantity', 'collected_quantity', 'missing_quantity')
        }),
        ('Дополнительно', {
            'fields': ('image_url', 'source')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def title_short(self, obj):
        return obj.title[:50] + '...' if obj.title and len(obj.title) > 50 else obj.title

    title_short.short_description = 'Название'

    def assembly_link(self, obj):
        return format_html(
            '<a href="/admin/particles/partiallypickedassembly/{}/change/">{}</a>',
            obj.assembly.id,
            obj.assembly.order_number
        )

    assembly_link.short_description = 'Сборка'
    assembly_link.admin_order_field = 'assembly__order_number'