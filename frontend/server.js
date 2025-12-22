const express = require('express');
const app = express();
const path = require('path');

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

// Environment Variables
const PORT = 8080;

// Routes
app.get('/', (req, res) => {
    res.render('index', {
        backendUrl: BACKEND_URL,
        theme: APP_THEME || 'red'
    });
});

// Start Server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Frontend running on http://0.0.0.0:${PORT}`);
    console.log(`Backend URL configured as: ${BACKEND_URL}`);
    console.log(`App Theme: ${APP_THEME || 'red (default)'}`);
});
