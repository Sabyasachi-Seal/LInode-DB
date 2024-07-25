from linode_api4 import LinodeClient
from app.config import settings

client = LinodeClient(settings.linode_token)
