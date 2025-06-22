import React, { useEffect, useState } from 'react';

interface Directory {
  path: string;
  document_count: number;
}

interface RAGDirectoryListProps {
  selectedDirectory?: string | null;
  onDirectorySelect?: (directory: string | null) => void;
  onDirectoryCreated?: () => void;
}

export default function RAGDirectoryList({ selectedDirectory, onDirectorySelect, onDirectoryCreated }: RAGDirectoryListProps) {
  const [directories, setDirectories] = useState<Directory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newDirectoryName, setNewDirectoryName] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

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

      // Refresh directories list
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
            <span className="text-sm text-blue-600">
              {directories.find(d => d.path === selectedDirectory)?.document_count || 0} documents
            </span>
          </div>
        </div>
      ) : (
        <ul className="divide-y divide-gray-200">
          {directories.map((dir) => (
            <li key={dir.path} className="py-2">
              <button
                onClick={() => handleDirectoryClick(dir.path)}
                className="w-full flex justify-between items-center hover:bg-gray-50 p-2 rounded transition-colors"
              >
                <span className="font-mono text-gray-700">{dir.path}</span>
                <span className="text-sm text-gray-500">{dir.document_count} documents</span>
              </button>
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
    </div>
  );
}
