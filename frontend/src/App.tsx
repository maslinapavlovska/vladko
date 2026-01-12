import { useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ConversationList } from './components/ConversationList';
import { useHealth } from './hooks/useHealth';
import { useDocuments } from './hooks/useDocuments';
import { useQuery } from './hooks/useQuery';
import { useStreamingQuery } from './hooks/useStreamingQuery';
import { useConversations } from './hooks/useConversations';
import type { Message } from './types';

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

  // Streaming query hook
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

  // Load messages when active conversation changes
  useEffect(() => {
    if (activeConversation?.messages) {
      setMessages(activeConversation.messages);
    } else {
      clearMessages();
    }
    // Reset streaming state when conversation changes
    resetStreamState();
  }, [activeConversation, setMessages, clearMessages, resetStreamState]);

  // Track if we've already processed the completed stream
  const hasProcessedCompletion = useRef(false);

  // When streaming completes, add the message to the list and refresh
  useEffect(() => {
    if (!isStreaming && partialAnswer && streamStatus?.stage === 'complete' && !hasProcessedCompletion.current) {
      hasProcessedCompletion.current = true;

      // Create a new message from the streamed response
      const newMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: partialAnswer,
        citations: streamCitations || undefined,
        reasoning: streamReasoning || undefined,
      };

      setMessages((prev: Message[]) => [...prev, newMessage]);

      // Delay reset to allow smooth transition
      setTimeout(() => {
        resetStreamState();
        hasProcessedCompletion.current = false;
      }, 100);

      // Refresh conversations and active conversation
      loadConversations();
      if (activeConversation?.id) {
        loadConversation(activeConversation.id);
      }
    }
  }, [isStreaming, partialAnswer, streamStatus, streamCitations, streamReasoning, setMessages, resetStreamState, loadConversations, loadConversation, activeConversation?.id]);

  // Reset the completion flag when starting a new stream
  useEffect(() => {
    if (isStreaming) {
      hasProcessedCompletion.current = false;
    }
  }, [isStreaming]);

  const handleReset = async () => {
    await reset();
    clearMessages();
    clearActive();
    resetStreamState();
  };

  const handleNewChat = async () => {
    // Create a new conversation
    await createConversation();
    resetStreamState();
  };

  const handleSelectConversation = async (id: string) => {
    await loadConversation(id);
    resetStreamState();
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

    // Add user message to local state immediately
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
    };
    setMessages((prev: Message[]) => [...prev, userMessage]);

    // Send streaming query with the conversation ID
    await sendStreamingQuery(question, convId);
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
          isStreaming={isStreaming}
          streamStatus={streamStatus}
          partialAnswer={partialAnswer}
          streamCitations={streamCitations}
          optionsValidation={optionsValidation}
        />
      </div>
    </div>
  );
}

export default App;
