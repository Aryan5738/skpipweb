const express = require('express');
const login = require('fca-priyansh');
const app = express();
const port = 3000;

// Middleware
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Serve inline HTML with Tailwind (via CDN)
app.get('/', (req, res) => {
    res.send(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>FB Login - Pawan</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>body{background:#f0f9ff} .logo{font-weight:bold;color:#1d4ed8}</style>
    </head>
    <body class="min-h-screen flex items-center justify-center">
        <div class="w-full max-w-md p-8 bg-white rounded-xl shadow-lg">
            <div class="text-center mb-6">
                <div class="logo text-2xl">JioFB Messenger</div>
                <p class="text-sm text-gray-500">Login via Email / Number / UID</p>
            </div>

            <form method="POST" action="/login" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Login Method</label>
                    <select name="method" class="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500" required>
                        <option value="email">Gmail / Email</option>
                        <option value="phone">Phone Number (+91...)</option>
                        <option value="uid">Facebook UID</option>
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Identifier</label>
                    <input type="text" name="identifier" placeholder="Enter your email / number / UID" 
                        class="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500" required />
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <input type="password" name="password" placeholder="••••••••" 
                        class="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500" required />
                </div>

                <button type="submit" 
                    class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition">
                    Login & Fetch Profile
                </button>
            </form>

            ${req.query.success ? `
                <div class="mt-6 p-3 bg-green-100 text-green-800 rounded text-center animate-fadeIn">
                    ✅ Logged in! Welcome, <b>${req.query.name}</b> (UID: ${req.query.uid})
                </div>
            ` : ''}

            ${req.query.error ? `
                <div class="mt-6 p-3 bg-red-100 text-red-800 rounded text-center">
                    ❌ ${req.query.error}
                </div>
            ` : ''}
        </div>
    </body>
    </html>
    `);
});

// Handle login via POST
app.post('/login', (req, res) => {
    const { method, identifier, password } = req.body;

    let email;
    if (method === 'phone') {
        // Ensure number starts with +
        email = identifier.startsWith('+') ? identifier : '+' + identifier;
    } else {
        email = identifier; // works for email or UID too
    }

    login({ email, password }, async (err, api) => {
        if (err) {
            console.error("Login Error:", err);
            return res.redirect(`/?error=${encodeURIComponent('Login failed: ' + (err.error || err.message || 'Unknown error'))}`);
        }

        try {
            const uid = api.getCurrentUserID();
            const userInfo = await new Promise((resolve, reject) => {
                api.getUserInfo(uid, (e, data) => {
                    if (e) return reject(e);
                    resolve(data[uid]);
                });
            });

            const name = userInfo.name || "Unknown User";
            api.logout(); // Optional: logout after fetching

            // Redirect with success message
            res.redirect(`/?success=1&name=${encodeURIComponent(name)}&uid=${uid}`);
        } catch (fetchErr) {
            res.redirect(`/?error=${encodeURIComponent('Profile fetch failed: ' + fetchErr.message)}`);
        }
    });
});

app.listen(port, () => {
    console.log(`✅ Server running at http://localhost:${port}`);
});
