import os
import requests
from dotenv import load_dotenv
from app.setup.db_setup import create_db_and_tables
import time

# Load environment variables from .env file
load_dotenv()

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


def create_database(
    user_id: str,
    db_name: str,
    db_type: str,
    new_user: str,
    new_user_password: str,
    instance_type: str,
    region: str,
):
    response = requests.post(
        f"{BASE_URL}/create_database",
        json={
            "user_id": user_id,
            "db_name": db_name,
            "db_type": db_type,
            "new_user": new_user,
            "new_user_password": new_user_password,
            "instance_type": instance_type,
            "region": region,
        },
    )
    assert response.status_code == 200, f"Failed to create database: {response.text}"
    return response.json()


def list_databases():
    response = requests.get(f"{BASE_URL}/databases")
    assert response.status_code == 200, f"Failed to list databases: {response.text}"
    return response.json()


def get_database(database_id: str):
    response = requests.get(f"{BASE_URL}/databases/{database_id}")
    assert response.status_code == 200, f"Failed to get database: {response.text}"
    return response.json()


def update_database(database_id: str, new_db_name: str, new_instance_type: str):
    response = requests.put(
        f"{BASE_URL}/databases/",
        json={
            "database_id": database_id,
            "database_name": new_db_name,
            "instance_type": new_instance_type,
        },
    )
    assert response.status_code == 200, f"Failed to update database: {response.text}"
    return response.json()


def delete_database(database_id: str):
    response = requests.delete(f"{BASE_URL}/databases/{database_id}")
    assert response.status_code == 200, f"Failed to delete database: {response.text}"
    return response.json()


def schedule_backup(
    database_id: str,
    hour_of_day: int,
    frequency: str,
    day_of_week: int = None,
    day_of_month: int = None,
):
    response = requests.post(
        f"{BASE_URL}/schedule_backup/",
        json={
            "user_id": "1",
            "database_id": database_id,
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week,
            "day_of_month": day_of_month,
            "frequency": frequency,
        },
    )
    assert response.status_code == 200, f"Failed to schedule backup: {response.text}"
    print("Backup schedule created successfully.")
    return response.json()


def get_linode_stats(db_id: str):
    while len(input("Press Enter to get Linode stats...")) == 0:
        response = requests.get(f"{BASE_URL}/databases/{db_id}/stats")
        print(response.json())


def get_linode_health(db_id: str):
    while len(input("Press Enter to get Linode stats...")) == 0:
        response = requests.get(f"{BASE_URL}/databases/{db_id}/health")
        print(response.json())


def list_backups(db_id: str):
    response = requests.get(f"{BASE_URL}/databases/{db_id}/backups")
    assert response.status_code == 200, f"Failed to list backups: {response.text}"
    return response.json()


def delete_backup(backup_id: str):
    response = requests.delete(f"{BASE_URL}/backups", json={"backup_id": backup_id})
    assert response.status_code == 200, f"Failed to delete backup: {response.text}"
    return response.json()


def test_all():
    def controller(func, prompt_text, *args):
        user_input = input(prompt_text)
        if not user_input:
            result = func(*args)
            return result
        else:
            print("Skipped function")

    # s = input("Existing DB ID: ")

    db_id = "4610ab03-31b1-4a4d-a96a-823dc6051044"

    # if not s:
    #     res = controller(
    #         create_database,
    #         "Press Enter to create a database: ",
    #         "1",
    #         "test_mysql_db_something_big_name",
    #         "mysql",
    #         "seal",
    #         "Webknot@1234",
    #         "g6-nanode-1",
    #         "us-east",
    #     )
    #     print(res)
    #     db_id = res["database_id"]
    # else:
    #     db_id = s

    # # Use the controller function to manage operations
    # print(controller(get_database, "Press Enter to get database details: ", db_id))

    # print(
    #     controller(
    #         update_database,
    #         "Press Enter to update database: ",
    #         db_id,
    #         "test_db_mysql_2",
    #         "g6-standard-2",
    #     )
    # )

    # print(
    #     controller(
    #         schedule_backup, "Press Enter to schedule backup: ", db_id, 2, "daily"
    #     )
    # )

    res = controller(list_backups, "Press Enter to list backups: ", db_id)

    print(res)

    print(
        controller(
            delete_backup, "Press Enter to delete backup: ", res["backups"][0]["id"]
        )
    )

    controller(get_linode_stats, "Press Enter to get Linode stats: ", db_id)
    controller(get_linode_health, "Press Enter to get Linode health: ", db_id)

    print(controller(delete_database, "Press Enter to delete database: ", db_id))


if __name__ == "__main__":
    # create_db_and_tables()
    test_all()
