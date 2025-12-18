from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Country(models.Model):
    name = models.CharField(verbose_name="Страна", max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страны"


class City(models.Model):
    name = models.CharField(verbose_name="Город", max_length=255)
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="cities",
        verbose_name="Страна"
    )

    def __str__(self):
        return f"{self.name} ({self.country.name})"

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"


class Role(models.Model):
    name = models.CharField(verbose_name="Должность", max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"


class Department(models.Model):
    name = models.CharField(verbose_name="Отдел", max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"


class Store(models.Model):
    name = models.CharField(verbose_name="Магазин", max_length=255)
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="stores",
        verbose_name="Город",
        null=True,
        blank=True
    )
    address = models.CharField(
        verbose_name="Адрес",
        max_length=500,
        blank=True,
        null=True
    )

    def __str__(self):
        if self.city:
            return f"{self.name} ({self.city.name})"
        return self.name

    class Meta:
        verbose_name = "Магазин"
        verbose_name_plural = "Магазины"


class CustomUser(AbstractUser):
    TYPE_STATUS = [
        ("Работа", "Работа"),
        ("Отпуск", "Отпуск"),
        ("Больничный", "Больничный"),
        ("Уволен", "Уволен"),
    ]

    country = models.ForeignKey(
        Country,  # Исправлено: было Role, должно быть Country
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users_country",  # Уникальный related_name
        verbose_name="Страна"
    )

    city = models.ForeignKey(
        City,  # Исправлено: было Role, должно быть City
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users_city",  # Уникальный related_name
        verbose_name="Город"
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users_role",  # Уникальный related_name
        verbose_name="Должность"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="department_users",
        verbose_name="Отдел"
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="store_users",
        verbose_name="Магазин"
    )

    status_work = models.CharField(
        verbose_name="Статус работы",
        default="Работа",
        choices=TYPE_STATUS,
        max_length=20
    )

    photo = models.ImageField(
        verbose_name="Фото",
        upload_to="user_photos/%Y/%m/%d/",  # Лучшая структура для хранения
        blank=True,
        null=True
    )

    phone_number = models.CharField(
        verbose_name="Номер телефона",
        max_length=15,
        blank=True,
        null=True
    )

    birth_date = models.DateField(
        verbose_name="Дата рождения",
        null=True,
        blank=True
    )

    address = models.TextField(
        verbose_name="Адрес проживания",
        blank=True,
        null=True
    )

    telegram = models.CharField(
        verbose_name="Telegram",
        max_length=100,
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено"
    )

    last_input_main = models.DateTimeField(
        verbose_name="Последняя активность",
        null=True,
        blank=True
    )

    def set_last_input_main(self):
        """Обновить время последней активности"""
        self.last_input_main = timezone.now()
        self.save()

    def get_full_name_display(self):
        """Полное имя пользователя для отображения"""
        if self.first_name and self.last_name:
            return f"{self.last_name} {self.first_name}"
        elif self.first_name:
            return self.first_name
        return self.username

    def get_location_display(self):
        """Отображение местоположения"""
        location_parts = []
        if self.city:
            location_parts.append(self.city.name)
        if self.country:
            location_parts.append(self.country.name)
        return ", ".join(location_parts) if location_parts else "Не указано"

    def get_work_info_display(self):
        """Отображение рабочей информации"""
        info_parts = []
        if self.role:
            info_parts.append(str(self.role))
        if self.department:
            info_parts.append(f"отдел: {self.department}")
        if self.store:
            info_parts.append(f"магазин: {self.store}")
        return " | ".join(info_parts) if info_parts else "Не указано"

    def __str__(self):
        return self.get_full_name_display()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['department']),
            models.Index(fields=['store']),
            models.Index(fields=['status_work']),
        ]