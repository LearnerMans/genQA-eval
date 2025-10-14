import { useState } from 'react';

export default function ChunkItem({ indexLabel, content, sourceType, source }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const toggle = () => setExpanded((e) => !e);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(content || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {}
  };

  return (
    <div className="border border-secondary rounded-lg p-3 bg-background">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="min-w-0">
          <div className="font-heading font-semibold text-sm text-text">{indexLabel}</div>
          <div className="font-body text-[11px] text-text/60 truncate">
            {sourceType ? `${sourceType} • ` : ''}{source || 'Unknown source'}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={copy} className="px-2 py-0.5 text-[10px] border border-secondary rounded-md font-body text-text/70 hover:text-text hover:bg-secondary/10 cursor-pointer">
            {copied ? 'Copied' : 'Copy'}
          </button>
          <button onClick={toggle} className="px-2 py-0.5 text-[10px] border border-secondary rounded-md font-body text-text/70 hover:text-text hover:bg-secondary/10 cursor-pointer">
            {expanded ? 'Collapse' : 'Expand'}
          </button>
        </div>
      </div>
      <pre className={`whitespace-pre-wrap font-body text-xs text-text bg-secondary/5 rounded-md p-2 border border-secondary/60 ${expanded ? '' : 'max-h-36 overflow-hidden'}`}>{content || '—'}</pre>
    </div>
  );
}

