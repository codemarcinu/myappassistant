import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ReceiptUploader } from './ReceiptUploader';
import * as ApiServiceModule from '../../services/ApiService';

// Mock ApiService
jest.mock('../../services/ApiService', () => ({
  ApiService: {
    uploadReceipt: jest.fn(),
  },
}));

describe('ReceiptUploader Integration', () => {
  const mockOnUpload = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('obsługuje upload pliku paragonu', async () => {
    const file = new File(['test content'], 'receipt.jpg', { type: 'image/jpeg' });

    render(<ReceiptUploader onUpload={mockOnUpload} isUploading={false} />);

    // Wybierz plik
    const fileInput = screen.getByRole('button', { name: /wgraj/i });
    const input = screen.getByDisplayValue('');
    fireEvent.change(input, { target: { files: [file] } });

    // Kliknij przycisk upload
    fireEvent.click(fileInput);

    await waitFor(() => {
      expect(mockOnUpload).toHaveBeenCalledWith(file);
    });
  });

  it('wyświetla stan ładowania podczas upload', () => {
    render(<ReceiptUploader onUpload={mockOnUpload} isUploading={true} />);

    expect(screen.getByText(/przetwarzanie/i)).toBeInTheDocument();
  });
});
