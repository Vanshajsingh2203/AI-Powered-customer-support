
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  getCustomers,
  updateCustomerStatus,
} from '../api/customers';

function CustomerManagementPage() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [updatingCustomerId, setUpdatingCustomerId] = useState(null);
  const [success, setSuccess] = useState('');

  const loadCustomers = async () => {
    try {
      setLoading(true);
      setError('');

      const data = await getCustomers();
      setCustomers(data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to load customers.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, []);

  const handleToggleStatus = async (customer) => {
    const newStatus = !customer.is_active;

    const action = newStatus ? 'activate' : 'deactivate';

    const confirmed = window.confirm(
      `Are you sure you want to ${action} ${customer.full_name}?`
    );

    if (!confirmed) return;

    try {
      setUpdatingCustomerId(customer.id);
      setError('');
      setSuccess('');

      await updateCustomerStatus(customer.id, newStatus);

      setSuccess(
        `Customer ${action}d successfully.`
      );

      await loadCustomers();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        `Unable to ${action} customer.`
      );
    } finally {
      setUpdatingCustomerId(null);
    }
  };

  const filteredCustomers = customers.filter((customer) => {
    const searchTerm = search.toLowerCase();

    return (
      customer.full_name.toLowerCase().includes(searchTerm) ||
      customer.email.toLowerCase().includes(searchTerm)
    );
  });

  if (loading) {
    return (
      <div className="container mt-5 text-center">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-2">Loading customers...</p>
      </div>
    );
  }

  return (
    <div className="container-fluid py-4">

      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2>Customer Management</h2>
          <p className="text-muted mb-0">
            View and manage registered customer accounts.
          </p>
        </div>

        <Link
          to="/admin/dashboard"
          className="btn btn-outline-secondary"
        >
          Back to Dashboard
        </Link>
      </div>

      {error && (
        <div className="alert alert-danger">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      <div className="row mb-4">
        <div className="col-md-4">
          <div className="card shadow-sm">
            <div className="card-body">
              <h6 className="text-muted">Total Customers</h6>
              <h3>{customers.length}</h3>
            </div>
          </div>
        </div>

        <div className="col-md-4">
          <div className="card shadow-sm">
            <div className="card-body">
              <h6 className="text-muted">Active Customers</h6>
              <h3>
                {customers.filter((c) => c.is_active).length}
              </h3>
            </div>
          </div>
        </div>

        <div className="col-md-4">
          <div className="card shadow-sm">
            <div className="card-body">
              <h6 className="text-muted">Inactive Customers</h6>
              <h3>
                {customers.filter((c) => !c.is_active).length}
              </h3>
            </div>
          </div>
        </div>
      </div>

      <div className="card shadow-sm">
        <div className="card-body">

          <div className="mb-3">
            <input
              type="text"
              className="form-control"
              placeholder="Search by customer name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="table-responsive">
            <table className="table table-hover align-middle">

              <thead className="table-light">
                <tr>
                  <th>Customer</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Registered On</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {filteredCustomers.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="text-center py-4">
                      No customers found.
                    </td>
                  </tr>
                ) : (
                  filteredCustomers.map((customer) => (
                    <tr key={customer.id}>
                      <td>{customer.full_name}</td>

                      <td>{customer.email}</td>

                      <td>
                        <span className="badge bg-secondary">
                          {customer.role}
                        </span>
                      </td>

                      <td>
                        <span
                          className={`badge ${
                            customer.is_active
                              ? 'bg-success'
                              : 'bg-danger'
                          }`}
                        >
                          {customer.is_active
                            ? 'Active'
                            : 'Inactive'}
                        </span>
                      </td>

                      <td>
                        {new Date(
                          customer.created_at
                        ).toLocaleDateString()}
                      </td>

                      <td>
                        <button
                          className={`btn btn-sm ${
                            customer.is_active
                              ? 'btn-danger'
                              : 'btn-success'
                          }`}
                          disabled={
                            updatingCustomerId === customer.id
                          }
                          onClick={() =>
                            handleToggleStatus(customer)
                          }
                        >
                          {updatingCustomerId === customer.id
                            ? 'Updating...'
                            : customer.is_active
                              ? 'Deactivate'
                              : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>

            </table>
          </div>

        </div>
      </div>

    </div>
  );
}

export default CustomerManagementPage;
