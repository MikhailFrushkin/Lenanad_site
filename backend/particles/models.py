from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class PartiallyPickedAssembly(models.Model):
    """
    Модель для хранения данных о частично собранных сборках
    Защита от дублирования: уникальность по order_number + task_id
    """
    # Информация о сборке
    order_number = models.CharField(
        verbose_name="Номер заказа",
        max_length=50,
        db_index=True
    )

    task_id = models.CharField(
        verbose_name="ID сборки",
        max_length=100,
        db_index=True
    )

    status_str = models.CharField(
        verbose_name="Статус сборки",
        max_length=50,
        default="PARTIALLY_PICKED"
    )

    assembly_zone = models.CharField(
        verbose_name="Зона сборки",
        max_length=50,
        null=True,
        blank=True
    )

    assembler = models.CharField(
        verbose_name="Сборщик",
        max_length=255,
        null=True,
        blank=True
    )

    # Метаданные
    timestamp = models.DateTimeField(
        verbose_name="Время отправки",
        default=timezone.now
    )

    source_system = models.CharField(
        verbose_name="Источник данных",
        max_length=100,
        default="assembly_tracker"
    )

    # Вычисляемые поля для удобства фильтрации
    products_count = models.IntegerField(
        verbose_name="Количество несобранных товаров",
        default=0
    )

    total_missing_quantity = models.IntegerField(
        verbose_name="Общее количество недостающих штук",
        default=0
    )

    created_at = models.DateTimeField(
        verbose_name="Время создания записи",
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        verbose_name="Время обновления записи",
        auto_now=True
    )

    class Meta:
        verbose_name = "Частично собранная сборка"
        verbose_name_plural = "Частично собранные сборки"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['order_number', 'timestamp']),
            models.Index(fields=['assembler', 'timestamp']),
        ]
        # Уникальная комбинация order_number и task_id
        constraints = [
            models.UniqueConstraint(
                fields=['order_number', 'task_id'],
                name='unique_assembly_order_task'
            )
        ]

    def __str__(self):
        return f"{self.order_number} - {self.task_id} ({self.assembler})"

    def clean(self):
        """Валидация при сохранении"""
        # Проверяем уникальность перед сохранением
        if PartiallyPickedAssembly.objects.filter(
                order_number=self.order_number,
                task_id=self.task_id
        ).exclude(pk=self.pk).exists():
            raise ValidationError(
                f"Сборка с номером заказа '{self.order_number}' и ID сборки '{self.task_id}' уже существует."
            )

    def update_metrics(self):
        """Обновляет вычисляемые метрики на основе связанных продуктов"""
        products = self.products.all()
        self.products_count = products.count()
        self.total_missing_quantity = sum(
            product.missing_quantity for product in products
        )
        self.save(update_fields=['products_count', 'total_missing_quantity', 'updated_at'])

    def save(self, *args, **kwargs):
        # Вызываем clean для валидации
        self.full_clean()
        super().save(*args, **kwargs)


class PartiallyPickedProduct(models.Model):
    """
    Модель для хранения данных о несобранных товарах в сборке
    Защита от дублирования: уникальность по assembly + lm_code + quantity + collected_quantity
    """
    # Связь с родительской сборкой
    assembly = models.ForeignKey(
        PartiallyPickedAssembly,
        verbose_name="Сборка",
        on_delete=models.CASCADE,
        related_name='products'
    )

    # Основные данные о товаре
    lm_code = models.CharField(
        verbose_name="LM код товара",
        max_length=50,
        db_index=True
    )

    department_id = models.CharField(
        verbose_name="ID отдела",
        max_length=10,
        null=True,
        blank=True
    )

    title = models.TextField(
        verbose_name="Название товара",
        null=True,
        blank=True
    )

    image_url = models.URLField(
        verbose_name="URL изображения",
        max_length=500,
        null=True,
        blank=True
    )

    # Количественные показатели
    quantity = models.IntegerField(
        verbose_name="Требуемое количество",
        default=0
    )

    collected_quantity = models.IntegerField(
        verbose_name="Собранное количество",
        default=0
    )

    missing_quantity = models.IntegerField(
        verbose_name="Недостающее количество",
        default=0
    )

    # Дополнительные поля
    source = models.CharField(
        verbose_name="Источник",
        max_length=100,
        null=True,
        blank=True
    )

    is_critical = models.BooleanField(
        verbose_name="Критический товар",
        default=False
    )

    created_at = models.DateTimeField(
        verbose_name="Время создания записи",
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        verbose_name="Время обновления записи",
        auto_now=True
    )

    class Meta:
        verbose_name = "Несобранный товар"
        verbose_name_plural = "Несобранные товары"
        ordering = ['-missing_quantity']
        indexes = [
            models.Index(fields=['lm_code', 'missing_quantity']),
            models.Index(fields=['department_id', 'missing_quantity']),
        ]
        # Уникальная комбинация для предотвращения дублирования товаров
        constraints = [
            models.UniqueConstraint(
                fields=['assembly', 'lm_code', 'quantity', 'collected_quantity'],
                name='unique_product_in_assembly'
            )
        ]

    def __str__(self):
        return f"{self.lm_code} - {self.title[:50] if self.title else 'Без названия'}"

    def clean(self):
        """Валидация при сохранении"""
        # Проверяем уникальность товара в сборке
        if PartiallyPickedProduct.objects.filter(
                assembly=self.assembly,
                lm_code=self.lm_code,
                quantity=self.quantity,
                collected_quantity=self.collected_quantity
        ).exclude(pk=self.pk).exists():
            raise ValidationError(
                f"Товар с кодом '{self.lm_code}' и такими же параметрами (кол-во: {self.quantity}, собрано: {self.collected_quantity}) уже существует в этой сборке."
            )

        # Проверяем, что collected_quantity не больше quantity
        if self.collected_quantity > self.quantity:
            raise ValidationError(
                f"Собранное количество ({self.collected_quantity}) не может быть больше требуемого ({self.quantity})"
            )

    def save(self, *args, **kwargs):
        # Вычисляем недостающее количество перед сохранением
        self.missing_quantity = max(0, self.quantity - self.collected_quantity)

        # Проверяем, является ли товар критическим
        self.is_critical = self.missing_quantity > 5

        # Проверяем уникальность и другие правила
        self.full_clean()

        # Определяем, это новая запись или обновление существующей
        is_new = self.pk is None

        super().save(*args, **kwargs)

        # Обновляем метрики родительской сборки
        self.assembly.update_metrics()

    def delete(self, *args, **kwargs):
        assembly = self.assembly
        super().delete(*args, **kwargs)
        assembly.update_metrics()