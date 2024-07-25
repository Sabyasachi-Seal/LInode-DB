import os
import requests
from dotenv import load_dotenv
from app.setup.db_setup import create_db_and_tables

# Load environment variables from .env file
load_dotenv()

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

def create_database(db_type: str, db_root_password: str, new_user: str, new_user_password: str, instance_type: str, region: str):
    response = requests.post(f"{BASE_URL}/create_database", json={
        "db_type": db_type,
        "db_root_password": db_root_password,
        "new_user": new_user,
        "new_user_password": new_user_password,
        "instance_type": instance_type,
        "region": region,
    })
    assert response.status_code == 200, f"Failed to create database: {response.text}"
    print("Database instance created successfully.")
    return response.json()

def schedule_backup(database_id: str, hour_of_day: int, frequency: str, day_of_week: int = None, day_of_month: int = None):
    response = requests.post(f"{BASE_URL}/schedule_backup/", json={
        "database_id": database_id,
        "hour_of_day": hour_of_day,
        "day_of_week": day_of_week,
        "day_of_month": day_of_month,
        "frequency": frequency
    })
    assert response.status_code == 200, f"Failed to schedule backup: {response.text}"
    print("Backup schedule created successfully.")
    return response.json()

def test_databases():
    res = create_database("mysql", "Webknot@1234", "seal", "Webknot@1234", "g6-nanode-1", "us-east")
    res = schedule_backup(res['instance_id'], 2, "daily")
    print(res)

if __name__ == "__main__":
    # create_db_and_tables()
    test_databases()