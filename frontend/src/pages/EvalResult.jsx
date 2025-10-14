import { useEffect, useMemo, useState } from 'react';
import { useToast } from '../components/Toaster.jsx';
import { evalsAPI, qaAPI, promptsAPI, testRunsAPI } from '../services/api';
import Section from '../components/eval/Section.jsx';
import MetricCard from '../components/eval/MetricCard.jsx';
import MetricsGrid from '../components/eval/MetricsGrid.jsx';
import ScoreBar from '../components/eval/ScoreBar.jsx';
import AnswerBlock from '../components/eval/AnswerBlock.jsx';

export default function EvalResult({ projectId, testId, runId, qaId }) {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [qa, setQa] = useState(null);
  const [evalRow, setEvalRow] = useState(null);
  const [prompts, setPrompts] = useState([]);
  const [runs, setRuns] = useState([]);

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
          <p className="font-body text-red-600">{error || 'Evaluation not found'}</p>
          <button onClick={goBack} className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 cursor-pointer">Back</button>
        </div>
      </div>
    );
  }

  const lg = evalRow;

  return (
    <div className="min-h-screen bg-background">
      <header className="w-full max-w-6xl mx-auto px-3 py-4">
        <nav className="flex items-center gap-1 text-sm">
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
              <div className="font-heading font-semibold text-sm text-text mb-2">LLM Judgement</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <ScoreBar label="Overall" value={lg.llm_judged_overall ?? null} />
                <ScoreBar label="Answer Relevance" value={lg.answer_relevance ?? null} />
                <ScoreBar label="Context Relevance" value={lg.context_relevance ?? null} />
                <ScoreBar label="Groundedness" value={lg.groundedness ?? null} />
              </div>
            </div>
            <div className="border border-secondary rounded-lg p-3 bg-secondary/5">
              <div className="font-heading font-semibold text-sm text-text mb-2">Lexical Aggregate</div>
              <ScoreBar label="Aggregate" value={lg.lexical_aggregate ?? null} />
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
      </main>
    </div>
  );
}

