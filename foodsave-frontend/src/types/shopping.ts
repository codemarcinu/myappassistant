/**
 * Type definitions for the Shopping module
 */

export interface Product {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  price: number;
  category?: string;
  unified_category?: string;
  expiry_date?: string;
  purchase_date?: string;
  store?: string;
  receipt_id?: string;
}

export interface Receipt {
  id: string;
  date: string;
  store: string;
  total: number;
  items: Product[];
  raw_text?: string;
  image_url?: string;
}

export interface ShoppingState {
  products: Product[];
  receipts: Receipt[];
  isLoading: boolean;
  error: string | null;
}

export interface ReceiptUploaderProps {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
}

export interface ProductTableProps {
  products: Product[];
  isLoading?: boolean;
  onDeleteProduct?: (id: string) => Promise<void>;
  onEditProduct?: (id: string, updates: Partial<Product>) => Promise<void>;
}

export interface ShoppingContextType {
  state: ShoppingState;
  fetchProducts: () => Promise<void>;
  uploadReceipt: (file: File) => Promise<void>;
  deleteProduct: (id: string) => Promise<void>;
  updateProduct: (id: string, updates: Partial<Product>) => Promise<void>;
}
