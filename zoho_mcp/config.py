from dataclasses import dataclass
from dotenv import load_dotenv
import os

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
    access_token : str

# We can specify the token here or leave the value as it is. 
# The AI itself will trigger the token refresh tool and the token will be updated.
access_token_config = AccessTokenConfig(access_token='AAA')

def get_access_token() -> str:
    return access_token_config.access_token

def update_access_token(new_access_token : str) -> str:
    access_token_config.access_token = new_access_token
    return new_access_token