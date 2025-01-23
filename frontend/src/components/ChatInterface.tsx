import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Send, 
  Plus, 
  MoreVertical, 
  Trash2, 
  Copy, 
  ThumbsUp, 
  ThumbsDown,
  MessageSquare,
  Clock,
  User,
  Bot,
  Wifi,
  WifiOff,
  AlertCircle,
  PanelLeftClose,
  PanelLeftOpen,
  Home,
  Search,
  Settings,
  ChevronDown,
  ChevronRight
} from "lucide-react";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { useChat } from "@/hooks/useChat";
import { useAuth } from "@/hooks/useAuth";
import { ChatHistoryApiService } from "@/services/chatHistoryApi";
import { ChatApiService } from "@/services/chatApi";
import { cn } from "@/lib/utils";
import { formatDateTime, groupMessagesByDate, formatShortDate, sortChatsByDate, formatTimeOnly, areMessagesCloseInTime, groupChatsForDisplay } from "@/lib/dateUtils";

export interface ChatHistory {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
}

export interface ChatInterfaceProps {
  chatType: 'patient' | 'research';
  className?: string;
  showSidebar?: boolean;
  initialMessage?: string;
  chatId?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  chatType,
  className,
  showSidebar = true,
  initialMessage,
  chatId: providedChatId
}) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [message, setMessage] = useState("");
  const [chatHistories, setChatHistories] = useState<ChatHistory[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'online' | 'offline' | 'checking'>('online');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedDateGroups, setExpandedDateGroups] = useState<Set<string>>(new Set(['Today', 'Yesterday']));
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const apiBase = import.meta.env.VITE_API_BASE_URL;

  const { messages, isLoading, error, sendMessage, clearMessages, chatId, isHistoryLoading } = useChat({
    chatType,
    initialMessage: initialMessage || (chatType === 'patient' 
      ? "Hello! I'm here to help answer your health-related questions. Please remember that I provide general information only and cannot replace professional medical advice. How can I assist you today?"
      : "Hello! I'm your research assistant. I can help you find and analyze cancer research papers, clinical trials, and treatment protocols. What would you like to research today?"
    ),
    chatId: providedChatId || selectedChatId || undefined
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Monitor connection status
  useEffect(() => {
    const checkConnection = async () => {
      setConnectionStatus('checking');
      try {
        const response = await fetch(`${apiBase}/health`, { 
          method: 'GET',
          signal: AbortSignal.timeout(5000)
        });
        if (response.ok) {
          setConnectionStatus('online');
        } else {
          setConnectionStatus('offline');
        }
      } catch (error) {
        setConnectionStatus('offline');
      }
    };

    checkConnection();

    const handleOnline = () => setConnectionStatus('online');
    const handleOffline = () => setConnectionStatus('offline');

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    const interval = setInterval(checkConnection, 120000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, []);

  // Load chat histories on mount
  useEffect(() => {
    const loadChatHistories = async () => {
      if (!user) {
        console.log('No user found, skipping chat history load');
        return;
      }
      
      setIsLoadingHistory(true);
      try {
        const response = await ChatHistoryApiService.getChatsMetadata(user.userid);
        
        if (response.chats_metadata) {
          const histories: ChatHistory[] = response.chats_metadata.map((chat: any) => ({
            id: chat.id,
            title: chat.title || 'Untitled Chat',
            lastMessage: chat.last_message || '',
            timestamp: new Date(chat.updated_at || chat.created_at),
            messageCount: chat.message_count || 0
          }));
          
          const sortedHistories = sortChatsByDate(histories);
          setChatHistories(sortedHistories);
        } else {
          setChatHistories([]);
        }
      } catch (err) {
        console.error('Failed to load chat histories:', err);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    loadChatHistories();
  }, [user]);

  const handleSendMessage = async () => {
    if (!message.trim() || isLoading) return;
    
    const userMessage = message;
    setMessage("");
    
    try {
      await sendMessage(userMessage);
      if (user) {
        const response = await ChatHistoryApiService.getChatsMetadata(user.userid);
        if (response.chats_metadata) {
          const histories: ChatHistory[] = response.chats_metadata.map((chat: any) => ({
            id: chat.id,
            title: chat.title || 'Untitled Chat',
            lastMessage: chat.last_message || '',
            timestamp: new Date(chat.updated_at || chat.created_at),
            messageCount: chat.message_count || 0
          }));
          const sortedHistories = sortChatsByDate(histories);
          setChatHistories(sortedHistories);
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleNewChat = async () => {
    clearMessages();
    const tempChatId = ChatApiService.generateChatId();
    setSelectedChatId(tempChatId);
    if (providedChatId) {
      navigate(`/chat/${chatType}`);
    }
    if (user) {
      try {
        const response = await ChatHistoryApiService.getChatsMetadata(user.userid);
        if (response.chats_metadata) {
          const histories: ChatHistory[] = response.chats_metadata.map((chat: any) => ({
            id: chat.id,
            title: chat.title || 'Untitled Chat',
            lastMessage: chat.last_message || '',
            timestamp: new Date(chat.updated_at || chat.created_at),
            messageCount: chat.message_count || 0
          }));
          const sortedHistories = sortChatsByDate(histories);
          setChatHistories(sortedHistories);
        }
      } catch (error) {
        console.error('Failed to refresh chat history:', error);
      }
    }
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  };

  const handleSelectChat = (chatId: string) => {
    setSelectedChatId(chatId);
    navigate(`/chat/${chatType}?chatId=${chatId}`);
    inputRef.current?.focus();
  };

  const handleHomeNavigation = () => {
    const homeRoute = chatType === 'patient' ? '/patients' : '/research';
    navigate(homeRoute);
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const toggleDateGroup = (date: string) => {
    const newExpanded = new Set(expandedDateGroups);
    if (newExpanded.has(date)) {
      newExpanded.delete(date);
    } else {
      newExpanded.add(date);
    }
    setExpandedDateGroups(newExpanded);
  };

  const filteredChatHistories = chatHistories.filter(chat => 
    chat.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    chat.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className={cn("flex h-screen bg-background overflow-hidden", className)}>
      {/* Sidebar - Hidden on mobile, overlay on tablet, fixed on desktop */}
      {showSidebar && (
        <div className={cn(
          "border-r bg-muted/30 flex flex-col transition-all duration-300 ease-in-out",
          "absolute md:relative z-40 h-full",
          isSidebarCollapsed ? "w-0 md:w-16 -translate-x-full md:translate-x-0" : "w-64 sm:w-80 translate-x-0",
          !isSidebarCollapsed && "shadow-lg md:shadow-none"
        )}>
          {/* Sidebar Header */}
          <div className="p-3 sm:p-4 border-b">
            <div className="flex items-center justify-between mb-4">
              {!isSidebarCollapsed && (
                <h2 className="text-lg font-semibold">
                  {chatType === 'patient' ? 'Patient Chats' : 'Research Chats'}
                </h2>
              )}
              <div className="flex items-center gap-2">
                <Button
                  onClick={handleNewChat}
                  size="sm"
                  variant="ghost"
                  className="h-9 w-9 p-0 hover:bg-accent/50 transition-colors"
                  title="New Chat"
                >
                  <Plus className="h-4 w-4" />
                </Button>
                <Button
                  onClick={toggleSidebar}
                  size="sm"
                  variant="ghost"
                  className="h-9 w-9 p-0 hover:bg-accent/50 transition-colors"
                  title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
                >
                  {isSidebarCollapsed ? (
                    <PanelLeftOpen className="h-4 w-4" />
                  ) : (
                    <PanelLeftClose className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
            
            {/* Navigation */}
            {!isSidebarCollapsed && (
              <div className="space-y-2 mb-4">
                <Button
                  onClick={handleHomeNavigation}
                  variant="ghost"
                  className="w-full justify-start h-9 px-3 hover:bg-accent/50 transition-colors"
                >
                  <Home className="h-4 w-4 mr-3" />
                  Home
                </Button>
              </div>
            )}
            
            {/* Search/Filter */}
            {!isSidebarCollapsed && (
              <div className="relative">
                <Input
                  placeholder="Search chats..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 h-9 bg-background/50 border-muted-foreground/20 focus:border-primary/50 transition-colors"
                />
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              </div>
            )}
            
            {/* Collapsed state navigation */}
            {isSidebarCollapsed && (
              <div className="space-y-2">
                <Button
                  onClick={handleHomeNavigation}
                  variant="ghost"
                  size="sm"
                  className="w-full h-9 p-0 hover:bg-accent/50 transition-colors"
                  title="Home"
                >
                  <Home className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>

          {/* Chat History */}
          <ScrollArea className="flex-1">
            <div className={cn("p-2 space-y-1", isSidebarCollapsed && "px-2")}>
              {isLoadingHistory ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner size="sm" />
                </div>
              ) : filteredChatHistories.length === 0 ? (
                <div className={cn(
                  "text-center py-8 text-muted-foreground",
                  isSidebarCollapsed && "px-0"
                )}>
                  <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  {!isSidebarCollapsed && (
                    <>
                      <p className="text-sm">No chat history yet</p>
                      <p className="text-xs">Start a new conversation</p>
                    </>
                  )}
                </div>
              ) : (
                groupChatsForDisplay(filteredChatHistories).map((dateGroup) => (
                  <div key={dateGroup.date} className="space-y-2">
                    {/* Date Header - Only show when not collapsed */}
                    {!isSidebarCollapsed && (
                      <Button
                        variant="ghost"
                        className="w-full justify-between h-8 px-3 py-1 hover:bg-accent/50 transition-colors"
                        onClick={() => toggleDateGroup(dateGroup.date)}
                      >
                        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                          {dateGroup.displayDate}
                        </h3>
                        {expandedDateGroups.has(dateGroup.date) ? (
                          <ChevronDown className="h-3 w-3" />
                        ) : (
                          <ChevronRight className="h-3 w-3" />
                        )}
                      </Button>
                    )}
                    
                    {/* Chats for this date */}
                    {(isSidebarCollapsed || expandedDateGroups.has(dateGroup.date)) && (
                      <div className="space-y-1">
                        {dateGroup.chats.map((chat) => {
                          const isSelected = selectedChatId === chat.id || providedChatId === chat.id;
                          return (
                            <div
                              key={chat.id}
                              className={cn(
                                "cursor-pointer transition-all duration-200 rounded-lg hover:bg-accent/50 group",
                                isSelected && "bg-accent/30 shadow-sm ring-1 ring-primary/20",
                                isSidebarCollapsed ? "p-2" : "p-3"
                              )}
                              onClick={() => handleSelectChat(chat.id)}
                              title={isSidebarCollapsed ? chat.title : undefined}
                            >
                              {isSidebarCollapsed ? (
                                <div className="flex items-center justify-center">
                                  <MessageSquare className={cn(
                                    "h-4 w-4 transition-colors",
                                    isSelected ? "text-primary" : "text-muted-foreground"
                                  )} />
                                </div>
                              ) : (
                                <div className="flex items-start justify-between">
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                      {isSelected && (
                                        <div className="w-2 h-2 bg-primary rounded-full flex-shrink-0 animate-pulse" />
                                      )}
                                      <h3 className={cn(
                                        "font-medium text-sm truncate transition-colors",
                                        isSelected && "text-primary font-semibold"
                                      )}>
                                        {chat.title}
                                      </h3>
                                    </div>
                                    <p className="text-xs text-muted-foreground truncate mt-1 leading-relaxed">
                                      {chat.lastMessage}
                                    </p>
                                    <div className="flex items-center gap-2 mt-2">
                                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                        <Clock className="h-3 w-3" />
                                        {formatTimeOnly(chat.timestamp)}
                                      </div>
                                    </div>
                                  </div>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-accent"
                                  >
                                    <MoreVertical className="h-3 w-3" />
                                  </Button>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
          
          {/* Sidebar Footer */}
          {!isSidebarCollapsed && (
            <div className="p-4 border-t bg-muted/20">
              <Button
                variant="ghost"
                className="w-full justify-start h-9 px-3 hover:bg-accent/50 transition-colors"
              >
                <Settings className="h-4 w-4 mr-3" />
                Settings
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="border-b p-3 sm:p-4 bg-background/95 backdrop-blur-sm">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 sm:gap-4 min-w-0 flex-1">
              {/* Sidebar toggle button when collapsed or hidden */}
              {(showSidebar && isSidebarCollapsed) || !showSidebar ? (
                <Button
                  onClick={showSidebar ? toggleSidebar : undefined}
                  variant="ghost"
                  size="sm"
                  className="hover:bg-accent/50 transition-colors h-8 w-8 p-0 flex-shrink-0"
                  title={showSidebar ? "Expand Sidebar" : "Sidebar Hidden"}
                >
                  <PanelLeftOpen className="h-4 w-4" />
                </Button>
              ) : null}
              
              {!showSidebar && (
                <Button
                  onClick={handleHomeNavigation}
                  variant="ghost"
                  size="sm"
                  className="hover:bg-accent/50 transition-colors h-8 px-2 sm:px-3 flex-shrink-0"
                >
                  <Home className="h-4 w-4 sm:mr-2" />
                  <span className="hidden sm:inline">Home</span>
                </Button>
              )}
              <div className="min-w-0 flex-1">
                <h1 className="text-base sm:text-xl font-semibold truncate">
                  {chatType === 'patient' ? 'Patient Support' : 'Research Assistant'}
                </h1>
                <p className="text-xs sm:text-sm text-muted-foreground truncate hidden sm:block">
                  {chatType === 'patient' 
                    ? 'Get general health information and support'
                    : 'Access comprehensive cancer research data and insights'
                  }
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
              {/* Connection Status Indicator */}
              <div className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm">
                {connectionStatus === 'online' && (
                  <div className="flex items-center gap-1 text-green-600 bg-green-50 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full">
                    <Wifi className="h-3 w-3" />
                    <span className="text-xs font-medium hidden sm:inline">Online</span>
                  </div>
                )}
                {connectionStatus === 'offline' && (
                  <div className="flex items-center gap-1 text-red-600 bg-red-50 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full">
                    <WifiOff className="h-3 w-3" />
                    <span className="text-xs font-medium hidden sm:inline">Offline</span>
                  </div>
                )}
                {connectionStatus === 'checking' && (
                  <div className="flex items-center gap-1 text-yellow-600 bg-yellow-50 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full">
                    <AlertCircle className="h-3 w-3 animate-spin" />
                    <span className="text-xs font-medium hidden sm:inline">Checking...</span>
                  </div>
                )}
              </div>
              
              <Button
                onClick={handleNewChat}
                variant="outline"
                size="sm"
                className="hover:bg-accent/50 transition-colors shadow-sm h-8 px-2 sm:px-3"
              >
                <Plus className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">New Chat</span>
              </Button>
            </div>
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 p-3 sm:p-4 md:p-6">
          <div className="space-y-4 sm:space-y-6 max-w-4xl mx-auto">
            {/* Loading indicator for chat history */}
            {isHistoryLoading && (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner size="sm" />
                <span className="ml-2 text-sm text-muted-foreground">Loading chat history...</span>
              </div>
            )}
            {/* Group messages by date */}
            {groupMessagesByDate(messages).map((dateGroup) => (
              <div key={dateGroup.date} className="space-y-6">
                {/* Date Header */}
                <div className="flex items-center justify-center">
                  <div className="bg-muted/80 text-muted-foreground px-4 py-2 rounded-full text-sm font-medium border shadow-sm">
                    {dateGroup.displayDate}
                  </div>
                </div>
                
                {/* Messages for this date */}
                <div className="space-y-6">
                  {dateGroup.messages.map((msg, index) => {
                    const prevMsg = index > 0 ? dateGroup.messages[index - 1] : null;
                    const showTime = !prevMsg || !areMessagesCloseInTime(msg, prevMsg);
                    
                    return (
                      <div key={msg.id} className="space-y-3">
                        {/* Time header for message groups */}
                        {showTime && (
                          <div className="flex items-center justify-center">
                            <div className="bg-background border border-muted rounded-full px-3 py-1 text-xs text-muted-foreground shadow-sm">
                              {formatTimeOnly(new Date(msg.timestamp))}
                            </div>
                          </div>
                        )}
                        
                        {/* Message */}
                        <div
                          className={cn(
                            "flex gap-4",
                            msg.type === 'user' ? 'justify-end' : 'justify-start'
                          )}
                        >
                          {/* Avatar */}
                          <div className={cn(
                            "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm transition-colors",
                            msg.type === 'user' 
                              ? 'bg-primary text-primary-foreground order-2' 
                              : 'bg-secondary text-secondary-foreground'
                          )}>
                            {msg.type === 'user' ? (
                              <User className="h-4 w-4" />
                            ) : (
                              <Bot className="h-4 w-4" />
                            )}
                          </div>

                          {/* Message Content */}
                          <div className={cn(
                            "flex-1 max-w-3xl group",
                            msg.type === 'user' ? 'order-1' : 'order-2'
                          )}>
                            <div
                              className={cn(
                                "rounded-2xl px-4 py-3 shadow-sm transition-shadow hover:shadow-md",
                                msg.type === 'user'
                                  ? 'bg-primary text-primary-foreground'
                                  : 'bg-muted text-foreground border'
                              )}
                            >
                              {msg.type === 'assistant' ? (
                                <MarkdownRenderer 
                                  content={msg.content}
                                  className={msg.type === 'assistant' ? 'prose-invert' : ''}
                                />
                              ) : (
                                <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                              )}
                            </div>
                            
                            {/* Message Actions */}
                            <div className="flex items-center gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-7 px-3 text-xs hover:bg-accent/50 transition-colors"
                                onClick={() => copyToClipboard(msg.content)}
                              >
                                <Copy className="h-3 w-3 mr-1" />
                                Copy
                              </Button>
                              {msg.type === 'assistant' && (
                                <>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="h-7 px-3 text-xs hover:bg-accent/50 transition-colors"
                                  >
                                    <ThumbsUp className="h-3 w-3 mr-1" />
                                    Good
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="h-7 px-3 text-xs hover:bg-accent/50 transition-colors"
                                  >
                                    <ThumbsDown className="h-3 w-3 mr-1" />
                                    Bad
                                  </Button>
                                </>
                              )}
                            </div>

                            {/* Sources and Reasoning for assistant messages */}
                            {msg.type === 'assistant' && (msg.sources?.length || msg.reasoning?.length) && (
                              <div className="mt-4 space-y-4">
                                {msg.sources && msg.sources.length > 0 && (
                                  <div className="bg-muted/50 rounded-lg p-4 border">
                                    <p className="text-sm font-medium text-muted-foreground mb-3">Sources:</p>
                                    <div className="flex flex-wrap gap-2">
                                      {msg.sources.map((source, idx) => (
                                        <Badge key={idx} variant="outline" className="text-xs hover:bg-accent transition-colors">
                                          {typeof source === 'string' ? source : source.title || source.name || 'Source'}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                {msg.reasoning && msg.reasoning.length > 0 && (
                                  <div className="bg-muted/30 rounded-lg p-4 border">
                                    <div className="flex items-center gap-2 mb-4">
                                      <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                                      <p className="text-sm font-semibold text-foreground">AI Reasoning Process</p>
                                      <span className="text-xs text-muted-foreground bg-primary/10 px-2 py-1 rounded-full">
                                        {msg.reasoning.length} step{msg.reasoning.length > 1 ? 's' : ''}
                                      </span>
                                    </div>
                                    <div className="text-sm text-muted-foreground space-y-3">
                                      {msg.reasoning.map((reason, idx) => (
                                        <div key={idx} className="bg-background/50 rounded-lg p-4 border-l-4 border-primary/30 hover:bg-background/70 transition-colors">
                                          <div className="flex items-start gap-3 mb-3">
                                            <span className="text-primary font-bold text-sm bg-primary/10 px-3 py-1 rounded-full flex-shrink-0">
                                              Step {idx + 1}
                                            </span>
                                          </div>
                                          <div className="prose prose-sm max-w-none">
                                            <MarkdownRenderer 
                                              content={typeof reason === 'string' ? reason : reason.text || reason.description || 'Reasoning step'}
                                              className="prose-invert"
                                            />
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center shadow-sm">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="bg-muted text-foreground px-4 py-3 rounded-2xl flex items-center gap-3 border shadow-sm">
                    <LoadingSpinner size="sm" />
                    <div className="flex flex-col">
                      <span className="font-medium">AI is researching...</span>
                      <span className="text-xs text-muted-foreground">
                        Scanning relevant research papers and patient experiences... (up to 6 minutes)
                      </span>
                      <div className="w-full bg-muted-foreground/20 rounded-full h-1 mt-2">
                        <div className="bg-primary h-1 rounded-full animate-pulse transition-all" style={{width: '60%'}}></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {error && (
              <div className="flex justify-start">
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-destructive text-destructive-foreground flex items-center justify-center shadow-sm">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-2xl border border-destructive/20 shadow-sm">
                    <span className="text-sm font-medium">{error}</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t p-3 sm:p-4 bg-background/95 backdrop-blur-sm">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-2 sm:gap-3">
              <div className="relative flex-1">
                <Input
                  ref={inputRef}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder={
                    chatType === 'patient'
                      ? "Ask about symptoms, treatments..."
                      : "Search research papers..."
                  }
                  onKeyPress={handleKeyPress}
                  className="flex-1 pr-10 sm:pr-12 h-10 sm:h-12 rounded-2xl border-muted-foreground/20 focus:border-primary/50 transition-all shadow-sm bg-background/50 backdrop-blur-sm text-sm sm:text-base"
                  disabled={isLoading}
                />
                <Button 
                  onClick={handleSendMessage} 
                  variant="default" 
                  disabled={isLoading || !message.trim() || connectionStatus === 'offline'}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 h-7 w-7 sm:h-8 sm:w-8 p-0 rounded-xl shadow-sm hover:shadow-md transition-all"
                >
                  {isLoading ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    <Send className="h-3 w-3 sm:h-4 sm:w-4" />
                  )}
                </Button>
              </div>
            </div>
            <div className="mt-2 sm:mt-3 space-y-1">
              <p className="text-xs text-muted-foreground leading-relaxed">
                {chatType === 'patient' 
                  ? "This AI assistant provides general information only and is not a substitute for professional medical advice."
                  : "Research data is for informational purposes. Always consult with healthcare professionals for medical decisions."
                }
              </p>
              {connectionStatus === 'offline' && (
                <p className="text-xs text-red-600 flex items-center gap-1 bg-red-50 px-2 py-1 rounded-full">
                  <WifiOff className="h-3 w-3" />
                  You seem to be offline. Trying to auto-connect again...
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;