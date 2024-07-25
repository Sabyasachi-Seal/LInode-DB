from app.config import settings
from app.constants.enums import DatabaseType
import pkg_resources

# StackScript IDs for different databases
STACKSCRIPTS = {
    DatabaseType.mysql.value: settings.stackscript_mysql,
    DatabaseType.postgresql.value: settings.stackscript_postgresql,
    DatabaseType.mongodb.value: settings.stackscript_mongodb
}

BACKUP_SCRIPTS = {
    DatabaseType.mysql.value: pkg_resources.resource_string("app", "data/mysql_backup.sh").decode("utf-8")
}

SUPPORTED_DATABASES = [DatabaseType.mysql.value]

AUTHORIZED_KEYS = settings.authorized_keys.split(",") if len (settings.authorized_keys) > 0 else None

INSTANCE_DEFAULT_USER = "root"