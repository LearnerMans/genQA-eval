import { useState, useEffect } from 'react';
import ProjectCard from '../components/ProjectCard';
import Pagination from '../components/Pagination';
import { projectsAPI } from '../services/api';
import { useToast } from '../components/Toaster.jsx';

export default function Projects() {
  const toast = useToast();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [creating, setCreating] = useState(false);
  const [query, setQuery] = useState('');

  const projectsPerPage = 9;

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const data = await projectsAPI.getAllProjects();
      setProjects(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      toast.error(err.message || 'Failed to fetch projects', 'Request Failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    try {
      setCreating(true);
      await projectsAPI.createProject(newProjectName.trim());
      setNewProjectName('');
      setShowCreateModal(false);
      await fetchProjects();
      // toast.success('Project created', newProjectName.trim());
    } catch (err) {
      toast.error(err.message || 'Failed to create project', 'Request Failed');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteProject = async (projectId) => {
    try {
      await projectsAPI.deleteProject(projectId);
      await fetchProjects();
      if (paginatedProjects.length === 1 && currentPage > 1) {
        setCurrentPage(currentPage - 1);
      }
    } catch (err) {
      toast.error(err.message || 'Failed to delete project', 'Request Failed');
    }
  };

  const handleOpenProject = (project) => {
    // No router in this app yet; surface a toast for now
    toast.info(`"${project.name}"`, 'Open Project');
    // Optionally, implement navigation once routes exist
  };

  const filtered = projects.filter((p) =>
    p?.name?.toLowerCase().includes(query.trim().toLowerCase())
  );
  const totalPages = Math.ceil(filtered.length / projectsPerPage) || 1;
  const indexOfLastProject = currentPage * projectsPerPage;
  const indexOfFirstProject = indexOfLastProject - projectsPerPage;
  const paginatedProjects = filtered.slice(indexOfFirstProject, indexOfLastProject);

  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 font-body text-text/70">Loading projects...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="font-body text-red-500">Error: {error}</p>
          <button
            onClick={fetchProjects}
            className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 cursor-pointer"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Content */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 py-12">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h2 className="font-heading font-bold text-2xl text-text">Projects</h2>
            <p className="font-body text-text/70 mt-1">
              {filtered.length > 0 ? `${filtered.length} project${filtered.length === 1 ? '' : 's'}` : 'No projects yet'}
            </p>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-80">
              <input
                type="text"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder="Search projects..."
                className="w-full pl-10 pr-3 py-2 border border-secondary rounded-lg bg-background text-text font-body focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-text/50" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-4.35-4.35M11 18a7 7 0 100-14 7 7 0 000 14z" />
              </svg>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex px-4 py-2 bg-primary text-white font-body font-bold rounded-lg hover:bg-primary/90 transition-colors cursor-pointer"
            >
              Create Project
            </button>
          </div>
        </div>

        {projects.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-secondary rounded-xl bg-background/60">
            <div className="mx-auto h-14 w-14 rounded-lg bg-accent/30 flex items-center justify-center">
              <svg className="h-7 w-7 text-primary" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
              </svg>
            </div>
            <h3 className="mt-4 font-heading font-bold text-xl text-text">Create your first project</h3>
            <p className="mt-1 font-body text-text/70">Use the button above to get started.</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {paginatedProjects.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onDelete={handleDeleteProject}
                  onOpen={handleOpenProject}
                />
              ))}
            </div>

            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          </>
        )}
      </main>

      {/* Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-text/50 flex items-center justify-center p-4 z-50">
          <div className="bg-background rounded-lg p-6 max-w-md w-full border border-secondary">
            <h2 className="font-heading font-bold text-2xl text-text mb-4">
              Create New Project
            </h2>
            <form onSubmit={handleCreateProject}>
              <label className="block mb-2 font-body font-bold text-sm text-text">
                Project Name
              </label>
              <input
                type="text"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                className="w-full px-4 py-2 border border-secondary rounded-lg font-body focus:outline-none focus:ring-2 focus:ring-accent bg-background text-text"
                placeholder="Enter project name"
                autoFocus
                maxLength={255}
                required
              />
              <div className="flex gap-3 mt-6">
                <button
                  type="submit"
                  disabled={creating || !newProjectName.trim()}
                  className="flex-1 px-4 py-2 bg-primary text-white font-body font-bold rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  {creating ? 'Creating...' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewProjectName('');
                  }}
                  disabled={creating}
                  className="flex-1 px-4 py-2 bg-secondary text-text font-body font-bold rounded-lg hover:bg-secondary/90 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="mt-auto border-t border-secondary/50">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center">
          <p className="font-body text-text/60">&copy; {new Date().getFullYear()} RAG Eval Core</p>
        </div>
      </footer>
    </div>
  );
}
