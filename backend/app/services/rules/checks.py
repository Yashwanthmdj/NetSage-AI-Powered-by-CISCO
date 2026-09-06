from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List, Sequence

from app.services.rules.iputil import (
    covers,
    in_subnet,
    is_apipa,
    is_unspecified,
    network_of,
    parse_ipv4,
    split_cidr,
)
from app.services.rules.models import Inventory
from app.services.rules.result import RuleResult

CheckFn = Callable[[Inventory], RuleResult]


def check_duplicate_ip(inventory: Inventory) -> RuleResult:
    grouped: Dict[str, List[str]] = defaultdict(list)
    evidence: Dict[str, List[str]] = defaultdict(list)
    for item in inventory.addresses:
        if is_apipa(item.ip) or is_unspecified(item.ip):
            continue
        key = "%s:%s" % (item.device, item.name)
        if key in grouped[item.ip]:
            continue
        grouped[item.ip].append(key)
        evidence[item.ip].append(item.evidence)
    collisions = {ip: owners for ip, owners in grouped.items() if len(owners) > 1}
    if not collisions:
        return RuleResult.passed(
            "DUP_IP",
            explanation="No duplicate IPv4 addresses were found across hosts and interfaces.",
            evidence=["Checked %s assigned IPv4 addresses." % len(inventory.addresses)],
        )
    lines = []
    devices = []
    ev = []
    for ip, owners in sorted(collisions.items()):
        lines.append("IPv4 %s is configured on %s." % (ip, ", ".join(owners)))
        devices.extend(owner.split(":", 1)[0] for owner in owners)
        ev.extend(evidence[ip])
    return RuleResult.failed(
        "DUP_IP",
        explanation=" ".join(lines),
        evidence=ev,
        devices=devices,
        severity="high",
    )


def check_bad_mask(inventory: Inventory) -> RuleResult:
    failures: List[str] = []
    ev: List[str] = []
    devices: List[str] = []

    bindings = [item for item in inventory.addresses if item.prefix is not None or item.mask]
    for item in inventory.hosts:
        if item.mask and item.prefix is None:
            failures.append("%s has an invalid subnet mask %s." % (item.device, item.mask))
            ev.append(item.evidence)
            devices.append(item.device)

    topology_nets = []
    for cidr in _topology_cidrs(inventory.topology_note):
        topology_nets.append(cidr)

    for item in bindings:
        prefix = item.prefix
        if prefix is None:
            continue
        for network, topo_prefix in topology_nets:
            if covers(item.ip, network, topo_prefix) and prefix != topo_prefix:
                failures.append(
                    "%s %s uses /%s but topology declares %s/%s."
                    % (item.device, item.ip, prefix, network, topo_prefix)
                )
                ev.append(item.evidence)
                devices.append(item.device)

    by_octet: Dict[str, List[int]] = defaultdict(list)
    for item in bindings:
        if item.prefix is None:
            continue
        by_octet[".".join(item.ip.split(".")[:3])].append(item.prefix)
    for item in bindings:
        if item.prefix is None:
            continue
        prefixes = set(by_octet[".".join(item.ip.split(".")[:3])])
        if len(prefixes) > 1:
            failures.append(
                "%s %s/%s conflicts with other masks on the same /24-aligned prefix."
                % (item.device, item.ip, item.prefix)
            )
            ev.append(item.evidence)
            devices.append(item.device)

    if not failures:
        return RuleResult.passed(
            "BAD_MASK",
            explanation="Host and interface masks are consistent with each other and with topology CIDR hints.",
            evidence=["Checked %s addressed endpoints for mask consistency." % len(bindings)],
        )
    # de-dupe while preserving order
    unique = list(dict.fromkeys(failures))
    return RuleResult.failed(
        "BAD_MASK",
        explanation=" ".join(unique),
        evidence=list(dict.fromkeys(ev)),
        devices=list(dict.fromkeys(devices)),
        severity="high",
    )


def check_gateway_mismatch(inventory: Inventory) -> RuleResult:
    if not inventory.hosts:
        return RuleResult.passed(
            "GW_MISMATCH",
            explanation="No host ipconfig blocks were present, so gateway consistency was not applicable.",
            evidence=["No host address records parsed."],
        )

    failures: List[str] = []
    ev: List[str] = []
    devices: List[str] = []
    router_ips = {item.ip for item in inventory.router_addresses()}

    for host in inventory.hosts:
        if not host.ip or is_apipa(host.ip):
            continue
        if not host.gateway or is_unspecified(host.gateway):
            failures.append("%s has no default gateway configured." % host.device)
            ev.append(host.evidence)
            devices.append(host.device)
            continue
        if host.mask and not in_subnet(host.gateway, host.ip, host.mask):
            failures.append(
                "%s gateway %s is outside subnet %s/%s."
                % (host.device, host.gateway, host.ip, host.prefix)
            )
            ev.append(host.evidence)
            devices.append(host.device)
            continue
        if router_ips and host.gateway not in router_ips:
            failures.append(
                "%s gateway %s does not match any router/SVI address in evidence (%s)."
                % (host.device, host.gateway, ", ".join(sorted(router_ips)))
            )
            ev.append(host.evidence)
            devices.append(host.device)

    if not failures:
        return RuleResult.passed(
            "GW_MISMATCH",
            explanation="Host default gateways are present, in-subnet, and match a router address when one is shown.",
            evidence=[host.evidence for host in inventory.hosts if host.evidence],
        )
    return RuleResult.failed(
        "GW_MISMATCH",
        explanation=" ".join(failures),
        evidence=list(dict.fromkeys(ev)),
        devices=list(dict.fromkeys(devices)),
        severity="high",
    )


