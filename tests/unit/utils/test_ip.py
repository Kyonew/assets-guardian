"""Tests for the IP address resolution and geolocation service."""

import logging
from ipaddress import IPv4Address, IPv6Address

import requests
import responses

from assets_guardian.utils.ip import get_ip_location, get_my_ip, parse_ip

# Disable logging for the duration of tests to keep output clean
logging.getLogger("assets_guardian.utils.ip").setLevel(logging.CRITICAL)


@responses.activate
def test_get_my_ip_success():
    """Verify that get_my_ip successfully retrieves the public IP address on a 200 HTTP response."""
    responses.add(
        responses.GET,
        "https://api64.ipify.org?format=json",
        json={"ip": "1.2.3.4"},
        status=200,
    )
    assert get_my_ip() == "1.2.3.4"


@responses.activate
def test_get_my_ip_request_exception():
    """Verify that get_my_ip returns an empty string when a network request exception occurs."""
    responses.add(
        responses.GET,
        "https://api64.ipify.org?format=json",
        body=requests.exceptions.RequestException("Conn error"),
    )
    assert get_my_ip() == ""


@responses.activate
def test_get_my_ip_key_error():
    """Verify that get_my_ip returns an empty string when the JSON response is missing the expected 'ip' key."""
    responses.add(
        responses.GET,
        "https://api64.ipify.org?format=json",
        json={"wrong_key": "1.2.3.4"},
        status=200,
    )
    assert get_my_ip() == ""


@responses.activate
def test_get_ip_location_success():
    """Verify that get_ip_location successfully retrieves the geolocation details of a given IP on a 200 HTTP response."""
    ip = "1.2.3.4"
    responses.add(
        responses.GET,
        f"https://ipapi.co/{ip}/json/",
        json={"city": "Paris", "region": "IDF", "country_code": "FR"},
        status=200,
    )
    result = get_ip_location(ip)
    assert result == {
        "ip": ip,
        "city": "Paris",
        "region": "IDF",
        "country": "FR",
    }


@responses.activate
def test_get_ip_location_http_error():
    """Verify that get_ip_location returns an empty dictionary when the geolocation API returns an HTTP error (e.g. 404)."""
    ip = "1.2.3.4"
    responses.add(responses.GET, f"https://ipapi.co/{ip}/json/", status=404)
    result = get_ip_location(ip)
    assert result == {}


@responses.activate
def test_get_ip_location_request_exception():
    """Verify that get_ip_location returns an empty dictionary when a network exception is raised during geolocation."""
    ip = "1.2.3.4"
    responses.add(
        responses.GET,
        f"https://ipapi.co/{ip}/json/",
        body=requests.exceptions.RequestException("Conn error"),
    )
    result = get_ip_location(ip)
    assert result == {}


def test_parse_ip_valid_ipv4():
    """Verify that parse_ip parses a valid IPv4 address."""
    result = parse_ip("1.2.3.4")
    assert isinstance(result, IPv4Address)
    assert str(result) == "1.2.3.4"


def test_parse_ip_valid_ipv6():
    """Verify that parse_ip parses a valid IPv6 address."""
    result = parse_ip("2001:db8::1")
    assert isinstance(result, IPv6Address)
    assert str(result) == "2001:db8::1"


def test_parse_ip_whitespace():
    """Verify that parse_ip handles extra whitespaces in the input string."""
    result = parse_ip("  192.168.1.1  ")
    assert isinstance(result, IPv4Address)
    assert str(result) == "192.168.1.1"


def test_parse_ip_invalid_format(caplog):
    """Verify that parse_ip returns None and logs a warning on an invalid IP string format."""
    logger = logging.getLogger("assets_guardian.utils.ip")
    original_level = logger.level
    logger.setLevel(logging.WARNING)
    try:
        with caplog.at_level(logging.WARNING):
            assert parse_ip("not-an-ip") is None
            assert "Invalid IP ignored: not-an-ip" in caplog.text
    finally:
        logger.setLevel(original_level)


def test_parse_ip_empty_or_none():
    """Verify that parse_ip returns None when input is empty or None."""
    assert parse_ip("") is None
    assert parse_ip(None) is None


def test_parse_ip_invalid_types():
    """Verify that parse_ip returns None when input is of an invalid type."""
    assert parse_ip(12345) is None
    assert parse_ip(["1.2.3.4"]) is None
