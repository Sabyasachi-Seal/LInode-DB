from linode_api4 import LinodeClient, Instance, Firewall
from app.config import settings
import paramiko
import boto3

client = LinodeClient(settings.linode_token)
ssh_client = paramiko.SSHClient()

linode_obj_config = {
    "aws_access_key_id": settings.linode_db_backup_bucket_access_key,
    "aws_secret_access_key": settings.linode_db_backup_bucket_secret_key,
    "region_name": settings.linode_db_backup_bucket_region,
    "endpoint_url": f"https://{settings.linode_db_backup_bucket_region}.linodeobjects.com",
}

object_storage_client = boto3.client("s3", **linode_obj_config)
