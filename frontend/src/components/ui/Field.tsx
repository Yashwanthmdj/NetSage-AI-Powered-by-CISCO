import type { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";
import { cn } from "../../lib/cn";

const fieldClass =
  "rounded-md border border-line bg-ink px-3 py-2 text-sm text-snow placeholder:text-mist/70 transition hover:border-mist/40 focus:border-accent/60";

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={cn(fieldClass, props.className)} />;
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={cn(fieldClass, props.className)} />;
}

export function TextArea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={cn(fieldClass, "font-mono leading-6", props.className)} />;
}

export function FieldLabel({ children }: { children: string }) {
  return <span className="mb-1.5 block text-[11px] font-medium uppercase tracking-[0.14em] text-mist">{children}</span>;
}
