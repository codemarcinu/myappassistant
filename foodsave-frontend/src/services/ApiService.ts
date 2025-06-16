import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:8000';

class ApiServiceClass {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for authentication
    this.client.interceptors.request.use((config) => {
      // Add authentication token if available
      const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // Handle common errors (e.g., 401 Unauthorized, 500 Server Error)
        if (error.response) {
          const { status } = error.response;

          if (status === 401) {
            // Handle unauthorized error
            if (typeof window !== 'undefined') {
              localStorage.removeItem('authToken');
              window.location.href = '/login';
            }
          }

          // Return error message from response if available
          const errorMessage = error.response.data?.detail ||
                              error.response.data?.error ||
                              'An error occurred';
          return Promise.reject(new Error(errorMessage));
        }

        // Handle network errors
        return Promise.reject(new Error('Network error. Please check your connection.'));
      }
    );
  }

  // Generic request method
  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client(config);
      return response.data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Unknown error occurred');
    }
  }

  // GET request
  public async get<T>(url: string, params?: Record<string, any>): Promise<T> {
    return this.request<T>({ method: 'GET', url, params });
  }

  // POST request
  public async post<T>(url: string, data?: any): Promise<T> {
    return this.request<T>({ method: 'POST', url, data });
  }

  // PUT request
  public async put<T>(url: string, data?: any): Promise<T> {
    return this.request<T>({ method: 'PUT', url, data });
  }

  // PATCH request
  public async patch<T>(url: string, data?: any): Promise<T> {
    return this.request<T>({ method: 'PATCH', url, data });
  }

  // DELETE request
  public async delete<T>(url: string): Promise<T> {
    return this.request<T>({ method: 'DELETE', url });
  }

  // File upload with progress tracking
  public async uploadFile<T>(
    url: string,
    file: File,
    onProgress?: (percentage: number) => void
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<T>({
      method: 'POST',
      url,
      data: formData,
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

  // Specific API methods

  // Send chat message
  public async sendChatMessage(payload: {
    task: string;
    conversation_state?: Record<string, any>;
    agent_states?: Record<string, boolean>;
  }) {
    return this.post('/api/v1/agents/execute', payload);
  }

  // Upload receipt
  public async uploadReceipt(file: File) {
    return this.uploadFile('/api/v1/receipts/upload', file);
  }

  // Get products
  public async getProducts() {
    return this.get('/api/v1/pantry/products');
  }

  // Get weather data
  public async getWeatherData(location: string) {
    return this.get('/api/v1/weather', { location });
  }
}

// Create a singleton instance
export const ApiService = new ApiServiceClass();

// Helper function for fetching weather data (used in Server Components)
export async function fetchWeatherData(location: string) {
  const response = await fetch(`${API_BASE_URL}/api/v1/weather?location=${encodeURIComponent(location)}`);
  if (!response.ok) {
    throw new Error('Failed to fetch weather data');
  }
  return response.json();
}
