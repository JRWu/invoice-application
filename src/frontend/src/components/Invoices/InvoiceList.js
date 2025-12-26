import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { invoicesAPI } from '../../utils/api';
import { toast } from 'react-toastify';
import { 
  Plus, 
  Eye, 
  Edit, 
  Trash2, 
  Calendar,
  Search,
  Filter,
  Download
} from 'lucide-react';
import { format } from 'date-fns';

const InvoiceList = () => {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchInvoices();
  }, []);

  const fetchInvoices = async () => {
    try {
      const response = await invoicesAPI.getAll();
      setInvoices(response.data.invoices);
    } catch (error) {
      toast.error('Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (invoiceId) => {
    if (window.confirm('Are you sure you want to delete this invoice?')) {
      try {
        await invoicesAPI.delete(invoiceId);
        toast.success('Invoice deleted successfully');
        fetchInvoices();
      } catch (error) {
        toast.error('Failed to delete invoice');
      }
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'paid':
        return 'status-badge status-paid';
      case 'sent':
        return 'status-badge status-sent';
      case 'overdue':
        return 'status-badge status-overdue';
      default:
        return 'status-badge status-draft';
    }
  };

  const filteredInvoices = invoices.filter(invoice => {
    const matchesSearch = invoice.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         invoice.invoice_number.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || invoice.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleExportCSV = () => {
    try {
      if (filteredInvoices.length === 0) {
        toast.warning('No invoices to export');
        return;
      }

      const headers = ['Invoice Number', 'Customer Name', 'Customer Email', 'Issue Date', 'Due Date', 'Amount', 'Status'];
      const csvRows = [headers.join(',')];

      filteredInvoices.forEach(invoice => {
        const row = [
          invoice.invoice_number,
          `"${invoice.customer_name}"`,
          invoice.customer_email || '',
          format(new Date(invoice.issue_date), 'yyyy-MM-dd'),
          format(new Date(invoice.due_date), 'yyyy-MM-dd'),
          invoice.total_amount.toFixed(2),
          invoice.status
        ];
        csvRows.push(row.join(','));
      });

      const csvContent = csvRows.join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      
      link.setAttribute('href', url);
      link.setAttribute('download', `invoices_${format(new Date(), 'yyyy-MM-dd')}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      toast.success(`Exported ${filteredInvoices.length} invoice(s)`);
    } catch (error) {
      toast.error('Failed to export invoices');
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingTop: '2rem', paddingBottom: '2rem' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem'
      }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1e293b' }}>
          Invoices
        </h1>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={handleExportCSV} className="btn btn-outline">
            <Download size={16} />
            Export
          </button>
          <Link to="/invoices/new" className="btn btn-primary">
            <Plus size={16} />
            New Invoice
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          alignItems: 'end'
        }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">
              <Search size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
              Search
            </label>
            <input
              type="text"
              className="form-input"
              placeholder="Search by customer or invoice number..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">
              <Filter size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
              Status
            </label>
            <select
              className="form-input"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="sent">Sent</option>
              <option value="paid">Paid</option>
              <option value="overdue">Overdue</option>
            </select>
          </div>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="card">
        {filteredInvoices.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Invoice #</th>
                  <th>Customer</th>
                  <th>Issue Date</th>
                  <th>Due Date</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredInvoices.map((invoice) => (
                  <tr key={invoice.id}>
                    <td style={{ fontWeight: '500' }}>
                      {invoice.invoice_number}
                    </td>
                    <td>
                      <div>
                        <div style={{ fontWeight: '500' }}>
                          {invoice.customer_name}
                        </div>
                        {invoice.customer_email && (
                          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                            {invoice.customer_email}
                          </div>
                        )}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Calendar size={14} color="#6b7280" />
                        {format(new Date(invoice.issue_date), 'MMM dd, yyyy')}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Calendar size={14} color="#6b7280" />
                        {format(new Date(invoice.due_date), 'MMM dd, yyyy')}
                      </div>
                    </td>
                    <td style={{ fontWeight: '500' }}>
                      ${invoice.total_amount.toFixed(2)}
                    </td>
                    <td>
                      <span className={getStatusBadgeClass(invoice.status)}>
                        {invoice.status}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <Link
                          to={`/invoices/${invoice.id}`}
                          className="btn btn-outline"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        >
                          <Eye size={12} />
                        </Link>
                        <Link
                          to={`/invoices/${invoice.id}/edit`}
                          className="btn btn-outline"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        >
                          <Edit size={12} />
                        </Link>
                        <button
                          onClick={() => handleDelete(invoice.id)}
                          className="btn btn-danger"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{
            textAlign: 'center',
            padding: '3rem',
            color: '#6b7280'
          }}>
            <Search size={48} color="#d1d5db" style={{ margin: '0 auto 1rem' }} />
            <p style={{ fontSize: '1.125rem', marginBottom: '0.5rem' }}>
              {searchTerm || statusFilter !== 'all' ? 'No invoices found' : 'No invoices yet'}
            </p>
            <p style={{ marginBottom: '1.5rem' }}>
              {searchTerm || statusFilter !== 'all' 
                ? 'Try adjusting your search or filter criteria'
                : 'Create your first invoice to get started'
              }
            </p>
            {!searchTerm && statusFilter === 'all' && (
              <Link to="/invoices/new" className="btn btn-primary">
                <Plus size={16} />
                Create Invoice
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default InvoiceList;
