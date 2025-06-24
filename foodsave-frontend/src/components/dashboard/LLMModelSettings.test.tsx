import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LLMModelSettings } from './LLMModelSettings';
import { ApiService } from '@/services/ApiService';

// Mock ApiService
jest.mock('@/services/ApiService');
const mockApiService = ApiService as jest.Mocked<typeof ApiService>;

// Mock data
const mockModels = [
  {
    name: 'SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0',
    size: '5061216212',
    modified_at: '2025-06-24T07:25:02.498570882Z',
  },
  {
    name: 'SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M',
    size: '7907041623',
    modified_at: '2025-06-24T06:35:06.71652751Z',
  },
];

const mockSelectedModel = 'SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M';

// Test wrapper with QueryClient
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('LLMModelSettings', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    mockApiService.getAvailableLLMModels.mockResolvedValue(mockModels);
    mockApiService.getSelectedLLMModel.mockResolvedValue(mockSelectedModel);

    render(
      <TestWrapper>
        <LLMModelSettings />
      </TestWrapper>
    );

    expect(screen.getByText('Ładowanie ustawień modeli...')).toBeInTheDocument();
  });

  it('renders models list when data is loaded', async () => {
    mockApiService.getAvailableLLMModels.mockResolvedValue(mockModels);
    mockApiService.getSelectedLLMModel.mockResolvedValue(mockSelectedModel);

    render(
      <TestWrapper>
        <LLMModelSettings />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Ustawienia Modelu LLM')).toBeInTheDocument();
      expect(screen.getByText('SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0')).toBeInTheDocument();
      expect(screen.getByText('Aktualny model:')).toBeInTheDocument();
    });
  });

  it('displays current selected model', async () => {
    mockApiService.getAvailableLLMModels.mockResolvedValue(mockModels);
    mockApiService.getSelectedLLMModel.mockResolvedValue(mockSelectedModel);

    render(
      <TestWrapper>
        <LLMModelSettings />
      </TestWrapper>
    );

    await waitFor(() => {
      const currentModelSection = screen.getByText('Aktualny model:').closest('div');
      expect(currentModelSection).toHaveTextContent('SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M');
    });
  });

  it('shows error state when API fails', async () => {
    mockApiService.getAvailableLLMModels.mockRejectedValue(new Error('API Error'));
    mockApiService.getSelectedLLMModel.mockRejectedValue(new Error('API Error'));

    render(
      <TestWrapper>
        <LLMModelSettings />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Błąd ładowania ustawień')).toBeInTheDocument();
      expect(screen.getByText('Nie udało się załadować ustawień modeli LLM.')).toBeInTheDocument();
    });
  });
});
