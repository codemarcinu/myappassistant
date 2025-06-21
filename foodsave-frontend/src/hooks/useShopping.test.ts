import '@testing-library/jest-dom';
import { renderHook, waitFor } from '@testing-library/react';
import { useShopping } from './useShopping';
import * as ApiServiceModule from '../services/ApiService';

// Mock ApiService
jest.mock('../services/ApiService', () => ({
  ApiService: {
    getProducts: jest.fn(),
    uploadReceipt: jest.fn(),
    delete: jest.fn(),
    patch: jest.fn(),
  },
}));

describe('useShopping', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('pobiera produkty przy inicjalizacji', async () => {
    const mockProducts = [
      { id: '1', name: 'Test Product', quantity: 1, unit: 'szt' },
    ];
    (ApiServiceModule.ApiService.getProducts as jest.Mock).mockResolvedValue(mockProducts);

    const { result } = renderHook(() => useShopping());

    await waitFor(() => {
      expect(result.current.products).toEqual(mockProducts);
    });
  });

  it('obsługuje błędy podczas pobierania produktów', async () => {
    const errorMessage = 'Failed to fetch products';
    (ApiServiceModule.ApiService.getProducts as jest.Mock).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useShopping());

    await waitFor(() => {
      expect(result.current.error).toBe(errorMessage);
    });
  });
});
