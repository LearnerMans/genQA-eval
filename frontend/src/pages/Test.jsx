import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useToast } from '../components/Toaster.jsx';
import { API_BASE_URL, projectsAPI, testsAPI, qaAPI, promptsAPI, testRunsAPI, evalsAPI } from '../services/api';
import Logo from '../components/Logo';

const stageDescriptions = {
  queued: 'Queued',
  started: 'Starting',
  contexts_retrieved: 'Contexts ready',
  answer_generated: 'Answer generated',
  lexical_metrics_calculated: 'Scoring lexical metrics',
  llm_metrics_calculated: 'Running GPT-5 evaluation',
  saved: 'Saving results',
  failed: 'Failed'
};

const describeStage = (stage) => {
  if (!stage) return '';
  return stageDescriptions[stage] || stage.replace(/_/g, ' ');
};

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
  const [runProgress, setRunProgress] = useState({}); // { [runId]: { [qaId]: status } }
  const evalSocketsRef = useRef(new Map());

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

  // Pagination for QA metrics table in each run (Recent Runs tab)
  const [qaMetricsPage, setQaMetricsPage] = useState({});
  const qaMetricsPerPage = 10;

  // Pagination for main QA Results table (Test Runs tab)
  const [qaResultsPage, setQaResultsPage] = useState(1);
  const qaResultsPerPage = 10;

  // Filters for QA Results table
  const [qaFilters, setQaFilters] = useState({
    bleuMin: '',
    bleuMax: '',
    rougeMin: '',
    rougeMax: '',
    ansRelMin: '',
    ansRelMax: '',
    ctxRelMin: '',
    ctxRelMax: '',
    groundMin: '',
    groundMax: '',
    runStatus: 'all' // 'all', 'completed', 'pending'
  });
  const [showFilters, setShowFilters] = useState(false);

  const activeRunIds = useMemo(() => selectedRuns.filter(Boolean), [selectedRuns]);
  const activeRunsKey = useMemo(() => [...activeRunIds].sort().join(','), [activeRunIds]);

  const updateRunProgress = useCallback((runId, qaId, updater) => {
    setRunProgress((prev) => {
      const next = { ...prev };
      const runEntry = { ...(next[runId] || {}) };
      const previous = runEntry[qaId] || {};
      const patch = typeof updater === 'function' ? updater(previous) : updater;
      runEntry[qaId] = {
        ...previous,
        ...patch,
        updatedAt: Date.now()
      };
      next[runId] = runEntry;
      return next;
    });
  }, []);

  const updateEvalMetrics = useCallback((runId, qaId, partial) => {
    if (!partial) return;
    setEvalsByRun((prev) => {
      const next = { ...prev };
      const runEntry = { ...(next[runId] || {}) };
      const previous = runEntry[qaId] || {};
      runEntry[qaId] = { ...previous, ...partial };
      next[runId] = runEntry;
      return next;
    });
  }, []);

  const handleEvaluationMessage = useCallback((message) => {
    if (!message || message.type !== 'evaluation_progress') return;

    const {
      test_run_id: runId,
      qa_pair_id: qaId,
      event,
      stage,
      status,
      data,
      result,
      error
    } = message;

    updateRunProgress(runId, qaId, (prev = {}) => {
      const next = { ...prev, lastEvent: event };

      if (event === 'status') {
        next.status = status;
        next.stage = status === 'queued' ? 'queued' : stage || next.stage;
        next.error = undefined;
      } else if (event === 'progress') {
        const derivedStatus = status || (stage === 'failed' ? 'failed' : 'running');
        next.status = derivedStatus;
        if (stage) next.stage = stage;
        next.error = error;
      } else if (event === 'completed') {
        next.status = status || 'completed';
        next.stage = 'completed';
        next.error = undefined;
      } else if (event === 'error') {
        next.status = 'failed';
        next.stage = 'failed';
        next.error = error;
      }

      return next;
    });

    if (event === 'progress') {
      if (stage === 'lexical_metrics_calculated' && data) {
        updateEvalMetrics(runId, qaId, {
          bleu: data.bleu ?? null,
          rouge: data.rouge_l ?? data.rouge ?? null,
          rouge_l_precision: data.rouge_l_precision,
          rouge_l_recall: data.rouge_l_recall,
          squad_em: data.squad_em,
          squad_token_f1: data.squad_token_f1,
          content_f1: data.content_f1,
          lexical_aggregate: data.lexical_aggregate
        });
      } else if (stage === 'llm_metrics_calculated' && data) {
        updateEvalMetrics(runId, qaId, {
          answer_relevance: data.answer_relevance ?? null,
          context_relevance: data.context_relevance ?? null,
          groundedness: data.groundedness ?? null,
          llm_judged_overall: data.llm_judged_overall ?? null
        });
      } else if (stage === 'saved' && data?.eval_id) {
        updateEvalMetrics(runId, qaId, { eval_id: data.eval_id });
      }

      if ((status === 'failed' || stage === 'failed') && error) {
        toast.error(error);
      }
    } else if (event === 'completed' && result) {
      updateEvalMetrics(runId, qaId, {
        bleu: result.lexical_metrics?.bleu ?? null,
        rouge: result.lexical_metrics?.rouge_l ?? null,
        rouge_l_precision: result.lexical_metrics?.rouge_l_precision,
        rouge_l_recall: result.lexical_metrics?.rouge_l_recall,
        squad_em: result.lexical_metrics?.squad_em,
        squad_token_f1: result.lexical_metrics?.squad_token_f1,
        content_f1: result.lexical_metrics?.content_f1,
        lexical_aggregate: result.lexical_metrics?.lexical_aggregate,
        answer_relevance: result.llm_judged_metrics?.answer_relevance ?? null,
        context_relevance: result.llm_judged_metrics?.context_relevance ?? null,
        groundedness: result.llm_judged_metrics?.groundedness ?? null,
        llm_judged_overall: result.llm_judged_metrics?.llm_judged_overall ?? result.llm_judged_metrics?.overall_score ?? null,
        generated_answer: result.generated_answer,
        eval_id: result.eval_id,
        contexts: result.contexts,
        llm_judged_reasoning: result.llm_judged_reasoning ?? null
      });
    } else if (event === 'error' && error) {
      toast.error(error);
    }
  }, [toast, updateEvalMetrics, updateRunProgress]);

  const wsUrlForPath = useCallback((path) => {
    try {
      const url = new URL(path, API_BASE_URL);
      url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      return url.toString();
    } catch {
      const secure = API_BASE_URL.startsWith('https://');
      const base = API_BASE_URL.replace(/^https?:\/\//, '').replace(/\/$/, '');
      return `${secure ? 'wss://' : 'ws://'}${base}${path}`;
    }
  }, [API_BASE_URL]);

  const setupSocketForRun = useCallback((runId) => {
    const existing = evalSocketsRef.current.get(runId);
    if (existing) return;

    const wsUrl = wsUrlForPath(`/ws/evaluations/run/${runId}`);
    try {
      const socket = new WebSocket(wsUrl);
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          handleEvaluationMessage(payload);
        } catch (e) {
          console.error('Failed to parse evaluation message', e);
        }
      };
      socket.onerror = (event) => {
        console.error('Evaluation websocket error', event);
      };
      socket.onclose = () => {
        evalSocketsRef.current.delete(runId);
      };
      evalSocketsRef.current.set(runId, socket);
    } catch (e) {
      console.error('Failed to open evaluation websocket', e);
    }
  }, [handleEvaluationMessage, wsUrlForPath]);

  useEffect(() => {
    const sockets = evalSocketsRef.current;
    const desired = new Set(activeRunIds);

    // Close sockets for runs no longer selected
    for (const [runId, socket] of Array.from(sockets.entries())) {
      if (!desired.has(runId)) {
        try {
          socket.close();
        } catch (e) {
          console.error('Error closing evaluation websocket', e);
        }
        sockets.delete(runId);
      }
    }

    // Create sockets for new runs
    activeRunIds.forEach((runId) => {
      if (!sockets.has(runId)) {
        setupSocketForRun(runId);
      }
    });
  }, [activeRunIds, activeRunsKey, setupSocketForRun]);

  useEffect(() => {
    return () => {
      evalSocketsRef.current.forEach((socket) => {
        try {
          socket.close();
        } catch {
          /* noop */
        }
      });
      evalSocketsRef.current.clear();
    };
  }, []);

  const handleRunQa = useCallback(async (runId, qaId) => {
    if (!runId || !qaId) return;

    const existing = runProgress[runId]?.[qaId];
    if (existing && ['running', 'queued'].includes(existing.status)) {
      return;
    }

    updateRunProgress(runId, qaId, {
      status: 'queued',
      stage: 'queued',
      lastEvent: 'manual_start',
      error: undefined
    });

    try {
      await evalsAPI.run({ test_run_id: runId, qa_pair_id: qaId });
    } catch (e) {
      const message = e.message || 'Failed to start evaluation';
      updateRunProgress(runId, qaId, {
        status: 'failed',
        stage: 'failed',
        error: message
      });
      toast.error(message);
    }
  }, [runProgress, toast, updateRunProgress]);

  const runButtonLabel = useCallback((prefix, progress) => {
    if (!progress || !progress.status) return `Run ${prefix}`;
    if (progress.status === 'queued') return `${prefix} Queued`;
    if (progress.status === 'running') return `${prefix} Running…`;
    if (progress.status === 'failed') return `${prefix} Retry`;
    return `${prefix} Re-run`;
  }, []);

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

  // When switching to Recent Runs tab, lazily load evals for all runs
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

  // Build a friendly label for a run using its prompt name if available
  const labelForRun = (r) => {
    if (!r) return '';
    const p = r.prompt_id ? promptsMap.get(r.prompt_id) : null;
    const base = p?.name || (r.prompt_id ? `Prompt ${r.prompt_id.slice(0, 6)}` : 'Run');
    // Include short run id to disambiguate if names repeat
    return `${base}`;
  };

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

  const openEvalDetails = (runId, qaId) => {
    if (!runId || !qaId) return;
    window.location.hash = `#project/${projectId}/test/${testId}/run/${runId}/qa/${qaId}`;
  };

  const formatDate = (d) => (d ? new Date(d).toLocaleString() : 'N/A');

  // Helper to get current page for a run's QA table (default to 1)
  const getQaPage = (runId) => qaMetricsPage[runId] || 1;

  // Helper to set page for a run's QA table
  const setQaPage = (runId, page) => {
    setQaMetricsPage(prev => ({ ...prev, [runId]: page }));
  };

  // Calculate paginated QA set for a specific run (Recent Runs tab)
  const getPaginatedQaSet = (runId) => {
    const currentPage = getQaPage(runId);
    const startIndex = (currentPage - 1) * qaMetricsPerPage;
    const endIndex = startIndex + qaMetricsPerPage;
    return qaSet.slice(startIndex, endIndex);
  };

  // Filter and paginate QA Results
  const filteredQaResults = useMemo(() => {
    return qaSet.filter((qa) => {
      const runA = selectedRuns[0];
      const runB = selectedRuns[1];
      const evA = runA ? (evalsByRun[runA]?.[qa.id] || {}) : {};
      const evB = runB ? (evalsByRun[runB]?.[qa.id] || {}) : {};

      // Filter by run status (completed/pending)
      if (qaFilters.runStatus !== 'all') {
        const hasEvA = runA && Object.keys(evA).length > 0 && evA.bleu !== undefined;
        const hasEvB = runB && Object.keys(evB).length > 0 && evB.bleu !== undefined;

        if (qaFilters.runStatus === 'completed') {
          if (runB) {
            // Both runs must be completed
            if (!hasEvA || !hasEvB) return false;
          } else {
            // Only run A must be completed
            if (!hasEvA) return false;
          }
        } else if (qaFilters.runStatus === 'pending') {
          if (runB) {
            // At least one run must be pending
            if (hasEvA && hasEvB) return false;
          } else {
            // Run A must be pending
            if (hasEvA) return false;
          }
        }
      }

      // Filter by score ranges (check both runs)
      const checkScore = (value, min, max) => {
        // If no filters are set, everything passes
        if (min === '' && max === '') return true;

        // If filters are set but value is missing, it fails the filter
        if (value === null || value === undefined || value === '-') return false;

        const num = typeof value === 'number' ? value : parseFloat(value);
        if (isNaN(num)) return false;

        if (min !== '' && num < parseFloat(min)) return false;
        if (max !== '' && num > parseFloat(max)) return false;
        return true;
      };

      // BLEU filter
      if (qaFilters.bleuMin !== '' || qaFilters.bleuMax !== '') {
        const passA = runA ? checkScore(evA.bleu, qaFilters.bleuMin, qaFilters.bleuMax) : false;
        const passB = runB ? checkScore(evB.bleu, qaFilters.bleuMin, qaFilters.bleuMax) : false;
        if (!passA && !passB) return false;
      }

      // ROUGE-L filter
      if (qaFilters.rougeMin !== '' || qaFilters.rougeMax !== '') {
        const rougeA = evA.rouge_l ?? evA.rouge;
        const rougeB = evB.rouge_l ?? evB.rouge;
        const passA = runA ? checkScore(rougeA, qaFilters.rougeMin, qaFilters.rougeMax) : false;
        const passB = runB ? checkScore(rougeB, qaFilters.rougeMin, qaFilters.rougeMax) : false;
        if (!passA && !passB) return false;
      }

      // Answer Relevance filter
      if (qaFilters.ansRelMin !== '' || qaFilters.ansRelMax !== '') {
        const passA = runA ? checkScore(evA.answer_relevance, qaFilters.ansRelMin, qaFilters.ansRelMax) : false;
        const passB = runB ? checkScore(evB.answer_relevance, qaFilters.ansRelMin, qaFilters.ansRelMax) : false;
        if (!passA && !passB) return false;
      }

      // Context Relevance filter
      if (qaFilters.ctxRelMin !== '' || qaFilters.ctxRelMax !== '') {
        const passA = runA ? checkScore(evA.context_relevance, qaFilters.ctxRelMin, qaFilters.ctxRelMax) : false;
        const passB = runB ? checkScore(evB.context_relevance, qaFilters.ctxRelMin, qaFilters.ctxRelMax) : false;
        if (!passA && !passB) return false;
      }

      // Groundedness filter
      if (qaFilters.groundMin !== '' || qaFilters.groundMax !== '') {
        const passA = runA ? checkScore(evA.groundedness, qaFilters.groundMin, qaFilters.groundMax) : false;
        const passB = runB ? checkScore(evB.groundedness, qaFilters.groundMin, qaFilters.groundMax) : false;
        if (!passA && !passB) return false;
      }

      return true;
    });
  }, [qaSet, qaFilters, selectedRuns, evalsByRun]);

  // Paginate filtered results
  const paginatedQaResults = useMemo(() => {
    const startIndex = (qaResultsPage - 1) * qaResultsPerPage;
    const endIndex = startIndex + qaResultsPerPage;
    return filteredQaResults.slice(startIndex, endIndex);
  }, [filteredQaResults, qaResultsPage, qaResultsPerPage]);

  const totalQaResultsPages = Math.ceil(filteredQaResults.length / qaResultsPerPage);

  // Reset to page 1 when filters change
  useEffect(() => {
    setQaResultsPage(1);
  }, [qaFilters]);

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
          <p className="font-body text-danger">{error || 'Test not found'}</p>
          <button onClick={goBack} className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 cursor-pointer">Back</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="w-full max-w-6xl mx-auto px-3 py-4">
        <Logo size="sm" showText={true} />
        <div className="flex items-center justify-between mt-4">
          <nav className="flex items-center gap-1 text-sm">
            <button
              onClick={() => window.location.hash = `#project/${projectId}`}
              className="font-body text-primary hover:text-primary/80 cursor-pointer hover:underline transition-colors"
              title="Go to project"
            >
              {project?.name}
            </button>
            <svg className="w-3 h-3 text-text/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            <span className="font-body text-text/80 font-medium" title="Current test">
              {test.name}
            </span>
          </nav>
          <div className="flex items-center gap-2">
            <button onClick={goBack} className="font-body text-xs text-text/70 hover:text-text cursor-pointer" style={{ visibility: 'hidden' }}>← Back to Project</button>
          </div>
        </div>

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
            <section className="border border-secondary rounded-lg p-2 bg-secondary/10">
              {/* Aligned 3-column grid with fixed action column width (compact) */}
              <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_2.25rem] gap-2 items-end">

                {/* Row 1: selectors */}
                <div className="min-w-0">
                  <div className="text-[11px] leading-none font-body text-text/60 mb-0.5">Test Run 1</div>
                  <div className="relative">
                    <select
                      onFocus={() => { if (!runs || runs.length === 0) loadRuns(); }}
                      value={selectedRuns[0] || ''}
                      onChange={(e) => handleSelectRun(0, e.target.value)}
                      className="w-full h-9 appearance-none border border-secondary rounded-md px-2 pr-6 text-xs font-body bg-background hover:border-primary focus:border-primary focus:ring-1 focus:ring-primary cursor-pointer"
                    >
                      <option value="" disabled="">Select a run</option>
                      {(runs || []).map((r) => (
                        <option key={r.id} value={r.id}>{labelForRun(r)}</option>
                      ))}
                      <option value="__new__">+ New Run…</option>
                    </select>
                    <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-text/40 text-xs">▾</div>
                  </div>
                </div>

                {!secondRunEnabled ? (
                  <div className="min-w-0 self-end flex items-end">
                    <button
                      onClick={enableSecondRun}
                      className="inline-flex items-center justify-center h-9 px-3 text-xs font-body font-medium bg-primary text-white rounded-md hover:bg-primary/90 cursor-pointer transition-colors"
                      title="Compare with another run"
                      aria-label="Compare with another run"
                    >
                      Compare
                    </button>
                  </div>
                ) : (
                  <div className="min-w-0">
                    <div className="text-[11px] leading-none font-body text-text/60 mb-0.5">Test Run 2</div>
                    <div className="relative">
                      <select
                        onFocus={() => { if (!runs || runs.length === 0) loadRuns(); }}
                        value={selectedRuns[1] || ''}
                        onChange={(e) => handleSelectRun(1, e.target.value)}
                        className="w-full h-9 appearance-none border border-secondary rounded-md px-2 pr-6 text-xs font-body bg-background hover:border-primary focus:border-primary focus:ring-1 focus:ring-primary cursor-pointer"
                      >
                        <option value="" disabled="">Select a run</option>
                        {(runs || []).map((r) => (
                          <option key={r.id} value={r.id}>{labelForRun(r)}</option>
                        ))}
                        <option value="__new__">+ New Run…</option>
                      </select>
                      <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-text/40 text-xs">▾</div>
                    </div>
                  </div>
                )}

                {/* Close button cell (fixed width) */}
                <div className="flex items-end justify-end self-end">
                  {secondRunEnabled ? (
                    <button
                      onClick={() => {
                        setSecondRunEnabled(false);
                        setSelectedRuns([selectedRuns[0], null]);
                      }}
                      className="inline-flex items-center justify-center h-9 w-9 text-sm font-body text-text/70 hover:text-text cursor-pointer border border-secondary/60 rounded-md hover:border-secondary transition-colors"
                      title="Remove comparison"
                      aria-label="Remove comparison"
                    >
                      ×
                    </button>
                  ) : (
                    <div className="h-9 w-9" aria-hidden="true"></div>
                  )}
                </div>

                {runsLoading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary col-span-full"></div>}
              </div>
            {/* Prompt name + preview row, compact and aligned */}
            {(selectedRuns[0] || (secondRunEnabled && selectedRuns[1])) && (
              <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_2.25rem] gap-2 mt-0.5">
                <div className="min-w-0">
                  {selectedRuns[0] && (
                    <div className="text-[11px] font-body text-text/80">
                      <div className="flex items-center gap-1 mt-0.5">
                        <span className="font-medium truncate">
                          {promptsMap.get(runs.find((r)=>r.id===selectedRuns[0])?.prompt_id)?.name || runs.find((r)=>r.id===selectedRuns[0])?.prompt_id || '—'}
                        </span>
                        <button onClick={() => toggleRunPrompt(selectedRuns[0])} className="text-primary hover:underline cursor-pointer">
                          {expandedRunPrompts.has(selectedRuns[0]) ? 'Hide' : 'Preview'}
                        </button>
                      </div>
                      {expandedRunPrompts.has(selectedRuns[0]) && (
                        <pre className="mt-1 whitespace-pre-wrap border border-secondary rounded-md p-2 bg-background text-text/90 text-[11px] max-h-40 overflow-auto">
                          {promptsMap.get(runs.find((r)=>r.id===selectedRuns[0])?.prompt_id)?.prompt || '(no prompt text)'}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
                <div className="min-w-0">
                  {secondRunEnabled && selectedRuns[1] && (
                    <div className="text-[11px] font-body text-text/80">
                      <div className="flex items-center gap-1 mt-0.5">
                        <span className="font-medium truncate">
                          {promptsMap.get(runs.find((r)=>r.id===selectedRuns[1])?.prompt_id)?.name || runs.find((r)=>r.id===selectedRuns[1])?.prompt_id || '—'}
                        </span>
                        <button onClick={() => toggleRunPrompt(selectedRuns[1])} className="text-primary hover:underline cursor-pointer">
                          {expandedRunPrompts.has(selectedRuns[1]) ? 'Hide' : 'Preview'}
                        </button>
                      </div>
                      {expandedRunPrompts.has(selectedRuns[1]) && (
                        <pre className="mt-1 whitespace-pre-wrap border border-secondary rounded-md p-2 bg-background text-text/90 text-[11px] max-h-40 overflow-auto">
                          {promptsMap.get(runs.find((r)=>r.id===selectedRuns[1])?.prompt_id)?.prompt || '(no prompt text)'}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
                {/* Empty cell under the close button to maintain exact column widths */}
                <div className="h-9" aria-hidden="true"></div>
              </div>
            )}
          </section>


        {/* QA Results */}
        {(selectedRuns[0] || selectedRuns[1]) && (
          <section className="border border-secondary rounded-lg overflow-hidden">
            <div className="bg-secondary/20 px-2 py-1.5 font-heading text-xs text-text/80 border-b border-secondary flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span>QA Results</span>
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="px-2 py-0.5 text-xs border border-secondary rounded-md hover:bg-secondary/10 cursor-pointer font-body"
                >
                  {showFilters ? '− Hide Filters' : '+ Show Filters'}
                </button>
                {filteredQaResults.length !== qaSet.length && (
                  <span className="text-xs text-primary font-body">
                    ({filteredQaResults.length} of {qaSet.length})
                  </span>
                )}
              </div>
              {totalQaResultsPages > 1 && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setQaResultsPage(p => Math.max(1, p - 1))}
                    disabled={qaResultsPage === 1}
                    className="px-2 py-0.5 text-xs border border-secondary rounded-md hover:bg-secondary/10 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer font-body"
                  >
                    ← Prev
                  </button>
                  <span className="font-body text-xs text-text/70">
                    Page {qaResultsPage} of {totalQaResultsPages}
                  </span>
                  <button
                    onClick={() => setQaResultsPage(p => Math.min(totalQaResultsPages, p + 1))}
                    disabled={qaResultsPage === totalQaResultsPages}
                    className="px-2 py-0.5 text-xs border border-secondary rounded-md hover:bg-secondary/10 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer font-body"
                  >
                    Next →
                  </button>
                </div>
              )}
            </div>

            {/* Filter Panel */}
            {showFilters && (
              <div className="bg-secondary/5 px-3 py-3 border-b border-secondary">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-3">
                  {/* BLEU Filter */}
                  <div>
                    <label className="font-body text-xs text-text/70 block mb-1">BLEU</label>
                    <div className="flex gap-1">
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="1"
                        placeholder="Min"
                        value={qaFilters.bleuMin}
                        onChange={(e) => setQaFilters({...qaFilters, bleuMin: e.target.value})}
                        className="w-full px-2 py-1 text-xs border border-secondary rounded-md bg-background font-body"
                      />
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="1"
                        placeholder="Max"
                        value={qaFilters.bleuMax}
                        onChange={(e) => setQaFilters({...qaFilters, bleuMax: e.target.value})}
                        className="w-full px-2 py-1 text-xs border border-secondary rounded-md bg-background font-body"
                      />
                    </div>
                  </div>

                  {/* ROUGE-L Filter */}
                  <div>
                    <label className="font-body text-xs text-text/70 block mb-1">ROUGE-L</label>
                    <div className="flex gap-1">
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="1"
                        placeholder="Min"
                        value={qaFilters.rougeMin}
                        onChange={(e) => setQaFilters({...qaFilters, rougeMin: e.target.value})}
                        className="w-full px-2 py-1 text-xs border border-secondary rounded-md bg-background font-body"
                      />
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="1"
                        placeholder="Max"
                        value={qaFilters.rougeMax}
                        onChange={(e) => setQaFilters({...qaFilters, rougeMax: e.target.value})}
                        className="w-full px-2 py-1 text-xs border border-secondary rounded-md bg-background font-body"
                      />
                    </div>
                  </div>

                  {/* Answer Relevance Filter */}
                  <div>
                    <label className="font-body text-xs text-text/70 block mb-1">AnsRel</label>
                    <div className="flex gap-1">
                      <input
                        type="number"
                        step="1"
                        min="0"
                        max="5"
                        placeholder="Min"
                        value={qaFilters.ansRelMin}
                        onChange={(e) => setQaFilters({...qaFilters, ansRelMin: e.target.value})}
                        className="w-full px-2 py-1 text-xs border border-secondary rounded-md bg-background font-body"
                      />
                      <input
                        type="number"
                        step="1"
                        min="0"
                        max="5"
                        placeholder="Max"
                        value={qaFilters.ansRelMax}
                        onChange={(e) => setQaFilters({...qaFilters, ansRelMax: e.target.value})}
                        className="w-full px-2 py-1 text-xs border border-secondary rounded-md bg-background font-body"
                      />
                    </div>
                  </div>

                  {/* Context Relevance Filter */}
                  <div>
                    <label className="font-body text-xs text-text/70 block mb-1">CtxRel</label>
                    <div className="flex gap-1">
                      <input
                        type="number"
                        step="1"
                        min="0"
                        max="5"
                        placeholder="Min"
                        value={qaFilters.ctxRelMin}
                        onChange={(e) => setQaFilters({...qaFilters, ctxRelMin: e.target.value})}
                        className="w-full px-2 py-1 text-xs border border-secondary rounded-md bg-background font-body"
                      />
                      <input
                        type="number"
                        step="1"
                        min="0"
                        max="5"
                        placeholder="Max"
                        value={qaFilters.ctxRelMax}
                        onChange={(e) => setQaFilters({...qaFilters, ctxRelMax: e.target.value})}
                        className="w-full px-2 py-1 text-xs border border-secondary rounded-md bg-background font-body"
                      />
                    </div>
                  </div>

                  {/* Groundedness Filter */}
                  <div>
                    <label className="font-body text-xs text-text/70 block mb-1">Ground</label>
                    <div className="flex gap-1">
                      <input
                        type="number"
                        step="1"
                        min="0"
                        max="5"
                        placeholder="Min"
                        value={qaFilters.groundMin}
                        onChange={(e) => setQaFilters({...qaFilters, groundMin: e.target.value})}
                        className="w-full px-2 py-1 text-xs border border-secondary rounded-md bg-background font-body"
                      />
                      <input
                        type="number"
                        step="1"
                        min="0"
                        max="5"
                        placeholder="Max"
                        value={qaFilters.groundMax}
                        onChange={(e) => setQaFilters({...qaFilters, groundMax: e.target.value})}
                        className="w-full px-2 py-1 text-xs border border-secondary rounded-md bg-background font-body"
                      />
                    </div>
                  </div>

                  {/* Run Status Filter */}
                  <div>
                    <label className="font-body text-xs text-text/70 block mb-1">Status</label>
                    <select
                      value={qaFilters.runStatus}
                      onChange={(e) => setQaFilters({...qaFilters, runStatus: e.target.value})}
                      className="w-full px-2 py-1 text-xs border border-secondary rounded-md bg-background font-body h-[26px]"
                    >
                      <option value="all">All</option>
                      <option value="completed">Completed</option>
                      <option value="pending">Pending</option>
                    </select>
                  </div>
                </div>

                {/* Clear Filters Button */}
                <button
                  onClick={() => setQaFilters({
                    bleuMin: '', bleuMax: '', rougeMin: '', rougeMax: '',
                    ansRelMin: '', ansRelMax: '', ctxRelMin: '', ctxRelMax: '',
                    groundMin: '', groundMax: '', runStatus: 'all'
                  })}
                  className="px-3 py-1 text-xs border border-secondary rounded-md hover:bg-secondary/10 cursor-pointer font-body"
                >
                  Clear All Filters
                </button>
              </div>
            )}
            <div className="overflow-x-auto max-h-[900px] overflow-y-auto">
              <table className="min-w-full text-xs font-body">
                <thead className="bg-secondary/10 sticky top-0 z-10">
                  <tr>
                    <th className="text-left px-2 py-1.5 text-text/70 font-medium text-xs">Question</th>
                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">A BLEU</th>
                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">A ROUGE-L</th>
                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">A AnsRel</th>
                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">A CtxRel</th>
                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">A Ground</th>
                    {selectedRuns[1] && (
                      <>
                        <th className="px-1 py-1.5 text-text/70 font-medium text-xs">B BLEU</th>
                        <th className="px-1 py-1.5 text-text/70 font-medium text-xs">B ROUGE-L</th>
                        <th className="px-1 py-1.5 text-text/70 font-medium text-xs">B AnsRel</th>
                        <th className="px-1 py-1.5 text-text/70 font-medium text-xs">B CtxRel</th>
                        <th className="px-1 py-1.5 text-text/70 font-medium text-xs">B Ground</th>
                      </>
                    )}
                    <th className="px-2 py-1.5 text-right"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-secondary/30">
                  {paginatedQaResults.map((qa) => {
                    const runA = selectedRuns[0];
                    const runB = selectedRuns[1];
                    const evA = runA ? (evalsByRun[runA]?.[qa.id] || {}) : {};
                    const evB = runB ? (evalsByRun[runB]?.[qa.id] || {}) : {};
                    const progressA = runA ? (runProgress[runA]?.[qa.id] || null) : null;
                    const progressB = runB ? (runProgress[runB]?.[qa.id] || null) : null;
                    return (
                      <tr key={qa.id} className="bg-background/60 hover:bg-secondary/10">
                        <td className="px-2 py-1.5 align-top max-w-[320px]">
                          <div className="text-text font-medium truncate text-xs" title={qa.question}>Q: {qa.question}</div>
                          <div className="text-text/70 text-xs line-clamp-1">A: {qa.answer}</div>
                          {runA && evA.generated_answer && (
                            <div
                              className="text-primary/70 text-[11px] mt-0.5 line-clamp-2"
                              title={evA.generated_answer}
                            >
                              A Gen: {evA.generated_answer}
                            </div>
                          )}
                          {runB && evB.generated_answer && (
                            <div
                              className="text-accent/70 text-[11px] mt-0.5 line-clamp-2"
                              title={evB.generated_answer}
                            >
                              B Gen: {evB.generated_answer}
                            </div>
                          )}
                        </td>
                        <td className="px-1 py-1.5 text-center">{evA.bleu !== null && evA.bleu !== undefined ? Number(evA.bleu).toFixed(2) : '-'}</td>
                        <td className="px-1 py-1.5 text-center">{(evA.rouge_l ?? evA.rouge) !== null && (evA.rouge_l ?? evA.rouge) !== undefined ? Number(evA.rouge_l ?? evA.rouge).toFixed(2) : '-'}</td>
                        <td className="px-1 py-1.5 text-center">{evA.answer_relevance ?? '-'}</td>
                        <td className="px-1 py-1.5 text-center">{evA.context_relevance ?? '-'}</td>
                        <td className="px-1 py-1.5 text-center">{evA.groundedness ?? '-'}</td>
                        {runB && (
                          <>
                            <td className="px-1 py-1.5 text-center">{evB.bleu !== null && evB.bleu !== undefined ? Number(evB.bleu).toFixed(2) : '-'}</td>
                            <td className="px-1 py-1.5 text-center">{(evB.rouge_l ?? evB.rouge) !== null && (evB.rouge_l ?? evB.rouge) !== undefined ? Number(evB.rouge_l ?? evB.rouge).toFixed(2) : '-'}</td>
                            <td className="px-1 py-1.5 text-center">{evB.answer_relevance ?? '-'}</td>
                            <td className="px-1 py-1.5 text-center">{evB.context_relevance ?? '-'}</td>
                            <td className="px-1 py-1.5 text-center">{evB.groundedness ?? '-'}</td>
                          </>
                        )}
                        <td className="px-2 py-1.5 text-right">
                          <div className="flex flex-col items-end gap-0.5">
                            <div className="flex gap-1">
                              {runA && (
                                <button
                                  onClick={() => handleRunQa(runA, qa.id)}
                                  disabled={progressA ? ['running', 'queued'].includes(progressA.status) : false}
                                  className={`px-2 py-0.5 text-xs border rounded-md font-body transition-colors ${
                                    progressA?.status === 'failed'
                                      ? 'border-danger-contrast text-danger-accent hover:bg-danger-muted'
                                      : 'border-primary text-primary hover:bg-primary/10'
                                  } ${progressA && ['running', 'queued'].includes(progressA.status) ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
                                >
                                  {runButtonLabel('A', progressA)}
                                </button>
                              )}
                              {runB && (
                                <button
                                  onClick={() => handleRunQa(runB, qa.id)}
                                  disabled={progressB ? ['running', 'queued'].includes(progressB.status) : false}
                                  className={`px-2 py-0.5 text-xs border rounded-md font-body transition-colors ${
                                    progressB?.status === 'failed'
                                      ? 'border-danger-contrast text-danger-accent hover:bg-danger-muted'
                                      : 'border-primary text-primary hover:bg-primary/10'
                                  } ${progressB && ['running', 'queued'].includes(progressB.status) ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
                                >
                                  {runButtonLabel('B', progressB)}
                                </button>
                              )}
                            </div>
                            <div className="flex gap-1">
                              {runA && (
                                <button
                                  onClick={() => openEvalDetails(runA, qa.id)}
                                  className="px-2 py-0.5 text-[10px] border border-secondary rounded-md font-body text-text/70 hover:text-text hover:bg-secondary/10 cursor-pointer"
                                >
                                  Details A
                                </button>
                              )}
                              {runB && (
                                <button
                                  onClick={() => openEvalDetails(runB, qa.id)}
                                  className="px-2 py-0.5 text-[10px] border border-secondary rounded-md font-body text-text/70 hover:text-text hover:bg-secondary/10 cursor-pointer"
                                >
                                  Details B
                                </button>
                              )}
                            </div>
                            {runA && progressA?.status && progressA.status !== 'completed' && (
                              <div className={`text-[10px] ${progressA.status === 'failed' ? 'text-danger-accent' : 'text-text/60'}`}>
                                A · {progressA.status === 'failed'
                                  ? (progressA.error || 'Failed')
                                  : (describeStage(progressA.stage) || progressA.status)}
                              </div>
                            )}
                            {runB && progressB?.status && progressB.status !== 'completed' && (
                              <div className={`text-[10px] ${progressB.status === 'failed' ? 'text-danger-accent' : 'text-text/60'}`}>
                                B · {progressB.status === 'failed'
                                  ? (progressB.error || 'Failed')
                                  : (describeStage(progressB.stage) || progressB.status)}
                              </div>
                            )}
                          </div>
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
              <div className="font-heading font-semibold text-sm text-text mb-3">Recent Runs ({runs.length})</div>
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
                            <pre className="mt-2 whitespace-pre-wrap border border-secondary rounded-md p-2 bg-background text-text/90 text-xs">{p.prompt}</pre>
                          </div>
                        )}
                        <div className="px-3 py-2 border-t border-secondary">
                          <div className="flex items-center justify-between mb-2">
                            <div className="font-heading font-semibold text-xs text-text">QA Metrics</div>
                            {qaSet.length > qaMetricsPerPage && (
                              <div className="flex items-center gap-2">
                                <button
                                  onClick={() => setQaPage(r.id, Math.max(1, getQaPage(r.id) - 1))}
                                  disabled={getQaPage(r.id) === 1}
                                  className="px-2 py-0.5 text-xs border border-secondary rounded-md hover:bg-secondary/10 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer font-body"
                                >
                                  ← Prev
                                </button>
                                <span className="font-body text-xs text-text/70">
                                  Page {getQaPage(r.id)} of {Math.ceil(qaSet.length / qaMetricsPerPage)}
                                </span>
                                <button
                                  onClick={() => setQaPage(r.id, Math.min(Math.ceil(qaSet.length / qaMetricsPerPage), getQaPage(r.id) + 1))}
                                  disabled={getQaPage(r.id) === Math.ceil(qaSet.length / qaMetricsPerPage)}
                                  className="px-2 py-0.5 text-xs border border-secondary rounded-md hover:bg-secondary/10 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer font-body"
                                >
                                  Next →
                                </button>
                              </div>
                            )}
                          </div>
                          {loading ? (
                            <div className="font-body text-xs text-text/60">Loading metrics…</div>
                          ) : (
                            <div className="overflow-x-auto max-h-[900px] overflow-y-auto">
                              <table className="min-w-full text-xs font-body">
                                <thead className="bg-secondary/10 sticky top-0">
                                  <tr>
                                    <th className="text-left px-2 py-1.5 text-text/70 font-medium text-xs">Question</th>
                                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">BLEU</th>
                                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">ROUGE-L</th>
                                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">AnsRel</th>
                                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">CtxRel</th>
                                    <th className="px-1 py-1.5 text-text/70 font-medium text-xs">Ground</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-secondary/30">
                                  {getPaginatedQaSet(r.id).map((qa) => {
                                    const ev = evMap[qa.id] || {};
                                    return (
                                      <tr key={qa.id} className="bg-background/60">
                                        <td
                                          className="px-2 py-1.5 align-top max-w-[320px] cursor-pointer hover:bg-secondary/10 rounded-sm"
                                          onClick={() => openEvalDetails(r.id, qa.id)}
                                          title="View full evaluation"
                                        >
                                          <div className="text-text font-medium truncate text-xs" title={qa.question}>Q: {qa.question}</div>
                                          <div className="text-text/70 text-xs line-clamp-1">A: {qa.answer}</div>
                                          {ev.generated_answer && (
                                            <div
                                              className="text-primary/70 text-[11px] mt-0.5 line-clamp-2"
                                              title={ev.generated_answer}
                                            >
                                              Gen: {ev.generated_answer}
                                            </div>
                                          )}
                                        </td>
                                        <td className="px-1 py-1.5 text-center">{ev.bleu !== null && ev.bleu !== undefined ? Number(ev.bleu).toFixed(2) : '-'}</td>
                                        <td className="px-1 py-1.5 text-center">{(ev.rouge_l ?? ev.rouge) !== null && (ev.rouge_l ?? ev.rouge) !== undefined ? Number(ev.rouge_l ?? ev.rouge).toFixed(2) : '-'}</td>
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
                            <button onClick={() => handleDeletePrompt(p.id)} className="text-xs text-danger hover:text-danger-strong cursor-pointer font-body">Delete</button>
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
                        Your prompt must include <code className="bg-primary/20 text-primary px-1.5 py-0.5 rounded font-mono text-xs">{'{' + '{query}' + '}'}</code> and <code className="bg-accent/20 text-accent px-1.5 py-0.5 rounded font-mono text-xs">{'{' + '{chunks}' + '}'}</code> variables
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
                              <code className="font-mono font-bold text-primary text-xs">{'{' + '{query}' + '}'}</code>
                              <p className="font-body text-xs text-text/70 mt-1">
                                This will be replaced with the actual question from your QA pairs.
                              </p>
                            </div>

                            <div className="bg-accent/5 rounded-md p-2 border border-accent/20">
                              <code className="font-mono font-bold text-accent text-xs">{'{' + '{chunks}' + '}'}</code>
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
                      <div className="bg-danger-muted border-2 border-danger-contrast rounded-lg p-3 flex items-start gap-2">
                        <svg className="w-5 h-5 text-danger flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <div className="flex-1">
                          <div className="font-body font-bold text-danger-stronger text-sm">{validationError}</div>
                          <div className="font-body text-xs text-danger-strong mt-0.5">
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
                          onClick={() => insertVariable('{{query}}')}
                          className="px-3 py-1.5 bg-primary/10 hover:bg-primary/20 border-2 border-primary/30 text-primary rounded-md font-mono text-xs font-bold transition-all hover:scale-105 flex items-center gap-1.5"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                          </svg>
                          {'{' + '{query}' + '}'}
                        </button>
                        <button
                          type="button"
                          onClick={() => insertVariable('{{chunks}}')}
                          className="px-3 py-1.5 bg-accent/10 hover:bg-accent/20 border-2 border-accent/30 text-accent rounded-md font-mono text-xs font-bold transition-all hover:scale-105 flex items-center gap-1.5"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                          </svg>
                          {'{' + '{chunks}' + '}'}
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
                              validationError ? 'border-danger-contrast' : 'border-secondary'
                            }`}
                            placeholder="Write your prompt here...

**Example:**
You are a helpful AI assistant. Use the following context to answer the question.

**Chunks:** {{chunks}}

**Query:** {{query}}

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
                            <div className={`flex items-center gap-1.5 ${newPromptText.includes('{{query}}') ? 'text-success' : 'text-text/40'}`}>
                              {newPromptText.includes('{{query}}') ? (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              ) : (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              )}
                              <code className="font-mono font-bold">{'{' + '{query}' + '}'}</code>
                            </div>
                            <div className={`flex items-center gap-1.5 ${newPromptText.includes('{{chunks}}') ? 'text-success' : 'text-text/40'}`}>
                              {newPromptText.includes('{{chunks}}') ? (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              ) : (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              )}
                              <code className="font-mono font-bold">{'{' + '{chunks}' + '}'}</code>
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
        <div className="fixed inset-0 bg-overlay flex items-center justify-center p-4 z-40">
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
                <button onClick={() => setRunModal(null)} className="px-3 py-1.5 text-xs border border-secondary text-text rounded-md hover:bg-secondary/20 cursor-pointer font-body">Cancel</button>
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
