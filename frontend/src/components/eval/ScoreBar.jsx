export default function ScoreBar({ label, value, hint, max = 1, decimals = 2 }) {
  const safe = typeof value === 'number' && !Number.isNaN(value);
  const pct = safe ? Math.max(0, Math.min(100, (value / max) * 100)) : 0;
  const color = pct >= 80 ? 'bg-green-500' : pct >= 60 ? 'bg-emerald-500' : pct >= 40 ? 'bg-yellow-500' : pct >= 20 ? 'bg-orange-500' : 'bg-red-500';

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs font-body text-text/70">
        <div className="truncate" title={label}>{label}</div>
        <div className="font-semibold text-text/80">{safe ? (value * (100/max)).toFixed(decimals) + '%' : '—'}</div>
      </div>
      <div className="h-2 rounded-full bg-secondary/30 overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      {hint ? (
        <div className="text-[10px] text-text/50 font-body">{hint}</div>
      ) : null}
    </div>
  );
}

