from app.dataset._record import record
from app.models.enums import ConceptTag, OsiLayer, Severity

ROUTING_CASES = [
    record(
        case_code="RT-001",
        title="Missing static route to the remote LAN",
        symptom=(
            "PC on 192.168.10.0/24 pings its local gateway and the WAN serial next hop, "
            "but cannot reach 192.168.200.10 behind R2."
        ),
        topology_note=(
            "R1 G0/0 192.168.10.1/24, S0/0/0 10.1.1.1/30. R2 S0/0/0 10.1.1.2/30, "
            "G0/0 192.168.200.1/24. Only R2 has a static for 192.168.10.0/24."
        ),
        show_outputs="""
PC12> ping 192.168.10.1
Reply from 192.168.10.1: bytes=32 time=1ms TTL=255

PC12> ping 10.1.1.2
Reply from 10.1.1.2: bytes=32 time=8ms TTL=254

PC12> ping 192.168.200.10
Request timed out.

R1# show ip route
Codes: C - connected, S - static, R - RIP
     10.0.0.0/30 is subnetted, 1 subnets
C       10.1.1.0 is directly connected, Serial0/0/0
C    192.168.10.0/24 is directly connected, GigabitEthernet0/0

R2# show ip route
C    10.1.1.0/30 is directly connected, Serial0/0/0
C    192.168.200.0/24 is directly connected, GigabitEthernet0/0
S    192.168.10.0/24 [1/0] via 10.1.1.1
        """.strip(),
        expected_fault=(
            "R1 has no route to 192.168.200.0/24, so packets toward the remote LAN are "
            "dropped even though the serial link and return route exist."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.ROUTING,
        severity=Severity.HIGH,
    ),
    record(
        case_code="RT-002",
        title="Static route uses the wrong next hop",
        symptom=(
            "A new static route was added for 172.16.5.0/24 but traceroute from HQ hops "
            "to the wrong branch router and then dies."
        ),
        topology_note=(
            "HQ-RTR has two serials: S0/0/0 to BR1 10.2.2.2 and S0/0/1 to BR2 10.3.3.2. "
            "Subnet 172.16.5.0/24 lives only behind BR2."
        ),
        show_outputs="""
HQ-RTR# show ip route 172.16.5.0
Routing entry for 172.16.5.0/24
  Known via "static", distance 1, metric 0
  Routing Descriptor Blocks:
  * 10.2.2.2
      Route metric is 0, traffic share count is 1

HQ-RTR# show running-config | include ip route
ip route 172.16.5.0 255.255.255.0 10.2.2.2
ip route 0.0.0.0 0.0.0.0 10.9.9.2

HQ-RTR# show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
Serial0/0/0            10.2.2.1        YES manual up                    up
Serial0/0/1            10.3.3.1        YES manual up                    up

BR2# show ip interface brief
GigabitEthernet0/0     172.16.5.1      YES manual up                    up
Serial0/0/0            10.3.3.2        YES manual up                    up
        """.strip(),
        expected_fault=(
            "The static route for 172.16.5.0/24 points at 10.2.2.2 (BR1) instead of "
            "10.3.3.2 (BR2), so traffic is forwarded to a router that does not own the LAN."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.ROUTING,
        severity=Severity.HIGH,
    ),
    record(
        case_code="RT-003",
        title="OSPF missing network statement for the LAN",
        symptom=(
            "Remote sites can ping R10's WAN address 10.8.8.1 but cannot reach the LAN "
            "192.168.110.0/24 behind it."
        ),
        topology_note=(
            "R10 G0/0 192.168.110.1/24, S0/0/0 10.8.8.1/30 in OSPF area 0. Neighbor R11 "
            "is FULL. Only the serial network was advertised."
        ),
        show_outputs="""
R10# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
11.11.11.11       0   FULL/  -        00:00:35    10.8.8.2        Serial0/0/0

R10# show ip ospf interface brief
Interface    PID   Area            IP Address/Mask    Cost  State Nbrs F/C
Se0/0/0      1     0               10.8.8.1/30        64    P2P   1/1

R10# show running-config | section router ospf
router ospf 1
 router-id 10.10.10.10
 network 10.8.8.0 0.0.0.3 area 0

R11# show ip route ospf
R11#
        """.strip(),
        expected_fault=(
            "OSPF on R10 does not advertise 192.168.110.0/24 (missing network statement "
            "or interface in OSPF), so neighbors have no route to the LAN."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.ROUTING,
        severity=Severity.HIGH,
    ),
    record(
        case_code="RT-004",
        title="Default route missing on the edge router",
        symptom=(
            "Campus users reach internal servers but cannot reach any Internet address. "
            "The ISP serial is up and the ISP can ping the edge WAN IP."
        ),
        topology_note=(
            "EDGE G0/0 campus 10.10.0.1/16, S0/0/0 203.0.113.2/30 to ISP 203.0.113.1. "
            "NAT is not yet in scope; this lab only tests IPv4 routing to 8.8.8.8 via ISP."
        ),
        show_outputs="""
EDGE# show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     10.10.0.1       YES manual up                    up
Serial0/0/0            203.0.113.2     YES manual up                    up

EDGE# show ip route
C    10.10.0.0/16 is directly connected, GigabitEthernet0/0
     203.0.113.0/30 is subnetted, 1 subnets
C       203.0.113.0 is directly connected, Serial0/0/0

PC13> ping 10.10.0.1
Reply from 10.10.0.1: bytes=32 time=1ms TTL=255

PC13> ping 8.8.8.8
Request timed out.

ISP# ping 203.0.113.2
Reply from 203.0.113.2: bytes=32 time=4ms TTL=255
        """.strip(),
        expected_fault=(
            "EDGE has no default route toward 203.0.113.1, so unknown destinations "
            "including 8.8.8.8 are not forwarded to the ISP."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.ROUTING,
        severity=Severity.CRITICAL,
    ),
    record(
        case_code="RT-005",
        title="RIP version mismatch stops route exchange",
        symptom=(
            "Two-router RIP lab: each LAN is reachable locally, but neither router "
            "learns the remote LAN. Interfaces are up."
        ),
        topology_note=(
            "R12 G0/0 192.168.1.1/24, S0/0/0 10.12.12.1/30 running RIPv2. "
            "R13 G0/0 192.168.2.1/24, S0/0/0 10.12.12.2/30 left at RIP version 1."
        ),
        show_outputs="""
R12# show ip protocols
Routing Protocol is "rip"
  Sending updates every 30 seconds
  Default version control: send version 2, receive version 2
  Interface           Send  Recv  Triggered RIP  Key-chain
  Serial0/0/0         2     2
  Automatic network summarization is in effect
  Maximum path: 4
  Routing for Networks:
    10.0.0.0
    192.168.1.0

R13# show ip protocols
Routing Protocol is "rip"
  Default version control: send version 1, receive version 1
  Interface           Send  Recv  Triggered RIP  Key-chain
  Serial0/0/0         1     1
  Routing for Networks:
    10.0.0.0
    192.168.2.0

R12# show ip route rip
R12#
R13# show ip route rip
R13#
        """.strip(),
        expected_fault=(
            "R12 sends/receives RIPv2 while R13 is locked to RIPv1, so RIP routes "
            "are ignored and each LAN stays local-only."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.ROUTING,
        severity=Severity.MEDIUM,
    ),
]
