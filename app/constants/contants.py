from app.config import settings
from app.constants.enums import DatabaseType
import pkg_resources
from string import Template

# StackScript IDs for different databases
STACKSCRIPTS = {
    DatabaseType.mysql.value: settings.stackscript_mysql,
    DatabaseType.postgresql.value: settings.stackscript_postgresql,
    DatabaseType.mongodb.value: settings.stackscript_mongodb,
}

BACKUP_SCRIPTS = {
    DatabaseType.mysql.value: pkg_resources.resource_string(
        "app", "data/mysql_backup.sh"
    ).decode("utf-8")
}

SUPPORTED_DATABASES = [DatabaseType.mysql.value]

AUTHORIZED_KEYS = (
    settings.authorized_keys.split(",") if len(settings.authorized_keys) > 0 else None
)

INSTANCE_DEFAULT_USER = "root"

BACKUP_SCRIPT_SUFFIXES = {
    DatabaseType.mysql.value: Template(
        "$DB_HOST $DB_USER $DB_PASSWORD $DB_NAME $BUCKET_NAME $OBJECT_STORAGE_REGION $MAX_BACKUPS $BACKUP_FILE_PREFIX $USER_ID $DB_TYPE $DB_ID"
    ),
}

MAX_BACKUP_LIMIT = "7"

BACKUP_SCRIPT_SAVE_PATH = "/usr/local/bin/backup_script.sh"

S3CFG_FILE_PATH = "~/.s3cfg"

S3CFG_CONTENT = Template(
    pkg_resources.resource_string("app", "data/s3cfg.txt").decode("utf-8")
)
