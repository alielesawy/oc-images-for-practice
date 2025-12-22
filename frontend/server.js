const express = require('express');
const app = express();
const path = require('path');

// Set EJS as templating engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Middleware
app.use(express.static('public')); // Optional if we had static assets separate, but good practice

// Environment Variables
const PORT = 8080;
// Default to localhost:5000 if not set, but in OCP it will be the service name
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:5000';

// Routes
app.get('/', (req, res) => {
    res.render('index', { backendUrl: BACKEND_URL });
});

// Start Server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Frontend running on http://0.0.0.0:${PORT}`);
    console.log(`Backend URL configured as: ${BACKEND_URL}`);
});
