from __future__ import annotations

import ipaddress
from typing import Optional, Tuple


def parse_ipv4(value: str) -> Optional[ipaddress.IPv4Address]:
    try:
        addr = ipaddress.ip_address(value.strip())
    except ValueError:
        return None
    if isinstance(addr, ipaddress.IPv4Address):
        return addr
    return None


def mask_to_prefix(mask: str) -> Optional[int]:
    text = mask.strip()
    if text.isdigit():
        prefix = int(text)
        if 0 <= prefix <= 32:
            return prefix
        return None
    try:
        return ipaddress.IPv4Network("0.0.0.0/%s" % text).prefixlen
    except ValueError:
        return None


def to_interface(ip: str, mask_or_prefix: str) -> Optional[ipaddress.IPv4Interface]:
    prefix = mask_to_prefix(mask_or_prefix)
    if prefix is None:
        return None
    try:
        return ipaddress.IPv4Interface("%s/%s" % (ip.strip(), prefix))
    except ValueError:
        return None


def network_of(ip: str, mask_or_prefix: str) -> Optional[ipaddress.IPv4Network]:
    iface = to_interface(ip, mask_or_prefix)
    return iface.network if iface else None


def in_subnet(ip: str, network_ip: str, mask_or_prefix: str) -> bool:
    network = network_of(network_ip, mask_or_prefix)
    addr = parse_ipv4(ip)
    return bool(network and addr and addr in network)


def covers(destination: str, network: str, prefix: int) -> bool:
    addr = parse_ipv4(destination)
    try:
        net = ipaddress.IPv4Network("%s/%s" % (network, prefix), strict=False)
    except ValueError:
        return False
    return bool(addr and addr in net)


def split_cidr(value: str) -> Optional[Tuple[str, int]]:
    if "/" not in value:
        return None
    ip_text, prefix_text = value.split("/", 1)
    addr = parse_ipv4(ip_text)
    try:
        prefix = int(prefix_text)
    except ValueError:
        return None
    if addr is None or not 0 <= prefix <= 32:
        return None
    return str(addr), prefix


def is_apipa(ip: str) -> bool:
    addr = parse_ipv4(ip)
    return bool(addr and addr in ipaddress.IPv4Network("169.254.0.0/16"))


def is_unspecified(ip: str) -> bool:
    addr = parse_ipv4(ip)
    return bool(addr and int(addr) == 0)
