"use client";

import { useState, useCallback, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { PantryItem, Recipe } from '@/types/cooking';
import { Message } from '@/types/chat';
import { ApiService } from '@/services/ApiService';

interface PantryResponse {
  items: PantryItem[];
}

interface RecipesResponse {
  recipes: Recipe[];
}

interface ConversationResponse {
  response?: string;
  conversation_state?: Record<string, any>;
  data?: {
    pantry_updated?: boolean;
    [key: string]: any;
  };
}

export function useCooking() {
  // State declarations
  const [pantryItems, setPantryItems] = useState<PantryItem[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: uuidv4(),
      role: 'assistant',
      content: 'Witaj w asystencie kulinarnym! Mogę pomóc Ci znaleźć przepisy na podstawie produktów w Twojej spiżarni lub doradzić, co można ugotować.'
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationState, setConversationState] = useState<Record<string, any>>({});
  const [usePerplexity, setUsePerplexity] = useState(false);
  const [useBielik, setUseBielik] = useState(true); // Domyślnie używamy Bielika
  const togglePerplexity = () => setUsePerplexity(prev => !prev);
  const toggleModel = () => setUseBielik(prev => !prev);

  // Fetch pantry items
  const fetchPantryItems = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await ApiService.get<PantryItem[] | PantryResponse>('/api/v1/pantry/items');

      if (Array.isArray(data)) {
        setPantryItems(data);
      } else if (data && 'items' in data) {
        setPantryItems(data.items);
      } else {
        throw new Error('Unexpected data format from API');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch pantry items');
      console.error('Error fetching pantry items:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch recipes
  const fetchRecipes = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await ApiService.get<Recipe[] | RecipesResponse>('/api/v1/recipes');

      if (Array.isArray(data)) {
        setRecipes(data);
      } else if (data && 'recipes' in data) {
        setRecipes(data.recipes);
      } else {
        throw new Error('Unexpected data format from API');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch recipes');
      console.error('Error fetching recipes:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Add pantry item
  const addPantryItem = useCallback(async (item: Omit<PantryItem, 'id'>) => {
    try {
      setIsLoading(true);
      setError(null);
      const newItem = await ApiService.post<PantryItem>('/api/v1/pantry/items', item);
      setPantryItems(items => [...items, newItem]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add pantry item');
      console.error('Error adding pantry item:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Delete pantry item
  const deletePantryItem = useCallback(async (id: string) => {
    try {
      setIsLoading(true);
      setError(null);
      await ApiService.delete(`/api/v1/pantry/items/${id}`);
      setPantryItems(items => items.filter(item => item.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete pantry item');
      console.error('Error deleting pantry item:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Update pantry item
  const updatePantryItem = useCallback(async (id: string, updates: Partial<PantryItem>) => {
    try {
      setIsLoading(true);
      setError(null);
      const updatedItem = await ApiService.patch<PantryItem>(`/api/v1/pantry/items/${id}`, updates);
      setPantryItems(items =>
        items.map(item =>
          item.id === id ? { ...item, ...updatedItem } : item
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update pantry item');
      console.error('Error updating pantry item:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Send message to cooking assistant
  const sendCookingMessage = useCallback(async (content: string, usePerplexity?: boolean, useBielik?: boolean) => {
    try {
      setError(null);
      setIsLoading(true);

      // Add user message to the chat
      const userMessage: Message = {
        id: uuidv4(),
        role: 'user',
        content,
        usePerplexity: usePerplexity || false,
        useBielik: useBielik !== undefined ? useBielik : true
      };
      setMessages(prev => [...prev, userMessage]);

      // Send message to the API
      const response = await ApiService.sendChatMessage({
        message: content,
        session_id: uuidv4(), // Generate session ID
        agent_states: {
          weather: false,
          search: false,
          shopping: false,
          cooking: true,
        },
        usePerplexity: usePerplexity || false,
        useBielik: useBielik !== undefined ? useBielik : true,
      }, (chunk) => {
        // Handle streaming response
        console.log('Received chunk:', chunk);
      }) as ConversationResponse;

      // Update conversation state
      if (response.conversation_state) {
        setConversationState(response.conversation_state);
      }

      // Add assistant response to the chat
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: response.response || 'Przepraszam, wystąpił błąd w przetwarzaniu.',
        data: response.data,
        usePerplexity: usePerplexity || false,
        useBielik: useBielik !== undefined ? useBielik : true,
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Refresh pantry items if response indicates changes
      if (response.data?.pantry_updated) {
        fetchPantryItems();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [fetchPantryItems]);

  // Load initial data
  useEffect(() => {
    fetchPantryItems();
    fetchRecipes();
  }, [fetchPantryItems, fetchRecipes]);

  return {
    pantryItems,
    recipes,
    messages,
    isLoading,
    error,
    fetchPantryItems,
    fetchRecipes,
    addPantryItem,
    deletePantryItem,
    updatePantryItem,
    sendCookingMessage,
    usePerplexity,
    togglePerplexity,
    useBielik,
    toggleModel,
  };
}
