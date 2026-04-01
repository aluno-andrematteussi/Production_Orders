# Flask Back-end: REST API routes

from flask import Flask, jsonify, request
from flask_cors import CORS
from database import init_db, get_connection

# Creates a Flash aplication instance 
app = Flask(__name__, static_folder='static', static_url_path='')

# Allows CORS
CORS(app)

# 1st Route - Initial page
@app.route('/')
def index():
    # Feed the index.html file from the static folder
    return app.send_static_file('index.html')

# 2nd Route - API status
@app.route('/status')
def status():
    
    # API verification route (health)
    # Returns a json informing that the server is active
    
    return jsonify({
        "status": "online",
        "system": "Production Order System",
        "version": "1.0.0",
        "message": "Hello, Factory, API is working!"
    })
    
# 3rd Route - List all the orders (GET)
@app.route('/orders', methods=['GET'])
def list_orders():
    
    # List all the registered production orders
    # Method HTTP: GET
    # URL: http://localhost:5000/orders
    # Returns: List and orders in JSON format.
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders ORDER BY id DESC')
    orders = cursor.fetchall()
    conn.close()

    # Convert each SQLite Row into a Python dictionary to serialize into JSON
    return jsonify([dict(o) for o in orders])

# Route by ID - Search a specific order by id (GET)
@app.route('/orders/<int:order_id>', methods=['GET'])
def search_order(order_id):
    # Retrieves a single production order by ID
    
    # URL Parameters:
        # order id(int): Order ID to be fetched
    # Returns:
        # 200 + order's JSON, of the order is found.
        # 400 + error message, if it doesn't exists.
    conn = get_connection()
    cursor = conn.cursor()
    # Uses a parameterized query to safely bind the ID
    cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    order = cursor.fetchone() # Returns a single register or None
    conn.close()
    
    if order is None:
        return jsonify({'error': f'Order {order_id} not found'}), 404
    return jsonify(dict(order)), 200

# Creates a new production order
@app.route('orders', methods=['POST'])
def order_create():
    
    # Create a new production order from sent JSON data
    
    # Expected body (JSON):

    #     product     (str) : Product name    - Required
    #     quantity    (int) : Part quantity   - Required, > 0
    #     status      (str) : Optional        - Standard : "Pending"
        
    #     Return:
    #         201 : Order's JSON created, in sucessfull case
    #         400 : Error message, if data is invalid
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'The request body is missing or invalid.'}), 400
    
    # Required field check
    product = data.get('produto', '').strip()
    if not product:
        return jsonify({'error': '"Product" field is required and it cant be null'})
    
    # Check if quantity is a positive and integer
    try:
        quantity = data.get('quantity')
        if quantity is None:
            return jsonify({'error': '"Quantity" field is required'}), 400
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'error': '"Quantity" field must be a positive integer'}), 400
    
    # Status (*pending, in progress, completed) - optional
    valid_status = ['Pending', 'In progress', 'Completed']
    status = data.get('status', 'Pending')
    if status not in valid_status:
        return jsonify({'error': f'Invalid status. Use {valid_status}'}), 400
    
# Entry point
if __name__=='__main__':
    init_db()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
    