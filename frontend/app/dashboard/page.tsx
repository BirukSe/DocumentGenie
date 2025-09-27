'use client';

import { useState, useEffect, useRef } from "react";
import { supabase } from "../../lib/supabase";
import { useRouter } from "next/navigation";
import { FileText, Upload, LogOut, User, Settings, Sparkles, Download, Edit3 } from "lucide-react";
import { getInitialTheme, saveTheme } from "../../lib/theme";

interface Document {
  id: string;
  name: string;
  file_size: number;
  created_at: string;
  file_path: string;
}

export default function Dashboard() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [sidebarWidth, setSidebarWidth] = useState(320);
  const [isResizing, setIsResizing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [isDark, setIsDark] = useState(true);
  const router = useRouter();
  const sidebarRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    if (!user) return;
    
    const { data, error } = await supabase
      .from('documents')
      .select('*')
      .order('created_at', { ascending: false });
    
    if (error) {
      console.error('Error fetching documents:', error);
    } else {
      setDocuments(data || []);
    }
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

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (event === 'SIGNED_OUT' || !session) {
          router.push('/');
        }
      }
    );

    return () => subscription.unsubscribe();
  }, [router]);

  useEffect(() => {
    if (user) {
      fetchDocuments();
    }
  }, [user]);

  useEffect(() => {
    setIsDark(getInitialTheme());
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    saveTheme(newTheme);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsResizing(true);
    e.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const newWidth = e.clientX;
      if (newWidth >= 250 && newWidth <= 500) {
        setSidebarWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays - 1} days ago`;
    return date.toLocaleDateString();
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  const handleFileUpload = async (file: File) => {
    if (!user || !file) return;
    
    setUploading(true);
    try {
      // Upload file to Supabase storage
      const fileExt = file.name.split('.').pop();
      const fileName = `${user.id}/${Date.now()}.${fileExt}`;
      
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('documents')
        .upload(fileName, file);
      
      if (uploadError) throw uploadError;
      
      // Save document metadata to database
      const { error: dbError } = await supabase
        .from('documents')
        .insert({
          user_id: user.id,
          name: file.name,
          file_path: uploadData.path,
          file_size: file.size,
          mime_type: file.type
        });
      
      if (dbError) throw dbError;
      
      // Refresh documents list
      await fetchDocuments();
      
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload file. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      handleFileUpload(file);
    } else {
      alert('Please select a PDF file.');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
      handleFileUpload(file);
    } else {
      alert('Please drop a PDF file.');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-gray-800' : 'bg-gray-100'}`}>
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${isDark ? 'bg-gray-900' : 'bg-gray-100'}`}>
      {/* Header */}
      <header className={`border-b ${isDark ? 'border-gray-700 bg-gray-800' : 'border-gray-300 bg-gray-50'} shadow-sm`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <h1 className={`text-xl font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>DocumentGenie</h1>
            </div>
            
            <div className="flex items-center space-x-4">
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
        {/* Left Sidebar - Document List */}
        <div 
          ref={sidebarRef}
          className={`${isDark ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-300'} border-r flex flex-col relative shadow-sm`}
          style={{ width: sidebarWidth }}
        >
          <div className={`p-4 border-b ${isDark ? 'border-gray-700' : 'border-gray-300'}`}>
            <h2 className={`text-lg font-medium mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>Documents</h2>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Select a document to edit</p>
          </div>
          
          <div className="flex-1 overflow-y-auto p-3">
            {/* Document List */}
            <div className="space-y-1">
              {documents.length > 0 ? (
                documents.map((doc) => (
                  <div 
                    key={doc.id} 
                    className={`p-3 cursor-pointer transition-colors rounded-md ${isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`}
                    onClick={() => router.push(`/document/${doc.id}`)}
                  >
                    <div className="flex items-center space-x-3">
                      <FileText className="w-4 h-4 text-red-500 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-medium truncate ${isDark ? 'text-white' : 'text-gray-900'}`}>{doc.name}</p>
                        <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{formatFileSize(doc.file_size)} • {formatDate(doc.created_at)}</p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className={`mt-8 text-center ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                  <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No documents yet</p>
                  <p className="text-xs">Upload your first PDF to get started</p>
                </div>
              )}
            </div>
          </div>
          
          {/* Sidebar Footer */}
          <div className={`p-3 border-t ${isDark ? 'border-gray-700' : 'border-gray-300'}`}>
            <button className={`w-full flex items-center justify-center space-x-2 px-3 py-2 border rounded-md transition-colors text-sm ${isDark ? 'bg-gray-700 hover:bg-gray-600 text-gray-300 border-gray-600' : 'bg-gray-100 hover:bg-gray-200 text-gray-700 border-gray-300'}`}>
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </button>
          </div>
          
          {/* Resize Handle */}
          <div 
            className="absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-blue-400 transition-colors"
            onMouseDown={handleMouseDown}
          />
        </div>

        {/* Main Content Area - Upload/Edit */}
        <div className={`flex-1 flex flex-col ${isDark ? 'bg-gray-900' : 'bg-gray-50'}`}>
          <div className="flex-1 p-6 flex items-center justify-center">
            {/* Upload Area */}
            <div className="w-full max-w-xl">
              <div className="text-center mb-6">
                <h2 className={`text-2xl font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  Upload PDF Document
                </h2>
                <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  Drag and drop your file here, or click to browse
                </p>
              </div>

              {/* Drag and Drop Zone */}
              <div 
                className={`border-2 border-dashed rounded-lg p-12 transition-all cursor-pointer ${isDark ? 'border-gray-600 hover:border-blue-400 hover:bg-blue-900/20' : 'border-gray-400 hover:border-blue-400 hover:bg-blue-50/30'}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="text-center space-y-4">
                  <div className={`mx-auto w-16 h-16 rounded-full flex items-center justify-center ${isDark ? 'bg-blue-900/30' : 'bg-blue-50'}`}>
                    {uploading ? (
                      <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                      <Upload className="w-8 h-8 text-blue-500" />
                    )}
                  </div>
                  
                  <div className="space-y-1">
                    <h3 className={`text-lg font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                      {uploading ? 'Uploading...' : 'Choose a file'}
                    </h3>
                    <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                      Maximum size: 10MB
                    </p>
                  </div>

                  <div className="space-y-3">
                    <button 
                      className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                      disabled={uploading}
                    >
                      {uploading ? 'Uploading...' : 'Browse Files'}
                    </button>
                    
                    <div className={`flex items-center justify-center space-x-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                      <span>Supports:</span>
                      <span className={`px-2 py-1 rounded text-xs ${isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'}`}>PDF</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                className="hidden"
              />

              {/* Quick Actions */}
              <div className="mt-6 grid grid-cols-3 gap-3">
                <div className={`p-3 border rounded-lg text-center transition-colors cursor-pointer ${isDark ? 'bg-gray-800 border-gray-700 hover:bg-gray-700' : 'bg-gray-100 border-gray-300 hover:bg-gray-200'}`}>
                  <Edit3 className="w-6 h-6 text-blue-600 mx-auto mb-1" />
                  <h4 className={`text-sm font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>Edit</h4>
                  <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Rearrange pages</p>
                </div>
                
                <div className={`p-3 border rounded-lg text-center transition-colors cursor-pointer ${isDark ? 'bg-gray-800 border-gray-700 hover:bg-gray-700' : 'bg-gray-100 border-gray-300 hover:bg-gray-200'}`}>
                  <Sparkles className="w-6 h-6 text-purple-600 mx-auto mb-1" />
                  <h4 className={`text-sm font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>Enhance</h4>
                  <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>AI improve</p>
                </div>
                
                <div className={`p-3 border rounded-lg text-center transition-colors cursor-pointer ${isDark ? 'bg-gray-800 border-gray-700 hover:bg-gray-700' : 'bg-gray-100 border-gray-300 hover:bg-gray-200'}`}>
                  <Download className="w-6 h-6 text-green-600 mx-auto mb-1" />
                  <h4 className={`text-sm font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>Export</h4>
                  <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Download</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
