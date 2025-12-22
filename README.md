# OCP-TaskMaster

A simple 2-tier microservices application (Frontend + Backend) designed for learning OpenShift deployment.

## Architecture

1.  **Backend (Python Flask)**:
    *   Exposes a REST API on port `5000`.
    *   Connects to a MySQL database.
    *   Endpoints: `GET /tasks`, `POST /tasks`, `DELETE /tasks/<id>`, `GET /health`.
2.  **Frontend (Node.js Express + EJS)**:
    *   Runs on port `8080`.
    *   Serves a server-side rendered dashboard.
    *   Connects to the Backend via HTTP.

---

## Prerequisites

*   **Python 3.9+** (for local backend)
*   **Node.js 16/18+** (for local frontend)
*   **Podman** (or Docker) for containerization.
*   **MySQL Database**: You need a running MySQL instance.
    *   *Example Remote DB*: `104.248.22.89` (Port 3306).

---

## 1. Local Development (Running on Host)

Run the apps directly on your machine without containers for quick iteration.

### Step 1: Backend

1.  Open a terminal in the project root (`d:/oc-project`).
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set the Database URL (replace values with your actual DB credentials):
    *   *PowerShell*:
        ```powershell
        $env:DATABASE_URL='mysql://redhat:redhat123@104.248.22.89:3306/todo'
        ```
    *   *Bash*:
        ```bash
        export DATABASE_URL='mysql://redhat:redhat123@104.248.22.89:3306/todo'
        ```
4.  Run the application:
    ```bash
    python app.py
    ```
    *The backend is now running at `http://localhost:5000`.*

### Step 2: Frontend

1.  Open a **new** terminal window.
2.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
3.  Install dependencies:
    ```bash
    npm install
    ```
4.  Set Environment Variables:
    *   `BACKEND_URL`: Where the frontend can find the backend.
    *   `APP_THEME` (Optional): `red` (default) or `blue`.
    *   *PowerShell*:
        ```powershell
        $env:BACKEND_URL='http://localhost:5000'; $env:APP_THEME='blue'
        ```
5.  Run the server:
    ```bash
    node server.js
    ```
    *The frontend is now running at `http://localhost:8080`.*

---

## 2. Containerized Development (Using Podman)

Package the apps into standard OCI containers.

### Step 1: Build Images

**Backend Image**:
```bash
# Run from project root
podman build -t ocp-taskmaster-backend .
```

**Frontend Image**:
```bash
# Run from project root
podman build -t ocp-taskmaster-frontend frontend/.
```

### Step 2: Run Containers

We will create a specific network so containers can talk to each other easily, or just use host networking for simplicity. Here we use **Port Mapping**.

**1. Run Backend**:
```bash
podman run -d \
  --name taskmaster-backend \
  -p 5000:5000 \
  -e DATABASE_URL='mysql://redhat:redhat123@104.248.22.89:3306/todo' \
  ocp-taskmaster-backend
```

**2. Run Frontend**:
*Note: Since the backend is running on your host machine's port 5000 (via the mapping above), the frontend container needs to reach it. If running on Linux/Mac/Windows (WSL), `localhost` inside a container refers to the container itself, not the host. You typically need to use the Host IP or `--network host`.*

*Option A: Use Host Networking (Easiest for local)*:
```bash
podman run -d \
  --name taskmaster-frontend \
  --network host \
  -e BACKEND_URL='http://localhost:5000' \
  -e APP_THEME='blue' \
  ocp-taskmaster-frontend
```
*Access at `http://localhost:8080`.*

*Option B: Standard Linking (Bridge Network)*:
If you cannot use host networking, use the backend container's IP or alias if on the same podman network.
```bash
# Create network
podman network create task-net

# Run Backend on network
podman run -d --name backend --net task-net -e DATABASE_URL='...' ocp-taskmaster-backend

# Run Frontend on network (referencing backend by name)
podman run -d -p 8080:8080 --net task-net \
  -e BACKEND_URL='http://backend:5000' \
  -e APP_THEME='red' \
  ocp-taskmaster-frontend
```

---

## Environment Variables Reference

### Backend
| Variable | Description | Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | Connection string for MySQL | `mysql://user:pass@host:3306/db` |

### Frontend
| Variable | Description | Example |
| :--- | :--- | :--- |
| `BACKEND_URL` | URL of the Backend API | `http://backend-service:5000` |
| `APP_THEME` | Color theme (`red` or `blue`) | `blue` |
