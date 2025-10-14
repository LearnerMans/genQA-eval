export default function Section({ title, subtitle, right, children }) {
  return (
    <section className="border border-secondary rounded-lg">
      <div className="px-3 py-2 border-b border-secondary/50 bg-secondary/10 flex items-center justify-between">
        <div>
          <div className="font-heading font-semibold text-sm text-text">{title}</div>
          {subtitle && <div className="font-body text-xs text-text/60">{subtitle}</div>}
        </div>
        {right && (
          <div className="flex items-center gap-2">{right}</div>
        )}
      </div>
      <div className="p-3">
        {children}
      </div>
    </section>
  );
}

