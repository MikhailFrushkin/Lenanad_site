set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${DATE}.sql.gz"

echo "Создание бекапа базы данных..."

# Создаем директорию для бекапов
mkdir -p ${BACKUP_DIR}

# Создаем дамп базы данных
docker exec django_db pg_dumpall -U admin_user -c | gzip > ${BACKUP_FILE}

# Проверяем успешность
if [ $? -eq 0 ]; then
    echo "Бекап успешно создан: ${BACKUP_FILE}"

    # Удаляем старые бекапы (старше 30 дней)
    find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete
    echo "Старые бекапы (старше 30 дней) удалены"
else
    echo "Ошибка при создании бекапа!"
    exit 1
fi