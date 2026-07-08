import logging
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Any

import requests

logger = logging.getLogger(__name__)


def parse_ip(ip_str: Any) -> IPv4Address | IPv6Address | None:
    """Parses an IP string into an IPv4Address or IPv6Address object.

    Args:
        ip_str: The IP address string.

    Returns:
        IPv4Address | IPv6Address | None: The parsed IP object, or None if invalid or empty.
    """
    if not ip_str or not isinstance(ip_str, str):
        return None
    try:
        return ip_address(ip_str.strip())
    except ValueError:
        logger.warning("Invalid IP ignored: %s", ip_str)
        return None


def get_my_ip() -> str:
    """
    Gets the public IP address of the current machine.

    Returns:
        str: The public IP address.
    """
    try:
        response = requests.get("https://api64.ipify.org?format=json", timeout=100)
        response.raise_for_status()
        return str(response.json()["ip"])
    except (requests.exceptions.RequestException, KeyError):
        logger.exception("Failed to retrieve public IP: %s")
        return ""


def get_ip_location(ip_address: str) -> dict[str, Any]:
    """
    Gets the location details of a given IP address.

    Args:
        ip_address: The IP address to locate.

    Returns:
        dict: A dictionary containing the location details (ip, city, region, country).
    """
    try:
        response = requests.get(f"https://ipapi.co/{ip_address}/json/", timeout=100)
        response.raise_for_status()
        data = response.json()
        return {
            "ip": ip_address,
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country_code"),
        }
    except requests.exceptions.HTTPError:
        logger.exception("HTTP Error occurred while fetching location for %s: %s", ip_address)
    except requests.exceptions.RequestException:
        logger.exception("An error occurred while fetching location for %s: %s", ip_address)
    return {}
