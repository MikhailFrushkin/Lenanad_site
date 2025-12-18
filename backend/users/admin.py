from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    Country, City, Role, Department, Store, CustomUser
)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'cities_count', 'users_count')
    search_fields = ('name',)
    ordering = ('name',)

    def cities_count(self, obj):
        return obj.cities.count()

    cities_count.short_description = 'Количество городов'

    def users_count(self, obj):
        return obj.users_country.count()

    users_count.short_description = 'Количество пользователей'


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country', 'stores_count', 'users_count')
    list_filter = ('country',)
    search_fields = ('name', 'country__name')
    ordering = ('country', 'name')

    def stores_count(self, obj):
        return obj.stores.count()

    stores_count.short_description = 'Количество магазинов'

    def users_count(self, obj):
        return obj.users_city.count()

    users_count.short_description = 'Количество пользователей'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'users_count')
    search_fields = ('name',)
    ordering = ('name',)

    def users_count(self, obj):
        return obj.users_role.count()

    users_count.short_description = 'Количество сотрудников'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'users_count')
    search_fields = ('name',)
    ordering = ('name',)

    def users_count(self, obj):
        return obj.department_users.count()

    users_count.short_description = 'Количество сотрудников'


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'city', 'address_preview', 'users_count')
    list_filter = ('city', 'city__country')
    search_fields = ('name', 'city__name', 'address')
    ordering = ('city', 'name')

    def address_preview(self, obj):
        if obj.address and len(obj.address) > 50:
            return f"{obj.address[:50]}..."
        return obj.address or "-"

    address_preview.short_description = 'Адрес'

    def users_count(self, obj):
        return obj.store_users.count()

    users_count.short_description = 'Количество сотрудников'


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'photo_preview',
        'username',
        'get_full_name',
        'email',
        'role',
        'department',
        'store',
        'status_work',
        'city',
        'country',
        'is_active',
        'is_staff'
    )

    list_filter = (
        'is_staff',
        'is_active',
        'is_superuser',
        'status_work',
        'role',
        'department',
        'store',
        'country',
        'city'
    )

    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'phone_number',
        'telegram'
    )

    ordering = ('-date_joined',)

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'username',
                'password',
                'email',
                'first_name',
                'last_name'
            )
        }),
        ('Местоположение', {
            'fields': (
                'country',
                'city',
                'address'
            )
        }),
        ('Рабочая информация', {
            'fields': (
                'role',
                'department',
                'store',
                'status_work'
            )
        }),
        ('Контактная информация', {
            'fields': (
                'phone_number',
                'telegram',
                'photo',
                'birth_date'
            )
        }),
        ('Статусы и активность', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'last_input_main'
            )
        }),
        ('Группы и права', {
            'fields': (
                'groups',
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': (
                'last_login',
                'date_joined'
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = (
        'last_login',
        'date_joined',
        'last_input_main'
    )

    add_fieldsets = (
        ('Основная информация', {
            'classes': ('wide',),
            'fields': (
                'username',
                'password1',
                'password2',
                'email',
                'first_name',
                'last_name'
            )
        }),
        ('Рабочая информация', {
            'classes': ('wide',),
            'fields': (
                'role',
                'department',
                'store',
                'status_work'
            )
        }),
        ('Местоположение', {
            'classes': ('wide',),
            'fields': (
                'country',
                'city'
            )
        }),
        ('Контактная информация', {
            'classes': ('wide',),
            'fields': (
                'phone_number',
                'telegram'
            )
        }),
        ('Права доступа', {
            'classes': ('wide',),
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser'
            )
        }),
    )

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />',
                obj.photo.url
            )
        return format_html(
            '<div style="width:50px;height:50px;border-radius:50%;background:#f0f0f0;'
            'display:flex;align-items:center;justify-content:center;color:#999;">'
            'Нет фото</div>'
        )

    photo_preview.short_description = 'Фото'

    def get_full_name(self, obj):
        return obj.get_full_name_display()

    get_full_name.short_description = 'ФИО'

    actions = [
        'activate_users',
        'deactivate_users',
        'set_status_work',
        'set_status_vacation',
        'set_status_sick'
    ]

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано {updated} пользователей.')

    activate_users.short_description = "Активировать пользователей"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано {updated} пользователей.')

    deactivate_users.short_description = "Деактивировать пользователей"

    def set_status_work(self, request, queryset):
        updated = queryset.update(status_work='Работа')
        self.message_user(request, f'Статус "Работа" установлен для {updated} пользователей.')

    set_status_work.short_description = "Установить статус 'Работа'"

    def set_status_vacation(self, request, queryset):
        updated = queryset.update(status_work='Отпуск')
        self.message_user(request, f'Статус "Отпуск" установлен для {updated} пользователей.')

    set_status_vacation.short_description = "Установить статус 'Отпуск'"

    def set_status_sick(self, request, queryset):
        updated = queryset.update(status_work='Больничный')
        self.message_user(request, f'Статус "Больничный" установлен для {updated} пользователей.')

    set_status_sick.short_description = "Установить статус 'Больничный'"