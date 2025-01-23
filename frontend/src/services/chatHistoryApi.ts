// Ensure we use localhost instead of 0.0.0.0 for CORS compatibility
const getApiBase = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && envUrl.includes('0.0.0.0')) {
    return envUrl.replace('0.0.0.0', 'localhost');
  }
  return envUrl || "http://localhost:8000";
};

const API_BASE = getApiBase();

export interface ChatHistory {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
}

export interface ChatLookup {
  user_id: string;
  chat_id: string;
}

export interface ChatIDsRequest {
  user_id: string;
}

export interface ChatIDsResponse {
  chat_ids: string[] | null;
}

export interface ChatsMetadataResponse {
  chats_metadata: any[] | null;
}

export interface ChatHistoryResponse {
  chat_history: any[] | null;
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
  options: RequestInit = {}
): Promise<T> {
  try {
    console.log(`Making request to: ${API_BASE}${endpoint}`);
    console.log('Request options:', options);
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        ...getAuthHeaders(),
        ...options.headers,
      },
    });

    console.log('Response status:', response.status);
    console.log('Response ok:', response.ok);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Error response:', errorData);
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Response data:', data);
    return data;
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}

export async function getChatIds(userId: string): Promise<ChatIDsResponse> {
  return makeRequest<ChatIDsResponse>("/api/v1/chats/get_ids", {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
    }),
  });
}

export async function getChatsMetadata(userId: string): Promise<ChatsMetadataResponse> {
  return makeRequest<ChatsMetadataResponse>("/api/v1/chats/get_metadata", {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
    }),
  });
}

export async function getChatHistory(userId: string, chatId: string): Promise<ChatHistoryResponse> {
  return makeRequest<ChatHistoryResponse>("/api/v1/chats/fetch_history", {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
      chat_id: chatId,
    }),
  });
}

export async function checkChatExists(userId: string, chatId: string): Promise<boolean> {
  const response = await makeRequest<{ result: boolean }>("/api/v1/chats/exists", {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
      chat_id: chatId,
    }),
  });
  return response.result;
}

export async function getChatTitle(userId: string, chatId: string): Promise<string> {
  const response = await makeRequest<{ result: string }>("/api/v1/chats/get_title", {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
      chat_id: chatId,
    }),
  });
  return response.result;
}

export const ChatHistoryApiService = {
  getChatIds,
  getChatsMetadata,
  getChatHistory,
  checkChatExists,
  getChatTitle,
};

