import React, { useEffect, useState } from 'react';

interface Directory {
  path: string;
  document_count: number;
}

interface RAGDirectoryListProps {
  selectedDirectory?: string | null;
  onDirectorySelect?: (directory: string | null) => void;
}

export default function RAGDirectoryList({ selectedDirectory, onDirectorySelect }: RAGDirectoryListProps) {
  const [directories, setDirectories] = useState<Directory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
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
    fetchDirectories();
  }, []);

  const handleDirectoryClick = (directory: string) => {
    onDirectorySelect?.(directory);
  };

  const handleBackToAll = () => {
    onDirectorySelect?.(null);
  };

  if (loading) return <div className="py-4 text-gray-500">Loading directories...</div>;
  if (error) return <div className="py-4 text-red-500">Error: {error}</div>;
  if (!directories.length) return <div className="py-4 text-gray-500">No directories found.</div>;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mt-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">RAG Directories</h2>
        {selectedDirectory && (
          <button
            onClick={handleBackToAll}
            className="text-sm text-blue-600 hover:text-blue-800 underline"
          >
            ← Back to all directories
          </button>
        )}
      </div>

      {selectedDirectory ? (
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
    </div>
  );
}
