"use client";

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
      role: 'assistant',
      content: 'Witaj w asystencie kulinarnym! Mogę pomóc Ci znaleźć przepisy na podstawie produktów w Twojej spiżarni lub doradzić, co można ugotować.'
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationState, setConversationState] = useState<Record<string, any>>({});

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
      }) as ConversationResponse;

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
