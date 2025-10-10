import { useEffect, useMemo, useState } from 'react';
import { useToast } from '../components/Toaster.jsx';
import { projectsAPI, testsAPI, qaAPI, promptsAPI, testRunsAPI, evalsAPI } from '../services/api';

export default function Test({ projectId: propProjectId, testId: propTestId }) {
  const toast = useToast();

  const projectId = useMemo(() => propProjectId, [propProjectId]);
  const testId = useMemo(() => propTestId, [propTestId]);

  const [project, setProject] = useState(null);
  const [test, setTest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [qaSet, setQaSet] = useState([]);
  const [qaLoading, setQaLoading] = useState(false);

  const [runs, setRuns] = useState([]);
  const [runsLoading, setRunsLoading] = useState(false);

  const [selectedRuns, setSelectedRuns] = useState([null, null]);
  const [secondRunEnabled, setSecondRunEnabled] = useState(false);

  const [evalsByRun, setEvalsByRun] = useState({}); // { [runId]: { [qaId]: metrics } }
  const [evalsLoading, setEvalsLoading] = useState({}); // { [runId]: boolean }

  // Prompts state
  const [prompts, setPrompts] = useState([]);
  const [promptsLoading, setPromptsLoading] = useState(false);
  const [newPromptName, setNewPromptName] = useState('');
  const [newPromptText, setNewPromptText] = useState('');
  const [creatingPrompt, setCreatingPrompt] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [promptsTab, setPromptsTab] = useState('view');
  const [expandedPrompts, setExpandedPrompts] = useState(new Set());
  const [validationError, setValidationError] = useState('');
  const [textareaRef, setTextareaRef] = useState(null);
  const [showInfoTooltip, setShowInfoTooltip] = useState(false);

  // Run creation modal
  const [runModal, setRunModal] = useState(null); // { open: true, slotIndex: 0|1 }
  const [runModalPrompts, setRunModalPrompts] = useState([]);
  const [runModalLoading, setRunModalLoading] = useState(false);
  const [creatingRun, setCreatingRun] = useState(false);
  const [chosenPromptId, setChosenPromptId] = useState('');

  // UI: expanded prompt previews per run
  const [expandedRunPrompts, setExpandedRunPrompts] = useState(new Set());

  // UI: expanded prompt text in recent runs
  const [expandedRecentPrompts, setExpandedRecentPrompts] = useState(new Set());

  // Tabs: 'runs' | 'recent' | 'prompts'
  const [activeTab, setActiveTab] = useState('runs');

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const all = await projectsAPI.getAllProjects();
        const proj = all.find((p) => p.id === projectId) || null;
        if (!proj) throw new Error('Project not found');
        setProject(proj);

        const tlist = await testsAPI.getByProject(projectId);
        const tt = tlist.find((x) => x.id === testId) || null;
        if (!tt) throw new Error('Test not found');
        setTest(tt);
      } catch (e) {
        setError(e.message || 'Failed to load test');
      } finally {
        setLoading(false);
      }
    })();
  }, [projectId, testId]);

  useEffect(() => {
    if (!projectId) return;
    (async () => {
      setQaLoading(true);
      try {
        const qa = await qaAPI.getByProject(projectId);
        setQaSet(qa);
      } catch (e) {
        toast.error(e.message || 'Failed to fetch QA pairs');
      } finally {
        setQaLoading(false);
      }
    })();
  }, [projectId, toast]);

  const loadRuns = async () => {
    try {
      setRunsLoading(true);
      const r = await testRunsAPI.getByTest(testId);
      setRuns(r);
    } catch (e) {
      toast.error(e.message || 'Failed to fetch test runs');
    } finally {
      setRunsLoading(false);
    }
  };

  useEffect(() => {
    if (!testId) return;
    loadRuns();
  }, [testId]);

  // When switching to Recent Runs tab, lazily load evals for visible runs
  useEffect(() => {
    if (activeTab !== 'recent') return;
    for (const r of runs) {
      if (!evalsByRun[r.id] && !evalsLoading[r.id]) {
        loadEvalsForRun(r.id);
      }
    }
  }, [activeTab, runs]);

  // Load prompts when switching to prompts tab
  useEffect(() => {
    if (activeTab !== 'prompts' || !testId) return;
    (async () => {
      try {
        setPromptsLoading(true);
        const list = await promptsAPI.getByTest(testId);
        setPrompts(list);
      } catch (e) {
        toast.error(e.message || 'Failed to load prompts');
      } finally {
        setPromptsLoading(false);
      }
    })();
  }, [activeTab, testId, toast]);

  // Load prompts for this test on mount to enable prompt previews
  useEffect(() => {
    if (!testId) return;
    (async () => {
      try {
        const list = await promptsAPI.getByTest(testId);
        setPrompts(list);
      } catch (e) {
        // non-blocking
      }
    })();
  }, [testId]);

  const loadEvalsForRun = async (runId) => {
    if (!runId) return;
    try {
      setEvalsLoading((s) => ({ ...s, [runId]: true }));
      const evals = await evalsAPI.getByRun(runId);
      const byQa = {};
      for (const ev of evals) byQa[ev.qa_pair_id] = ev;
      setEvalsByRun((m) => ({ ...m, [runId]: byQa }));
    } catch (e) {
      setEvalsByRun((m) => ({ ...m, [runId]: {} }));
    } finally {
      setEvalsLoading((s) => ({ ...s, [runId]: false }));
    }
  };

  const handleSelectRun = (slotIndex, value) => {
    if (value === '__new__') {
      openNewRunModal(slotIndex);
      return;
    }
    setSelectedRuns((arr) => {
      const copy = [...arr];
      copy[slotIndex] = value || null;
      return copy;
    });
    if (value) loadEvalsForRun(value);
  };

  const openNewRunModal = async (slotIndex) => {
    try {
      setRunModal({ open: true, slotIndex });
      setRunModalLoading(true);
      const list = await promptsAPI.getByTest(testId);
      setRunModalPrompts(list);
    } catch (e) {
      toast.error(e.message || 'Failed to load prompts');
    } finally {
      setRunModalLoading(false);
    }
  };

  const handleCreateRun = async () => {
    if (!runModal || !testId) return;
    if (!chosenPromptId) return toast.error('Please choose a prompt');
    try {
      setCreatingRun(true);
      const created = await testRunsAPI.createRun({ test_id: testId, prompt_id: chosenPromptId });
      await loadRuns();
      setSelectedRuns((arr) => {
        const copy = [...arr];
        copy[runModal.slotIndex] = created.id;
        return copy;
      });
      loadEvalsForRun(created.id);
      setRunModal(null);
      setChosenPromptId('');
      toast.success('Test run created');
    } catch (e) {
      toast.error(e.message || 'Failed to create test run');
    } finally {
      setCreatingRun(false);
    }
  };

  const enableSecondRun = () => setSecondRunEnabled(true);

  const promptsMap = useMemo(() => {
    const m = new Map();
    for (const p of prompts) m.set(p.id, p);
    return m;
  }, [prompts]);

  const toggleRunPrompt = (runId) => {
    setExpandedRunPrompts((prev) => {
      const s = new Set(prev);
      if (s.has(runId)) s.delete(runId);
      else s.add(runId);
      return s;
    });
  };

  const toggleRecentPrompt = (runId) => {
    setExpandedRecentPrompts((prev) => {
      const s = new Set(prev);
      if (s.has(runId)) s.delete(runId);
      else s.add(runId);
      return s;
    });
  };

  const runAgain = async (promptId) => {
    try {
      if (!promptId) return toast.error('No prompt assigned to this run');
      setCreatingRun(true);
      const created = await testRunsAPI.createRun({ test_id: testId, prompt_id: promptId });
      await loadRuns();
      toast.success('Run started');
      // Optionally auto-select as Run A if empty
      setSelectedRuns((arr) => {
        if (!arr[0]) return [created.id, arr[1]];
        if (!arr[1]) return [arr[0], created.id];
        return arr;
      });
      loadEvalsForRun(created.id);
    } catch (e) {
      toast.error(e.message || 'Failed to run');
    } finally {
      setCreatingRun(false);
    }
  };

  const handleCreatePrompt = async (e) => {
    e.preventDefault();
    if (!newPromptName.trim() || !newPromptText.trim()) return;
    try {
      setCreatingPrompt(true);
      await promptsAPI.createPrompt({ test_id: testId, name: newPromptName.trim(), prompt: newPromptText.trim() });
      const list = await promptsAPI.getByTest(testId);
      setPrompts(list);
      setNewPromptName('');
      setNewPromptText('');
      setPromptsTab('view');
      toast.success('Prompt created');
    } catch (e) {
      toast.error(e.message || 'Failed to create prompt');
    } finally {
      setCreatingPrompt(false);
    }
  };

  const handleDeletePrompt = async (promptId) => {
    try {
      await promptsAPI.deletePrompt(promptId);
      setPrompts((prev) => prev.filter((p) => p.id !== promptId));
      toast.success('Prompt deleted');
    } catch (e) {
      toast.error(e.message || 'Failed to delete prompt');
    }
  };

  const togglePromptExpanded = (promptId) => {
    setExpandedPrompts((prev) => {
      const s = new Set(prev);
      if (s.has(promptId)) s.delete(promptId);
      else s.add(promptId);
      return s;
    });
  };

  const insertVariable = (variable) => {
    if (!textareaRef) return;
    const start = textareaRef.selectionStart;
    const end = textareaRef.selectionEnd;
    const text = newPromptText;
    const before = text.substring(0, start);
    const after = text.substring(end);
    const newText = before + variable + after;
    setNewPromptText(newText);
    if (validationError) setValidationError('');
    setTimeout(() => {
      textareaRef.selectionStart = textareaRef.selectionEnd = start + variable.length;
      textareaRef.focus();
    }, 0);
  };

  const goBack = () => {
    window.location.hash = `#project/${projectId}`;
  };

  const formatDate = (d) => (d ? new Date(d).toLocaleString() : 'N/A');

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 font-body text-text/70">Loading test…</p>
        </div>
      </div>
    );
  }

  if (error || !project || !test) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="font-body text-red-600">{error || 'Test not found'}</p>
          <button onClick={goBack} className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 cursor-pointer">Back</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="w-full max-w-6xl mx-auto px-3 py-4">
        <button onClick={goBack} className="font-body text-xs text-text/70 hover:text-text cursor-pointer">← Back to Project</button>
        <h1 className="font-heading font-bold text-xl text-text mt-1">{test.name}</h1>

        {/* Tabs */}
        <div className="mt-4 flex gap-2 border-b border-secondary/40">
          {[
            { id: 'runs', label: 'Test Runs' },
            { id: 'recent', label: 'Recent Runs' },
            { id: 'prompts', label: 'Prompts' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 text-sm font-body font-medium transition-colors cursor-pointer ${
                activeTab === tab.id ? 'text-primary border-b-2 border-primary' : 'text-text/60 hover:text-text'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      <main className="w-full max-w-6xl mx-auto px-3 pb-8 space-y-4">
        {activeTab === 'runs' && (
          <>
        {/* Test Runs + Compare */}
            <section className="border border-secondary rounded-lg p-3 bg-secondary/10">
              <div className="flex items-center justify-between mb-2">
              </div>

              <div className="flex items-center gap-3">
                {/* Run A selector */}
                <div className="flex-1">
                  <div className="text-xs font-body text-text/60 mb-1">Test Run 1</div>
                  <div className="relative mb-3">
                    <select
                      onFocus={() => { if (!runs || runs.length === 0) loadRuns(); }}
                      value={selectedRuns[0] || ''}
                      onChange={(e) => handleSelectRun(0, e.target.value)}
                      className="w-full appearance-none border border-secondary rounded-lg px-2 py-1.5 text-xs font-body bg-background hover:border-primary focus:border-primary focus:ring-1 focus:ring-primary cursor-pointer"
                    >
                      <option value="" disabled>Select a run</option>
                      {(runs || []).map((r) => (
                        <option key={r.id} value={r.id}>{`Run ${r.id.slice(0,6)}${r.prompt_id ? ` · Prompt ${r.prompt_id.slice(0,6)}`: ''}`}</option>
                      ))}
                      <option value="__new__">+ New Run…</option>
                    </select>
                    <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-text/40 text-xs">▾</div>
                  </div>
                </div>

                {/* Add compare button (circle) OR Run B selector */}
                {!secondRunEnabled ? (
                  <button
                    onClick={enableSecondRun}
                    className="shrink-0 h-[40px] w-[40px] rounded-full border border-primary text-primary hover:bg-primary/10 flex items-center justify-center cursor-pointer"
                    title="Add comparison"
                    aria-label="Add comparison"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                  </button>
                ) : (
                  <div className="flex-1">
                    <div className="text-xs font-body text-text/60 mb-1">Test Run 2</div>
                    <div className="relative mb-2">
                      <select
                        onFocus={() => { if (!runs || runs.length === 0) loadRuns(); }}
                        value={selectedRuns[1] || ''}
                        onChange={(e) => handleSelectRun(1, e.target.value)}
                        className="w-full appearance-none border border-secondary rounded-lg px-2 py-1.5 text-xs font-body bg-background hover:border-primary focus:border-primary focus:ring-1 focus:ring-primary cursor-pointer"
                      >
                        <option value="" disabled>Select a run</option>
                        {(runs || []).map((r) => (
                          <option key={r.id} value={r.id}>{`Run ${r.id.slice(0,6)}${r.prompt_id ? ` · Prompt ${r.prompt_id.slice(0,6)}`: ''}`}</option>
                        ))}
                        <option value="__new__">+ New Run…</option>
                      </select>
                      <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-text/40 text-xs">▾</div>
                    </div>
                  </div>
                )}

                {runsLoading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>}
              </div>
            {/* Prompt previews side by side */}
            <div className="flex gap-3">
              {/* Prompt preview for Run A */}
              {selectedRuns[0] && (
                <div className="flex-1 text-xs font-body text-text/70">
                  Prompt: {promptsMap.get(runs.find((r)=>r.id===selectedRuns[0])?.prompt_id)?.name || runs.find((r)=>r.id===selectedRuns[0])?.prompt_id || '—'}
                  <button onClick={() => toggleRunPrompt(selectedRuns[0])} className="ml-2 text-primary hover:underline cursor-pointer">{expandedRunPrompts.has(selectedRuns[0]) ? 'Hide' : 'Preview'}</button>
                  {expandedRunPrompts.has(selectedRuns[0]) && (
                    <pre className="mt-1 whitespace-pre-wrap border border-secondary rounded-md p-2 bg-background text-text/90">{promptsMap.get(runs.find((r)=>r.id===selectedRuns[0])?.prompt_id)?.prompt || '(prompt text unavailable)'}</pre>
                  )}
                </div>
              )}

              {/* Prompt preview for Run B */}
              {secondRunEnabled && selectedRuns[1] && (
                <div className="flex-1 text-xs font-body text-text/70">
                  Prompt: {promptsMap.get(runs.find((r)=>r.id===selectedRuns[1])?.prompt_id)?.name || runs.find((r)=>r.id===selectedRuns[1])?.prompt_id || '—'}
                  <button onClick={() => toggleRunPrompt(selectedRuns[1])} className="ml-2 text-primary hover:underline cursor-pointer">{expandedRunPrompts.has(selectedRuns[1]) ? 'Hide' : 'Preview'}</button>
                  {expandedRunPrompts.has(selectedRuns[1]) && (
                    <pre className="mt-1 whitespace-pre-wrap border border-secondary rounded-md p-2 bg-background text-text/90">{promptsMap.get(runs.find((r)=>r.id===selectedRuns[1])?.prompt_id)?.prompt || '(prompt text unavailable)'}</pre>
                  )}
                </div>
              )}
            </div>
          </section>


        {/* QA Results */}
        {(selectedRuns[0] || selectedRuns[1]) && (
          <section className="border border-secondary rounded-lg overflow-hidden">
            <div className="bg-secondary/20 px-2 py-1.5 font-heading text-xs text-text/80 border-b border-secondary">QA Results</div>
            <div className="overflow-x-auto max-h-[480px] overflow-y-auto">
              <table className="min-w-full text-xs font-body">
                <thead className="bg-secondary/10 sticky top-0 z-10">
                  <tr>
                    <th className="text-left px-2 py-1.5 text-text/70 font-medium text-xs">Question</th>
                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">A BLEU</th>
                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">A ROUGE</th>
                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">A AnsRel</th>
                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">A CtxRel</th>
                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">A Ground</th>
                    {selectedRuns[1] && (
                      <>
                        <th className="px-1 py-1.5 text-text/70 font-medium text-xs">B BLEU</th>
                        <th className="px-1 py-1.5 text-text/70 font-medium text-xs">B ROUGE</th>
                        <th className="px-1 py-1.5 text-text/70 font-medium text-xs">B AnsRel</th>
                        <th className="px-1 py-1.5 text-text/70 font-medium text-xs">B CtxRel</th>
                        <th className="px-1 py-1.5 text-text/70 font-medium text-xs">B Ground</th>
                      </>
                    )}
                    <th className="px-2 py-1.5 text-right"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-secondary/30">
                  {qaSet.map((qa) => {
                    const runA = selectedRuns[0];
                    const runB = selectedRuns[1];
                    const evA = runA ? (evalsByRun[runA]?.[qa.id] || {}) : {};
                    const evB = runB ? (evalsByRun[runB]?.[qa.id] || {}) : {};
                    return (
                      <tr key={qa.id} className="bg-background/60 hover:bg-secondary/10">
                        <td className="px-2 py-1.5 align-top max-w-[280px]">
                          <div className="text-text font-medium truncate text-xs" title={qa.question}>Q: {qa.question}</div>
                          <div className="text-text/70 text-xs line-clamp-1">A: {qa.answer}</div>
                        </td>
                        <td className="px-1 py-1.5 text-center">{evA.bleu ?? '-'}</td>
                        <td className="px-1 py-1.5 text-center">{evA.rouge ?? '-'}</td>
                        <td className="px-1 py-1.5 text-center">{evA.answer_relevance ?? '-'}</td>
                        <td className="px-1 py-1.5 text-center">{evA.context_relevance ?? '-'}</td>
                        <td className="px-1 py-1.5 text-center">{evA.groundedness ?? '-'}</td>
                        {runB && (
                          <>
                            <td className="px-1 py-1.5 text-center">{evB.bleu ?? '-'}</td>
                            <td className="px-1 py-1.5 text-center">{evB.rouge ?? '-'}</td>
                            <td className="px-1 py-1.5 text-center">{evB.answer_relevance ?? '-'}</td>
                            <td className="px-1 py-1.5 text-center">{evB.context_relevance ?? '-'}</td>
                            <td className="px-1 py-1.5 text-center">{evB.groundedness ?? '-'}</td>
                          </>
                        )}
                        <td className="px-2 py-1.5 text-right">
                          <button disabled className="px-2 py-0.5 text-xs border border-secondary rounded-md cursor-not-allowed opacity-60 font-body" title="Not implemented yet">Run</button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}
          </>
        )}

        {/* Recent Runs Tab */}
        {activeTab === 'recent' && (
          <section className="space-y-3">
            <div className="border border-secondary rounded-lg p-3">
              <div className="font-heading font-semibold text-sm text-text mb-2">Recent Runs ({runs.length})</div>
              {runs.length === 0 ? (
                <div className="font-body text-xs text-text/60">No runs yet.</div>
              ) : (
                <div className="space-y-3">
                  {runs.map((r) => {
                    const p = r.prompt_id ? promptsMap.get(r.prompt_id) : null;
                    const evMap = evalsByRun[r.id] || {};
                    const loading = !!evalsLoading[r.id];
                    return (
                      <div key={r.id} className="border border-secondary rounded-md">
                        <div className="px-3 py-2 flex items-start justify-between gap-3 bg-secondary/10">
                          <div className="min-w-0 flex-1">
                            <div className="font-body text-sm text-text">Run {r.id.slice(0,8)} · {r.created_at ? formatDate(r.created_at) : ''}</div>
                            <div className="font-body text-xs text-text/70">
                              Prompt: {p?.name || (r.prompt_id ? r.prompt_id.slice(0,8) : '—')}
                              {p?.prompt && (
                                <button onClick={() => toggleRecentPrompt(r.id)} className="ml-2 text-primary hover:underline cursor-pointer">
                                  {expandedRecentPrompts.has(r.id) ? 'Hide' : 'Show'}
                                </button>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {r.prompt_id && (
                              <button onClick={() => runAgain(r.prompt_id)} className="px-2 py-0.5 text-xs border border-primary text-primary rounded-md hover:bg-primary/10 cursor-pointer font-body">Run Again</button>
                            )}
                          </div>
                        </div>
                        {p?.prompt && expandedRecentPrompts.has(r.id) && (
                          <div className="px-3 py-2 border-t border-secondary">
                            <div className="font-body text-xs text-text/60 mb-1">Prompt Text</div>
                            <pre className="whitespace-pre-wrap font-body text-xs text-text bg-background rounded-md p-2 border border-secondary">{p.prompt}</pre>
                          </div>
                        )}
                        <div className="px-3 py-2 border-t border-secondary">
                          <div className="font-heading font-semibold text-xs text-text mb-2">QA Metrics</div>
                          {loading ? (
                            <div className="font-body text-xs text-text/60">Loading metrics…</div>
                          ) : (
                            <div className="overflow-x-auto">
                              <table className="min-w-full text-xs font-body">
                                <thead className="bg-secondary/10">
                                  <tr>
                                    <th className="text-left px-2 py-1.5 text-text/70 font-medium text-xs">Question</th>
                                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">BLEU</th>
                                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">ROUGE</th>
                                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">AnsRel</th>
                                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">CtxRel</th>
                                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">Ground</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-secondary/30">
                                  {qaSet.map((qa) => {
                                    const ev = evMap[qa.id] || {};
                                    return (
                                      <tr key={qa.id} className="bg-background/60">
                                        <td className="px-2 py-1.5 align-top max-w-[280px]">
                                          <div className="text-text font-medium truncate text-xs" title={qa.question}>Q: {qa.question}</div>
                                          <div className="text-text/70 text-xs line-clamp-1">A: {qa.answer}</div>
                                        </td>
                                        <td className="px-1 py-1.5 text-center">{ev.bleu ?? '-'}</td>
                                        <td className="px-1 py-1.5 text-center">{ev.rouge ?? '-'}</td>
                                        <td className="px-1 py-1.5 text-center">{ev.answer_relevance ?? '-'}</td>
                                        <td className="px-1 py-1.5 text-center">{ev.context_relevance ?? '-'}</td>
                                        <td className="px-1 py-1.5 text-center">{ev.groundedness ?? '-'}</td>
                                      </tr>
                                    );
                                  })}
                                </tbody>
                              </table>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </section>
        )}

        {/* Prompts Tab */}
        {activeTab === 'prompts' && (
          <section className="space-y-3">
            <div className="border border-secondary rounded-lg p-3">
              <div className="flex items-center gap-2 border-b border-secondary/40 mb-3">
                <button onClick={() => setPromptsTab('view')} className={`px-2 py-1 text-xs font-body ${promptsTab==='view' ? 'text-primary border-b-2 border-primary' : 'text-text/60 hover:text-text'}`}>View</button>
                <button onClick={() => setPromptsTab('create')} className={`px-2 py-1 text-xs font-body ${promptsTab==='create' ? 'text-primary border-b-2 border-primary' : 'text-text/60 hover:text-text'}`}>Create</button>
              </div>

              {promptsTab === 'view' ? (
                <div>
                  {promptsLoading ? (
                    <div className="font-body text-text/60 text-sm">Loading…</div>
                  ) : prompts.length === 0 ? (
                    <div className="font-body text-text/60 text-sm">No prompts yet.</div>
                  ) : (
                    <div className="divide-y divide-secondary/30">
                      {prompts.map((p) => (
                        <div key={p.id} className="py-2">
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0 flex-1">
                              <div className="font-heading font-semibold text-sm text-text">{p.name}</div>
                              <button onClick={() => togglePromptExpanded(p.id)} className="font-body text-xs text-primary hover:underline cursor-pointer">{expandedPrompts.has(p.id) ? 'Hide' : 'Show'} prompt</button>
                              {expandedPrompts.has(p.id) && (
                                <pre className="whitespace-pre-wrap font-body text-xs text-text bg-background rounded-md p-2 mt-2 border border-secondary">{p.prompt}</pre>
                              )}
                            </div>
                            <button onClick={() => handleDeletePrompt(p.id)} className="text-xs text-red-600 hover:text-red-700 cursor-pointer font-body">Delete</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-6 bg-gradient-to-br from-secondary/5 to-transparent">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-heading font-bold text-lg text-text mb-1 flex items-center gap-2">
                        <span className="w-2 h-2 bg-primary rounded-full animate-pulse"></span>
                        Create New Prompt
                      </h3>
                      <p className="font-body text-text/60 text-xs">
                        Your prompt must include <code className="bg-primary/20 text-primary px-1.5 py-0.5 rounded font-mono text-xs">{'{' + '{question}' + '}'}</code> and <code className="bg-accent/20 text-accent px-1.5 py-0.5 rounded font-mono text-xs">{'{' + '{context}' + '}'}</code> variables
                      </p>
                    </div>

                    {/* Info Tooltip */}
                    <div className="relative">
                      <button
                        type="button"
                        onMouseEnter={() => setShowInfoTooltip(true)}
                        onMouseLeave={() => setShowInfoTooltip(false)}
                        className="w-8 h-8 rounded-full bg-primary/10 hover:bg-primary/20 flex items-center justify-center text-primary transition-colors cursor-help"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </button>

                      {/* Tooltip */}
                      {showInfoTooltip && (
                        <div className="absolute right-0 top-10 w-72 bg-white rounded-lg shadow-2xl border-2 border-primary/20 p-4 z-10 animate-fadeIn">
                          <div className="flex items-start gap-2 mb-3">
                            <svg className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                            <div>
                              <h4 className="font-heading font-bold text-sm text-text mb-1">How to use variables</h4>
                              <p className="font-body text-xs text-text/70">Add these placeholders to your prompt:</p>
                            </div>
                          </div>

                          <div className="space-y-2 mb-3">
                            <div className="bg-primary/5 rounded-md p-2 border border-primary/20">
                              <code className="font-mono font-bold text-primary text-xs">{'{' + '{question}' + '}'}</code>
                              <p className="font-body text-xs text-text/70 mt-1">
                                This will be replaced with the actual question from your QA pairs.
                              </p>
                            </div>

                            <div className="bg-accent/5 rounded-md p-2 border border-accent/20">
                              <code className="font-mono font-bold text-accent text-xs">{'{' + '{context}' + '}'}</code>
                              <p className="font-body text-xs text-text/70 mt-1">
                                This will be replaced with relevant context retrieved for the question.
                              </p>
                            </div>
                          </div>

                          <div className="bg-secondary/10 rounded-md p-2">
                            <p className="font-body text-xs text-text/80 font-medium mb-1">💡 Quick Tips:</p>
                            <ul className="font-body text-xs text-text/70 space-y-0.5 ml-3 list-disc">
                              <li>Click the insert buttons below to add variables</li>
                              <li>Or type them manually with double curly braces</li>
                              <li>Position your cursor where you want to insert</li>
                            </ul>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <form onSubmit={handleCreatePrompt} className="space-y-4">
                    {/* Prompt Name Input */}
                    <div>
                      <label className="font-body text-xs font-medium text-text mb-1.5 block">
                        Prompt Name *
                      </label>
                      <input
                        type="text"
                        className="w-full border-2 border-secondary rounded-lg px-4 py-2 font-body text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-text"
                        placeholder="e.g., QA Assistant, Context-Based Answering..."
                        value={newPromptName}
                        onChange={(e) => setNewPromptName(e.target.value)}
                        required
                      />
                    </div>

                    {/* Write/Preview Tab Switcher */}
                    <div className="flex gap-2 bg-secondary/20 p-1 rounded-lg w-fit shadow-inner">
                      <button
                        type="button"
                        onClick={() => {
                          setPreviewMode(false);
                          setValidationError('');
                        }}
                        className={`px-4 py-1.5 rounded-md font-body text-xs font-bold transition-all ${
                          !previewMode
                            ? 'bg-gradient-to-r from-primary to-accent text-white shadow-md'
                            : 'text-text/70 hover:text-text'
                        }`}
                      >
                        ✏️ Write
                      </button>
                      <button
                        type="button"
                        onClick={() => setPreviewMode(true)}
                        className={`px-4 py-1.5 rounded-md font-body text-xs font-bold transition-all ${
                          previewMode
                            ? 'bg-gradient-to-r from-primary to-accent text-white shadow-md'
                            : 'text-text/70 hover:text-text'
                        }`}
                      >
                        👁️ Preview
                      </button>
                    </div>

                    {/* Validation Error */}
                    {validationError && (
                      <div className="bg-red-50 border-2 border-red-400 rounded-lg p-3 flex items-start gap-2">
                        <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <div className="flex-1">
                          <div className="font-body font-bold text-red-900 text-sm">{validationError}</div>
                          <div className="font-body text-xs text-red-700 mt-0.5">
                            Please include both required variables in your prompt.
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Quick Insert Buttons */}
                    {!previewMode && (
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-body text-xs text-text/60 font-medium">Quick Insert:</span>
                        <button
                          type="button"
                          onClick={() => insertVariable('{{question}}')}
                          className="px-3 py-1.5 bg-primary/10 hover:bg-primary/20 border-2 border-primary/30 text-primary rounded-md font-mono text-xs font-bold transition-all hover:scale-105 flex items-center gap-1.5"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                          </svg>
                          {'{' + '{question}' + '}'}
                        </button>
                        <button
                          type="button"
                          onClick={() => insertVariable('{{context}}')}
                          className="px-3 py-1.5 bg-accent/10 hover:bg-accent/20 border-2 border-accent/30 text-accent rounded-md font-mono text-xs font-bold transition-all hover:scale-105 flex items-center gap-1.5"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                          </svg>
                          {'{' + '{context}' + '}'}
                        </button>
                        <div className="ml-1 font-body text-xs text-text/50 italic">
                          Click to insert at cursor position
                        </div>
                      </div>
                    )}

                    {/* Input/Preview Area */}
                    <div className="relative">
                      {!previewMode ? (
                        <div>
                          <textarea
                            ref={setTextareaRef}
                            className={`w-full border-2 rounded-lg px-4 py-3 font-body text-sm min-h-[200px] focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-text resize-y ${
                              validationError ? 'border-red-400' : 'border-secondary'
                            }`}
                            placeholder="Write your prompt here...

**Example:**
You are a helpful AI assistant. Use the following context to answer the question.

**Context:** {{context}}

**Question:** {{question}}

**Instructions:**
- Provide clear and concise answers
- Use the context provided
- If unsure, acknowledge limitations"
                            value={newPromptText}
                            onChange={(e) => {
                              setNewPromptText(e.target.value);
                              if (validationError) setValidationError('');
                            }}
                            required
                          />
                          <div className="mt-2 flex items-center gap-3 text-xs">
                            <div className={`flex items-center gap-1.5 ${newPromptText.includes('{{question}}') ? 'text-green-600' : 'text-text/40'}`}>
                              {newPromptText.includes('{{question}}') ? (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              ) : (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              )}
                              <code className="font-mono font-bold">{'{' + '{question}' + '}'}</code>
                            </div>
                            <div className={`flex items-center gap-1.5 ${newPromptText.includes('{{context}}') ? 'text-green-600' : 'text-text/40'}`}>
                              {newPromptText.includes('{{context}}') ? (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              ) : (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              )}
                              <code className="font-mono font-bold">{'{' + '{context}' + '}'}</code>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="border-2 border-secondary rounded-lg p-4 bg-secondary/5 min-h-[200px]">
                          <div className="flex items-center gap-2 mb-3 pb-2 border-b border-secondary/30">
                            <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            <span className="font-body text-xs font-bold text-text/70">Preview</span>
                          </div>
                          <pre className="whitespace-pre-wrap font-body text-sm text-text/90">{newPromptText || '(empty)'}</pre>
                        </div>
                      )}
                    </div>

                    <button
                      disabled={creatingPrompt || !newPromptName.trim() || !newPromptText.trim()}
                      className="px-4 py-2 text-sm bg-gradient-to-r from-primary to-accent text-white rounded-lg hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer font-body font-medium transition-all"
                    >
                      {creatingPrompt ? 'Creating…' : 'Create Prompt'}
                    </button>
                  </form>
                </div>
              )}
            </div>
          </section>
        )}
      </main>

      {/* Create Run Modal */}
      {runModal?.open && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-40">
          <div className="bg-background border border-secondary rounded-lg w-full max-w-md">
            <div className="p-3 border-b border-secondary flex items-center justify-between">
              <div className="font-heading font-bold text-text">Create Test Run</div>
              <button onClick={() => setRunModal(null)} className="text-text/60 hover:text-text cursor-pointer font-body text-sm">✕ Close</button>
            </div>
            <div className="p-3 space-y-3">
              <div>
                <label className="font-body text-xs font-medium text-text mb-1 block">Choose Prompt</label>
                {runModalLoading ? (
                  <div className="font-body text-text/60 text-sm">Loading prompts…</div>
                ) : (
                  <select value={chosenPromptId} onChange={(e) => setChosenPromptId(e.target.value)} className="w-full border border-secondary rounded-lg px-2 py-1.5 text-xs font-body bg-background">
                    <option value="">Select a prompt</option>
                    {runModalPrompts.map((p) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                )}
              </div>
              <div className="flex justify-end gap-2">
                <button onClick={() => setRunModal(null)} className="px-3 py-1.5 text-xs border border-secondary rounded-md hover:bg-secondary/20 cursor-pointer font-body">Cancel</button>
                <button onClick={handleCreateRun} disabled={creatingRun || !chosenPromptId} className="px-3 py-1.5 text-xs bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 cursor-pointer font-body font-medium">
                  {creatingRun ? 'Creating…' : 'Create Run'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
