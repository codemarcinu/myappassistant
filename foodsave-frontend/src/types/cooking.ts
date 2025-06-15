/**
 * Type definitions for the Cooking (Pantry) module
 */

export interface PantryItem {
  id: string;
  name: string;
  quantity?: number;
  unit?: string;
  category?: string;
  unified_category: string;
  expiry_date?: string;
  purchase_date?: string;
  notes?: string;
}

export interface Ingredient {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  optional?: boolean;
  notes?: string;
}

export interface Recipe {
  id: string;
  name: string;
  description: string;
  ingredients: Ingredient[];
  instructions: string[];
  prepTime: number; // minutes
  cookTime: number; // minutes
  servings: number;
  difficulty: 'easy' | 'medium' | 'hard';
  cuisine?: string;
  tags?: string[];
  image_url?: string;
}

export interface CookingState {
  pantryItems: PantryItem[];
  recipes: Recipe[];
  isLoading: boolean;
  error: string | null;
}

export interface PantryListProps {
  items: PantryItem[];
  isLoading?: boolean;
  onAddItem?: (item: Omit<PantryItem, 'id'>) => Promise<void>;
  onDeleteItem?: (id: string) => Promise<void>;
  onUpdateItem?: (id: string, updates: Partial<PantryItem>) => Promise<void>;
}

export interface RecipeCardProps {
  recipe: Recipe;
  onSelect: (recipe: Recipe) => void;
}

export interface CookingChatProps {
  pantryItems: PantryItem[];
  onSendMessage: (message: string) => Promise<void>;
  messages: import('./chat').Message[];
  isLoading?: boolean;
}

export interface CookingContextType {
  state: CookingState;
  fetchPantryItems: () => Promise<void>;
  fetchRecipes: () => Promise<void>;
  addPantryItem: (item: Omit<PantryItem, 'id'>) => Promise<void>;
  deletePantryItem: (id: string) => Promise<void>;
  updatePantryItem: (id: string, updates: Partial<PantryItem>) => Promise<void>;
}
