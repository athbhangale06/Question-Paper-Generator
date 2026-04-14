import { memo } from "react";
import { CheckCircle2 } from "lucide-react";

function StatusBadge({ loading, ready }) {
  const label = loading ? "Generating..." : ready ? "Done" : "Waiting";
  const styles = loading
    ? "border-blue-200 bg-blue-50 text-blue-700"
    : ready
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : "border-blue-100 bg-white text-slate-600";

  return (
    <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${styles}`}>
      {ready && !loading ? <CheckCircle2 className="h-3.5 w-3.5" /> : <span className="h-2 w-2 rounded-full bg-current opacity-70" />}
      {label}
    </span>
  );
}

export default memo(StatusBadge);
