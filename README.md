# Частые проблемы:

1) Внутренняя апишка WB, функция make_card_info_url которая позволяет быстро и без нагрузки на апишку продавца получать
   артикула связанных карточек в нужной что бы привязать еще одну. Нужно всегда проверять и прописывать новый host, он
   увеличивается по увеличению карточек на вб, мало прослеживаемая логика между интервалами что бы это
   автоматизировать =(
2) Иногда карточка может не завестись на ВБ (не часто). Нужно проверять на ежедневной основе WbCard таблицу, иногда
   сотрудники могут некорректно заполнить характеристики и карточка попадает в черновики и из-за этого не прогружаютсья
   изображения и не происходит склейка карточек пока не прогрузятся они. Из-за этого задача висит в статусе "В процессе
   загрузки"
3) Если на хостинге кончается место, ломается очередь задач django_apscheduler. Удалять текущие задачи и перезапускать
   сайт.

# Рекомендации к разработке:

1) Загрузка пользовательских файлов не на жеский сайта, а на хранилище. Реализован класс для работы с хранилищем Cloud,
   можно его использовать для реализвации. Раньше использовалосб для загрузки файлов для иморта на сайт на Тильде.
   сейчас за ненадобностью отключил хранилище в лк хостинга.
2) Вывести прогресс загрузки файлов для пользователей
3) Прикрутить Redis, celery
4) Бэкапы и логи тоже можно грузить на S3


# Сбор статических файлов
python backend/manage.py collectstatic

# Планировщик задач Django (APScheduler)

Этот модуль настраивает фоновый планировщик задач для Django-проекта, используя APScheduler.

## Основные функции

### Активные задачи

- **Резервное копирование БД** - ежедневно в 2:00 (`db_backup`)
- **Анализ воронки продаж** - ежедневно в 6:00 (`scan_sales_funnel`)
- **Получение информации о ценах и остатках WB** - ежедневно в 4:00 (`get_info_cards_price_stock`)
- **Сканирование Ozon** - ежедневно в 7:15 (`scan_ozon`)
- **Поиск ошибок WB** - ежедневно в 7:00 (`search_error_wb`)
- **Поиск ошибок Ozon** - ежедневно в 7:25 (`search_error_ozon`)
- **Создание уведомлений о просроченных задачах у сотрудников** - ежедневно в 10:00 (`created_nof_ols_task`)
- **Генерация еженедельных отчетов дизайнеров** - каждую субботу (`generate_daily_reports`)
- **Загрузка файлов задач** - каждые 6 минут (`download_task_file`)
- **Загрузка файлов для редактирования** - каждые 10 минут (в :03, :13, :23 и т.д.) (`download_edit_files`)
- **Создание карточек WB** - каждые 4 минуты (`created_wb_cards`)
- **Объединение карточек WB** - каждые 2 минуты (`join_cards_wb`)
- **Замена изображений** - каждые 46 минут (`replace_image_func`)

### Закомментированные задачи (неактивные)

```python
# Заведение карточек на Ozon (дубли с WB)
# scheduler_online.add_job(
#     main_create_card_ozon,
#     trigger=CronTrigger(minute="*/37"),
#     jobstore="default",
#     id="main_create_card_ozon",
#     replace_existing=True,
#     misfire_grace_time=60,
#     max_instances=1,
# )

# Парсер WB/Ozon (не актуально)
# scheduler_online.add_job(
#     main_parser_wb_ozon,
#     trigger=trigger,
#     jobstore="default",
#     id="main_parser_wb_ozon",
#     replace_existing=True,
#     misfire_grace_time=60,
#     max_instances=1,
# )

# Создание карточек Ozon (не актуально)
# scheduler_online.add_job(
#     main_create_ozon,
#     trigger=trigger2,
#     jobstore="default",
#     id="main_create_ozon",
#     replace_existing=True,
#     misfire_grace_time=60,
#     max_instances=1,
# )

# Создание новых карточек из Tilda (не актуально)
# scheduler_online.add_job(
#     create_new_card_tilda,
#     "cron",
#     hour=4,
#     minute=0,
#     jobstore="default",
#     id="create_new_card_tilda",
#     replace_existing=True,
#     misfire_grace_time=60*10,
#     max_instances=1,
# )

# Заполнение параметров карточек Tilda (не актуально)
# scheduler_online.add_job(
#     filling_parameters_tilda_card,
#     "cron",
#     hour=5,
#     minute=0,
#     jobstore="default",
#     id="filling_parameters_tilda_card",
#     replace_existing=True,
#     misfire_grace_time=60*10,
#     max_instances=1,
# )

# Загрузка файлов на S3 (не актуально)
# scheduler_online.add_job(
#     upload_file_s3,
#     trigger=CronTrigger(minute="*/6"),
#     jobstore="default",
#     id="upload_file_s3",
#     replace_existing=True,
#     misfire_grace_time=60,
#     max_instances=1,
# )

# Создание CSV файлов (не актуально)
# scheduler_online.add_job(
#     create_csv_files,
#     "cron",
#     hour=10,
#     minute=0,
#     jobstore="default",
#     id="create_csv_files",
#     replace_existing=True,
#     misfire_grace_time=60*10,
#     max_instances=1,
# )