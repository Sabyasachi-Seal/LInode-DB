#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -lt 11 ] || [ "$#" -gt 11 ]; then
    echo "Usage: $0 <DB_HOST> <DB_USER> <DB_PASSWORD> <DB_NAME> <BUCKET_NAME> <OBJECT_STORAGE_REGION> <MAX_DAYS_BACKUPS> <BACKUP_FILE_PREFIX> <USER_ID> <DB_TYPE> <DB_ID>"
    exit 1
fi

perform_backup() {
    # Assigning passed arguments to variables
    DB_HOST="$1"
    DB_USER="$2"
    DB_PASSWORD="$3"
    DB_NAME="$4"
    BUCKET_NAME="$5"
    OBJECT_STORAGE_REGION="$6"
    MAX_BACKUPS="$7"
    BACKUP_FILE_PREFIX="$8"
    USER_ID="$9"
    DB_TYPE="${10}"
    DB_ID="${11}"

    if [ "$DB_NAME" == "all" ]; then
        DB_NAME="--all-databases"
    fi

    LOG_DIR="/logs"

    # Backup filename
    DATE=$(date +%Y-%m-%d_%H-%M-%S)
    YEAR=$(date +%Y)
    MONTH=$(date +%m)
    BACKUP_FILE="/tmp/${BACKUP_FILE_PREFIX}_${DATE}.sql"
    COMPRESSED_BACKUP_FILE="${BACKUP_FILE_PREFIX}_${DATE}.gz"
    LOCAL_LOG_FILE="/tmp/${DATE}_backup.log"
    LOG_FILE_PATH="logs/${DB_TYPE}/${USER_ID}/${DB_ID}/${YEAR}/${MONTH}/${DATE}_backup.log"

    # Function to log messages
    log_message() {
        echo "$(date +%Y-%m-%d_%H-%M-%S) - $1" >> "$LOCAL_LOG_FILE"
        echo $1
    }

    # Create a MySQL database backup from a remote host
    mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE"

    if [ $? -eq 0 ]; then
        log_message "Database backup was successful."
    else
        log_message "Database backup failed."
    fi

    # Compress the backup file
    log_message "Compressing the backup file..."
    gzip -c "$BACKUP_FILE" > "/tmp/${COMPRESSED_BACKUP_FILE}"
    log_message "Backup file compressed."

    TARGET_PATH="s3://${BUCKET_NAME}/${DB_TYPE}/${USER_ID}/${DB_ID}/${YEAR}/${MONTH}/${COMPRESSED_BACKUP_FILE}"
    s4cmd put "/tmp/${COMPRESSED_BACKUP_FILE}" "$TARGET_PATH" --endpoint-url=https://"$OBJECT_STORAGE_REGION".linodeobjects.com

    if [ $? -eq 0 ]; then
        log_message "Compressed backup successfully uploaded to Linode Object Storage."
    else
        log_message "Failed to upload compressed backup to Linode Object Storage."
    fi

    # Optional: Remove the local compressed backup file to save space
    rm "/tmp/${COMPRESSED_BACKUP_FILE}"

    # Managing the retention of backups

    # If we have more than MAX_BACKUPS, delete the oldest
    # Calculate the cutoff date. Files older than this date will be deleted.
    CUTOFF_DATE=$(date -d "-$MAX_BACKUPS days" +%Y-%m-%d)

    # List all backup files in the specific database backup directory
    BACKUP_DIR="$DB_TYPE/$USER_ID/$DB_ID"
    log_message "Checking for old backups in the $BACKUP_DIR directory..."
    BACKUP_FILES=$(s4cmd ls s3://$BUCKET_NAME/$BACKUP_DIR/ --endpoint-url=https://$OBJECT_STORAGE_REGION.linodeobjects.com)

    log_message "Checking for backups older than $MAX_BACKUPS days..."

    # Iterate through the list of backup files
    echo "$BACKUP_FILES" | while read -r line; do
        # Extract the full path of the backup file
        BACKUP_PATH=$(echo "$line" | awk '{print $4}')
        # if backup path is empty, skip the iteration
        if [ -z "$BACKUP_PATH" ]; then
            continue
        fi

        # Extract the timestamp from the backup file name
        BACKUP_TIMESTAMP=$(basename "$BACKUP_PATH" .gz | awk -F '_' '{print $2}')

        # Compare the backup timestamp to the cutoff date
        if [[ "$BACKUP_TIMESTAMP" < "$CUTOFF_DATE" ]]; then
            # Delete backups older than the cutoff date
            log_message "Deleting old backup: $BACKUP_PATH"
            s4cmd del "$BACKUP_PATH" --endpoint-url=https://$OBJECT_STORAGE_REGION.linodeobjects.com
        fi
    done

    log_message "Old backup cleanup complete."

    log_message "Uploading log file to Linode Object Storage."

    s4cmd put "$LOCAL_LOG_FILE" "s3://${BUCKET_NAME}/${LOG_FILE_PATH}" --endpoint-url=https://"$OBJECT_STORAGE_REGION".linodeobjects.com

    if [ $? -eq 0 ]; then
        echo "Log file successfully uploaded to Linode Object Storage."
    else
        echo "Failed to upload log file to Linode Object Storage."
    fi

    # Cleanup local log file
    rm "$LOCAL_LOG_FILE"
}

perform_backup "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9" "${10}" "${11}"
if [ $? -ne 0 ]; then
    echo "An error occurred while backup."
fi