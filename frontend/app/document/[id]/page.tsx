'use client';

import { useState, useEffect, useRef } from "react";
import { supabase } from "../../../lib/supabase";
import { useRouter, useParams } from "next/navigation";
import { FileText, Send, ArrowLeft, User, LogOut, Settings, Maximize2, Minimize2, Save, X, CheckCircle, AlertCircle, Loader } from "lucide-react";
import { getInitialTheme, saveTheme } from "../../../lib/theme";

interface Document {
  id: string;
  name: string;
  file_size: number;
  created_at: string;
  file_path: string;
  file_url: string;
  user_id: string;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'ai' | 'system';
  content: string;
  timestamp: Date;
  status?: 'sending' | 'processing' | 'completed' | 'error';
}

interface WebSocketMessage {
  type: string;
  operation?: string;
  progress?: number;
  message?: string;
  details?: any;
  timestamp?: number;
  preview_url?: string;
  result_path?: string;
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
  const [isProcessing, setIsProcessing] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [currentProgress, setCurrentProgress] = useState(0);
  const [currentOperation, setCurrentOperation] = useState('');
  const [sessionInitialized, setSessionInitialized] = useState(false);
  const [previewUrl, setPreviewUrl] = useState('');
  const router = useRouter();
  const params = useParams();
  const chatEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

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
        // Initialize session with backend
        await initializeSession(data.id, urlData.signedUrl);
      }
    };

    if (user) {
      fetchDocument();
    }
  }, [user, params.id, router]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  useEffect(() => {
    return () => {
      // Cleanup WebSocket on unmount
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  const initializeSession = async (documentId: string, originalUrl: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/document/session/init', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: documentId,
          original_url: originalUrl
        })
      });
      
      if (response.ok) {
        setSessionInitialized(true);
        // Connect WebSocket
        connectWebSocket(documentId);
      }
    } catch (error) {
      console.error('Failed to initialize session:', error);
    }
  };

  const connectWebSocket = (documentId: string) => {
    const ws = new WebSocket(`ws://localhost:8000/ws/document/${documentId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      handleWebSocketMessage(message);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Attempt to reconnect after 3 seconds
      setTimeout(() => connectWebSocket(documentId), 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'manipulation_progress':
        setCurrentProgress(message.progress || 0);
        setCurrentOperation(message.operation || '');
        setIsProcessing(true);
        
        // Add system message to chat
        const progressMessage: ChatMessage = {
          id: Date.now().toString(),
          type: 'system',
          content: message.message || 'Processing...',
          timestamp: new Date(),
          status: 'processing'
        };
        setChatMessages(prev => [...prev, progressMessage]);
        break;
        
      case 'manipulation_complete':
        setCurrentProgress(100);
        setIsProcessing(false);
        setHasUnsavedChanges(true);
        
        if (message.preview_url) {
          setPreviewUrl(`http://localhost:8000${message.preview_url}`);
          setPdfUrl(`http://localhost:8000${message.preview_url}`);
        }
        
        const completeMessage: ChatMessage = {
          id: Date.now().toString(),
          type: 'system',
          content: message.message || 'Modification completed successfully',
          timestamp: new Date(),
          status: 'completed'
        };
        setChatMessages(prev => [...prev, completeMessage]);
        break;
        
      case 'error':
        setIsProcessing(false);
        setCurrentProgress(0);
        
        const errorMessage: ChatMessage = {
          id: Date.now().toString(),
          type: 'system',
          content: message.message || 'An error occurred',
          timestamp: new Date(),
          status: 'error'
        };
        setChatMessages(prev => [...prev, errorMessage]);
        break;
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !sessionInitialized || isProcessing) return;

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
      status: 'sending'
    };

    setChatMessages(prev => [...prev, newMessage]);
    const command = inputMessage;
    setInputMessage('');
    setIsProcessing(true);

    try {
      const response = await fetch('http://localhost:8000/api/document/modify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: document?.id,
          command: command
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to process command');
      }
      
      // Update message status
      setChatMessages(prev => prev.map(msg => 
        msg.id === newMessage.id ? { ...msg, status: 'processing' } : msg
      ));
      
    } catch (error) {
      setIsProcessing(false);
      setChatMessages(prev => prev.map(msg => 
        msg.id === newMessage.id ? { ...msg, status: 'error' } : msg
      ));
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
        status: 'error'
      };
      setChatMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleSaveChanges = async () => {
    if (!document?.id || !hasUnsavedChanges) return;
    
    try {
      const response = await fetch('http://localhost:8000/api/document/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: document.id
        })
      });
      
      if (response.ok) {
        setHasUnsavedChanges(false);
        const saveMessage: ChatMessage = {
          id: Date.now().toString(),
          type: 'system',
          content: 'Document saved successfully!',
          timestamp: new Date(),
          status: 'completed'
        };
        setChatMessages(prev => [...prev, saveMessage]);
      }
    } catch (error) {
      console.error('Failed to save changes:', error);
    }
  };

  const handleDiscardChanges = async () => {
    if (!document?.id) return;
    
    try {
      const response = await fetch('http://localhost:8000/api/document/discard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: document.id
        })
      });
      
      if (response.ok) {
        setHasUnsavedChanges(false);
        setPreviewUrl('');
        // Reset to original PDF
        const { data: urlData } = await supabase.storage
          .from('documents')
          .createSignedUrl(document.file_path, 3600);
        if (urlData?.signedUrl) {
          setPdfUrl(urlData.signedUrl);
        }
      }
    } catch (error) {
      console.error('Failed to discard changes:', error);
    }
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
              {/* Save/Discard buttons */}
              {hasUnsavedChanges && (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleSaveChanges}
                    className="flex items-center space-x-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    title="Save changes"
                  >
                    <Save className="w-4 h-4" />
                    <span className="text-sm">Save</span>
                  </button>
                  <button
                    onClick={handleDiscardChanges}
                    className="flex items-center space-x-2 px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    title="Discard changes"
                  >
                    <X className="w-4 h-4" />
                    <span className="text-sm">Discard</span>
                  </button>
                </div>
              )}
              
              {/* Processing indicator */}
              {isProcessing && (
                <div className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg">
                  <Loader className="w-4 h-4 animate-spin" />
                  <span className="text-sm">{currentOperation || 'Processing...'}</span>
                  <span className="text-sm">({currentProgress}%)</span>
                </div>
              )}
              
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
                      : message.type === 'system'
                      ? message.status === 'error'
                        ? 'bg-red-100 text-red-800 border border-red-200'
                        : message.status === 'completed'
                        ? 'bg-green-100 text-green-800 border border-green-200'
                        : 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                      : isDark ? 'bg-gray-700 text-gray-100' : 'bg-white text-gray-900 border border-gray-200'
                  }`}>
                    <div className="flex items-start space-x-2">
                      {message.type === 'system' && (
                        <div className="flex-shrink-0 mt-0.5">
                          {message.status === 'error' && <AlertCircle className="w-4 h-4" />}
                          {message.status === 'completed' && <CheckCircle className="w-4 h-4" />}
                          {message.status === 'processing' && <Loader className="w-4 h-4 animate-spin" />}
                        </div>
                      )}
                      <div className="flex-1">
                        <p className="text-sm">{message.content}</p>
                        <div className="flex items-center justify-between mt-1">
                          <p className={`text-xs ${
                            message.type === 'user' 
                              ? 'text-blue-100' 
                              : message.type === 'system'
                              ? 'text-current opacity-70'
                              : isDark ? 'text-gray-400' : 'text-gray-500'
                          }`}>
                            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                          {message.status && message.type === 'user' && (
                            <div className="flex items-center space-x-1">
                              {message.status === 'sending' && <Loader className="w-3 h-3 animate-spin text-blue-200" />}
                              {message.status === 'processing' && <Loader className="w-3 h-3 animate-spin text-blue-200" />}
                              {message.status === 'completed' && <CheckCircle className="w-3 h-3 text-blue-200" />}
                              {message.status === 'error' && <AlertCircle className="w-3 h-3 text-red-200" />}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
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
                disabled={!inputMessage.trim() || !sessionInitialized || isProcessing}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title={!sessionInitialized ? "Initializing session..." : isProcessing ? "Processing..." : "Send message"}
              >
                {isProcessing ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
