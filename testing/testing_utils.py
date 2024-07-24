import os
import requests
from dotenv import load_dotenv
from app.setup.db_setup import create_db_and_tables

# Load environment variables from .env file
load_dotenv()

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

def create_database(db_type: str, db_root_password: str, new_user: str, new_user_password: str, instance_type: str, region: str, backup_schedule: str):
    response = requests.post(f"{BASE_URL}/create_database", json={
        "db_type": db_type,
        "db_root_password": db_root_password,
        "new_user": new_user,
        "new_user_password": new_user_password,
        "instance_type": instance_type,
        "region": region,
        "backup_schedule": backup_schedule
    })
    assert response.status_code == 200, f"Failed to create database: {response.text}"
    print("Database instance created successfully.")
    return response.json()

def test_databases():
    create_database("mysql", "Webknot@1234", "seal", "Webknot@1234", "g6-nanode-1", "us-east", "daily")

if __name__ == "__main__":
    # create_db_and_tables()
    test_databases()