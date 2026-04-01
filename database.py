# SQLite Database creation and configuration

import sqlite3

# Constant with database archive name
# Archive will be created
db_order = 'orders.db'

# ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def get_connection():

    # Creates and returns a connection to the SQLite database

    # The row_factory property allows accessing columns by name
    # (Ex.: Order['product'] index preferred (Ex.: order[1]))

    # Returns:
        # sqlite3.Connection: database connection object

    conn = sqlite3.connect(db_order)
    conn.row_factory = sqlite3.Row
    return conn

# ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def init_db():
    
    # Inicializates the database creating 'orders' table if it doesn't yet exists
    # Press to call it multiple times
    
    conn = get_connection()
    
    # cursor() - Allows to execute SQL commands
    cursor = conn.cursor()
    
    #IF NOT EXIST - Ensures that the command does not fail if the table already exists
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS orders(
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       product      TEXT      NOT NULL,
                       quantity   INTEGER   NOT NULL,
                       status       TEXT      DEFAULT 'Pending',
                       created_at    TEXT      DEFAULT(datetime('now', 'localtime'))
                       )
                       ''')
    # Saves changes in .db archive
    conn.commit()
    
    # Liberates the connection (best practice)
    conn.close()
    
    print("Database inicialized with success!")

# ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

init_db()