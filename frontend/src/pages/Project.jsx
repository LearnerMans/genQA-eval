import { useEffect, useMemo, useState } from 'react';
import { projectsAPI, testsAPI, corpusAPI, qaAPI, configAPI, promptsAPI } from '../services/api';
import { useToast } from '../components/Toaster.jsx';
import DeleteConfirmationModal from '../components/DeleteConfirmationModal.jsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// POSSIBLE VALUES FOR CONFIG FIELDS
// type: "semantic" | "recursive"
// generative_model: "openai_4o" | "openai_4o_mini" | "claude_sonnet_3_5" | "claude_opus_3" | "gemini_pro"
// embedding_model: "openai_text_embedding_large_3" | "openai_text_embedding_small_3" | "cohere_embed_v3" | "voyage_ai_2"
// chunk_size: 100-5000 (recommended: 500-1500)
// overlap: 0-500 (recommended: 50-200)
// top_k: 1-50 (recommended: 5-15)

const CONFIG_OPTIONS = {
  types: ['semantic', 'recursive'],
  generativeModels: ['openai_4o', 'openai_4o_mini', 'claude_sonnet_3_5', 'claude_opus_3', 'gemini_pro'],
  embeddingModels: ['openai_text_embedding_large_3', 'openai_text_embedding_small_3', 'cohere_embed_v3', 'voyage_ai_2'],
};

