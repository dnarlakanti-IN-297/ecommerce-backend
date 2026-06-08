from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://ecommerce:password@localhost:5432/ecommerce'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(500))
    rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    shipping_address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

# Routes - Products
@app.route('/api/products', methods=['GET'])
def get_products():
    category = request.args.get('category')
    search = request.args.get('search')

    query = Product.query

    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    products = query.all()

    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'price': p.price,
        'category': p.category,
        'stock': p.stock,
        'image_url': p.image_url,
        'rating': p.rating
    } for p in products])

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)

    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'category': product.category,
        'stock': product.stock,
        'image_url': product.image_url,
        'rating': product.rating
    })

# Routes - Cart (using session-based cart for simplicity)
cart_storage = {}

@app.route('/api/cart', methods=['GET'])
def get_cart():
    session_id = request.headers.get('X-Session-ID', 'default')
    cart = cart_storage.get(session_id, [])

    total = sum(item['price'] * item['quantity'] for item in cart)

    return jsonify({
        'items': cart,
        'total': total,
        'item_count': sum(item['quantity'] for item in cart)
    })

@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    session_id = request.headers.get('X-Session-ID', 'default')
    data = request.get_json()

    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    product = Product.query.get_or_404(product_id)

    if product.stock < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400

    if session_id not in cart_storage:
        cart_storage[session_id] = []

    cart = cart_storage[session_id]

    # Check if product already in cart
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            break
    else:
        cart.append({
            'product_id': product.id,
            'name': product.name,
            'price': product.price,
            'quantity': quantity,
            'image_url': product.image_url
        })

    return jsonify({'success': True, 'cart': get_cart().json})

@app.route('/api/cart/<int:product_id>', methods=['DELETE'])
def remove_from_cart(product_id):
    session_id = request.headers.get('X-Session-ID', 'default')

    if session_id in cart_storage:
        cart_storage[session_id] = [
            item for item in cart_storage[session_id]
            if item['product_id'] != product_id
        ]

    return jsonify({'success': True})

# Routes - Orders
@app.route('/api/checkout', methods=['POST'])
def checkout():
    session_id = request.headers.get('X-Session-ID', 'default')
    data = request.get_json()

    cart = cart_storage.get(session_id, [])

    if not cart:
        return jsonify({'error': 'Cart is empty'}), 400

    total = sum(item['price'] * item['quantity'] for item in cart)

    # Create order (simplified - no user auth for now)
    order = Order(
        user_id=1,  # Default user
        total_amount=total,
        status='confirmed',
        shipping_address=data.get('shipping_address', '')
    )

    db.session.add(order)
    db.session.commit()

    # Add order items
    for item in cart:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item['product_id'],
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(order_item)

        # Update stock
        product = Product.query.get(item['product_id'])
        product.stock -= item['quantity']

    db.session.commit()

    # Clear cart
    cart_storage[session_id] = []

    return jsonify({
        'success': True,
        'order_id': order.id,
        'total': total,
        'status': 'confirmed'
    })

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get_or_404(order_id)

    items = OrderItem.query.filter_by(order_id=order_id).all()

    return jsonify({
        'id': order.id,
        'total_amount': order.total_amount,
        'status': order.status,
        'shipping_address': order.shipping_address,
        'created_at': order.created_at.isoformat(),
        'items': [{
            'product_id': item.product_id,
            'quantity': item.quantity,
            'price': item.price
        } for item in items]
    })

# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'backend'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
