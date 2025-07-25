import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { invoicesAPI } from '../../utils/api';
import { toast } from 'react-toastify';
import { 
  Save, 
  Plus, 
  Trash2, 
  ArrowLeft,
  User,
  Mail,
  MapPin,
  Calendar,
  FileText,
  DollarSign
} from 'lucide-react';
import { format } from 'date-fns';

const InvoiceForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = !!id;

  const [formData, setFormData] = useState({
    customer_name: '',
    customer_email: '',
    customer_address: '',
    due_date: '',
    tax_rate: 0,
    notes: '',
    status: 'draft',
    items: [{ description: '', quantity: 1, unit_price: 0 }]
  });
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(isEditing);

  useEffect(() => {
    if (isEditing) {
      fetchInvoice();
    }
  }, [id, isEditing]);

  const fetchInvoice = async () => {
    try {
      const response = await invoicesAPI.getById(id);
      const invoice = response.data.invoice;
      
      setFormData({
        customer_name: invoice.customer_name,
        customer_email: invoice.customer_email || '',
        customer_address: invoice.customer_address || '',
        due_date: invoice.due_date,
        tax_rate: invoice.tax_rate,
        notes: invoice.notes || '',
        status: invoice.status,
        items: invoice.items.length > 0 ? invoice.items : [{ description: '', quantity: 1, unit_price: 0 }]
      });
    } catch (error) {
      toast.error('Failed to load invoice');
      navigate('/invoices');
    } finally {
      setInitialLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleItemChange = (index, field, value) => {
    const updatedItems = [...formData.items];
    updatedItems[index] = {
      ...updatedItems[index],
      [field]: field === 'quantity' || field === 'unit_price' ? parseFloat(value) || 0 : value
    };
    setFormData(prev => ({
      ...prev,
      items: updatedItems
    }));
  };

  const addItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, { description: '', quantity: 1, unit_price: 0 }]
    }));
  };

  const removeItem = (index) => {
    if (formData.items.length > 1) {
      const updatedItems = formData.items.filter((_, i) => i !== index);
      setFormData(prev => ({
        ...prev,
        items: updatedItems
      }));
    }
  };

  const calculateSubtotal = () => {
    return formData.items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
  };

  const calculateTax = () => {
    return calculateSubtotal() * (formData.tax_rate / 100);
  };

  const calculateTotal = () => {
    return calculateSubtotal() + calculateTax();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const submitData = {
        ...formData,
        tax_rate: parseFloat(formData.tax_rate) || 0
      };

      if (isEditing) {
        await invoicesAPI.update(id, submitData);
        toast.success('Invoice updated successfully');
      } else {
        await invoicesAPI.create(submitData);
        toast.success('Invoice created successfully');
      }
      
      navigate('/invoices');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to save invoice');
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
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
        alignItems: 'center',
        gap: '1rem',
        marginBottom: '2rem'
      }}>
        <button
          onClick={() => navigate('/invoices')}
          className="btn btn-outline"
        >
          <ArrowLeft size={16} />
          Back
        </button>
        <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1e293b' }}>
          {isEditing ? 'Edit Invoice' : 'Create New Invoice'}
        </h1>
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '2rem',
          marginBottom: '2rem'
        }}>
          {/* Customer Information */}
          <div className="card">
            <h3 style={{
              fontSize: '1.25rem',
              fontWeight: '600',
              color: '#1e293b',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <User size={20} />
              Customer Information
            </h3>

            <div className="form-group">
              <label className="form-label">Customer Name *</label>
              <input
                type="text"
                name="customer_name"
                value={formData.customer_name}
                onChange={handleChange}
                className="form-input"
                placeholder="Enter customer name"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                <Mail size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
                Email
              </label>
              <input
                type="email"
                name="customer_email"
                value={formData.customer_email}
                onChange={handleChange}
                className="form-input"
                placeholder="customer@example.com"
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                <MapPin size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
                Address
              </label>
              <textarea
                name="customer_address"
                value={formData.customer_address}
                onChange={handleChange}
                className="form-textarea"
                placeholder="Customer address"
                rows={3}
              />
            </div>
          </div>

          {/* Invoice Details */}
          <div className="card">
            <h3 style={{
              fontSize: '1.25rem',
              fontWeight: '600',
              color: '#1e293b',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <FileText size={20} />
              Invoice Details
            </h3>

            <div className="form-group">
              <label className="form-label">
                <Calendar size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
                Due Date *
              </label>
              <input
                type="date"
                name="due_date"
                value={formData.due_date}
                onChange={handleChange}
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Status</label>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="form-input"
              >
                <option value="draft">Draft</option>
                <option value="sent">Sent</option>
                <option value="paid">Paid</option>
                <option value="overdue">Overdue</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Tax Rate (%)</label>
              <input
                type="number"
                name="tax_rate"
                value={formData.tax_rate}
                onChange={handleChange}
                className="form-input"
                min="0"
                max="100"
                step="0.01"
                placeholder="0.00"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Notes</label>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                className="form-textarea"
                placeholder="Additional notes..."
                rows={3}
              />
            </div>
          </div>
        </div>

        {/* Invoice Items */}
        <div className="card">
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1.5rem'
          }}>
            <h3 style={{
              fontSize: '1.25rem',
              fontWeight: '600',
              color: '#1e293b',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <DollarSign size={20} />
              Invoice Items
            </h3>
            <button
              type="button"
              onClick={addItem}
              className="btn btn-outline"
            >
              <Plus size={16} />
              Add Item
            </button>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th style={{ minWidth: '200px' }}>Description</th>
                  <th style={{ width: '100px' }}>Quantity</th>
                  <th style={{ width: '120px' }}>Unit Price</th>
                  <th style={{ width: '120px' }}>Total</th>
                  <th style={{ width: '80px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {formData.items.map((item, index) => (
                  <tr key={index}>
                    <td>
                      <input
                        type="text"
                        value={item.description}
                        onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                        className="form-input"
                        placeholder="Item description"
                        required
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        value={item.quantity}
                        onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                        className="form-input"
                        min="0.01"
                        step="0.01"
                        required
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        value={item.unit_price}
                        onChange={(e) => handleItemChange(index, 'unit_price', e.target.value)}
                        className="form-input"
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                        required
                      />
                    </td>
                    <td style={{ fontWeight: '500' }}>
                      ${(item.quantity * item.unit_price).toFixed(2)}
                    </td>
                    <td>
                      {formData.items.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeItem(index)}
                          className="btn btn-danger"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        >
                          <Trash2 size={12} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Totals */}
          <div style={{
            marginTop: '2rem',
            paddingTop: '1rem',
            borderTop: '1px solid #e5e7eb'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'flex-end'
            }}>
              <div style={{ minWidth: '300px' }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '0.5rem'
                }}>
                  <span>Subtotal:</span>
                  <span>${calculateSubtotal().toFixed(2)}</span>
                </div>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '0.5rem'
                }}>
                  <span>Tax ({formData.tax_rate}%):</span>
                  <span>${calculateTax().toFixed(2)}</span>
                </div>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '1.25rem',
                  fontWeight: 'bold',
                  paddingTop: '0.5rem',
                  borderTop: '1px solid #e5e7eb'
                }}>
                  <span>Total:</span>
                  <span>${calculateTotal().toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '1rem',
          marginTop: '2rem'
        }}>
          <button
            type="button"
            onClick={() => navigate('/invoices')}
            className="btn btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? (
              <div className="spinner" style={{ width: '1rem', height: '1rem' }} />
            ) : (
              <>
                <Save size={16} />
                {isEditing ? 'Update Invoice' : 'Create Invoice'}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default InvoiceForm;
