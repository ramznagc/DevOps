import React from 'react';

function ProductList({ products, onDelete, onEdit }) {
  return (
    <div className="product-list">
      <h2>Products ({products.length})</h2>
      {products.length === 0 ? (
        <p className="no-products">No products found. Add your first product above!</p>
      ) : (
        <div className="products-grid">
          {products.map((product) => (
            <div key={product.id} className="product-card">
              <div className="product-header">
                <h3>{product.name}</h3>
                <span className="product-price">${product.price}</span>
              </div>
              <p className="product-description">{product.description}</p>
              <div className="product-footer">
                <span className="product-stock">
                  Stock: {product.stock}
                </span>
                <div className="product-actions">
                  <button
                    onClick={() => onEdit(product)}
                    className="btn btn-edit"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => onDelete(product.id)}
                    className="btn btn-delete"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ProductList;