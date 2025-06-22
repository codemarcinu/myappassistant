import React, { useState } from 'react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Product } from '@/types/shopping';

interface ReceiptDataTableProps {
  products: Product[];
  onSave: (products: Product[]) => void;
  onCancel: () => void;
}

export function ReceiptDataTable({ products, onSave, onCancel }: ReceiptDataTableProps) {
  const [editedProducts, setEditedProducts] = useState<Product[]>(
    products.map(product => ({
      ...product,
      expiry_date: product.expiry_date || ''
    }))
  );

  const handleProductChange = (index: number, field: keyof Product, value: any) => {
    const updatedProducts = [...editedProducts];
    updatedProducts[index] = {
      ...updatedProducts[index],
      [field]: value
    };
    setEditedProducts(updatedProducts);
  };

  const handleSave = () => {
    onSave(editedProducts);
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b">
        <h3 className="text-lg font-semibold">Dane z paragonu</h3>
        <p className="text-sm text-gray-500">Możesz edytować dane przed zapisaniem</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Produkt</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ilość</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Jednostka</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cena</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kategoria</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data ważności</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {editedProducts.map((product, index) => (
              <tr key={index}>
                <td className="px-4 py-2">
                  <Input
                    value={product.name}
                    onChange={e => handleProductChange(index, 'name', e.target.value)}
                    className="w-full"
                  />
                </td>
                <td className="px-4 py-2">
                  <Input
                    type="number"
                    value={product.quantity}
                    onChange={e => handleProductChange(index, 'quantity', parseFloat(e.target.value))}
                    className="w-20"
                  />
                </td>
                <td className="px-4 py-2">
                  <Input
                    value={product.unit || ''}
                    onChange={e => handleProductChange(index, 'unit', e.target.value)}
                    className="w-16"
                    placeholder="szt."
                  />
                </td>
                <td className="px-4 py-2">
                  <Input
                    type="number"
                    value={product.price || 0}
                    onChange={e => handleProductChange(index, 'price', parseFloat(e.target.value))}
                    className="w-24"
                    step="0.01"
                  />
                </td>
                <td className="px-4 py-2">
                  <Input
                    value={product.category || ''}
                    onChange={e => handleProductChange(index, 'category', e.target.value)}
                    className="w-full"
                  />
                </td>
                <td className="px-4 py-2">
                  <Input
                    type="date"
                    value={product.expiry_date || ''}
                    onChange={e => handleProductChange(index, 'expiry_date', e.target.value)}
                    className="w-full"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="p-4 border-t flex justify-end space-x-3">
        <Button variant="secondary" onClick={onCancel}>
          Anuluj
        </Button>
        <Button onClick={handleSave}>
          Zapisz produkty
        </Button>
      </div>
    </div>
  );
}
