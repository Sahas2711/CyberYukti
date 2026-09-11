import { Badge } from "@/components/shared/Badge";
import type { ValidationResult } from "@/lib/api/types";

interface Props {
  status: ValidationResult["status"];
  confidence: number;
}

const variantMap: Record<
  ValidationResult["status"],
  "confirmed" | "not-confirmed" | "inconclusive" | "stale"
> = {
  CONFIRMED: "confirmed",
  NOT_CONFIRMED: "not-confirmed",
  INCONCLUSIVE: "inconclusive",
  STALE: "stale",
};

export function ValidationBadge({ status, confidence }: Props) {
  const confidencePct = Math.round(
    (typeof confidence === "number" ? confidence : 0) * 100
  );

  return (
    <Badge variant={variantMap[status]}>
      {status}
      {confidencePct >= 0 ? ` · ${confidencePct}% confidence` : ""}
    </Badge>
  );
}