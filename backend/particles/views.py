from pprint import pprint

import pandas as pd
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Avg, Max
from django.db.models.functions import TruncDate, ExtractHour
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
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
    template_name = "particles/particles.html"
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
        assembly_zone = self.request.GET.get('assembly_zone')
        logger.debug(date_from)
        logger.debug(date_to)
        # Базовый QuerySet с префетчем
        assemblies = PartiallyPickedAssembly.objects.filter(black_list=False).prefetch_related('products').all()

        # Применяем фильтры
        if assembler:
            assemblies = assemblies.filter(assembler__icontains=assembler)

        if order_number:
            assemblies = assemblies.filter(order_number=order_number)

        if date_from:
            assemblies = assemblies.filter(created_at__date__gte=date_from)

        if date_to:
            assemblies = assemblies.filter(created_at__date__lte=date_to)

        if department_id:
            assemblies = assemblies.filter(products__department_id=department_id).distinct()

        if assembly_zone:
            assemblies = assemblies.filter(assembly_zone__icontains=assembly_zone)

        # Создаем плоский список для таблицы
        table_data = []
        for assembly in assemblies.order_by("-created_at", "order_number", "task_id"):
            products = assembly.products.filter(black_list=False)

            if department_id:
                products = products.filter(department_id=department_id)

            if products.exists():
                for product in products:
                    table_data.append({
                        'assembly': assembly,
                        'product': product,
                        'is_first_product': True,
                    })
            # else:
            #     if not department_id:
            #         table_data.append({
            #             'assembly': assembly,
            #             'product': None,
            #             'is_first_product': True,
            #         })

        context['table_data'] = table_data
        context['total_rows'] = len(table_data)
        context['total_assemblies'] = assemblies.count()

        context['unique_assemblers'] = list(set(i.get("assembler") for i in assemblies.values('assembler')))
        context['unique_zones'] = assemblies.values('assembly_zone').distinct().order_by('assembly_zone')
        context['unique_departments'] = PartiallyPickedProduct.objects.values('department_id').exclude(
            department_id__isnull=True
        ).exclude(department_id='').distinct().order_by('department_id')

        # Параметры фильтров
        context['filter_assembler'] = assembler
        context['filter_order'] = order_number
        context['filter_date_from'] = date_from
        context['filter_date_to'] = date_to
        context['filter_department'] = department_id
        context['filter_zone'] = assembly_zone

        return context


class AssemblyDetailView(LoginRequiredMixin, TemplateView):
    template_name = "particles/assembly_detail.html"
    login_url = "home:login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.request.user.username

        assembly_id = self.kwargs.get('pk')

        try:
            assembly = PartiallyPickedAssembly.objects.prefetch_related('products').get(id=assembly_id)
            context['assembly'] = assembly

            # Статистика по товарам
            products = assembly.products.filter(black_list=False)
            context['products'] = products
            context['critical_products'] = products.filter(is_critical=True)
            context['total_missing'] = sum(p.missing_quantity for p in products)

        except PartiallyPickedAssembly.DoesNotExist:
            context['error'] = "Сборка не найдена"

        return context


def product_blacklist(request, pk):
    """Добавить товар в черный список"""
    try:
        product = get_object_or_404(PartiallyPickedProduct, id=pk)
        product.mark_as_blacklisted()  # Используем новый метод
        messages.success(request, f'Товар {product.lm_code} добавлен в черный список')
    except Exception as e:
        messages.error(request, f'Ошибка: {e}')

    return redirect("particles:particles_main")


def product_remove_blacklist(request, pk):
    """Убрать товар из черного списка"""
    try:
        product = get_object_or_404(PartiallyPickedProduct, id=pk)
        product.remove_from_blacklist()  # Используем новый метод
        messages.success(request, f'Товар {product.lm_code} убран из черного списка')
    except Exception as e:
        messages.error(request, f'Ошибка: {e}')

    return redirect("particles:particles_main")

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

