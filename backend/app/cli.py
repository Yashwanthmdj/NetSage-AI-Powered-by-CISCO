from __future__ import annotations

import argparse
import json

from app.db.session import init_db, session_scope
from app.dataset.catalog import CASE_RECORDS, validate_catalog
from app.services.cases import CaseService
from app.services.rules import evaluate
from app.services.seed import seed_catalog


def main() -> None:
    parser = argparse.ArgumentParser(description="NetSage AI maintenance commands")
    sub = parser.add_subparsers(dest="command", required=True)

    seed_parser = sub.add_parser("seed", help="Upsert the lab catalog into the database")
    seed_parser.add_argument(
        "--no-csv",
        action="store_true",
        help="Skip writing data/cases.csv",
    )

    sub.add_parser("validate-catalog", help="Validate the in-repo case catalog")
    sub.add_parser("coverage", help="Print dataset coverage from the database")

    rules_parser = sub.add_parser("rules", help="Run the deterministic rule engine")
    rules_parser.add_argument("--case", help="Case code from the catalog, e.g. VLAN-001")
    rules_parser.add_argument("--sample", action="store_true", help="Run the built-in sample lab")
    rules_parser.add_argument("--show-file", help="Path to a show-command dump")
    rules_parser.add_argument("--topology", default="", help="Optional topology notes")

    args = parser.parse_args()
    if args.command == "validate-catalog":
        errors = validate_catalog()
        if errors:
            raise SystemExit("\n".join(errors))
        print(json.dumps({"ok": True, "cases": len(CASE_RECORDS)}, indent=2))
        return

    if args.command == "rules":
        show_outputs, topology = _rule_inputs(args)
        print(evaluate(show_outputs, topology).model_dump_json(indent=2))
        return

    init_db()
    db = session_scope()
    try:
        if args.command == "seed":
            result = seed_catalog(db, write_csv=not args.no_csv)
            print(json.dumps(result, indent=2))
        elif args.command == "coverage":
            print(CaseService(db).coverage().model_dump_json(indent=2))
    finally:
        db.close()


SAMPLE_SHOW = """
PC0> ipconfig
IP Address......................: 192.168.10.10
Subnet Mask.....................: 255.255.255.0
Default Gateway.................: 192.168.10.1

R1# show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     192.168.10.1    YES manual up                    up
GigabitEthernet0/1     192.168.10.10   YES manual administratively down down

S1# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/2
10   STAFF                            active    Fa0/1

S1# show interfaces fa0/24 switchport
Name: Fa0/24
Access Mode VLAN: 30 (Inactive)

PC0> ping 192.168.200.10
Request timed out.

R1# show ip route
C    192.168.10.0/24 is directly connected, GigabitEthernet0/0
""".strip()

SAMPLE_TOPOLOGY = "VLAN 30 server subnet 192.168.200.0/24 is behind R2. Staff LAN is 192.168.10.0/24."


def _rule_inputs(args) -> tuple[str, str]:
    if args.sample:
        return SAMPLE_SHOW, SAMPLE_TOPOLOGY
    if args.case:
        for row in CASE_RECORDS:
            if row["case_code"] == args.case:
                return row["show_outputs"], row["topology_note"]
        raise SystemExit("Unknown case code: %s" % args.case)
    if args.show_file:
        with open(args.show_file, encoding="utf-8") as handle:
            return handle.read(), args.topology
    raise SystemExit("Provide --sample, --case CODE, or --show-file PATH")


if __name__ == "__main__":
    main()

