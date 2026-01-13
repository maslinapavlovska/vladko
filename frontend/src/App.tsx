import { useState, useEffect, useRef } from 'react';
import { useHealth } from './hooks/useHealth';
import { useDocuments } from './hooks/useDocuments';
import { useQuery } from './hooks/useQuery';
import { useStreamingQuery } from './hooks/useStreamingQuery';
import { useConversations } from './hooks/useConversations';
import { useConversationSearch } from './hooks/useConversationSearch';
import { useProjects } from './hooks/useProjects';
import type { Message, Chat, ChatSearchResult, Project, Document } from './types';

// Icons
const Icons = {
  Sparkles: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
    </svg>
  ),
  Message: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>
    </svg>
  ),
  File: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/>
    </svg>
  ),
  Plus: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 5v14M5 12h14"/>
    </svg>
  ),
  Send: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m22 2-7 20-4-9-9-4 20-7z"/><path d="m22 2-11 11"/>
    </svg>
  ),
  Upload: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>
    </svg>
  ),
  Trash: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
    </svg>
  ),
  User: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
    </svg>
  ),
  Check: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6 9 17l-5-5"/>
    </svg>
  ),
  ChevronDown: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m6 9 6 6 6-6"/>
    </svg>
  ),
  Brain: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>
      <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/>
    </svg>
  ),
  Search: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
    </svg>
  ),
  X: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
    </svg>
  ),
  Loader: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="animate-spin">
      <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
    </svg>
  ),
  Folder: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>
    </svg>
  ),
};

// Typing indicator
const TypingIndicator = () => (
  <div className="typing-indicator">
    <span></span>
    <span></span>
    <span></span>
  </div>
);

// Status dot
const StatusDot = ({ status }: { status: 'online' | 'offline' }) => (
  <div className={`status-dot ${status}`}></div>
);

