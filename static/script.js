// Base URL of the Flask API
// In production, we change this to: 'https://myserver.com'
const API_URL = 'http://localhost:5000';

// 5.3 Checking the API status
async function checkStatus() {
    const badge = document.getElementById('status-badge');
    try {
        const resp = await fetch(`${API_URL}/status`);
        const data = await resp.json();
        badge.textContent = `API Online | ${data.total_orders} orders`;
        badge.className = 'online';
    } catch (error) {
        badge.textContent = 'API Offline';
        badge.className = 'offline';
    }
}

// 5.4 Function loadOrders() - GET /orders
async function loadOrders() {
    const loading = document.getElementById('loading');
    const noData = document.getElementById('no-data');
    const table = document.getElementById('orders-table');
    const body = document.getElementById('table-body');

    // Shows loading indicator and hides the table
    loading.classList.remove('hidden');
    table.classList.add('hidden');
    noData.classList.add('hidden');

    try {
        // Makes the GET /orders request
        const response = await fetch(`${API_URL}/orders`);
        
        // Converts the response (JSON text) into a JavaScript array
        const orders = await response.json();

        // Hides the loading
        loading.classList.add('hidden');

        // If there are no orders, shows message and exits the function
        if (orders.length === 0) {
            noData.classList.remove('hidden');
            return;
        }

        // For each order, creates a <tr> row in the table
        body.innerHTML = orders.map(order => ` 
            <tr id="row-${order.id}"> 
                <td>${order.id}</td> 
                <td>${order.product}</td> 
                <td>${order.quantity}</td> 
                <td>${renderBadge(order.status)}</td> 
                <td>${order.created_at || 'N/A'}</td> 
                <td> 
                    <select class="select-status" onchange="updateStatus(${order.id}, this.value)"> 
                        <option value="Pending" ${order.status === 'Pending' ? 'selected' : ''}>Pending</option> 
                        <option value="In progress" ${order.status === 'In progress' ? 'selected' : ''}>In progress</option> 
                        <option value="Completed" ${order.status === 'Completed' ? 'selected' : ''}>Completed</option> 
                    </select> 
                    
                    <button class="btn-edit" onclick="editOrder(${order.id}, '${order.product}', ${order.quantity})"> 
                        Edit 
                    </button>

                    <button class="btn-delete" onclick="deleteOrder(${order.id})"> 
                        Delete 
                    </button> 
                </td> 
            </tr> 
        `).join('');

        // Shows the filled table
        table.classList.remove('hidden');

    } catch (error) {
        loading.classList.add('hidden');
        console.error('Error loading orders:', error);
        showMessage('Error connecting to the API. Is the server running?', 'error');
    }
}

// Returns the colored badge HTML according to the status
function renderBadge(status) {
    const classes = {
        'Pending': 'badge badge-pending',
        'In progress': 'badge badge-progress',
        'Completed': 'badge badge-completed',
    };
    const cls = classes[status] || 'badge';
    return `<span class="${cls}">${status}</span>`;
}

async function createOrder() {
    // Captures the values from the HTML fields
    const product = document.getElementById('product').value.trim();
    const quantity = document.getElementById('quantity').value;
    const status = document.getElementById('new-status').value;

    // Front-end validation (before calling the API)
    if (!product) {
        showMessage('Please fill in the product name.', 'error');
        document.getElementById('product').focus();
        return;
    }

    if (!quantity || Number(quantity) <= 0) {
        showMessage('Please provide a valid quantity (positive number).', 'error');
        document.getElementById('quantity').focus();
        return;
    }

    // Disables the button to prevent double clicking
    const btn = document.getElementById('btn-register');
    btn.disabled = true;
    btn.textContent = 'Registering...';

    try {
        const response = await fetch(`${API_URL}/orders`, {
            method: 'POST',
            // Content-Type tells Flask that the body is JSON
            headers: { 'Content-Type': 'application/json' },
            // JSON.stringify converts JS object to JSON string
            body: JSON.stringify({
                product: product,
                quantity: Number(quantity),
                status: status
            })
        });

        const data = await response.json();

        if (response.ok) { // response.ok = true for status 200-299
            showMessage(`Order #${data.id} registered successfully!`, 'success');
            clearForm();
            await loadOrders();  // Updates the table
            await checkStatus(); // Updates the counter in the header
        } else {
            // Shows the error message returned by Flask
            showMessage(data.error || 'Error registering.', 'error');
        }

    } catch (error) {
        showMessage('Error connecting to the API.', 'error');
        console.error(error);
    } finally {
        // The finally block ALWAYS executes, with or without error
        btn.disabled = false;
        btn.textContent = 'Register Order';
    }
}