#Статистика
class StatisticsDashboard(LoginRequiredMixin, TemplateView):
    """Дашборд статистики по частичным сборкам"""
    template_name = "particles/dashboard.html"
    login_url = "home:login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Параметры периода
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        assembler = self.request.GET.get('assembler')
        department_id = self.request.GET.get('department_id')

        # Базовые QuerySet'ы
        assemblies = PartiallyPickedAssembly.objects.all()
        products = PartiallyPickedProduct.objects.all()

        # Применяем фильтры
        if date_from:
            assemblies = assemblies.filter(created_at__date__gte=date_from)
            products = products.filter(assembly__created_at__date__gte=date_from)

        if date_to:
            assemblies = assemblies.filter(created_at__date__lte=date_to)
            products = products.filter(assembly__created_at__date__lte=date_to)

        if assembler:
            assemblies = assemblies.filter(assembler__icontains=assembler)
            products = products.filter(assembly__assembler__icontains=assembler)

        if department_id:
            products = products.filter(department_id=department_id)
            assemblies = assemblies.filter(products__department_id=department_id).distinct()

        # 1. Общая статистика за период
        context['total_stats'] = self.get_total_stats(assemblies, products)

        # 2. Статистика по сборщикам
        context['assembler_stats'] = self.get_assembler_stats(assemblies)

        # 3. Статистика по товарам
        context['product_stats'] = self.get_product_stats(products)

        # 4. Статистика по отделам
        context['department_stats'] = self.get_department_stats(products)

        # 5. Временная статистика (по дням, часам)
        context['time_stats'] = self.get_time_stats(assemblies)

        # 6. Критические товары
        context['critical_stats'] = self.get_critical_stats(products)

        # Фильтры для отображения
        context['date_from'] = date_from
        context['date_to'] = date_to
        context['assembler'] = assembler
        context['department_id'] = department_id

        # Уникальные значения для фильтров
        context['unique_assemblers'] = PartiallyPickedAssembly.objects.values(
            'assembler'
        ).exclude(assembler__isnull=True).exclude(assembler='').distinct().order_by('assembler')

        context['unique_departments'] = PartiallyPickedProduct.objects.values(
            'department_id'
        ).exclude(department_id__isnull=True).exclude(department_id='').distinct().order_by('department_id')

        return context

    def get_total_stats(self, assemblies, products):
        """Общая статистика за период"""
        total_assemblies = assemblies.count()
        total_products = products.count()

        # Сборки с товарами и без
        assemblies_with_products = assemblies.filter(products_count__gt=0).count()
        assemblies_without_products = total_assemblies - assemblies_with_products

        # Товарная статистика
        total_missing_quantity = products.aggregate(
            total=Sum('missing_quantity')
        )['total'] or 0

        total_required_quantity = products.aggregate(
            total=Sum('quantity')
        )['total'] or 0

        total_collected_quantity = products.aggregate(
            total=Sum('collected_quantity')
        )['total'] or 0

        # Критические товары
        critical_products = products.filter(is_critical=True).count()

        return {
            'total_assemblies': total_assemblies,
            'total_products': total_products,
            'assemblies_with_products': assemblies_with_products,
            'assemblies_without_products': assemblies_without_products,
            'total_missing_quantity': total_missing_quantity,
            'total_required_quantity': total_required_quantity,
            'total_collected_quantity': total_collected_quantity,
            'collection_rate': (total_collected_quantity / total_required_quantity * 100
                                if total_required_quantity > 0 else 0),
            'critical_products': critical_products,
            'critical_percentage': (critical_products / total_products * 100
                                    if total_products > 0 else 0),
        }

    def get_assembler_stats(self, assemblies):
        """Статистика по сборщикам"""
        stats = assemblies.values('assembler').annotate(
            assembly_count=Count('id'),
            total_products=Sum('products_count'),
            total_missing=Sum('total_missing_quantity'),
            avg_products_per_assembly=Avg('products_count'),
            last_activity=Max('created_at'),
        ).order_by('-assembly_count')

        # Рассчитываем дополнительные метрики
        for item in stats:
            # Среднее время между сборками
            assembler_assemblies = assemblies.filter(assembler=item['assembler'])
            if assembler_assemblies.count() > 1:
                time_diffs = []
                prev_time = None
                for assembly in assembler_assemblies.order_by('created_at'):
                    if prev_time:
                        time_diffs.append((assembly.created_at - prev_time).total_seconds() / 60)  # в минутах
                    prev_time = assembly.created_at
                if time_diffs:
                    item['avg_time_between'] = sum(time_diffs) / len(time_diffs)
                else:
                    item['avg_time_between'] = 0
            else:
                item['avg_time_between'] = None

            # Часы пиковой активности
            hours = assembler_assemblies.annotate(
                hour=ExtractHour('created_at')
            ).values('hour').annotate(
                count=Count('id')
            ).order_by('-count')

            if hours.exists():
                peak_hour = hours.first()
                item['peak_hour'] = f"{peak_hour['hour']}:00"
                item['peak_hour_count'] = peak_hour['count']
            else:
                item['peak_hour'] = None
                item['peak_hour_count'] = 0

        return list(stats)

    def get_product_stats(self, products):
        """Статистика по товарам"""
        # Топ товаров по количеству недостачи
        top_by_missing = products.values('lm_code', 'title', 'department_id').annotate(
            total_missing=Sum('missing_quantity'),
            occurrences=Count('id'),
            avg_missing=Avg('missing_quantity'),
            max_missing=Max('missing_quantity'),
            assemblies_count=Count('assembly', distinct=True),
            assemblers_count=Count('assembly__assembler', distinct=True),
        ).order_by('-total_missing')[:20]

        # Товары с повторными попаданиями в течение суток
        # Для этого нужен более сложный запрос
        repeated_products = []
        today = timezone.now().date()

        for product in products.filter(assembly__created_at__date=today).values(
                'lm_code', 'title', 'department_id'
        ).annotate(
            today_count=Count('id')
        ).filter(today_count__gt=1):
            # Получаем подробности о повторениях
            product_details = products.filter(
                lm_code=product['lm_code'],
                assembly__created_at__date=today
            ).values('assembly__order_number', 'missing_quantity',
                     'assembly__created_at', 'assembly__assembler')

            repeated_products.append({
                'lm_code': product['lm_code'],
                'title': product['title'],
                'department_id': product['department_id'],
                'today_count': product['today_count'],
                'details': list(product_details),
            })

        # Частота появления товаров
        frequency_stats = products.values('lm_code', 'title').annotate(
            total_occurrences=Count('id'),
            days_active=Count('assembly__created_at__date', distinct=True),
            avg_per_day=Count('id') / Count('assembly__created_at__date', distinct=True),
            last_seen=Max('assembly__created_at'),
        ).order_by('-total_occurrences')[:15]

        return {
            'top_by_missing': list(top_by_missing),
            'repeated_today': repeated_products,
            'frequency_stats': list(frequency_stats),
        }

    def get_department_stats(self, products):
        """Статистика по отделам"""
        stats = products.values('department_id').exclude(
            department_id__isnull=True
        ).exclude(
            department_id=''
        ).annotate(
            product_count=Count('id'),
            total_missing=Sum('missing_quantity'),
            total_required=Sum('quantity'),
            total_collected=Sum('collected_quantity'),
            avg_missing=Avg('missing_quantity'),
            unique_products=Count('lm_code', distinct=True),
            unique_assemblies=Count('assembly', distinct=True),
            unique_assemblers=Count('assembly__assembler', distinct=True),
        ).order_by('-total_missing')

        # Рассчитываем проценты
        for item in stats:
            if item['total_required'] > 0:
                item['collection_rate'] = (item['total_collected'] / item['total_required'] * 100)
            else:
                item['collection_rate'] = 0

            if item['product_count'] > 0:
                item['avg_per_assembly'] = item['product_count'] / item['unique_assemblies']
            else:
                item['avg_per_assembly'] = 0

        return list(stats)

    def get_time_stats(self, assemblies):
        """Статистика по времени"""
        # По дням
        daily_stats = assemblies.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            total_products=Sum('products_count'),
            total_missing=Sum('total_missing_quantity'),
        ).order_by('date')

        # По часам (среднее за период)
        hourly_stats = assemblies.annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            count=Count('id'),
            avg_products=Avg('products_count'),
            avg_missing=Avg('total_missing_quantity'),
        ).order_by('hour')

        # Тренды
        trend_data = []
        current_date = None
        current_count = 0
        for stat in daily_stats:
            if stat['date'] != current_date:
                if current_date:
                    trend_data.append({
                        'date': current_date,
                        'count': current_count
                    })
                current_date = stat['date']
                current_count = 0
            current_count += stat['count']

        if current_date:
            trend_data.append({
                'date': current_date,
                'count': current_count
            })

        return {
            'daily': list(daily_stats),
            'hourly': list(hourly_stats),
            'trend': trend_data,
        }

    def get_critical_stats(self, products):
        """Статистика по критическим товарам"""
        critical = products.filter(is_critical=True)

        # По отделам
        by_department = critical.values('department_id').annotate(
            count=Count('id'),
            total_missing=Sum('missing_quantity'),
            avg_missing=Avg('missing_quantity'),
        ).order_by('-count')

        # По сборщикам
        by_assembler = critical.values('assembly__assembler').annotate(
            count=Count('id'),
            total_missing=Sum('missing_quantity'),
        ).order_by('-count')

        # По товарам
        by_product = critical.values('lm_code', 'title').annotate(
            count=Count('id'),
            total_missing=Sum('missing_quantity'),
            assemblies=Count('assembly', distinct=True),
        ).order_by('-total_missing')[:10]

        # Временное распределение
        by_time = critical.annotate(
            date=TruncDate('assembly__created_at'),
            hour=ExtractHour('assembly__created_at')
        ).values('date', 'hour').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        return {
            'by_department': list(by_department),
            'by_assembler': list(by_assembler),
            'by_product': list(by_product),
            'by_time': list(by_time),
            'total_critical': critical.count(),
        }


