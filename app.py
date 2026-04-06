# Flask Back-end: REST API routes

from flask import Flask, jsonify, request
from flask_cors import CORS
from database import init_db, get_connection

# Creates a Flash aplication instance
app = Flask(__name__, static_folder='static', static_url_path='')

# Allows CORS
CORS(app)

# 1st Route - Initial page ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    """
    Feed the index.html file from the static folder
    """
    return app.send_static_file('index.html')

# 2nd Route - API status ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
@app.route('/status')
def status():
    """
    API verification route (health)
    Returns a json informing that the server is active
    """
    return jsonify({
        "status": "online",
        "system": "Production Order System",
        "version": "1.0.0",
        "message": "Hello, Factory, API is working!"
    })
    
# 3rd Route - List all the orders (GET) ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
@app.route('/orders', methods=['GET'])
def list_orders():
    """
    List all the registered production orders
    Method HTTP: GET
    URL: http://localhost:5000/orders
    Returns: List and orders in JSON format
    """
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders ORDER BY id DESC')
    orders = cursor.fetchall()
    conn.close()

    # Convert each SQLite Row into a Python dictionary to serialize into JSON
    return jsonify([dict(o) for o in orders])

# 4th Route - Search a specific order by id (GET) ───────────────────────────────────────────────────────────────────────────────────────────────────
@app.route('/orders/<int:order_id>', methods=['GET'])
def search_order(order_id):
    """
    Retrieves a single production order by ID
    
    URL Parameters:
        order id(int): Order ID to be fetched
    Returns:
        200 + order's JSON, of the order is found
        400 + error message, if it doesn't exists
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Uses a parameterized query to safely bind the ID
    cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    order = cursor.fetchone() # Returns a single register or None
    conn.close()
    
    if order is None:
        return jsonify({'error': f'Order {order_id} not found'}), 404
    return jsonify(dict(order)), 200

# 5th Route - Creates a new production order (POST) ─────────────────────────────────────────────────────────────────────────────────────────────────
@app.route('/orders', methods=['POST'])
def order_create():
    """
    Create a new production order from sent JSON data
    
    Expected body (JSON):

        product     (str) : Product name    - Required
        quantity    (int) : Part quantity   - Required, > 0
        status      (str) : Optional        - Standard : "Pending"
        
        Returns:
            201 : Order's JSON created, in sucessfull case
            400 : Error message, if data is invalid
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'The request body is missing or invalid.'}), 400
    
    # Required field check
    product = data.get('product', '').strip()
    if not product:
        return jsonify({'error': '"Product" field is required and it cant be null'}), 400
    
    # Check if quantity is a positive and integer
    try:
        quantity = data.get('quantity')
        if quantity is None:
            return jsonify({'error': '"Quantity" field is required'}), 400
            
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({'error': 'Quantity must be greater than zero'}), 400
            
    except (ValueError, TypeError):
        return jsonify({'error': '"Quantity" field must be a valid number'}), 400
    
    # Status (*pending, in progress, completed) - optional
    valid_status = ['Pending', 'In progress', 'Completed']
    status = data.get('status', 'Pending')
    if status not in valid_status:
        return jsonify({'error': f'Invalid status. Use {valid_status}'}), 400
    # Database insertion
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO orders (product, quantity, status) VALUES (?, ?, ?)', (product, quantity, status)
    )
    conn.commit()
    
    # Saving the database generated ID
    new_id = cursor.lastrowid
    conn.close()
    
    # Search for the newly created records
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE id = ?', (new_id,))
    new_order = cursor.fetchone()
    conn.close()
    # 201 - Returns "created" with full register
    return jsonify(dict(new_order)), 201
# 6th Route - Update the status of a production order (PUT) ─────────────────────────────────────────────────────────────────────────────────────────
@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    """
    Updates the status of an existing production order.
    
    URL Parameters:
        order_id (int) : ID of the order to update
        
    Expected body (JSON):
        status (str) : New status. Accepted values:
                       'Pending', 'In progress', 'Completed'.
                       
    Returns:
        200 : JSON of the updated order
        400 : Error message if the status is invalid
        404 : Error message if the order was not found
    """
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid or missing requisit body.'}), 400
    
    # Status field validation
    valid_status = ['Pending', 'In progress', 'Completed']
    new_status = data.get('status', '').strip()
    
    if not new_status:
        return jsonify({'error': '"Status" field is required.'}), 400
    
    if new_status not in valid_status:
        return jsonify({'error' : f'Invalid status! Please use the allowed values: {valid_status}'}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM orders WHERE id = ?', (order_id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({'error' : f'Order {order_id} not found'}), 404
    
    # Actually updating the record
    cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
    
    conn.commit()
    conn.close()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    updated_order = cursor.fetchone()
    conn.close()
    
    return jsonify(dict(updated_order)), 200

# Entry point ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
if __name__=='__main__':
    init_db()
    
    app.run(debug=True, host='0.0.0.0', port=5000)