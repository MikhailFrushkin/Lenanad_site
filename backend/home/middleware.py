# middleware.py
from django.utils import timezone
from urllib.parse import urlparse, urlunparse, parse_qs
import re


class VisitCounterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.excluded_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/robots.txt',
            '/sitemap.xml',
        ]

        # Регулярные выражения для исключения определенных путей
        self.excluded_patterns = [
            r'^/static/',
            r'^/media/',
            r'^/admin/',
            r'\.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf|eot)$',
        ]

    def __call__(self, request):
        # Пропускаем если не нужно отслеживать
        if not self._should_track(request):
            return self.get_response(request)

        # Получаем или создаем ключ сессии
        if not request.session.session_key:
            request.session.save()

        # Нормализуем URL (убираем параметры)
        full_url = request.build_absolute_uri()
        normalized_url = self._normalize_url(full_url)

        # Сохраняем посещение
        self._save_visit(request, full_url, normalized_url)

        response = self.get_response(request)
        return response

    def _should_track(self, request):
        """Проверяем, нужно ли отслеживать этот запрос"""
        path = request.path

        # Проверяем исключенные пути
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return False

        # Проверяем регулярные выражения
        for pattern in self.excluded_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return False

        # Игнорируем AJAX запросы если нужно (опционально)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return False

        return True

    def _normalize_url(self, url):
        """
        Нормализует URL, убирая параметры запроса

        Пример:
        Вход: https://lemana-pro.online/particles/?assembler=&assembly_zone=&department_id=...
        Выход: https://lemana-pro.online/particles/
        """
        try:
            parsed = urlparse(url)

            # Создаем новый URL без параметров запроса
            normalized = urlunparse((
                parsed.scheme,  # http или https
                parsed.netloc,  # domain
                parsed.path,  # путь без параметров
                '',  # params (устарело)
                '',  # query string (убираем!)
                ''  # fragment (убираем!)
            ))

            # Убираем слеш в конце если нужно (опционально)
            # if normalized.endswith('/') and len(normalized) > 1:
            #     normalized = normalized.rstrip('/')

            return normalized
        except:
            # Если что-то пошло не так, возвращаем оригинальный URL
            return url

    def _get_client_ip(self, request):
        """Получаем IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _save_visit(self, request, full_url, normalized_url):
        """Сохраняет информацию о посещении"""
        try:
            from .models import PageVisit

            # Проверяем, не был ли этот URL уже посещен в этой сессии
            # (для предотвращения дублирования при перезагрузках)
            session_key = request.session.session_key

            # Можно добавить проверку на частые посещения
            # например, не считать посещения чаще чем раз в 30 секунд
            last_visit_key = f'last_visit_{normalized_url}'
            last_visit_time = request.session.get(last_visit_key)
            current_time = timezone.now().timestamp()

            if last_visit_time and (current_time - last_visit_time < 30):
                # Пропускаем слишком частые посещения
                return

            # Сохраняем время последнего посещения
            request.session[last_visit_key] = current_time

            # Создаем запись о посещении
            visit = PageVisit(
                user=request.user if request.user.is_authenticated else None,
                session_key=session_key,
                url=normalized_url,
                full_url=full_url,
                ip_address=self._get_client_ip(request),
                referer=request.META.get('HTTP_REFERER', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                method=request.method,
                timestamp=timezone.now()
            )
            visit.save()

        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving visit: {e}")