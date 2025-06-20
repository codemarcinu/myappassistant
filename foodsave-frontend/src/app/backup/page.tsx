'use client';

import React from 'react';
import { BackupManager } from '@/components/backup/BackupManager';

export default function BackupPage() {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Backup System Management
        </h1>
        <p className="text-gray-600">
          Create, manage, and restore system backups following the 3-2-1 rule
        </p>
      </div>

      <BackupManager />
    </div>
  );
}
