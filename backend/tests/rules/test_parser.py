from app.services.rules.parser import parse_inventory, split_blocks

BRIEF = """
R1# show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     192.168.10.1    YES manual up                    up
Vlan50                 192.168.50.1    YES manual administratively down down
""".strip()

VLAN = """
S1# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/2, Fa0/3
10   STAFF                            active    Fa0/1
1002 fddi-default                     act/unsup
""".strip()

IPCONFIG = """
PC0> ipconfig
IP Address......................: 192.168.10.25
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 192.168.10.254
""".strip()


def test_split_blocks_handles_prompt_and_body() -> None:
    blocks = split_blocks(BRIEF)
    assert len(blocks) == 1
    assert blocks[0].device == "R1"
    assert blocks[0].command.lower().startswith("show ip interface brief")


def test_parse_ip_brief_and_down_interface() -> None:
    inventory = parse_inventory(BRIEF)
    assert len(inventory.interfaces) == 2
    down = [item for item in inventory.interfaces if item.name == "Vlan50"][0]
    assert down.admin_status == "administratively down"
    assert down.protocol_status == "down"
    assert {item.ip for item in inventory.addresses} == {"192.168.10.1", "192.168.50.1"}


def test_parse_vlan_skips_reserved_ids() -> None:
    inventory = parse_inventory(VLAN)
    assert {vlan.vlan_id for vlan in inventory.vlans} == {1, 10}


def test_parse_ipconfig_dotted_labels() -> None:
    inventory = parse_inventory(IPCONFIG)
    host = inventory.hosts[0]
    assert host.ip == "192.168.10.25"
    assert host.prefix == 24
    assert host.gateway == "192.168.10.254"


def test_parse_route_inherits_subnetted_prefix() -> None:
    text = """
R1# show ip route
     10.0.0.0/30 is subnetted, 1 subnets
C       10.1.1.0 is directly connected, Serial0/0/0
C    192.168.10.0/24 is directly connected, GigabitEthernet0/0
""".strip()
    inventory = parse_inventory(text)
    prefixes = {(route.network, route.prefix) for route in inventory.routes}
    assert ("10.1.1.0", 30) in prefixes
    assert ("192.168.10.0", 24) in prefixes


def test_parser_tolerates_messy_whitespace() -> None:
    messy = "  PC0>   ipconfig  \n\n  IP Address......................:   10.0.0.8  \n"
    inventory = parse_inventory(messy)
    assert inventory.hosts[0].ip == "10.0.0.8"
