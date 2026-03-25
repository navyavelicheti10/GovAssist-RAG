"use client";

import { useState, useRef, useEffect } from "react";
import { Mic, Paperclip, Send, ShieldCheck, Loader2, Bot, User, Share2, Home, MessageSquare, Image as ImageIcon, Headphones, FileText, Settings, HelpCircle, ArrowUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  matches?: any[];
  citations?: string[];
  confidence?: number;
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
}

export default function VozhiApp() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState("");
  const [history, setHistory] = useState<ChatSession[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize from Database
  useEffect(() => {
    async function loadData() {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/sessions");
        if (res.ok) {
          const loadedHistory: ChatSession[] = await res.json();
          setHistory(loadedHistory);
          
          if (loadedHistory.length > 0) {
            // Load the most recent session
            const active = loadedHistory[0];
            setSession(active.id);
            const msgRes = await fetch(`http://127.0.0.1:8000/api/sessions/${active.id}`);
            if (msgRes.ok) {
              const data = await msgRes.json();
              setMessages(data.messages);
            }
          } else {
            createNewSession([]);
          }
        }
      } catch (e) {
        console.error("Failed to load history from DB", e);
        createNewSession([]);
      }
    }
    loadData();
  }, []);

  const createNewSession = (currentHistory: ChatSession[] = history) => {
    const newSessionId = "web-" + Math.random().toString(36).substring(7);
    const initialMsg: Message = {
      id: Date.now().toString(),
      role: "assistant",
      content: "Namaskaram! I am Vozhi, India’s Intelligent Benefits Orchestrator. How can I help you discover and unlock government schemes today?",
    };
    
    // Set locally
    const newSession: ChatSession = {
      id: newSessionId,
      title: "New Conversation",
      messages: [initialMsg],
      updatedAt: Date.now()
    };
    
    setHistory([newSession, ...currentHistory]);
    setSession(newSessionId);
    setMessages([initialMsg]);
    
    // Save to DB
    fetch("http://127.0.0.1:8000/api/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: newSessionId, title: "New Conversation", messages: [initialMsg] })
    }).catch(console.error);
  };

  // Sync active chat history to Database when messages change
  useEffect(() => {
    if (session && messages.length > 0) {
      // Pick title from the first human message
      const firstUser = messages.find(m => m.role === "user");
      const newTitle = firstUser ? (firstUser.content.length > 25 ? firstUser.content.substring(0, 25) + "..." : firstUser.content) : "New Conversation";
      
      // Update local history array for Sidebar immediately
      setHistory(prev => prev.map(h => h.id === session ? { ...h, updatedAt: Date.now(), title: newTitle } : h));

      // Push to DB
      fetch("http://127.0.0.1:8000/api/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: session, title: newTitle, messages: messages })
      }).catch(console.error);
    }
  }, [messages, session]);
  
  const [activeTab, setActiveTab] = useState<"home" | "chat">("chat");
  const [dragActive, setDragActive] = useState(false);
  const [uploadedDoc, setUploadedDoc] = useState<File | null>(null);

  // Modals state
  const [showWhatsApp, setShowWhatsApp] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const startNewChat = () => {
    createNewSession();
    setActiveTab("chat");
  };

  const loadChat = async (chatId: string) => {
    setSession(chatId);
    setActiveTab("chat");
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/sessions/${chatId}`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages);
      }
    } catch (e) {
      console.error("Failed to load chat", e);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() && !uploadedDoc) return;
    
    const userMsg: Message = { id: Date.now().toString(), role: "user", content: input || `(Uploaded Document: ${uploadedDoc?.name})` };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    
    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg.content, session_id: session })
      });
      if (!res.ok) throw new Error("API Error");
      
      const data = await res.json();
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: "assistant",
        content: data.answer,
        matches: data.matches,
        confidence: data.confidence,
        citations: data.matches?.map((m: any) => m.scheme_name) || []
      }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: "assistant",
        content: "Sorry, I am having trouble connecting to the Vozhi Orchestrator right now."
      }]);
    } finally {
      setLoading(false);
      setUploadedDoc(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen w-full bg-white text-zinc-900 font-sans overflow-hidden">
      
      {/* Sidebar - Matching Sarvam style */}
      <aside className="w-64 border-r border-zinc-200 bg-[#f9f9f9] flex flex-col hidden md:flex shrink-0">
        <div className="px-6 py-5 border-b border-zinc-200 flex items-center justify-between">
            <h1 className="text-xl font-bold tracking-tight text-zinc-900 font-sans flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-zinc-800" />
              vozhi
            </h1>
        </div>
        
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-8">
          
          <div className="space-y-1">
             <button 
                onClick={() => setActiveTab("home")}
                className={`flex items-center gap-3 w-full px-3 py-2 text-sm font-medium rounded-md transition-colors text-left ${activeTab === "home" ? "bg-zinc-200/60 text-zinc-900" : "text-zinc-600 hover:bg-zinc-200/50"}`}
             >
                <Home className="w-4 h-4" /> Home
             </button>
          </div>

          <div className="flex flex-col flex-1 min-h-0">
             <h3 className="px-3 pb-2 text-[11px] font-medium text-zinc-500 uppercase tracking-widest">Recent Chats</h3>
             <div className="space-y-1 mt-1 overflow-y-auto custom-scrollbar flex-1 pb-4">
               {history.sort((a,b) => b.updatedAt - a.updatedAt).map(chat => (
                 <button 
                    key={chat.id}
                    onClick={() => loadChat(chat.id)}
                    className={`flex items-center gap-3 w-full px-3 py-2 text-sm font-medium rounded-md transition-colors text-left truncate ${
                      session === chat.id && activeTab === "chat" ? "bg-zinc-200/60 text-zinc-900" : "text-zinc-600 hover:bg-zinc-200/50"
                    }`}
                 >
                    <MessageSquare className="w-4 h-4 shrink-0" /> 
                    <span className="truncate">{chat.title}</span>
                 </button>
               ))}
               {history.length === 0 && (
                 <p className="text-xs text-zinc-400 px-3 py-2">No recent chats.</p>
               )}
             </div>
          </div>
        </div>

        <div className="p-4 border-t border-zinc-200 flex items-center gap-3">
           <div className="w-8 h-8 rounded-full bg-zinc-800 text-white flex items-center justify-center text-xs font-semibold">
              D
           </div>
           <span className="text-sm font-medium text-zinc-800">Dhina</span>
        </div>
      </aside>

      {/* Main Area */}
      <main className="flex-1 grid grid-rows-[auto_1fr] h-screen min-w-0 bg-white relative">
        
        {/* Header */}
        <header className="px-8 py-5 flex items-center justify-between border-b border-zinc-100 z-10 bg-white">
          <div>
            <h2 className="text-xl font-semibold text-zinc-800 tracking-tight">{activeTab === "home" ? "Welcome Home" : "Vozhi Assistant"}</h2>
            <p className="text-sm text-zinc-500 mt-0.5">{activeTab === "home" ? "Overview of Graph RAG capabilities and indexed schemes." : "Discover eligible schemes, upload documents securely, and chat in any language."}</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setShowWhatsApp(true)} className="text-sm rounded-lg h-9 font-medium shadow-sm flex items-center gap-2">
              <Share2 className="w-4 h-4" /> Try WhatsApp
            </Button>
            <Button variant="outline" onClick={startNewChat} className="text-sm rounded-lg h-9 font-medium shadow-sm flex items-center gap-2">
              + New Chat
            </Button>
            <Button variant="ghost" onClick={() => setShowSettings(true)} size="icon" className="h-9 w-9 text-zinc-500 rounded-lg hover:bg-zinc-100">
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </header>

        {activeTab === "home" ? (
          <div className="w-full h-full overflow-y-auto p-8 sm:p-12">
            <div className="max-w-4xl mx-auto space-y-8">
              
              <div className="bg-gradient-to-br from-zinc-900 to-zinc-800 rounded-3xl p-10 text-white shadow-xl">
                <h1 className="text-3xl font-bold tracking-tight mb-3">Welcome to Vozhi.</h1>
                <p className="text-zinc-300 max-w-2xl leading-relaxed text-lg mb-8">
                  India’s first Intelligent Government Benefits Orchestrator powered by Graph RAG and Multi-Agent architecture. Vozhi turns natural voice/text queries into verified, bundled actionable benefits.
                </p>
                <div className="flex gap-4">
                  <Button onClick={startNewChat} className="bg-white text-zinc-900 hover:bg-zinc-100 rounded-xl px-6 h-11 font-medium shadow-sm border-0">
                    <MessageSquare className="w-4 h-4 mr-2" /> Start Chat
                  </Button>
                  <Button variant="outline" onClick={() => setShowSettings(true)} className="border-zinc-600 text-white hover:bg-zinc-800 rounded-xl px-6 h-11 font-medium bg-transparent">
                    View Architecture
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white border border-zinc-200 rounded-2xl p-6 shadow-sm">
                   <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center mb-4">
                     <FileText className="w-5 h-5 text-blue-600" />
                   </div>
                   <h3 className="font-bold text-zinc-800 tracking-tight mb-2">Graph RAG Engine</h3>
                   <p className="text-sm text-zinc-500 leading-relaxed">
                     LlamaIndex PropertyGraph analyzes complex interdependencies between state and central schemes, creating perfectly tailored eligibility bundles.
                   </p>
                </div>
                
                <div className="bg-white border border-zinc-200 rounded-2xl p-6 shadow-sm">
                   <div className="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center mb-4">
                     <Headphones className="w-5 h-5 text-purple-600" />
                   </div>
                   <h3 className="font-bold text-zinc-800 tracking-tight mb-2">Omnichannel Voice</h3>
                   <p className="text-sm text-zinc-500 leading-relaxed">
                     Integrated with Sarvam AI and Twilio WhatsApp to ensure rural access. Speak in any Indian language and get native audio responses.
                   </p>
                </div>

                <div className="bg-white border border-zinc-200 rounded-2xl p-6 shadow-sm">
                   <div className="w-10 h-10 rounded-xl bg-green-50 flex items-center justify-center mb-4">
                     <ImageIcon className="w-5 h-5 text-green-600" />
                   </div>
                   <h3 className="font-bold text-zinc-800 tracking-tight mb-2">Document Intelligence</h3>
                   <p className="text-sm text-zinc-500 leading-relaxed">
                     Upload Aadhaar or Income Certificates. EasyOCR and Llama 3.2 Vision instantly extract exact demographic entities to prove eligibility.
                   </p>
                </div>
              </div>

              <div className="mt-8 border border-zinc-200 rounded-2xl overflow-hidden shadow-sm">
                <div className="bg-zinc-50 px-6 py-4 border-b border-zinc-200 flex justify-between items-center">
                  <h3 className="font-bold text-zinc-800 tracking-tight">System Status</h3>
                  <div className="flex items-center gap-2 text-xs font-semibold text-green-600 bg-green-50 px-2 py-1 rounded-md">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    ALL SYSTEMS OPERATIONAL
                  </div>
                </div>
                <div className="p-6 bg-white grid grid-cols-2 md:grid-cols-4 gap-6 divide-x divide-zinc-100">
                   <div className="px-4">
                      <p className="text-xs font-semibold text-zinc-400 uppercase tracking-widest mb-1">Knowledge Nodes</p>
                      <p className="text-2xl font-bold text-zinc-800 font-mono">1,402</p>
                   </div>
                   <div className="px-6">
                      <p className="text-xs font-semibold text-zinc-400 uppercase tracking-widest mb-1">Synergy Edges</p>
                      <p className="text-2xl font-bold text-zinc-800 font-mono">859</p>
                   </div>
                   <div className="px-6">
                      <p className="text-xs font-semibold text-zinc-400 uppercase tracking-widest mb-1">LangGraph Agents</p>
                      <p className="text-2xl font-bold text-zinc-800 font-mono">4 Active</p>
                   </div>
                   <div className="px-6">
                      <p className="text-xs font-semibold text-zinc-400 uppercase tracking-widest mb-1">Inference Engine</p>
                      <p className="text-2xl font-bold text-zinc-800">Groq</p>
                   </div>
                </div>
              </div>

            </div>
          </div>
        ) : (
          <>
            {/* Chat Scroll Container */}
            <div className="w-full h-full overflow-y-auto pb-40 px-4 sm:px-8 pt-8 custom-scrollbar">
              <div className="max-w-[760px] mx-auto space-y-8 pb-10">
                {messages.map((m) => (
                  <div key={m.id} className="w-full flex">
                    {m.role === 'assistant' ? (
                      <div className="flex flex-col w-full">
                         <div className="flex items-center gap-2 text-zinc-500 mb-2 font-medium text-[13px]">
                            <Bot className="w-4 h-4 text-zinc-600" />
                            <span>Vozhi Assistant</span>
                            {m.confidence && (
                                <>
                                  <span className="text-zinc-300 mx-1">|</span>
                                  <span className="text-green-600 flex items-center gap-1.5 font-mono text-[11px] tracking-tight">
                                    <ShieldCheck className="w-3.5 h-3.5" /> Faithfulness: {m.confidence.toFixed(1)}%
                                  </span>
                                </>
                            )}
                         </div>
                         <div className="prose prose-sm max-w-none text-zinc-800 leading-relaxed font-sans whitespace-pre-wrap ml-6">
                            {m.content}
                         </div>
                         {m.citations && m.citations.length > 0 && (
                            <div className="mt-4 ml-6 space-y-1.5">
                               {m.citations.slice(0, 3).map((cite, i) => (
                                 <div key={i} className="text-xs bg-zinc-50 border border-zinc-200 px-3 py-1.5 rounded-md flex items-start gap-2 max-w-fit shadow-sm text-zinc-600">
                                   <span className="text-zinc-400 font-mono">[{i+1}]</span> {cite}
                                 </div>
                               ))}
                            </div>
                         )}
                      </div>
                    ) : (
                      <div className="flex justify-end w-full">
                          <div className="bg-[#f0f0f0] text-zinc-800 px-4 py-2.5 rounded-2xl rounded-br-sm text-[14.5px] max-w-[80%] leading-relaxed shadow-sm">
                            <p className="whitespace-pre-wrap">{m.content}</p>
                          </div>
                      </div>
                    )}
                  </div>
                ))}
                
                {loading && (
                  <div className="flex gap-4 justify-start">
                      <div className="flex flex-col w-full">
                         <div className="flex items-center gap-2 text-zinc-500 mb-2 font-medium text-[13px]">
                            <Bot className="w-4 h-4 animate-pulse text-zinc-600" />
                            <span>Executing LangGraph nodes...</span>
                         </div>
                         <div className="ml-6 py-2">
                            <Loader2 className="w-5 h-5 animate-spin text-zinc-300" />
                         </div>
                      </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Floating Input Area exactly like Sarvam */}
            <div className="absolute bottom-6 left-0 w-full flex justify-center z-20 pointer-events-none px-4">
              <div className="w-full max-w-[760px] pointer-events-auto bg-white border border-zinc-200 rounded-2xl shadow-lg ring-1 ring-zinc-100 min-h-[56px] flex flex-col items-center">
                
                {/* Document Preview inside input */}
                {uploadedDoc && (
                  <div className="w-full px-4 pt-3 pb-1 flex items-center justify-between border-b border-zinc-100">
                    <span className="text-xs font-semibold text-zinc-600 flex items-center gap-1.5 bg-zinc-100 px-2 py-1 rounded-md">
                      <FileText className="w-3.5 h-3.5 text-blue-600" /> {uploadedDoc.name}
                    </span>
                    <button onClick={() => setUploadedDoc(null)} className="text-[11px] font-semibold text-red-500 hover:text-red-700 uppercase tracking-widest">Remove</button>
                  </div>
                )}

                <div className="flex items-end w-full p-2 gap-2 relative">
                  
                  <div className="flex shrink-0 pl-1 pb-1">
                     <Button variant="ghost" size="icon" className="rounded-full w-8 h-8 text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 relative">
                        <input type="file" className="absolute inset-0 opacity-0 cursor-pointer" onChange={(e) => e.target.files && setUploadedDoc(e.target.files[0])} />
                        <Paperclip className="w-4 h-4" />
                     </Button>
                  </div>

                  <Textarea 
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="What's on your mind? Type a query or upload an Aadhaar card..."
                    className="flex-1 w-full border-0 focus-visible:ring-0 resize-none min-h-[40px] max-h-[160px] py-2.5 px-0 text-[14px] text-zinc-800 placeholder:text-zinc-400 bg-transparent shadow-none focus:outline-none focus:ring-0"
                    rows={1}
                  />
                  
                  <div className="flex shrink-0 pb-1 pr-1">
                    <Button 
                      onClick={handleSend}
                      disabled={loading || (!input.trim() && !uploadedDoc)}
                      size="icon" 
                      className="rounded-full w-8 h-8 bg-zinc-600 hover:bg-zinc-800 text-white transition-all disabled:opacity-30 disabled:hover:bg-zinc-600"
                    >
                      <ArrowUp className="w-4 h-4" />
                    </Button>
                  </div>

                </div>
              </div>
            </div>
          </>
        )}
      </main>

      {/* WhatsApp Modal */}
      <Dialog open={showWhatsApp} onOpenChange={setShowWhatsApp}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Try Vozhi on WhatsApp</DialogTitle>
            <DialogDescription>
              Experience the power of Vozhi through Twilio WhatsApp. You can send voice notes or text anywhere in India.
            </DialogDescription>
          </DialogHeader>
          <div className="bg-zinc-100 p-4 rounded-xl space-y-3 mt-4">
            <p className="text-sm text-zinc-700">1. Open your WhatsApp application.</p>
            <p className="text-sm text-zinc-700">2. Send <span className="font-mono bg-zinc-200 px-1 py-0.5 rounded text-xs select-all">join familiar-metal</span> to <span className="font-mono bg-zinc-200 px-1 py-0.5 rounded text-xs">+1 415 523 8886</span></p>
            <p className="text-sm text-zinc-700">3. Ask a question like <em>"I am a farmer from Bengal, what schemes am I eligible for?"</em></p>
          </div>
          <div className="flex justify-end mt-4">
            <Button onClick={() => setShowWhatsApp(false)}>Done</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Settings / Architecture Modal */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Vozhi System Architecture</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex justify-between items-center text-sm border-b pb-2">
              <span className="font-medium">Orchestrator Node</span>
              <span className="text-zinc-500 font-mono text-xs">LangGraph v1.x</span>
            </div>
            <div className="flex justify-between items-center text-sm border-b pb-2">
              <span className="font-medium">Inference Engine</span>
              <span className="text-zinc-500 font-mono text-xs">llama-3.1-8b (Groq)</span>
            </div>
            <div className="flex justify-between items-center text-sm border-b pb-2">
              <span className="font-medium">Graph Synergy Store</span>
              <span className="text-zinc-500 font-mono text-xs">LlamaIndex PropertyGraph</span>
            </div>
            <div className="flex justify-between items-center text-sm border-b pb-2">
              <span className="font-medium">Vector Store</span>
              <span className="text-zinc-500 font-mono text-xs">Qdrant Local</span>
            </div>
            <div className="flex justify-between items-center text-sm border-b pb-2">
              <span className="font-medium">Vision Extractor</span>
              <span className="text-zinc-500 font-mono text-xs">llama-3.2-11b-vision / EasyOCR</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="font-medium">STT / TTS Provider</span>
              <span className="text-zinc-500 font-mono text-xs">Sarvam AI</span>
            </div>
          </div>
          <div className="flex justify-end mt-4">
            <Button onClick={() => setShowSettings(false)}>Close</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
