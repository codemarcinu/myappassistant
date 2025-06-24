import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import qs from 'qs';
import { LLMModel, LLMModelSettings, LLMModelListResponse, LLMModelSelectedResponse } from '@/types/api';

const IS_SERVER = typeof window === 'undefined';

const API_BASE_URL = IS_SERVER
  ? process.env.INTERNAL_API_BASE_URL || 'http://backend:8000'
  : process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Retry configuration
const RETRY_CONFIG = {
  maxRetries: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
  retryableStatuses: [408, 429, 500, 502, 503, 504],
  retryableErrors: ['ECONNRESET', 'ENOTFOUND', 'ETIMEDOUT', 'ECONNABORTED']
};

// Error types for better error handling
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
    public retryable: boolean = false
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends ApiError {
  constructor(message: string = 'Network error. Please check your connection.') {
    super(message, undefined, 'NETWORK_ERROR', true);
    this.name = 'NetworkError';
  }
}

export class TimeoutError extends ApiError {
  constructor(message: string = 'Request timeout. Please try again.') {
    super(message, undefined, 'TIMEOUT_ERROR', true);
    this.name = 'TimeoutError';
  }
}

// Utility function for exponential backoff
function calculateBackoffDelay(attempt: number): number {
  const delay = Math.min(
    RETRY_CONFIG.baseDelay * Math.pow(2, attempt),
    RETRY_CONFIG.maxDelay
  );
  // Add jitter to prevent thundering herd
  return delay + Math.random() * 1000;
}

// Enhanced fetch with retry logic and AbortController
export async function fetchWithRetry<T>(
  url: string,
  options: RequestInit = {},
  retries: number = RETRY_CONFIG.maxRetries,
  abortSignal?: AbortSignal
): Promise<T> {
  const controller = new AbortController();

  // Combine abort signals
  if (abortSignal) {
    abortSignal.addEventListener('abort', () => controller.abort());
  }

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const isRetryable = RETRY_CONFIG.retryableStatuses.includes(response.status);

        if (isRetryable && attempt < retries) {
          const delay = calculateBackoffDelay(attempt);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }

        throw new ApiError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          'HTTP_ERROR',
          isRetryable
        );
      }

      return await response.json();
    } catch (error) {
      if (controller.signal.aborted) {
        throw new ApiError('Request was aborted', undefined, 'ABORTED', false);
      }

      if (error instanceof ApiError) {
        throw error;
      }

      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        if (attempt < retries) {
          const delay = calculateBackoffDelay(attempt);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
        throw new NetworkError();
      }

      // Handle timeout errors
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Request was aborted');
        throw new ApiError('Request was aborted', undefined, 'ABORTED', false);
      }

      throw new ApiError(
        error instanceof Error ? error.message : 'Unknown error occurred',
        undefined,
        'UNKNOWN_ERROR',
        false
      );
    }
  }

  throw new ApiError('Max retries exceeded', undefined, 'MAX_RETRIES_EXCEEDED', false);
}

