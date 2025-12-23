import os
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import logging
import sys
from urllib.parse import urlparse
import threading
import math

# Configure Logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global Stress Test State
is_stressing = False

def stress_cpu():
    """Function to generate CPU load."""
    global is_stressing
    logger.info("Stress test started (CPU load).")
    while is_stressing:
        # Perform heavy calculation (e.g., primes)
        [x * x for x in range(1000)]
        # Check flag frequently to allow quick stop
        if not is_stressing:
            break
    logger.info("Stress test stopped.")

# Database Connection Details
DATABASE_URL = os.environ.get("DATABASE_URL")

def parse_db_url(url):
    """Parses the DATABASE_URL string."""
    if not url:
        return None
    try:
        # Expected format: mysql://username:password@host:port/databasename
        parsed = urlparse(url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 3306,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/')
        }
    except Exception as e:
        logger.error(f"Failed to parse DATABASE_URL: {e}")
        return None

def get_db_connection():
    """Establishes a connection to the database."""
    db_config = parse_db_url(DATABASE_URL)
    
    if not db_config:
        logger.error("DATABASE_URL is missing or invalid.")
        return None

    # Mask password for logging
    log_config = db_config.copy()
    if log_config.get('password'):
        log_config['password'] = '******'
    
    logger.debug(f"Attempting to connect to database: {log_config['host']}:{log_config['port']} / {log_config['database']}")

    try:
        conn = mysql.connector.connect(**db_config)
        logger.debug("Database connection established successfully.")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Error connecting to database: {err}", exc_info=True)
        return None

def init_db():
    """Initializes the database table if it doesn't exist."""
    logger.info("Initializing database...")
    for i in range(10):
        try:
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
                logger.info("Database initialized successfully.")
                return
        except Exception as e:
            logger.warning(f"Database wait attempt {i+1}/10... ({e})")
            time.sleep(2)
    logger.critical("Could not initialize database after multiple attempts.")
    sys.exit(1)

# Request Logging Middleware
@app.before_request
def log_request_info():
    logger.debug(f"Handling Request: {request.method} {request.path}")
    if request.is_json:
        logger.debug(f"Request Body: {request.get_json()}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks")
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        logger.debug(f"Retrieved {len(tasks)} tasks.")
        return jsonify(tasks)
    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.json
    if not data or 'content' not in data:
        logger.warning("Invalid request: Content is required")
        return jsonify({"error": "Content is required"}), 400
    
    content = data['content']
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (content) VALUES (%s)", (content,))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        logger.info(f"Task added with ID: {new_id}")
        return jsonify({"id": new_id, "content": content, "message": "Task added"}), 201
    except Exception as e:
        logger.error(f"Error adding task: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
        conn.commit()
        rows_affected = cursor.rowcount
        cursor.close()
        conn.close()
        
        if rows_affected == 0:
            logger.warning(f"Task with ID {id} not found for deletion.")
            return jsonify({"error": "Task not found"}), 404
        
        logger.info(f"Task with ID {id} deleted.")
        return jsonify({"message": "Task deleted", "id": id}), 200
    except Exception as e:
        logger.error(f"Error deleting task: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/stress/start', methods=['POST'])
def start_stress():
    global is_stressing
    data = request.json
    if not data or not data.get('cpu_load'):
         return jsonify({"error": "Invalid payload"}), 400

    if is_stressing:
        return jsonify({"status": "Stress test already running", "pid": os.getpid()}), 400

    is_stressing = True
    thread = threading.Thread(target=stress_cpu)
    thread.start()
    
    return jsonify({"status": "Stress test started", "pid": os.getpid()}), 200

@app.route('/stress/stop', methods=['POST'])
def stop_stress():
    global is_stressing
    is_stressing = False
    return jsonify({"status": "Stress test stopped"}), 200

# Initialize DB on startup (Fail Fast)
init_db()

if __name__ == '__main__':
    # Run server for development only
    logger.info("Starting Flask application on port 5000...")
    app.run(host='0.0.0.0', port=5000)
