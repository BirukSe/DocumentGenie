'use client';

import { useState, useEffect, useRef } from "react";
import { supabase } from "../../../lib/supabase";
import { useRouter, useParams } from "next/navigation";
import { FileText, Send, ArrowLeft, User, LogOut, Settings, Maximize2, Minimize2 } from "lucide-react";
import { getInitialTheme, saveTheme } from "../../../lib/theme";

interface Document {
  id: string;
  name: string;
  file_size: number;
  created_at: string;
  file_path: string;
  user_id: string;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

export default function DocumentViewer() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [document, setDocument] = useState<Document | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string>('');
  const [isDark, setIsDark] = useState(true);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isChatExpanded, setIsChatExpanded] = useState(false);
  const router = useRouter();
  const params = useParams();
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsDark(getInitialTheme());
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    saveTheme(newTheme);
  };

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        router.push('/');
        return;
      }
      setUser(user);
      setLoading(false);
    };

    getUser();
  }, [router]);

  useEffect(() => {
    const fetchDocument = async () => {
      if (!user || !params.id) return;

      const { data, error } = await supabase
        .from('documents')
        .select('*')
        .eq('id', params.id)
        .eq('user_id', user.id)
        .single();

      if (error) {
        console.error('Error fetching document:', error);
        router.push('/dashboard');
        return;
      }

      setDocument(data);

      // Get PDF URL from storage
      const { data: urlData } = await supabase.storage
        .from('documents')
        .createSignedUrl(data.file_path, 3600); // 1 hour expiry

      if (urlData?.signedUrl) {
        setPdfUrl(urlData.signedUrl);
      }
    };

    if (user) {
      fetchDocument();
    }
  }, [user, params.id, router]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setChatMessages(prev => [...prev, newMessage]);
    setInputMessage('');

    // TODO: Send to AI backend for processing
    // For now, add a placeholder AI response
    setTimeout(() => {
      const aiResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: 'I understand you want to modify the document. The AI backend will be integrated here to process your request and update the PDF in real-time.',
        timestamp: new Date()
      };
      setChatMessages(prev => [...prev, aiResponse]);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-gray-900' : 'bg-gray-100'}`}>
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-gray-900' : 'bg-gray-100'}`}>
        <div className="text-center">
          <FileText className={`w-16 h-16 mx-auto mb-4 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} />
          <h2 className={`text-xl font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Document not found</h2>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${isDark ? 'bg-gray-900' : 'bg-gray-100'}`}>
      {/* Header */}
      <header className={`border-b ${isDark ? 'border-gray-700 bg-gray-800' : 'border-gray-300 bg-gray-50'} shadow-sm`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/dashboard')}
                className={`p-2 rounded-lg transition-colors ${isDark ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-200 text-gray-600'}`}
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-600 rounded-lg">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    {document.name}
                  </h1>
                  <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                    {new Date(document.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className={`p-2 rounded-lg transition-colors ${isDark ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-600'}`}
                title="Toggle fullscreen"
              >
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </button>
              <button
                onClick={toggleTheme}
                className={`p-2 rounded-lg transition-colors ${isDark ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-600'}`}
                title="Toggle brightness"
              >
                {isDark ? '☀️' : '🌙'}
              </button>
              <div className={`flex items-center space-x-2 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <User className="w-4 h-4" />
                <span className="text-sm">{user?.email}</span>
              </div>
              <button
                onClick={handleSignOut}
                className={`flex items-center space-x-2 px-3 py-2 transition-colors ${isDark ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`}
              >
                <LogOut className="w-4 h-4" />
                <span className="text-sm">Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-4rem)]">
        {/* Left Side - PDF Viewer */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 p-4">
            {pdfUrl ? (
              <div className="h-full w-full">
                <iframe
                  src={pdfUrl}
                  className="w-full h-full border-0 rounded-lg shadow-lg"
                  title={document.name}
                />
              </div>
            ) : (
              <div className={`h-full flex items-center justify-center ${isDark ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-lg`}>
                <div className="text-center">
                  <FileText className={`w-16 h-16 mx-auto mb-4 ${isDark ? 'text-gray-600' : 'text-gray-400'}`} />
                  <p className={`text-lg font-medium mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Loading document...</p>
                  <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Side - AI Chat */}
        <div className={`${isFullscreen ? 'w-0 overflow-hidden' : isChatExpanded ? 'w-[600px]' : 'w-96'} ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-300'} border-l flex flex-col transition-all duration-300 relative`}>
          <div className={`p-4 border-b ${isDark ? 'border-gray-700' : 'border-gray-300'} flex justify-between items-center`}>
            <div>
              <h2 className={`text-lg font-medium mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>AI Assistant</h2>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Describe how you want to modify your document</p>
            </div>
            <button
              onClick={() => setIsChatExpanded(!isChatExpanded)}
              className={`p-2 rounded-lg transition-colors ${isDark ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-200 text-gray-600'}`}
              title={isChatExpanded ? 'Collapse chat' : 'Expand chat'}
            >
              {isChatExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          </div>
          
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.length === 0 ? (
              <div className={`text-center py-8 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                <div className={`w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center ${isDark ? 'bg-blue-900/30' : 'bg-blue-50'}`}>
                  <Send className="w-6 h-6 text-blue-500" />
                </div>
                <p className="text-sm">Start a conversation to modify your document</p>
                <p className="text-xs mt-1">Try: "Move page 2 to the beginning" or "Resize all images to 50%"</p>
              </div>
            ) : (
              chatMessages.map((message) => (
                <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.type === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : isDark ? 'bg-gray-700 text-gray-100' : 'bg-white text-gray-900 border border-gray-200'
                  }`}>
                    <p className="text-sm">{message.content}</p>
                    <p className={`text-xs mt-1 ${
                      message.type === 'user' 
                        ? 'text-blue-100' 
                        : isDark ? 'text-gray-400' : 'text-gray-500'
                    }`}>
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))
            )}
            <div ref={chatEndRef} />
          </div>
          
          {/* Chat Input */}
          <div className={`p-4 border-t ${isDark ? 'border-gray-700' : 'border-gray-300'}`}>
            <div className="flex space-x-2">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Describe your document modification..."
                className={`flex-1 px-3 py-2 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
                  isDark 
                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                    : 'bg-white border-gray-400 text-gray-900 placeholder-gray-500'
                }`}
                rows={2}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
