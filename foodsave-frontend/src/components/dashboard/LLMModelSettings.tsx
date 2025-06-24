'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ApiService } from '@/services/ApiService';
import { LLMModel } from '@/types/api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';

export const LLMModelSettings: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState<string>('');
  const queryClient = useQueryClient();

  // Query for available models
  const {
    data: availableModels,
    isLoading: isLoadingModels,
    error: modelsError,
  } = useQuery({
    queryKey: ['llm-models'],
    queryFn: () => ApiService.getAvailableLLMModels(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Query for selected model
  const {
    data: currentModel,
    isLoading: isLoadingCurrent,
    error: currentError,
  } = useQuery({
    queryKey: ['llm-model-selected'],
    queryFn: () => ApiService.getSelectedLLMModel(),
    staleTime: 1 * 60 * 1000, // 1 minute
  });

  // Mutation for setting selected model
  const setModelMutation = useMutation({
    mutationFn: (modelName: string) => ApiService.setSelectedLLMModel(modelName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-model-selected'] });
      setSelectedModel('');
    },
    onError: (error) => {
      console.error('Failed to set model:', error);
    },
  });

  const handleModelChange = (modelName: string) => {
    setSelectedModel(modelName);
  };

  const handleSaveModel = () => {
    if (selectedModel) {
      setModelMutation.mutate(selectedModel);
    }
  };

  if (isLoadingModels || isLoadingCurrent) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center space-x-2">
          <Spinner />
          <span>Ładowanie ustawień modeli...</span>
        </div>
      </Card>
    );
  }

  if (modelsError || currentError) {
    return (
      <Card className="p-6">
        <div className="text-red-600">
          <h3 className="font-semibold mb-2">Błąd ładowania ustawień</h3>
          <p>Nie udało się załadować ustawień modeli LLM.</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-4">Ustawienia Modelu LLM</h2>

      {/* Current Model Display */}
      <div className="mb-6">
        <h3 className="text-lg font-medium mb-2">Aktualny model:</h3>
        <div className="bg-gray-100 p-3 rounded-lg">
          <span className="font-mono text-sm">
            {currentModel?.selected_model || 'Nie wybrano modelu'}
          </span>
        </div>
      </div>

      {/* Model Selection */}
      <div className="mb-6">
        <h3 className="text-lg font-medium mb-2">Wybierz model:</h3>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {availableModels?.map((model: LLMModel) => (
            <div
              key={model.name}
              role="button"
              tabIndex={0}
              className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                selectedModel === model.name
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => handleModelChange(model.name)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleModelChange(model.name);
                }
              }}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="font-medium text-sm">{model.name}</h4>
                  <p className="text-xs text-gray-600 mt-1">
                    Rozmiar: {model.size} | Zmodyfikowano: {model.modified_at}
                  </p>
                </div>
                {selectedModel === model.name && (
                  <div className="text-blue-500">✓</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSaveModel}
          disabled={!selectedModel || setModelMutation.isPending}
          className="min-w-[120px]"
        >
          {setModelMutation.isPending ? (
            <>
              <Spinner className="w-4 h-4 mr-2" />
              Zapisywanie...
            </>
          ) : (
            'Zapisz model'
          )}
        </Button>
      </div>

      {/* Error Display */}
      {setModelMutation.error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 text-sm">
            Błąd podczas zapisywania modelu: {setModelMutation.error.message}
          </p>
        </div>
      )}
    </Card>
  );
};
