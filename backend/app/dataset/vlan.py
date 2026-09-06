from app.dataset._record import record
from app.models.enums import ConceptTag, OsiLayer, Severity

VLAN_CASES = [
    record(
        case_code="VLAN-001",
        title="Missing VLAN 30 blocks inter-VLAN server access",
        symptom=(
            "PC0 receives 192.168.10.10/24 and can ping its gateway 192.168.10.1, "
            "but cannot reach Server0 at 192.168.30.10 in VLAN 30."
        ),
        topology_note=(
            "Packet Tracer: S1 access Fa0/1 VLAN 10 (PC0), Fa0/24 intended VLAN 30 (Server0). "
            "R1 router-on-a-stick: G0/0.10 192.168.10.1/24 and G0/0.30 192.168.30.1/24. "
            "S1 G0/1 trunk to R1 G0/0."
        ),
        show_outputs="""
PC0> ping 192.168.10.1
Reply from 192.168.10.1: bytes=32 time=1ms TTL=255

PC0> ping 192.168.30.10
Request timed out.

S1# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/2, Fa0/3, Fa0/4, Fa0/5
10   STAFF                            active    Fa0/1
1002 fddi-default                     act/unsup
1003 token-ring-default               act/unsup

S1# show interfaces trunk
Port        Mode         Encapsulation  Status        Native vlan
G0/1        on           802.1q         trunking      1
Port        Vlans allowed on trunk
G0/1        1-4094
Port        Vlans in spanning tree forwarding state and not pruned
G0/1        1,10

S1# show interfaces fa0/24 switchport
Name: Fa0/24
Switchport: Enabled
Administrative Mode: static access
Access Mode VLAN: 30 (Inactive)
        """.strip(),
        expected_fault=(
            "VLAN 30 is missing from the VLAN database, so the server access port is inactive "
            "and inter-VLAN frames for 192.168.30.0/24 never enter the trunk."
        ),
        osi_layer=OsiLayer.L2,
        concept_tag=ConceptTag.VLAN,
        severity=Severity.HIGH,
    ),
    record(
        case_code="VLAN-002",
        title="Access port placed in the wrong VLAN",
        symptom=(
            "PC1 was moved to the Sales floor and now has no connectivity to the Sales server "
            "at 192.168.20.10. It can only reach hosts that still sit on VLAN 1."
        ),
        topology_note=(
            "S2 Fa0/3 is the Sales access port for PC1. VLAN 20 SALES exists. "
            "R2 SVI VLAN 20 is 192.168.20.1/24. PC1 should be access VLAN 20."
        ),
        show_outputs="""
PC1> ipconfig
IP Address......................: 192.168.1.14
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 192.168.1.1

S2# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/1, Fa0/2, Fa0/3, Fa0/4
20   SALES                            active    Fa0/10, Fa0/11
30   SERVERS                          active    Fa0/24

S2# show interfaces fa0/3 switchport
Name: Fa0/3
Administrative Mode: static access
Access Mode VLAN: 1 (default)

S2# show mac address-table interface fa0/3
          Mac Address Table
-------------------------------------------
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
   1    00e0.f7a1.0003    DYNAMIC     Fa0/3
        """.strip(),
        expected_fault=(
            "PC1 access port Fa0/3 is still in VLAN 1 instead of VLAN 20, so the host "
            "is on the default subnet and never joins the Sales broadcast domain."
        ),
        osi_layer=OsiLayer.L2,
        concept_tag=ConceptTag.VLAN,
        severity=Severity.MEDIUM,
    ),
    record(
        case_code="VLAN-003",
        title="Native VLAN mismatch on inter-switch trunk",
        symptom=(
            "After adding a second switch, some hosts on VLAN 10 lose connectivity and "
            "CDP reports a native VLAN mismatch. Broadcasts from VLAN 1 appear on VLAN 10."
        ),
        topology_note=(
            "S1 G0/2 trunks to S3 G0/2. S1 native VLAN is 1. S3 was set to native VLAN 10 "
            "during a campus template copy. VLANs 10 and 20 must cross the trunk."
        ),
        show_outputs="""
S1# show interfaces trunk
Port        Mode         Encapsulation  Status        Native vlan
G0/2        on           802.1q         trunking      1
Port        Vlans allowed on trunk
G0/2        1,10,20

S3# show interfaces trunk
Port        Mode         Encapsulation  Status        Native vlan
G0/2        on           802.1q         trunking      10
Port        Vlans allowed on trunk
G0/2        1,10,20

S1# show cdp neighbors detail
Device ID: S3
Interface: GigabitEthernet0/2
Native VLAN: 10
%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered on G0/2 (1), with S3 G0/2 (10)
        """.strip(),
        expected_fault=(
            "Native VLAN mismatch on the S1-S3 trunk (VLAN 1 vs VLAN 10) leaks untagged "
            "frames between the wrong broadcast domains."
        ),
        osi_layer=OsiLayer.L2,
        concept_tag=ConceptTag.VLAN,
        severity=Severity.HIGH,
    ),
    record(
        case_code="VLAN-004",
        title="Required VLAN not allowed on trunk",
        symptom=(
            "Server0 in VLAN 30 is locally up on S1, but hosts on S4 never reach it. "
            "Same-switch VLAN 30 pings work. Cross-switch pings fail."
        ),
        topology_note=(
            "S1 G0/1 trunks to S4 G0/1. VLAN 10, 20, and 30 are in use. "
            "S4 has VLAN 30 created and Server0 is on S1 Fa0/24 access VLAN 30."
        ),
        show_outputs="""
S1# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
10   STAFF                            active    Fa0/1, Fa0/2
20   SALES                            active    Fa0/10
30   SERVERS                          active    Fa0/24

S1# show interfaces trunk
Port        Mode         Encapsulation  Status        Native vlan
G0/1        on           802.1q         trunking      1
Port        Vlans allowed on trunk
G0/1        10,20
Port        Vlans in spanning tree forwarding state and not pruned
G0/1        10,20

S4# show interfaces trunk
Port        Mode         Encapsulation  Status        Native vlan
G0/1        on           802.1q         trunking      1
Port        Vlans allowed on trunk
G0/1        1-4094
        """.strip(),
        expected_fault=(
            "VLAN 30 is pruned from the allowed VLAN list on S1 G0/1, so tagged server "
            "traffic never crosses the trunk to S4."
        ),
        osi_layer=OsiLayer.L2,
        concept_tag=ConceptTag.VLAN,
        severity=Severity.HIGH,
    ),
    record(
        case_code="VLAN-005",
        title="Trunk forced to access mode on one side",
        symptom=(
            "Inter-VLAN routing worked yesterday. After a junior engineer 'secured' S5, "
            "only VLAN 1 crosses to the router. VLAN 10 and 20 hosts lost their gateway."
        ),
        topology_note=(
            "Router-on-a-stick R3 G0/0 subinterfaces .10 and .20. S5 G0/1 must be a trunk. "
            "S5 ports Fa0/1-8 are access VLAN 10; Fa0/9-16 are access VLAN 20."
        ),
        show_outputs="""
R3# show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     unassigned      YES unset  up                    up
GigabitEthernet0/0.10  192.168.10.1    YES manual up                    up
GigabitEthernet0/0.20  192.168.20.1    YES manual up                    up

S5# show interfaces g0/1 switchport
Name: G0/1
Administrative Mode: static access
Operational Mode: static access
Access Mode VLAN: 1 (default)
Trunking Native Mode VLAN: 1 (default)
Trunking VLANs Enabled: ALL

S5# show interfaces trunk
S5#
        """.strip(),
        expected_fault=(
            "S5 G0/1 was changed from trunk to static access VLAN 1, so only untagged "
            "VLAN 1 reaches the router and the subinterfaces no longer receive VLAN 10/20 tags."
        ),
        osi_layer=OsiLayer.L2,
        concept_tag=ConceptTag.VLAN,
        severity=Severity.CRITICAL,
    ),
]
