from linode_api4 import LinodeClient

# StackScript IDs for different databases
STACKSCRIPTS = {
    "mysql": 123456,  # Replace with your MySQL StackScript ID
    "postgresql": 123457,  # Replace with your PostgreSQL StackScript ID
    "mongodb": 123458  # Replace with your MongoDB StackScript ID
}

client = LinodeClient("your_linode_api_token")

def create_linode_instance(label, db_type, db_root_password, new_user, new_user_password, new_db):
    stackscript_data = {
        "db_root_password": db_root_password,
        "new_user": new_user,
        "new_user_password": new_user_password,
    }
    if db_type != "mysql":
        stackscript_data["new_db"] = new_db

    instance = client.linode.instance_create(
        type="g6-nanode-1",
        region="us-east",
        image="linode/ubuntu20.04",
        label=label,
        root_pass=db_root_password,
        stackscript_id=STACKSCRIPTS[db_type],
        stackscript_data=stackscript_data
    )
    return instance