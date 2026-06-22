import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import toast from 'react-hot-toast';
import { formatDistanceToNow } from 'date-fns';
import { FiMessageSquare, FiPhone, FiClock } from 'react-icons/fi';

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
    <div className="page-container">
      {/* Header */}
      <div className="mb-8">
        <h1 className="section-heading">Conversations</h1>
        <p className="text-gray-600">Monitor and manage client conversations.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-250px)]">
        {/* Conversation List */}
        <div className="card overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <h2 className="font-semibold text-gray-900">Chats</h2>
            {conversations.length > 0 && (
              <p className="text-xs text-gray-500 mt-1">{conversations.length} conversation(s)</p>
            )}
          </div>

          <div className="flex-1 overflow-auto">
            {loading ? (
              <div className="loading h-full">
                <div>
                  <span className="loading-spinner mr-3"></span>
                  <span className="text-gray-600">Loading chats...</span>
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
                  className={`list-item w-full text-left ${
                    selectedConversation?.id === conv.id ? 'active' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900">{conv.client_phone}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        <FiClock className="inline mr-1" />
                        {formatDistanceToNow(new Date(conv.created_at), {
                          addSuffix: true,
                        })}
                      </p>
                    </div>
                    <span
                      className={`badge badge-${
                        conv.status === 'active' ? 'success' : 'gray'
                      } text-xs ml-2 flex-shrink-0`}
                    >
                      {conv.status}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Message View */}
        <div className="lg:col-span-2 card overflow-hidden flex flex-col">
          {selectedConversation ? (
            <>
              {/* Conversation Header */}
              <div className="p-4 border-b border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-semibold text-gray-900 flex items-center">
                      <FiPhone className="mr-2 text-blue-600" />
                      {selectedConversation.client_phone}
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">
                      Status: <span className="font-medium capitalize">{selectedConversation.status}</span>
                    </p>
                  </div>
                </div>
              </div>

              {/* Messages Container */}
              <div className="flex-1 overflow-auto p-6 space-y-4 bg-white">
                {messageLoading ? (
                  <div className="loading h-full">
                    <div>
                      <span className="loading-spinner mr-3"></span>
                      <span className="text-gray-600">Loading messages...</span>
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
                        className={`max-w-xs px-4 py-3 rounded-lg ${
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
                        <p className="text-sm break-words">{msg.content}</p>

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
          ) : (
            <div className="loading h-full">
              <p className="text-gray-500">Select a conversation to view messages</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Conversations;
