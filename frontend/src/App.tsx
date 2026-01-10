import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { useHealth } from './hooks/useHealth';
import { useDocuments } from './hooks/useDocuments';
import { useQuery } from './hooks/useQuery';

function App() {
  const health = useHealth();
  const { documents, isLoading: docsLoading, upload, remove, reset } = useDocuments();
  const { messages, isLoading: queryLoading, sendQuery, clearMessages } = useQuery();

  const handleReset = async () => {
    await reset();
    clearMessages();
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Header health={health} />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          documents={documents}
          isLoading={docsLoading}
          onUpload={async (file) => {
            await upload(file);
          }}
          onDelete={remove}
          onReset={handleReset}
        />

        <ChatArea
          messages={messages}
          isLoading={queryLoading}
          onSendMessage={sendQuery}
          hasDocuments={documents.length > 0}
        />
      </div>
    </div>
  );
}

export default App;
