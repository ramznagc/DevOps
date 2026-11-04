"""
API routes for product management
"""
from flask import Blueprint, request, jsonify
import psycopg2
import os
from .models import Product
from . import cache

api = Blueprint('api', __name__)

def get_db_connection():
    """Create database connection"""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'postgres'),
        database=os.getenv('DB_NAME', 'ecommerce'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )
    return conn

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'backend'}), 200

@api.route('/products', methods=['GET'])
def get_products():
    """Get all products with caching"""
    # Check cache first
    cached_products = cache.get_cached_products()
    if cached_products:
        return jsonify({
            'products': cached_products,
            'source': 'cache'
        }), 200

    # If not in cache, get from database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, price, stock FROM products ORDER BY id')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    products = []
    for row in rows:
        product = Product(
            id=row[0],
            name=row[1],
            description=row[2],
            price=row[3],
            stock=row[4]
        )
        products.append(product.to_dict())

    # Cache the results
    cache.set_cached_products(products)

    return jsonify({
        'products': products,
        'source': 'database'
    }), 200

@api.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product by ID"""
    # Check cache
    cached_product = cache.get_cached_product(product_id)
    if cached_product:
        return jsonify({
            'product': cached_product,
            'source': 'cache'
        }), 200

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, name, description, price, stock FROM products WHERE id = %s',
        (product_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row is None:
        return jsonify({'error': 'Product not found'}), 404

    product = Product(
        id=row[0],
        name=row[1],
        description=row[2],
        price=row[3],
        stock=row[4]
    )

    product_dict = product.to_dict()
    cache.set_cached_product(product_id, product_dict)

    return jsonify({
        'product': product_dict,
        'source': 'database'
    }), 200

@api.route('/products', methods=['POST'])
def create_product():
    """Create new product"""
    data = request.get_json()

    # Validation
    required_fields = ['name', 'description', 'price', 'stock']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO products (name, description, price, stock) VALUES (%s, %s, %s, %s) RETURNING id',
        (data['name'], data['description'], data['price'], data['stock'])
    )
    product_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    # Invalidate cache
    cache.invalidate_products_cache()

    return jsonify({
        'message': 'Product created successfully',
        'product_id': product_id
    }), 201

@api.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update existing product"""
    data = request.get_json()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if product exists
    cursor.execute('SELECT id FROM products WHERE id = %s', (product_id,))
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Product not found'}), 404

    # Update product
    cursor.execute(
        'UPDATE products SET name = %s, description = %s, price = %s, stock = %s WHERE id = %s',
        (data['name'], data['description'], data['price'], data['stock'], product_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    # Invalidate cache
    cache.invalidate_products_cache()

    return jsonify({'message': 'Product updated successfully'}), 200

@api.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete product"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
    rows_deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    if rows_deleted == 0:
        return jsonify({'error': 'Product not found'}), 404

    # Invalidate cache
    cache.invalidate_products_cache()

    return jsonify({'message': 'Product deleted successfully'}), 200