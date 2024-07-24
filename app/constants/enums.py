from enum import Enum

class DatabaseType(str, Enum):
    mysql = "mysql"
    postgresql = "postgresql"
    mongodb = "mongodb"

class InstanceType(str, Enum):
    nanode_1 = "g6-nanode-1"
    standard_1 = "g6-standard-1"
    standard_2 = "g6-standard-2"
    highmem_1 = "g6-highmem-1"
    highmem_2 = "g6-highmem-2"

class Region(str, Enum):
    us_east = "us-east"
    us_west = "us-west"
    eu_central = "eu-central"
    ap_southeast = "ap-southeast"

class BackupSchedule(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"

class BackupStatus(Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    FAILED = "failed"