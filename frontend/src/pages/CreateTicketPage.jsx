
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { createTicket } from '../api/tickets';
import { getCategories } from '../api/categories';

function CreateTicketPage() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category_id: '',
  });

  const [categories, setCategories] = useState([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [categoryError, setCategoryError] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Fetch available categories when the page loads.
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const data = await getCategories();
        setCategories(data);
      } catch (err) {
        console.error('Failed to fetch categories:', err);
        setCategoryError(
          'Unable to load categories. You can still create a ticket without selecting one.'
        );
      } finally {
        setCategoriesLoading(false);
      }
    };

    fetchCategories();
  }, []);

  // Update form state when an input changes.
  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }));
  };

  // Submit a new support ticket.
  const handleSubmit = async (event) => {
    event.preventDefault();

    setError('');
    setSuccess('');

    if (formData.title.trim().length < 5) {
      setError('Title must contain at least 5 characters.');
      return;
    }

    if (formData.description.trim().length < 10) {
      setError('Description must contain at least 10 characters.');
      return;
    }

    setLoading(true);

    try {
      await createTicket({
        title: formData.title.trim(),
        description: formData.description.trim(),
        category_id: formData.category_id || null,
      });

      setSuccess('Your support ticket has been created successfully!');

      setTimeout(() => {
        navigate('/customer/dashboard');
      }, 1200);

    } catch (err) {
      const responseData = err.response?.data;

      if (Array.isArray(responseData?.detail)) {
        setError(
          responseData.detail.map((item) => item.msg).join(', ')
        );
      } else {
        setError(
          responseData?.detail ||
          'Unable to create your ticket. Please try again.'
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-lg-8 col-md-10">

          <div className="mb-4">
            <Link
              to="/customer/dashboard"
              className="text-decoration-none"
            >
              &larr; Back to Dashboard
            </Link>

            <h2 className="mt-3 fw-bold">
              Create Support Ticket
            </h2>

            <p className="text-muted">
              Describe the issue you're experiencing.
              Our support team will assist you.
            </p>
          </div>

          <div className="card border-0 shadow-sm">
            <div className="card-body p-4">

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

              {categoryError && (
                <div className="alert alert-warning">
                  {categoryError}
                </div>
              )}

              <form onSubmit={handleSubmit}>

                {/* Ticket title */}
                <div className="mb-4">
                  <label
                    htmlFor="title"
                    className="form-label fw-semibold"
                  >
                    Ticket Title
                  </label>

                  <input
                    type="text"
                    id="title"
                    name="title"
                    className="form-control"
                    placeholder="Example: Unable to access my account"
                    value={formData.title}
                    onChange={handleChange}
                    minLength={5}
                    maxLength={200}
                    required
                  />

                  <div className="form-text">
                    Minimum 5 characters.
                  </div>
                </div>

                {/* Ticket category */}
                <div className="mb-4">
                  <label
                    htmlFor="category_id"
                    className="form-label fw-semibold"
                  >
                    Category
                  </label>

                  <select
                    id="category_id"
                    name="category_id"
                    className="form-select"
                    value={formData.category_id}
                    onChange={handleChange}
                    disabled={categoriesLoading || categories.length === 0}
                  >
                    <option value="">
                      {categoriesLoading
                        ? 'Loading categories...'
                        : 'Select a category (optional)'}
                    </option>

                    {categories.map((category) => (
                      <option
                        key={category.id}
                        value={category.id}
                      >
                        {category.name}
                      </option>
                    ))}
                  </select>

                  <div className="form-text">
                    Select the category that best describes your issue.
                  </div>
                </div>

                {/* Ticket description */}
                <div className="mb-4">
                  <label
                    htmlFor="description"
                    className="form-label fw-semibold"
                  >
                    Describe Your Issue
                  </label>

                  <textarea
                    id="description"
                    name="description"
                    className="form-control"
                    rows="6"
                    placeholder="Explain your problem in detail..."
                    value={formData.description}
                    onChange={handleChange}
                    minLength={10}
                    required
                  />

                  <div className="form-text">
                    Minimum 10 characters.
                  </div>
                </div>

                {/* Form actions */}
                <div className="d-flex gap-3">
                  <button
                    type="submit"
                    className="btn btn-primary px-4"
                    disabled={loading}
                  >
                    {loading ? 'Creating...' : 'Submit Ticket'}
                  </button>

                  <Link
                    to="/customer/dashboard"
                    className="btn btn-outline-secondary"
                  >
                    Cancel
                  </Link>
                </div>

              </form>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

export default CreateTicketPage;
