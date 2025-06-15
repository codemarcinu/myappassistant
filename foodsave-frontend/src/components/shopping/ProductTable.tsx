import React from 'react';
import { Product, ProductTableProps } from '@/types/shopping';
import { Button } from '../ui/Button';

export const ProductTable: React.FC<ProductTableProps> = ({
  products,
  isLoading = false,
  onDeleteProduct,
  onEditProduct
}) => {
  if (isLoading) {
    return <div className="h-40 animate-pulse bg-gray-100 rounded" />;
  }

  if (products.length === 0) {
    return <div className="text-center p-4">Brak produktów do wyświetlenia</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Nazwa
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Ilość
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Cena
            </th>
            {onDeleteProduct && (
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Akcje
              </th>
            )}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {products.map((product) => (
            <tr key={product.id}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm font-medium text-gray-900">{product.name}</div>
                {product.category && (
                  <div className="text-xs text-gray-500">{product.unified_category || product.category}</div>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900">{product.quantity} {product.unit}</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900">{product.price} zł</div>
              </td>
              {onDeleteProduct && (
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  {onEditProduct && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onEditProduct(product.id, {})}
                      className="mr-2"
                    >
                      Edytuj
                    </Button>
                  )}
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => onDeleteProduct(product.id)}
                  >
                    Usuń
                  </Button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
