import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Heart, 
  Shield, 
  Users, 
  MessageSquare, 
  Plus, 
  Clock, 
  Search,
  ArrowRight,
  Bot
} from "lucide-react";
import Navigation from "@/components/Navigation";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { ChatHistoryApiService, ChatHistory } from "@/services/chatHistoryApi";
import { useAuth } from "@/hooks/useAuth";
import { formatShortDate, sortChatsByDate, groupChatsForDisplay, formatTimeOnly } from "@/lib/dateUtils";

const PatientPortal = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [chatHistories, setChatHistories] = useState<ChatHistory[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (user) {
      loadChatHistories();
    }
  }, [user]);

  const loadChatHistories = async () => {
    if (!user) return;
    
    setIsLoadingHistory(true);
    try {
      const response = await ChatHistoryApiService.getChatsMetadata(user.userid);
      if (response.chats_metadata) {
        const histories: ChatHistory[] = response.chats_metadata
          .map((chat: any) => ({
            id: chat.id, // Backend returns 'id', not 'chat_id'
            title: chat.title || 'Untitled Chat',
            lastMessage: chat.last_message || 'No messages yet',
            timestamp: new Date(chat.updated_at || chat.created_at),
            messageCount: chat.message_count || 0
          }));
        
        // Sort chats by date (newest first) using the utility function
        const sortedHistories = sortChatsByDate(histories);
        setChatHistories(sortedHistories);
      }
    } catch (error) {
      console.error('Failed to load chat histories:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleNewChat = () => {
    navigate('/chat/patient');
  };

  const handleChatClick = (chatId: string) => {
    navigate(`/chat/patient?chatId=${chatId}`);
  };

  const filteredChats = chatHistories.filter(chat =>
    chat.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    chat.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatTimestamp = (date: Date) => {
    return formatShortDate(date);
  };

  return (
    <div className="min-h-screen bg-subtle-gradient">
      <Navigation />
      
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-serif font-bold text-foreground mb-4">
              Patient Support Portal
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Get general health information and support in a safe, welcoming environment. 
              Our AI assistant can help answer your questions about cancer care and treatment.
            </p>
          </div>

          {/* Trust Indicators */}
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <Card className="card-shadow border-accent/20">
              <CardContent className="p-6 text-center">
                <div className="bg-accent/10 rounded-full p-3 w-fit mx-auto mb-4">
                  <Heart className="h-6 w-6 text-accent" />
                </div>
                <h3 className="font-semibold text-foreground mb-2">Compassionate Care</h3>
                <p className="text-sm text-muted-foreground">
                  Designed with empathy and understanding for patients and families
                </p>
              </CardContent>
            </Card>

            <Card className="card-shadow border-primary/20">
              <CardContent className="p-6 text-center">
                <div className="bg-primary/10 rounded-full p-3 w-fit mx-auto mb-4">
                  <Shield className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-semibold text-foreground mb-2">Privacy Protected</h3>
                <p className="text-sm text-muted-foreground">
                  Your conversations are private and secure
                </p>
              </CardContent>
            </Card>

            <Card className="card-shadow border-accent/20">
              <CardContent className="p-6 text-center">
                <div className="bg-accent/10 rounded-full p-3 w-fit mx-auto mb-4">
                  <Users className="h-6 w-6 text-accent" />
                </div>
                <h3 className="font-semibold text-foreground mb-2">Community Support</h3>
                <p className="text-sm text-muted-foreground">
                  Connect with resources and support networks
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid lg:grid-cols-4 gap-8">
            {/* Main Chat History */}
            <div className="lg:col-span-3">
              <Card className="card-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl">Your Chat History</CardTitle>
                    <Button onClick={handleNewChat} className="gap-2">
                      <Plus className="h-4 w-4" />
                      New Chat
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  {/* Search */}
                  <div className="p-6 border-b">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                      <Input
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search your conversations..."
                        className="pl-10"
                      />
                    </div>
                  </div>

                  {/* Chat List */}
                  <ScrollArea className="h-96">
                    {isLoadingHistory ? (
                      <div className="flex items-center justify-center py-12">
                        <div className="flex flex-col items-center gap-4">
                          <LoadingSpinner size="lg" className="text-primary" />
                          <p className="text-muted-foreground">Loading your conversations...</p>
                        </div>
                      </div>
                    ) : filteredChats.length === 0 ? (
                      <div className="text-center py-12">
                        <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                        <h3 className="text-lg font-semibold text-foreground mb-2">
                          {searchQuery ? 'No matching conversations' : 'No conversations yet'}
                        </h3>
                        <p className="text-muted-foreground mb-4">
                          {searchQuery 
                            ? 'Try adjusting your search terms'
                            : 'Start a new conversation with our AI assistant'
                          }
                        </p>
                        {!searchQuery && (
                          <Button onClick={handleNewChat} className="gap-2">
                            <Plus className="h-4 w-4" />
                            Start New Chat
                          </Button>
                        )}
                      </div>
                    ) : (
                      <div className="p-4 space-y-4">
                        {groupChatsForDisplay(filteredChats).map((dateGroup) => (
                          <div key={dateGroup.date} className="space-y-3">
                            {/* Date Header */}
                            <div className="sticky top-0 bg-background/95 backdrop-blur-sm z-10">
                              <div className="px-2 py-1">
                                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                                  {dateGroup.displayDate}
                                </h3>
                              </div>
                            </div>
                            
                            {/* Chats for this date */}
                            <div className="space-y-2">
                              {dateGroup.chats.map((chat) => (
                                <Card
                                  key={chat.id}
                                  className="cursor-pointer transition-colors hover:bg-accent/50 border-0"
                                  onClick={() => handleChatClick(chat.id)}
                                >
                                  <CardContent className="p-4">
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-2">
                                          <Bot className="h-4 w-4 text-primary flex-shrink-0" />
                                          <h3 className="font-medium text-sm truncate">
                                            {chat.title}
                                          </h3>
                                        </div>
                                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                          <div className="flex items-center gap-1">
                                            <Clock className="h-3 w-3" />
                                            {formatTimeOnly(chat.timestamp)}
                                          </div>
                                        </div>
                                      </div>
                                      <ArrowRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                    </div>
                                  </CardContent>
                                </Card>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions Sidebar */}
            <div className="space-y-6">
              <Card className="card-shadow">
                <CardHeader>
                  <CardTitle className="text-lg">Quick Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Button 
                    onClick={handleNewChat} 
                    className="w-full justify-start gap-2"
                    variant="default"
                  >
                    <Plus className="h-4 w-4" />
                    Start New Chat
                  </Button>
                  <Button 
                    variant="outline" 
                    className="w-full justify-start gap-2"
                    onClick={() => setSearchQuery('symptoms')}
                  >
                    <MessageSquare className="h-4 w-4" />
                    Ask About Symptoms
                  </Button>
                  <Button 
                    variant="outline" 
                    className="w-full justify-start gap-2"
                    onClick={() => setSearchQuery('treatment')}
                  >
                    <MessageSquare className="h-4 w-4" />
                    Treatment Questions
                  </Button>
                </CardContent>
              </Card>

              <Card className="card-shadow">
                <CardHeader>
                  <CardTitle className="text-lg">Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  {chatHistories.length > 0 ? (
                    <div className="space-y-2">
                      {chatHistories.slice(0, 3).map((chat) => (
                        <div 
                          key={chat.id}
                          className="text-sm text-muted-foreground cursor-pointer hover:text-primary transition-colors"
                          onClick={() => handleChatClick(chat.id)}
                        >
                          <div className="truncate">{chat.title}</div>
                          <div className="text-xs">{formatTimestamp(chat.timestamp)}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No recent activity</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientPortal;