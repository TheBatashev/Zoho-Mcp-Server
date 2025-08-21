from mcp.server.fastmcp import FastMCP
import requests
import json

from zoho_mcp.config import get_zoho_config, get_access_token, update_access_token

from dotenv import load_dotenv, find_dotenv
import os
import traceback

load_dotenv(find_dotenv(), override=False)

mcp = FastMCP("Demo")


@mcp.tool(name='Zoho MCP - refresh token')
def refresh_token():
    zoho_config = get_zoho_config()
    base_url_acc = 'https://accounts.zoho.eu'
    path = '/oauth/v2/token'
    params = {
        'grant_type': 'refresh_token',
        'client_id': zoho_config.client_id,
        'client_secret': zoho_config.client_secret,
        'refresh_token': zoho_config.refresh_token
    }

    response = requests.post(base_url_acc + path, data=params)
    try:
        json_resp =  response.json()
        access_token = json_resp['access_token']
        is_created = update_access_token(access_token)
        if is_created :
            return {
                'status_code': response.status_code,
                'error' : None
            }
        else:
            raise RuntimeError('Error when updating the token')

    except Exception as ex:
        return {
            'status_code' : response.status_code,
            'error' : f'{ex} \n {traceback.format_exc()}'
        }

@mcp.tool()
def get_module_data(ctx, module_name: str = None):
    """
    Fetch data from Zoho CRM modules
    
    Args:
        module_name: Specific module name (e.g., 'Contacts', 'Leads'). 
                    If None, fetches from all modules.
    """
    access_token = get_access_token()
    zoho_config = get_zoho_config()
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    if module_name:
        url = f"{zoho_config.base_url}/{module_name}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json().get("data", [])
            return {
                "status": "success",
                "module": module_name,
                "count": len(data),
                "data": data
            }
        else:
            return {
                "status": "error",
                "module": module_name,
                "message": response.text,
                "code": response.status_code
            }
    else:
        all_data = {}
        errors = []
        
        for module in zoho_config.modules:
            url = f"{zoho_config.base_url}/{module}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json().get("data", [])
                all_data[module] = {
                    "count": len(data),
                    "data": data
                }
            else:
                errors.append({
                    "module": module,
                    "code": response.status_code,
                    "message": response.text
                })
        
        return {
            "status": "success",
            "modules_fetched": len(all_data),
            "total_records": sum(module_data["count"] for module_data in all_data.values()),
            "data": all_data,
            "errors": errors if errors else None
        }

@mcp.tool()
def get_available_modules(ctx):
    """Get list of all available modules in Zoho CRM"""
    access_token = get_access_token()
    zoho_config = get_zoho_config()
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    url = f"{zoho_config.base_url}/settings/modules"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        modules = response.json().get("modules", [])
        return {
            "status": "success",
            "count": len(modules),
            "modules": [module["api_name"] for module in modules]
        }
    else:
        return {
            "status": "error",
            "message": response.text,
            "code": response.status_code
        }

@mcp.tool()
def search_records(ctx, module_name: str, search_criteria: str):
    """
    Search for records in a specific module
    
    Args:
        module_name: Module to search in (e.g., 'Contacts', 'Leads')
        search_criteria: Search query (e.g., 'email:john@example.com')
    """
    access_token = get_access_token()
    zoho_config = get_zoho_config()

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    url = f"{zoho_config.base_url}/{module_name}/search"
    params = {"criteria": search_criteria}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json().get("data", [])
        return {
            "status": "success",
            "module": module_name,
            "count": len(data),
            "data": data
        }
    else:
        return {
            "status": "error",
            "module": module_name,
            "message": response.text,
            "code": response.status_code
        }