class StatisticsAPIView(LoginRequiredMixin, TemplateView):
    """API для динамической загрузки статистики (для графиков)"""

    def get(self, request, *args, **kwargs):
        chart_type = request.GET.get('chart_type', 'daily_assemblies')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')

        # Базовый QuerySet с фильтрами
        assemblies = PartiallyPickedAssembly.objects.all()
        products = PartiallyPickedProduct.objects.all()

        if date_from:
            assemblies = assemblies.filter(created_at__date__gte=date_from)
            products = products.filter(assembly__created_at__date__gte=date_from)

        if date_to:
            assemblies = assemblies.filter(created_at__date__lte=date_to)
            products = products.filter(assembly__created_at__date__lte=date_to)

        data = {}

        if chart_type == 'daily_assemblies':
            # Сборки по дням
            stats = assemblies.annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')

            data = {
                'labels': [item['date'].strftime('%d.%m') for item in stats],
                'datasets': [{
                    'label': 'Количество сборок',
                    'data': [item['count'] for item in stats],
                    'borderColor': 'rgb(75, 192, 192)',
                    'tension': 0.1
                }]
            }

        elif chart_type == 'assembler_performance':
            # Производительность сборщиков
            stats = assemblies.values('assembler').annotate(
                count=Count('id'),
                avg_products=Avg('products_count'),
                avg_missing=Avg('total_missing_quantity'),
            ).order_by('-count')[:10]

            data = {
                'labels': [item['assembler'] or 'Не указан' for item in stats],
                'datasets': [
                    {
                        'label': 'Количество сборок',
                        'data': [item['count'] for item in stats],
                        'backgroundColor': 'rgba(255, 99, 132, 0.5)',
                    },
                    {
                        'label': 'Среднее кол-во товаров',
                        'data': [item['avg_products'] for item in stats],
                        'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                    }
                ]
            }

        elif chart_type == 'department_distribution':
            # Распределение по отделам
            stats = products.values('department_id').annotate(
                count=Count('id'),
                total_missing=Sum('missing_quantity'),
            ).order_by('-count')[:10]

            data = {
                'labels': [f"Отдел {item['department_id']}" for item in stats],
                'datasets': [{
                    'label': 'Количество товаров',
                    'data': [item['count'] for item in stats],
                    'backgroundColor': [
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(255, 206, 86, 0.5)',
                        'rgba(75, 192, 192, 0.5)',
                        'rgba(153, 102, 255, 0.5)',
                    ],
                }]
            }

        elif chart_type == 'missing_quantity_trend':
            # Тренд недостающего количества
            stats = assemblies.annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                total_missing=Sum('total_missing_quantity'),
                total_products=Sum('products_count'),
            ).order_by('date')

            data = {
                'labels': [item['date'].strftime('%d.%m') for item in stats],
                'datasets': [
                    {
                        'label': 'Недостающее количество',
                        'data': [item['total_missing'] for item in stats],
                        'borderColor': 'rgb(255, 99, 132)',
                        'tension': 0.1
                    },
                    {
                        'label': 'Количество товаров',
                        'data': [item['total_products'] for item in stats],
                        'borderColor': 'rgb(54, 162, 235)',
                        'tension': 0.1
                    }
                ]
            }

        return JsonResponse(data, safe=False)


class StatisticsExportView(LoginRequiredMixin, TemplateView):
    """Экспорт статистики в JSON"""

    def get(self, request, *args, **kwargs):
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')

        # Собираем все данные
        dashboard_view = StatisticsDashboard()
        dashboard_view.request = request

        context = dashboard_view.get_context_data()

        # Формируем структуру для экспорта
        export_data = {
            'period': {
                'date_from': date_from,
                'date_to': date_to,
                'generated_at': timezone.now().isoformat(),
            },
            'total_statistics': context['total_stats'],
            'assembler_statistics': context['assembler_stats'],
            'department_statistics': context['department_stats'],
            'product_statistics': context['product_stats'],
            'critical_statistics': context['critical_stats'],
        }

        response = JsonResponse(export_data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="statistics_{date_from}_{date_to}.json"'
        return response


