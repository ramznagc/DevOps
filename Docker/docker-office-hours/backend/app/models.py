"""
Database models for the e-commerce application
"""

class Product:
    """Product model representing items in the catalog"""

    def __init__(self, id=None, name=None, description=None, price=None, stock=None):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.stock = stock

    def to_dict(self):
        """Convert product to dictionary format"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else None,
            'stock': self.stock
        }

    @staticmethod
    def from_dict(data):
        """Create product from dictionary"""
        return Product(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            price=data.get('price'),
            stock=data.get('stock')
        )