import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Define log data structure
interface LogData {
  timestamp: string;
  level: string;
  message: string;
  data?: string;
  app: string;
}

// Ensure log directory exists
const LOG_DIR = '/tmp/logs';
try {
  fs.mkdirSync(LOG_DIR, { recursive: true });
} catch (error) {
  console.error('Failed to create log directory:', error);
}

// Log file path
const LOG_FILE = path.join(LOG_DIR, 'frontend.log');

/**
 * API endpoint to receive logs from frontend and write them to file
 */
export async function POST(request: Request) {
  try {
    const logData = await request.json() as LogData;

    // Validate log data
    if (!logData.timestamp || !logData.level || !logData.message) {
      return NextResponse.json({ error: 'Invalid log data' }, { status: 400 });
    }

    // Format log entry
    const logEntry = `${logData.timestamp} - ${logData.app} - ${logData.level.toUpperCase()} - ${logData.message}${logData.data ? ` - ${logData.data}` : ''}\n`;

    // Write to log file
    fs.appendFileSync(LOG_FILE, logEntry);

    // Return success
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error writing log:', error);
    return NextResponse.json({ error: 'Failed to write log' }, { status: 500 });
  }
}
