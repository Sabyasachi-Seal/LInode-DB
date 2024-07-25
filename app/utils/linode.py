from app.constants.contants import STACKSCRIPTS
from app.constants.contants import SUPPORTED_DATABASES
from app.resources.resources import client
def create_linode_instance(label, db_type, db_root_password, new_user, new_user_password, instance_type, region):
    stackscript_data = {
        "MYSQL_ROOT_PASSWORD": db_root_password,
        "NEW_USER": new_user,
        "NEW_USER_PASSWORD": new_user_password,
        "NEW_USER_HOST": "%" # NOTE - allow option to restrict host
    }
    if db_type not in SUPPORTED_DATABASES:
        raise NotImplementedError(f"Database type {db_type} is not supported.")

    instance = client.linode.instance_create(
        ltype=instance_type,
        region=region,
        image="linode/ubuntu22.04", # NOTE - add more images ?
        label=label,
        root_pass=db_root_password,
        stackscript_id=STACKSCRIPTS[db_type],
        stackscript_data=stackscript_data
    )

    return instance