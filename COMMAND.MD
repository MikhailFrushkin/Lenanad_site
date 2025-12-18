cd mycego_online #переход в каталог с докер файлом
git pull #загружаем изменения с гита(миграции тоже грузим)
docker compose up --build -d #запуск сборки контейнера, миграции применяются в докер файле 
docker exec -it mycego_online sh #если нужно что то потестить в самом контейнере, открывает консоль из контейнера


docker cp ~/mycego_online/nginx_configs/nginx/conf.d/ nginx_mycego_online:/etc/nginx/conf.d/ #Копирование конфига nginx в указанную папку

docker ps #список активных контейнеров
docker stop $(docker ps -aq)  # Остановить все контейнеры
docker rm $(docker ps -aq)    # Удалить все контейнеры
docker rmi $(docker images -q)  # Удалить все образы
docker volume prune -f  # Удалить все неиспользуемые тома
docker network prune -f  # Удалить все неиспользуемые сети
docker builder prune -f  # Удалить все неиспользуемые кэши сборки

docker system prune -a --volumes -f #чистит все, стопнуть все контейнеры перед этим
-a — удаляет все неиспользуемые образы, не только те, которые не имеют контейнеров.
--volumes — также удаляет все неиспользуемые тома.
-f — принудительно выполняет команду без подтверждения.

docker exec -i mycego_online_db mysqldump --user=root --password=fma160392 mycego_online > /30042025.sql #mycego.online сделать бекап базы в корневой каталог
docker exec -i mysql_db mysqldump --user=root --password=fma160392 mycego_nov > /nov_03052025.sql #mycego.ru сделать бекап базы в корневой каталог
docker exec -i mysql_db mysqldump --user=root --password=fma160392 mycego_nng > /nng_03052025.sql #mycego-novgorod.ru сделать бекап базы в корневой каталог

"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql" -u root -p mycego_online < "G:\backup\crm\14052025.sql" #на своем компе загружаю в свою базу скачанный бэкап
"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql" -u root -p mycego < "G:\backup\Nov\03052025.sql"
#Если есть проблемы с локальной базой и рассинхрон, удаляем полностью, потом восстанавливаем из скачанного файла
"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql" -u root -p #Заходим в локальную базу
DROP DATABASE mycego_online;
CREATE DATABASE mycego_online;


#Создание сертификатов SSL

Далее ssl:
Начну издалека.
ssl-сертификаты не зря называются сертификатами. Это эдакая справка-ключ. Выдавать её могут только сертифицированные центры. 
Один из таких сертифицированных центров (самый популярный) - Let's Encrypt - занимается выдачей сертификатов бесплатно и живёт на пожертвования. У бесплатного сертификата есть минус - центр, его выдавший не даёт никаких гарантий, что ключ не взломают. Чтобы свести риски к минимуму сертификат от LE живёт максимум 90 дней. Сертификат получается через программу certbot
certbot работает с такой штукой как dhparams - это секретный ключ по типу django-secret, который представляет собой огромное (ОГРОМНОЕ) простое число. мы обычно используем int32 или int64, а dhparam обычно генерирует 2048 или 4096 битовое число. Генерация такого числа для миллионов пользователей по всему миру - дело дорогостоящее и не по карману бесплатному центру, поэтому они возлагают такую генерацию на пользователей.

функция генерации dhparam есть в утилите openssl (стандартная либо любого убунту, если нет - всегда можно скачать через apt install) команда для генерации ключа:
openssl dhparam -out /etc/letsencrypt/ssl-dhparams.pem 4096
где -out [путь к файлу] (обычно файлы ключей делают расширением .pem, но можно и .key и .crt)
а 4096 это сколько битовое должно быть число.
генерация может занимать до 10 минут, но задействует всего 1 ядро, так что сайт не рухнет

далее нужно запустить certbot он сделает запрос на сервера letsencrypt, а потом "поймает" запрос от сервера.
этот пинг-понг в LE называют "acme challenge". Делается для того, чтобы центр получил dhparam, и использовал его при генерации сертификатов.
делается командой
certbot certonly --standalone --register-unsafely-without-email -d "${BASE_DOMAIN},www.${BASE_DOMAIN}" --rsa-key-size ${rsa-key-size:-2048} --agree-tos --force-renewal
где —standalone означает 1 запуск, без reverse-proxy типа nginx
--register-unsafely-without-email означает регистрацию без указания электронной почты. unsafely потому, что если кто-то украдёт сертификат - ты не сможешь доказать что это твой сертификат и чужой сайт нужно заблокировать. Происходит крайне редко, и не с сайтами где "все свои".
-d "${BASE_DOMAIN},www.${BASE_DOMAIN}" домены на которые будет выпущен сертификат. через запятую нужно указать все вариации, паттерна типа *.{BASE_DOMAIN} тут нет.
 --rsa-key-size ${rsa-key-size:2048} - устанавливает битовый размер ключа на значение rsa-key-size или на 2048. можно проставить 4096, но на небольшие по кол-ву ползователей сайты - 2048 за глаза.
 --agree-tos принять условия обслуживания
--force-renewal обновить даже если файлы с ключами уже есть (или они пустые и т.п.)

результатом по пути /etc/letsencrypt/live/${BASE_DOMAIN} будут 3 ключа: cert.pem, fullchain.pem и privkey.pem
cert - это корневой сертификат - его мы подключаем в nginx в ssl_trusted_certificate
fullchain - это полный сертификат вместе с промежуточным. его мы подключаем в ssl_certificate, ну и ключ в ssl_certificate_key
закинуть их в /root/mycego_sites/cert_folder/{BASE_DOMAIN}

далее необходимо включить вечный цикл обновления сертификата
trap exit TERM; while :; do certbot renew; sleep 24h && wait $${!}; done;
trap exit TERM - если программа получает сигнал о завершении - выходит из программы
далее цикл, который раз в 24 часа выполняет обновление сертификата. certbot проверяет сертификат, если он уже "прожил" 30 дней - обновляет, в другом случае - не делает ничего. после ждёт 24 часа. wait $${!} обязателен, т.к.  do certbot renew обновляется в фоновом процессе, а wait как раз ждёт фоновый процесс.

чтобы упростить это всё у меня есть docker-compose файл
в файле помимо вышеупомянутых команд есть вот такие:
test -f /etc/letsencrypt/ssl-dhparams.pem ||
тестирует наличие файла/папки. если их нет - выполняет команду после ||
если есть - выходит
таким образом при перезапуске контейнеров не придётся ждать dhparam ил certbot-oneshot

ОДНАКО не на всех системах в контейнере нормально отрабатывает dhparams. я рекомендую сгенерировать его командой выше вручную в папка_проекта/cert_volume
#генерация файлов
certbot certonly --standalone --register-unsafely-without-email -d "mycego.ru,www.mycego.ru" --rsa-key-size 2048 --agree-tos --force-renewal
#Копирование сгенерированных файлов в нужный каталок в папку сайта
sudo cp -f /etc/letsencrypt/archive/mycego.ru/fullchain2.pem /root/mycego_sites/cert_folder/mycego.ru.crt
sudo cp -f /etc/letsencrypt/archive/mycego.ru/privkey2.pem /root/mycego_sites/cert_folder/mycego.ru.key
sudo cp -f /etc/letsencrypt/archive/mycego.ru/chain2.pem /root/mycego_sites/cert_folder/ca.crt



mysqlbinlog "G:\binlog.000106" --result-file="G:\output.txt" --set-charset=utf8mb4 #Преобразование логов базы в файл txt
