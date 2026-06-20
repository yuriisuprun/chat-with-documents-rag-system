import React, { useState, useEffect } from 'react';
import { FiPlus, FiEdit2, FiTrash2 } from 'react-icons/fi';
import apiClient from '../api/client';
import toast from 'react-hot-toast';

interface Tenant {
  id: string;
  business_name: string;
  professional_name: string;
  whatsapp_number: string;
  auto_reply_delay_minutes: number;
  is_active: boolean;
  created_at: string;
}

const Tenants = () => {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    business_name: '',
    professional_name: '',
    whatsapp_number: '',
    auto_reply_delay_minutes: 30,
    booking_url: '',
    disclaimer: 'This is an automated assistant. This message is not professional advice.',
  });

  useEffect(() => {
    fetchTenants();
  }, []);

  const fetchTenants = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/tenants');
      setTenants(response.data);
    } catch (error: any) {
      toast.error('Failed to load tenants');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/tenants', formData);
      toast.success('Tenant created successfully');
      setShowForm(false);
      setFormData({
        business_name: '',
        professional_name: '',
        whatsapp_number: '',
        auto_reply_delay_minutes: 30,
        booking_url: '',
        disclaimer: 'This is an automated assistant. This message is not professional advice.',
      });
      fetchTenants();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create tenant');
    }
  };

  const handleDelete = async (tenantId: string) => {
    if (!window.confirm('Are you sure you want to delete this tenant?')) return;
    try {
      await apiClient.delete(`/tenants/${tenantId}`);
      toast.success('Tenant deleted');
      fetchTenants();
    } catch (error: any) {
      toast.error('Failed to delete tenant');
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Tenants</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          <FiPlus className="mr-2" />
          New Tenant
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Business Name"
                value={formData.business_name}
                onChange={(e) =>
                  setFormData({ ...formData, business_name: e.target.value })
                }
                className="border rounded-lg px-4 py-2 focus:outline-none focus:border-blue-600"
                required
              />
              <input
                type="text"
                placeholder="Professional Name"
                value={formData.professional_name}
                onChange={(e) =>
                  setFormData({ ...formData, professional_name: e.target.value })
                }
                className="border rounded-lg px-4 py-2 focus:outline-none focus:border-blue-600"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <input
                type="tel"
                placeholder="WhatsApp Number (+1234567890)"
                value={formData.whatsapp_number}
                onChange={(e) =>
                  setFormData({ ...formData, whatsapp_number: e.target.value })
                }
                className="border rounded-lg px-4 py-2 focus:outline-none focus:border-blue-600"
                required
              />
              <input
                type="number"
                placeholder="Auto Reply Delay (minutes)"
                value={formData.auto_reply_delay_minutes}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    auto_reply_delay_minutes: parseInt(e.target.value),
                  })
                }
                min="1"
                max="120"
                className="border rounded-lg px-4 py-2 focus:outline-none focus:border-blue-600"
              />
            </div>

            <textarea
              placeholder="Disclaimer"
              value={formData.disclaimer}
              onChange={(e) => setFormData({ ...formData, disclaimer: e.target.value })}
              className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:border-blue-600"
              rows={3}
            />

            <div className="flex gap-2">
              <button
                type="submit"
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
              >
                Create
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="bg-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-400 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">Loading...</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold">
                  Business
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold">
                  Professional
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold">
                  Phone
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold">
                  Delay (min)
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-sm font-semibold">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((tenant) => (
                <tr
                  key={tenant.id}
                  className="border-t hover:bg-gray-50 transition"
                >
                  <td className="px-6 py-3">{tenant.business_name}</td>
                  <td className="px-6 py-3">{tenant.professional_name}</td>
                  <td className="px-6 py-3 font-mono">{tenant.whatsapp_number}</td>
                  <td className="px-6 py-3">{tenant.auto_reply_delay_minutes}</td>
                  <td className="px-6 py-3">
                    <span
                      className={`px-3 py-1 rounded-full text-sm ${
                        tenant.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {tenant.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-right">
                    <button
                      onClick={() => handleDelete(tenant.id)}
                      className="text-red-600 hover:text-red-800 transition"
                    >
                      <FiTrash2 />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Tenants;
