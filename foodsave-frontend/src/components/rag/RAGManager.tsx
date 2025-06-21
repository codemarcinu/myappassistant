"use client";

import React, { useState, useCallback, ChangeEvent, KeyboardEvent } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ApiService } from '@/services/ApiService';

interface RAGStats {
  vector_store: {
    total_chunks: number;
    total_documents: number;
  };
  processor: {
    chunk_size: number;
    chunk_overlap: number;
    use_local_embeddings: boolean;
    use_pinecone: boolean;
  };
}

interface SearchResult {
  text: string;
  similarity: number;
  metadata: any;
  source_id: string;
}

interface SyncResult {
  success: boolean;
  total_chunks: number;
  results: {
    receipts?: { processed_trips: number; total_chunks: number };
    pantry?: { processed_products: number; total_chunks: number };
    conversations?: { processed_conversations: number; total_chunks: number };
  };
}

export function RAGManager() {
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState<RAGStats | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState('');
  const [uploadTags, setUploadTags] = useState('');

  // Load RAG statistics
  const loadStats = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await ApiService.get('/api/v2/rag/stats') as any;
      setStats(response.data);
    } catch (error) {
      console.error('Error loading RAG stats:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Search documents
  const searchDocuments = useCallback(async () => {
    if (!searchQuery.trim()) return;

    try {
      setIsLoading(true);
      const response = await ApiService.get('/api/v2/rag/search', {
        params: {
          query: searchQuery,
          k: 10,
          min_similarity: 0.65
        }
      }) as any;
      setSearchResults(response.data.results);
    } catch (error) {
      console.error('Error searching documents:', error);
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery]);

  // Sync database to RAG
  const syncDatabase = useCallback(async (syncType: string) => {
    try {
      setIsLoading(true);
      const response = await ApiService.post('/api/v2/rag/sync-database', { sync_type: syncType }) as any;
      setSyncResult(response);
    } catch (error) {
      console.error('Error syncing database:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Upload document
  const uploadDocument = useCallback(async () => {
    if (!selectedFile) return;

    try {
      setIsLoading(true);
      const formData = new FormData();
      formData.append('file', selectedFile);

      if (uploadCategory) {
        formData.append('category', uploadCategory);
      }
      if (uploadTags) {
        formData.append('tags', uploadTags);
      }

      const response = await ApiService.uploadFile('/api/v2/rag/upload', selectedFile) as any;

      // Reset form
      setSelectedFile(null);
      setUploadCategory('');
      setUploadTags('');

      // Reload stats
      await loadStats();

      alert('Document uploaded successfully!');
    } catch (error) {
      console.error('Error uploading document:', error);
      alert('Error uploading document');
    } finally {
      setIsLoading(false);
    }
  }, [selectedFile, uploadCategory, uploadTags, loadStats]);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Statistics Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex justify-between items-center">
            RAG System Statistics
            <Button onClick={loadStats} disabled={isLoading}>
              {isLoading ? 'Loading...' : 'Refresh'}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {stats ? (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold mb-2">Vector Store</h4>
                <p>Total Chunks: {stats.vector_store.total_chunks}</p>
                <p>Total Documents: {stats.vector_store.total_documents}</p>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Processor</h4>
                <p>Chunk Size: {stats.processor.chunk_size}</p>
                <p>Chunk Overlap: {stats.processor.chunk_overlap}</p>
                <p>Local Embeddings: {stats.processor.use_local_embeddings ? 'Yes' : 'No'}</p>
                <p>Pinecone: {stats.processor.use_pinecone ? 'Yes' : 'No'}</p>
              </div>
            </div>
          ) : (
            <p>Click "Refresh" to load statistics</p>
          )}
        </CardContent>
      </Card>

      {/* Document Upload Card */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Document</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Select File</label>
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md,.html,.doc"
              onChange={handleFileChange}
              className="w-full p-2 border rounded"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Category (optional)</label>
              <Input
                value={uploadCategory}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setUploadCategory(e.target.value)}
                placeholder="e.g., recipes, guides"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Tags (optional)</label>
              <Input
                value={uploadTags}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setUploadTags(e.target.value)}
                placeholder="e.g., cooking, healthy, quick"
              />
            </div>
          </div>

          <Button
            onClick={uploadDocument}
            disabled={!selectedFile || isLoading}
            className="w-full"
          >
            {isLoading ? 'Uploading...' : 'Upload Document'}
          </Button>
        </CardContent>
      </Card>

      {/* Database Sync Card */}
      <Card>
        <CardHeader>
          <CardTitle>Database Synchronization</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <Button
              onClick={() => syncDatabase('receipts')}
              disabled={isLoading}
            >
              Sync Receipts
            </Button>
            <Button
              onClick={() => syncDatabase('pantry')}
              disabled={isLoading}
            >
              Sync Pantry
            </Button>
            <Button
              onClick={() => syncDatabase('conversations')}
              disabled={isLoading}
            >
              Sync Conversations
            </Button>
            <Button
              onClick={() => syncDatabase('all')}
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Sync All
            </Button>
          </div>

          {syncResult && (
            <div className="mt-4 p-4 bg-gray-50 rounded">
              <h4 className="font-semibold mb-2">Sync Results:</h4>
              <p>Total Chunks: {syncResult.total_chunks}</p>
              {syncResult.results.receipts && (
                <p>Receipts: {syncResult.results.receipts.processed_trips} trips, {syncResult.results.receipts.total_chunks} chunks</p>
              )}
              {syncResult.results.pantry && (
                <p>Pantry: {syncResult.results.pantry.processed_products} products, {syncResult.results.pantry.total_chunks} chunks</p>
              )}
              {syncResult.results.conversations && (
                <p>Conversations: {syncResult.results.conversations.processed_conversations} conversations, {syncResult.results.conversations.total_chunks} chunks</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Search Card */}
      <Card>
        <CardHeader>
          <CardTitle>Search Documents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-4">
            <Input
              value={searchQuery}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
              placeholder="Enter search query..."
              onKeyPress={(e: KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && searchDocuments()}
            />
            <Button onClick={searchDocuments} disabled={!searchQuery.trim() || isLoading}>
              {isLoading ? 'Searching...' : 'Search'}
            </Button>
          </div>

          {searchResults.length > 0 && (
            <div className="space-y-4">
              <h4 className="font-semibold">Search Results ({searchResults.length})</h4>
              {searchResults.map((result, index) => (
                <div key={index} className="p-4 border rounded">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm text-gray-600">
                      Similarity: {(result.similarity * 100).toFixed(1)}%
                    </span>
                    <span className="text-sm text-gray-600">
                      Source: {result.source_id}
                    </span>
                  </div>
                  <p className="text-sm">{result.text}</p>
                  {result.metadata && (
                    <div className="mt-2 text-xs text-gray-500">
                      <p>Type: {result.metadata.type}</p>
                      {result.metadata.category && <p>Category: {result.metadata.category}</p>}
                      {result.metadata.date && <p>Date: {result.metadata.date}</p>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
