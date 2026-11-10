
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  getAdminCategories,
  createCategory,
  updateCategory,
  deleteCategory,
} from '../api/admin';

function CategoryManagementPage() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const [editingCategoryId, setEditingCategoryId] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Fetch all categories.
  const loadCategories = async () => {
    try {
      setLoading(true);
      setError('');

      const data = await getAdminCategories();
      setCategories(data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to load categories.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCategories();
  }, []);

  // Handle form input changes.
  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  // Reset the form.
  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
    });

    setEditingCategoryId(null);
  };

  // Create or update a category.
  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setSubmitting(true);
      setError('');
      setSuccess('');

      const categoryData = {
        name: formData.name.trim(),
        description: formData.description.trim() || null,
      };

      if (editingCategoryId) {
        await updateCategory(
          editingCategoryId,
          categoryData
        );

        setSuccess('Category updated successfully.');
      } else {
        await createCategory(categoryData);

        setSuccess('Category created successfully.');
      }

      resetForm();
      await loadCategories();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to save category.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  // Load category information into the form.
  const handleEdit = (category) => {
    setEditingCategoryId(category.id);

    setFormData({
      name: category.name,
      description: category.description || '',
    });

    setError('');
    setSuccess('');
  };

  // Delete a category.
  const handleDelete = async (category) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${category.name}"?`
    );

    if (!confirmed) return;

    try {
      setDeletingId(category.id);
      setError('');
      setSuccess('');

      await deleteCategory(category.id);

      setSuccess('Category deleted successfully.');

      if (editingCategoryId === category.id) {
        resetForm();
      }

      await loadCategories();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to delete category.'
      );
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) {
    return (
      <div className="container mt-5 text-center">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>

        <p className="mt-2">Loading categories...</p>
      </div>
    );
  }

  return (
    <div className="container-fluid py-4">

      {/* Page heading */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2>Category Management</h2>
          <p className="text-muted mb-0">
            Create and manage ticket categories.
          </p>
        </div>

        <Link
          to="/admin/dashboard"
          className="btn btn-outline-secondary"
        >
          Back to Dashboard
        </Link>
      </div>

      {/* Alerts */}
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

      <div className="row g-4">

        {/* Category form */}
        <div className="col-lg-4">
          <div className="card shadow-sm">
            <div className="card-body">

              <h5 className="card-title mb-3">
                {editingCategoryId
                  ? 'Edit Category'
                  : 'Create Category'}
              </h5>

              <form onSubmit={handleSubmit}>

                <div className="mb-3">
                  <label
                    htmlFor="categoryName"
                    className="form-label"
                  >
                    Category Name
                  </label>

                  <input
                    id="categoryName"
                    type="text"
                    name="name"
                    className="form-control"
                    value={formData.name}
                    onChange={handleChange}
                    minLength={2}
                    maxLength={100}
                    required
                    placeholder="e.g. Technical Support"
                  />
                </div>

                <div className="mb-3">
                  <label
                    htmlFor="categoryDescription"
                    className="form-label"
                  >
                    Description
                  </label>

                  <textarea
                    id="categoryDescription"
                    name="description"
                    className="form-control"
                    rows="4"
                    value={formData.description}
                    onChange={handleChange}
                    placeholder="Describe this category..."
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submitting}
                >
                  {submitting
                    ? 'Saving...'
                    : editingCategoryId
                      ? 'Update Category'
                      : 'Create Category'}
                </button>

                {editingCategoryId && (
                  <button
                    type="button"
                    className="btn btn-outline-secondary ms-2"
                    onClick={resetForm}
                  >
                    Cancel
                  </button>
                )}

              </form>
            </div>
          </div>
        </div>

        {/* Categories table */}
        <div className="col-lg-8">
          <div className="card shadow-sm">
            <div className="card-body">

              <div className="d-flex justify-content-between align-items-center mb-3">
                <h5 className="card-title mb-0">
                  All Categories
                </h5>

                <span className="badge bg-primary">
                  {categories.length} Categories
                </span>
              </div>

              <div className="table-responsive">
                <table className="table table-hover align-middle">

                  <thead className="table-light">
                    <tr>
                      <th>Name</th>
                      <th>Description</th>
                      <th>Actions</th>
                    </tr>
                  </thead>

                  <tbody>
                    {categories.length === 0 ? (
                      <tr>
                        <td
                          colSpan="3"
                          className="text-center py-4"
                        >
                          No categories found. Create your first category.
                        </td>
                      </tr>
                    ) : (
                      categories.map((category) => (
                        <tr key={category.id}>
                          <td className="fw-semibold">
                            {category.name}
                          </td>

                          <td>
                            {category.description || (
                              <span className="text-muted">
                                No description
                              </span>
                            )}
                          </td>

                          <td>
                            <div className="d-flex gap-2">

                              <button
                                className="btn btn-sm btn-outline-primary"
                                onClick={() => handleEdit(category)}
                              >
                                Edit
                              </button>

                              <button
                                className="btn btn-sm btn-outline-danger"
                                disabled={deletingId === category.id}
                                onClick={() => handleDelete(category)}
                              >
                                {deletingId === category.id
                                  ? 'Deleting...'
                                  : 'Delete'}
                              </button>

                            </div>
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

      </div>
    </div>
  );
}

export default CategoryManagementPage;
