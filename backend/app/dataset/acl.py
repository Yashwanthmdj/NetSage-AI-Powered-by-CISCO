from app.dataset._record import record
from app.models.enums import ConceptTag, OsiLayer, Severity

ACL_CASES = [
    record(
        case_code="ACL-001",
        title="ACL denies the server subnet on the user SVI",
        symptom=(
            "PC gets an IP and pings the VLAN 10 gateway, but cannot reach the server "
            "in VLAN 30. Other VLAN 30 hosts are also unreachable."
        ),
        topology_note=(
            "R1 G0/0.10 192.168.10.1 with inbound ACL BLOCK_SERVER. "
            "Server0 is 192.168.30.10. This matches the VIP worked example pattern."
        ),
        show_outputs="""
PC14> ping 192.168.10.1
Reply from 192.168.10.1: bytes=32 time=1ms TTL=255

PC14> ping 192.168.30.10
Request timed out.

R1# show ip interface g0/0.10
GigabitEthernet0/0.10 is up, line protocol is up
  Internet address is 192.168.10.1/24
  Inbound  access list is BLOCK_SERVER

R1# show access-lists BLOCK_SERVER
Extended IP access list BLOCK_SERVER
    10 deny ip any 192.168.30.0 0.0.0.255
    20 permit ip any any
    10 matches

R1# show ip route
C    192.168.10.0/24 is directly connected, GigabitEthernet0/0.10
C    192.168.30.0/24 is directly connected, GigabitEthernet0/0.30
        """.strip(),
        expected_fault=(
            "Inbound ACL BLOCK_SERVER on the user subinterface denies all IP to "
            "192.168.30.0/24, which is an inter-VLAN ACL fault at Layer 3/4."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.ACL,
        severity=Severity.HIGH,
    ),
    record(
        case_code="ACL-002",
        title="ACL applied in the wrong direction",
        symptom=(
            "Engineers applied an ACL meant to stop inbound probes from the WAN, but "
            "campus users can no longer initiate SSH to the jump host, while inbound "
            "WAN pings still arrive."
        ),
        topology_note=(
            "EDGE G0/1 is the campus LAN. ACL WAN_FILTER should be inbound on S0/0/0. "
            "It was mistakenly applied outbound on G0/1."
        ),
        show_outputs="""
EDGE# show ip interface g0/1
GigabitEthernet0/1 is up, line protocol is up
  Internet address is 10.20.0.1/16
  Outgoing access list is WAN_FILTER
  Inbound  access list is not set

EDGE# show ip interface s0/0/0
Serial0/0/0 is up, line protocol is up
  Internet address is 198.51.100.2/30
  Outgoing access list is not set
  Inbound  access list is not set

EDGE# show access-lists WAN_FILTER
Extended IP access list WAN_FILTER
    10 permit tcp any 10.20.0.0 0.0.255.255 established
    20 deny tcp any 10.20.0.50 0.0.0.0 eq 22
    30 permit ip any any
        """.strip(),
        expected_fault=(
            "WAN_FILTER is applied outbound on the LAN interface instead of inbound on "
            "the WAN, so legitimate outbound SSH from campus hits the deny."
        ),
        osi_layer=OsiLayer.L4,
        concept_tag=ConceptTag.ACL,
        severity=Severity.HIGH,
    ),
    record(
        case_code="ACL-003",
        title="Implicit deny drops return traffic",
        symptom=(
            "A permit-only-www ACL was added inbound on the WAN. Users can no longer "
            "receive any replies except HTTP. Ping and DNS break."
        ),
        topology_note=(
            "EDGE S0/0/0 inbound ACL WEB_ONLY permits tcp eq 80 to the inside. "
            "No established/permit icmp/permit udp 53 lines were added."
        ),
        show_outputs="""
EDGE# show ip interface s0/0/0
Serial0/0/0 is up, line protocol is up
  Inbound  access list is WEB_ONLY

EDGE# show access-lists WEB_ONLY
Extended IP access list WEB_ONLY
    10 permit tcp any 10.20.0.0 0.0.255.255 eq 80
    10 matches

PC15> ping 8.8.8.8
Request timed out.

PC15> nslookup cisco.com
DNS request timed out.
        """.strip(),
        expected_fault=(
            "ACL WEB_ONLY permits only inbound HTTP and then implicit deny drops ICMP, "
            "DNS, and TCP established return traffic."
        ),
        osi_layer=OsiLayer.L4,
        concept_tag=ConceptTag.ACL,
        severity=Severity.CRITICAL,
    ),
    record(
        case_code="ACL-004",
        title="Guest VLAN can reach an internal server",
        symptom=(
            "Guest Wi-Fi users can open the finance file server 192.168.30.10. "
            "Guest isolation was supposed to allow Internet only."
        ),
        topology_note=(
            "Guest VLAN 90 192.168.90.0/24 on R1 G0/0.90. Internal servers are VLAN 30. "
            "ACL GUEST_ISOLATE is missing or permits ip any any too early. VIP example."
        ),
        show_outputs="""
GUEST_PC> ping 192.168.30.10
Reply from 192.168.30.10: bytes=32 time=2ms TTL=254

GUEST_PC> ipconfig
IP Address......................: 192.168.90.44
Default Gateway.................: 192.168.90.1

R1# show ip interface g0/0.90
GigabitEthernet0/0.90 is up, line protocol is up
  Internet address is 192.168.90.1/24
  Inbound  access list is GUEST_ISOLATE

R1# show access-lists GUEST_ISOLATE
Extended IP access list GUEST_ISOLATE
    10 permit ip any any

R1# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
30   SERVERS                          active
90   GUEST                            active
        """.strip(),
        expected_fault=(
            "Guest isolation failed: ACL GUEST_ISOLATE permits ip any any, so the guest "
            "VLAN can reach internal server 192.168.30.10."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.ACL,
        severity=Severity.CRITICAL,
    ),
    record(
        case_code="ACL-005",
        title="Wrong port in ACL blocks HTTPS instead of HTTP",
        symptom=(
            "The security policy was to block inbound HTTP to the public web VIP while "
            "leaving HTTPS up. After the change, HTTPS died and HTTP still answers."
        ),
        topology_note=(
            "EDGE inbound ACL on G0/0 to host 203.0.113.10. Intended deny tcp eq 80. "
            "Line 10 was written as eq 443."
        ),
        show_outputs="""
EDGE# show access-lists PUBLIC_WEB
Extended IP access list PUBLIC_WEB
    10 deny tcp any host 203.0.113.10 eq 443
    20 permit ip any any

EDGE# show ip interface g0/0
GigabitEthernet0/0 is up, line protocol is up
  Internet address is 203.0.113.1/28
  Inbound  access list is PUBLIC_WEB

ADMIN_PC> ping 203.0.113.10
Reply from 203.0.113.10: bytes=32 time=1ms TTL=64
        """.strip(),
        expected_fault=(
            "ACL PUBLIC_WEB denies TCP 443 instead of TCP 80, so HTTPS is blocked and "
            "cleartext HTTP remains reachable."
        ),
        osi_layer=OsiLayer.L4,
        concept_tag=ConceptTag.ACL,
        severity=Severity.MEDIUM,
    ),
]
