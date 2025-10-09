import { useEffect, useMemo, useState } from 'react';
import { projectsAPI, testsAPI, corpusAPI, qaAPI, configAPI } from '../services/api';
import { useToast } from '../components/Toaster.jsx';

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

  const [corpus, setCorpus] = useState(null);
  const [corpusLoading, setCorpusLoading] = useState(true);
  const [newCorpusName, setNewCorpusName] = useState('Default Corpus');
  const [items, setItems] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [addingUrl, setAddingUrl] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [preview, setPreview] = useState(null); // {type: 'file'|'url', data}

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
      <header className="w-full max-w-7xl mx-auto px-4 py-6">
        <div>
          <button onClick={goBack} className="font-body text-sm text-text/70 hover:text-text cursor-pointer">← Back to Projects</button>
          <h1 className="font-heading font-bold text-2xl text-text mt-2">{project.name}</h1>
          <p className="font-body text-text/60 text-sm">Project ID: {project.id}</p>
        </div>

        {/* Tabs */}
        <div className="mt-6 flex gap-2 border-b border-secondary/40">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 font-body font-medium transition-colors cursor-pointer ${
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

      <main className="w-full max-w-7xl mx-auto px-4 pb-12">
        {/* Tests Tab */}
        {activeTab === 'tests' && (
          <section className="space-y-6">
            <div className="bg-background border border-secondary rounded-xl p-6">
              <h2 className="font-heading font-bold text-xl text-text mb-4">Create New Test</h2>
              <form onSubmit={handleCreateTest} className="flex gap-2">
                <input
                  type="text"
                  className="flex-1 border border-secondary rounded-lg px-3 py-2 font-body"
                  placeholder="New test name…"
                  value={newTestName}
                  onChange={(e) => setNewTestName(e.target.value)}
                />
                <button disabled={creatingTest || !newTestName.trim()} className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 cursor-pointer font-body font-medium">
                  {creatingTest ? 'Creating…' : 'Create Test'}
                </button>
              </form>
            </div>

            {/* Fancy Test Cards */}
            {tests.length === 0 ? (
              <div className="bg-background border border-secondary rounded-xl p-12 text-center">
                <div className="font-body text-text/60 text-lg">No tests yet</div>
                <p className="font-body text-text/40 text-sm mt-2">Create your first test to get started</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {tests.map((t) => (
                  <div key={t.id} className="bg-gradient-to-br from-background to-secondary/5 border border-secondary rounded-xl p-5 hover:shadow-lg transition-all duration-200 hover:border-primary/30">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-heading font-bold text-lg text-text truncate">{t.name}</h3>
                        <p className="font-body text-xs text-text/50 mt-1">ID: {t.id.slice(0, 8)}...</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-text/60 font-body mb-4">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {formatDate(t.created_at)}
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => handleOpenConfigModal(t)}
                        className="flex-1 px-3 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 font-body text-sm font-medium cursor-pointer transition-colors flex items-center justify-center gap-1.5"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        Config
                      </button>
                      <button
                        onClick={() => handleDeleteTest(t.id)}
                        className="px-3 py-2 border border-red-600 text-red-600 rounded-lg hover:bg-red-50 font-body text-sm cursor-pointer transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
          <section className="bg-background border border-secondary rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-heading font-bold text-xl text-text">Corpus</h2>
            </div>

            {corpusLoading ? (
              <div className="font-body text-text/60">Loading corpus…</div>
            ) : !corpus ? (
              <form onSubmit={handleCreateCorpus} className="flex gap-2">
                <input
                  type="text"
                  className="flex-1 border border-secondary rounded-lg px-3 py-2 font-body"
                  placeholder="Corpus name"
                  value={newCorpusName}
                  onChange={(e) => setNewCorpusName(e.target.value)}
                />
                <button className="px-3 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 cursor-pointer">Create Corpus</button>
              </form>
            ) : (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-body text-text font-medium">{corpus.name}</div>
                    <div className="font-body text-xs text-text/60">ID: {corpus.id}</div>
                  </div>
                </div>

                {/* Styled Upload Section */}
                <div className="bg-secondary/10 border-2 border-dashed border-secondary rounded-xl p-6">
                  <h3 className="font-heading font-bold text-base text-text mb-4">Add Content to Corpus</h3>

                  <div className="space-y-4">
                    {/* File Upload */}
                    <div className="bg-background rounded-lg p-4 border border-secondary">
                      <label className="font-body text-sm font-medium text-text mb-2 block">Upload File</label>
                      <div className="flex items-center gap-3">
                        <label className="flex-1 cursor-pointer">
                          <div className="border border-secondary rounded-lg px-4 py-2 hover:bg-secondary/20 transition-colors text-center">
                            <span className="font-body text-sm text-text/70">
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
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
                        )}
                      </div>
                    </div>

                    {/* URL Input */}
                    <div className="bg-background rounded-lg p-4 border border-secondary">
                      <label className="font-body text-sm font-medium text-text mb-2 block">Add URL</label>
                      <form onSubmit={handleAddUrl} className="flex gap-2">
                        <input
                          type="url"
                          className="flex-1 border border-secondary rounded-lg px-3 py-2 font-body text-sm"
                          placeholder="https://example.com/document"
                          value={newUrl}
                          onChange={(e) => setNewUrl(e.target.value)}
                        />
                        <button
                          disabled={addingUrl || !newUrl.trim()}
                          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 cursor-pointer font-body text-sm font-medium"
                        >
                          {addingUrl ? 'Adding…' : 'Add'}
                        </button>
                      </form>
                    </div>
                  </div>
                </div>

                {/* Items List */}
                <div>
                  <h3 className="font-heading font-bold text-lg text-text mb-3">Items ({items.length})</h3>
                  {items.length === 0 ? (
                    <div className="font-body text-text/60 text-center py-8 bg-secondary/5 rounded-lg">
                      No items in corpus yet. Upload a file or add a URL to get started.
                    </div>
                  ) : (
                    <div className="divide-y divide-secondary/40">
                      {items.map((it) => (
                        <div key={it.id} className="py-3 flex items-center justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <div className="font-body text-text">
                              {it.type === 'file' ? `${it.metadata?.name || it.id}${it.metadata?.ext || ''}` : it.metadata?.url}
                            </div>
                            <div className="font-body text-xs text-text/60">{it.type.toUpperCase()} · Created {formatDate(it.metadata?.created_at)}</div>
                          </div>
                          <div className="flex items-center gap-2">
                            <button onClick={() => handlePreview(it)} className="px-3 py-1 text-sm border border-secondary rounded-md hover:bg-secondary/30 cursor-pointer font-body">Preview</button>
                            <button onClick={() => handleDeleteItem(it)} className="px-3 py-1 text-sm text-red-600 hover:text-red-700 cursor-pointer font-body">Delete</button>
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
          <section className="bg-background border border-secondary rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-heading font-bold text-xl text-text">QA Set</h2>
              <div className="flex items-center gap-2">
                {qaSet.length > 0 && (
                  <button
                    onClick={() => setShowQAForms(!showQAForms)}
                    className="px-3 py-2 border border-secondary text-text rounded-lg hover:bg-secondary/20 cursor-pointer font-body text-sm font-medium"
                  >
                    {showQAForms ? '✕ Hide Forms' : '+ Add QA'}
                  </button>
                )}
                <button
                  onClick={handleDownloadTemplate}
                  className="px-3 py-2 border border-primary text-primary rounded-lg hover:bg-primary/10 cursor-pointer font-body text-sm font-medium"
                >
                  📥 Template
                </button>
              </div>
            </div>

            {qaLoading ? (
              <div className="font-body text-text/60">Loading QA pairs…</div>
            ) : (
              <div className="space-y-6">
                {/* Show forms when: no QA pairs OR showQAForms is true */}
                {(qaSet.length === 0 || showQAForms) && (
                  <>
                    {/* Manual Entry Form */}
                    <div className="bg-secondary/10 border-2 border-dashed border-secondary rounded-xl p-6">
                      <h3 className="font-heading font-bold text-base text-text mb-4">Add QA Pair Manually</h3>
                      <form onSubmit={handleCreateQA} className="space-y-4">
                        <div>
                          <label className="font-body text-sm font-medium text-text mb-2 block">Question</label>
                          <input
                            type="text"
                            className="w-full border border-secondary rounded-lg px-3 py-2 font-body"
                            placeholder="What is RAG?"
                            value={newQuestion}
                            onChange={(e) => setNewQuestion(e.target.value)}
                            required
                          />
                        </div>
                        <div>
                          <label className="font-body text-sm font-medium text-text mb-2 block">Answer</label>
                          <textarea
                            className="w-full border border-secondary rounded-lg px-3 py-2 font-body min-h-[100px]"
                            placeholder="RAG stands for Retrieval-Augmented Generation..."
                            value={newAnswer}
                            onChange={(e) => setNewAnswer(e.target.value)}
                            required
                          />
                        </div>
                        <button
                          disabled={creatingQA || !newQuestion.trim() || !newAnswer.trim()}
                          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 cursor-pointer font-body font-medium"
                        >
                          {creatingQA ? 'Creating…' : 'Add QA Pair'}
                        </button>
                      </form>
                    </div>

                    {/* CSV Upload Section */}
                    <div className="bg-secondary/10 border-2 border-dashed border-secondary rounded-xl p-6">
                      <h3 className="font-heading font-bold text-base text-text mb-4">Upload CSV File</h3>
                      <div className="space-y-3">
                        <p className="font-body text-sm text-text/70">
                          Upload a CSV file with <code className="bg-secondary/30 px-1 rounded">question</code> and <code className="bg-secondary/30 px-1 rounded">answer</code> columns. Duplicates will be automatically skipped.
                        </p>
                        <div className="flex items-center gap-3">
                          <label className="flex-1 cursor-pointer">
                            <div className="border border-secondary rounded-lg px-4 py-3 hover:bg-secondary/20 transition-colors text-center bg-background">
                              <span className="font-body text-sm text-text/70">
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
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
                          )}
                        </div>
                      </div>
                    </div>
                  </>
                )}

                {/* QA Pairs List */}
                <div>
                  <h3 className="font-heading font-bold text-lg text-text mb-3">QA Pairs ({qaSet.length})</h3>
                  {qaSet.length === 0 ? (
                    <div className="font-body text-text/60 text-center py-8 bg-secondary/5 rounded-lg">
                      No QA pairs yet. Add them manually or upload a CSV file.
                    </div>
                  ) : (
                    <div className="divide-y divide-secondary/40">
                      {qaSet.map((qa) => (
                        <div key={qa.id} className="py-4">
                          <div className="flex items-start justify-between gap-3 mb-2">
                            <div className="flex-1 min-w-0">
                              <div className="font-body text-text font-medium mb-1">Q: {qa.question}</div>
                              <div className="font-body text-text/80 text-sm">A: {qa.answer}</div>
                            </div>
                            <button
                              onClick={() => handleDeleteQA(qa.id)}
                              className="px-3 py-1 text-sm text-red-600 hover:text-red-700 cursor-pointer font-body flex-shrink-0"
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

      {/* Config Modal */}
      {configModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-background border-b border-secondary px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-heading font-bold text-xl text-text">Test Configuration</h2>
                  <p className="font-body text-sm text-text/60 mt-1">{configModal.testName}</p>
                </div>
                <button onClick={() => setConfigModal(null)} className="text-text/60 hover:text-text cursor-pointer">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <form onSubmit={handleSaveConfig} className="p-6 space-y-5">
              {/* Type */}
              <div>
                <label className="font-body text-sm font-medium text-text mb-2 block">
                  Chunking Type *
                </label>
                <select
                  className="w-full border border-secondary rounded-lg px-3 py-2 font-body bg-background"
                  value={configForm.type}
                  onChange={(e) => setConfigForm({ ...configForm, type: e.target.value })}
                  required
                >
                  {CONFIG_OPTIONS.types.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
                <p className="font-body text-xs text-text/50 mt-1">Choose between semantic or recursive chunking</p>
              </div>

              {/* Generative Model */}
              <div>
                <label className="font-body text-sm font-medium text-text mb-2 block">
                  Generative Model *
                </label>
                <select
                  className="w-full border border-secondary rounded-lg px-3 py-2 font-body bg-background"
                  value={configForm.generative_model}
                  onChange={(e) => setConfigForm({ ...configForm, generative_model: e.target.value })}
                  required
                >
                  {CONFIG_OPTIONS.generativeModels.map(model => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
                <p className="font-body text-xs text-text/50 mt-1">Model used for generating responses</p>
              </div>

              {/* Embedding Model */}
              <div>
                <label className="font-body text-sm font-medium text-text mb-2 block">
                  Embedding Model *
                </label>
                <select
                  className="w-full border border-secondary rounded-lg px-3 py-2 font-body bg-background"
                  value={configForm.embedding_model}
                  onChange={(e) => setConfigForm({ ...configForm, embedding_model: e.target.value })}
                  required
                >
                  {CONFIG_OPTIONS.embeddingModels.map(model => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
                <p className="font-body text-xs text-text/50 mt-1">Model used for creating embeddings</p>
              </div>

              {/* Numerical Parameters in a Grid */}
              <div className="bg-secondary/5 rounded-lg p-5 space-y-4">
                <h3 className="font-heading font-semibold text-base text-text mb-3">Numerical Parameters</h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Chunk Size */}
                  <div>
                    <label className="font-body text-sm font-medium text-text mb-2 block">
                      Chunk Size *
                    </label>
                    <input
                      type="number"
                      min="100"
                      max="5000"
                      className="w-full border border-secondary rounded-lg px-3 py-2.5 font-body bg-background focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors"
                      value={configForm.chunk_size}
                      onChange={(e) => setConfigForm({ ...configForm, chunk_size: parseInt(e.target.value) || 100 })}
                      required
                    />
                    <div className="mt-1.5 space-y-0.5">
                      <p className="font-body text-xs text-text/50">Range: 100-5000</p>
                      <p className="font-body text-xs text-primary/80">Recommended: 500-1500</p>
                    </div>
                  </div>

                  {/* Overlap */}
                  <div>
                    <label className="font-body text-sm font-medium text-text mb-2 block">
                      Overlap *
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="500"
                      className="w-full border border-secondary rounded-lg px-3 py-2.5 font-body bg-background focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors"
                      value={configForm.overlap}
                      onChange={(e) => setConfigForm({ ...configForm, overlap: parseInt(e.target.value) || 0 })}
                      required
                    />
                    <div className="mt-1.5 space-y-0.5">
                      <p className="font-body text-xs text-text/50">Range: 0-500</p>
                      <p className="font-body text-xs text-primary/80">Recommended: 50-200</p>
                    </div>
                  </div>

                  {/* Top K */}
                  <div>
                    <label className="font-body text-sm font-medium text-text mb-2 block">
                      Top K *
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      className="w-full border border-secondary rounded-lg px-3 py-2.5 font-body bg-background focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors"
                      value={configForm.top_k}
                      onChange={(e) => setConfigForm({ ...configForm, top_k: parseInt(e.target.value) || 1 })}
                      required
                    />
                    <div className="mt-1.5 space-y-0.5">
                      <p className="font-body text-xs text-text/50">Range: 1-50</p>
                      <p className="font-body text-xs text-primary/80">Recommended: 5-15</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4 border-t border-secondary">
                <button
                  type="button"
                  onClick={() => setConfigModal(null)}
                  className="flex-1 px-4 py-2 border border-secondary rounded-lg hover:bg-secondary/20 cursor-pointer font-body font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingConfig}
                  className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 cursor-pointer font-body font-medium"
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

