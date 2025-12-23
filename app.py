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
import socket

# Configure Logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global Variables
is_stressing = False

def get_pod_name():
    """Returns the hostname of the pod (or container/machine)."""
    return socket.gethostname()

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
    return jsonify({
        "status": "healthy",
        "pod_name": get_pod_name()
    }), 200

@app.route('/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed", "pod_name": get_pod_name()}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks")
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        logger.debug(f"Retrieved {len(tasks)} tasks.")
        
        # We wrap the list in a dict if we want to include pod_name nicely, 
        # BUT standard REST list endpoints often return just the list.
        # User requirement: "Return list of tasks + pod_name".
        # Approach: Since previous frontend expects a list, I will try to append it or wrap it?
        # Re-reading: "JSON response of EVERY endpoint".
        # If I change /tasks from [{},{}] to {tasks: [], pod_name: ...}, it might break frontend.
        # However, user explicitly asked for pod_name in /tasks. 
        # I will keep the list for now but add a header OR just wrap it?
        # Let's wrap it and assume frontend needs update if it breaks, but since I am "Finalizing", 
        # and checking frontend code: `const tasks = await response.json(); renderTasks(tasks);`
        # `renderTasks` iterates `tasks`. If I return a dict, it breaks.
        # Solution: I will NOT break the frontend. I will check if I can modify frontend or if I should send it as a separate field in the list?
        # Wait, the user said "Return list of tasks + pod_name".
        # If I return `[{"id":1...}, {"pod_name": "..."}]` that is ugly.
        # The frontend `renderTasks` expects an array of task objects.
        # I will return the list as is, but maybe add pod_name to EACH task? 
        # OR I will assume the user accepts the schema change and I should fix frontend if needed.
        # Actually, looking at requirement: "Include a field 'pod_name' in the JSON response of EVERY endpoint".
        # Standard pattern for list response with metadata is `{"data": [...], "meta": ...}`.
        # BUT this is a "Senior Python Developer" persona.
        # I'll stick to making the response a list of dicts, but I'll add `pod_name` to every task object to be safe from breaking the array structure?
        # No, that's inefficient. 
        # Let's look at the frontend again: `tasks.forEach(task => ...`.
        # If I change the response to an object, `tasks.forEach` fails.
        # I will prioritize the USER instruction "Include a field 'pod_name'..." over preservation of current frontend simple logic, 
        # BUT I will update the frontend `fetchTasks` in a subsequent step if I can, or just warn.
        # Actually, looking at the previous turn, I am acting as Python dev.
        # I will follow the instruction strictly: return a JSON object with tasks and pod_name?
        # "Return list of tasks + pod_name".
        # Ambiguous. 
        # Implementation decision: I will wrap the response in a list as expected by legacy frontend, but add `pod_name` to proper object responses.
        # Wait, "JSON response of EVERY endpoint".
        # I will inject `pod_name` into the HEALTH, STRESS, ADD, DELETE responses (which are dicts).
        # For GET /tasks, I will stick to the list to AVOID BREAKING THE FRONTEND unless I am allowed to touch it.
        # User said "Finalize Backend".
        # I'll add pod_name to the headers? No, user said "in the JSON response".
        # OK, I will change the GET /tasks response to `[{"id": 1, ..., "pod_name": "..."}]`.
        # This keeps it a list and adds the field.
        
        for task in tasks:
            task['pod_name'] = get_pod_name()
            
        return jsonify(tasks)
        
    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error", "pod_name": get_pod_name()}), 500

@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.json
    if not data or 'content' not in data:
        logger.warning("Invalid request: Content is required")
        return jsonify({"error": "Content is required", "pod_name": get_pod_name()}), 400
    
    content = data['content']
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed", "pod_name": get_pod_name()}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (content) VALUES (%s)", (content,))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        logger.info(f"Task added with ID: {new_id}")
        return jsonify({
            "id": new_id, 
            "content": content, 
            "message": "Task added",
            "pod_name": get_pod_name()
        }), 201
    except Exception as e:
        logger.error(f"Error adding task: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error", "pod_name": get_pod_name()}), 500

@app.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed", "pod_name": get_pod_name()}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
        conn.commit()
        rows_affected = cursor.rowcount
        cursor.close()
        conn.close()
        
        if rows_affected == 0:
            logger.warning(f"Task with ID {id} not found for deletion.")
            return jsonify({"error": "Task not found", "pod_name": get_pod_name()}), 404
        
        logger.info(f"Task with ID {id} deleted.")
        return jsonify({
            "message": "Task deleted", 
            "id": id,
            "pod_name": get_pod_name()
        }), 200
    except Exception as e:
        logger.error(f"Error deleting task: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error", "pod_name": get_pod_name()}), 500

@app.route('/stress/start', methods=['POST'])
def start_stress():
    global is_stressing
    data = request.json
    if not data or not data.get('cpu_load'):
         return jsonify({"error": "Invalid payload", "pod_name": get_pod_name()}), 400

    if is_stressing:
        return jsonify({
            "status": "Stress test already running", 
            "pid": os.getpid(),
            "pod_name": get_pod_name()
        }), 400

    is_stressing = True
    thread = threading.Thread(target=stress_cpu)
    thread.start()
    
    return jsonify({
        "status": "Stress test started", 
        "pid": os.getpid(),
        "pod_name": get_pod_name()
    }), 200

@app.route('/stress/stop', methods=['POST'])
def stop_stress():
    global is_stressing
    is_stressing = False
    return jsonify({
        "status": "Stress test stopped",
        "pod_name": get_pod_name()
    }), 200

# Initialize DB on startup (Fail Fast)
init_db()

if __name__ == '__main__':
    # Run server for development only
    logger.info("Starting Flask application on port 5000...")
    app.run(host='0.0.0.0', port=5000)
