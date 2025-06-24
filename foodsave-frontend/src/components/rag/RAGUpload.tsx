'use client';

import React, { useState, useCallback } from 'react';
import { Upload, File, Trash2, Search, Plus, AlertCircle, CheckCircle } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import RAGDirectoryList from './RAGDirectoryList';

interface RAGDocument {
  document_id: string;
  filename: string;
  description?: string;
  tags: string[];
  chunks_count: number;
  uploaded_at?: string;
  metadata?: {
    directory_path?: string | null;
  };
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
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [selectedDirectory, setSelectedDirectory] = useState<string | null>(null);
  const [showMoveModal, setShowMoveModal] = useState(false);
  const [movingDocument, setMovingDocument] = useState<RAGDocument | null>(null);
  const [targetDirectory, setTargetDirectory] = useState('');
  const [moving, setMoving] = useState(false);
  const [moveError, setMoveError] = useState<string | null>(null);
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());
  const [showBulkMoveModal, setShowBulkMoveModal] = useState(false);
  const [showBulkDeleteModal, setShowBulkDeleteModal] = useState(false);
  const [bulkTargetDirectory, setBulkTargetDirectory] = useState('');
  const [bulkOperating, setBulkOperating] = useState(false);
  const [bulkError, setBulkError] = useState<string | null>(null);

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
            metadata: {
              directory_path: selectedDirectory || undefined,
            },
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
  }, [description, tags, onUpload, selectedDirectory]);

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
    setShowSearchResults(false);
    try {
      const requestBody: any = {
        question: query,
        max_results: 10,
        include_sources: true,
      };

      if (selectedDirectory) {
        requestBody.directory_path = selectedDirectory;
      }

      const response = await fetch('/api/v2/rag/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const result = await response.json();
        setQueryResult(result.answer || 'No answer found');
        setSearchResults(result.sources || []);
        setShowSearchResults(true);
      } else {
        setQueryResult('Error querying RAG system');
        setSearchResults([]);
      }
    } catch (error) {
      setQueryResult('Error querying RAG system');
      setSearchResults([]);
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

  const handleMoveDocument = async (document: RAGDocument) => {
    setMovingDocument(document);
    setTargetDirectory('');
    setMoveError(null);
    setShowMoveModal(true);
  };

  const executeMove = async () => {
    if (!movingDocument || !targetDirectory.trim()) {
      setMoveError('Please select a target directory');
      return;
    }

    setMoving(true);
    setMoveError(null);

    try {
      const response = await fetch(`/api/v2/rag/documents/${movingDocument.document_id}/move`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_directory_path: targetDirectory.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to move document');
      }

      // Update the document in the local state
      setDocuments(prev => prev.map(doc =>
        doc.document_id === movingDocument.document_id
          ? { ...doc, metadata: { ...doc.metadata, directory_path: targetDirectory.trim() } }
          : doc
      ));

      setShowMoveModal(false);
      setMovingDocument(null);
      setTargetDirectory('');
    } catch (err: any) {
      setMoveError(err.message || 'Unknown error');
    } finally {
      setMoving(false);
    }
  };

  const handleDocumentSelect = (documentId: string, selected: boolean) => {
    setSelectedDocuments(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(documentId);
      } else {
        newSet.delete(documentId);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedDocuments.size === filteredDocuments.length) {
      setSelectedDocuments(new Set());
    } else {
      setSelectedDocuments(new Set(filteredDocuments.map(doc => doc.document_id)));
    }
  };

  const executeBulkMove = async () => {
    if (selectedDocuments.size === 0 || !bulkTargetDirectory.trim()) {
      setBulkError('Please select documents and enter a target directory');
      return;
    }

    setBulkOperating(true);
    setBulkError(null);

    try {
      const response = await fetch('/api/v2/rag/documents/bulk-move', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_ids: Array.from(selectedDocuments),
          new_directory_path: bulkTargetDirectory.trim()
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to bulk move documents');
      }

      // Refresh documents list
      await loadDocuments();
      setSelectedDocuments(new Set());
      setShowBulkMoveModal(false);
      setBulkTargetDirectory('');
    } catch (err: any) {
      setBulkError(err.message || 'Unknown error');
    } finally {
      setBulkOperating(false);
    }
  };

  const executeBulkDelete = async () => {
    if (selectedDocuments.size === 0) {
      setBulkError('Please select documents to delete');
      return;
    }

    setBulkOperating(true);
    setBulkError(null);

    try {
      const response = await fetch('/api/v2/rag/documents/bulk-delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_ids: Array.from(selectedDocuments)
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to bulk delete documents');
      }

      // Refresh documents list
      await loadDocuments();
      setSelectedDocuments(new Set());
      setShowBulkDeleteModal(false);
    } catch (err: any) {
      setBulkError(err.message || 'Unknown error');
    } finally {
      setBulkOperating(false);
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

  const filteredDocuments = selectedDirectory
    ? documents.filter(doc => doc.metadata?.directory_path === selectedDirectory)
    : documents;

  const handleDirectorySelect = (directory: string | null) => {
    setSelectedDirectory(directory);
  };

  React.useEffect(() => {
    loadDocuments();
  }, []);

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <RAGDirectoryList
        selectedDirectory={selectedDirectory}
        onDirectorySelect={handleDirectorySelect}
        onDirectoryCreated={loadDocuments}
        onDirectoryDeleted={loadDocuments}
        onDirectoryRenamed={loadDocuments}
      />
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">RAG Knowledge Base</h1>
        <p className="text-gray-600">
          {selectedDirectory
            ? `Documents in: ${selectedDirectory}`
            : 'Upload documents to enhance AI responses with your knowledge'
          }
        </p>
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
              <label htmlFor="description-input" className="block text-sm font-medium text-gray-700 mb-1">
                Description (optional)
              </label>
              <input
                id="description-input"
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Brief description of the document"
              />
            </div>
            <div>
              <label htmlFor="tags-input" className="block text-sm font-medium text-gray-700 mb-1">
                Tags (comma-separated)
              </label>
              <input
                id="tags-input"
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
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold flex items-center">
            <Search className="w-5 h-5 mr-2" />
            Query Knowledge Base
          </h2>
          {selectedDirectory && (
            <div className="text-sm text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
              📁 Searching in: {selectedDirectory}
            </div>
          )}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={
              selectedDirectory
                ? `Ask a question about documents in ${selectedDirectory}...`
                : "Ask a question about your documents..."
            }
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
          <div className="mt-4 space-y-4">
            <div className="p-4 bg-gray-50 rounded-md">
              <h3 className="font-medium text-gray-900 mb-2">Answer:</h3>
              <p className="text-gray-700">{queryResult}</p>
            </div>

            {showSearchResults && searchResults.length > 0 && (
              <div className="p-4 bg-blue-50 rounded-md">
                <h3 className="font-medium text-gray-900 mb-3">Sources ({searchResults.length}):</h3>
                <div className="space-y-3">
                  {searchResults.map((source, index) => (
                    <div key={index} className="p-3 bg-white rounded border">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-sm text-gray-900">
                          {source.filename || 'Unknown document'}
                        </span>
                        {source.metadata?.directory_path && (
                          <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
                            📁 {source.metadata.directory_path}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {source.content || source.text || 'No content available'}
                      </p>
                      {source.score && (
                        <div className="mt-2 text-xs text-gray-500">
                          Relevance: {Math.round(source.score * 100)}%
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold flex items-center">
            <File className="w-5 h-5 mr-2" />
            Uploaded Documents ({filteredDocuments.length})
          </h2>

          {filteredDocuments.length > 0 && (
            <div className="flex items-center space-x-2">
              <button
                onClick={handleSelectAll}
                className="text-sm text-blue-600 hover:text-blue-800 underline"
              >
                {selectedDocuments.size === filteredDocuments.length ? 'Deselect All' : 'Select All'}
              </button>

              {selectedDocuments.size > 0 && (
                <>
                  <span className="text-sm text-gray-500">
                    ({selectedDocuments.size} selected)
                  </span>
                  <button
                    onClick={() => setShowBulkMoveModal(true)}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                  >
                    Move Selected
                  </button>
                  <button
                    onClick={() => setShowBulkDeleteModal(true)}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
                  >
                    Delete Selected
                  </button>
                </>
              )}
            </div>
          )}
        </div>

        {filteredDocuments.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <File className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No documents uploaded yet</p>
            <p className="text-sm">Upload your first document to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.document_id}
                className={`flex items-center justify-between p-4 border rounded-lg transition-colors ${
                  selectedDocuments.has(doc.document_id)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={selectedDocuments.has(doc.document_id)}
                    onChange={(e) => handleDocumentSelect(doc.document_id, e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
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
                      {doc.metadata?.directory_path && (
                        <span className="text-blue-600">
                          📁 {doc.metadata.directory_path}
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
                    onClick={() => handleMoveDocument(doc)}
                    className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
                    title="Move document"
                  >
                    📁
                  </button>

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

      {/* Move Document Modal */}
      {showMoveModal && movingDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Move Document</h3>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                Moving: <strong>{movingDocument.filename}</strong>
              </p>
              <p className="text-sm text-gray-600 mb-4">
                From: <span className="font-mono">{movingDocument.metadata?.directory_path || 'default'}</span>
              </p>

              <label htmlFor="target-directory" className="block text-sm font-medium text-gray-700 mb-2">
                To Directory
              </label>
              <input
                id="target-directory"
                type="text"
                value={targetDirectory}
                onChange={(e) => setTargetDirectory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter directory name"
                onKeyPress={(e) => e.key === 'Enter' && executeMove()}
              />
            </div>

            {moveError && (
              <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">
                {moveError}
              </div>
            )}

            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowMoveModal(false);
                  setMovingDocument(null);
                  setTargetDirectory('');
                  setMoveError(null);
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
                disabled={moving}
              >
                Cancel
              </button>
              <button
                onClick={executeMove}
                disabled={moving || !targetDirectory.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {moving ? 'Moving...' : 'Move'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Move Modal */}
      {showBulkMoveModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Move Selected Documents</h3>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                Moving <strong>{selectedDocuments.size} documents</strong>
              </p>

              <label htmlFor="bulk-target-directory" className="block text-sm font-medium text-gray-700 mb-2">
                To Directory
              </label>
              <input
                id="bulk-target-directory"
                type="text"
                value={bulkTargetDirectory}
                onChange={(e) => setBulkTargetDirectory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter directory name"
                onKeyPress={(e) => e.key === 'Enter' && executeBulkMove()}
              />
            </div>

            {bulkError && (
              <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">
                {bulkError}
              </div>
            )}

            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowBulkMoveModal(false);
                  setBulkTargetDirectory('');
                  setBulkError(null);
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
                disabled={bulkOperating}
              >
                Cancel
              </button>
              <button
                onClick={executeBulkMove}
                disabled={bulkOperating || !bulkTargetDirectory.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {bulkOperating ? 'Moving...' : 'Move'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Delete Modal */}
      {showBulkDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-lg font-semibold mb-4 text-red-600">Delete Selected Documents</h3>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                Are you sure you want to delete <strong>{selectedDocuments.size} documents</strong>?
              </p>
              <p className="text-sm text-red-600">
                This action cannot be undone.
              </p>
            </div>

            {bulkError && (
              <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">
                {bulkError}
              </div>
            )}

            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowBulkDeleteModal(false);
                  setBulkError(null);
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
                disabled={bulkOperating}
              >
                Cancel
              </button>
              <button
                onClick={executeBulkDelete}
                disabled={bulkOperating}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {bulkOperating ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
