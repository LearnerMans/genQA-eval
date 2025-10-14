import { useState } from 'react';

export default function AnswerBlock({ question, reference, generated }) {
  const [copied, setCopied] = useState(null); // 'ref' | 'gen'
  const copy = async (text, which) => {
    try {
      await navigator.clipboard.writeText(text || '');
      setCopied(which);
      setTimeout(() => setCopied(null), 1200);
    } catch {}
  };

  return (
    <div className="space-y-3">
      <div>
        <div className="text-[11px] font-body text-text/60 mb-1">Question</div>
        <div className="font-heading text-sm text-text bg-background border border-secondary rounded-md p-2 whitespace-pre-wrap">{question || '—'}</div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="text-[11px] font-body text-text/60">Reference Answer</div>
            <button
              className="text-[11px] font-body text-primary hover:underline cursor-pointer"
              onClick={() => copy(reference || '', 'ref')}
            >
              {copied === 'ref' ? 'Copied' : 'Copy'}
            </button>
          </div>
          <div className="font-body text-sm text-text bg-background border border-secondary rounded-md p-2 whitespace-pre-wrap min-h-[84px]">{reference || '—'}</div>
        </div>
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="text-[11px] font-body text-text/60">Generated Answer</div>
            <button
              className="text-[11px] font-body text-primary hover:underline cursor-pointer"
              onClick={() => copy(generated || '', 'gen')}
            >
              {copied === 'gen' ? 'Copied' : 'Copy'}
            </button>
          </div>
          <div className="font-body text-sm text-text bg-background border border-secondary rounded-md p-2 whitespace-pre-wrap min-h-[84px]">{generated || '—'}</div>
        </div>
      </div>
    </div>
  );
}

