const express = require('express');
const multer = require('multer');
const { initializeApp, applicationDefault } = require('firebase-admin/app');
const { getFirestore } = require('firebase-admin/firestore');
const { getAuth } = require('firebase-admin/auth');
const { createWorker } = require('tesseract.js');
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const port = 8000;

// Initialize Firebase
if (!initializeApp.length) {
    initializeApp({ credential: applicationDefault() });
}
const db = getFirestore();
const auth = getAuth();

app.use(express.json());
const upload = multer({ dest: 'uploads/' });

// Solve equation
app.post('/solve', (req, res) => {
    try {
        const equation = req.body.equation;
        if (!equation) {
            return res.status(400).json({ error: "Equation is required" });
        }
        console.log(`Received equation: ${equation}`);
        const result = execSync(`python3 -c "import sympy; print(sympy.solve('${equation}'))"`).toString().trim();
        console.log(`Solution found: ${result}`);
        res.json({ solution: result });
    } catch (error) {
        console.error(`Error solving equation: ${error.message}`);
        res.status(400).json({ error: `Invalid equation: ${error.message}` });
    }
});

// OCR Processing
app.post('/upload-image', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: "No file uploaded" });
        }
        console.log(`Received file: ${req.file.originalname}`);
        const worker = await createWorker('eng');
        const { data: { text } } = await worker.recognize(req.file.path);
        await worker.terminate();
        fs.unlinkSync(req.file.path);
        console.log(`Extracted text: ${text.trim()}`);
        res.json({ extracted_text: text.trim() });
    } catch (error) {
        console.error(`Image processing error: ${error.message}`);
        res.status(400).json({ error: `Image processing error: ${error.message}` });
    }
});

// User Authentication
app.post('/login', async (req, res) => {
    try {
        const { email } = req.body;
        if (!email) {
            return res.status(400).json({ error: "Email is required" });
        }
        console.log(`Login attempt for email: ${email}`);
        const userRecord = await auth.getUserByEmail(email);
        console.log(`User found: ${userRecord.uid}`);
        res.json({ message: "User exists", user_id: userRecord.uid });
    } catch (error) {
        console.warn("User not found or error occurred");
        res.status(404).json({ error: "User not found" });
    }
});

app.post('/register', async (req, res) => {
    try {
        const { email, password } = req.body;
        if (!email || !password) {
            return res.status(400).json({ error: "Email and password are required" });
        }
        console.log(`Registering user: ${email}`);
        const userRecord = await auth.createUser({ email, password });
        console.log(`User registered: ${userRecord.uid}`);
        res.json({ message: "User registered", user_id: userRecord.uid });
    } catch (error) {
        console.error(`Registration error: ${error.message}`);
        res.status(400).json({ error: error.message });
    }
});

app.get('/session/:user_id', async (req, res) => {
    try {
        const user_id = req.params.user_id;
        if (!user_id) {
            return res.status(400).json({ error: "User ID is required" });
        }
        console.log(`Fetching sessions for user_id: ${user_id}`);
        const sessionsRef = db.collection('sessions');
        const snapshot = await sessionsRef.where('user_id', '==', user_id).get();
        const sessions = snapshot.docs.map(doc => doc.data());
        console.log(`Sessions retrieved: ${sessions.length}`);
        res.json({ sessions });
    } catch (error) {
        console.error(`Database error: ${error.message}`);
        res.status(500).json({ error: `Database error: ${error.message}` });
    }
});

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
