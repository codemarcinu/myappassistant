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

  // Load backups and stats on component mount
  useEffect(() => {
    loadBackups();
    loadStats();
  }, []);

  const loadBackups = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await ApiService.get('/api/v2/backup/list') as any;
      setBackups(response.data.backups);
    } catch (error) {
      console.error('Error loading backups:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const response = await ApiService.get('/api/v2/backup/stats') as any;
      setStats(response.data);
    } catch (error) {
      console.error('Error loading backup stats:', error);
    }
  }, []);

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
            <Button onClick={loadStats} disabled={isLoading}>
              {isLoading ? 'Loading...' : 'Refresh'}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {stats ? (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold mb-2">Overview</h4>
                <p>Total Backups: {stats.total_backups}</p>
                <p>Total Size: {stats.total_size_mb.toFixed(2)} MB</p>
                <p>Backup Dir Size: {stats.backup_dir_size_mb.toFixed(2)} MB</p>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Retention Policy</h4>
                <p>Daily: {stats.retention_policy.daily_retention_days} days</p>
                <p>Weekly: {stats.retention_policy.weekly_retention_weeks} weeks</p>
                <p>Monthly: {stats.retention_policy.monthly_retention_months} months</p>
              </div>
            </div>
          ) : (
            <p>Click "Refresh" to load statistics</p>
          )}
        </CardContent>
      </Card>

      {/* Create Backup Card */}
      <Card>
        <CardHeader>
          <CardTitle>Create New Backup</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Backup Name (optional)</label>
            <Input
              value={backupName}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setBackupName(e.target.value)}
              placeholder="e.g., pre_deployment_backup"
            />
          </div>

          <Button
            onClick={createBackup}
            disabled={isLoading}
            className="w-full"
          >
            {isLoading ? 'Creating Backup...' : 'Create Full Backup'}
          </Button>

          {lastBackupResult && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
              <h4 className="font-semibold text-green-800 mb-2">Last Backup Result:</h4>
              <p className="text-sm text-green-700">Name: {lastBackupResult.backup_name}</p>
              <p className="text-sm text-green-700">Size: {formatFileSize(lastBackupResult.total_size)}</p>
              <p className="text-sm text-green-700">Status: {lastBackupResult.verification.overall_status}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Backup List Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex justify-between items-center">
            Available Backups
            <Button onClick={loadBackups} disabled={isLoading}>
              {isLoading ? 'Loading...' : 'Refresh'}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {backups.length > 0 ? (
            <div className="space-y-4">
              {backups.map((backup) => (
                <div key={backup.name} className="p-4 border rounded">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h4 className="font-semibold">{backup.name}</h4>
                      <p className="text-sm text-gray-600">
                        Created: {formatDate(backup.created_at)}
                      </p>
                      <p className="text-sm text-gray-600">
                        Size: {formatFileSize(backup.total_size)}
                      </p>
                      <p className="text-sm text-gray-600">
                        Components: {backup.components.join(', ')}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => verifyBackup(backup.name)}
                        disabled={isLoading}
                      >
                        Verify
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p>No backups found. Create your first backup above.</p>
          )}
        </CardContent>
      </Card>

      {/* Restore Backup Card */}
      <Card>
        <CardHeader>
          <CardTitle>Restore Backup</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Select Backup</label>
            <select
              value={selectedBackup}
              onChange={(e) => setSelectedBackup(e.target.value)}
              className="w-full p-2 border rounded"
            >
              <option value="">Choose a backup...</option>
              {backups.map((backup) => (
                <option key={backup.name} value={backup.name}>
                  {backup.name} ({formatDate(backup.created_at)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Components to Restore (optional, comma-separated)
            </label>
            <Input
              value={restoreComponents}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRestoreComponents(e.target.value)}
              placeholder="e.g., database,files,configuration"
            />
            <p className="text-xs text-gray-500 mt-1">
              Leave empty to restore all components
            </p>
          </div>

          <Button
            onClick={restoreBackup}
            disabled={!selectedBackup || isLoading}
            className="w-full bg-red-600 hover:bg-red-700"
          >
            {isLoading ? 'Restoring...' : 'Restore Backup'}
          </Button>
        </CardContent>
      </Card>

      {/* Maintenance Card */}
      <Card>
        <CardHeader>
          <CardTitle>Maintenance</CardTitle>
        </CardHeader>
        <CardContent>
          <Button
            onClick={cleanupOldBackups}
            disabled={isLoading}
            className="w-full bg-orange-600 hover:bg-orange-700"
          >
            {isLoading ? 'Cleaning...' : 'Cleanup Old Backups'}
          </Button>
          <p className="text-xs text-gray-500 mt-2">
            This will delete backups older than the retention policy
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
