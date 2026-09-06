from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class CommandBlock:
    device: str
    command: str
    body: str
    raw: str


@dataclass
class AddressBinding:
    device: str
    name: str
    ip: str
    prefix: Optional[int]
    mask: Optional[str]
    kind: str
    evidence: str


@dataclass
class InterfaceRecord:
    device: str
    name: str
    ip: Optional[str]
    prefix: Optional[int]
    admin_status: str
    protocol_status: str
    evidence: str


@dataclass
class HostRecord:
    device: str
    ip: Optional[str]
    mask: Optional[str]
    prefix: Optional[int]
    gateway: Optional[str]
    evidence: str


@dataclass
class VlanRecord:
    device: str
    vlan_id: int
    name: str
    status: str
    ports: List[str]
    evidence: str


@dataclass
class AccessPort:
    device: str
    port: str
    vlan_id: int
    inactive: bool
    evidence: str


@dataclass
class RouteRecord:
    device: str
    network: str
    prefix: int
    kind: str
    next_hop: Optional[str]
    interface: Optional[str]
    evidence: str


@dataclass
class PingProbe:
    source: str
    destination: str
    success: bool
    evidence: str


@dataclass
class Inventory:
    blocks: List[CommandBlock] = field(default_factory=list)
    hosts: List[HostRecord] = field(default_factory=list)
    interfaces: List[InterfaceRecord] = field(default_factory=list)
    addresses: List[AddressBinding] = field(default_factory=list)
    vlans: List[VlanRecord] = field(default_factory=list)
    access_ports: List[AccessPort] = field(default_factory=list)
    routes: List[RouteRecord] = field(default_factory=list)
    pings: List[PingProbe] = field(default_factory=list)
    topology_note: str = ""
    show_outputs: str = ""

    def router_addresses(self) -> List[AddressBinding]:
        return [item for item in self.addresses if item.kind == "interface"]

    def devices_with_vlan_db(self) -> List[str]:
        return sorted({vlan.device for vlan in self.vlans})

    def devices_with_routes(self) -> List[str]:
        return sorted({route.device for route in self.routes})
