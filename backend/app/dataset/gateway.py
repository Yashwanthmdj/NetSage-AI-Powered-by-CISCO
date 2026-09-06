from app.dataset._record import record
from app.models.enums import ConceptTag, OsiLayer, Severity

GATEWAY_CASES = [
    record(
        case_code="GW-001",
        title="Host default gateway points at the wrong address",
        symptom=(
            "PC0 pings other hosts on 192.168.10.0/24 but cannot reach the remote server "
            "192.168.30.10. Traceroute dies immediately."
        ),
        topology_note=(
            "Single switch S1 VLAN 10. R1 SVI/router interface for the subnet is 192.168.10.1. "
            "PC0 was statically addressed after a printer template was copied onto the PC."
        ),
        show_outputs="""
PC0> ipconfig
IP Address......................: 192.168.10.25
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 192.168.10.254

PC0> ping 192.168.10.10
Reply from 192.168.10.10: bytes=32 time=1ms TTL=128

PC0> ping 192.168.10.1
Reply from 192.168.10.1: bytes=32 time=1ms TTL=255

PC0> ping 192.168.30.10
Request timed out.

R1# show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0.10  192.168.10.1    YES manual up                    up
GigabitEthernet0/0.30  192.168.30.1    YES manual up                    up

S1# show mac address-table | include 192.168.10.254
S1#
        """.strip(),
        expected_fault=(
            "PC0 default gateway is 192.168.10.254, but the only router on the subnet is "
            "192.168.10.1. Off-subnet packets are sent to a nonexistent gateway."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.GATEWAY,
        severity=Severity.MEDIUM,
    ),
    record(
        case_code="GW-002",
        title="Gateway address is outside the host subnet",
        symptom=(
            "A newly imaged PC cannot reach anything beyond itself. Local pings to the "
            "supposed gateway fail, and the user cannot browse."
        ),
        topology_note=(
            "VLAN 40 VOICE subnet is 192.168.40.0/24. R1 SVI VLAN 40 is 192.168.40.1. "
            "PC2 was given mask 255.255.255.0 but gateway 192.168.10.1 from the data VLAN."
        ),
        show_outputs="""
PC2> ipconfig
IP Address......................: 192.168.40.22
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 192.168.10.1

PC2> ping 192.168.10.1
Request timed out.

PC2> ping 192.168.40.1
Reply from 192.168.40.1: bytes=32 time=1ms TTL=255

R1# show running-config interface vlan 40
interface Vlan40
 ip address 192.168.40.1 255.255.255.0
 no shutdown

S1# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
40   VOICE                            active    Fa0/6
        """.strip(),
        expected_fault=(
            "PC2 gateway 192.168.10.1 is not in 192.168.40.0/24, so the host never ARPs "
            "the real SVI 192.168.40.1 for off-net traffic."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.GATEWAY,
        severity=Severity.HIGH,
    ),
    record(
        case_code="GW-003",
        title="SVI gateway is administratively down",
        symptom=(
            "Every host in VLAN 50 can ping each other but none can leave the VLAN. "
            "The documented gateway 192.168.50.1 is unreachable."
        ),
        topology_note=(
            "Layer-3 switch MLS1 has SVI VLAN 50 192.168.50.1/24. Hosts are access VLAN 50. "
            "ip routing is enabled. A maintenance window left the SVI shut."
        ),
        show_outputs="""
PC3> ping 192.168.50.10
Reply from 192.168.50.10: bytes=32 time=1ms TTL=128

PC3> ping 192.168.50.1
Request timed out.

MLS1# show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
Vlan1                  10.0.0.1        YES manual up                    up
Vlan50                 192.168.50.1    YES manual administratively down down

MLS1# show interfaces vlan 50
Vlan50 is administratively down, line protocol is down
  Internet address is 192.168.50.1/24

MLS1# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
50   GUEST                            active    Fa0/1, Fa0/2, Fa0/3
        """.strip(),
        expected_fault=(
            "SVI Vlan50 is administratively down, so the default gateway 192.168.50.1 "
            "does not exist on the wire even though the VLAN itself is active."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.GATEWAY,
        severity=Severity.CRITICAL,
    ),
    record(
        case_code="GW-004",
        title="Client has no default gateway configured",
        symptom=(
            "PC4 can print to a local printer at 192.168.60.20 and open local shares, "
            "but any Internet or campus server address fails immediately."
        ),
        topology_note=(
            "Static addressing lab. VLAN 60 subnet 192.168.60.0/24, gateway 192.168.60.1 on R5. "
            "DHCP is disabled on this bench. PC4 was configured by hand."
        ),
        show_outputs="""
PC4> ipconfig
IP Address......................: 192.168.60.44
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 0.0.0.0

PC4> ping 192.168.60.20
Reply from 192.168.60.20: bytes=32 time=1ms TTL=128

PC4> ping 8.8.8.8
Request timed out.

R5# show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/1     192.168.60.1    YES manual up                    up
Serial0/0/0            10.1.1.1        YES manual up                    up

R5# show ip route
C    192.168.60.0/24 is directly connected, GigabitEthernet0/1
S*   0.0.0.0/0 [1/0] via 10.1.1.2
        """.strip(),
        expected_fault=(
            "PC4 has no default gateway (0.0.0.0). Local subnet traffic works; all "
            "remote destinations have no next hop on the host."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.GATEWAY,
        severity=Severity.MEDIUM,
    ),
]
