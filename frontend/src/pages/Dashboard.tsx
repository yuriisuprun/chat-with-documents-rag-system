import React, { useState, useEffect } from 'react';
import { FiMessageSquare, FiUsers, FiFileText, FiTrendingUp } from 'react-icons/fi';
import apiClient from '../api/client';
import toast from 'react-hot-toast';

interface Stats {
  totalTenants: number;
  totalConversations: number;
  totalDocuments: number;
  activeConversations: number;
}

const Dashboard = () => {
  const [stats, setStats] = useState<Stats>({
    totalTenants: 0,
    totalConversations: 0,
    totalDocuments: 0,
    activeConversations: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const [conversationsRes, docsRes] = await Promise.all([
          apiClient.get('/conversations?skip=0&limit=1000'),
          apiClient.get('/documents?skip=0&limit=1000').catch(() => ({ data: [] })),
        ]);

        setStats({
          totalTenants: 1, // Single tenant app
          totalConversations: conversationsRes.data.length,
          totalDocuments: docsRes.data.length,
          activeConversations: conversationsRes.data.filter(
            (c: any) => c.status === 'active'
          ).length,
        });
      catch (error: any) {
        console.error('Error loading dashboard stats:', error);
        toast.error('Failed to load dashboard stats');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const StatCard = ({
    icon: Icon,
    label,
    value,
  }: {
    icon: any;
    label: string;
    value: number;
  }) => {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm">{label}</p>
            <p className="text-3xl font-bold mt-2">{value}</p>
          </div>
          <div className="text-blue-600 text-3xl">
            <Icon />
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">Loading...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={FiUsers}
            label="Active Tenants"
            value={stats.totalTenants}
          />
          <StatCard
            icon={FiMessageSquare}
            label="Total Conversations"
            value={stats.totalConversations}
          />
          <StatCard
            icon={FiTrendingUp}
            label="Active Conversations"
            value={stats.activeConversations}
          />
          <StatCard
            icon={FiFileText}
            label="Knowledge Documents"
            value={stats.totalDocuments}
          />
        </div>
      )}

      <div className="mt-12 bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Quick Start</h2>
        <ul className="space-y-3 text-gray-700">
          <li>✓ Create a new tenant to start accepting messages</li>
          <li>✓ Upload knowledge documents for context-aware responses</li>
          <li>✓ Configure auto-reply delays and disclaimers</li>
          <li>✓ Monitor conversations and AI responses in real-time</li>
        </ul>
      </div>
    </div>
  );
};

export default Dashboard;
