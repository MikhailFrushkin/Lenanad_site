-- init-db.sql
-- Создаем базу данных если она еще не существует
SELECT 'CREATE DATABASE lemana_pro_online'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'lemana_pro_online')\gexec

-- Подключаемся к базе данных
\c lemana_pro_online;

-- Предоставляем права пользователю
GRANT ALL ON SCHEMA public TO admin_user;
GRANT CREATE ON SCHEMA public TO admin_user;
GRANT ALL PRIVILEGES ON DATABASE lemana_pro_online TO admin_user;