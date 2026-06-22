import React, { useState, useEffect } from 'react';
import { FiPlus, FiTrash2, FiUpload, FiFile } from 'react-icons/fi';
import apiClient from '../api/client';
import toast from 'react-hot-toast';

// Icon wrapper to bypass TypeScript JSX checking issues with react-icons
const Icon = ({ icon: IconComponent, className }: { icon: any; className?: string }) => (
  <IconComponent className={className} />
);

interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  section_title?: string;
  is_active: boolean;
  created_at: string;
}

const Documents = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/documents?skip=0&limit=1000');
      setDocuments(response.data);
    } catch (error) {
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!validTypes.includes(file.type)) {
      toast.error('Only PDF, DOCX, and TXT files are allowed');
      return;
    }

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error('File size exceeds 10MB limit');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      await apiClient.post('/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      toast.success('Document uploaded successfully');
      fetchDocuments();
      e.target.value = '';
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!window.confirm(`Delete "${filename}"?`)) return;

    try {
      await apiClient.delete(`/documents/${docId}`);
      toast.success('Document deleted');
      fetchDocuments();
    } catch (error) {
      toast.error('Failed to delete document');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="page-container pt-20 lg:pt-8">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="section-heading text-2xl sm:text-3xl lg:text-4xl">Knowledge Base</h1>
        <p className="text-gray-600 text-sm sm:text-base mt-1 sm:mt-2">Manage documents to train your AI assistant.</p>
      </div>

      {/* Upload Section */}
      <div className="card card-standard mb-6 sm:mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 mb-1 text-base sm:text-lg">Upload Document</h3>
            <p className="text-xs sm:text-sm text-gray-600">
              Supported formats: PDF, DOCX, TXT (Max 10MB)
            </p>
          </div>
          <label className="btn btn-primary flex-shrink-0 w-full sm:w-auto justify-center sm:justify-start">
            <Icon icon={FiUpload} className="mr-2" />
            <span className="text-sm sm:text-base">
              {uploading ? 'Uploading...' : 'Choose File'}
            </span>
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
              aria-label="Upload document"
            />
          </label>
        </div>
      </div>

      {/* Documents List */}
      {loading ? (
        <div className="loading h-48 sm:h-64">
          <div>
            <span className="loading-spinner mr-3"></span>
            <span className="text-gray-600 text-sm sm:text-base">Loading documents...</span>
          </div>
        </div>
      ) : documents.length === 0 ? (
        <div className="empty-state card card-standard">
          <div className="empty-state-icon">
            <Icon icon={FiFile} />
          </div>
          <p className="empty-state-text">No documents uploaded yet</p>
          <p className="text-xs sm:text-sm text-gray-500 mt-2">Start by uploading a document to train your assistant.</p>
        </div>
      ) : (
        <>
          {/* Desktop Table View */}
          <div className="hidden sm:block card overflow-hidden">
            <div className="overflow-x-auto">
              <table>
                <thead>
                  <tr>
                    <th className="text-left text-xs sm:text-sm">Filename</th>
                    <th className="text-left text-xs sm:text-sm">Type</th>
                    <th className="text-left text-xs sm:text-sm">Size</th>
                    <th className="text-left text-xs sm:text-sm hidden md:table-cell">Section</th>
                    <th className="text-left text-xs sm:text-sm">Status</th>
                    <th className="text-left text-xs sm:text-sm hidden lg:table-cell">Uploaded</th>
                    <th className="text-right text-xs sm:text-sm">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr key={doc.id}>
                      <td>
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="w-2 h-2 bg-blue-600 rounded-full flex-shrink-0"></span>
                          <span className="font-medium text-gray-900 truncate text-xs sm:text-sm">{doc.filename}</span>
                        </div>
                      </td>
                      <td>
                        <span className="inline-block px-2 py-1 bg-gray-100 rounded text-xs font-medium text-gray-700">
                          {doc.file_type.toUpperCase()}
                        </span>
                      </td>
                      <td className="text-xs sm:text-sm">{formatFileSize(doc.file_size_bytes)}</td>
                      <td className="text-xs sm:text-sm hidden md:table-cell">{doc.section_title || <span className="text-gray-400">-</span>}</td>
                      <td>
                        <span
                          className={`badge text-xs ${
                            doc.is_active ? 'badge-success' : 'badge-gray'
                          }`}
                        >
                          {doc.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="text-xs sm:text-sm text-gray-600 hidden lg:table-cell">{formatDate(doc.created_at)}</td>
                      <td className="text-right">
                        <button
                          onClick={() => handleDelete(doc.id, doc.filename)}
                          className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-red-600 hover:bg-red-50 transition-colors flex-shrink-0"
                          aria-label={`Delete ${doc.filename}`}
                          title="Delete document"
                        >
                          <Icon icon={FiTrash2} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Mobile Card View */}
          <div className="sm:hidden space-y-3">
            {documents.map((doc) => (
              <div key={doc.id} className="card card-standard">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900 truncate text-sm">{doc.filename}</p>
                    <p className="text-xs text-gray-600 mt-1">{doc.file_type.toUpperCase()}</p>
                  </div>
                  <button
                    onClick={() => handleDelete(doc.id, doc.filename)}
                    className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-red-600 hover:bg-red-50 transition-colors flex-shrink-0"
                    aria-label={`Delete ${doc.filename}`}
                    title="Delete document"
                  >
                    <Icon icon={FiTrash2} />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <p className="text-gray-600">Size</p>
                    <p className="font-medium text-gray-900">{formatFileSize(doc.file_size_bytes)}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Status</p>
                    <p className="font-medium">
                      <span className={`badge text-xs ${doc.is_active ? 'badge-success' : 'badge-gray'}`}>
                        {doc.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-gray-600">Uploaded</p>
                    <p className="font-medium text-gray-900">{formatDate(doc.created_at)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Info Section */}
      {documents.length > 0 && (
        <div className="mt-6 sm:mt-8 card card-standard bg-blue-50 border-l-4 border-blue-600">
          <h3 className="font-semibold text-gray-900 mb-2 text-base sm:text-lg">💡 Tip</h3>
          <p className="text-xs sm:text-sm text-gray-700">
            Documents are used by your AI assistant to provide more accurate and context-aware responses. 
            Make sure to upload relevant documentation for your business.
          </p>
        </div>
      )}
    </div>
  );
};

export default Documents;
