from linode_api4 import LinodeClient
from app.config import settings

# StackScript IDs for different databases
STACKSCRIPTS = {
    "mysql": settings.stackscript_mysql,
    "postgresql": settings.stackscript_postgresql,
    "mongodb": settings.stackscript_mongodb
}

client = LinodeClient(settings.linode_token)

def create_linode_instance(label, db_type, db_root_password, new_user, new_user_password, instance_type, region):
    stackscript_data = {
        "db_root_password": db_root_password,
        "new_user": new_user,
        "new_user_password": new_user_password,
        "new_user_host": "%"
    }
    if db_type not in  ["mysql"]:
        raise NotImplementedError(f"Database type {db_type} is not supported.")

    instance = client.linode.instance_create(
        ltype=instance_type,
        region=region,
        image="linode/ubuntu22.04",
        label=label,
        root_pass=db_root_password,
        stackscript_id=STACKSCRIPTS[db_type],
        stackscript_data=stackscript_data
    )

    return instance