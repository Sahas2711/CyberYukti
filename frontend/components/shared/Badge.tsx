interface BadgeProps {
  variant:
    | "p1"
    | "p2"
    | "p3"
    | "p4"
    | "confirmed"
    | "not-confirmed"
    | "inconclusive"
    | "stale"
    | "pending"
    | "approved"
    | "rejected"
    | "overridden"
    | "primary"
    | "secondary"
    | "success"
    | "warning"
    | "destructive";
  children: React.ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeProps["variant"], string> = {
  p1: "bg-priority-p1/15 text-priority-p1 border-priority-p1/40",
  p2: "bg-priority-p2/15 text-priority-p2 border-priority-p2/40",
  p3: "bg-priority-p3/15 text-priority-p3 border-priority-p3/40",
  p4: "bg-priority-p4/15 text-priority-p4 border-priority-p4/40",
  confirmed:
    "bg-evidence-confirmed/15 text-evidence-confirmed border-evidence-confirmed/40",
  "not-confirmed":
    "bg-evidence-not-confirmed/15 text-evidence-not-confirmed border-evidence-not-confirmed/40",
  inconclusive:
    "bg-evidence-inconclusive/20 text-slate-400 border-evidence-inconclusive/40",
  stale: "bg-amber-500/10 text-amber-400/90 border-amber-500/30",
  pending: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  approved: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  rejected: "bg-red-500/10 text-red-400 border-red-500/30",
  overridden: "bg-violet-500/10 text-violet-400 border-violet-500/30",
  primary: "bg-accent/15 text-accent border-accent/40",
  secondary: "bg-graphite-panel text-tx-secondary border-line",
  success: "bg-emerald-500/15 text-emerald-400 border-emerald-500/40",
  warning: "bg-amber-500/15 text-amber-400 border-amber-500/40",
  destructive: "bg-red-500/15 text-red-400 border-red-500/40",
};

export function Badge({ variant, children, className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded border px-1.5 py-[3px] text-[10px] font-semibold uppercase tracking-wider ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
}