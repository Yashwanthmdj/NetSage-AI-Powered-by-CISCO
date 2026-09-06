import type { ButtonHTMLAttributes } from "react";
import { cn } from "../../lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger";

export function Button({
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  const styles: Record<Variant, string> = {
    primary: "bg-accent text-ink hover:bg-accent/90",
    secondary: "border border-line bg-raised text-snow hover:border-accent/50 hover:text-accent",
    ghost: "text-mist hover:bg-raised hover:text-snow",
    danger: "border border-danger/40 bg-danger/10 text-danger hover:bg-danger/15",
  };
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md px-3.5 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-45",
        styles[variant],
        className,
      )}
      {...props}
    />
  );
}
