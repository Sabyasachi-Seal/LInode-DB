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
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from datetime import datetime


def get_unique_instance_name(id: str, db_name: str):
    db_name.replace(".", "-")
    return f"{db_name}.{id[:8]}.{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


def get_instance_name_from_label(label: str):
    return label.split(".")[0]


def delete_all_objects_from_folder(
    bucket_name: str = settings.linode_db_backup_bucket, folder: str = ""
):

    linode_obj_config = {
        "aws_access_key_id": settings.linode_db_backup_bucket_access_key,
        "aws_secret_access_key": settings.linode_db_backup_bucket_secret_key,
        "region_name": settings.linode_db_backup_bucket_region,
        "endpoint_url": f"https://{settings.linode_db_backup_bucket_region}.linodeobjects.com",
    }

    s3_client = boto3.client("s3", **linode_obj_config)

    try:
        # List all objects in the specified bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder)

        if "Contents" in response:
            for obj in response["Contents"]:
                # Delete each object
                s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])
    except NoCredentialsError:
        print("Credentials not available.")
    except PartialCredentialsError:
        print("Incomplete credentials provided.")
    except Exception as e:
        print(f"An error occurred: {e}")


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


def get_instance_status(instance_id: str):
    try:
        instance: Instance = client.load(Instance, instance_id)
        return instance.status
    except Exception as e:
        raise ValueError(
            f"Error retrieving status for Linode instance {instance_id}: {str(e)}"
        )


def get_linode_stats(instance_id: str):
    try:

        instance: Instance = client.load(Instance, instance_id)
        try:
            stats = instance.stats
            stats = stats.get("data", {})
            stats["status"] = True
        except Exception as e:
            stats = {"status": False, "error": str(e)}
        return stats
    except Exception as e:
        print(e)
        raise ValueError(
            f"Error retrieving stats for Linode instance {instance_id}: {str(e)}"
        )


def update_linode_instance(
    instance_id: str, instance_type: str = None, instance_name: str = None
):
    try:
        instance: Instance = client.load(Instance, instance_id)

        if instance_type:
            status = instance.resize(instance_type)
            if not status:
                print(
                    f"Failed to resize Linode instance {instance_id} to {instance_type}"
                )

        instance.label = instance_name if instance_name else instance.label
        instance.save()
    except Exception as e:
        raise ValueError(f"Error updating Linode instance {instance_id}: {str(e)}")


def delete_linode_instance(instance_id: str):
    try:
        instance = client.load(Instance, instance_id)
        instance.delete()
    except Exception as e:
        raise ValueError(f"Error deleting Linode instance {instance_id}: {str(e)}")


def get_linode_instance_details(instance_id: str) -> dict:
    try:
        instance = client.load(Instance, instance_id)
        instance_details = {
            "label": instance.label,
            "specs": {
                "disk": instance.specs.disk,
                "gpus": instance.specs.gpus,
                "memory": instance.specs.memory,
                "transfer": instance.specs.transfer,
                "vcpus": instance.specs.vcpus,
            },
            "status": instance.status,
        }
        return instance_details
    except Exception as e:
        raise ValueError(f"Error retrieving Linode instance {instance_id}: {str(e)}")


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
