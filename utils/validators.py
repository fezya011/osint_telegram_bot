import re
import ipaddress

def validate_phone(phone: str) -> bool:
    pattern = r'^\+\d{10,15}$'
    return bool(re.match(pattern, phone))

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_username(username: str) -> bool:
    pattern = r'^[a-zA-Z0-9_]{3,}$'
    return bool(re.match(pattern, username))

def validate_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False