// Clears the form fields after successful registration
function clearForm() {
    document.getElementById('product').value = '';
    document.getElementById('quantity').value = '';
    document.getElementById('new-status').value = 'Pending';
}

async function updateStatus(id, newStatus) {
    try {
        // Sends a PUT request to the order's specific route
        const response = await fetch(`${API_URL}/orders/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(`Status of Order #${id} updated to '${newStatus}'.`, 'success');
            
            // Updates only the badge in the row, without reloading the whole table (faster)
            const row = document.getElementById(`row-${id}`);
            if (row) {
                const tdStatus = row.cells[4]; // Locates the status cell (column 4)
                tdStatus.innerHTML = renderBadge(newStatus); // Replaces HTML with the new badge
            }
            await checkStatus(); // Updates the general counter at the top
        } else {
            showMessage(data.error || 'Error updating status.', 'error');
            // If there's an error, reloads the table to reset the select to its original value
            await loadOrders();
        }
    } catch (error) {
        showMessage('Connection error.', 'error');
        console.error(error);
    }
}

async function deleteOrder(id) {
    // Shows a browser confirmation alert
    const confirmed = window.confirm(`Are you sure you want to delete Order #${id}? This action is permanent.`);
    
    if (!confirmed) return; // If the user clicks "Cancel", stops execution here

    try {
        const response = await fetch(`${API_URL}/orders/${id}`, {
            method: 'DELETE' // The DELETE method usually doesn't need a 'body'
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(data.message, 'success');

            // Removes the row from the table visually without needing to reload everything
            const row = document.getElementById(`row-${id}`);
            if (row) row.remove();

            // Checks if the table became empty to show the "No data" message
            const body = document.getElementById('table-body');
            if (body.children.length === 0) {
                document.getElementById('orders-table').classList.add('hidden');
                document.getElementById('no-data').classList.remove('hidden');
            }
            await checkStatus(); // Updates the order counter
        } else {
            showMessage(data.error || 'Error deleting.', 'error');
        }
    } catch (error) {
        showMessage('Connection error.', 'error');
        console.error(error);
    }
}

function showMessage(text, type) {
    const div = document.getElementById('message');
    div.textContent = text;
    
    // Defines the CSS class based on type (e.g., 'message success' or 'message error')
    div.className = `message ${type}`; 
    
    // Makes the message visible
    div.classList.remove('hidden');

    // Timer: Hides the message automatically after 4 seconds (4000ms)
    setTimeout(() => {
        div.classList.add('hidden');
    }, 4000);
}

async function editOrder(id, currentProduct, currentQuantity) {
    const newProduct = window.prompt(`Editing order #${id}\nMotor/Product name:`, currentProduct);
    if (newProduct === null) return; 

    const newQuantityStr = window.prompt(`New quantity for '${newProduct}':`, currentQuantity);
    if (newQuantityStr === null) return;

    const newQuantity = Number(newQuantityStr);

    if (!newProduct.trim()) {
        showMessage('The product name cannot be empty.', 'error');
        return;
    }
    if (isNaN(newQuantity) || newQuantity <= 0) {
        showMessage('The quantity must be a number greater than zero.', 'error');
        return;
    }

    if (newProduct.trim() === currentProduct && newQuantity === currentQuantity) {
        return; 
    }

    try {
        const response = await fetch(`${API_URL}/orders/${id}/info`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product: newProduct.trim(),
                quantity: newQuantity
            })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(`Order #${id} updated successfully!`, 'success');
            await loadOrders(); 
        } else {
            showMessage(data.error || 'Error updating the order.', 'error');
        }
    } catch (error) {
        showMessage('Connection error while trying to edit.', 'error');
        console.error(error);
    }
}

// Executes when the page loads
window.onload = async function() {
    // Fetches the server status (Online/Offline)
    await checkStatus();
    // Fetches the order list from the database
    await loadOrders();
};