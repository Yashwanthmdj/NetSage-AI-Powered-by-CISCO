# Diagnosis JSON schema

The model must return a single JSON object and nothing else.

Required fields:

- `root_cause` (string): the most likely fault, stated in one or two sentences.
- `confidence` (number): 0.0 to 1.0.
- `confidence_label` (string): `low` | `medium` | `high`.
- `osi_layer` (string): `L1` | `L2` | `L3` | `L4` | `L5` | `L6` | `L7`.
- `concept_tag` (string): `vlan` | `gateway` | `dhcp` | `dns` | `routing` | `acl` | `nat` | `wireless`.
  `concept` is accepted as an alias for `concept_tag`.
- `severity` (string): `low` | `medium` | `high` | `critical`.
- `evidence` (array of objects): each object has `quote`, `command`, `why`.
  `quote` must be copied from the supplied show-command output.
- `next_command` (string): the single most useful next show/debug command.
- `next_commands` (array of strings): additional commands, may be empty.
- `fix_steps` (array of strings): ordered actions a human can apply in Packet Tracer.
- `verification_command` (string): command or ping used to prove the fix.

Optional:

- `uncertainties` (array of strings)
- `rule_alignment` (string): `agrees` | `extends` | `conflicts`
