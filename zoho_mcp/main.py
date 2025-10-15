from mcp.server.fastmcp import FastMCP
import requests
import json

from zoho_mcp.config import get_zoho_config, get_access_token, update_access_token, is_token_expired

from dotenv import load_dotenv
import os
import traceback

load_dotenv()

mcp = FastMCP("Demo")


def refresh_token():
    """Обновляет access token используя refresh token"""
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
        json_resp = response.json()
        access_token = json_resp['access_token']
        update_access_token(access_token)
        return True
    except Exception as ex:
        print(f"Ошибка обновления токена: {ex}")
        return False

def ensure_valid_token():
    """Проверяет валидность токена и обновляет его при необходимости"""
    if is_token_expired():
        if not refresh_token():
            raise RuntimeError("Не удалось обновить токен доступа")

@mcp.tool()
def get_module_data(ctx, module_name: str = None, limit: int = 10, offset: int = 0):
    """
    Fetch data from Zoho CRM modules
    
    Args:
        module_name: Specific module name (e.g., 'Contacts', 'Leads'). 
                    If None, fetches from all modules.
        limit: Maximum number of records to return per module (default: 10, max: 200)
        offset: Number of records to skip (default: 0)
    """
    ensure_valid_token()
    access_token = get_access_token()
    zoho_config = get_zoho_config()
    
    # Ограничиваем limit максимальным значением 200 (первая страница Zoho per_page)
    limit = min(limit, 200) if limit and isinstance(limit, int) else 10
    if limit <= 0:
        limit = 10
    
    # Вычисляем номер страницы из offset и используем серверную пагинацию Zoho
    # per_page соответствует нашему limit
    page = (offset // limit) + 1 if offset and isinstance(offset, int) else 1
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    # Используем серверную пагинацию Zoho CRM v2: page + per_page
    params = {"page": page, "per_page": limit}
    
    if module_name:
        url = f"{zoho_config.base_url}/{module_name}"
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            response_data = response.json()
            records = response_data.get("data", [])
            info = response_data.get("info", {})
            
            return {
                "status": "success",
                "module": module_name,
                "count": len(records),
                "data": records,
                "pagination": {
                    "page": info.get("page", page),
                    "per_page": info.get("per_page", limit),
                    "more_records": info.get("more_records", False),
                    "returned_count": len(records),
                    "next_offset": (offset + limit) if info.get("more_records", False) else None
                }
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
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                response_data = response.json()
                records = response_data.get("data", [])
                info = response_data.get("info", {})

                all_data[module] = {
                    "count": len(records),
                    "data": records,
                    "pagination": {
                        "page": info.get("page", page),
                        "per_page": info.get("per_page", limit),
                        "more_records": info.get("more_records", False),
                        "returned_count": len(records)
                    }
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
            "data": all_data,
            "pagination": {
                "per_page_per_module": limit,
                "page": page,
                "note": "Server-side pagination via Zoho CRM API (page/per_page)"
            },
            "errors": errors if errors else None
        }

@mcp.tool()
def get_available_modules(ctx):
    """Get list of all available modules in Zoho CRM"""
    ensure_valid_token()
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
def search_records(ctx, module_name: str, search_criteria: str, limit: int = 50, page: int = 1):
    """
    Search for records in a specific module
    
    Args:
        module_name: Module to search in (e.g., 'Contacts', 'Leads')
        search_criteria: Search query (e.g., 'Email:john@example.com')
    """
    ensure_valid_token()
    access_token = get_access_token()
    zoho_config = get_zoho_config()

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    # Параметры серверной пагинации
    limit = min(limit, 200) if limit and isinstance(limit, int) else 50
    if limit <= 0:
        limit = 50
    page = page if page and isinstance(page, int) and page > 0 else 1

    url = f"{zoho_config.base_url}/{module_name}/search"
    params = {"criteria": search_criteria, "page": page, "per_page": limit}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        body = response.json()
        data = body.get("data", [])
        info = body.get("info", {})
        return {
            "status": "success",
            "module": module_name,
            "count": len(data),
            "data": data,
            "pagination": {
                "page": info.get("page", page),
                "per_page": info.get("per_page", limit),
                "more_records": info.get("more_records", False),
                "returned_count": len(data)
            }
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
    ensure_valid_token()
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
    ensure_valid_token()
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
def create_lead_from_form(
    ctx,
    first_name: str | None = None,
    last_name: str = "",
    mobile: str | None = None,
    possible_funds_to_invest: str | None = None,
    client_status: str | None = None,
    client_description: str | None = None,
):
    """
    Create a new Lead in Zoho CRM (module 'Leads') from form fields.

    Args:
        first_name: Optional first name.
        last_name: Required last name.
        mobile: Mobile phone number.
        possible_funds_to_invest: Possible funds for investing (will be stored in a Note).
        client_status: Client status (maps to Lead_Status field).
        client_description: Client description (will be stored in a Note).
    """
    ensure_valid_token()
    access_token = get_access_token()
    zoho_config = get_zoho_config()

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
    }

    # Validate last name
    if not last_name:
        return {
            "status": "error",
            "module": "Leads",
            "message": "last_name is required",
            "code": 400,
        }

    # Build record with only provided (non-empty) fields
    record: dict[str, str] = {
        "Last_Name": last_name.strip(),
    }
    if first_name :
        first_name = first_name.strip()
        record["First_Name"] = first_name
    if mobile:
        record["Mobile"] = mobile
    if client_status:
        record["Lead_Status"] = client_status

    url = f"{zoho_config.base_url}/Leads"
    payload = {"data": [record]}

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 201:
        result = response.json()
        note_result = None

        # Try to add a Note with invest/description if provided
        try:
            data_items = result.get("data", []) or []
            lead_id = None
            if data_items and isinstance(data_items, list):
                details = data_items[0].get("details") or {}
                lead_id = details.get("id")

            # Build note content only if we have something to add and a lead id
            note_lines = []
            if possible_funds_to_invest:
                note_lines.append(f"Possible funds to invest: {possible_funds_to_invest}")
            if client_description:
                note_lines.append(f"Description: {client_description}")

            if lead_id and note_lines:
                note_content = "\n".join(note_lines)
                notes_url = f"{zoho_config.base_url}/Notes"
                note_payload = {
                    "data": [
                        {
                            "Note_Title": "Lead Form Details",
                            "Note_Content": note_content,
                            "Parent_Id": lead_id,
                            "se_module": "Leads",
                        }
                    ]
                }
                note_resp = requests.post(notes_url, headers=headers, data=json.dumps(note_payload))
                if note_resp.status_code == 201:
                    note_result = {"status": "created"}
                else:
                    note_result = {"status": "failed", "code": note_resp.status_code, "message": note_resp.text}
            else:
                note_result = {"status": "skipped"}
        except Exception as _:
            note_result = {"status": "failed", "message": "Unexpected error while creating note"}

        return {
            "status": "success",
            "module": "Leads",
            "message": "Lead created successfully",
            "data": result.get("data", []),
            "note": note_result,
        }
    else:
        return {
            "status": "error",
            "module": "Leads",
            "message": response.text,
            "code": response.status_code,
        }

@mcp.tool()
def delete_record(ctx, module_name: str, record_id: str):
    """
    Delete a record from a specific module
    
    Args:
        module_name: Module containing the record (e.g., 'Contacts', 'Leads')
        record_id: ID of the record to delete
    """
    ensure_valid_token()
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
    ensure_valid_token()
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
    ensure_valid_token()
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


@mcp.tool()
def get_module_fields(ctx, module_name: str):
    """
    Get Zoho CRM module fields metadata including API names and picklist values.
    """
    ensure_valid_token()
    access_token = get_access_token()
    zoho_config = get_zoho_config()

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
    }

    url = f"{zoho_config.base_url}/settings/fields?module={module_name}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        body = response.json()
        fields = body.get("fields", [])
        # normalize output to essential info
        result = []
        for f in fields:
            entry = {
                "api_name": f.get("api_name"),
                "field_label": f.get("field_label"),
                "data_type": f.get("data_type"),
                "system_mandatory": f.get("system_mandatory"),
            }
            if f.get("pick_list_values"):
                entry["pick_list_values"] = [v.get("actual_value") for v in f.get("pick_list_values", [])]
            result.append(entry)
        return {"status": "success", "module": module_name, "count": len(result), "fields": result}
    else:
        return {
            "status": "error",
            "module": module_name,
            "message": response.text,
            "code": response.status_code,
        }


def run():
    mcp.run()

if __name__ == "__main__":
    # mcp.run()
    run()