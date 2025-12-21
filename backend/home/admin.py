# admin.py (минимальная версия)
from django.contrib import admin
from .models import PageVisit


@admin.register(PageVisit)
class SimplePageVisitAdmin(admin.ModelAdmin):
    # Что показываем в списке
    list_display = ['id', 'url', 'user', 'ip_address', 'timestamp', 'method']

    # Что можно редактировать (ничего)
    readonly_fields = [field.name for field in PageVisit._meta.fields]

    # Поиск
    search_fields = ['url', 'ip_address', 'user__username']

    # Фильтры
    list_filter = ['timestamp', 'method', 'user']

    # Сортировка
    ordering = ['-timestamp']

    # Пагинация
    list_per_page = 100

    # Нельзя добавлять/редактировать
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False