from __future__ import annotations

import re
from typing import Iterable, List, Optional

from app.services.rules.iputil import mask_to_prefix, parse_ipv4, split_cidr
from app.services.rules.models import (
    AccessPort,
    AddressBinding,
    CommandBlock,
    HostRecord,
    InterfaceRecord,
    Inventory,
    PingProbe,
    RouteRecord,
    VlanRecord,
)

PROMPT_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_./-]*)\s*[#>]\s*(.*)$")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b")
VLAN_HINT_RE = re.compile(r"\bvlan\s+(\d{1,4})\b", re.IGNORECASE)

IP_BRIEF_RE = re.compile(
    r"^(?P<name>\S+)\s+(?P<ip>\S+)\s+\S+\s+\S+\s+"
    r"(?P<admin>administratively\s+down|up|down)\s+(?P<proto>up|down)\s*$",
    re.IGNORECASE,
)
VLAN_ROW_RE = re.compile(
    r"^(?P<id>\d+)\s+(?P<name>\S+)\s+(?P<status>\S+)(?:\s+(?P<ports>.+))?$"
)
ROUTE_RE = re.compile(
    r"^(?P<kind>[A-Z*]{1,3})\s+(?P<net>(?:\d{1,3}\.){3}\d{1,3})(?:/(?P<prefix>\d+))?"
    r"(?P<rest>.*)$"
)
SUBNETTED_RE = re.compile(
    r"^\s*(?P<net>(?:\d{1,3}\.){3}\d{1,3})/(?P<prefix>\d+)\s+is subnetted",
    re.IGNORECASE,
)
IFACE_HEADER_RE = re.compile(
    r"^(?P<name>\S+)\s+is\s+(?P<admin>administratively down|up|down),\s+"
    r"line protocol is\s+(?P<proto>up|down)",
    re.IGNORECASE,
)
INTERNET_ADDR_RE = re.compile(
    r"Internet address is\s+(?P<cidr>(?:\d{1,3}\.){3}\d{1,3}/\d+)",
    re.IGNORECASE,
)
CFG_IFACE_RE = re.compile(r"^interface\s+(?P<name>\S+)", re.IGNORECASE)
CFG_IP_RE = re.compile(
    r"ip address\s+(?P<ip>(?:\d{1,3}\.){3}\d{1,3})\s+(?P<mask>(?:\d{1,3}\.){3}\d{1,3})",
    re.IGNORECASE,
)
HOST_FIELD_RE = re.compile(
    r"^(?P<label>IP Address|Subnet Mask|Default Gateway)\s*[.:]+\s*(?P<value>\S+)",
    re.IGNORECASE,
)
PING_DEST_RE = re.compile(
    r"\bping(?:ing)?\s+(?P<dest>(?:\d{1,3}\.){3}\d{1,3})\b",
    re.IGNORECASE,
)


def split_blocks(show_outputs: str) -> List[CommandBlock]:
    blocks: List[CommandBlock] = []
    current_device = ""
    current_command = ""
    body_lines: List[str] = []
    raw_lines: List[str] = []

    def flush() -> None:
        if not current_device:
            return
        blocks.append(
            CommandBlock(
                device=current_device,
                command=current_command.strip(),
                body="\n".join(body_lines).strip(),
                raw="\n".join(raw_lines).strip(),
            )
        )

    for line in show_outputs.replace("\r\n", "\n").split("\n"):
        match = PROMPT_RE.match(line.strip())
        if match:
            flush()
            current_device = match.group(1)
            current_command = match.group(2)
            body_lines = []
            raw_lines = [line.rstrip()]
            continue
        if current_device:
            body_lines.append(line.rstrip())
            raw_lines.append(line.rstrip())
    flush()
    return [block for block in blocks if block.command]


def command_key(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip().lower())


def extract_topology_cidrs(topology_note: str) -> List[str]:
    return [item for item in IP_RE.findall(topology_note or "") if "/" in item]


def extract_topology_vlans(topology_note: str) -> List[int]:
    return sorted({int(item) for item in VLAN_HINT_RE.findall(topology_note or "")})


def parse_inventory(show_outputs: str, topology_note: str = "") -> Inventory:
    inventory = Inventory(topology_note=topology_note or "", show_outputs=show_outputs or "")
    inventory.blocks = split_blocks(show_outputs or "")
    for block in inventory.blocks:
        key = command_key(block.command)
        if key.startswith("show ip interface brief"):
            _parse_ip_brief(inventory, block)
        elif key.startswith("show vlan brief"):
            _parse_vlan_brief(inventory, block)
        elif "switchport" in key:
            _parse_switchport(inventory, block)
        elif key.startswith("ipconfig"):
            _parse_ipconfig(inventory, block)
        elif key.startswith("show ip route"):
            _parse_ip_route(inventory, block)
        elif key.startswith("show interfaces") or key.startswith("show ip interface"):
            _parse_interface_detail(inventory, block)
        elif key.startswith("show running-config interface") or key.startswith(
            "show running-config"
        ):
            _parse_running_config(inventory, block)
        elif key.startswith("ping") or key.startswith("pinging"):
            _parse_ping(inventory, block)
        elif "ping" in key and IP_RE.search(key):
            _parse_ping(inventory, block)
    _parse_inline_pings(inventory)
    return inventory


def _add_address(inventory: Inventory, binding: AddressBinding) -> None:
    inventory.addresses.append(binding)


def _parse_ip_brief(inventory: Inventory, block: CommandBlock) -> None:
    for line in block.body.splitlines():
        match = IP_BRIEF_RE.match(line.strip())
        if not match:
            continue
        ip = match.group("ip")
        parsed_ip = None if ip.lower() == "unassigned" else parse_ipv4(ip)
        iface = InterfaceRecord(
            device=block.device,
            name=match.group("name"),
            ip=str(parsed_ip) if parsed_ip else None,
            prefix=None,
            admin_status=re.sub(r"\s+", " ", match.group("admin").lower()),
            protocol_status=match.group("proto").lower(),
            evidence=line.strip(),
        )
        inventory.interfaces.append(iface)
        if parsed_ip:
            _add_address(
                inventory,
                AddressBinding(
                    device=block.device,
                    name=iface.name,
                    ip=str(parsed_ip),
                    prefix=None,
                    mask=None,
                    kind="interface",
                    evidence=line.strip(),
                ),
            )


def _parse_vlan_brief(inventory: Inventory, block: CommandBlock) -> None:
    for line in block.body.splitlines():
        match = VLAN_ROW_RE.match(line.strip())
        if not match:
            continue
        vlan_id = int(match.group("id"))
        if vlan_id >= 1002:
            continue
        ports = [item.strip() for item in (match.group("ports") or "").split(",") if item.strip()]
        inventory.vlans.append(
            VlanRecord(
                device=block.device,
                vlan_id=vlan_id,
                name=match.group("name"),
                status=match.group("status"),
                ports=ports,
                evidence=line.strip(),
            )
        )


def _parse_switchport(inventory: Inventory, block: CommandBlock) -> None:
    port = ""
    vlan_id = None
    inactive = False
    name_match = re.search(r"^Name:\s+(\S+)", block.body, re.MULTILINE)
    if name_match:
        port = name_match.group(1)
    access_match = re.search(
        r"Access Mode VLAN:\s+(\d+)(?:\s+\(([^)]+)\))?",
        block.body,
        re.IGNORECASE,
    )
    if access_match:
        vlan_id = int(access_match.group(1))
        inactive = "inactive" in (access_match.group(2) or "").lower()
    if vlan_id is None:
        return
    inventory.access_ports.append(
        AccessPort(
            device=block.device,
            port=port or "unknown",
            vlan_id=vlan_id,
            inactive=inactive,
            evidence=access_match.group(0),
        )
    )


def _parse_ipconfig(inventory: Inventory, block: CommandBlock) -> None:
    values = {"ip": None, "mask": None, "gateway": None}
    evidence_lines = []
    for line in block.body.splitlines():
        match = HOST_FIELD_RE.match(line.strip())
        if not match:
            continue
        label = match.group("label").lower()
        value = match.group("value")
        evidence_lines.append(line.strip())
        if label.startswith("ip address"):
            parsed = parse_ipv4(value)
            values["ip"] = str(parsed) if parsed else value
        elif label.startswith("subnet"):
            values["mask"] = value
        elif label.startswith("default"):
            parsed = parse_ipv4(value)
            values["gateway"] = str(parsed) if parsed else value
    prefix = mask_to_prefix(values["mask"]) if values["mask"] else None
    host = HostRecord(
        device=block.device,
        ip=values["ip"],
        mask=values["mask"],
        prefix=prefix,
        gateway=values["gateway"],
        evidence="\n".join(evidence_lines) or block.raw,
    )
    inventory.hosts.append(host)
    if host.ip and parse_ipv4(host.ip) and not str(host.ip).startswith("169.254."):
        _add_address(
            inventory,
            AddressBinding(
                device=block.device,
                name="host",
                ip=host.ip,
                prefix=prefix,
                mask=host.mask,
                kind="host",
                evidence=host.evidence,
            ),
        )


def _parse_ip_route(inventory: Inventory, block: CommandBlock) -> None:
    inherited_prefix: Optional[int] = None
    for raw_line in block.body.splitlines():
        line = raw_line.rstrip()
        subnetted = SUBNETTED_RE.search(line)
        if subnetted:
            inherited_prefix = int(subnetted.group("prefix"))
            continue
        match = ROUTE_RE.match(line.strip())
        if not match:
            continue
        kind = match.group("kind").replace("*", "")
        if kind not in {"C", "S", "R", "O", "D", "B", "L"}:
            continue
        prefix = int(match.group("prefix")) if match.group("prefix") else inherited_prefix
        if prefix is None:
            prefix = 32 if match.group("net") else None
        if prefix is None:
            continue
        rest = match.group("rest")
        next_hop = None
        interface = None
        via = re.search(r"via\s+(\S+)", rest)
        if via:
            next_hop = via.group(1).rstrip(",")
        connected = re.search(r"directly connected,\s+(\S+)", rest, re.IGNORECASE)
        if connected:
            interface = connected.group(1).rstrip(",")
        inventory.routes.append(
            RouteRecord(
                device=block.device,
                network=match.group("net"),
                prefix=prefix,
                kind=kind,
                next_hop=next_hop,
                interface=interface,
                evidence=line.strip(),
            )
        )


def _parse_interface_detail(inventory: Inventory, block: CommandBlock) -> None:
    header = IFACE_HEADER_RE.search(block.body) or IFACE_HEADER_RE.search(block.raw)
    internet = INTERNET_ADDR_RE.search(block.body)
    if not header:
        return
    cidr = split_cidr(internet.group("cidr")) if internet else None
    iface = InterfaceRecord(
        device=block.device,
        name=header.group("name"),
        ip=cidr[0] if cidr else None,
        prefix=cidr[1] if cidr else None,
        admin_status=re.sub(r"\s+", " ", header.group("admin").lower()),
        protocol_status=header.group("proto").lower(),
        evidence=header.group(0),
    )
    inventory.interfaces.append(iface)
    if cidr:
        _add_address(
            inventory,
            AddressBinding(
                device=block.device,
                name=iface.name,
                ip=cidr[0],
                prefix=cidr[1],
                mask=None,
                kind="interface",
                evidence=internet.group(0) if internet else iface.evidence,
            ),
        )


def _parse_running_config(inventory: Inventory, block: CommandBlock) -> None:
    current = None
    shutdown = False
    ip = None
    mask = None
    evidence = []
    for line in block.body.splitlines():
        iface = CFG_IFACE_RE.search(line)
        if iface:
            current = iface.group("name")
            shutdown = False
            ip = None
            mask = None
            evidence = [line.strip()]
            continue
        evidence.append(line.strip())
        if re.search(r"^\s*shutdown\s*$", line, re.IGNORECASE):
            shutdown = True
        addr = CFG_IP_RE.search(line)
        if addr:
            ip = addr.group("ip")
            mask = addr.group("mask")
    if current and ip:
        prefix = mask_to_prefix(mask) if mask else None
        inventory.interfaces.append(
            InterfaceRecord(
                device=block.device,
                name=current,
                ip=ip,
                prefix=prefix,
                admin_status="administratively down" if shutdown else "up",
                protocol_status="down" if shutdown else "up",
                evidence="\n".join(evidence),
            )
        )
        _add_address(
            inventory,
            AddressBinding(
                device=block.device,
                name=current,
                ip=ip,
                prefix=prefix,
                mask=mask,
                kind="interface",
                evidence="\n".join(evidence),
            ),
        )


def _parse_ping(inventory: Inventory, block: CommandBlock) -> None:
    dest = None
    cmd_match = PING_DEST_RE.search(block.command)
    if cmd_match:
        dest = cmd_match.group("dest")
    body_match = PING_DEST_RE.search(block.body)
    if not dest and body_match:
        dest = body_match.group("dest")
    if not dest:
        return
    success = bool(
        re.search(r"Reply from\s+%s" % re.escape(dest), block.body, re.IGNORECASE)
        or re.search(r"bytes=\d+\s+time=", block.body, re.IGNORECASE)
    )
    failed = bool(
        re.search(r"Request timed out|Destination host unreachable|could not find host", block.body, re.IGNORECASE)
    )
    if not success and not failed:
        return
    inventory.pings.append(
        PingProbe(
            source=block.device,
            destination=dest,
            success=success and not failed,
            evidence=block.raw,
        )
    )


def _parse_inline_pings(inventory: Inventory) -> None:
    """Capture `PC> ping 1.2.3.4` blocks whose body is only the reply."""
    seen = {(item.source, item.destination, item.success) for item in inventory.pings}
    for block in inventory.blocks:
        if not command_key(block.command).startswith("ping"):
            continue
        dest_match = PING_DEST_RE.search(block.command)
        if not dest_match:
            continue
        dest = dest_match.group("dest")
        success = "reply from" in block.body.lower()
        failed = "timed out" in block.body.lower() or "unreachable" in block.body.lower()
        key = (block.device, dest, success and not failed)
        if key in seen:
            continue
        if not success and not failed:
            continue
        inventory.pings.append(
            PingProbe(
                source=block.device,
                destination=dest,
                success=success and not failed,
                evidence=block.raw,
            )
        )
        seen.add(key)


def iter_lines(text: str) -> Iterable[str]:
    for line in text.splitlines():
        yield line.rstrip()
