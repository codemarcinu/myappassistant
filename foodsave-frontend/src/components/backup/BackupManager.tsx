"use client";

import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ApiService } from '@/services/ApiService';

interface Backup {
  name: string;
  created_at: string;
  total_size: number;
  components: string[];
  status: string;
  manifest_file: string;
}

interface BackupStats {
  total_backups: number;
  total_size_mb: number;
  backup_dir_size_mb: number;
  retention_policy: {
    daily_retention_days: number;
    weekly_retention_weeks: number;
    monthly_retention_months: number;
  };
  verification_enabled: boolean;
  checksum_verification: boolean;
}

interface BackupResult {
  backup_name: string;
  timestamp: string;
  components: {
    database?: { status: string; size: number };
    files?: { status: string; size: number };
    configuration?: { status: string; size: number };
    vector_store?: { status: string; size: number };
  };
  total_size: number;
  verification: {
    overall_status: string;
    components: Record<string, any>;
  };
}

export function BackupManager() {
  const [isLoading, setIsLoading] = useState(false);
  const [backups, setBackups] = useState<Backup[]>([]);
  const [stats, setStats] = useState<BackupStats | null>(null);
  const [backupName, setBackupName] = useState('');
  const [lastBackupResult, setLastBackupResult] = useState<BackupResult | null>(null);
  const [selectedBackup, setSelectedBackup] = useState<string>('');
  const [restoreComponents, setRestoreComponents] = useState<string>('');

  const loadBackups = useCallback(async (signal?: AbortSignal) => {
    try {
      setIsLoading(true);
      const response = await ApiService.get('/api/v2/backup/list', undefined, signal) as any;
      setBackups(response.data.backups);
    } catch (error) {
      // Don't log error if request was aborted
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      console.error('Error loading backups:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadStats = useCallback(async (signal?: AbortSignal) => {
    try {
      const response = await ApiService.get('/api/v2/backup/stats', undefined, signal) as any;
      setStats(response.data);
    } catch (error) {
      // Don't log error if request was aborted
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      console.error('Error loading backup stats:', error);
    }
  }, []);

  // Load backups and stats on component mount with proper cleanup
  useEffect(() => {
    const controller = new AbortController();

    loadBackups(controller.signal);
    loadStats(controller.signal);

    // Cleanup function to abort requests when component unmounts
    return () => {
      controller.abort();
    };
  }, [loadBackups, loadStats]);

  const createBackup = useCallback(async () => {
    try {
      setIsLoading(true);
      const params = new URLSearchParams();
      if (backupName) {
        params.append('backup_name', backupName);
      }
      params.append('verify', 'true');

      const response = await ApiService.post(`/api/v2/backup/create?${params}`) as any;
      setLastBackupResult(response.data);
      setBackupName('');

      // Reload backups and stats
      await loadBackups();
      await loadStats();

      alert('Backup created successfully!');
    } catch (error) {
      console.error('Error creating backup:', error);
      alert('Error creating backup');
    } finally {
      setIsLoading(false);
    }
  }, [backupName, loadBackups, loadStats]);

  const restoreBackup = useCallback(async () => {
    if (!selectedBackup) {
      alert('Please select a backup to restore');
      return;
    }

    if (!confirm(`Are you sure you want to restore backup "${selectedBackup}"? This will overwrite current data.`)) {
      return;
    }

    try {
      setIsLoading(true);
      const params = new URLSearchParams();
      if (restoreComponents) {
        params.append('components', restoreComponents);
      }

      const response = await ApiService.post(`/api/v2/backup/restore/${selectedBackup}?${params}`) as any;

      alert(`Backup restored successfully! Status: ${response.data.status}`);
      setSelectedBackup('');
      setRestoreComponents('');
    } catch (error) {
      console.error('Error restoring backup:', error);
      alert('Error restoring backup');
    } finally {
      setIsLoading(false);
    }
  }, [selectedBackup, restoreComponents]);

  const verifyBackup = useCallback(async (backupName: string) => {
    try {
      setIsLoading(true);
      const response = await ApiService.post(`/api/v2/backup/verify/${backupName}`) as any;

      const status = response.data.overall_status;
      alert(`Backup verification completed. Status: ${status}`);
    } catch (error) {
      console.error('Error verifying backup:', error);
      alert('Error verifying backup');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const cleanupOldBackups = useCallback(async () => {
    if (!confirm('Are you sure you want to cleanup old backups? This action cannot be undone.')) {
      return;
    }

    try {
      setIsLoading(true);
      await ApiService.delete('/api/v2/backup/cleanup');

      alert('Old backups cleaned up successfully!');
      await loadBackups();
      await loadStats();
    } catch (error) {
      console.error('Error cleaning up backups:', error);
      alert('Error cleaning up backups');
    } finally {
      setIsLoading(false);
    }
  }, [loadBackups, loadStats]);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-6">
      {/* Statistics Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex justify-between items-center">
            Backup System Statistics
            <Button onClick={() => loadStats()} disabled={isLoading}>
              {isLoading ? 'Loading...' : 'Refresh'}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {stats ? (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Total Backups</p>
                <p className="text-2xl font-bold">{stats.total_backups}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Size</p>
                <p className="text-2xl font-bold">{stats.total_size_mb.toFixed(2)} MB</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Backup Directory Size</p>
                <p className="text-2xl font-bold">{stats.backup_dir_size_mb.toFixed(2)} MB</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Verification</p>
                <p className="text-2xl font-bold">{stats.verification_enabled ? 'Enabled' : 'Disabled'}</p>
              </div>
            </div>
          ) : (
            <p>Loading statistics...</p>
          )}
        </CardContent>
      </Card>

      {/* Create Backup Card */}
      <Card>
        <CardHeader>
          <CardTitle>Create New Backup</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Input
              type="text"
              placeholder="Backup name (optional)"
              value={backupName}
              onChange={(e) => setBackupName(e.target.value)}
              className="flex-grow"
            />
            <Button onClick={createBackup} disabled={isLoading}>
              {isLoading ? 'Creating...' : 'Create Backup'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Backup List Card */}
      <Card>
        <CardHeader>
          <CardTitle>Backup History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {backups.map((backup) => (
              <div key={backup.name} className="border rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold">{backup.name}</h3>
                    <p className="text-sm text-gray-500">
                      Created: {formatDate(backup.created_at)}
                    </p>
                    <p className="text-sm text-gray-500">
                      Size: {formatFileSize(backup.total_size)}
                    </p>
                    <p className="text-sm text-gray-500">
                      Status: {backup.status}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => verifyBackup(backup.name)}
                      disabled={isLoading}
                    >
                      Verify
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedBackup(backup.name)}
                    >
                      Restore
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            {backups.length === 0 && (
              <p className="text-center text-gray-500">No backups found</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Restore Backup Card */}
      {selectedBackup && (
        <Card>
          <CardHeader>
            <CardTitle>Restore Backup: {selectedBackup}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Input
                type="text"
                placeholder="Components to restore (comma-separated, leave empty for all)"
                value={restoreComponents}
                onChange={(e) => setRestoreComponents(e.target.value)}
              />
              <div className="flex gap-2">
                <Button onClick={restoreBackup} disabled={isLoading}>
                  {isLoading ? 'Restoring...' : 'Restore'}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setSelectedBackup('')}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Cleanup Card */}
      <Card>
        <CardHeader>
          <CardTitle>Maintenance</CardTitle>
        </CardHeader>
        <CardContent>
          <Button
            variant="destructive"
            onClick={cleanupOldBackups}
            disabled={isLoading}
          >
            {isLoading ? 'Cleaning...' : 'Cleanup Old Backups'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
