import os
import requests
from dotenv import load_dotenv
from app.setup.db_setup import create_db_and_tables
# Load environment variables from .env file
load_dotenv()

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
MYSQL_ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD", "rootpassword")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "testdb")
MYSQL_USER = os.getenv("MYSQL_USER", "testuser")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "testpassword")

def register_user(email: str, password: str):
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password
    })
    assert response.status_code == 201, f"Failed to register user: {response.text}"
    print("User registered successfully.")
    return response.json()

def login_user(email: str, password: str):
    response = requests.post(f"{BASE_URL}/auth/jwt/login", json={
        "username": email,
        "password": password
    })
    assert response.status_code == 200, f"Failed to login: {response.text}"
    jwt_token = response.json()["access_token"]
    print("User logged in successfully.")
    return jwt_token

def create_database(jwt_token: str, db_type: str, db_root_password: str, new_user: str, new_user_password: str, new_db: str, instance_type: str, region: str, backup_schedule: str):
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = requests.post(f"{BASE_URL}/create_database", json={
        "db_type": db_type,
        "db_root_password": db_root_password,
        "new_user": new_user,
        "new_user_password": new_user_password,
        "new_db": new_db,
        "instance_type": instance_type,
        "region": region,
        "backup_schedule": backup_schedule
    }, headers=headers)
    assert response.status_code == 200, f"Failed to create database: {response.text}"
    print("Database instance created successfully.")
    return response.json()

def test_users():
    email = "test@example.com"
    password = "password"
    register_user(email, password)
    jwt_token = login_user(email, password)
    return jwt_token

def test_databases(jwt_token: str):
    create_database(jwt_token, "mysql", MYSQL_ROOT_PASSWORD, "newuser", "newuserpassword", "newdatabase", "g6-nanode-1", "us-east", "daily")

if __name__ == "__main__":
    create_db_and_tables()
    # jwt_token = test_users()
    # test_databases(jwt_token)