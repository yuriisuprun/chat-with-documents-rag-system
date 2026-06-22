import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import toast from 'react-hot-toast';
import { formatDistanceToNow } from 'date-fns';

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

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Conversations</h1>

      <div className="grid grid-cols-3 gap-6 h-[calc(100vh-200px)]">
        {/* Conversation List */}
        <div className="bg-white rounded-lg shadow overflow-hidden flex flex-col">
          <div className="p-4 border-b">
            <h2 className="font-bold">Chats</h2>
          </div>
          <div className="flex-1 overflow-auto">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-500">Loading...</p>
              </div>
            ) : conversations.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-500">No conversations</p>
              </div>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => handleSelectConversation(conv)}
                  className={`w-full text-left p-4 border-b hover:bg-gray-50 transition ${
                    selectedConversation?.id === conv.id ? 'bg-blue-50' : ''
                  }`}
                >
                  <p className="font-semibold">{conv.client_phone}</p>
                  <p className="text-sm text-gray-500">
                    {formatDistanceToNow(new Date(conv.created_at), {
                      addSuffix: true,
                    })}
                  </p>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Message View */}
        <div className="col-span-2 bg-white rounded-lg shadow overflow-hidden flex flex-col">
          {selectedConversation ? (
            <>
              <div className="p-4 border-b bg-gray-50">
                <h2 className="font-bold">{selectedConversation.client_phone}</h2>
                <p className="text-sm text-gray-500">
                  Status: {selectedConversation.status}
                </p>
              </div>

              <div className="flex-1 overflow-auto p-4 space-y-4">
                {messageLoading ? (
                  <div className="flex items-center justify-center h-full">
                    <p className="text-gray-500">Loading messages...</p>
                  </div>
                ) : messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full">
                    <p className="text-gray-500">No messages</p>
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
                        className={`max-w-xs px-4 py-2 rounded-lg ${
                          msg.sender === 'professional'
                            ? 'bg-blue-600 text-white'
                            : msg.sender === 'ai'
                            ? 'bg-purple-100 text-gray-900'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        <p className="text-sm">{msg.content}</p>
                        {msg.transcript && (
                          <p className="text-xs mt-2 opacity-75">
                            Voice: {msg.transcript}
                          </p>
                        )}
                        {msg.is_auto_reply && (
                          <span className="text-xs mt-1 inline-block">
                            Auto-reply
                          </span>
                        )}
                        <p className="text-xs mt-1 opacity-75">
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
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500">Select a conversation to view messages</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Conversations;
