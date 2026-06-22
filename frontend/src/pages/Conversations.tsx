import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import toast from 'react-hot-toast';
import { formatDistanceToNow } from 'date-fns';
import { FiMessageSquare, FiPhone, FiClock, FiChevronLeft } from 'react-icons/fi';

interface Message {
  id: string;
  sender: string;
  content: string;
  transcript?: string;
  created_at: string;
  is_auto_reply: boolean;
}

interface Conversation {
  id: string;
  client_phone: string;
  status: string;
  last_client_message_at?: string;
  created_at: string;
}

const Conversations = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [messageLoading, setMessageLoading] = useState(false);

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/conversations?skip=0&limit=100');
      setConversations(response.data);
      setSelectedConversation(null);
      setMessages([]);
    } catch (error: any) {
      toast.error('Failed to load conversations');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectConversation = async (conv: Conversation) => {
    setSelectedConversation(conv);
    setMessageLoading(true);
    try {
      const response = await apiClient.get(`/conversations/${conv.id}/messages`);
      setMessages(response.data);
    } catch (error) {
      toast.error('Failed to load messages');
    } finally {
      setMessageLoading(false);
    }
  };

  const getSenderBadgeColor = (sender: string) => {
    switch (sender) {
      case 'client':
        return 'bg-blue-100 text-blue-800';
      case 'professional':
        return 'bg-green-100 text-green-800';
      case 'ai':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSenderLabel = (sender: string) => {
    switch (sender) {
      case 'client':
        return 'Client';
      case 'professional':
        return 'You';
      case 'ai':
        return 'AI Assistant';
      default:
        return sender;
    }
  };

  return (
    <div className="page-container pt-20 lg:pt-8 flex flex-col h-[calc(100vh-5rem)] lg:h-auto">
      {/* Header - Hidden on mobile when viewing conversation */}
      {!selectedConversation && (
        <div className="mb-4 sm:mb-6">
          <h1 className="section-heading text-2xl sm:text-3xl lg:text-4xl">Conversations</h1>
          <p className="text-gray-600 text-sm sm:text-base mt-1">Monitor and manage client conversations.</p>
        </div>
      )}

      {/* Mobile-first: Single column, tablet+: 3 column grid */}
      <div className={`flex-1 overflow-hidden lg:overflow-auto grid gap-3 sm:gap-4 lg:gap-6 ${
        selectedConversation ? 'hidden lg:grid' : 'grid-cols-1'
      } lg:grid-cols-3`}>
        {/* Conversation List */}
        <div className="card overflow-hidden flex flex-col">
          <div className="p-3 sm:p-4 border-b border-gray-200 bg-gray-50 flex-shrink-0">
            <h2 className="font-semibold text-gray-900 text-base sm:text-lg">Chats</h2>
            {conversations.length > 0 && (
              <p className="text-xs text-gray-500 mt-1">{conversations.length} conversation(s)</p>
            )}
          </div>

          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="loading h-48">
                <div>
                  <span className="loading-spinner mr-3"></span>
                  <span className="text-gray-600 text-sm">Loading chats...</span>
                </div>
              </div>
            ) : conversations.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">
                  <FiMessageSquare />
                </div>
                <p className="empty-state-text">No conversations yet</p>
              </div>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => handleSelectConversation(conv)}
                  className={`list-item w-full text-left px-3 sm:px-4 py-3 sm:py-4 border-b border-gray-100 last:border-0 transition-colors ${
                    selectedConversation?.id === conv.id ? 'active bg-blue-50' : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 text-sm sm:text-base truncate">{conv.client_phone}</p>
                      <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                        <FiClock className="flex-shrink-0" size={12} />
                        <span className="truncate">
                          {formatDistanceToNow(new Date(conv.created_at), {
                            addSuffix: true,
                          })}
                        </span>
                      </p>
                    </div>
                    <span
                      className={`badge badge-${
                        conv.status === 'active' ? 'success' : 'gray'
                      } text-xs flex-shrink-0`}
                    >
                      {conv.status}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Message View - Hidden on mobile unless conversation selected */}
        {selectedConversation && (
          <div className="lg:col-span-2 card overflow-hidden flex flex-col">
            <>
              {/* Conversation Header */}
              <div className="p-3 sm:p-4 border-b border-gray-200 bg-gray-50 flex-shrink-0">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <h2 className="font-semibold text-gray-900 flex items-center gap-2 text-base sm:text-lg">
                      <FiPhone className="text-blue-600 flex-shrink-0" size={18} />
                      <span className="truncate">{selectedConversation.client_phone}</span>
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-600 mt-1">
                      Status: <span className="font-medium capitalize">{selectedConversation.status}</span>
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedConversation(null);
                      setMessages([]);
                    }}
                    className="lg:hidden p-2 hover:bg-gray-200 rounded-lg transition-colors flex-shrink-0"
                    aria-label="Back to conversations"
                  >
                    <FiChevronLeft size={20} />
                  </button>
                </div>
              </div>

              {/* Messages Container */}
              <div className="flex-1 overflow-y-auto p-3 sm:p-4 lg:p-6 space-y-3 sm:space-y-4 bg-white">
                {messageLoading ? (
                  <div className="loading h-full">
                    <div>
                      <span className="loading-spinner mr-3"></span>
                      <span className="text-gray-600 text-sm">Loading messages...</span>
                    </div>
                  </div>
                ) : messages.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-state-icon">
                      <FiMessageSquare />
                    </div>
                    <p className="empty-state-text">No messages</p>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${
                        msg.sender === 'professional' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      <div
                        className={`max-w-xs sm:max-w-md px-3 sm:px-4 py-2 sm:py-3 rounded-lg text-sm break-words ${
                          msg.sender === 'professional'
                            ? 'bg-blue-600 text-white rounded-br-none'
                            : msg.sender === 'ai'
                            ? 'bg-purple-100 text-gray-900 rounded-bl-none'
                            : 'bg-gray-100 text-gray-900 rounded-bl-none'
                        }`}
                      >
                        {/* Sender Badge */}
                        <div className="flex items-center mb-1">
                          <span
                            className={`text-xs font-semibold px-2 py-0.5 rounded ${getSenderBadgeColor(
                              msg.sender
                            )}`}
                          >
                            {getSenderLabel(msg.sender)}
                          </span>
                        </div>

                        {/* Message Content */}
                        <p className="text-xs sm:text-sm">{msg.content}</p>

                        {/* Transcript */}
                        {msg.transcript && (
                          <p className="text-xs mt-2 opacity-75 italic">
                            Voice: {msg.transcript}
                          </p>
                        )}

                        {/* Auto-reply Badge */}
                        {msg.is_auto_reply && (
                          <span className="text-xs mt-2 inline-block opacity-75">
                            🤖 Auto-reply
                          </span>
                        )}

                        {/* Timestamp */}
                        <p className="text-xs mt-2 opacity-75">
                          {formatDistanceToNow(new Date(msg.created_at), {
                            addSuffix: true,
                          })}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          </div>
        )}

        {/* Desktop placeholder when no conversation selected */}
        {!selectedConversation && (
          <div className="hidden lg:flex lg:col-span-2 card items-center justify-center">
            <div className="text-center">
              <FiMessageSquare className="mx-auto mb-3 text-gray-400" size={48} />
              <p className="text-gray-500">Select a conversation to view messages</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Conversations;
