from dataclasses import dataclass
from dotenv import load_dotenv
import os
import time

load_dotenv()

@dataclass
class ZohoConfig:
    base_url : str
    refresh_token : str
    client_id : str
    client_secret : str
    modules : list[str]



def get_zoho_config():
    zoho_config = ZohoConfig(
        base_url=os.getenv('ZOHO_BASE_API_URL','https://www.zohoapis.eu/crm/v2'),
        refresh_token=os.getenv('ZOHO_REFRESH_TOKEN'),
        client_id=os.getenv('ZOHO_CLIENT_ID'),
        client_secret=os.getenv('ZOHO_CLIENT_SECRET'),
        modules = [
            "Leads",
            "Accounts", 
            "Contacts",
            "Deals"
        ]

    )
    return zoho_config


@dataclass
class AccessTokenConfig:
    access_token: str
    token_timestamp: float = 0.0  # Время получения токена в секундах

# We can specify the token here or leave the value as it is. 
# Token will be automatically refreshed when needed.
access_token_config = AccessTokenConfig(access_token='AAA', token_timestamp=0.0)

def get_access_token() -> str:
    return access_token_config.access_token

def update_access_token(new_access_token: str) -> str:
    """Обновляет токен и сохраняет время получения"""
    access_token_config.access_token = new_access_token
    access_token_config.token_timestamp = time.time()
    return new_access_token

def is_token_expired() -> bool:
    """Проверяет, истек ли токен (3600 секунд = 1 час)"""
    if access_token_config.token_timestamp == 0.0:
        return True  # Токен не был получен
    
    current_time = time.time()
    elapsed_time = current_time - access_token_config.token_timestamp
    return elapsed_time >= 3600  # 1 час в секундах