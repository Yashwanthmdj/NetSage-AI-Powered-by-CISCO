import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { createCase } from "../api/cases";
import type { ConceptTag, OsiLayer, Severity } from "../api/types";
import { ErrorState } from "./EmptyState";
import { Notice } from "./Notice";
import { Button } from "./ui/Button";
import { Card } from "./ui/Card";
import { FieldLabel, Select, TextArea, TextInput } from "./ui/Field";

const CONCEPTS: ConceptTag[] = ["vlan", "gateway", "dhcp", "dns", "routing", "acl", "nat", "wireless"];
const LAYERS: OsiLayer[] = ["L1", "L2", "L3", "L4", "L5", "L6", "L7"];

export function CaseCreateForm({ onCreated }: { onCreated: () => void }) {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    case_code: "",
    title: "",
    symptom: "",
    topology_note: "",
    show_outputs: "",
    expected_fault: "",
    osi_layer: "L3" as OsiLayer,
    concept_tag: "vlan" as ConceptTag,
    severity: "medium" as Severity,
  });

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const created = await createCase(form);
      setSuccess(`Case ${created.case_code} saved.`);
      setForm({
        case_code: "",
        title: "",
        symptom: "",
        topology_note: "",
        show_outputs: "",
        expected_fault: "",
        osi_layer: "L3",
        concept_tag: "vlan",
        severity: "medium",
      });
      onCreated();
      navigate(`/cases/${created.case_code}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card
      title="Create case"
      description="Persists a new Packet Tracer case through POST /cases. Codes must match ABC-001."
      actions={
        <Button variant="secondary" type="button" onClick={() => setOpen((value) => !value)}>
          {open ? "Hide form" : "New case"}
        </Button>
      }
    >
      {!open && <p className="text-sm text-mist">Open the form to add a case to the live catalog.</p>}
      {open && (
        <form className="grid gap-3 md:grid-cols-2" onSubmit={onSubmit}>
          <label>
            <FieldLabel>Case code</FieldLabel>
            <TextInput
              className="w-full"
              value={form.case_code}
              onChange={(event) => setForm({ ...form, case_code: event.target.value.toUpperCase() })}
              placeholder="LAB-001"
              required
            />
          </label>
          <label>
            <FieldLabel>Title</FieldLabel>
            <TextInput
              className="w-full"
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
              required
            />
          </label>
          <label>
            <FieldLabel>Concept</FieldLabel>
            <Select
              className="w-full"
              value={form.concept_tag}
              onChange={(event) => setForm({ ...form, concept_tag: event.target.value as ConceptTag })}
            >
              {CONCEPTS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Select>
          </label>
          <label>
            <FieldLabel>OSI layer</FieldLabel>
            <Select
              className="w-full"
              value={form.osi_layer}
              onChange={(event) => setForm({ ...form, osi_layer: event.target.value as OsiLayer })}
            >
              {LAYERS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Select>
          </label>
          <label>
            <FieldLabel>Severity</FieldLabel>
            <Select
              className="w-full"
              value={form.severity}
              onChange={(event) => setForm({ ...form, severity: event.target.value as Severity })}
            >
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="critical">critical</option>
            </Select>
          </label>
          <label className="md:col-span-2">
            <FieldLabel>Symptom</FieldLabel>
            <TextArea
              className="w-full"
              rows={3}
              value={form.symptom}
              onChange={(event) => setForm({ ...form, symptom: event.target.value })}
              required
            />
          </label>
          <label className="md:col-span-2">
            <FieldLabel>Topology notes</FieldLabel>
            <TextArea
              className="w-full"
              rows={3}
              value={form.topology_note}
              onChange={(event) => setForm({ ...form, topology_note: event.target.value })}
              required
            />
          </label>
          <label className="md:col-span-2">
            <FieldLabel>Show-command evidence</FieldLabel>
            <TextArea
              className="w-full"
              rows={6}
              value={form.show_outputs}
              onChange={(event) => setForm({ ...form, show_outputs: event.target.value })}
              required
            />
          </label>
          <label className="md:col-span-2">
            <FieldLabel>Expected fault</FieldLabel>
            <TextArea
              className="w-full"
              rows={3}
              value={form.expected_fault}
              onChange={(event) => setForm({ ...form, expected_fault: event.target.value })}
              required
            />
          </label>
          {error && <div className="md:col-span-2"><ErrorState message={error} /></div>}
          {success && <div className="md:col-span-2"><Notice tone="success">{success}</Notice></div>}
          <div className="md:col-span-2">
            <Button type="submit" disabled={saving}>
              {saving ? "Saving…" : "Save case"}
            </Button>
          </div>
        </form>
      )}
    </Card>
  );
}