export default function Project({ projectId: propProjectId }) {
  const toast = useToast();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Tab state
  const [activeTab, setActiveTab] = useState('tests'); // 'tests' | 'corpus' | 'qaset'

  const [tests, setTests] = useState([]);
  const [newTestName, setNewTestName] = useState('');
  const [creatingTest, setCreatingTest] = useState(false);
  const [showTestForm, setShowTestForm] = useState(false);


  // Config modal state
  const [configModal, setConfigModal] = useState(null); // {testId, testName, config}
  const [configForm, setConfigForm] = useState({
    type: 'semantic',
    chunk_size: 1000,
    overlap: 100,
    generative_model: 'openai_4o',
    embedding_model: 'openai_text_embedding_large_3',
    top_k: 10
  });
  const [savingConfig, setSavingConfig] = useState(false);

  // Prompts modal state
  const [promptsModal, setPromptsModal] = useState(null); // {testId, testName}
  const [prompts, setPrompts] = useState([]);
  const [newPromptName, setNewPromptName] = useState('');
  const [newPromptText, setNewPromptText] = useState('');
  const [creatingPrompt, setCreatingPrompt] = useState(false);
  const [promptsLoading, setPromptsLoading] = useState(false);
  const [previewMode, setPreviewMode] = useState(false); // toggle between write and preview
  const [promptsTab, setPromptsTab] = useState('view'); // 'view' | 'create'
  const [expandedPrompts, setExpandedPrompts] = useState(new Set()); // Set of expanded prompt IDs
  const [validationError, setValidationError] = useState(''); // validation message for required variables
  const [textareaRef, setTextareaRef] = useState(null); // ref to textarea for inserting variables
  const [showInfoTooltip, setShowInfoTooltip] = useState(false); // show/hide info tooltip

  const [corpus, setCorpus] = useState(null);
  const [corpusLoading, setCorpusLoading] = useState(true);
  const [newCorpusName, setNewCorpusName] = useState('Default Corpus');
  const [items, setItems] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [addingUrl, setAddingUrl] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [preview, setPreview] = useState(null); // {type: 'file'|'url', data}

  // Delete confirmation modal state
  const [deleteModal, setDeleteModal] = useState(null); // {type: 'test'|'prompt'|'qa'|'item', id, name}

  // QA Set state
  const [qaSet, setQaSet] = useState([]);
  const [qaLoading, setQaLoading] = useState(true);
  const [newQuestion, setNewQuestion] = useState('');
  const [newAnswer, setNewAnswer] = useState('');
  const [creatingQA, setCreatingQA] = useState(false);
  const [uploadingCSV, setUploadingCSV] = useState(false);
  const [showQAForms, setShowQAForms] = useState(false);

  const projectId = propProjectId || useMemo(() => {
    const hash = window.location.hash || '';
    const match = hash.match(/#project\/(.+)$/);
    return match ? match[1] : null;
  }, [propProjectId]);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError(null);
        let proj = null;
        // In absence of a GET /projects/:id, fetch all and find
        const all = await projectsAPI.getAllProjects();
        proj = all.find((p) => p.id === projectId) || null;
        if (!proj) throw new Error('Project not found');
        setProject(proj);
      } catch (e) {
        setError(e.message || 'Failed to load project');
      } finally {
        setLoading(false);
      }
    })();
  }, [projectId]);

  useEffect(() => {
    if (!projectId) return;
    (async () => {
      try {
        const t = await testsAPI.getByProject(projectId);
        setTests(t);
      } catch (e) {
        toast.error(e.message || 'Failed to fetch tests');
      }
    })();
  }, [projectId, toast]);

  useEffect(() => {
    if (!projectId) return;
    (async () => {
      setCorpusLoading(true);
      try {
        const c = await corpusAPI.getCorpusByProject(projectId);
        setCorpus(c);
        if (c) {
          const it = await corpusAPI.getItemsByProject(projectId);
          setItems(it);
        } else {
          setItems([]);
        }
      } catch (e) {
        toast.error(e.message || 'Failed to fetch corpus');
      } finally {
        setCorpusLoading(false);
      }
    })();
  }, [projectId, toast]);

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

  const goBack = () => {
    window.location.hash = '';
  };

  const handleCreateTest = async (e) => {
    e.preventDefault();
    if (!newTestName.trim()) return;
    try {
      setCreatingTest(true);
      await testsAPI.createTest({ name: newTestName.trim(), project_id: projectId });
      setNewTestName('');
      setShowTestForm(false);
      const t = await testsAPI.getByProject(projectId);
      setTests(t);
    } catch (e) {
      toast.error(e.message || 'Failed to create test');
    } finally {
      setCreatingTest(false);
    }
  };

  const handleDeleteTest = async (testId) => {
    try {
      await testsAPI.deleteTest(testId);
      setTests((prev) => prev.filter((t) => t.id !== testId));
      setDeleteModal(null);
      toast.success('Test deleted successfully');
    } catch (e) {
      toast.error(e.message || 'Failed to delete test');
    }
  };

  const handleOpenConfigModal = async (test) => {
    try {
      const existingConfig = await configAPI.getByTestId(test.id);
      if (existingConfig) {
        setConfigForm({
          type: existingConfig.type,
          chunk_size: existingConfig.chunk_size,
          overlap: existingConfig.overlap,
          generative_model: existingConfig.generative_model,
          embedding_model: existingConfig.embedding_model,
          top_k: existingConfig.top_k
        });
      } else {
        // Reset to defaults
        setConfigForm({
          type: 'semantic',
          chunk_size: 1000,
          overlap: 100,
          generative_model: 'openai_4o',
          embedding_model: 'openai_text_embedding_large_3',
          top_k: 10
        });
      }
      setConfigModal({ testId: test.id, testName: test.name, config: existingConfig });
    } catch (e) {
      toast.error(e.message || 'Failed to load config');
    }
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    if (!configModal) return;
    try {
      setSavingConfig(true);
      await configAPI.createConfig({
        test_id: configModal.testId,
        ...configForm
      });
      toast.success('Config saved');
      setConfigModal(null);
    } catch (e) {
      toast.error(e.message || 'Failed to save config');
    } finally {
      setSavingConfig(false);
    }
  };

  const handleOpenPromptsModal = async (test) => {
    try {
      setPromptsModal({ testId: test.id, testName: test.name });
      setPromptsLoading(true);
      const fetchedPrompts = await promptsAPI.getByTest(test.id);
      setPrompts(fetchedPrompts);
    } catch (e) {
      toast.error(e.message || 'Failed to load prompts');
    } finally {
      setPromptsLoading(false);
    }
  };


  const validatePrompt = (text) => {
    const hasChunks = text.includes('{chunks}');
    const hasQuery = text.includes('{query}');

    if (!hasChunks && !hasQuery) {
      return 'Prompt must contain both {chunks} and {query} variables';
    }
    if (!hasChunks) {
      return 'Prompt must contain the {chunks} variable';
    }
    if (!hasQuery) {
      return 'Prompt must contain the {query} variable';
    }
    return '';
  };

  const handleCreatePrompt = async (e) => {
    e.preventDefault();
    if (!newPromptName.trim() || !newPromptText.trim() || !promptsModal) return;

    // Validate required variables
    const error = validatePrompt(newPromptText.trim());
    if (error) {
      setValidationError(error);
      toast.error(error);
      return;
    }

    try {
      setCreatingPrompt(true);
      setValidationError('');
      await promptsAPI.createPrompt({ test_id: promptsModal.testId, name: newPromptName.trim(), prompt: newPromptText.trim() });
      setNewPromptName('');
      setNewPromptText('');
      const fetchedPrompts = await promptsAPI.getByTest(promptsModal.testId);
      setPrompts(fetchedPrompts);
      toast.success('Prompt created');
      setPromptsTab('view'); // Switch to view tab after creation
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
      setDeleteModal(null);
      toast.success('Prompt deleted');
    } catch (e) {
      toast.error(e.message || 'Failed to delete prompt');
    }
  };

  const handleClosePromptsModal = () => {
    setPromptsModal(null);
    setPrompts([]);
    setNewPromptName('');
    setNewPromptText('');
    setPreviewMode(false);
    setPromptsTab('view');
    setExpandedPrompts(new Set());
    setValidationError('');
    setTextareaRef(null);
    setShowInfoTooltip(false);
  };

  const togglePromptExpanded = (promptId) => {
    setExpandedPrompts((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(promptId)) {
        newSet.delete(promptId);
      } else {
        newSet.add(promptId);
      }
      return newSet;
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

    // Set cursor position after inserted variable
    setTimeout(() => {
      textareaRef.selectionStart = textareaRef.selectionEnd = start + variable.length;
      textareaRef.focus();
    }, 0);
  };

  const handleCreateCorpus = async (e) => {
    e.preventDefault();
    try {
      const c = await corpusAPI.createCorpus({ project_id: projectId, name: newCorpusName.trim() || 'Default Corpus' });
      setCorpus(c);
      const it = await corpusAPI.getItemsByProject(projectId);
      setItems(it);
      toast.success('Corpus created', c.name);
    } catch (e) {
      toast.error(e.message || 'Failed to create corpus');
    }
  };

  const handleUploadFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !corpus) return;
    try {
      setUploading(true);
      await corpusAPI.uploadFile({ project_id: projectId, corpus_id: corpus.id, file });
      const it = await corpusAPI.getItemsByProject(projectId);
      setItems(it);
      toast.success('File uploaded');
      e.target.value = '';
    } catch (er) {
      toast.error(er.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleAddUrl = async (e) => {
    e.preventDefault();
    if (!newUrl.trim() || !corpus) return;
    try {
      setAddingUrl(true);
      await corpusAPI.addUrl({ project_id: projectId, corpus_id: corpus.id, url: newUrl.trim() });
      const it = await corpusAPI.getItemsByProject(projectId);
      setItems(it);
      setNewUrl('');
      toast.success('URL added');
    } catch (er) {
      toast.error(er.message || 'Failed to add URL');
    } finally {
      setAddingUrl(false);
    }
  };

  const handlePreview = async (item) => {
    try {
      if (item.type === 'file') {
        const full = await corpusAPI.getFileById(item.id);
        setPreview({ type: 'file', data: full });
      } else {
        const full = await corpusAPI.getUrlById(item.id);
        setPreview({ type: 'url', data: full });
      }
    } catch (e) {
      toast.error(e.message || 'Failed to load item');
    }
  };

  const handleDeleteItem = async (item) => {
    try {
      if (item.type === 'file') {
        await corpusAPI.deleteFile(item.id);
      } else {
        await corpusAPI.deleteUrl(item.id);
      }
      setItems((prev) => prev.filter((i) => i.id !== item.id));
      if (preview?.data?.id === item.id) setPreview(null);
      setDeleteModal(null);
      toast.success('Item deleted successfully');
    } catch (e) {
      toast.error(e.message || 'Failed to delete item');
    }
  };

  const handleCreateQA = async (e) => {
    e.preventDefault();
    if (!newQuestion.trim() || !newAnswer.trim()) return;
    try {
      setCreatingQA(true);
      await qaAPI.createQA({
        project_id: projectId,
        question: newQuestion.trim(),
        answer: newAnswer.trim()
      });
      setNewQuestion('');
      setNewAnswer('');
      const qa = await qaAPI.getByProject(projectId);
      setQaSet(qa);
      toast.success('QA pair created');
    } catch (e) {
      toast.error(e.message || 'Failed to create QA pair');
    } finally {
      setCreatingQA(false);
    }
  };

  const handleUploadCSV = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setUploadingCSV(true);
      const result = await qaAPI.uploadCSV({ project_id: projectId, file });
      const qa = await qaAPI.getByProject(projectId);
      setQaSet(qa);
      e.target.value = '';

      // Show detailed results
      toast.success(`CSV uploaded: ${result.created_count} created, ${result.skipped_count} skipped, ${result.failed_count} failed`);
    } catch (e) {
      toast.error(e.message || 'CSV upload failed');
    } finally {
      setUploadingCSV(false);
    }
  };

  const handleDeleteQA = async (qaId) => {
    try {
      await qaAPI.deleteQA(qaId);
      setQaSet((prev) => prev.filter((qa) => qa.id !== qaId));
      setDeleteModal(null);
      toast.success('QA pair deleted');
    } catch (e) {
      toast.error(e.message || 'Failed to delete QA pair');
    }
  };

  const handleDownloadTemplate = () => {
    qaAPI.downloadTemplate();
    toast.success('Template downloaded');
  };

  const formatDate = (d) => (d ? new Date(d).toLocaleString() : 'N/A');

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 font-body text-text/70">Loading project…</p>
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="font-body text-red-600">{error || 'Project not found'}</p>
          <button onClick={goBack} className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 cursor-pointer">Back</button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'tests', label: 'Tests' },
    { id: 'corpus', label: 'Corpus' },
    { id: 'qaset', label: 'QA Set' }
  ];

  return (
    <div className="min-h-screen bg-background">
      <header className="w-full max-w-6xl mx-auto px-3 py-4">
        <div>
          <button onClick={goBack} className="font-body text-xs text-text/70 hover:text-text cursor-pointer">← Back to Projects</button>
          <h1 className="font-heading font-bold text-xl text-text mt-1">{project.name}</h1>
        </div>

        {/* Tabs */}
        <div className="mt-4 flex gap-2 border-b border-secondary/40">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 text-sm font-body font-medium transition-colors cursor-pointer ${
                activeTab === tab.id
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-text/60 hover:text-text'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      <main className="w-full max-w-6xl mx-auto px-3 pb-8">
        {/* Tests Tab */}
        {activeTab === 'tests' && (
          <section className="space-y-3">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-heading font-bold text-base text-text">Tests</h2>
              {!showTestForm && (
                <button
                  onClick={() => setShowTestForm(true)}
                  className="px-3 py-1.5 bg-primary text-white rounded-lg hover:bg-primary/90 cursor-pointer transition-all flex items-center gap-1.5 text-xs font-body font-medium"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  New Test
                </button>
              )}
            </div>

            {showTestForm && (
              <div className="bg-background border border-secondary rounded-lg p-3">
                <form onSubmit={handleCreateTest} className="flex gap-2 items-center">
                  <input
                    type="text"
                    className="flex-1 border border-secondary rounded-lg px-2 py-1 text-xs font-body"
                    placeholder="Enter test name…"
                    value={newTestName}
                    onChange={(e) => setNewTestName(e.target.value)}
                    autoFocus
                  />
                  <button
                    type="submit"
                    disabled={creatingTest || !newTestName.trim()}
                    className="px-3 py-1 text-xs bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 cursor-pointer font-body font-medium whitespace-nowrap"
                  >
                    {creatingTest ? 'Creating…' : 'Create'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowTestForm(false);
                      setNewTestName('');
                    }}
                    className="px-3 py-1 text-xs border border-secondary text-text/70 rounded-lg hover:bg-secondary/20 cursor-pointer font-body font-medium"
                  >
                    Cancel
                  </button>
                </form>
              </div>
            )}

            {/* Fancy Test Cards */}
            {tests.length === 0 && !showTestForm ? (
              <div className="bg-background border border-secondary rounded-lg p-8 text-center">
                <div className="font-body text-text/60 text-base">No tests yet</div>
                <p className="font-body text-text/40 text-xs mt-1">Create your first test to get started</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-3">
                {tests.map((t) => (
                  <div
                    key={t.id}
                    onClick={() => { window.location.hash = `#project/${projectId}/test/${t.id}`; }}
                    className="bg-gradient-to-br from-background to-secondary/5 border border-secondary rounded-lg p-3 hover:shadow-lg transition-all duration-200 hover:border-primary/30 cursor-pointer"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-heading font-bold text-sm text-text truncate">{t.name}</h3>
                        <p className="font-body text-xs text-text/50">ID: {t.id.slice(0, 8)}...</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 text-xs text-text/60 font-body mb-3">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {formatDate(t.created_at)}
                    </div>

                    <div className="flex gap-1.5" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => handleOpenPromptsModal(t)}
                        className="flex-1 px-2 py-1.5 bg-accent text-white rounded-lg hover:bg-accent/90 font-body text-xs font-medium cursor-pointer transition-colors flex items-center justify-center gap-1"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                        Prompts
                      </button>
                      <button
                        onClick={() => handleOpenConfigModal(t)}
                        className="flex-1 px-2 py-1.5 bg-primary text-white rounded-lg hover:bg-primary/90 font-body text-xs font-medium cursor-pointer transition-colors flex items-center justify-center gap-1"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        Config
                      </button>
                      <button
                        onClick={() => setDeleteModal({ type: 'test', id: t.id, name: t.name })}
                        className="px-2 py-1.5 border border-red-600 text-red-600 rounded-lg hover:bg-red-50 font-body text-xs cursor-pointer transition-colors"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* Corpus Tab */}
        {activeTab === 'corpus' && (
          <section className="bg-background border border-secondary rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-heading font-bold text-base text-text">Corpus</h2>
            </div>

            {corpusLoading ? (
              <div className="font-body text-text/60 text-sm">Loading corpus…</div>
            ) : !corpus ? (
              <form onSubmit={handleCreateCorpus} className="flex gap-2">
                <input
                  type="text"
                  className="flex-1 border border-secondary rounded-lg px-3 py-1.5 text-sm font-body"
                  placeholder="Corpus name"
                  value={newCorpusName}
                  onChange={(e) => setNewCorpusName(e.target.value)}
                />
                <button className="px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 cursor-pointer">Create Corpus</button>
              </form>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-body text-sm text-text font-medium">{corpus.name}</div>
                    <div className="font-body text-xs text-text/60">ID: {corpus.id}</div>
                  </div>
                </div>

                {/* Styled Upload Section */}
                <div className="bg-secondary/10 border-2 border-dashed border-secondary rounded-lg p-4">
                  <h3 className="font-heading font-bold text-sm text-text mb-3">Add Content to Corpus</h3>

                  <div className="space-y-3">
                    {/* File Upload */}
                    <div className="bg-background rounded-lg p-3 border border-secondary">
                      <label className="font-body text-xs font-medium text-text mb-2 block">Upload File</label>
                      <div className="flex items-center gap-3">
                        <label className="flex-1 cursor-pointer">
                          <div className="border border-secondary rounded-lg px-3 py-1.5 hover:bg-secondary/20 transition-colors text-center">
                            <span className="font-body text-xs text-text/70">
                              {uploading ? 'Uploading…' : 'Choose file'}
                            </span>
                          </div>
                          <input
                            type="file"
                            onChange={handleUploadFile}
                            disabled={uploading}
                            className="hidden"
                          />
                        </label>
                        {uploading && (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                        )}
                      </div>
                    </div>

                    {/* URL Input */}
                    <div className="bg-background rounded-lg p-3 border border-secondary">
                      <label className="font-body text-xs font-medium text-text mb-2 block">Add URL</label>
                      <form onSubmit={handleAddUrl} className="flex gap-2">
                        <input
                          type="url"
                          className="flex-1 border border-secondary rounded-lg px-3 py-1.5 font-body text-xs"
                          placeholder="https://example.com/document"
                          value={newUrl}
                          onChange={(e) => setNewUrl(e.target.value)}
                        />
                        <button
                          disabled={addingUrl || !newUrl.trim()}
                          className="px-3 py-1.5 text-xs bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 cursor-pointer font-body font-medium"
                        >
                          {addingUrl ? 'Adding…' : 'Add'}
                        </button>
                      </form>
                    </div>
                  </div>
                </div>

                {/* Items List */}
                <div>
                  <h3 className="font-heading font-bold text-sm text-text mb-2">Items ({items.length})</h3>
                  {items.length === 0 ? (
                    <div className="font-body text-text/60 text-center py-6 text-xs bg-secondary/5 rounded-lg">
                      No items in corpus yet. Upload a file or add a URL to get started.
                    </div>
                  ) : (
                    <div className="divide-y divide-secondary/40">
                      {items.map((it) => (
                        <div key={it.id} className="py-2 flex items-center justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <div className="font-body text-sm text-text">
                              {it.type === 'file' ? `${it.metadata?.name || it.id}${it.metadata?.ext || ''}` : it.metadata?.url}
                            </div>
                            <div className="font-body text-xs text-text/60">{it.type.toUpperCase()} · Created {formatDate(it.metadata?.created_at)}</div>
                          </div>
                          <div className="flex items-center gap-2">
                            <button onClick={() => handlePreview(it)} className="px-2 py-1 text-xs border border-secondary rounded-md hover:bg-secondary/30 cursor-pointer font-body">Preview</button>
                            <button onClick={() => setDeleteModal({ type: 'item', id: it.id, name: it.type === 'file' ? `${it.metadata?.name || it.id}${it.metadata?.ext || ''}` : it.metadata?.url, data: it })} className="px-2 py-1 text-xs text-red-600 hover:text-red-700 cursor-pointer font-body">Delete</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Preview Modal */}
                {preview && (
                  <div className="mt-4 border border-secondary rounded-lg p-4 bg-secondary/5">
                    <div className="flex items-center justify-between mb-3">
                      <div className="font-heading font-bold text-text">Preview</div>
                      <button onClick={() => setPreview(null)} className="text-text/60 hover:text-text cursor-pointer font-body text-sm">✕ Close</button>
                    </div>
                    {preview.type === 'file' ? (
                      <div>
                        <div className="font-body text-sm text-text/70 mb-2 font-medium">{preview.data.name}{preview.data.ext}</div>
                        <pre className="whitespace-pre-wrap font-body text-sm text-text bg-background rounded-md p-4 max-h-96 overflow-auto border border-secondary">{preview.data.content || '(empty file)'}</pre>
                      </div>
                    ) : (
                      <div>
                        <div className="font-body text-sm text-text/70 mb-2 font-medium break-all">{preview.data.url}</div>
                        <pre className="whitespace-pre-wrap font-body text-sm text-text bg-background rounded-md p-4 max-h-96 overflow-auto border border-secondary">{preview.data.content || '(no content)'}</pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {/* QA Set Tab */}
        {activeTab === 'qaset' && (
          <section className="bg-background border border-secondary rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-heading font-bold text-base text-text">QA Set</h2>
              <div className="flex items-center gap-2">
                {qaSet.length > 0 && (
                  <button
                    onClick={() => setShowQAForms(!showQAForms)}
                    className="px-2 py-1 text-xs border border-secondary text-text rounded-lg hover:bg-secondary/20 cursor-pointer font-body font-medium"
                  >
                    {showQAForms ? '✕ Hide' : '+ Add'}
                  </button>
                )}
                <button
                  onClick={handleDownloadTemplate}
                  className="px-2 py-1 text-xs border border-primary text-primary rounded-lg hover:bg-primary/10 cursor-pointer font-body font-medium"
                >
                  📥 Template
                </button>
              </div>
            </div>

            {qaLoading ? (
              <div className="font-body text-text/60 text-sm">Loading QA pairs…</div>
            ) : (
              <div className="space-y-4">
                {/* Show forms when: no QA pairs OR showQAForms is true */}
                {(qaSet.length === 0 || showQAForms) && (
                  <>
                    {/* Manual Entry Form */}
                    <div className="bg-secondary/10 border-2 border-dashed border-secondary rounded-lg p-4">
                      <h3 className="font-heading font-bold text-sm text-text mb-3">Add QA Pair Manually</h3>
                      <form onSubmit={handleCreateQA} className="space-y-3">
                        <div>
                          <label className="font-body text-xs font-medium text-text mb-1 block">Question</label>
                          <input
                            type="text"
                            className="w-full border border-secondary rounded-lg px-3 py-1.5 text-sm font-body"
                            placeholder="What is RAG?"
                            value={newQuestion}
                            onChange={(e) => setNewQuestion(e.target.value)}
                            required
                          />
                        </div>
                        <div>
                          <label className="font-body text-xs font-medium text-text mb-1 block">Answer</label>
                          <textarea
                            className="w-full border border-secondary rounded-lg px-3 py-1.5 text-sm font-body min-h-[80px]"
                            placeholder="RAG stands for Retrieval-Augmented Generation..."
                            value={newAnswer}
                            onChange={(e) => setNewAnswer(e.target.value)}
                            required
                          />
                        </div>
                        <button
                          disabled={creatingQA || !newQuestion.trim() || !newAnswer.trim()}
                          className="px-3 py-1.5 text-xs bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 cursor-pointer font-body font-medium"
                        >
                          {creatingQA ? 'Creating…' : 'Add QA Pair'}
                        </button>
                      </form>
                    </div>

                    {/* CSV Upload Section */}
                    <div className="bg-secondary/10 border-2 border-dashed border-secondary rounded-lg p-4">
                      <h3 className="font-heading font-bold text-sm text-text mb-3">Upload CSV File</h3>
                      <div className="space-y-2">
                        <p className="font-body text-xs text-text/70">
                          Upload a CSV file with <code className="bg-secondary/30 px-1 rounded text-xs">question</code> and <code className="bg-secondary/30 px-1 rounded text-xs">answer</code> columns.
                        </p>
                        <div className="flex items-center gap-3">
                          <label className="flex-1 cursor-pointer">
                            <div className="border border-secondary rounded-lg px-3 py-2 hover:bg-secondary/20 transition-colors text-center bg-background">
                              <span className="font-body text-xs text-text/70">
                                {uploadingCSV ? 'Uploading…' : 'Choose CSV file'}
                              </span>
                            </div>
                            <input
                              type="file"
                              accept=".csv"
                              onChange={handleUploadCSV}
                              disabled={uploadingCSV}
                              className="hidden"
                            />
                          </label>
                          {uploadingCSV && (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                          )}
                        </div>
                      </div>
                    </div>
                  </>
                )}

                {/* QA Pairs List */}
                <div>
                  <h3 className="font-heading font-bold text-sm text-text mb-2">QA Pairs ({qaSet.length})</h3>
                  {qaSet.length === 0 ? (
                    <div className="font-body text-text/60 text-center py-6 text-xs bg-secondary/5 rounded-lg">
                      No QA pairs yet. Add them manually or upload a CSV file.
                    </div>
                  ) : (
                    <div className="divide-y divide-secondary/40">
                      {qaSet.map((qa) => (
                        <div key={qa.id} className="py-3">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <div className="font-body text-sm text-text font-medium mb-1">Q: {qa.question}</div>
                              <div className="font-body text-text/80 text-xs">A: {qa.answer}</div>
                            </div>
                            <button
                              onClick={() => setDeleteModal({ type: 'qa', id: qa.id, name: qa.question })}
                              className="px-2 py-1 text-xs text-red-600 hover:text-red-700 cursor-pointer font-body flex-shrink-0"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </section>
        )}
      </main>

      {/* Prompts Modal */}
      {promptsModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-xl shadow-2xl w-full max-w-5xl h-[85vh] max-h-[700px] overflow-hidden border-2 border-primary/20">
            {/* Header */}
            <div className="sticky top-0 bg-gradient-to-r from-primary/10 via-accent/10 to-primary/10 border-b-2 border-primary/20 px-4 py-3">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-heading font-bold text-lg text-text flex items-center gap-2">
                    <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Prompts Manager
                  </h2>
                  <p className="font-body text-xs text-text/70 mt-0.5">{promptsModal.testName}</p>
                </div>
                <button onClick={handleClosePromptsModal} className="text-text/60 hover:text-text cursor-pointer transition-colors p-1 hover:bg-secondary/30 rounded-lg">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Main Tabs */}
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => setPromptsTab('view')}
                  className={`flex-1 px-4 py-2 rounded-lg font-body text-sm font-bold transition-all ${
                    promptsTab === 'view'
                      ? 'bg-gradient-to-r from-primary to-accent text-white shadow-lg'
                      : 'bg-secondary/20 text-text/70 hover:bg-secondary/30 hover:text-text'
                  }`}
                >
                  <div className="flex items-center justify-center gap-1.5">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    View Prompts
                    <span className={`ml-1 px-1.5 py-0.5 rounded-full text-xs font-bold ${
                      promptsTab === 'view' ? 'bg-white/20' : 'bg-primary/20 text-primary'
                    }`}>
                      {prompts.length}
                    </span>
                  </div>
                </button>
                <button
                  onClick={() => setPromptsTab('create')}
                  className={`flex-1 px-4 py-2 rounded-lg font-body text-sm font-bold transition-all ${
                    promptsTab === 'create'
                      ? 'bg-gradient-to-r from-primary to-accent text-white shadow-lg'
                      : 'bg-secondary/20 text-text/70 hover:bg-secondary/30 hover:text-text'
                  }`}
                >
                  <div className="flex items-center justify-center gap-1.5">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Create New
                  </div>
                </button>
              </div>
            </div>

            <div className="overflow-y-auto" style={{maxHeight: 'calc(85vh - 120px)'}}>
              {/* VIEW TAB */}
              {promptsTab === 'view' && (
                <div className="p-8">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="font-heading font-bold text-2xl text-text flex items-center gap-2">
                      <svg className="w-7 h-7 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                      </svg>
                      Saved Prompts
                    </h3>
                    {prompts.length > 0 && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => setExpandedPrompts(new Set(prompts.map(p => p.id)))}
                          className="px-3 py-2 text-sm border border-primary text-primary rounded-lg hover:bg-primary/10 cursor-pointer font-body font-medium transition-all"
                        >
                          Expand All
                        </button>
                        <button
                          onClick={() => setExpandedPrompts(new Set())}
                          className="px-3 py-2 text-sm border border-secondary text-text/70 rounded-lg hover:bg-secondary/20 cursor-pointer font-body font-medium transition-all"
                        >
                          Collapse All
                        </button>
                      </div>
                    )}
                  </div>

                  {promptsLoading ? (
                    <div className="text-center py-16">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                      <p className="mt-4 font-body text-text/70 text-lg">Loading prompts...</p>
                    </div>
                  ) : prompts.length === 0 ? (
                    <div className="text-center py-20 bg-gradient-to-br from-secondary/10 to-transparent rounded-2xl border-2 border-dashed border-secondary/40">
                      <svg className="w-20 h-20 text-text/30 mx-auto mb-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <h4 className="font-heading font-bold text-2xl text-text mb-3">No prompts yet</h4>
                      <p className="font-body text-text/60 text-lg mb-6">Create your first prompt to get started!</p>
                      <button
                        onClick={() => setPromptsTab('create')}
                        className="px-6 py-3 bg-gradient-to-r from-primary to-accent text-white rounded-xl hover:shadow-lg cursor-pointer font-body font-bold transition-all transform hover:scale-105"
                      >
                        Create Your First Prompt
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {prompts.map((prompt, idx) => {
                        const isExpanded = expandedPrompts.has(prompt.id);
                        return (
                          <div
                            key={prompt.id}
                            className="bg-gradient-to-br from-background to-secondary/5 border-2 border-secondary/40 rounded-xl overflow-hidden hover:border-primary/40 transition-all hover:shadow-lg"
                          >
                            {/* Collapsed Header */}
                            <div
                              onClick={() => togglePromptExpanded(prompt.id)}
                              className="flex items-center justify-between p-5 cursor-pointer hover:bg-secondary/5 transition-colors"
                            >
                              <div className="flex items-center gap-4 flex-1 min-w-0">
                                <div className="w-12 h-12 bg-gradient-to-br from-primary to-accent rounded-xl flex items-center justify-center text-white font-bold font-heading shadow-md flex-shrink-0">
                                  {idx + 1}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="font-heading text-lg text-text truncate">
                                    {prompt.name || 'Untitled Prompt'}
                                  </div>
                                  <div className="font-body text-sm text-text/50">Created {formatDate(prompt.created_at)}</div>
                                  <div className="font-body text-xs text-text/40 mt-1">ID: {prompt.id.slice(0, 8)}...</div>
                                </div>
                              </div>
                              <div className="flex items-center gap-3">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setDeleteModal({ type: 'prompt', id: prompt.id, name: prompt.name || 'Untitled Prompt' });
                                  }}
                                  className="px-3 py-2 text-sm text-red-600 hover:text-white hover:bg-red-600 border border-red-600 rounded-lg cursor-pointer font-body font-medium transition-all flex items-center gap-1.5"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                  </svg>
                                  Delete
                                </button>
                                <svg
                                  className={`w-6 h-6 text-text/60 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                                  fill="none"
                                  stroke="currentColor"
                                  viewBox="0 0 24 24"
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                              </div>
                            </div>

                            {/* Expanded Content */}
                            {isExpanded && (
                              <div className="border-t-2 border-secondary/30 bg-background/60 p-6 animate-fadeIn">
                                <div className="bg-gradient-to-br from-background to-secondary/5 rounded-xl p-6 border border-secondary/20">
                                  <h3 className="font-heading text-xl text-text mb-4">
                                    {prompt.name || 'Untitled Prompt'}
                                  </h3>
                                  <div className="prose prose-sm max-w-none font-body text-text">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{prompt.prompt}</ReactMarkdown>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* CREATE TAB */}
              {promptsTab === 'create' && (
                <div className="p-8 bg-gradient-to-br from-secondary/5 to-transparent">
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <h3 className="font-heading font-bold text-2xl text-text mb-2 flex items-center gap-2">
                        <span className="w-3 h-3 bg-primary rounded-full animate-pulse"></span>
                        Create New Prompt
                      </h3>
                      <p className="font-body text-text/60">
                        Your prompt must include <code className="bg-primary/20 text-primary px-2 py-0.5 rounded font-mono text-sm">{'{chunks}'}</code> and <code className="bg-accent/20 text-accent px-2 py-0.5 rounded font-mono text-sm">{'{query}'}</code> variables
                      </p>
                    </div>

                    {/* Info Tooltip */}
                    <div className="relative">
                      <button
                        type="button"
                        onMouseEnter={() => setShowInfoTooltip(true)}
                        onMouseLeave={() => setShowInfoTooltip(false)}
                        className="w-10 h-10 rounded-full bg-primary/10 hover:bg-primary/20 flex items-center justify-center text-primary transition-colors cursor-help"
                      >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </button>

                      {/* Tooltip */}
                      {showInfoTooltip && (
                        <div className="absolute right-0 top-12 w-80 bg-white rounded-xl shadow-2xl border-2 border-primary/20 p-5 z-10 animate-fadeIn">
                          <div className="flex items-start gap-3 mb-4">
                            <svg className="w-6 h-6 text-primary flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                            <div>
                              <h4 className="font-heading font-bold text-base text-text mb-1">How to use variables</h4>
                              <p className="font-body text-sm text-text/70">Add these placeholders to your prompt:</p>
                            </div>
                          </div>

                          <div className="space-y-3 mb-4">
                            <div className="bg-primary/5 rounded-lg p-3 border border-primary/20">
                              <code className="font-mono font-bold text-primary text-sm">{'{chunks}'}</code>
                              <p className="font-body text-xs text-text/70 mt-1.5">
                                This will be replaced with relevant context from your corpus documents when the prompt runs.
                              </p>
                            </div>

                            <div className="bg-accent/5 rounded-lg p-3 border border-accent/20">
                              <code className="font-mono font-bold text-accent text-sm">{'{query}'}</code>
                              <p className="font-body text-xs text-text/70 mt-1.5">
                                This will be replaced with the user's actual question or search query.
                              </p>
                            </div>
                          </div>

                          <div className="bg-secondary/10 rounded-lg p-3">
                            <p className="font-body text-xs text-text/80 font-medium mb-2">💡 Quick Tips:</p>
                            <ul className="font-body text-xs text-text/70 space-y-1 ml-4 list-disc">
                              <li>Click the insert buttons below to add variables</li>
                              <li>Or type them manually with curly braces</li>
                              <li>Position your cursor where you want to insert</li>
                            </ul>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <form onSubmit={handleCreatePrompt} className="space-y-5">
                    {/* Prompt Name Input */}
                    <div>
                      <label className="font-body text-sm font-medium text-text mb-2 block">
                        Prompt Name *
                      </label>
                      <input
                        type="text"
                        className="w-full border-2 border-secondary rounded-xl px-5 py-3 font-body focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-text"
                        placeholder="e.g., Customer Support Assistant, Technical Documentation Helper..."
                        value={newPromptName}
                        onChange={(e) => setNewPromptName(e.target.value)}
                        required
                      />
                    </div>

                    {/* Write/Preview Tab Switcher */}
                    <div className="flex gap-2 bg-secondary/20 p-1.5 rounded-xl w-fit shadow-inner">
                      <button
                        type="button"
                        onClick={() => {
                          setPreviewMode(false);
                          setValidationError('');
                        }}
                        className={`px-6 py-2.5 rounded-lg font-body text-sm font-bold transition-all ${
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
                        className={`px-6 py-2.5 rounded-lg font-body text-sm font-bold transition-all ${
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
                      <div className="bg-red-50 border-2 border-red-400 rounded-xl p-4 flex items-start gap-3">
                        <svg className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <div className="flex-1">
                          <div className="font-body font-bold text-red-900">{validationError}</div>
                          <div className="font-body text-sm text-red-700 mt-1">
                            Please include both required variables in your prompt.
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Quick Insert Buttons */}
                    {!previewMode && (
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-body text-sm text-text/60 font-medium">Quick Insert:</span>
                        <button
                          type="button"
                          onClick={() => insertVariable('{chunks}')}
                          className="px-4 py-2 bg-primary/10 hover:bg-primary/20 border-2 border-primary/30 text-primary rounded-lg font-mono text-sm font-bold transition-all hover:scale-105 flex items-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                          </svg>
                          {'{chunks}'}
                        </button>
                        <button
                          type="button"
                          onClick={() => insertVariable('{query}')}
                          className="px-4 py-2 bg-accent/10 hover:bg-accent/20 border-2 border-accent/30 text-accent rounded-lg font-mono text-sm font-bold transition-all hover:scale-105 flex items-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                          </svg>
                          {'{query}'}
                        </button>
                        <div className="ml-2 font-body text-xs text-text/50 italic">
                          Click to insert at cursor position
                        </div>
                      </div>
                    )}

                    {/* Input/Preview Area */}
                    <div className="relative">
                      {!previewMode ? (
                        <div>
                          <textarea
                            ref={(el) => setTextareaRef(el)}
                            className={`w-full border-2 rounded-xl px-5 py-4 font-body min-h-[300px] focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-text resize-y ${
                              validationError ? 'border-red-400' : 'border-secondary'
                            }`}
                            placeholder="Write your prompt in markdown...

**Example:**
You are a helpful AI assistant. Use the following context to answer the question.

**Context:** {chunks}

**Question:** {query}

**Instructions:**
- Use **bold** and *italic* text
- Create lists
- Add code blocks with \`code\`
- And much more!"
                            value={newPromptText}
                            onChange={(e) => {
                              setNewPromptText(e.target.value);
                              if (validationError) setValidationError('');
                            }}
                            required
                          />
                          <div className="mt-3 flex items-center gap-4 text-sm">
                            <div className={`flex items-center gap-2 ${newPromptText.includes('{chunks}') ? 'text-green-600' : 'text-text/40'}`}>
                              {newPromptText.includes('{chunks}') ? (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              ) : (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              )}
                              <code className="font-mono font-bold">{'{chunks}'}</code>
                            </div>
                            <div className={`flex items-center gap-2 ${newPromptText.includes('{query}') ? 'text-green-600' : 'text-text/40'}`}>
                              {newPromptText.includes('{query}') ? (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              ) : (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              )}
                              <code className="font-mono font-bold">{'{query}'}</code>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="w-full border-2 border-primary/30 rounded-xl px-6 py-5 min-h-[300px] bg-gradient-to-br from-background to-secondary/5">
                          {newPromptText.trim() ? (
                            <div className="prose prose-sm max-w-none font-body text-text">
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>{newPromptText}</ReactMarkdown>
                            </div>
                          ) : (
                            <div className="flex items-center justify-center h-full min-h-[250px]">
                              <p className="font-body text-text/40 italic text-lg">Preview will appear here...</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex justify-end gap-3 pt-4">
                      <button
                        type="button"
                        onClick={() => setPromptsTab('view')}
                        className="px-6 py-3 border-2 border-secondary text-text rounded-xl hover:bg-secondary/20 cursor-pointer font-body font-bold transition-all"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={creatingPrompt || !newPromptText.trim() || !newPromptName.trim()}
                        className="px-8 py-3 bg-gradient-to-r from-primary to-accent text-white rounded-xl hover:shadow-xl disabled:opacity-50 cursor-pointer font-body font-bold transition-all transform hover:scale-105 disabled:hover:scale-100 flex items-center gap-2"
                      >
                        {creatingPrompt ? (
                          <>
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                            Creating...
                          </>
                        ) : (
                          <>
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                            </svg>
                            Add Prompt
                          </>
                        )}
                      </button>
                    </div>
                  </form>
                </div>
              )}
            </div>
          </div>
        </div>
      )}


      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={deleteModal !== null}
        onClose={() => setDeleteModal(null)}
        onConfirm={() => {
          if (deleteModal?.type === 'test') handleDeleteTest(deleteModal.id);
          else if (deleteModal?.type === 'prompt') handleDeletePrompt(deleteModal.id);
          else if (deleteModal?.type === 'qa') handleDeleteQA(deleteModal.id);
          else if (deleteModal?.type === 'item') handleDeleteItem(deleteModal.data);
        }}
        itemType={deleteModal?.type || ''}
        itemName={deleteModal?.name || ''}
      />

      {/* Config Modal */}
      {configModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-xl shadow-2xl max-w-xl w-full max-h-[85vh] overflow-y-auto">
            <div className="sticky top-0 bg-background border-b border-secondary px-4 py-3">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-heading font-bold text-base text-text">Test Configuration</h2>
                  <p className="font-body text-xs text-text/60 mt-0.5">{configModal.testName}</p>
                </div>
                <button onClick={() => setConfigModal(null)} className="text-text/60 hover:text-text cursor-pointer">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <form onSubmit={handleSaveConfig} className="p-4 space-y-3">
              {/* Type */}
              <div>
                <label className="font-body text-xs font-medium text-text mb-1 block">
                  Chunking Type *
                </label>
                <select
                  className="w-full border border-secondary rounded-lg px-3 py-1.5 text-sm font-body bg-background"
                  value={configForm.type}
                  onChange={(e) => setConfigForm({ ...configForm, type: e.target.value })}
                  required
                >
                  {CONFIG_OPTIONS.types.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              {/* Generative Model */}
              <div>
                <label className="font-body text-xs font-medium text-text mb-1 block">
                  Generative Model *
                </label>
                <select
                  className="w-full border border-secondary rounded-lg px-3 py-1.5 text-sm font-body bg-background"
                  value={configForm.generative_model}
                  onChange={(e) => setConfigForm({ ...configForm, generative_model: e.target.value })}
                  required
                >
                  {CONFIG_OPTIONS.generativeModels.map(model => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
              </div>

              {/* Embedding Model */}
              <div>
                <label className="font-body text-xs font-medium text-text mb-1 block">
                  Embedding Model *
                </label>
                <select
                  className="w-full border border-secondary rounded-lg px-3 py-1.5 text-sm font-body bg-background"
                  value={configForm.embedding_model}
                  onChange={(e) => setConfigForm({ ...configForm, embedding_model: e.target.value })}
                  required
                >
                  {CONFIG_OPTIONS.embeddingModels.map(model => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
              </div>

              {/* Numerical Parameters in a Grid */}
              <div className="bg-secondary/5 rounded-lg p-3 space-y-3">
                <h3 className="font-heading font-semibold text-sm text-text">Numerical Parameters</h3>

                <div className="grid grid-cols-3 gap-3">
                  {/* Chunk Size */}
                  <div>
                    <label className="font-body text-xs font-medium text-text mb-1 block">
                      Chunk Size *
                    </label>
                    <input
                      type="number"
                      min="100"
                      max="5000"
                      className="w-full border border-secondary rounded-lg px-2 py-1.5 text-sm font-body bg-background"
                      value={configForm.chunk_size}
                      onChange={(e) => setConfigForm({ ...configForm, chunk_size: parseInt(e.target.value) || 100 })}
                      required
                    />
                    <p className="font-body text-xs text-text/50 mt-0.5">100-5000</p>
                  </div>

                  {/* Overlap */}
                  <div>
                    <label className="font-body text-xs font-medium text-text mb-1 block">
                      Overlap *
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="500"
                      className="w-full border border-secondary rounded-lg px-2 py-1.5 text-sm font-body bg-background"
                      value={configForm.overlap}
                      onChange={(e) => setConfigForm({ ...configForm, overlap: parseInt(e.target.value) || 0 })}
                      required
                    />
                    <p className="font-body text-xs text-text/50 mt-0.5">0-500</p>
                  </div>

                  {/* Top K */}
                  <div>
                    <label className="font-body text-xs font-medium text-text mb-1 block">
                      Top K *
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      className="w-full border border-secondary rounded-lg px-2 py-1.5 text-sm font-body bg-background"
                      value={configForm.top_k}
                      onChange={(e) => setConfigForm({ ...configForm, top_k: parseInt(e.target.value) || 1 })}
                      required
                    />
                    <p className="font-body text-xs text-text/50 mt-0.5">1-50</p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 pt-3 border-t border-secondary">
                <button
                  type="button"
                  onClick={() => setConfigModal(null)}
                  className="flex-1 px-3 py-1.5 text-sm border border-secondary rounded-lg hover:bg-secondary/20 cursor-pointer font-body font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingConfig}
                  className="flex-1 px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 cursor-pointer font-body font-medium"
                >
                  {savingConfig ? 'Saving…' : 'Save Config'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
