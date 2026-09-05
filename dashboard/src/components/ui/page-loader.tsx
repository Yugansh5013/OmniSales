import { Loader2 } from "lucide-react";

export function PageLoader({ label = "Loading live data..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-24 text-zinc-500 animate-in fade-in duration-200">
      <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
      <span className="text-xs font-mono">{label}</span>
    </div>
  );
}
