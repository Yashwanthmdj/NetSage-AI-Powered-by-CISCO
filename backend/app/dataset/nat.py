from app.dataset._record import record
from app.models.enums import ConceptTag, OsiLayer, Severity

NAT_CASES = [
    record(
        case_code="NAT-001",
        title="NAT inside and outside interfaces not marked",
        symptom=(
            "Inside hosts can ping the edge LAN and the public WAN address of the router, "
            "but Internet destinations fail. show ip nat translations is empty."
        ),
        topology_note=(
            "NAT-R G0/0 inside 192.168.10.1/24, S0/0/0 outside 203.0.113.2/30. "
            "overload list NAT_ACL exists but ip nat inside/outside is missing."
        ),
        show_outputs="""
NAT-R# show ip nat translations
NAT-R#

NAT-R# show running-config | include nat
ip nat pool WEB 203.0.113.2 203.0.113.2 netmask 255.255.255.252
ip nat inside source list NAT_ACL interface Serial0/0/0 overload
ip access-list standard NAT_ACL
 permit 192.168.10.0 0.0.0.255

NAT-R# show ip interface g0/0
GigabitEthernet0/0 is up, line protocol is up
  Internet address is 192.168.10.1/24

NAT-R# show ip interface s0/0/0
Serial0/0/0 is up, line protocol is up
  Internet address is 203.0.113.2/30

PC16> ping 8.8.8.8
Request timed out.
        """.strip(),
        expected_fault=(
            "NAT rule exists but interfaces are not marked ip nat inside / ip nat outside, "
            "so no translations are created."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.NAT,
        severity=Severity.HIGH,
    ),
    record(
        case_code="NAT-002",
        title="NAT ACL does not match inside traffic",
        symptom=(
            "A second user subnet 192.168.40.0/24 cannot reach the Internet. "
            "The original 192.168.10.0/24 subnet still NATs correctly."
        ),
        topology_note=(
            "NAT-R does PAT on S0/0/0. ACL NAT_ACL still only permits 192.168.10.0/24. "
            "VLAN 40 was added last week."
        ),
        show_outputs="""
NAT-R# show access-lists NAT_ACL
Standard IP access list NAT_ACL
    10 permit 192.168.10.0, wildcard bits 0.0.0.255 (87 matches)

NAT-R# show ip nat translations
Pro Inside global      Inside local       Outside local      Outside global
icmp 203.0.113.2:1     192.168.10.25:1    8.8.8.8:1          8.8.8.8:1

NAT-R# show ip nat statistics
Total active translations: 1 (0 static, 1 dynamic)
Outside interfaces:
  Serial0/0/0
Inside interfaces:
  GigabitEthernet0/0
  GigabitEthernet0/1
Hits: 174  Misses: 22

PC17> ipconfig
IP Address......................: 192.168.40.17
Default Gateway.................: 192.168.40.1

PC17> ping 8.8.8.8
Request timed out.
        """.strip(),
        expected_fault=(
            "NAT interesting-traffic ACL permits only 192.168.10.0/24, so VLAN 40 "
            "hosts are never translated."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.NAT,
        severity=Severity.HIGH,
    ),
    record(
        case_code="NAT-003",
        title="Static NAT maps the server to the wrong public IP",
        symptom=(
            "Partners were told to reach the lab server at 203.0.113.10. Connections "
            "land on a different host. Inside users still reach 192.168.30.10 locally."
        ),
        topology_note=(
            "Server0 private 192.168.30.10 should static NAT to 203.0.113.10. "
            "The static line currently maps 192.168.30.10 to 203.0.113.20."
        ),
        show_outputs="""
NAT-R# show ip nat translations
Pro Inside global      Inside local       Outside local      Outside global
--- 203.0.113.20       192.168.30.10      ---                ---

NAT-R# show running-config | include ip nat inside source static
ip nat inside source static 192.168.30.10 203.0.113.20

OUTSIDE_PC> ping 203.0.113.10
Request timed out.

OUTSIDE_PC> ping 203.0.113.20
Reply from 203.0.113.20: bytes=32 time=12ms TTL=62
        """.strip(),
        expected_fault=(
            "Static NAT publishes 192.168.30.10 as 203.0.113.20 instead of the assigned "
            "public address 203.0.113.10."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.NAT,
        severity=Severity.MEDIUM,
    ),
    record(
        case_code="NAT-004",
        title="NAT pool is exhausted because overload is missing",
        symptom=(
            "The first inside host can browse. Additional hosts fail with no translations. "
            "The public side has only one global address."
        ),
        topology_note=(
            "PAT should use interface overload. Current config is ip nat inside source "
            "list NAT_ACL pool TINY without overload. Pool TINY is a single address."
        ),
        show_outputs="""
NAT-R# show ip nat statistics
Total active translations: 1 (0 static, 1 dynamic)
Hits: 40  Misses: 18
Expired translations: 0
Dynamic mappings:
-- Inside Source
access-list NAT_ACL pool TINY refcount 1
 pool TINY: netmask 255.255.255.252
        start 203.0.113.2 end 203.0.113.2
        type generic, total addresses 1, allocated 1 (100%), misses 17

NAT-R# show running-config | include ip nat
ip nat pool TINY 203.0.113.2 203.0.113.2 netmask 255.255.255.252
ip nat inside source list NAT_ACL pool TINY

PC18> ping 8.8.8.8
Request timed out.
        """.strip(),
        expected_fault=(
            "The NAT pool has one address and overload/PAT is not enabled, so only a "
            "single inside host can translate."
        ),
        osi_layer=OsiLayer.L4,
        concept_tag=ConceptTag.NAT,
        severity=Severity.HIGH,
    ),
    record(
        case_code="NAT-005",
        title="Inside host uses a public address that NAT never sees",
        symptom=(
            "A mis-addressed PC with 203.0.113.50 cannot reach the Internet or the "
            "inside gateway. Other DHCP clients work and NAT translations exist for them."
        ),
        topology_note=(
            "Inside LAN is 192.168.10.0/24. Someone statically set a PC to a public IP "
            "from the WAN block. NAT ACL only matches 192.168.10.0/24."
        ),
        show_outputs="""
PC19> ipconfig
IP Address......................: 203.0.113.50
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 192.168.10.1

PC19> ping 192.168.10.1
Request timed out.

NAT-R# show access-lists NAT_ACL
Standard IP access list NAT_ACL
    10 permit 192.168.10.0, wildcard bits 0.0.0.255

NAT-R# show ip nat translations
Pro Inside global      Inside local       Outside local      Outside global
icmp 203.0.113.2:3     192.168.10.12:3    8.8.8.8:3          8.8.8.8:3
        """.strip(),
        expected_fault=(
            "The host is addressed with a public IP outside the inside subnet, so it "
            "cannot use 192.168.10.1 as gateway and never matches the NAT ACL."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.NAT,
        severity=Severity.MEDIUM,
    ),
]
