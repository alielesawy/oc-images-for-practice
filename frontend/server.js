const express = require('express');
const app = express();
const path = require('path');
const http = require('http');
const url = require('url');

// Critical Dependency Check
if (!process.env.BACKEND_URL) {
    console.error("FATAL: BACKEND_URL is not set");
    process.exit(1);
}
const BACKEND_URL = process.env.BACKEND_URL;

// Theme Configuration
const APP_THEME = process.env.APP_THEME;
if (!APP_THEME) {
    console.log("APP_THEME not set, defaulting to red");
}

// Set EJS as templating engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Middleware
app.use(express.static('public'));
app.use((req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
    next();
});

const PORT = 8080;

// Helper to fetch data from backend (Server-Side)
function fetchBackendData(endpoint) {
    return new Promise((resolve, reject) => {
        const backendUrl = new url.URL(BACKEND_URL);
        // Construct options, handling URL path if it exists
        const options = {
            hostname: backendUrl.hostname,
            port: backendUrl.port || 80,
            path: path.join(backendUrl.pathname, endpoint).replace(/\\/g, '/'), // Ensure forward slashes
            method: 'GET',
            timeout: 2000 // 2s timeout
        };

        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    resolve(null); // Failed to parse
                }
            });
        });

        req.on('error', (e) => {
            console.error(`Backend fetch error: ${e.message}`);
            resolve(null);
        });

        req.end();
    });
}

// Routes
app.get('/', async (req, res) => {
    let backendPodName = "Checking...";

    // Try to fetch tasks to get pod info
    const tasks = await fetchBackendData('/tasks');

    if (tasks && Array.isArray(tasks) && tasks.length > 0) {
        if (tasks[0].pod_name) {
            backendPodName = tasks[0].pod_name;
        }
    } else if (tasks && !Array.isArray(tasks) && tasks.error) {
        // Did we get an error object with pod_name?
        if (tasks.pod_name) backendPodName = tasks.pod_name;
    } else {
        // Fallback: try health if tasks empty (optional optimization, but good for "Final")
        const health = await fetchBackendData('/health');
        if (health && health.pod_name) {
            backendPodName = health.pod_name;
        } else {
            backendPodName = "Unknown (Backend Unreachable?)";
        }
    }

    res.render('index', {
        backendUrl: BACKEND_URL,
        theme: APP_THEME || 'red',
        backend_pod_name: backendPodName
    });
});

app.get('/stress', (req, res) => {
    res.render('stress', {
        backendUrl: BACKEND_URL,
        theme: APP_THEME || 'red',
        backend_pod_name: "Ready to Connect..." // Initial state
    });
});

// Start Server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Frontend running on http://0.0.0.0:${PORT}`);
    console.log(`Backend URL configured as: ${BACKEND_URL}`);
    console.log(`App Theme: ${APP_THEME || 'red (default)'}`);
});
