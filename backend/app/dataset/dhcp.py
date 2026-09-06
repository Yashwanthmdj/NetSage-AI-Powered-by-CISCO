from app.dataset._record import record
from app.models.enums import ConceptTag, OsiLayer, Severity

DHCP_CASES = [
    record(
        case_code="DHCP-001",
        title="DHCP pool network does not match the interface subnet",
        symptom=(
            "PC0 stays on APIPA 169.254.x.x after boot. The DHCP server service is running "
            "on R1 and the LAN interface is up."
        ),
        topology_note=(
            "R1 G0/0 is 192.168.10.1/24. A DHCP pool named STAFF was created with network "
            "192.168.20.0/24 after a cut-and-paste from another lab."
        ),
        show_outputs="""
PC0> ipconfig
IP Address......................: 169.254.13.27
Subnet Mask.....................: 255.255.0.0
Default Gateway.................: 0.0.0.0

R1# show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     192.168.10.1    YES manual up                    up

R1# show running-config | section dhcp
ip dhcp excluded-address 192.168.20.1 192.168.20.10
ip dhcp pool STAFF
 network 192.168.20.0 255.255.255.0
 default-router 192.168.20.1
 dns-server 192.168.20.5

R1# show ip dhcp binding
IP address       Client-ID/              Lease expiration        Type
                 Hardware address
        """.strip(),
        expected_fault=(
            "The STAFF DHCP pool serves 192.168.20.0/24, but the connected interface is "
            "192.168.10.1/24, so R1 never offers an address on the client VLAN."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.DHCP,
        severity=Severity.HIGH,
    ),
    record(
        case_code="DHCP-002",
        title="Missing IP helper-address on the relay interface",
        symptom=(
            "Hosts on VLAN 20 never receive a DHCP address. The DHCP server on VLAN 10 "
            "works for local VLAN 10 PCs."
        ),
        topology_note=(
            "Central DHCP server 192.168.10.5. MLS1 SVI VLAN 20 is 192.168.20.1/24. "
            "Clients on S2 access VLAN 20. DHCP server lives on VLAN 10."
        ),
        show_outputs="""
PC5> ipconfig
IP Address......................: 169.254.2.88
Subnet Mask.....................: 255.255.0.0
Default Gateway.................: 0.0.0.0

MLS1# show running-config interface vlan 20
interface Vlan20
 ip address 192.168.20.1 255.255.255.0
 no ip helper-address

MLS1# show running-config interface vlan 10
interface Vlan10
 ip address 192.168.10.1 255.255.255.0

DHCP_SERVER> ipconfig
IP Address......................: 192.168.10.5
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 192.168.10.1

MLS1# show ip dhcp snooping
DHCP Snooping is disabled
        """.strip(),
        expected_fault=(
            "SVI VLAN 20 has no ip helper-address, so DHCP discovers from VLAN 20 never "
            "reach the server at 192.168.10.5."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.DHCP,
        severity=Severity.HIGH,
    ),
    record(
        case_code="DHCP-003",
        title="DHCP interface is down so no offers are sent",
        symptom=(
            "All wireless and wired guests report limited connectivity. The DHCP router "
            "has a pool configured, but no leases appear."
        ),
        topology_note=(
            "R7 G0/1 is the guest LAN 192.168.80.1/24 and the DHCP source interface. "
            "G0/1 was shut during a cable swap and never reopened."
        ),
        show_outputs="""
PC6> ipconfig
IP Address......................: 169.254.77.4
Subnet Mask.....................: 255.255.0.0
Default Gateway.................: 0.0.0.0

R7# show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     10.0.0.2        YES manual up                    up
GigabitEthernet0/1     192.168.80.1    YES manual administratively down down

R7# show ip dhcp pool GUEST
Pool GUEST :
 Utilization mark (high/low)    : 100 / 0
 Subnet size (first/next)       : 0 / 0
 Total addresses                : 254
 Leased addresses               : 0
 Pending event                  : none
 1 subnet is currently in the pool :
 Current index        IP address range                    Leased
 192.168.80.1         192.168.80.1    - 192.168.80.254     0
        """.strip(),
        expected_fault=(
            "DHCP server interface G0/1 is administratively down, so the 192.168.80.0/24 "
            "pool has no live L3 interface and offers are never sent."
        ),
        osi_layer=OsiLayer.L2,
        concept_tag=ConceptTag.DHCP,
        severity=Severity.CRITICAL,
    ),
    record(
        case_code="DHCP-004",
        title="Client in the wrong VLAN gets no DHCP offer",
        symptom=(
            "A replacement PC on the Finance desk stays at 169.254.x.x. Neighboring Finance "
            "PCs get 192.168.70.0/24 addresses normally."
        ),
        topology_note=(
            "Finance VLAN 70. S8 Fa0/12 is the desk drop. DHCP pool FINANCE is on R8 "
            "interface VLAN 70 / G0/0.70. Port Fa0/12 was left in VLAN 1 after a patch."
        ),
        show_outputs="""
PC7> ipconfig
IP Address......................: 169.254.19.63
Subnet Mask.....................: 255.255.0.0
Default Gateway.................: 0.0.0.0

S8# show interfaces fa0/12 switchport
Name: Fa0/12
Administrative Mode: static access
Access Mode VLAN: 1 (default)

S8# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/12, Fa0/13
70   FINANCE                          active    Fa0/1, Fa0/2, Fa0/3, Fa0/4

R8# show ip dhcp binding
IP address       Client-ID/              Lease expiration        Type
192.168.70.11    00E0.F70A.0001          Feb 02 2026 10:11 AM    Automatic
192.168.70.12    00E0.F70A.0002          Feb 02 2026 10:14 AM    Automatic
        """.strip(),
        expected_fault=(
            "The replacement PC is on access VLAN 1, so its DHCP discovers never reach "
            "the Finance pool on VLAN 70."
        ),
        osi_layer=OsiLayer.L2,
        concept_tag=ConceptTag.DHCP,
        severity=Severity.MEDIUM,
    ),
]