@mcp.tool()
def create_record(ctx, module_name: str, record_data: dict):
    """
    Create a new record in a specific module
    
    Args:
        module_name: Module to create record in (e.g., 'Contacts', 'Leads')
        record_data: Dictionary containing the record fields and values
                    Example: {"First_Name": "John", "Last_Name": "Doe", "Email": "john@example.com"}
    """
    access_token = get_access_token()
    zoho_config = get_zoho_config()

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    url = f"{zoho_config.base_url}/{module_name}"
    
    # Wrap the record data in the required format
    payload = {
        "data": [record_data]
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 201:
        result = response.json()
        return {
            "status": "success",
            "module": module_name,
            "message": "Record created successfully",
            "data": result.get("data", [])
        }
    else:
        return {
            "status": "error",
            "module": module_name,
            "message": response.text,
            "code": response.status_code
        }

@mcp.tool()
def update_record(ctx, module_name: str, record_id: str, record_data: dict):
    """
    Update an existing record in a specific module
    
    Args:
        module_name: Module containing the record (e.g., 'Contacts', 'Leads')
        record_id: ID of the record to update
        record_data: Dictionary containing the fields to update and their new values
                    Example: {"First_Name": "Jane", "Email": "jane@example.com"}
    """
    access_token = get_access_token()
    zoho_config = get_zoho_config()

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    url = f"{zoho_config.base_url}/{module_name}/{record_id}"
    
    # Add the record ID to the data
    record_data["id"] = record_id
    
    # Wrap the record data in the required format
    payload = {
        "data": [record_data]
    }
    
    response = requests.put(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        result = response.json()
        return {
            "status": "success",
            "module": module_name,
            "record_id": record_id,
            "message": "Record updated successfully",
            "data": result.get("data", [])
        }
    else:
        return {
            "status": "error",
            "module": module_name,
            "record_id": record_id,
            "message": response.text,
            "code": response.status_code
        }

@mcp.tool()
def delete_record(ctx, module_name: str, record_id: str):
    """
    Delete a record from a specific module
    
    Args:
        module_name: Module containing the record (e.g., 'Contacts', 'Leads')
        record_id: ID of the record to delete
    """
    access_token = get_access_token()
    zoho_config = get_zoho_config()

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    url = f"{zoho_config.base_url}/{module_name}/{record_id}"
    
    response = requests.delete(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        return {
            "status": "success",
            "module": module_name,
            "record_id": record_id,
            "message": "Record deleted successfully",
            "data": result.get("data", [])
        }
    else:
        return {
            "status": "error",
            "module": module_name,
            "record_id": record_id,
            "message": response.text,
            "code": response.status_code
        }

@mcp.tool()
def bulk_create_records(ctx, module_name: str, records_data: list):
    """
    Create multiple records in a specific module
    
    Args:
        module_name: Module to create records in (e.g., 'Contacts', 'Leads')
        records_data: List of dictionaries containing record data
                     Example: [{"First_Name": "John", "Last_Name": "Doe"}, {"First_Name": "Jane", "Last_Name": "Smith"}]
    """
    access_token = get_access_token()
    zoho_config = get_zoho_config()

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    url = f"{zoho_config.base_url}/{module_name}"
    
    # Zoho CRM allows up to 100 records per API call
    if len(records_data) > 100:
        return {
            "status": "error",
            "message": "Maximum 100 records allowed per bulk operation"
        }
    
    payload = {
        "data": records_data
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 201:
        result = response.json()
        return {
            "status": "success",
            "module": module_name,
            "message": f"{len(records_data)} records created successfully",
            "data": result.get("data", [])
        }
    else:
        return {
            "status": "error",
            "module": module_name,
            "message": response.text,
            "code": response.status_code
        }

@mcp.tool()
def get_record_by_id(ctx, module_name: str, record_id: str):
    """
    Get a specific record by its ID
    
    Args:
        module_name: Module containing the record (e.g., 'Contacts', 'Leads')
        record_id: ID of the record to retrieve
    """
    access_token = get_access_token()
    zoho_config = get_zoho_config()

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    url = f"{zoho_config.base_url}/{module_name}/{record_id}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        data = result.get("data", [])
        return {
            "status": "success",
            "module": module_name,
            "record_id": record_id,
            "data": data[0] if data else None
        }
    else:
        return {
            "status": "error",
            "module": module_name,
            "record_id": record_id,
            "message": response.text,
            "code": response.status_code
        }

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


def run():
    mcp.run()

if __name__ == "__main__":
    # mcp.run()
    run()