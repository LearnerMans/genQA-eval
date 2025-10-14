export default function ScoreBar({ label, value, hint, max = 1, decimals = 2, display = 'percent', showOutOf = false }) {
  // display: 'percent' | 'value'
  const safe = typeof value === 'number' && !Number.isNaN(value);
  const ratio = safe ? (max > 0 ? value / max : 0) : 0;
  const pct = Math.max(0, Math.min(100, ratio * 100));
  const color =
    pct >= 80
      ? 'bg-success-bar'
      : pct >= 60
      ? 'bg-success-alt'
      : pct >= 40
      ? 'bg-warning-fill'
      : pct >= 20
      ? 'bg-warning-accent'
      : 'bg-danger-accent';

  const rightLabel = (() => {
    if (!safe) return '—';
    if (display === 'percent') return (ratio * 100).toFixed(decimals) + '%';
    return showOutOf ? `${value.toFixed(decimals)} / ${max}` : value.toFixed(decimals);
  })();

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs font-body text-text/70">
        <div className="truncate" title={label}>{label}</div>
        <div className="font-semibold text-text/80">{rightLabel}</div>
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
