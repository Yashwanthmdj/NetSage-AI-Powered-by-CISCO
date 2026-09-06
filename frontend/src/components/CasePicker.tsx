import type { CaseSummary } from "../api/types";
import { FieldLabel, Select } from "./ui/Field";

export function CasePicker({
  cases,
  value,
  onChange,
}: {
  cases: CaseSummary[];
  value: string;
  onChange: (caseCode: string) => void;
}) {
  return (
    <label className="block min-w-[220px]">
      <FieldLabel>Case</FieldLabel>
      <Select className="w-full" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Select a lab case</option>
        {cases.map((item) => (
          <option key={item.id} value={item.case_code}>
            {item.case_code} · {item.title}
          </option>
        ))}
      </Select>
    </label>
  );
}
