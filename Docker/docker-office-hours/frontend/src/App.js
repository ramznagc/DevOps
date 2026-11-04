import React, { useState, useEffect } from 'react';
import ProductList from './components/ProductList';
import ProductForm from './components/ProductForm';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function App() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingProduct, setEditingProduct] = useState(null);
  const [cacheSource, setCacheSource] = useState('');

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/products`);
      if (!response.ok) throw new Error('Failed to fetch products');
      const data = await response.json();
      setProducts(data.products);
      setCacheSource(data.source);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;

    try {
      const response = await fetch(`${API_URL}/products/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete product');
      await fetchProducts();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEdit = (product) => {
    setEditingProduct(product);
  };

  const handleSave = async (product) => {
    try {
      const url = product.id
        ? `${API_URL}/products/${product.id}`
        : `${API_URL}/products`;

      const method = product.id ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(product),
      });

      if (!response.ok) throw new Error('Failed to save product');

      setEditingProduct(null);
      await fetchProducts();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCancel = () => {
    setEditingProduct(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Product Catalog</h1>
        <p className="subtitle">Docker Multi-Container Application</p>
      </header>

      <main className="container">
        {error && (
          <div className="error-message">
            Error: {error}
          </div>
        )}

        {cacheSource && (
          <div className={`cache-indicator ${cacheSource}`}>
            Data source: {cacheSource.toUpperCase()}
            {cacheSource === 'cache' && ' ⚡'}
          </div>
        )}

        <ProductForm
          product={editingProduct}
          onSave={handleSave}
          onCancel={handleCancel}
        />

        {loading ? (
          <div className="loading">Loading products...</div>
        ) : (
          <ProductList
            products={products}
            onDelete={handleDelete}
            onEdit={handleEdit}
          />
        )}
      </main>
    </div>
  );
}

export default App;