import { useEffect } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ConversationList } from './components/ConversationList';
import { useHealth } from './hooks/useHealth';
import { useDocuments } from './hooks/useDocuments';
import { useQuery } from './hooks/useQuery';
import { useConversations } from './hooks/useConversations';

function App() {
  const health = useHealth();
  const { documents, isLoading: docsLoading, upload, remove, reset } = useDocuments();
  const {
    conversations,
    activeConversation,
    isLoading: convsLoading,
    loadConversation,
    create: createConversation,
    update: updateConversation,
    remove: removeConversation,
    clearActive,
    loadConversations,
  } = useConversations();

  // Pass active conversation ID to useQuery
  const {
    messages,
    isLoading: queryLoading,
    sendQuery,
    clearMessages,
    setMessages,
  } = useQuery(activeConversation?.id);

  // Load messages when active conversation changes
  useEffect(() => {
    if (activeConversation?.messages) {
      setMessages(activeConversation.messages);
    } else {
      clearMessages();
    }
  }, [activeConversation, setMessages, clearMessages]);

  const handleReset = async () => {
    await reset();
    clearMessages();
    clearActive();
  };

  const handleNewChat = async () => {
    // Create a new conversation
    await createConversation();
  };

  const handleSelectConversation = async (id: string) => {
    await loadConversation(id);
  };

  const handleSendMessage = async (question: string) => {
    // If no active conversation, create one first
    if (!activeConversation) {
      const newConv = await createConversation();
      if (newConv) {
        // Need to wait for state to update, then send
        // The useQuery hook will pick up the new conversation ID
        setTimeout(() => sendQuery(question), 100);
        return;
      }
    }
    await sendQuery(question);
    // Refresh conversations list to update preview/timestamp
    loadConversations();
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Header health={health} />

      <div className="flex-1 flex overflow-hidden">
        {/* Conversation List - Left sidebar */}
        <ConversationList
          conversations={conversations}
          activeConversation={activeConversation}
          isLoading={convsLoading}
          onSelect={handleSelectConversation}
          onCreate={createConversation}
          onDelete={removeConversation}
          onRename={updateConversation}
          onNewChat={handleNewChat}
        />

        {/* Documents Sidebar */}
        <Sidebar
          documents={documents}
          isLoading={docsLoading}
          onUpload={async (file) => {
            await upload(file);
          }}
          onDelete={remove}
          onReset={handleReset}
        />

        {/* Chat Area */}
        <ChatArea
          messages={messages}
          isLoading={queryLoading}
          onSendMessage={handleSendMessage}
          hasDocuments={documents.length > 0}
        />
      </div>
    </div>
  );
}

export default App;
