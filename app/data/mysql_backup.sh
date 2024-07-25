#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -lt 8 ] || [ "$#" -gt 9 ]; then
    echo "Usage: $0 <DB_HOST> <DB_USER> <DB_PASSWORD> <DB_NAME> <BUCKET_NAME> <OBJECT_STORAGE_REGION> <MAX_BACKUPS> <BACKUP_FILE_PREFIX> [OPTIONAL_LIFECYCLE_POLICY_PATH]"
    exit 1
fi

# Assigning passed arguments to variables
DB_HOST="$1"
DB_USER="$2"
DB_PASSWORD="$3"
DB_NAME="$4"
BUCKET_NAME="$5"
OBJECT_STORAGE_REGION="$6"
MAX_BACKUPS="$7"
BACKUP_FILE_PREFIX="$8"
LIFECYCLE_CONFIG_PATH="${9:-}" # Optional ninth argument

if [ "$DB_NAME" == "all" ]; then
	DB_NAME="--all-databases"
fi

# Backup filename
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="/tmp/${BACKUP_FILE_PREFIX}_${DATE}.sql"
COMPRESSED_BACKUP_FILE="${BACKUP_FILE}.gz"

# Create a MySQL database backup from a remote host
mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Database backup was successful."
else
    echo "Database backup failed."
    exit 1
fi

# Compress the backup file
gzip "$BACKUP_FILE"
echo "Backup file compressed."

# Upload the compressed backup to Linode Object Storage using s4cmd
s4cmd put "$COMPRESSED_BACKUP_FILE" s3://"$BUCKET_NAME"/ --endpoint-url=https://"$OBJECT_STORAGE_REGION".linodeobjects.com

if [ $? -eq 0 ]; then
    echo "Compressed backup successfully uploaded to Linode Object Storage."
else
    echo "Failed to upload compressed backup to Linode Object Storage."
    exit 1
fi

# Optional: Remove the local compressed backup file to save space
rm "$COMPRESSED_BACKUP_FILE"

# Managing the retention of backups
# List and count the backups
BACKUP_LIST=$(s4cmd ls s3://"$BUCKET_NAME"/ --endpoint-url=https://"$OBJECT_STORAGE_REGION".linodeobjects.com | grep "$BACKUP_FILE_PREFIX" | grep ".gz" | sort)
BACKUP_COUNT=$(echo "$BACKUP_LIST" | wc -l)

# If we have more than MAX_BACKUPS, delete the oldest
while [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; do
    OLDEST_BACKUP=$(echo "$BACKUP_LIST" | head -n 1 | awk '{print $4}')
    if [ ! -z "$OLDEST_BACKUP" ]; then
        s4cmd del "$OLDEST_BACKUP" --endpoint-url=https://"$OBJECT_STORAGE_REGION".linodeobjects.com
        echo "Deleted old compressed backup: $OLDEST_BACKUP"
    fi
    BACKUP_LIST=$(s4cmd ls s3://"$BUCKET_NAME"/ --endpoint-url=https://"$OBJECT_STORAGE_REGION".linodeobjects.com | grep "$BACKUP_FILE_PREFIX" | grep ".gz" | sort)
    BACKUP_COUNT=$(echo "$BACKUP_LIST" | wc -l)
done

# Apply lifecycle configuration if a config path is provided
if [ ! -z "$LIFECYCLE_CONFIG_PATH" ]; then
    if s3cmd setlifecycle "$LIFECYCLE_CONFIG_PATH" s3://"$BUCKET_NAME"/ --host=https://"$OBJECT_STORAGE_REGION".linodeobjects.com; then
        echo "Lifecycle policy applied successfully."
    else
        echo "Failed to apply lifecycle policy."
        exit 1
    fi
fi