def check_interface_down(inventory: Inventory) -> RuleResult:
    down = [
        iface
        for iface in inventory.interfaces
        if iface.admin_status != "up" or iface.protocol_status != "up"
    ]
    if not down:
        return RuleResult.passed(
            "IF_DOWN",
            explanation="No administratively down or protocol-down interfaces were found.",
            evidence=["Checked %s interfaces." % len(inventory.interfaces)],
        )
    return RuleResult.failed(
        "IF_DOWN",
        explanation=" ".join(
            "%s %s is %s / protocol %s."
            % (iface.device, iface.name, iface.admin_status, iface.protocol_status)
            for iface in down
        ),
        evidence=[iface.evidence for iface in down],
        devices=[iface.device for iface in down],
        severity="critical",
    )


def check_missing_vlan(inventory: Inventory) -> RuleResult:
    if not inventory.access_ports and not inventory.vlans:
        return RuleResult.passed(
            "MISSING_VLAN",
            explanation="No VLAN database or access-port evidence was present.",
            evidence=["No VLAN records parsed."],
        )

    failures: List[str] = []
    ev: List[str] = []
    devices: List[str] = []
    vlans_by_device: Dict[str, set] = defaultdict(set)
    for vlan in inventory.vlans:
        vlans_by_device[vlan.device].add(vlan.vlan_id)

    for port in inventory.access_ports:
        known = vlans_by_device.get(port.device)
        if port.inactive:
            failures.append(
                "%s %s is assigned VLAN %s which is inactive."
                % (port.device, port.port, port.vlan_id)
            )
            ev.append(port.evidence)
            devices.append(port.device)
        elif known is not None and port.vlan_id not in known:
            failures.append(
                "%s uses access VLAN %s, which is missing from the VLAN database."
                % (port.device, port.vlan_id)
            )
            ev.append(port.evidence)
            devices.append(port.device)

    if not failures:
        return RuleResult.passed(
            "MISSING_VLAN",
            explanation="Access VLANs referenced in switchport evidence exist in the VLAN database.",
            evidence=[port.evidence for port in inventory.access_ports]
            or [vlan.evidence for vlan in inventory.vlans[:3]],
        )
    return RuleResult.failed(
        "MISSING_VLAN",
        explanation=" ".join(failures),
        evidence=list(dict.fromkeys(ev)),
        devices=list(dict.fromkeys(devices)),
        severity="high",
    )


def check_missing_route(inventory: Inventory) -> RuleResult:
    if not inventory.routes:
        return RuleResult.passed(
            "MISSING_ROUTE",
            explanation="No routing table was present in the evidence, so missing-route checks were not applied.",
            evidence=["No show ip route output parsed."],
        )

    failed_dests = [
        probe
        for probe in inventory.pings
        if not probe.success and parse_ipv4(probe.destination) and not is_apipa(probe.destination)
    ]
    if not failed_dests:
        return RuleResult.passed(
            "MISSING_ROUTE",
            explanation="Routing tables are present and there is no failed off-subnet ping that lacks a covering route.",
            evidence=[route.evidence for route in inventory.routes[:4]],
        )

    routes_by_device: Dict[str, List] = defaultdict(list)
    for route in inventory.routes:
        routes_by_device[route.device].append(route)

    host_subnets = []
    for host in inventory.hosts:
        if host.ip and host.mask:
            network = network_of(host.ip, host.mask)
            if network:
                host_subnets.append(network)

    failures: List[str] = []
    ev: List[str] = []
    devices: List[str] = []
    for probe in failed_dests:
        dest = probe.destination
        if any(parse_ipv4(dest) in network for network in host_subnets):
            continue
        for device, routes in routes_by_device.items():
            if any(covers(dest, route.network, route.prefix) for route in routes):
                continue
            failures.append(
                "%s has no route that covers failed destination %s." % (device, dest)
            )
            ev.append(probe.evidence)
            ev.extend(route.evidence for route in routes)
            devices.append(device)

    if not failures:
        return RuleResult.passed(
            "MISSING_ROUTE",
            explanation="Failed pings are covered by a route on every device that published a routing table, or they stay on-link.",
            evidence=[probe.evidence for probe in failed_dests],
        )
    return RuleResult.failed(
        "MISSING_ROUTE",
        explanation=" ".join(list(dict.fromkeys(failures))),
        evidence=list(dict.fromkeys(ev)),
        devices=list(dict.fromkeys(devices)),
        severity="high",
    )


RULES: Sequence[CheckFn] = (
    check_duplicate_ip,
    check_bad_mask,
    check_gateway_mismatch,
    check_interface_down,
    check_missing_vlan,
    check_missing_route,
)


def _topology_cidrs(topology_note: str):
    found = []
    for token in topology_note.split():
        cleaned = token.strip(" ,;")
        cidr = split_cidr(cleaned)
        if cidr:
            found.append(cidr)
    return found
