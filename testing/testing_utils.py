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
    input("Press Enter to list databases...")
    response = requests.get(f"{BASE_URL}/databases")
    assert response.status_code == 200, f"Failed to list databases: {response.text}"
    return response.json()


def get_database(database_id: str):
    input("Press Enter to get the database...")
    response = requests.get(f"{BASE_URL}/databases/{database_id}")
    assert response.status_code == 200, f"Failed to get database: {response.text}"
    return response.json()


def update_database(database_id: str, new_db_name: str, new_instance_type: str):
    input("Press Enter to update the database...")
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
    input("Press Enter to delete the database...")
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
    input("Press Enter to create a backup schedule...")
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


def test_databases():

    s = input("Existing DB Id ?")

    if not s:

        res = create_database(
            "1",
            "test_mysql_db_something_big_name",
            "mysql",
            "seal",
            "Webknot@1234",
            "g6-nanode-1",
            "us-east",
        )

        print(res)

        db_id = res["database_id"]

    else:
        db_id = s

    print(list_databases())

    print(get_database(db_id))

    print(update_database(db_id, "test_db_mysql_2", "g6-standard-2"))

    print(schedule_backup(db_id, 2, "daily"))

    print(delete_database(db_id))


if __name__ == "__main__":
    # create_db_and_tables()
    test_databases()
