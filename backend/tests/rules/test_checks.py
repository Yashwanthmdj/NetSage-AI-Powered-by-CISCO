from app.services.rules.checks import (
    check_bad_mask,
    check_duplicate_ip,
    check_gateway_mismatch,
    check_interface_down,
    check_missing_route,
    check_missing_vlan,
)
from app.services.rules.engine import evaluate
from app.services.rules.parser import parse_inventory

DUP = """
R1# show ip interface brief
GigabitEthernet0/0     10.0.0.1        YES manual up                    up
R2# show ip interface brief
GigabitEthernet0/0     10.0.0.1        YES manual up                    up
""".strip()

UNIQUE = """
R1# show ip interface brief
GigabitEthernet0/0     10.0.0.1        YES manual up                    up
R2# show ip interface brief
GigabitEthernet0/0     10.0.0.2        YES manual up                    up
""".strip()

MASK_FAIL = """
PC0> ipconfig
IP Address......................: 192.168.10.10
Subnet Mask.....................: 255.255.0.0
Default Gateway.................: 192.168.10.1
R1# show running-config interface GigabitEthernet0/0
interface GigabitEthernet0/0
 ip address 192.168.10.1 255.255.255.0
""".strip()

GW_OUTSIDE = """
PC2> ipconfig
IP Address......................: 192.168.40.22
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 192.168.10.1
""".strip()

GW_OK = """
PC0> ipconfig
IP Address......................: 192.168.10.25
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 192.168.10.1
R1# show ip interface brief
GigabitEthernet0/0.10  192.168.10.1    YES manual up                    up
""".strip()

IF_DOWN = """
R7# show ip interface brief
GigabitEthernet0/1     192.168.80.1    YES manual administratively down down
""".strip()

MISSING_VLAN = """
S1# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/2
10   STAFF                            active    Fa0/1
S1# show interfaces fa0/24 switchport
Name: Fa0/24
Access Mode VLAN: 30 (Inactive)
""".strip()

VLAN_OK = """
S2# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/3
20   SALES                            active    Fa0/10
S2# show interfaces fa0/3 switchport
Name: Fa0/3
Access Mode VLAN: 1 (default)
""".strip()

MISSING_ROUTE = """
PC12> ping 192.168.200.10
Request timed out.
R1# show ip route
C    192.168.10.0/24 is directly connected, GigabitEthernet0/0
C    10.1.1.0/30 is directly connected, Serial0/0/0
""".strip()

ROUTE_OK = """
PC13> ping 8.8.8.8
Reply from 8.8.8.8: bytes=32 time=4ms TTL=255
EDGE# show ip route
C    10.10.0.0/16 is directly connected, GigabitEthernet0/0
S*   0.0.0.0/0 [1/0] via 203.0.113.1
""".strip()


def _status(fn, text: str, topology: str = "") -> str:
    return fn(parse_inventory(text, topology)).status


def test_duplicate_ip_hit_and_miss() -> None:
    assert _status(check_duplicate_ip, DUP) == "fail"
    assert _status(check_duplicate_ip, UNIQUE) == "pass"


def test_bad_mask_detects_prefix_conflict() -> None:
    result = check_bad_mask(parse_inventory(MASK_FAIL, "Staff LAN 192.168.10.0/24"))
    assert result.status == "fail"
    assert "192.168.10.10" in result.explanation


def test_gateway_outside_subnet_and_valid_gateway() -> None:
    assert _status(check_gateway_mismatch, GW_OUTSIDE) == "fail"
    assert _status(check_gateway_mismatch, GW_OK) == "pass"


def test_interface_down() -> None:
    failed = check_interface_down(parse_inventory(IF_DOWN))
    assert failed.status == "fail"
    assert "GigabitEthernet0/1" in failed.explanation
    assert _status(check_interface_down, UNIQUE) == "pass"


def test_missing_vlan_inactive_and_present() -> None:
    failed = check_missing_vlan(parse_inventory(MISSING_VLAN))
    assert failed.status == "fail"
    assert "30" in failed.explanation
    assert _status(check_missing_vlan, VLAN_OK) == "pass"


def test_missing_route_without_covering_prefix() -> None:
    failed = check_missing_route(parse_inventory(MISSING_ROUTE))
    assert failed.status == "fail"
    assert "192.168.200.10" in failed.explanation
    assert _status(check_missing_route, ROUTE_OK) == "pass"


def test_engine_returns_all_six_rules_with_status() -> None:
    report = evaluate(MISSING_VLAN + "\n\n" + DUP)
    names = [item.rule_name for item in report.results]
    assert names == ["DUP_IP", "BAD_MASK", "GW_MISMATCH", "IF_DOWN", "MISSING_VLAN", "MISSING_ROUTE"]
    assert all(item.status in {"pass", "fail"} for item in report.results)
    assert all(item.explanation for item in report.results)
    assert report.fail_count >= 2


def test_engine_is_not_coupled_to_ai() -> None:
    import app.services.rules.engine as engine

    source = open(engine.__file__, encoding="utf-8").read()
    assert "from app.services.ai" not in source
    assert "openai" not in source.lower()
    assert "diagnos" not in source.lower()
