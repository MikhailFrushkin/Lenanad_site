import os
from pathlib import Path
from environs import Env
from loguru import logger

BASE_DIR = Path(__file__).resolve().parent.parent

env = Env()
env.read_env()
SECRET_KEY = env.str("SECRET_KEY")
DB_NAME = env.str("DB_NAME")
DB_USER = env.str("DB_USER")
DB_PASSWORD = env.str("DB_PASSWORD")
DB_PORT = env.str("DB_PORT")


DEBUG = os.getenv("DEBUG", "1") == "1"
BASE_URL = "https://lemana-pro.online"
ALLOWED_HOSTS = [os.getenv("HOST_NAME", "0.0.0.0"), f"www.{os.getenv('HOST_NAME')}"]
if DEBUG:
    ALLOWED_HOSTS += ["localhost", "127.0.0.1"]
    POSTGRES_HOST = "localhost"
else:
    POSTGRES_HOST = env.str("POSTGRES_HOST", "db")

CSRF_TRUSTED_ORIGINS = [
    f"https://*.{os.getenv('HOST_NAME')}",
    f"http://*.{os.getenv('HOST_NAME')}",
    f"https://{os.getenv('HOST_NAME')}",
    f"http://{os.getenv('HOST_NAME')}",
]
INTERNAL_IPS = [
    "127.0.0.1",
]
if DEBUG:
    CSRF_TRUSTED_ORIGINS += ["http://localhost", "http://127.0.0.1"]
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # ← добавляем humanize

    # Сторонние приложения
    'debug_toolbar',
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'simple_history',
    'django_apscheduler',
    'widget_tweaks',

    # Ваши приложения
    'home',
    'users',
    'particles',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',  # ← Добавить первым
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if not DEBUG:
    INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'debug_toolbar']
    MIDDLEWARE = [mw for mw in MIDDLEWARE if mw != 'debug_toolbar.middleware.DebugToolbarMiddleware']
else:
    # Для debug toolbar
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    }

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
APSCHEDULER_RUN_NOW_TIMEOUT = 25  # Seconds
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),  # Глобальные шаблоны
        ],
        "APP_DIRS": True,  # ВАЖНО: True для поиска в app/templates/
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': POSTGRES_HOST,
        'PORT': DB_PORT,
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]



LANGUAGE_CODE = "ru-RU"

TIME_ZONE = "Asia/Novosibirsk"

USE_I18N = True

USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = "/app/staticfiles"  # Для Docker
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),  # Исходные файлы
]

# Для разработки
if DEBUG:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
else:
    MEDIA_ROOT = "/app/media"
    MEDIA_URL = "/media/"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(BASE_DIR, "django_cache"),
    }
}

# Настройки аутентификации
LOGIN_URL = 'home:login'
LOGIN_REDIRECT_URL = 'home:index'
LOGOUT_REDIRECT_URL = 'home:login'

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}
AUTH_USER_MODEL = 'users.CustomUser'