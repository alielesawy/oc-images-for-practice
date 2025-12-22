import os
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

# Database Connection Details
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_NAME = os.environ.get("DB_NAME", "todo_db")

def get_db_connection():
    """Establishes a connection to the database."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

def init_db():
    """Initializes the database table if it doesn't exist."""
    print("Initializing database...")
    # Retry logic for database connection (useful for container startup order)
    for _ in range(10):
        try:
            # Connect to MySQL server first to create DB if needed (optional, assuming DB exists per prompt reqs but safe to check)
            # However, prompt says "Database Name" in env, so we assume DB exists or we connect to it.
            # We will just connect to the DB directly.
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        content TEXT NOT NULL
                    )
                """)
                conn.commit()
                cursor.close()
                conn.close()
                print("Database initialized successfully.")
                return
        except Exception as e:
            print(f"Database wait... ({e})")
            time.sleep(2)
    print("Could not initialize database.")

# Initialize DB on start (in a real production app, this might be a separate migration step)
# For this simple task, we'll do it before first request or just let it run on import if we can satisfy the connection,
# but usually it's better to verify connection on start.
# We will disable auto-run on import to avoid build-time issues, but prompt asks for a simple app.
# Let's add a before_first_request or just call it if we run as main.
# Flask 2.3+ deprecated before_first_request. We can just run it at the bottom.

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(tasks)

@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.json
    if not data or 'content' not in data:
        return jsonify({"error": "Content is required"}), 400
    
    content = data['content']
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (content) VALUES (%s)", (content,))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    return jsonify({"id": new_id, "content": content, "message": "Task added"}), 201

@app.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
    conn.commit()
    rows_affected = cursor.rowcount
    cursor.close()
    conn.close()
    
    if rows_affected == 0:
        return jsonify({"error": "Task not found"}), 404
        
    return jsonify({"message": "Task deleted", "id": id}), 200

if __name__ == '__main__':
    # Attempt to initialize DB
    init_db()
    
    # Run server
    app.run(host='0.0.0.0', port=5000)
