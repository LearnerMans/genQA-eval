export default function MetricCard({ title, value, suffix = '', decimals = 2, description, emphasize = false }) {
  const safe = typeof value === 'number' && !Number.isNaN(value);
  return (
    <div className={`border border-secondary rounded-lg p-3 bg-background ${emphasize ? 'shadow-sm' : ''}`}>
      <div className="text-[11px] font-body text-text/60 mb-1" title={title}>{title}</div>
      <div className={`font-heading ${emphasize ? 'text-xl' : 'text-lg'} text-text`}>{safe ? value.toFixed(decimals) + suffix : '—'}</div>
      {description && (
        <div className="text-[10px] text-text/50 font-body mt-1">{description}</div>
      )}
    </div>
  );
}

