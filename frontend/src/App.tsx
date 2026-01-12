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

  const {
    messages,
    isLoading: queryLoading,
    sendQuery,
    clearMessages,
    setMessages,
  } = useQuery();

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
    let convId = activeConversation?.id;

    // If no active conversation, create one first
    if (!convId) {
      const newConv = await createConversation();
      if (newConv) {
        convId = newConv.id;
      }
    }

    // Send query with the conversation ID
    await sendQuery(question, convId);

    // Refresh conversations list to update preview/timestamp
    loadConversations();

    // Refresh active conversation to get the new messages
    if (convId) {
      loadConversation(convId);
    }
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
