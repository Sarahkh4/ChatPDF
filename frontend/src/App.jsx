import { useEffect, useMemo, useRef, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import {
  FileUp,
  FileText,
  LogOut,
  Menu,
  MessageSquare,
  PanelLeftClose,
  Plus,
  Send,
  Trash2,
} from "lucide-react";

import { apiRequest, clearToken, getToken } from "./api.js";

const initialMessages = [
  {
    role: "assistant",
    content: "Upload a PDF in this chat, then ask a question about it.",
  },
];

export default function App() {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [messagesByChat, setMessagesByChat] = useState({});
  const [question, setQuestion] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isLoadingChats, setIsLoadingChats] = useState(true);
  const [isCreatingChat, setIsCreatingChat] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState("");
  const [isAnswering, setIsAnswering] = useState(false);
  const [error, setError] = useState("");

  const token = getToken();
  const activeMessages = useMemo(() => {
    if (!chatId) return initialMessages;
    return messagesByChat[chatId] || initialMessages;
  }, [chatId, messagesByChat]);

  useEffect(() => {
    if (!token) return;
    loadChats();
  }, [token]);

  useEffect(() => {
    if (!chatId || chats.length === 0) {
      setSelectedChat(null);
      setDocuments([]);
      return;
    }

    const chat = chats.find((item) => item.id === chatId);
    if (!chat) return;
    setSelectedChat(chat);
    loadChat(chatId);
  }, [chatId, chats]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeMessages, isAnswering]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  async function loadChats() {
    try {
      setError("");
      setIsLoadingChats(true);
      const data = await apiRequest("/chats");
      setChats(data.chats || []);

      if (!chatId && data.chats?.length) {
        navigate(`/chats/${data.chats[0].id}`, { replace: true });
      }
    } catch (err) {
      handleApiError(err);
    } finally {
      setIsLoadingChats(false);
    }
  }

  async function loadChat(id) {
    try {
      setError("");
      const data = await apiRequest(`/chats/${id}`);
      setSelectedChat(data.chat);
      setDocuments(data.documents || []);
      setMessagesByChat((current) => ({
        ...current,
        [id]: data.messages?.length ? data.messages : initialMessages,
      }));
    } catch (err) {
      handleApiError(err);
    }
  }

  async function createChat() {
    try {
      setError("");
      setIsCreatingChat(true);
      const data = await apiRequest("/chats", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title: "New chat" }),
      });
      setChats((current) => [data.chat, ...current]);
      navigate(`/chats/${data.chat.id}`);
    } catch (err) {
      handleApiError(err);
    } finally {
      setIsCreatingChat(false);
    }
  }

  async function uploadPdf(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || !chatId) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      setError("");
      setIsUploading(true);
      const data = await apiRequest(`/chats/${chatId}/upload`, {
        method: "POST",
        body: formData,
      });
      setDocuments((current) => {
        const exists = current.some((document) => document.id === data.document.id);
        return exists ? current : [data.document, ...current];
      });
      appendMessage(chatId, {
        role: "assistant",
        content: data.document.already_exists
          ? `${data.document.filename} is already attached to this chat.`
          : `Uploaded ${data.document.filename}. Ask me anything from this PDF.`,
      });
      await loadChats();
    } catch (err) {
      handleApiError(err);
    } finally {
      setIsUploading(false);
    }
  }

  async function deleteDocument(documentId) {
    if (!chatId || !documentId) return;

    try {
      setError("");
      setDeletingDocumentId(documentId);
      const deletedDocument = documents.find((document) => document.id === documentId);
      await apiRequest(`/chats/${chatId}/documents/${documentId}`, {
        method: "DELETE",
      });
      setDocuments((current) => current.filter((document) => document.id !== documentId));
      appendMessage(chatId, {
        role: "assistant",
        content: `${deletedDocument?.filename || "Document"} was deleted from this chat.`,
      });
      await loadChats();
    } catch (err) {
      handleApiError(err);
    } finally {
      setDeletingDocumentId("");
    }
  }

  async function askQuestion(event) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || !chatId || isAnswering) return;

    appendMessage(chatId, { role: "user", content: trimmedQuestion });
    setQuestion("");

    try {
      setError("");
      setIsAnswering(true);
      const data = await apiRequest(`/chats/${chatId}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: trimmedQuestion }),
      });
      appendMessage(chatId, {
        role: "assistant",
        content: data.final_answer || "I could not find an answer.",
      });
      await loadChats();
    } catch (err) {
      appendMessage(chatId, {
        role: "assistant",
        content: "I could not answer that request. Please try again.",
      });
      handleApiError(err);
    } finally {
      setIsAnswering(false);
    }
  }

  function appendMessage(id, message) {
    setMessagesByChat((current) => ({
      ...current,
      [id]: [...(current[id] || initialMessages), message],
    }));
  }

  function logout() {
    clearToken();
    navigate("/login", { replace: true });
  }

  function handleApiError(err) {
    if (err.status === 401 || err.message.toLowerCase().includes("credential")) {
      clearToken();
      navigate("/login", { replace: true });
      return;
    }
    setError(err.message);
  }

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100">
      <aside
        className={`${
          isSidebarOpen ? "w-72" : "w-0"
        } flex shrink-0 overflow-hidden border-r border-zinc-800 bg-zinc-900 transition-all duration-200 md:w-72`}
      >
        <div className="flex min-w-72 flex-col">
          <div className="flex h-16 items-center justify-between border-b border-zinc-800 px-4">
            <div>
              <p className="text-sm font-semibold text-white">ChatPDF</p>
              <p className="text-xs text-zinc-400">RAG workspace</p>
            </div>
            <button
              className="icon-button md:hidden"
              onClick={() => setIsSidebarOpen(false)}
              title="Close sidebar"
              type="button"
            >
              <PanelLeftClose size={18} />
            </button>
          </div>

          <div className="p-3">
            <button
              className="flex h-10 w-full items-center justify-center gap-2 rounded-md border border-zinc-700 bg-zinc-900 px-3 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isCreatingChat}
              onClick={createChat}
              type="button"
            >
              <Plus size={17} />
              {isCreatingChat ? "Creating..." : "New Chat"}
            </button>
          </div>

          <nav className="flex-1 overflow-y-auto px-2 pb-3">
            {isLoadingChats ? (
              <div className="px-3 py-2 text-sm text-zinc-400">Loading chats...</div>
            ) : chats.length === 0 ? (
              <div className="px-3 py-2 text-sm text-zinc-400">No chats yet</div>
            ) : (
              chats.map((chat) => (
                <button
                  className={`flex h-11 w-full items-center gap-3 rounded-md px-3 text-left text-sm transition ${
                    chat.id === chatId
                      ? "bg-zinc-800 text-white"
                      : "text-zinc-300 hover:bg-zinc-800/70"
                  }`}
                  key={chat.id}
                  onClick={() => navigate(`/chats/${chat.id}`)}
                  type="button"
                >
                  <MessageSquare size={16} className="shrink-0" />
                  <span className="min-w-0 flex-1 truncate">{chat.title || "New chat"}</span>
                  {chat.document_count > 0 && (
                    <span className="rounded bg-zinc-700 px-1.5 py-0.5 text-[11px] text-zinc-300">
                      {chat.document_count}
                    </span>
                  )}
                </button>
              ))
            )}
          </nav>

          <div className="border-t border-zinc-800 p-3">
            <button
              className="flex h-10 w-full items-center gap-2 rounded-md px-3 text-sm text-zinc-300 transition hover:bg-zinc-800 hover:text-white"
              onClick={logout}
              type="button"
            >
              <LogOut size={17} />
              Logout
            </button>
          </div>
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-zinc-800 bg-zinc-950 px-4">
          <div className="flex min-w-0 items-center gap-3">
            <button
              className="icon-button md:hidden"
              onClick={() => setIsSidebarOpen(true)}
              title="Open sidebar"
              type="button"
            >
              <Menu size={19} />
            </button>
            <div className="min-w-0">
              <h1 className="truncate text-base font-semibold text-white">
                {selectedChat?.title || "Select or create a chat"}
              </h1>
              <p className="truncate text-xs text-zinc-400">
                {documents.length
                  ? `${documents.length} PDF${documents.length === 1 ? "" : "s"} attached`
                  : "No PDF attached"}
              </p>
            </div>
          </div>

          <input
            accept="application/pdf"
            className="hidden"
            disabled={!chatId || isUploading}
            onChange={uploadPdf}
            ref={fileInputRef}
            type="file"
          />
        </header>

        {error && (
          <div className="border-b border-red-500/30 bg-red-950/60 px-4 py-3 text-sm text-red-100">
            {error}
          </div>
        )}

        <section className="flex-1 overflow-y-auto">
          {!chatId ? (
            <div className="mx-auto flex h-full max-w-2xl flex-col items-center justify-center px-6 text-center">
              <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-lg bg-zinc-900 text-emerald-400">
                <FileText size={28} />
              </div>
              <h2 className="text-2xl font-semibold text-white">Start a document chat</h2>
              <p className="mt-2 text-sm leading-6 text-zinc-400">
                Create a chat, upload a PDF, and ask questions from that document context.
              </p>
              <button
                className="mt-6 flex h-10 items-center gap-2 rounded-md bg-white px-4 text-sm font-medium text-zinc-950 transition hover:bg-zinc-200"
                onClick={createChat}
                type="button"
              >
                <Plus size={17} />
                New Chat
              </button>
            </div>
          ) : (
            <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col px-4 py-6">
              <DocumentPanel
                deletingDocumentId={deletingDocumentId}
                documents={documents}
                isUploading={isUploading}
                onDeleteDocument={deleteDocument}
                onUploadClick={() => fileInputRef.current?.click()}
              />

              <div className="flex-1 space-y-5">
                {activeMessages.map((message, index) => (
                  <MessageBubble key={`${message.role}-${index}`} message={message} />
                ))}
                {isAnswering && (
                  <MessageBubble
                    message={{
                      role: "assistant",
                      content: "Thinking through the document...",
                    }}
                    muted
                  />
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>
          )}
        </section>

        <footer className="shrink-0 border-t border-zinc-800 bg-zinc-950 px-4 py-4">
          <form className="mx-auto flex max-w-4xl items-end gap-3" onSubmit={askQuestion}>
            <textarea
              className="min-h-12 flex-1 resize-none rounded-md border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm leading-5 text-white outline-none transition placeholder:text-zinc-500 focus:border-emerald-500"
              disabled={!chatId || isAnswering}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  askQuestion(event);
                }
              }}
              placeholder={chatId ? "Ask a question about the uploaded PDF" : "Create or select a chat first"}
              rows={1}
              value={question}
            />
            <button
              className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-white text-zinc-950 transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:bg-zinc-800 disabled:text-zinc-500"
              disabled={!chatId || !question.trim() || isAnswering}
              title="Send message"
              type="submit"
            >
              <Send size={18} />
            </button>
          </form>
        </footer>
      </main>
    </div>
  );
}

function DocumentPanel({
  deletingDocumentId,
  documents,
  isUploading,
  onDeleteDocument,
  onUploadClick,
}) {
  return (
    <div className="mb-6 border-b border-zinc-800 pb-5">
      <button
        className="flex w-full items-center gap-4 rounded-lg border border-dashed border-emerald-500/60 bg-emerald-950/30 p-5 text-left transition hover:border-emerald-400 hover:bg-emerald-950/50 disabled:cursor-not-allowed disabled:opacity-70"
        disabled={isUploading}
        onClick={onUploadClick}
        type="button"
      >
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-emerald-600 text-white">
          <FileUp size={25} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-base font-semibold text-white">
            {isUploading ? "Uploading PDF..." : "Upload PDF"}
          </span>
          <span className="mt-1 block text-sm leading-5 text-emerald-100/80">
            Add a document to this chat before asking questions.
          </span>
        </span>
      </button>

      {documents.length > 0 && (
        <div className="mt-4 space-y-2">
          {documents.map((document) => (
            <div
              className="flex items-center gap-3 rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2"
              key={document.id}
            >
              <FileText className="shrink-0 text-emerald-400" size={18} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-white">{document.filename}</p>
                <p className="text-xs text-zinc-500">{document.total_chunks} chunks indexed</p>
              </div>
              <button
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-zinc-400 transition hover:bg-red-950/70 hover:text-red-200 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={deletingDocumentId === document.id}
                onClick={() => onDeleteDocument(document.id)}
                title={`Delete ${document.filename}`}
                type="button"
              >
                <Trash2 size={17} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MessageBubble({ message, muted = false }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[82%] rounded-lg px-4 py-3 text-sm leading-6 ${
          isUser
            ? "bg-emerald-600 text-white"
            : "border border-zinc-800 bg-zinc-900 text-zinc-100"
        } ${muted ? "text-zinc-400" : ""}`}
      >
        {message.content}
      </div>
    </div>
  );
}
