/**
 * API response types for the FoodSave application
 */

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface WeatherData {
  location: string;
  temperature: number;
  condition: string;
  highTemp: number;
  lowTemp: number;
  humidity?: number;
  windSpeed?: number;
  forecast?: WeatherForecast[];
}

export interface WeatherForecast {
  date: string;
  highTemp: number;
  lowTemp: number;
  condition: string;
}

export interface ConversationState {
  [key: string]: any;
}

export interface AgentExecuteRequest {
  task: string;
  conversation_state?: ConversationState;
  agent_states?: {
    weather?: boolean;
    search?: boolean;
    shopping?: boolean;
    cooking?: boolean;
  };
}

export interface AgentExecuteResponse {
  response: string;
  conversation_state?: ConversationState;
  data?: any;
}

export interface User {
  id: string;
  name: string;
  email: string;
  preferences?: {
    theme?: 'light' | 'dark';
    language?: string;
  };
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: number;
}
