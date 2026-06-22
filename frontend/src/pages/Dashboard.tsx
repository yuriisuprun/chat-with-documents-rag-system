import React, { useState, useEffect } from 'react';
import { FiMessageSquare, FiFileText, FiTrendingUp, FiArrowRight } from 'react-icons/fi';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';
import toast from 'react-hot-toast';

interface Stats {
  totalConversations: number;
  totalDocuments: number;
  activeConversations: number;
}

const Dashboard = () => {
  const [stats, setStats] = useState<Stats>({
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
          totalConversations: conversationsRes.data.length,
          totalDocuments: docsRes.data.length,
          activeConversations: conversationsRes.data.filter(
            (c: any) => c.status === 'active'
          ).length,
        });
      } catch (error: any) {
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
    link,
    color = 'blue',
  }: {
    icon: any;
    label: string;
    value: number;
    link?: string;
    color?: 'blue' | 'green' | 'purple' | 'orange';
  }) => {
    const colorClasses = {
      blue: 'bg-blue-50 text-blue-600 border-blue-200',
      green: 'bg-green-50 text-green-600 border-green-200',
      purple: 'bg-purple-50 text-purple-600 border-purple-200',
      orange: 'bg-orange-50 text-orange-600 border-orange-200',
    };

    const content = (
      <div className={`card card-standard border-l-4 border-${color}-600 group transition-all duration-200`}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-gray-600 text-xs sm:text-sm font-medium">{label}</p>
            <p className="text-3xl sm:text-4xl font-bold mt-2 sm:mt-3 text-gray-900">{value}</p>
          </div>
          <div className={`p-3 sm:p-4 rounded-lg ${colorClasses[color]} group-hover:scale-110 transition-transform flex-shrink-0`}>
            <Icon className="text-xl sm:text-2xl" />
          </div>
        </div>
      </div>
    );

    return link ? (
      <Link to={link} className="block hover:shadow-md transition-shadow">
        {content}
      </Link>
    ) : (
      content
    );
  };

  const QuickStartItem = ({
    icon: Icon,
    title,
    description,
    link,
  }: {
    icon: any;
    title: string;
    description: string;
    link: string;
  }) => (
    <Link
      to={link}
      className="card card-standard group hover:shadow-md transition-all flex flex-col sm:flex-row sm:items-start gap-3 sm:gap-4"
    >
      <div className="p-2 sm:p-3 bg-blue-100 rounded-lg text-blue-600 group-hover:scale-110 transition-transform flex-shrink-0 self-start">
        <Icon className="text-xl sm:text-2xl" />
      </div>
      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-gray-900 mb-1 text-sm sm:text-base">{title}</h3>
        <p className="text-xs sm:text-sm text-gray-600 line-clamp-2">{description}</p>
      </div>
      <FiArrowRight className="text-gray-400 group-hover:text-blue-600 transition-colors flex-shrink-0 mt-2 sm:mt-1 self-start sm:self-center" />
    </Link>
  );

  return (
    <div className="page-container pt-20 lg:pt-8">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="section-heading text-2xl sm:text-3xl lg:text-4xl">Dashboard</h1>
        <p className="text-gray-600 text-sm sm:text-base mt-1 sm:mt-2">Welcome back! Here's an overview of your WhatsApp AI Assistant.</p>
      </div>

      {/* Stats Section */}
      {loading ? (
        <div className="loading h-48 sm:h-64">
          <div>
            <span className="loading-spinner mr-3"></span>
            <span className="text-gray-600 text-sm sm:text-base">Loading statistics...</span>
          </div>
        </div>
      ) : (
        <>
          {/* Stats Grid - Mobile first: 1 col, tablet: 2 cols, desktop: 3 cols */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 lg:gap-6 mb-6 sm:mb-8">
            <StatCard
              icon={FiMessageSquare}
              label="Total Conversations"
              value={stats.totalConversations}
              link="/conversations"
              color="blue"
            />
            <StatCard
              icon={FiTrendingUp}
              label="Active Conversations"
              value={stats.activeConversations}
              link="/conversations"
              color="green"
            />
            <StatCard
              icon={FiFileText}
              label="Knowledge Documents"
              value={stats.totalDocuments}
              link="/documents"
              color="purple"
            />
          </div>

          {/* Quick Start Section */}
          <div className="mb-6 sm:mb-8">
            <h2 className="section-subheading text-lg sm:text-xl mb-3 sm:mb-4">Quick Start Guide</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <QuickStartItem
                icon={FiFileText}
                title="Upload Documents"
                description="Add knowledge documents to train your AI assistant for better responses."
                link="/documents"
              />
              <QuickStartItem
                icon={FiMessageSquare}
                title="Review Conversations"
                description="Monitor client interactions and AI responses in real-time."
                link="/conversations"
              />
            </div>
          </div>

          {/* Info Card */}
          <div className="card card-standard bg-gradient-to-r from-blue-50 to-blue-100 border-l-4 border-blue-600">
            <h3 className="font-semibold text-gray-900 mb-3 text-base sm:text-lg">Getting Started</h3>
            <ul className="space-y-2 text-xs sm:text-sm text-gray-700">
              <li className="flex items-start gap-3">
                <span className="w-2 h-2 bg-blue-600 rounded-full mt-1.5 flex-shrink-0"></span>
                <span>Upload knowledge documents for context-aware responses</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="w-2 h-2 bg-blue-600 rounded-full mt-1.5 flex-shrink-0"></span>
                <span>Configure auto-reply delays and disclaimers</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="w-2 h-2 bg-blue-600 rounded-full mt-1.5 flex-shrink-0"></span>
                <span>Monitor conversations and AI responses in real-time</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="w-2 h-2 bg-blue-600 rounded-full mt-1.5 flex-shrink-0"></span>
                <span>Review and respond to client messages</span>
              </li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;
