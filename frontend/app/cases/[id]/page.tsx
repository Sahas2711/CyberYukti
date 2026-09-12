import { CaseDetail } from "./CaseDetail";

/**
 * The six demo case IDs shipped with the app. These are used only when the
 * frontend is built in static-export mode (Windows EXE / Docker packaging).
 * In normal (non-export) builds this route remains fully dynamic and any
 * case ID works.
 */
const DEMO_CASE_IDS = [
  "CASE-001",
  "CASE-002",
  "CASE-003",
  "CASE-004",
  "CASE-005",
  "CASE-006",
];

export function generateStaticParams() {
  return DEMO_CASE_IDS.map((id) => ({ id }));
}

export default function CaseDetailPage() {
  return <CaseDetail />;
}
