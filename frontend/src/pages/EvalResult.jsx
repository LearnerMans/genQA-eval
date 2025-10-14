import { useEffect, useMemo, useState } from 'react';
import { useToast } from '../components/Toaster.jsx';
import { evalsAPI, qaAPI, promptsAPI, testRunsAPI } from '../services/api';
import Section from '../components/eval/Section.jsx';
import MetricCard from '../components/eval/MetricCard.jsx';
import MetricsGrid from '../components/eval/MetricsGrid.jsx';
import ScoreBar from '../components/eval/ScoreBar.jsx';
import AnswerBlock from '../components/eval/AnswerBlock.jsx';
import ChunksList from '../components/eval/ChunksList.jsx';
import ReasoningCard from '../components/eval/ReasoningCard.jsx';
import Logo from '../components/Logo';

export default function EvalResult({ projectId, testId, runId, qaId }) {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [qa, setQa] = useState(null);
  const [evalRow, setEvalRow] = useState(null);
  const [prompts, setPrompts] = useState([]);
  const [runs, setRuns] = useState([]);
  const [chunks, setChunks] = useState([]);
  const [chunksLoading, setChunksLoading] = useState(false);

  const run = useMemo(() => runs.find((r) => r.id === runId) || null, [runs, runId]);
  const prompt = useMemo(() => (run?.prompt_id ? prompts.find((p) => p.id === run.prompt_id) : null), [run, prompts]);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError('');
        const [qaRes, evalRes] = await Promise.all([
          qaAPI.getById(qaId),
          evalsAPI.getDetails(runId, qaId)
        ]);
        setQa(qaRes);
        setEvalRow(evalRes);
      } catch (e) {
        setError(e.message || 'Failed to load evaluation');
      } finally {
        setLoading(false);
      }
    })();
  }, [runId, qaId]);

  useEffect(() => {
    (async () => {
      if (!evalRow?.id) return;
      try {
        setChunksLoading(true);
        const list = await evalsAPI.getChunksByEvalId(evalRow.id);
        setChunks(list || []);
      } catch (e) {
        // non-blocking
      } finally {
        setChunksLoading(false);
      }
    })();
  }, [evalRow?.id]);

  useEffect(() => {
    (async () => {
      try {
        const [p, r] = await Promise.all([
          promptsAPI.getByTest(testId).catch(() => []),
          testRunsAPI.getByTest(testId).catch(() => [])
        ]);
        setPrompts(p || []);
        setRuns(r || []);
      } catch {
        // non-blocking for page
      }
    })();
  }, [testId]);

  const goBack = () => {
    window.location.hash = `#project/${projectId}/test/${testId}`;
  };

  const titleQuestion = qa?.question ? (qa.question.length > 64 ? qa.question.slice(0, 64) + '…' : qa.question) : '';

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 font-body text-text/70">Loading evaluation…</p>
        </div>
      </div>
    );
  }

  if (error || !evalRow) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="font-body text-danger">{error || 'Evaluation not found'}</p>
          <button onClick={goBack} className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 cursor-pointer">Back</button>
        </div>
      </div>
    );
  }

  const lg = evalRow;

  return (
    <div className="min-h-screen bg-background">
      <header className="w-full max-w-6xl mx-auto px-3 py-4">
        <Logo size="sm" showText={true} />
        <nav className="flex items-center gap-1 text-sm mt-4">
          <button onClick={() => window.location.hash = '#'} className="text-text/60 hover:text-text cursor-pointer">Projects</button>
          <span className="text-text/40">/</span>
          <button onClick={() => window.location.hash = `#project/${projectId}`} className="text-text/60 hover:text-text cursor-pointer">Project</button>
          <span className="text-text/40">/</span>
          <button onClick={goBack} className="text-text/60 hover:text-text cursor-pointer">Test</button>
          <span className="text-text/40">/</span>
          <div className="text-text/80">Run {runId.slice(0,8)} · {titleQuestion || qaId.slice(0,6)}</div>
        </nav>
        <div className="mt-1 flex items-center justify-between">
          <div>
            <h1 className="font-heading text-xl text-text">Evaluation Details</h1>
            <p className="font-body text-xs text-text/60">Prompt: {prompt?.name || (run?.prompt_id ? run.prompt_id.slice(0,8) : '—')}</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={goBack} className="px-3 py-1.5 text-xs border border-secondary rounded-md hover:bg-secondary/20 cursor-pointer font-body">Back</button>
          </div>
        </div>
      </header>

      <main className="w-full max-w-6xl mx-auto px-3 pb-6 space-y-3">
        {/* Overview scores */}
        <Section title="Overview">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="md:col-span-2 border border-secondary rounded-lg p-3 bg-secondary/5">
              <div className="font-heading font-semibold text-sm text-text mb-2">LLM Judgment</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <ScoreBar label="Overall" value={lg.llm_judged_overall ?? null} max={3} display="value" showOutOf hint="Scale 0–3 (poor→excellent)" />
                <ScoreBar label="Answer Relevance" value={lg.answer_relevance ?? null} max={3} display="value" showOutOf hint="Scale 0–3 (semantic relevance)" />
                <ScoreBar label="Context Relevance" value={lg.context_relevance ?? null} max={3} display="value" showOutOf hint="Scale 0–3 (uses retrieved context)" />
                <ScoreBar label="Groundedness" value={lg.groundedness ?? null} max={3} display="value" showOutOf hint="Scale 0–3 (factual grounding)" />
              </div>
            </div>
            <div className="border border-secondary rounded-lg p-3 bg-secondary/5">
              <div className="font-heading font-semibold text-sm text-text mb-2">Lexical Aggregate</div>
              <ScoreBar label="Aggregate" value={lg.lexical_aggregate ?? null} hint="Weighted BLEU(30%), ROUGE-L(40%), ContentF1(20%), EM(10%)" />
            </div>
          </div>
        </Section>

        {/* Answer details */}
        <Section title="Answers" subtitle="Compare reference vs generated">
          <AnswerBlock
            question={qa?.question}
            reference={qa?.answer}
            generated={lg.answer}
          />
        </Section>

        {/* Lexical metrics */}
        <Section title="Lexical Metrics" subtitle="Similarity-based scores from references">
          <MetricsGrid cols={4}>
            <MetricCard title="BLEU" value={lg.bleu} decimals={3} />
            <MetricCard title="ROUGE-L (F1)" value={lg.rouge_l} decimals={3} />
            <MetricCard title="ROUGE-L Precision" value={lg.rouge_l_precision} decimals={3} />
            <MetricCard title="ROUGE-L Recall" value={lg.rouge_l_recall} decimals={3} />
            <MetricCard title="SQuAD EM" value={lg.squad_em} decimals={3} />
            <MetricCard title="SQuAD Token F1" value={lg.squad_token_f1} decimals={3} />
            <MetricCard title="Content F1" value={lg.content_f1} decimals={3} />
            <MetricCard title="Aggregate" value={lg.lexical_aggregate} decimals={3} emphasize />
          </MetricsGrid>
        </Section>

        {/* LLM Judged metrics */}
        <Section title="LLM-Judged Metrics" subtitle="Model-based semantic assessments">
          <MetricsGrid cols={4}>
            <MetricCard title="Answer Relevance" value={lg.answer_relevance} decimals={3} />
            <MetricCard title="Context Relevance" value={lg.context_relevance} decimals={3} />
            <MetricCard title="Groundedness" value={lg.groundedness} decimals={3} />
            <MetricCard title="Overall" value={lg.llm_judged_overall} decimals={3} emphasize />
          </MetricsGrid>
        </Section>

        <Section title="LLM Reasoning" subtitle="Model explanations for each score">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <ReasoningCard title="Answer Relevance" explanation={lg.answer_relevance_reasoning} />
            <ReasoningCard title="Context Relevance" explanation={lg.context_relevance_reasoning}>
              {Array.isArray(lg.context_relevance_per_context) && lg.context_relevance_per_context.length > 0 ? (
                <div>
                  <div className="font-body font-semibold text-[11px] text-text/60 uppercase tracking-wide">Per-context scores</div>
                  <ul className="mt-1 space-y-0.5">
                    {lg.context_relevance_per_context.map((score, idx) => {
                      const numeric = typeof score === 'number' ? score : Number(score);
                      const value = Number.isFinite(numeric) ? numeric.toFixed(2) : String(score ?? '-');
                      return (
                        <li key={idx} className="font-body text-[11px] text-text/70">
                          Context {idx + 1}: {value}
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ) : null}
            </ReasoningCard>
            <ReasoningCard title="Groundedness" explanation={lg.groundedness_reasoning}>
              {Number.isFinite(lg?.groundedness_supported_claims) && Number.isFinite(lg?.groundedness_total_claims) ? (
                <div className="font-body text-[11px] text-text/70">
                  Supported claims: <span className="font-semibold text-text">{lg.groundedness_supported_claims}</span>
                  {' / '}
                  <span className="font-semibold text-text">{lg.groundedness_total_claims}</span>
                </div>
              ) : null}
            </ReasoningCard>
          </div>
        </Section>

        {/* Retrieved Chunks */}
        <Section title="Retrieved Chunks" subtitle="The context used for this evaluation">
          {chunksLoading ? (
            <div className="font-body text-sm text-text/60">Loading chunks…</div>
          ) : (
            <ChunksList items={chunks} />
          )}
        </Section>
      </main>
    </div>
  );
}
