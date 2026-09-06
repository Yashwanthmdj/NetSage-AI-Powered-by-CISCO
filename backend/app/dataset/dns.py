from app.dataset._record import record
from app.models.enums import ConceptTag, OsiLayer, Severity

DNS_CASES = [
    record(
        case_code="DNS-001",
        title="Client DNS server is unreachable",
        symptom=(
            "Users can ping 192.168.30.10 and browse by IP, but hostnames such as "
            "files.lab.local fail to resolve."
        ),
        topology_note=(
            "Internal DNS is 192.168.30.5. PC8 is on VLAN 10 with gateway 192.168.10.1. "
            "Someone set the NIC DNS field to 8.8.8.8, which this lab has no route to."
        ),
        show_outputs="""
PC8> ipconfig /all
IP Address......................: 192.168.10.18
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 192.168.10.1
DNS Servers.....................: 8.8.8.8

PC8> ping 192.168.30.10
Reply from 192.168.30.10: bytes=32 time=2ms TTL=254

PC8> ping files.lab.local
Ping request could not find host files.lab.local.

PC8> ping 8.8.8.8
Request timed out.

R1# show ip route
C    192.168.10.0/24 is directly connected, GigabitEthernet0/0.10
C    192.168.30.0/24 is directly connected, GigabitEthernet0/0.30
        """.strip(),
        expected_fault=(
            "The client DNS server 8.8.8.8 is unreachable, so name resolution fails even "
            "though IP connectivity to the internal server is healthy."
        ),
        osi_layer=OsiLayer.L7,
        concept_tag=ConceptTag.DNS,
        severity=Severity.MEDIUM,
    ),
    record(
        case_code="DNS-002",
        title="DHCP pool does not hand out a DNS server",
        symptom=(
            "New DHCP clients can ping gateways and IP addresses but every browser URL "
            "fails. Statically configured PCs on the same VLAN work."
        ),
        topology_note=(
            "R9 DHCP pool CAMPUS issues 192.168.90.0/24 and default-router 192.168.90.1. "
            "The dns-server line was omitted after a pool rebuild."
        ),
        show_outputs="""
PC9> ipconfig /all
IP Address......................: 192.168.90.44
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 192.168.90.1
DNS Servers.....................:

PC9> ping 192.168.90.1
Reply from 192.168.90.1: bytes=32 time=1ms TTL=255

PC9> ping www.lab.local
Ping request could not find host www.lab.local.

R9# show running-config | section dhcp
ip dhcp excluded-address 192.168.90.1 192.168.90.10
ip dhcp pool CAMPUS
 network 192.168.90.0 255.255.255.0
 default-router 192.168.90.1

STATIC_PC> ipconfig /all
IP Address......................: 192.168.90.8
DNS Servers.....................: 192.168.90.5
        """.strip(),
        expected_fault=(
            "The CAMPUS DHCP pool has no dns-server option, so DHCP clients receive a "
            "valid IP and gateway but an empty resolver list."
        ),
        osi_layer=OsiLayer.L7,
        concept_tag=ConceptTag.DNS,
        severity=Severity.MEDIUM,
    ),
    record(
        case_code="DNS-003",
        title="Wrong A record: name resolves to a dead address",
        symptom=(
            "http://app.lab.local fails. ping app.lab.local returns 192.168.30.99 which "
            "does not answer. Browsing to 192.168.30.10 works."
        ),
        topology_note=(
            "Web server is 192.168.30.10. DNS server 192.168.30.5 has zone lab.local. "
            "The A record for app was left pointing at a retired host."
        ),
        show_outputs="""
PC10> ipconfig /all
DNS Servers.....................: 192.168.30.5
IP Address......................: 192.168.10.21
Default Gateway.................: 192.168.10.1

PC10> ping app.lab.local
Pinging app.lab.local [192.168.30.99] with 32 bytes of data:
Request timed out.

PC10> ping 192.168.30.10
Reply from 192.168.30.10: bytes=32 time=1ms TTL=254

DNS_SERVER# show hosts
Default domain is lab.local
Name/address lookup uses domain service
app.lab.local  -->  192.168.30.99
www.lab.local  -->  192.168.30.10
        """.strip(),
        expected_fault=(
            "DNS A record app.lab.local points to 192.168.30.99 instead of the live web "
            "server 192.168.30.10, so the name resolves but the target is dead."
        ),
        osi_layer=OsiLayer.L7,
        concept_tag=ConceptTag.DNS,
        severity=Severity.LOW,
    ),
    record(
        case_code="DNS-004",
        title="ACL blocks UDP/TCP 53 to the DNS server",
        symptom=(
            "After a 'security hardening' change, name lookups fail from VLAN 10 while "
            "direct IP pings to 192.168.30.5 still succeed."
        ),
        topology_note=(
            "R1 SVI VLAN 10 has inbound ACL HARDEN. DNS server is 192.168.30.5. "
            "HTTP to 192.168.30.10 still works by IP."
        ),
        show_outputs="""
PC11> ping 192.168.30.5
Reply from 192.168.30.5: bytes=32 time=1ms TTL=254

PC11> nslookup files.lab.local
DNS request timed out.

R1# show ip interface g0/0.10
GigabitEthernet0/0.10 is up, line protocol is up
  Internet address is 192.168.10.1/24
  Outgoing access list is not set
  Inbound  access list is HARDEN

R1# show access-lists HARDEN
Extended IP access list HARDEN
    10 permit icmp any any
    20 permit tcp any 192.168.30.0 0.0.0.255 eq 80
    30 deny udp any 192.168.30.5 0.0.0.0 eq 53
    40 deny tcp any 192.168.30.5 0.0.0.0 eq 53
    50 permit ip any any
        """.strip(),
        expected_fault=(
            "ACL HARDEN explicitly denies DNS (tcp/udp 53) to 192.168.30.5, so ICMP "
            "and HTTP by IP work while hostname resolution times out."
        ),
        osi_layer=OsiLayer.L4,
        concept_tag=ConceptTag.DNS,
        severity=Severity.HIGH,
    ),
]
