"""
Redis cache utilities
"""
import json
import redis
import os

# Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

def get_cached_products():
    """Get products from cache"""
    try:
        cached = redis_client.get('products:all')
        if cached:
            return json.loads(cached)
        return None
    except Exception as e:
        print(f"Cache error: {e}")
        return None

def set_cached_products(products, ttl=300):
    """Cache products with TTL (default 5 minutes)"""
    try:
        redis_client.setex(
            'products:all',
            ttl,
            json.dumps(products)
        )
    except Exception as e:
        print(f"Cache error: {e}")

def invalidate_products_cache():
    """Invalidate products cache"""
    try:
        product_keys = list(redis_client.scan_iter('product:*'))
        redis_client.delete('products:all', *product_keys)
    except Exception as e:
        print(f"Cache error: {e}")

def get_cached_product(product_id):
    """Get single product from cache"""
    try:
        cached = redis_client.get(f'product:{product_id}')
        if cached:
            return json.loads(cached)
        return None
    except Exception as e:
        print(f"Cache error: {e}")
        return None

def set_cached_product(product_id, product, ttl=300):
    """Cache single product"""
    try:
        redis_client.setex(
            f'product:{product_id}',
            ttl,
            json.dumps(product)
        )
    except Exception as e:
        print(f"Cache error: {e}")