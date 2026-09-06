import {
  Activity,
  BarChart3,
  Binary,
  Brain,
  FolderOpen,
  LayoutDashboard,
  Scale,
  ShieldCheck,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { fetchHealth } from "../api/cases";
import { useApi } from "../hooks/useApi";
import { cn } from "../lib/cn";
import { StatusDot } from "./StatusDot";

const links = [
  { to: "/", label: "Command Center", icon: LayoutDashboard, end: true },
  { to: "/troubleshoot", label: "Troubleshooting", icon: Activity },
  { to: "/cases", label: "Cases", icon: FolderOpen },
  { to: "/diagnosis", label: "Diagnosis", icon: Brain },
  { to: "/review", label: "Human Review", icon: ShieldCheck },
  { to: "/rules", label: "Rule Engine", icon: Binary },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/rai", label: "Responsible AI", icon: Scale },
];

export function Layout() {
  const { data: health, error: healthError, loading } = useApi(fetchHealth);
  const online = Boolean(health && !healthError);

  return (
    <div className="min-h-screen bg-ink text-snow lg:flex">
      <aside className="border-b border-line bg-panel lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-64 lg:shrink-0 lg:flex-col lg:border-b-0 lg:border-r">
        <div className="border-b border-line px-5 py-5">
          <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-accent">NetSage AI</p>
          <p className="mt-1 text-sm font-medium text-snow">Network operations</p>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-3 py-3 lg:flex-1 lg:flex-col lg:overflow-visible">
          {links.map((link) => {
            const Icon = link.icon;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition",
                    isActive
                      ? "bg-raised text-snow"
                      : "text-mist hover:bg-raised/70 hover:text-snow",
                  )
                }
              >
                <Icon size={16} />
                <span className="whitespace-nowrap">{link.label}</span>
              </NavLink>
            );
          })}
        </nav>
        <div className="hidden border-t border-line px-5 py-4 text-xs text-mist lg:block">
          <div className="flex items-center gap-2">
            <StatusDot tone={online ? "ok" : healthError ? "danger" : "warn"} pulse={!online} />
            <span>
              {health
                ? `${health.app} · ${health.database} db`
                : loading
                  ? "Checking control plane"
                  : `API offline`}
            </span>
          </div>
          {health ? <p className="mt-1 pl-4">{health.case_count} cases indexed</p> : null}
          {health ? (
            <p className="mt-1 pl-4">{health.llm_configured ? "LLM configured" : "LLM not configured"}</p>
          ) : null}
        </div>
      </aside>
      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-10 border-b border-line bg-ink/85 backdrop-blur">
          <div className="flex items-center justify-between px-5 py-3 lg:px-8">
            <p className="text-xs text-mist">Packet Tracer lab operations · human review required</p>
            <div className="flex items-center gap-2 text-xs text-mist">
              <StatusDot tone={online ? "ok" : "danger"} pulse={!online} />
              {health ? "Control plane live" : healthError ? "Control plane unreachable" : "Connecting"}
            </div>
          </div>
        </header>
        <main className="animate-enter px-5 py-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
