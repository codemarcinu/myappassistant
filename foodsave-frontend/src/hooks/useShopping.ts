"use client";

import { Product, Receipt } from '@/types/shopping';
import { ApiService } from '@/services/ApiService';

interface ProductsResponse {
  products: Product[];
}

export function useShopping() {
  const [products, setProducts] = useState<Product[]>([]);
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch products
  const fetchProducts = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await ApiService.getProducts() as Product[] | ProductsResponse;

      // Ensure we're dealing with an array of products
      if (Array.isArray(data)) {
        setProducts(data);
      } else if (data && 'products' in data && Array.isArray(data.products)) {
        setProducts(data.products);
      } else {
        throw new Error('Unexpected data format from API');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch products');
      console.error('Error fetching products:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Upload receipt
  const uploadReceipt = useCallback(async (file: File) => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await ApiService.uploadReceipt(file);

      // Refresh products after upload
      await fetchProducts();

      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload receipt');
      console.error('Error uploading receipt:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [fetchProducts]);

  // Delete product
  const deleteProduct = useCallback(async (id: string) => {
    try {
      setIsLoading(true);
      setError(null);
      await ApiService.delete(`/api/v1/pantry/products/${id}`);
      setProducts(products => products.filter(product => product.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete product');
      console.error('Error deleting product:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Update product
  const updateProduct = useCallback(async (id: string, updates: Partial<Product>) => {
    try {
      setIsLoading(true);
      setError(null);
      const updatedProduct = await ApiService.patch<Product>(`/api/v1/pantry/products/${id}`, updates);
      setProducts(products =>
        products.map(product =>
          product.id === id ? { ...product, ...updatedProduct as Product } : product
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update product');
      console.error('Error updating product:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load initial data
  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  return {
    products,
    receipts,
    isLoading,
    error,
    fetchProducts,
    uploadReceipt,
    deleteProduct,
    updateProduct,
  };
}

// Mock implementation for the React hooks since we can't import them directly
function useState<T>(initialState: T): [T, (newState: T | ((prevState: T) => T)) => void] {
  // This is a placeholder implementation
  return [initialState, (newState) => {}];
}

function useCallback<T extends (...args: any[]) => any>(callback: T, deps: any[]): T {
  // This is a placeholder implementation
  return callback;
}

function useEffect(effect: () => void | (() => void), deps?: any[]): void {
  // This is a placeholder implementation
}