function App() {
  const health = useHealth();

  // Projects
  const {
    projects,
    activeProject,
    setActiveProjectId,
    createProject,
    deleteProject,
  } = useProjects();

  const activeProjectId = activeProject?.id || null;

  // Documents (per project)
  const { documents, isLoading: docsLoading, upload, remove: removeDocument } = useDocuments(activeProjectId);

  // Conversations (per project)
  const {
    conversations,
    activeConversation,
    isLoading: convsLoading,
    loadConversation,
    create: createConversation,
    remove: removeConversation,
    clearActive,
    loadConversations,
  } = useConversations(activeProjectId);

  const {
    messages,
    isLoading: queryLoading,
    clearMessages,
    setMessages,
  } = useQuery();

  const {
    isStreaming,
    status: streamStatus,
    partialAnswer,
    citations: streamCitations,
    reasoning: streamReasoning,
    optionsValidation,
    sendQuery: sendStreamingQuery,
    resetState: resetStreamState,
  } = useStreamingQuery();

  const {
    query: searchQuery,
    setQuery: setSearchQuery,
    results: searchResults,
    isSearching,
    isActive: isSearchActive,
    clearSearch,
  } = useConversationSearch(activeProjectId);

  const [activeTab, setActiveTab] = useState<'chats' | 'docs'>('chats');
  const [inputValue, setInputValue] = useState('');
  const [showSources, setShowSources] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [showProjectSelector, setShowProjectSelector] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const hasProcessedCompletion = useRef(false);
  const skipNextConversationEffect = useRef(false);

  // Auto-select project with documents, or first project
  useEffect(() => {
    if (!activeProjectId && projects.length > 0) {
      // Prefer a project that has documents
      const projectWithDocs = projects.find((p: Project) => (p.document_count || 0) > 0);
      if (projectWithDocs) {
        setActiveProjectId(projectWithDocs.id);
      } else {
        setActiveProjectId(projects[0].id);
      }
    }
  }, [projects, activeProjectId, setActiveProjectId]);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, partialAnswer]);

  // Load messages when active conversation changes
  useEffect(() => {
    if (skipNextConversationEffect.current) {
      skipNextConversationEffect.current = false;
      return;
    }
    if (activeConversation?.messages) {
      setMessages(activeConversation.messages);
    } else {
      clearMessages();
    }
    resetStreamState();
  }, [activeConversation, setMessages, clearMessages, resetStreamState]);

  // Handle streaming completion
  useEffect(() => {
    if (!isStreaming && partialAnswer && streamStatus?.stage === 'complete' && !hasProcessedCompletion.current) {
      hasProcessedCompletion.current = true;

      const newMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: partialAnswer,
        citations: streamCitations || undefined,
        reasoning: streamReasoning || undefined,
      };

      setMessages((prev: Message[]) => [...prev, newMessage]);

      setTimeout(() => {
        resetStreamState();
        hasProcessedCompletion.current = false;
      }, 100);

      loadConversations();
      if (activeConversation?.id) {
        loadConversation(activeConversation.id);
      }
    }
  }, [isStreaming, partialAnswer, streamStatus, streamCitations, streamReasoning, setMessages, resetStreamState, loadConversations, loadConversation, activeConversation?.id]);

  useEffect(() => {
    if (isStreaming) {
      hasProcessedCompletion.current = false;
    }
  }, [isStreaming]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isStreaming || !activeProjectId) return;

    let convId = activeConversation?.id;

    if (!convId) {
      skipNextConversationEffect.current = true;
      const newConv = await createConversation();
      if (newConv) {
        convId = newConv.id;
      }
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
    };
    setMessages((prev: Message[]) => [...prev, userMessage]);
    setInputValue('');

    await sendStreamingQuery(inputValue, convId, activeProjectId);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleNewChat = async () => {
    await createConversation();
    resetStreamState();
    clearSearch();
  };

  const handleSelectConversation = async (id: string) => {
    await loadConversation(id);
    resetStreamState();
    clearSearch();
  };

  const handleFileUpload = async (file: File) => {
    await upload(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file?.type === 'application/pdf') {
      handleFileUpload(file);
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    const project = await createProject(newProjectName.trim());
    setActiveProjectId(project.id);
    setNewProjectName('');
    setShowProjectSelector(false);
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  const isBusy = isStreaming || queryLoading;

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        {/* Header */}
        <div style={{ padding: '20px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <div
            className="logo"
            style={{ marginBottom: '20px', cursor: 'pointer' }}
            onClick={() => { clearActive(); clearMessages(); resetStreamState(); clearSearch(); }}
          >
            <div className="logo-icon">
              <Icons.Sparkles />
            </div>
            <span className="logo-text">Vladko</span>
          </div>

          {/* Project Selector */}
          <div style={{ marginBottom: '16px', position: 'relative' }}>
            <button
              onClick={() => setShowProjectSelector(!showProjectSelector)}
              style={{
                width: '100%',
                padding: '10px 12px',
                background: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '13px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Icons.Folder />
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {activeProject?.name || 'Select Project'}
                </span>
              </div>
              <Icons.ChevronDown />
            </button>

            {showProjectSelector && (
              <div style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                marginTop: '4px',
                background: '#1a1a2e',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                zIndex: 100,
                maxHeight: '300px',
                overflowY: 'auto',
              }}>
                {projects.map((project: Project) => (
                  <div
                    key={project.id}
                    onClick={() => {
                      setActiveProjectId(project.id);
                      setShowProjectSelector(false);
                    }}
                    style={{
                      padding: '10px 12px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: project.id === activeProjectId ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                      borderBottom: '1px solid rgba(255,255,255,0.05)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: project.color }} />
                      <span style={{ color: '#fff', fontSize: '13px' }}>{project.name}</span>
                    </div>
                    <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)' }}>
                      {project.document_count || 0} docs
                    </span>
                  </div>
                ))}
                <div style={{ padding: '8px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                  <input
                    type="text"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    placeholder="New project name..."
                    onKeyDown={(e) => e.key === 'Enter' && handleCreateProject()}
                    style={{
                      width: '100%',
                      padding: '8px',
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '6px',
                      color: '#fff',
                      fontSize: '13px',
                      outline: 'none',
                      marginBottom: '8px',
                    }}
                  />
                  <button
                    onClick={handleCreateProject}
                    disabled={!newProjectName.trim()}
                    style={{
                      width: '100%',
                      padding: '8px',
                      background: newProjectName.trim() ? 'rgba(99, 102, 241, 0.3)' : 'rgba(255,255,255,0.05)',
                      border: 'none',
                      borderRadius: '6px',
                      color: newProjectName.trim() ? '#fff' : 'rgba(255,255,255,0.3)',
                      fontSize: '13px',
                      cursor: newProjectName.trim() ? 'pointer' : 'not-allowed',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                    }}
                  >
                    <Icons.Plus />
                    Create Project
                  </button>
                </div>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>
              <StatusDot status={health.api === 'ok' ? 'online' : 'offline'} />
              <span>API</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>
              <StatusDot status={health.ollama === 'ok' ? 'online' : 'offline'} />
              <span>Ollama</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', padding: '12px', gap: '4px', background: 'rgba(0,0,0,0.2)' }}>
          <button className={`tab ${activeTab === 'chats' ? 'active' : ''}`} onClick={() => setActiveTab('chats')}>
            <Icons.Message />
            Chats
            <span style={{ background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '10px', fontSize: '11px' }}>
              {conversations.length}
            </span>
          </button>
          <button className={`tab ${activeTab === 'docs' ? 'active' : ''}`} onClick={() => setActiveTab('docs')}>
            <Icons.File />
            Docs
            <span style={{ background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '10px', fontSize: '11px' }}>
              {documents.length}
            </span>
          </button>
        </div>

        {/* New Chat / Upload */}
        <div style={{ padding: '12px' }}>
          {activeTab === 'chats' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <button className="new-chat-btn" onClick={handleNewChat} disabled={!activeProjectId}>
                <Icons.Plus />
                New Chat
              </button>
              {/* Search bar */}
              <div style={{ position: 'relative' }}>
                <div style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)' }}>
                  <Icons.Search />
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search chats..."
                  disabled={!activeProjectId}
                  style={{
                    width: '100%',
                    padding: '8px 32px 8px 32px',
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '13px',
                    outline: 'none',
                  }}
                />
                {searchQuery && (
                  <button
                    onClick={clearSearch}
                    style={{
                      position: 'absolute',
                      right: '8px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      color: 'rgba(255,255,255,0.4)',
                      cursor: 'pointer',
                      padding: '2px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {isSearching ? <Icons.Loader /> : <Icons.X />}
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div
              className={`upload-zone ${dragOver ? 'dragover' : ''} ${!activeProjectId ? 'disabled' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={activeProjectId ? handleDrop : undefined}
              onClick={() => activeProjectId && fileInputRef.current?.click()}
              style={{ opacity: activeProjectId ? 1 : 0.5, cursor: activeProjectId ? 'pointer' : 'not-allowed' }}
            >
              <div style={{ color: 'rgba(255,255,255,0.3)', marginBottom: '8px' }}>
                <Icons.Upload />
              </div>
              <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)' }}>
                {activeProjectId ? 'Drop PDF or click to upload' : 'Select a project first'}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                style={{ display: 'none' }}
                onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
              />
            </div>
          )}
        </div>

        {/* List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
          {!activeProjectId ? (
            <div style={{ padding: '20px', textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>
              Select a project to get started
            </div>
          ) : activeTab === 'chats' ? (
            isSearchActive ? (
              // Search results
              <>
                {isSearching ? (
                  <div style={{ padding: '20px', textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>
                    Searching...
                  </div>
                ) : searchResults.length === 0 ? (
                  <div style={{ padding: '20px', textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>
                    No results found for "{searchQuery}"
                  </div>
                ) : (
                  <>
                    <div style={{ padding: '8px 12px', fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>
                      {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} for "{searchQuery}"
                    </div>
                    {searchResults.map((result: ChatSearchResult) => (
                      <div
                        key={result.id}
                        className={`list-item ${activeConversation?.id === result.id ? 'active' : ''}`}
                        onClick={() => handleSelectConversation(result.id)}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                          <div style={{ fontSize: '14px', fontWeight: 500, color: '#fff' }}>{result.title}</div>
                          <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)' }}>{formatTime(result.updated_at)}</span>
                        </div>
                        {result.matched_content && (
                          <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', background: 'rgba(99, 102, 241, 0.1)', padding: '4px 8px', borderRadius: '4px', marginTop: '4px' }}>
                            "{result.matched_content}"
                          </div>
                        )}
                      </div>
                    ))}
                  </>
                )}
              </>
            ) : conversations.length === 0 ? (
              <div style={{ padding: '20px', textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>
                No chats yet
              </div>
            ) : (
              conversations.map((conv: Chat) => (
                <div
                  key={conv.id}
                  className={`list-item ${activeConversation?.id === conv.id ? 'active' : ''}`}
                  onClick={() => handleSelectConversation(conv.id)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <div style={{ fontSize: '14px', fontWeight: 500, color: '#fff' }}>{conv.title}</div>
                    <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)' }}>{formatTime(conv.updated_at)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                      {conv.preview || 'No messages'}
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); removeConversation(conv.id); }}
                      style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.3)', cursor: 'pointer', padding: '4px' }}
                    >
                      <Icons.Trash />
                    </button>
                  </div>
                </div>
              ))
            )
          ) : (
            documents.length === 0 ? (
              <div style={{ padding: '20px', textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>
                No documents uploaded
              </div>
            ) : (
              documents.map((doc: Document) => (
                <div key={doc.id} className="list-item">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: '36px', height: '36px', background: 'linear-gradient(135deg, rgba(239,68,68,0.2) 0%, rgba(249,115,22,0.2) 100%)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f97316' }}>
                      <Icons.File />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '13px', fontWeight: 500, color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{doc.filename}</div>
                      <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)' }}>
                        {doc.page_count ? `${doc.page_count} pages` : ''} {doc.chunk_count ? `· ${doc.chunk_count} chunks` : ''}
                      </div>
                    </div>
                    <button
                      onClick={() => removeDocument(doc.id)}
                      style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.3)', cursor: 'pointer', padding: '4px' }}
                    >
                      <Icons.Trash />
                    </button>
                  </div>
                </div>
              ))
            )
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Header */}
        <header style={{ padding: '16px 24px', borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(0,0,0,0.2)' }}>
          <h1 style={{ fontSize: '16px', fontWeight: 600, color: '#fff' }}>
            {activeConversation?.title || 'New Chat'}
          </h1>
        </header>

        {/* Chat Area */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {messages.length === 0 && !isStreaming ? (
            <div className="empty-state">
              <div className="empty-icon">
                <Icons.Sparkles />
              </div>
              <div style={{ fontSize: '20px', fontWeight: 600, color: '#fff', marginBottom: '8px' }}>
                {!activeProjectId ? 'Select a project' : documents.length > 0 ? 'Ask a question' : 'Upload a document'}
              </div>
              <div style={{ fontSize: '14px', color: 'rgba(255,255,255,0.5)', maxWidth: '300px' }}>
                {!activeProjectId
                  ? 'Choose a project from the dropdown to get started'
                  : documents.length > 0
                  ? 'I can help you find information in your uploaded documents'
                  : 'Upload a PDF document to get started'}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div key={msg.id} className={`message ${msg.role}`}>
                  <div className="message-avatar">
                    {msg.role === 'user' ? <Icons.User /> : <Icons.Sparkles />}
                  </div>
                  <div className="message-bubble" style={{ whiteSpace: 'pre-wrap' }}>
                    {msg.content}
                    {msg.role === 'assistant' && msg.reasoning?.justification && (
                      <div className={`confidence-badge ${msg.reasoning.justification.confidence?.toLowerCase() || 'low'}`}>
                        <Icons.Check />
                        {msg.reasoning.justification.confidence || 'LOW'} Confidence
                      </div>
                    )}
                    {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                      <>
                        <button
                          className="sources-toggle"
                          onClick={() => setShowSources(showSources === msg.id ? null : msg.id)}
                        >
                          <Icons.File />
                          {msg.citations.length} source{msg.citations.length !== 1 ? 's' : ''}
                          <Icons.ChevronDown />
                        </button>
                        {showSources === msg.id && (
                          <div className="sources-list">
                            {msg.citations.map((cit, i) => (
                              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px', borderRadius: '6px' }}>
                                <div style={{ width: '28px', height: '28px', background: 'rgba(249,115,22,0.2)', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f97316' }}>
                                  <Icons.File />
                                </div>
                                <div style={{ fontSize: '12px' }}>
                                  <div style={{ color: '#fff', fontWeight: 500 }}>{cit.filename}</div>
                                  <div style={{ color: 'rgba(255,255,255,0.5)' }}>Page {cit.page}</div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              ))}

              {/* Streaming Status */}
              {isStreaming && streamStatus && !partialAnswer && (
                <div className="message assistant">
                  <div className="message-avatar" style={{ background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)' }}>
                    <Icons.Sparkles />
                  </div>
                  <div className="thinking-bubble">
                    <span className="thinking-icon"><Icons.Brain /></span>
                    {streamStatus.message}
                    <TypingIndicator />
                  </div>
                </div>
              )}

              {/* Streaming Response */}
              {partialAnswer && (
                <div className="message assistant">
                  <div className="message-avatar">
                    <Icons.Sparkles />
                  </div>
                  <div style={{ maxWidth: '70%' }}>
                    <div className="message-bubble" style={{ whiteSpace: 'pre-wrap' }}>
                      {partialAnswer}
                      {isStreaming && <span style={{ display: 'inline-block', width: '8px', height: '16px', background: 'rgba(255,255,255,0.5)', marginLeft: '2px', animation: 'pulse 1s infinite' }}></span>}
                    </div>
                    {streamCitations && streamCitations.length > 0 && (
                      <div style={{ marginTop: '8px', fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>
                        Sources: {streamCitations.map(c => `${c.filename} p.${c.page}`).join(', ')}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div style={{ padding: '20px 24px', borderTop: '1px solid rgba(255,255,255,0.06)', background: 'rgba(0,0,0,0.2)' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
            <div className="input-container">
              <textarea
                className="input-field"
                placeholder={!activeProjectId ? 'Select a project first...' : documents.length > 0 ? 'Ask a question about your documents...' : 'Upload a document first...'}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isBusy || documents.length === 0 || !activeProjectId}
                rows={1}
              />
            </div>
            <button
              className="send-btn"
              onClick={handleSendMessage}
              disabled={isBusy || !inputValue.trim() || documents.length === 0 || !activeProjectId}
            >
              <Icons.Send />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
