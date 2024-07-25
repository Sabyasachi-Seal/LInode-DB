from app.config import settings
from app.constants.enums import DatabaseType
import pkg_resources

# StackScript IDs for different databases
STACKSCRIPTS = {
    DatabaseType.mysql.value: settings.stackscript_mysql,
    DatabaseType.postgresql.value: settings.stackscript_postgresql,
    DatabaseType.mongodb.value: settings.stackscript_mongodb
}

SUPPORTED_DATABASES = [DatabaseType.mysql.value]

MYSQL_BACKUP_SCRIPT = pkg_resources.resource_string("app", "data/mysql_backup.sh").decode("utf-8")