class ApiServiceClass {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000, // 10 second timeout
      headers: {
        'Content-Type': 'application/json',
      },
      paramsSerializer: params => qs.stringify(params, { arrayFormat: 'repeat' }),
    });

    // Enhanced request interceptor with retry logic
    this.client.interceptors.request.use((config) => {
      // Add authentication token if available
      const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // Add request ID for tracking
      config.headers['X-Request-ID'] = crypto.randomUUID();

      return config;
    });

    // Enhanced response interceptor with better error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        // Handle retry logic
        if (error.response && RETRY_CONFIG.retryableStatuses.includes(error.response.status)) {
          if (!originalRequest._retry) {
            originalRequest._retry = true;
            originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;

            if (originalRequest._retryCount <= RETRY_CONFIG.maxRetries) {
              const delay = calculateBackoffDelay(originalRequest._retryCount - 1);
              await new Promise(resolve => setTimeout(resolve, delay));
              return this.client(originalRequest);
            }
          }
        }

        // Handle specific error cases
        if (error.response) {
          const { status, data } = error.response;

          switch (status) {
            case 401:
              if (typeof window !== 'undefined') {
                localStorage.removeItem('authToken');
                window.location.href = '/login';
              }
              throw new ApiError('Unauthorized access', status, 'UNAUTHORIZED', false);

            case 403:
              throw new ApiError('Access forbidden', status, 'FORBIDDEN', false);

            case 404:
              throw new ApiError('Resource not found', status, 'NOT_FOUND', false);

            case 429:
              throw new ApiError('Too many requests. Please try again later.', status, 'RATE_LIMITED', true);

            case 500:
            case 502:
            case 503:
            case 504:
              throw new ApiError('Server error. Please try again later.', status, 'SERVER_ERROR', true);

            default:
              const errorMessage = (data as any)?.detail || (data as any)?.error || `HTTP ${status} error`;
              throw new ApiError(errorMessage, status, 'HTTP_ERROR', false);
          }
        }

        // Handle network errors
        if (error.code === 'ECONNABORTED') {
          throw new TimeoutError();
        }

        if (error.code === 'ERR_NETWORK') {
          throw new NetworkError();
        }

        throw new ApiError(
          error.message || 'An unexpected error occurred',
          undefined,
          'UNKNOWN_ERROR',
          false
        );
      }
    );
  }

  // Generic request method with enhanced error handling
  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client(config);
      return response.data;
    } catch (error) {
      if (axios.isCancel(error)) {
        throw new ApiError('Request was cancelled', undefined, 'ABORTED', false);
      }
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError('Unknown error occurred', undefined, 'UNKNOWN_ERROR', false);
    }
  }

  // GET request with AbortController support
  public async get<T>(
    url: string,
    params?: Record<string, any>,
    signal?: AbortSignal
  ): Promise<T> {
    return this.request<T>({
      method: 'GET',
      url,
      params,
      signal
    });
  }

  // POST request with AbortController support
  public async post<T>(
    url: string,
    data?: any,
    signal?: AbortSignal
  ): Promise<T> {
    return this.request<T>({
      method: 'POST',
      url,
      data,
      signal
    });
  }

  // PUT request with AbortController support
  public async put<T>(
    url: string,
    data?: any,
    signal?: AbortSignal
  ): Promise<T> {
    return this.request<T>({
      method: 'PUT',
      url,
      data,
      signal
    });
  }

  // PATCH request with AbortController support
  public async patch<T>(
    url: string,
    data?: any,
    signal?: AbortSignal
  ): Promise<T> {
    return this.request<T>({
      method: 'PATCH',
      url,
      data,
      signal
    });
  }

  // DELETE request with AbortController support
  public async delete<T>(
    url: string,
    signal?: AbortSignal
  ): Promise<T> {
    return this.request<T>({
      method: 'DELETE',
      url,
      signal
    });
  }

  // Enhanced file upload with progress tracking and AbortController
  public async uploadFile<T>(
    url: string,
    file: File,
    onProgress?: (percentage: number) => void,
    signal?: AbortSignal
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<T>({
      method: 'POST',
      url,
      data: formData,
      signal,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentage);
        }
      },
    });
  }

  // Enhanced chat message sending with streaming support
  public async sendChatMessage(
    request: {
      message: string;
      session_id: string;
      agent_states?: Record<string, boolean>;
      usePerplexity?: boolean;
      useBielik?: boolean;
    },
    onChunk?: (chunk: any) => void,
    signal?: AbortSignal
  ): Promise<any> {
    try {
      const controller = new AbortController();
      if (signal) {
        signal.addEventListener('abort', () => controller.abort());
      }

      const response = await fetch(`${API_BASE_URL}/api/agents/agents/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task: request.message,
          session_id: request.session_id,
          agent_states: request.agent_states,
          usePerplexity: request.usePerplexity,
          useBielik: request.useBielik,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new ApiError(`HTTP error! status: ${response.status}`, response.status);
      }

      // Create a default response object
      let responseData: {
        response: string;
        data: any;
        success: boolean;
        session_id: string;
        error: string | null;
      } = {
        response: '',
        data: null,
        success: true,
        session_id: request.session_id,
        error: null
      };

      // Handle streaming response if onChunk is provided
      if (onChunk && response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        let hasError = false;
        let errorMessage = '';

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n').filter(line => line.trim());

            for (const line of lines) {
              try {
                const data = JSON.parse(line);
                onChunk(data);

                // Check if this is an error response
                if (data.error_type) {
                  hasError = true;
                  errorMessage = data.text || `Error: ${data.error_type}`;
                  responseData.error = errorMessage;
                  responseData.success = false;
                }

                // Accumulate text from chunks if available
                if (data.text) {
                  fullText += data.text;
                }

                // Update response data with any additional fields
                if (data.data) {
                  responseData.data = data.data;
                }
              } catch (e) {
                // Skip invalid JSON lines
                console.warn('Invalid JSON chunk:', line);
              }
            }
          }
        } finally {
          reader.releaseLock();
        }

        // Set the accumulated text as the response
        responseData.response = hasError ? errorMessage : (fullText || 'Przetworzono odpowiedź strumieniową.');
        return responseData;
      }

      // If not streaming, parse the whole response.
      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }

      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError('Request was cancelled', undefined, 'ABORTED', false);
      }

      console.error('Error sending chat message:', error);
      throw new ApiError(
        error instanceof Error ? error.message : 'Failed to send chat message',
        undefined,
        'CHAT_ERROR',
        true
      );
    }
  }

  // Specific API methods with enhanced error handling

  // Upload receipt with progress tracking
  public async uploadReceipt(
    file: File,
    onProgress?: (percentage: number) => void,
    signal?: AbortSignal
  ) {
    return this.uploadFile('/api/v1/receipts/upload', file, onProgress, signal);
  }

  // Get products with caching support
  public async getProducts(signal?: AbortSignal) {
    return this.get('/api/v1/pantry/products', undefined, signal);
  }

  // Get weather data for multiple locations
  public async getWeather(locations: string[], signal?: AbortSignal) {
    return this.get('/api/v2/weather/weather/', { locations }, signal);
  }

  public async analyzeReceipt(ocrText: string) {
    return this.post('/api/v2/receipts/analyze', { ocr_text: ocrText });
  }

  public async saveReceiptData(receiptData: any) {
    return this.post('/api/v2/receipts/save', receiptData);
  }

  // LLM Model Settings Methods
  public async getAvailableLLMModels(signal?: AbortSignal): Promise<LLMModel[]> {
    return this.get<LLMModel[]>('/api/settings/llm-models', undefined, signal);
  }

  public async getSelectedLLMModel(signal?: AbortSignal): Promise<LLMModelSelectedResponse> {
    return this.get<LLMModelSelectedResponse>('/api/settings/llm-model/selected', undefined, signal);
  }

  public async setSelectedLLMModel(modelName: string, signal?: AbortSignal): Promise<LLMModelSelectedResponse> {
    return this.post<LLMModelSelectedResponse>(`/api/settings/llm-model/selected?model_name=${encodeURIComponent(modelName)}`, undefined, signal);
  }
}

// Create a singleton instance
export const ApiService = new ApiServiceClass();

// Helper function for fetching weather data (used in Server Components)
export async function fetchWeatherData(location: string, signal?: AbortSignal) {
  const controller = new AbortController();
  if (signal) {
    signal.addEventListener('abort', () => controller.abort());
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v2/weather/weather/?locations=${encodeURIComponent(location)}`,
      { signal: controller.signal }
    );

    if (!response.ok) {
      throw new ApiError('Failed to fetch weather data', response.status);
    }

    return response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new NetworkError('Failed to fetch weather data');
  }
}
