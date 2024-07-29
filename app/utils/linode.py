from app.constants.contants import (
    STACKSCRIPTS,
    SUPPORTED_DATABASES,
    AUTHORIZED_KEYS,
    BACKUP_SCRIPTS,
    INSTANCE_DEFAULT_USER,
    BACKUP_SCRIPT_SUFFIXES,
    MAX_BACKUP_LIMIT,
    BACKUP_SCRIPT_SAVE_PATH,
    S3CFG_CONTENT,
)
from app.resources.resources import client, ssh_client, paramiko, Instance
from app.constants.enums import DatabaseType
from app.config import settings


def get_backup_script_content(db_type: str):
    if db_type in SUPPORTED_DATABASES:
        return BACKUP_SCRIPTS[db_type]
    else:
        raise NotImplementedError(
            f"Backup script for database type {db_type} is not implemented."
        )


def get_server_ip(instance_id: str) -> str:
    try:
        instance = client.load(Instance, instance_id)
        # Assuming you want the public IPv4 address
        ip_address = instance.ipv4[0] if instance.ipv4 else None
        if not ip_address:
            raise ValueError("No public IPv4 address found for the instance.")
        return ip_address
    except Exception as e:
        raise ValueError(
            f"Error retrieving IP address for instance {instance_id}: {str(e)}"
        )


def create_linode_instance(
    label,
    db_type,
    instance_root_password,
    db_root_password,
    new_user,
    new_user_password,
    instance_type,
    region,
    new_user_host="%",
):

    stackscript_data = {
        "ROOT_PASSWORD": db_root_password,
        "NEW_USER": new_user,
        "NEW_USER_PASSWORD": new_user_password,
        "NEW_USER_HOST": new_user_host,
        "S3CFG_CONTENT": S3CFG_CONTENT.substitute(
            {
                "ACCESS_KEY": settings.linode_db_backup_bucket_access_key,
                "SECRET_KEY": settings.linode_db_backup_bucket_secret_key,
            }
        ),
    }

    if db_type not in SUPPORTED_DATABASES:
        raise NotImplementedError(f"Database type {db_type} is not supported.")

    instance = client.linode.instance_create(
        ltype=instance_type,
        region=region,
        image="linode/ubuntu22.04",  # NOTE - add more images ?
        label=label,
        root_pass=instance_root_password,
        stackscript_id=STACKSCRIPTS[db_type],
        stackscript_data=stackscript_data,
        authorized_keys=AUTHORIZED_KEYS,
    )

    return instance


def update_linode_instance(instance_id: str, instance_type: str, region: str):
    try:
        instance = client.load(Instance, instance_id)
        instance.type = instance_type
        instance.region = region
        instance.save()
    except Exception as e:
        raise ValueError(f"Error updating Linode instance {instance_id}: {str(e)}")


def delete_linode_instance(instance_id: str):
    try:
        instance = client.load(Instance, instance_id)
        instance.delete()
    except Exception as e:
        raise ValueError(f"Error deleting Linode instance {instance_id}: {str(e)}")


def deploy_backup_script(
    user_id: str,
    instance_id: str,
    db_type: str,
    cron_schedule: str,
    ssh_password: str,
    db_password: str,
    db_name: str = "all",
    ssh_username: str = INSTANCE_DEFAULT_USER,
):

    def add_cron_job_suffix():
        suffix = BACKUP_SCRIPT_SUFFIXES[db_type]
        final_suffix = suffix.substitute(
            {
                "DB_HOST": "localhost",
                "DB_USER": "root",
                "DB_PASSWORD": db_password,
                "DB_NAME": db_name,
                "BUCKET_NAME": settings.linode_db_backup_bucket,
                "OBJECT_STORAGE_REGION": settings.linode_db_backup_bucket_region,
                "MAX_BACKUPS": MAX_BACKUP_LIMIT,
                "BACKUP_FILE_PREFIX": instance_id,
                "USER_ID": user_id,
                "DB_TYPE": db_type,
            }
        )

        return final_suffix

    server_ip = get_server_ip(instance_id)

    backup_script_content = get_backup_script_content(db_type)

    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:

        ssh_client.connect(server_ip, username=ssh_username, password=ssh_password)

        # Transfer the backup script
        sftp = ssh_client.open_sftp()
        script_path = BACKUP_SCRIPT_SAVE_PATH
        with sftp.file(script_path, "w") as script_file:
            script_file.write(backup_script_content)
        sftp.chmod(script_path, 755)
        sftp.close()

        # Add the cron job
        cron_command = f'(crontab -l 2>/dev/null; echo "{cron_schedule} {script_path} {add_cron_job_suffix()}") | crontab -'

        print(cron_command)

        _, _, stderr = ssh_client.exec_command(cron_command)
        errors = stderr.read().decode()
        if errors:
            raise ValueError(f"Failed to add cron job: {errors}")

        print("Backup script deployed and cron job added successfully.")
        ssh_client.close()
        return 0
    except Exception as e:
        print(f"Error deploying backup script: {e}")
        ssh_client.close()
        return 1
