// Ensure we use localhost instead of 0.0.0.0 for CORS compatibility
const getApiBase = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && envUrl.includes('0.0.0.0')) {
    return envUrl.replace('0.0.0.0', 'localhost');
  }
  return envUrl || "http://localhost:8000";
};

const API_BASE = getApiBase();
console.log('API_BASE URL:', API_BASE);
console.log('VITE_API_BASE_URL env var:', import.meta.env.VITE_API_BASE_URL);

export interface ChatAPIRequest {
  question: string;
  user_id: string;
  chat_id: string;
}

export interface PatientChatResponse {
  answer: string;
  reasoning?: any[];
  sources?: any[];
  return_status?: "success" | "failed" | "fallback";
}

export interface ResearchChatResponse {
  answer: string;
  reasoning?: any[];
  sources?: any[];
  return_status?: "success" | "failed" | "fallback";
}

export interface ChatResponse {
  answer: string;
  reasoning?: any[];
  sources?: any[];
  tools?: any[];
  type?: any;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: any[];
  reasoning?: any[];
}

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("access_token");
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

async function makeRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  retries: number = 1,
  timeout: number = 120000
): Promise<T> {
  // Use shorter timeout for OPTIONS requests
  const requestTimeout = options.method === 'OPTIONS' ? 5000 : timeout;
  let lastError: Error | null = null;
  
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      console.log(`Making request to: ${API_BASE}${endpoint} (attempt ${attempt}/${retries})`);
      console.log('Request options:', options);
      
      // Create abort controller for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        console.log(`Request timeout after ${requestTimeout}ms`);
        controller.abort();
      }, requestTimeout);
      
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        signal: controller.signal,
        headers: {
          ...getAuthHeaders(),
          ...options.headers,
        },
      });
      
      clearTimeout(timeoutId);

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || `HTTP error! status: ${response.status}`;
        console.error(`Request failed (attempt ${attempt}):`, errorMessage);
        
        // Don't retry for client errors (4xx), only for server errors (5xx) and network issues
        if (response.status >= 400 && response.status < 500) {
          throw new Error(errorMessage);
        }
        
        lastError = new Error(errorMessage);
        
        // Wait before retrying (exponential backoff)
        if (attempt < retries) {
          const delay = Math.pow(2, attempt - 1) * 1000; // 1s, 2s, 4s
          console.log(`Retrying in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
      }

      const data = await response.json();
      console.log('Response data:', data);
      return data;
      
    } catch (error) {
      console.error(`Request failed (attempt ${attempt}):`, error);
      lastError = error instanceof Error ? error : new Error('Unknown error');
      
      // Handle different types of errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        // Network error - retry
        if (attempt < retries) {
          const delay = Math.pow(2, attempt - 1) * 1000;
          console.log(`Retrying in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
      } else if (error instanceof DOMException && error.name === 'AbortError') {
        // Timeout error - retry
        lastError = new Error('Request timed out');
        if (attempt < retries) {
          const delay = Math.pow(2, attempt - 1) * 1000;
          console.log(`Retrying after timeout in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
      } else {
        // Other errors - don't retry
        throw error;
      }
    }
  }
  
  throw lastError || new Error('Request failed after all retries');
}

export async function sendGeneralChat(
  question: string,
  userId: string,
  chatId: string
): Promise<ChatResponse> {
  return makeRequest<ChatResponse>("/api/v1/agents/generic", {
    method: "POST",
    body: JSON.stringify({
      question,
      user_id: userId,
      chat_id: chatId,
    }),
  });
}

export async function sendPatientChat(
  question: string,
  userId: string,
  chatId: string
): Promise<PatientChatResponse> {
  return makeRequest<PatientChatResponse>("/api/v1/agents/patient", {
    method: "POST",
    body: JSON.stringify({
      question,
      user_id: userId,
      chat_id: chatId,
    }),
  }, 1, 360000); // 6 minutes timeout for patient chat, no retries
}

export async function sendResearchChat(
  question: string,
  userId: string,
  chatId: string
): Promise<ResearchChatResponse> {
  return makeRequest<ResearchChatResponse>("/api/v1/agents/research", {
    method: "POST",
    body: JSON.stringify({
      question,
      user_id: userId,
      chat_id: chatId,
    }),
  }, 1, 360000); // 6 minutes timeout for research chat, no retries
}

export function generateChatId(): string {
  return `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export const ChatApiService = {
  sendGeneralChat,
  sendPatientChat,
  sendResearchChat,
  generateChatId,
  generateMessageId,
};
