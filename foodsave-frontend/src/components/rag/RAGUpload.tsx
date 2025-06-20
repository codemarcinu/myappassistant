'use client';

import React, { useState, useCallback } from 'react';
import { Upload, File, Trash2, Search, Plus, AlertCircle, CheckCircle } from 'lucide-react';
import { useDropzone } from 'react-dropzone';

interface RAGDocument {
  document_id: string;
  filename: string;
  description?: string;
  tags: string[];
  chunks_count: number;
  uploaded_at?: string;
}

interface RAGUploadProps {
  onUpload?: (document: RAGDocument) => void;
}

export default function RAGUpload({ onUpload }: RAGUploadProps) {
  const [documents, setDocuments] = useState<RAGDocument[]>([]);
  const [uploading, setUploading] = useState(false);
  const [query, setQuery] = useState('');
  const [queryResult, setQueryResult] = useState<string>('');
  const [querying, setQuerying] = useState(false);
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploading(true);

    try {
      for (const file of acceptedFiles) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('description', description);
        formData.append('tags', tags);

        const response = await fetch('/api/v2/rag/upload', {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const result = await response.json();
          const newDocument: RAGDocument = {
            document_id: result.document_id,
            filename: result.filename,
            description: description,
            tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag),
            chunks_count: 0,
            uploaded_at: new Date().toISOString(),
          };

          setDocuments(prev => [...prev, newDocument]);
          onUpload?.(newDocument);
        } else {
          console.error('Upload failed:', await response.text());
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
      setDescription('');
      setTags('');
    }
  }, [description, tags, onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/markdown': ['.md'],
      'application/rtf': ['.rtf'],
    },
    multiple: true,
  });

  const handleQuery = async () => {
    if (!query.trim()) return;

    setQuerying(true);
    try {
      const response = await fetch('/api/v2/rag/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: query,
          max_results: 5,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setQueryResult(result.answer);
      } else {
        setQueryResult('Error querying RAG system');
      }
    } catch (error) {
      setQueryResult('Error querying RAG system');
    } finally {
      setQuerying(false);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    try {
      const response = await fetch(`/api/v2/rag/documents/${documentId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setDocuments(prev => prev.filter(doc => doc.document_id !== documentId));
      }
    } catch (error) {
      console.error('Delete error:', error);
    }
  };

  const loadDocuments = async () => {
    try {
      const response = await fetch('/api/v2/rag/documents');
      if (response.ok) {
        const docs = await response.json();
        setDocuments(docs);
      }
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  };

  React.useEffect(() => {
    loadDocuments();
  }, []);

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">RAG Knowledge Base</h1>
        <p className="text-gray-600">Upload documents to enhance AI responses with your knowledge</p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Upload className="w-5 h-5 mr-2" />
          Upload Documents
        </h2>

        <div className="space-y-4">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            {isDragActive ? (
              <p className="text-blue-600">Drop the files here...</p>
            ) : (
              <div>
                <p className="text-gray-600 mb-2">
                  Drag & drop files here, or click to select
                </p>
                <p className="text-sm text-gray-500">
                  Supported: PDF, TXT, DOCX, MD, RTF
                </p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (optional)
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Brief description of the document"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="tag1, tag2, tag3"
              />
            </div>
          </div>

          {uploading && (
            <div className="flex items-center justify-center text-blue-600">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-2"></div>
              Uploading documents...
            </div>
          )}
        </div>
      </div>

      {/* Query Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Search className="w-5 h-5 mr-2" />
          Query Knowledge Base
        </h2>

        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Ask a question about your documents..."
            onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
          />
          <button
            onClick={handleQuery}
            disabled={querying || !query.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {querying ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            ) : (
              <Search className="w-4 h-4 mr-2" />
            )}
            Query
          </button>
        </div>

        {queryResult && (
          <div className="mt-4 p-4 bg-gray-50 rounded-md">
            <h3 className="font-medium text-gray-900 mb-2">Answer:</h3>
            <p className="text-gray-700">{queryResult}</p>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <File className="w-5 h-5 mr-2" />
          Uploaded Documents ({documents.length})
        </h2>

        {documents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <File className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No documents uploaded yet</p>
            <p className="text-sm">Upload your first document to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.document_id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                <div className="flex items-center space-x-3">
                  <File className="w-5 h-5 text-blue-600" />
                  <div>
                    <h3 className="font-medium text-gray-900">{doc.filename}</h3>
                    {doc.description && (
                      <p className="text-sm text-gray-600">{doc.description}</p>
                    )}
                    <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                      <span>{doc.chunks_count} chunks</span>
                      {doc.uploaded_at && (
                        <span>
                          {new Date(doc.uploaded_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {doc.tags.length > 0 && (
                    <div className="flex space-x-1">
                      {doc.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                      {doc.tags.length > 3 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                          +{doc.tags.length - 3}
                        </span>
                      )}
                    </div>
                  )}

                  <button
                    onClick={() => handleDeleteDocument(doc.document_id)}
                    className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                    title="Delete document"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
