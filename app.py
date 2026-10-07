import os
from flask import Flask, render_template_string, request, jsonify
from google import genai

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)

actions_db = [
    {"id": 1, "title": "PC Einschalten", "icon": "💻"},
    {"id": 2, "title": "Wecker stellen", "icon": "⏰"},
    {"id": 3, "title": "KI-Bild generieren", "icon": "🎨"}
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Jarvis Control</title>
    <link rel="apple-touch-icon" href="https://img.icons8.com/color/512/bot.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
        body { background-color: #0b0f19; color: #f8fafc; height: 100vh; display: flex; flex-direction: column; }
        .header { padding: 16px; background: #161e2e; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #243044; }
        .title { font-size: 18px; font-weight: 700; color: #00f2ff; }
        .tab-bar { display: flex; background: #161e2e; border-bottom: 1px solid #243044; }
        .tab-btn { flex: 1; padding: 12px; background: none; border: none; color: #94a3b8; font-weight: 600; font-size: 14px; cursor: pointer; }
        .tab-btn.active { color: #00f2ff; border-bottom: 2px solid #00f2ff; background: #111827; }
        .content { flex: 1; overflow-y: auto; padding: 16px; display: none; }
        .content.active { display: flex; flex-direction: column; }
        .chat-box { flex: 1; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; margin-bottom: 12px; }
        .msg { padding: 12px 16px; border-radius: 16px; max-width: 85%; font-size: 15px; line-height: 1.4; }
        .user { background: #2563eb; align-self: flex-end; }
        .bot { background: #1e293b; border: 1px solid #334155; align-self: flex-start; }
        .input-box { display: flex; gap: 8px; }
        input[type="text"] { flex: 1; padding: 14px; border-radius: 12px; border: 1px solid #334155; background: #161e2e; color: white; font-size: 15px; outline: none; }
        .send-btn { padding: 0 20px; border-radius: 12px; border: none; background: #00f2ff; color: #0b0f19; font-weight: bold; }
        .actions-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 12px; }
        .action-card { background: #161e2e; border: 1px solid #243044; border-radius: 16px; padding: 16px; display: flex; flex-direction: column; align-items: center; gap: 10px; cursor: pointer; text-align: center; }
        .action-icon { font-size: 32px; }
        .action-title { font-size: 14px; font-weight: 600; }
        .add-card { background: rgba(0, 242, 255, 0.05); border: 2px dashed #00f2ff; color: #00f2ff; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); justify-content: center; align-items: center; padding: 20px; }
        .modal-content { background: #161e2e; border: 1px solid #334155; padding: 24px; border-radius: 20px; width: 100%; max-width: 400px; display: flex; flex-direction: column; gap: 12px; }
        .modal-btn { padding: 12px; border-radius: 10px; border: none; background: #00f2ff; color: #0b0f19; font-weight: bold; }
        .close-btn { background: #334155; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">⚡ JARVIS CONTROL</div>
        <span style="color: #22c55e; font-size: 12px;">● Online</span>
    </div>
    <div class="tab-bar">
        <button class="tab-btn active" onclick="switchTab('chatTab', this)">💬 Chat</button>
        <button class="tab-btn" onclick="switchTab('actionsTab', this)">🎛️ Aktionen</button>
    </div>
    <div id="chatTab" class="content active">
        <div class="chat-box" id="chat">
            <div class="msg bot">Hallo Leon! Ich bin deine Jarvis App.</div>
        </div>
        <div class="input-box">
            <input type="text" id="userInput" placeholder="Nachricht an Jarvis...">
            <button class="send-btn" onclick="send()">Senden</button>
        </div>
    </div>
    <div id="actionsTab" class="content">
        <div class="actions-grid" id="actionsList"></div>
    </div>
    <div class="modal" id="addModal">
        <div class="modal-content">
            <h3 style="color: white;">Neue Funktion hinzufügen</h3>
            <input type="text" id="newTitle" placeholder="Titel (z.B. Licht aus)">
            <input type="text" id="newIcon" placeholder="Emoji (z.B. 💡)">
            <button class="modal-btn" onclick="saveAction()">Hinzufügen</button>
            <button class="modal-btn close-btn" onclick="closeModal()">Abbrechen</button>
        </div>
    </div>
    <script>
        function switchTab(tabId, btn) {
            document.querySelectorAll('.content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');
        }
        async function loadActions() {
            let res = await fetch('/get_actions');
            let actions = await res.json();
            let grid = document.getElementById('actionsList');
            grid.innerHTML = actions.map(a => `
                <div class="action-card">
                    <div class="action-icon">${a.icon}</div>
                    <div class="action-title">${a.title}</div>
                </div>
            `).join('');
            grid.innerHTML += `
                <div class="action-card add-card" onclick="openModal()">
                    <div class="action-icon">➕</div>
                    <div class="action-title">Hinzufügen</div>
                </div>
            `;
        }
        function openModal() { document.getElementById('addModal').style.display = 'flex'; }
        function closeModal() { document.getElementById('addModal').style.display = 'none'; }
        async function saveAction() {
            let title = document.getElementById('newTitle').value;
            let icon = document.getElementById('newIcon').value || '⚡';
            if(!title) return;
            await fetch('/add_action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title, icon})
            });
            closeModal();
            loadActions();
        }
        async function send() {
            let input = document.getElementById('userInput');
            let text = input.value.trim();
            if (!text) return;
            let chat = document.getElementById('chat');
            chat.innerHTML += `<div class="msg user">${text}</div>`;
            input.value = '';
            chat.scrollTop = chat.scrollHeight;
            let res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: text})
            });
            let data = await res.json();
            chat.innerHTML += `<div class="msg bot">${data.reply}</div>`;
            chat.scrollTop = chat.scrollHeight;
        }
        loadActions();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_actions')
def get_actions():
    return jsonify(actions_db)

@app.route('/add_action', methods=['POST'])
def add_action():
    data = request.get_json()
    actions_db.append({"id": len(actions_db) + 1, "title": data.get("title"), "icon": data.get("icon", "⚡")})
    return jsonify({"success": True})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_text = data.get("message", "")
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=user_text)
        reply = response.text
    except Exception as e:
        reply = f"Fehler: {e}"
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
