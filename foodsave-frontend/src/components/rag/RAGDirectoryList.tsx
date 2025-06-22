import React, { useEffect, useState } from 'react';

interface Directory {
  path: string;
  document_count: number;
}

export default function RAGDirectoryList() {
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

  if (loading) return <div className="py-4 text-gray-500">Loading directories...</div>;
  if (error) return <div className="py-4 text-red-500">Error: {error}</div>;
  if (!directories.length) return <div className="py-4 text-gray-500">No directories found.</div>;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mt-6">
      <h2 className="text-xl font-semibold mb-4">RAG Directories</h2>
      <ul className="divide-y divide-gray-200">
        {directories.map((dir) => (
          <li key={dir.path} className="py-2 flex justify-between items-center">
            <span className="font-mono text-gray-700">{dir.path}</span>
            <span className="text-sm text-gray-500">{dir.document_count} documents</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
