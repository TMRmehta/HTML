import { useState, useCallback, useEffect } from "react";
import { ChatApiService, ChatMessage, PatientChatResponse, ResearchChatResponse, ChatResponse } from "@/services/chatApi";
import { ChatHistoryApiService } from "@/services/chatHistoryApi";
import { useAuth } from "./useAuth";

export interface UseChatOptions {
  chatType: 'patient' | 'research';
  initialMessage?: string;
  chatId?: string; // Optional chat ID to continue an existing chat
}

export interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  chatId: string;
  isHistoryLoading: boolean;
}

export function useChat({ chatType, initialMessage, chatId: providedChatId }: UseChatOptions): UseChatReturn {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const initialMessages: ChatMessage[] = [];
    
    if (initialMessage) {
      initialMessages.push({
        id: ChatApiService.generateMessageId(),
        type: 'assistant',
        content: initialMessage,
        timestamp: new Date(),
      });
    }
    
    return initialMessages;
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatId, setChatId] = useState(() => providedChatId || ChatApiService.generateChatId());

  // Update chatId when providedChatId changes
  useEffect(() => {
    if (providedChatId) {
      console.log('Updating chatId from providedChatId:', providedChatId);
      setChatId(providedChatId);
    }
  }, [providedChatId]);

  // Load chat history when chatId is provided
  useEffect(() => {
    const loadChatHistory = async () => {
      if (!providedChatId || !user) return;
      
      setIsHistoryLoading(true);
      try {
        const response = await ChatHistoryApiService.getChatHistory(user.userid, providedChatId);
        if (response.chat_history && response.chat_history.length > 0) {
          const loadedMessages: ChatMessage[] = response.chat_history
            .map((msg: any) => ({
              id: ChatApiService.generateMessageId(), // Generate new IDs for frontend
              type: (msg.sender === 'Human' ? 'user' : 'assistant') as 'user' | 'assistant',
              content: msg.content,
              timestamp: new Date(msg.timestamp),
              sources: msg.sources,
              reasoning: msg.reasoning,
            }))
            .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime()); // Sort by timestamp (oldest first)
          
          console.log('Loaded messages in order:', loadedMessages.map(m => ({
            content: m.content.substring(0, 50) + '...',
            timestamp: m.timestamp.toISOString(),
            type: m.type
          })));
          
          setMessages(loadedMessages);
        }
      } catch (err) {
        console.error('Failed to load chat history:', err);
        setError('Failed to load chat history');
      } finally {
        setIsHistoryLoading(false);
      }
    };

    loadChatHistory();
  }, [providedChatId, user]);

  const addMessage = useCallback((message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: ChatApiService.generateMessageId(),
      timestamp: new Date(),
    };
    
    setMessages(prev => {
      const updatedMessages = [...prev, newMessage];
      // Sort by timestamp to maintain chronological order
      const sortedMessages = updatedMessages.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
      
      console.log('Added new message, total messages in order:', sortedMessages.map(m => ({
        content: m.content.substring(0, 30) + '...',
        timestamp: m.timestamp.toISOString(),
        type: m.type
      })));
      
      return sortedMessages;
    });
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading || !user) return;

    // Add user message immediately
    addMessage({
      type: 'user',
      content: content.trim(),
    });

    setIsLoading(true);
    setError(null);

    try {
      console.log(`Sending ${chatType} chat message:`, { 
        content: content.trim(), 
        userId: user.userid, 
        chatId,
        providedChatId,
        urlChatId: window.location.search
      });
      console.log(`Request started at: ${new Date().toISOString()}`);
      
      let response: PatientChatResponse | ResearchChatResponse | ChatResponse;

      if (chatType === 'patient') {
        response = await ChatApiService.sendPatientChat(
          content.trim(),
          user.userid,
          chatId
        );
      } else if (chatType === 'research') {
        response = await ChatApiService.sendResearchChat(
          content.trim(),
          user.userid,
          chatId
        );
      } else {
        response = await ChatApiService.sendGeneralChat(
          content.trim(),
          user.userid,
          chatId
        );
      }

      console.log('Received response:', response);
      console.log(`Request completed at: ${new Date().toISOString()}`);

      // Check if response is valid
      if (!response || !response.answer) {
        throw new Error('Received invalid response from server');
      }

      // Add assistant response
      addMessage({
        type: 'assistant',
        content: response.answer,
        sources: response.sources,
        reasoning: response.reasoning,
      });
      
      console.log('Message added successfully');
    } catch (err) {
      console.error('Error in sendMessage:', err);
      
      let errorMessage = 'An error occurred while sending the message';
      
      if (err instanceof Error) {
        errorMessage = err.message;
        
        // Provide more specific error messages
        if (err.message.includes('fetch')) {
          errorMessage = 'Network error. Please check your connection and try again.';
        } else if (err.message.includes('401') || err.message.includes('Unauthorized')) {
          errorMessage = 'Authentication failed. Please log in again.';
        } else if (err.message.includes('500')) {
          errorMessage = 'Server error. Please try again in a moment.';
        } else if (err.message.includes('timeout')) {
          errorMessage = 'Request timed out. Please try again.';
        }
      }
      
      setError(errorMessage);
      
      addMessage({
        type: 'assistant',
        content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
      });
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, user, chatType, chatId, addMessage]);

  const clearMessages = useCallback(() => {
    setMessages(initialMessage ? [{
      id: ChatApiService.generateMessageId(),
      type: 'assistant',
      content: initialMessage,
      timestamp: new Date(),
    }] : []);
    setError(null);
    // Generate a new chat ID when clearing messages for a new chat
    if (!providedChatId) {
      setChatId(ChatApiService.generateChatId());
    }
  }, [initialMessage, providedChatId]);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    addMessage,
    chatId,
    isHistoryLoading,
  };
}
