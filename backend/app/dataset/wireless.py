from app.dataset._record import record
from app.models.enums import ConceptTag, OsiLayer, Severity

WIRELESS_CASES = [
    record(
        case_code="WLESS-001",
        title="Guest SSID mapped onto the corporate VLAN",
        symptom=(
            "Guests who join LabGuest receive 192.168.10.0/24 addresses and can see "
            "staff file shares. The guest SSID should be VLAN 90."
        ),
        topology_note=(
            "WLC/Packet Tracer AP: SSID Staff -> VLAN 10, SSID LabGuest should -> VLAN 90. "
            "WLAN LabGuest is incorrectly bound to VLAN 10."
        ),
        show_outputs="""
GUEST_LAPTOP> ipconfig
IP Address......................: 192.168.10.88
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 192.168.10.1
SSID............................: LabGuest

WLC# show wlan summary
WLAN ID  WLAN Profile Name / SSID      Status    Interface
1        Staff / Staff                 Enabled   vlan10
2        LabGuest / LabGuest           Enabled   vlan10

WLC# show interface summary
Interface Name      VLAN Id
vlan10              10
vlan90              90
management          100

S1# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
10   STAFF                            active    Fa0/1
90   GUEST                            active
        """.strip(),
        expected_fault=(
            "SSID LabGuest is mapped to interface vlan10 instead of vlan90, so guests "
            "land on the corporate staff VLAN."
        ),
        osi_layer=OsiLayer.L2,
        concept_tag=ConceptTag.WIRELESS,
        severity=Severity.CRITICAL,
    ),
    record(
        case_code="WLESS-002",
        title="Guest Wi-Fi reaches an internal server",
        symptom=(
            "Guest Wi-Fi can reach internal server 192.168.30.10. Isolation and ACL "
            "rules were supposed to block east-west access to campus servers."
        ),
        topology_note=(
            "VIP example: Guest WLAN on VLAN 90, servers on VLAN 30. AP uplink is a trunk. "
            "No peer-to-peer blocking and no deny ACL toward 192.168.30.0/24."
        ),
        show_outputs="""
GUEST_LAPTOP> ping 192.168.30.10
Reply from 192.168.30.10: bytes=32 time=3ms TTL=254

GUEST_LAPTOP> ipconfig
IP Address......................: 192.168.90.22
Default Gateway.................: 192.168.90.1
SSID............................: LabGuest

WLC# show wlan 2
WLAN Identifier.................................. 2
Profile Name.................................... LabGuest
Interface....................................... vlan90
Peer-to-Peer Blocking Action.................... Disabled

R1# show access-lists
R1#

S1# show interfaces g0/2 trunk
Port        Vlans allowed on trunk
G0/2        10,30,90
        """.strip(),
        expected_fault=(
            "Guest isolation failure: LabGuest clients on VLAN 90 have a routed path "
            "and no ACL to 192.168.30.0/24, so the internal server is reachable."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.WIRELESS,
        severity=Severity.CRITICAL,
    ),
    record(
        case_code="WLESS-003",
        title="WLAN VLAN has no DHCP scope",
        symptom=(
            "Users associate to SSID LabVoice with full signal but stay on 169.254.x.x "
            "and never register to the call manager."
        ),
        topology_note=(
            "SSID LabVoice -> VLAN 40. AP trunk allows 40. Router SVI VLAN 40 is up at "
            "192.168.40.1 but no DHCP pool exists for 192.168.40.0/24."
        ),
        show_outputs="""
PHONE> ipconfig
IP Address......................: 169.254.5.9
Subnet Mask.....................: 255.255.0.0
Default Gateway.................: 0.0.0.0
SSID............................: LabVoice
Association State...............: Associated

WLC# show wlan 3
WLAN Identifier.................................. 3
Profile Name.................................... LabVoice
Interface....................................... vlan40
Status.......................................... Enabled

R1# show ip interface brief
Vlan40                 192.168.40.1    YES manual up                    up

R1# show run | section dhcp
ip dhcp pool STAFF
 network 192.168.10.0 255.255.255.0
 default-router 192.168.10.1
        """.strip(),
        expected_fault=(
            "Clients associate on VLAN 40 but R1 has no DHCP pool for 192.168.40.0/24, "
            "so associated wireless clients never receive an address."
        ),
        osi_layer=OsiLayer.L3,
        concept_tag=ConceptTag.WIRELESS,
        severity=Severity.HIGH,
    ),
    record(
        case_code="WLESS-004",
        title="AP trunk missing the wireless VLAN",
        symptom=(
            "SSID Staff works on AP1 connected to S1 G0/2. A second AP on S1 Fa0/20 "
            "associates clients that never get an IP and cannot ping 192.168.10.1."
        ),
        topology_note=(
            "CAPWAP/PT AP2 is on Fa0/20. Fa0/20 is access VLAN 1 instead of a trunk "
            "allowing VLAN 10. AP1 on G0/2 is a working trunk."
        ),
        show_outputs="""
S1# show interfaces fa0/20 switchport
Name: Fa0/20
Administrative Mode: static access
Operational Mode: static access
Access Mode VLAN: 1 (default)

S1# show interfaces g0/2 trunk
Port        Mode         Encapsulation  Status        Native vlan
G0/2        on           802.1q         trunking      1
Port        Vlans allowed on trunk
G0/2        10,90

AP2> show interface summary
Interface     VLAN    Status
management    1       up

CLIENT> ipconfig
IP Address......................: 169.254.44.12
SSID............................: Staff
Association State...............: Associated
        """.strip(),
        expected_fault=(
            "AP2 uplink Fa0/20 is access VLAN 1, not a trunk allowing VLAN 10, so Staff "
            "SSID traffic never enters the wireless VLAN."
        ),
        osi_layer=OsiLayer.L2,
        concept_tag=ConceptTag.WIRELESS,
        severity=Severity.HIGH,
    ),
]
