export default function ReasoningCard({ title, explanation, children }) {
  const hasExplanation = typeof explanation === 'string' && explanation.trim().length > 0;

  return (
    <div className="border border-secondary rounded-lg p-3 bg-secondary/5 h-full flex flex-col">
      <div className="font-heading font-semibold text-sm text-text mb-1">{title}</div>
      <p className="font-body text-sm text-text/80 whitespace-pre-line">
        {hasExplanation ? explanation.trim() : 'No reasoning provided.'}
      </p>
      {children ? (
        <div className="mt-2 text-xs text-text/70 space-y-1">
          {children}
        </div>
      ) : null}
    </div>
  );
}
