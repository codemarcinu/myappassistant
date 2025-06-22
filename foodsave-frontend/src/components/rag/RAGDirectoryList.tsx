import React, { useEffect, useState } from 'react';

interface Directory {
  path: string;
  document_count: number;
}

interface DirectoryStats {
  total_documents: number;
  total_chunks: number;
  total_tags: number;
  file_types: string[];
  recent_activity: number;
  average_chunks_per_document: number;
}

interface RAGDirectoryListProps {
  selectedDirectory?: string | null;
  onDirectorySelect?: (directory: string | null) => void;
  onDirectoryCreated?: () => void;
  onDirectoryDeleted?: () => void;
  onDirectoryRenamed?: () => void;
}

export default function RAGDirectoryList({
  selectedDirectory,
  onDirectorySelect,
  onDirectoryCreated,
  onDirectoryDeleted,
  onDirectoryRenamed
}: RAGDirectoryListProps) {
  const [directories, setDirectories] = useState<Directory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newDirectoryName, setNewDirectoryName] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletingDirectory, setDeletingDirectory] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [renamingDirectory, setRenamingDirectory] = useState<string | null>(null);
  const [newDirectoryPath, setNewDirectoryPath] = useState('');
  const [renaming, setRenaming] = useState(false);
  const [renameError, setRenameError] = useState<string | null>(null);
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [statsDirectory, setStatsDirectory] = useState<string | null>(null);
  const [directoryStats, setDirectoryStats] = useState<DirectoryStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [statsError, setStatsError] = useState<string | null>(null);

  const fetchDirectories = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v2/rag/directories');
      if (!response.ok) throw new Error('Failed to fetch directories');
      const data = await response.json();
      setDirectories(data.directories || []);
    } catch (err: any) {
      setError(err.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDirectories();
  }, []);

  const handleDirectoryClick = (directory: string) => {
    onDirectorySelect?.(directory);
  };

  const handleBackToAll = () => {
    onDirectorySelect?.(null);
  };

  const handleCreateDirectory = async () => {
    if (!newDirectoryName.trim()) {
      setCreateError('Directory name cannot be empty');
      return;
    }

    setCreating(true);
    setCreateError(null);

    try {
      const response = await fetch('/api/v2/rag/create-directory', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ directory_path: newDirectoryName.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to create directory');
      }

      await fetchDirectories();
      setShowCreateModal(false);
      setNewDirectoryName('');
      onDirectoryCreated?.();
    } catch (err: any) {
      setCreateError(err.message || 'Unknown error');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteDirectory = async () => {
    if (!deletingDirectory) return;

    setDeleting(true);
    setDeleteError(null);

    try {
      const response = await fetch(`/api/v2/rag/directories/${encodeURIComponent(deletingDirectory)}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to delete directory');
      }

      await fetchDirectories();
      setShowDeleteModal(false);
      setDeletingDirectory(null);
      onDirectoryDeleted?.();
    } catch (err: any) {
      setDeleteError(err.message || 'Unknown error');
    } finally {
      setDeleting(false);
    }
  };

  const handleRenameDirectory = async () => {
    if (!renamingDirectory || !newDirectoryPath.trim()) {
      setRenameError('Please enter a new directory name');
      return;
    }

    setRenaming(true);
    setRenameError(null);

    try {
      const response = await fetch(`/api/v2/rag/directories/${encodeURIComponent(renamingDirectory)}/rename`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_directory_path: newDirectoryPath.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to rename directory');
      }

      await fetchDirectories();
      setShowRenameModal(false);
      setRenamingDirectory(null);
      setNewDirectoryPath('');
      onDirectoryRenamed?.();
    } catch (err: any) {
      setRenameError(err.message || 'Unknown error');
    } finally {
      setRenaming(false);
    }
  };

  const handleShowStats = async (directory: string) => {
    setStatsDirectory(directory);
    setLoadingStats(true);
    setStatsError(null);
    setShowStatsModal(true);

    try {
      const response = await fetch(`/api/v2/rag/directories/${encodeURIComponent(directory)}/stats`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to fetch directory stats');
      }

      const data = await response.json();
      setDirectoryStats(data.stats);
    } catch (err: any) {
      setStatsError(err.message || 'Unknown error');
    } finally {
      setLoadingStats(false);
    }
  };

  if (loading) return <div className="py-4 text-gray-500">Loading directories...</div>;
  if (error) return <div className="py-4 text-red-500">Error: {error}</div>;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mt-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">RAG Directories</h2>
        <div className="flex items-center space-x-2">
          {selectedDirectory && (
            <button
              onClick={handleBackToAll}
              className="text-sm text-blue-600 hover:text-blue-800 underline"
            >
              ← Back to all directories
            </button>
          )}
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
          >
            + Create Directory
          </button>
        </div>
      </div>

      {directories.length === 0 ? (
        <div className="py-4 text-gray-500">No directories found.</div>
      ) : selectedDirectory ? (
        <div className="py-2">
          <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
            <span className="font-mono text-blue-700">{selectedDirectory}</span>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-blue-600">
                {directories.find(d => d.path === selectedDirectory)?.document_count || 0} documents
              </span>
              <button
                onClick={() => handleShowStats(selectedDirectory)}
                className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded"
                title="View statistics"
              >
                📊
              </button>
              <button
                onClick={() => {
                  setRenamingDirectory(selectedDirectory);
                  setNewDirectoryPath(selectedDirectory);
                  setShowRenameModal(true);
                }}
                className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded"
                title="Rename directory"
              >
                ✏️
              </button>
              <button
                onClick={() => {
                  setDeletingDirectory(selectedDirectory);
                  setShowDeleteModal(true);
                }}
                className="p-1 text-red-600 hover:text-red-800 hover:bg-red-100 rounded"
                title="Delete directory"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>
      ) : (
        <ul className="divide-y divide-gray-200">
          {directories.map((dir) => (
            <li key={dir.path} className="py-2">
              <div className="flex justify-between items-center hover:bg-gray-50 p-2 rounded transition-colors">
                <button
                  onClick={() => handleDirectoryClick(dir.path)}
                  className="flex-1 text-left"
                >
                  <span className="font-mono text-gray-700">{dir.path}</span>
                </button>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">{dir.document_count} documents</span>
                  <button
                    onClick={() => handleShowStats(dir.path)}
                    className="p-1 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded"
                    title="View statistics"
                  >
                    📊
                  </button>
                  <button
                    onClick={() => {
                      setRenamingDirectory(dir.path);
                      setNewDirectoryPath(dir.path);
                      setShowRenameModal(true);
                    }}
                    className="p-1 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded"
                    title="Rename directory"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={() => {
                      setDeletingDirectory(dir.path);
                      setShowDeleteModal(true);
                    }}
                    className="p-1 text-red-600 hover:text-red-800 hover:bg-red-100 rounded"
                    title="Delete directory"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* Create Directory Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Create New Directory</h3>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Directory Name
              </label>
              <input
                type="text"
                value={newDirectoryName}
                onChange={(e) => setNewDirectoryName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., recipes, guides, work"
                onKeyPress={(e) => e.key === 'Enter' && handleCreateDirectory()}
              />
            </div>

            {createError && (
              <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">
                {createError}
              </div>
            )}

            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewDirectoryName('');
                  setCreateError(null);
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
                disabled={creating}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateDirectory}
                disabled={creating || !newDirectoryName.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Directory Modal */}
      {showDeleteModal && deletingDirectory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-lg font-semibold mb-4 text-red-600">Delete Directory</h3>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                Are you sure you want to delete the directory <strong>{deletingDirectory}</strong>?
              </p>
              <p className="text-sm text-red-600">
                All documents in this directory will be moved to the default directory.
              </p>
            </div>

            {deleteError && (
              <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">
                {deleteError}
              </div>
            )}

            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeletingDirectory(null);
                  setDeleteError(null);
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteDirectory}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rename Directory Modal */}
      {showRenameModal && renamingDirectory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Rename Directory</h3>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                Renaming: <strong>{renamingDirectory}</strong>
              </p>

              <label className="block text-sm font-medium text-gray-700 mb-2">
                New Directory Name
              </label>
              <input
                type="text"
                value={newDirectoryPath}
                onChange={(e) => setNewDirectoryPath(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter new directory name"
                onKeyPress={(e) => e.key === 'Enter' && handleRenameDirectory()}
              />
            </div>

            {renameError && (
              <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">
                {renameError}
              </div>
            )}

            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowRenameModal(false);
                  setRenamingDirectory(null);
                  setNewDirectoryPath('');
                  setRenameError(null);
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
                disabled={renaming}
              >
                Cancel
              </button>
              <button
                onClick={handleRenameDirectory}
                disabled={renaming || !newDirectoryPath.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {renaming ? 'Renaming...' : 'Rename'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Directory Stats Modal */}
      {showStatsModal && statsDirectory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Directory Statistics</h3>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-4">
                <strong>{statsDirectory}</strong>
              </p>

              {loadingStats ? (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="text-sm text-gray-500 mt-2">Loading statistics...</p>
                </div>
              ) : statsError ? (
                <div className="p-2 bg-red-50 text-red-600 text-sm rounded">
                  {statsError}
                </div>
              ) : directoryStats ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-blue-50 rounded">
                      <div className="text-2xl font-bold text-blue-600">{directoryStats.total_documents}</div>
                      <div className="text-xs text-blue-600">Documents</div>
                    </div>
                    <div className="p-3 bg-green-50 rounded">
                      <div className="text-2xl font-bold text-green-600">{directoryStats.total_chunks}</div>
                      <div className="text-xs text-green-600">Chunks</div>
                    </div>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Tags:</span>
                      <span className="font-medium">{directoryStats.total_tags}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Recent Activity:</span>
                      <span className="font-medium">{directoryStats.recent_activity} docs</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Avg Chunks/Doc:</span>
                      <span className="font-medium">{directoryStats.average_chunks_per_document}</span>
                    </div>
                    {directoryStats.file_types.length > 0 && (
                      <div>
                        <span className="text-gray-600">File Types:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {directoryStats.file_types.map((type) => (
                            <span key={type} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                              .{type}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : null}
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => {
                  setShowStatsModal(false);
                  setStatsDirectory(null);
                  setDirectoryStats(null);
                  setStatsError(null);
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
