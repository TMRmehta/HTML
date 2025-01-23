import React from "react";
import { useParams, useSearchParams, useLocation } from "react-router-dom";
import Navigation from "@/components/Navigation";
import ChatInterface from "@/components/ChatInterface";

const ChatPage: React.FC = () => {
  const { chatType: chatTypeParam } = useParams<{ chatType: 'patient' | 'research' }>();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const chatId = searchParams.get('chatId');
  
  // Debug logging
  console.log('ChatPage - chatType param:', chatTypeParam);
  console.log('ChatPage - chatId from URL:', chatId);
  console.log('ChatPage - full URL:', window.location.href);
  console.log('ChatPage - pathname:', location.pathname);

  // Support both split routes (/chat/patient, /chat/research) and param route (/chat/:chatType)
  const chatType: 'patient' | 'research' | undefined = chatTypeParam
    || (location.pathname.includes('/chat/research') ? 'research'
    : location.pathname.includes('/chat/patient') ? 'patient' : undefined);

  if (!chatType || !['patient', 'research'].includes(chatType)) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-6 py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-foreground mb-4">Page Not Found</h1>
            <p className="text-muted-foreground">The requested chat page does not exist.</p>
          </div>
        </div>
      </div>
    );
  }

  const initialMessage = chatType === 'patient' 
    ? "Hello! I'm here to help answer your health-related questions. Please remember that I provide general information only and cannot replace professional medical advice. How can I assist you today?"
    : "Hello! I'm your research assistant. I can help you find and analyze cancer research papers, clinical trials, and treatment protocols. What would you like to research today?";

  return (
    <div className="min-h-screen bg-background">
      {/* <Navigation /> */}
      <div className="h-[calc(100vh-4rem)]">
        <ChatInterface 
          chatType={chatType}
          showSidebar={true}
          initialMessage={initialMessage}
          chatId={chatId || undefined}
        />
      </div>
    </div>
  );
};

export default ChatPage;

