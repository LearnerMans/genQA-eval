const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const projectsAPI = {
  async getAllProjects() {
    const response = await fetch(`${API_BASE_URL}/projects`);
    if (!response.ok) {
      throw new Error('Failed to fetch projects');
    }
    return response.json();
  },

  async createProject(name) {
    const response = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create project');
    }
    return response.json();
  },

  async deleteProject(projectId) {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete project');
    }
    return response.json();
  },
};

export const testsAPI = {
  async getByProject(projectId) {
    const response = await fetch(`${API_BASE_URL}/tests/project/${projectId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch tests');
    }
    return response.json();
  },

  async createTest({ name, project_id }) {
    const response = await fetch(`${API_BASE_URL}/tests`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, project_id }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to create test');
    }
    return response.json();
  },

  async deleteTest(testId) {
    const response = await fetch(`${API_BASE_URL}/tests/${testId}`, { method: 'DELETE' });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to delete test');
    }
    return response.json();
  },
};

export const corpusAPI = {
  async getCorpusByProject(projectId) {
    const response = await fetch(`${API_BASE_URL}/corpus/project/${projectId}`);
    if (response.status === 404) return null; // no corpus yet
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to fetch corpus');
    }
    return response.json();
  },

  async createCorpus({ project_id, name }) {
    const response = await fetch(`${API_BASE_URL}/corpus`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id, name }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to create corpus');
    }
    return response.json();
  },

  async getItemsByProject(projectId) {
    const response = await fetch(`${API_BASE_URL}/corpus-items/project/${projectId}`);
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to fetch corpus items');
    }
    return response.json();
  },

  async uploadFile({ project_id, corpus_id, file }) {
    const form = new FormData();
    form.append('project_id', project_id);
    form.append('corpus_id', corpus_id);
    form.append('file', file);
    const response = await fetch(`${API_BASE_URL}/corpus-files/upload`, {
      method: 'POST',
      body: form,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to upload file');
    }
    return response.json();
  },

  async addUrl({ project_id, corpus_id, url }) {
    const response = await fetch(`${API_BASE_URL}/corpus-urls`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id, corpus_id, url, content: '' }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to add URL');
    }
    return response.json();
  },

  async getFileById(fileId) {
    const response = await fetch(`${API_BASE_URL}/corpus-files/${fileId}`);
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to fetch file');
    }
    return response.json();
  },

  async getUrlById(urlId) {
    const response = await fetch(`${API_BASE_URL}/corpus-urls/${urlId}`);
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to fetch URL');
    }
    return response.json();
  },

  async deleteFile(fileId) {
    const response = await fetch(`${API_BASE_URL}/corpus-files/${fileId}`, { method: 'DELETE' });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to delete file');
    }
    return response.json();
  },

  async deleteUrl(urlId) {
    const response = await fetch(`${API_BASE_URL}/corpus-urls/${urlId}`, { method: 'DELETE' });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to delete URL');
    }
    return response.json();
  },
};

export const qaAPI = {
  async getByProject(projectId) {
    const response = await fetch(`${API_BASE_URL}/qa/project/${projectId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch QA pairs');
    }
    return response.json();
  },

  async createQA({ project_id, question, answer }) {
    const response = await fetch(`${API_BASE_URL}/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id, question, answer }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to create QA pair');
    }
    return response.json();
  },

  async uploadCSV({ project_id, file }) {
    const form = new FormData();
    form.append('project_id', project_id);
    form.append('file', file);
    const response = await fetch(`${API_BASE_URL}/qa/upload-csv`, {
      method: 'POST',
      body: form,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to upload CSV');
    }
    return response.json();
  },

  async deleteQA(qaId) {
    const response = await fetch(`${API_BASE_URL}/qa/${qaId}`, { method: 'DELETE' });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to delete QA pair');
    }
    return response.json();
  },

  downloadTemplate() {
    // Create CSV with BOM for Excel compatibility
    const BOM = '\uFEFF';
    const csvContent = BOM + 'question,answer\n"What is RAG?","RAG stands for Retrieval-Augmented Generation, a technique that combines retrieval and generation."\n"How does it work?","It retrieves relevant documents and uses them to generate more accurate responses."';

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'qa_template.csv';
    link.click();
    URL.revokeObjectURL(link.href);
  },
};

// POSSIBLE VALUES FOR CONFIG FIELDS
// type: "semantic" | "recursive"
// generative_model: "openai_4o" | "openai_4o_mini" | "claude_sonnet_3_5" | "claude_opus_3" | "gemini_pro"
// embedding_model: "openai_text_embedding_large_3" | "openai_text_embedding_small_3" | "cohere_embed_v3" | "voyage_ai_2"
// chunk_size: 100-5000 (recommended: 500-1500)
// overlap: 0-500 (recommended: 50-200)
// top_k: 1-50 (recommended: 5-15)

export const configAPI = {
  async getByTestId(testId) {
    const response = await fetch(`${API_BASE_URL}/configs/${testId}`);
    if (response.status === 404) return null; // no config yet
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to fetch config');
    }
    return response.json();
  },

  async createConfig(configData) {
    const response = await fetch(`${API_BASE_URL}/configs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(configData),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to create config');
    }
    return response.json();
  },

  async deleteConfig(testId) {
    const response = await fetch(`${API_BASE_URL}/configs/${testId}`, { method: 'DELETE' });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to delete config');
    }
    return response.json();
  },
};

export const promptsAPI = {
  async getByTest(testId) {
    const response = await fetch(`${API_BASE_URL}/prompts/test/${testId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch prompts');
    }
    return response.json();
  },

  async createPrompt({ test_id, name, prompt }) {
    const response = await fetch(`${API_BASE_URL}/prompts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ test_id, name, prompt }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to create prompt');
    }
    return response.json();
  },

  async deletePrompt(promptId) {
    const response = await fetch(`${API_BASE_URL}/prompts/${promptId}`, { method: 'DELETE' });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to delete prompt');
    }
    return response.json();
  },
};

export const testRunsAPI = {
  async getByTest(testId) {
    const response = await fetch(`${API_BASE_URL}/test-runs/test/${testId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch test runs');
    }
    return response.json();
  },

  async createRun({ test_id, prompt_id }) {
    const response = await fetch(`${API_BASE_URL}/test-runs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ test_id, prompt_id }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to create test run');
    }
    return response.json();
  },
};

export const evalsAPI = {
  async getByRun(test_run_id) {
    const response = await fetch(`${API_BASE_URL}/evals/run/${test_run_id}`);
    if (!response.ok) {
      throw new Error('Failed to fetch evaluations');
    }
    return response.json();
  },
};
