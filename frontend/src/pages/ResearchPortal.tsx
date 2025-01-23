import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Search, 
  ExternalLink, 
  FileText, 
  Database, 
  BookOpen, 
  MessageSquare, 
  Plus, 
  Clock, 
  ArrowRight,
  Bot,
  Brain
} from "lucide-react";
import Navigation from "@/components/Navigation";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { ChatHistoryApiService, ChatHistory } from "@/services/chatHistoryApi";
import { useAuth } from "@/hooks/useAuth";
import { formatShortDate, sortChatsByDate, groupChatsForDisplay, formatTimeOnly } from "@/lib/dateUtils";

const ResearchPortal = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [chatHistories, setChatHistories] = useState<ChatHistory[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<'search' | 'chat'>('search');

  const mockResults = [
    {
      title: "Novel Immunotherapy Approaches in Metastatic Melanoma",
      authors: "Johnson, M. et al.",
      journal: "Nature Medicine",
      year: "2024",
      citations: "147",
      summary: "This study presents breakthrough findings on combining checkpoint inhibitors with personalized vaccines...",
      sources: ["PubMed", "Clinical Trials", "Medical Forums"]
    },
    {
      title: "CAR-T Cell Therapy: Latest Clinical Trial Results",
      authors: "Zhang, L. et al.",
      journal: "Cell",
      year: "2024",
      citations: "89",
      summary: "Comprehensive analysis of CAR-T cell therapy outcomes across multiple cancer types...",
      sources: ["PubMed", "FDA Database", "Research Networks"]
    }
  ];

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
            title: chat.title || 'Untitled Research Chat',
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

  const handleSearch = async () => {
    if (!query.trim() || isSearching) return;
    
    setIsSearching(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      setResults(mockResults);
    } catch (error) {
      console.error("Search error:", error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleNewChat = () => {
    navigate('/chat/research');
  };

  const handleChatClick = (chatId: string) => {
    navigate(`/chat/research?chatId=${chatId}`);
  };

  const filteredChats = chatHistories.filter(chat =>
    chat.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    chat.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatTimestamp = (date: Date) => {
    return formatShortDate(date);
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-serif font-bold text-foreground mb-4">
              Research Portal
            </h1>
            <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
              Access comprehensive cancer research data with AI-powered insights, 
              citations, and connections to leading medical databases and clinical trials.
            </p>
          </div>

          {/* Tab Navigation */}
          <div className="flex justify-center mb-8">
            <div className="bg-muted p-1 rounded-lg flex gap-2">
              <Button
                variant={activeTab === 'search' ? 'default' : 'ghost'}
                onClick={() => setActiveTab('search')}
                className="gap-2"
              >
                <Search className="h-4 w-4" />
                Research Search
              </Button>
              <Button
                variant={activeTab === 'chat' ? 'default' : 'ghost'}
                onClick={() => setActiveTab('chat')}
                className="gap-2"
              >
                <MessageSquare className="h-4 w-4" />
                AI Research Assistant
              </Button>
            </div>
          </div>

          {activeTab === 'search' ? (
            <div className="grid lg:grid-cols-4 gap-8">
              {/* Main Search and Results */}
              <div className="lg:col-span-3 space-y-6">
                {/* Search Interface */}
                <Card className="card-shadow">
                  <CardContent className="p-6">
                    <div className="flex space-x-3">
                      <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                        <Input
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          placeholder="Search research papers, clinical trials, treatment protocols..."
                          className="pl-10"
                          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                        />
                      </div>
                      <Button onClick={handleSearch} variant="medical" disabled={isSearching || !query.trim()}>
                        {isSearching ? (
                          <LoadingSpinner size="sm" />
                        ) : (
                          <Search className="h-4 w-4" />
                        )}
                        {isSearching ? "Searching..." : "Search"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Results */}
                {isSearching && (
                  <div className="flex items-center justify-center py-12">
                    <div className="flex flex-col items-center gap-4">
                      <LoadingSpinner size="lg" className="text-primary" />
                      <p className="text-muted-foreground">Searching research databases...</p>
                    </div>
                  </div>
                )}
                
                {results.length > 0 && !isSearching && (
                  <div className="space-y-4">
                    <h2 className="text-2xl font-serif font-semibold text-foreground">
                      Research Results
                    </h2>
                    {results.map((result, index) => (
                      <Card key={index} className="card-shadow hover:shadow-lg transition-medical">
                        <CardContent className="p-6">
                          <div className="flex justify-between items-start mb-4">
                            <div className="flex-1">
                              <h3 className="text-lg font-semibold text-foreground mb-2 hover:text-primary cursor-pointer">
                                {result.title}
                              </h3>
                              <p className="text-sm text-muted-foreground mb-2">
                                {result.authors} • {result.journal} • {result.year}
                              </p>
                              <div className="flex items-center space-x-4 mb-3">
                                <Badge variant="secondary">
                                  {result.citations} citations
                                </Badge>
                                <div className="flex space-x-2">
                                  {result.sources.map((source, idx) => (
                                    <Badge key={idx} variant="outline" className="text-xs">
                                      {source}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                              <p className="text-foreground">
                                {result.summary}
                              </p>
                            </div>
                            <Button variant="outline" size="sm">
                              <ExternalLink className="h-4 w-4" />
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Quick Access */}
                <Card className="card-shadow">
                  <CardHeader>
                    <CardTitle className="text-lg">Quick Access</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <Button variant="outline" className="w-full justify-start">
                      <FileText className="h-4 w-4" />
                      Clinical Trials
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                      <Database className="h-4 w-4" />
                      PubMed Search
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                      <BookOpen className="h-4 w-4" />
                      Treatment Guidelines
                    </Button>
                  </CardContent>
                </Card>

                {/* Recent Searches */}
                <Card className="card-shadow">
                  <CardHeader>
                    <CardTitle className="text-lg">Recent Searches</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="text-sm text-muted-foreground cursor-pointer hover:text-primary transition-smooth">
                      CAR-T cell therapy effectiveness
                    </div>
                    <div className="text-sm text-muted-foreground cursor-pointer hover:text-primary transition-smooth">
                      Immunotherapy combination protocols
                    </div>
                    <div className="text-sm text-muted-foreground cursor-pointer hover:text-primary transition-smooth">
                      Melanoma targeted therapy
                    </div>
                  </CardContent>
                </Card>

                {/* Data Sources */}
                <Card className="card-shadow">
                  <CardHeader>
                    <CardTitle className="text-lg">Connected Sources</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>PLOS Research</span>
                      <Badge variant="secondary" className="text-xs">Active</Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>ClinicalTrials.gov</span>
                      <Badge variant="secondary" className="text-xs">In Progress</Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Medical Forums</span>
                      <Badge variant="secondary" className="text-xs">In Progress</Badge>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          ) : (
            /* Chat Interface Tab */
            <div className="grid lg:grid-cols-4 gap-8">
              {/* Main Chat History */}
              <div className="lg:col-span-3">
                <Card className="card-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xl flex items-center gap-2">
                        <Brain className="h-5 w-5 text-primary" />
                        Research Assistant Chats
                      </CardTitle>
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
                          placeholder="Search your research conversations..."
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
                            <p className="text-muted-foreground">Loading your research conversations...</p>
                          </div>
                        </div>
                      ) : filteredChats.length === 0 ? (
                        <div className="text-center py-12">
                          <Brain className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                          <h3 className="text-lg font-semibold text-foreground mb-2">
                            {searchQuery ? 'No matching conversations' : 'No research conversations yet'}
                          </h3>
                          <p className="text-muted-foreground mb-4">
                            {searchQuery 
                              ? 'Try adjusting your search terms'
                              : 'Start a new conversation with our AI research assistant'
                            }
                          </p>
                          {!searchQuery && (
                            <Button onClick={handleNewChat} className="gap-2">
                              <Plus className="h-4 w-4" />
                              Start New Research Chat
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
                                            <Brain className="h-4 w-4 text-primary flex-shrink-0" />
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
                      Start New Research Chat
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start gap-2"
                      onClick={() => setSearchQuery('immunotherapy')}
                    >
                      <MessageSquare className="h-4 w-4" />
                      Ask About Immunotherapy
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start gap-2"
                      onClick={() => setSearchQuery('clinical trials')}
                    >
                      <MessageSquare className="h-4 w-4" />
                      Clinical Trial Questions
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start gap-2"
                      onClick={() => setSearchQuery('treatment protocols')}
                    >
                      <MessageSquare className="h-4 w-4" />
                      Treatment Protocols
                    </Button>
                  </CardContent>
                </Card>

                <Card className="card-shadow">
                  <CardHeader>
                    <CardTitle className="text-lg">Recent Research Chats</CardTitle>
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
                      <p className="text-sm text-muted-foreground">No recent research chats</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResearchPortal;