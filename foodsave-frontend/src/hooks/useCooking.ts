import { useState, useCallback, useEffect } from 'react';
import { PantryItem, Recipe } from '@/types/cooking';
import { Message } from '@/types/chat';
import { ApiService } from '@/services/ApiService';

export function useCooking() {
  const [pantryItems, setPantryItems] = useState<PantryItem[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Witaj w asystencie kulinarnym! Mogę pomóc Ci znaleźć przepisy na podstawie produktów w Twojej spiżarni lub doradzić, co można ugotować.'
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationState, setConversationState] = useState({});

  // Fetch pantry items
  const fetchPantryItems = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await ApiService.get('/api/v1/pantry/items');

      if (Array.isArray(data)) {
        setPantryItems(data);
      } else if (data && typeof data === 'object' && Array.isArray(data.items)) {
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
      const data = await ApiService.get('/api/v1/recipes');

      if (Array.isArray(data)) {
        setRecipes(data);
      } else if (data && typeof data === 'object' && Array.isArray(data.recipes)) {
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
      const newItem = await ApiService.post('/api/v1/pantry/items', item);
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
      const updatedItem = await ApiService.patch(`/api/v1/pantry/items/${id}`, updates);
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
  const sendCookingMessage = useCallback(async (content: string) => {
    try {
      setError(null);
      setIsLoading(true);

      // Add user message to the chat
      const userMessage: Message = { role: 'user', content };
      setMessages(prev => [...prev, userMessage]);

      // Send message to the API
      const response = await ApiService.sendChatMessage({
        task: content,
        conversation_state: conversationState,
        agent_states: {
          weather: false,
          search: false,
          shopping: false,
          cooking: true,
        }
      });

      // Update conversation state
      if (response.conversation_state) {
        setConversationState(response.conversation_state);
      }

      // Add assistant response to the chat
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response || 'Przepraszam, wystąpił błąd w przetwarzaniu.',
        data: response.data
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
  }, [conversationState, fetchPantryItems]);

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
  };
}
