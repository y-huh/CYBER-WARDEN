from flask import Flask, render_template_string, request, jsonify
import requests
import json
import os
import threading
import re
from datetime import datetime
import telebot

app = Flask(__name__)

# ==========================================
# === НАСТРОЙКИ ===
# ==========================================
BOT_TOKEN = "9042206074:AAEpbWGGjjhPr_D3547Ody16Ttzn3sNfDCg"
ADMIN_CHAT_ID = 1516333018  

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"

# Инициализация Telegram бота
bot = telebot.TeleBot(BOT_TOKEN)

# Временная память для контекста юзеров
user_histories = {}
MAX_HISTORY_LENGTH = 5

# Общая база данных инцидентов и статистика категорий
incidents_db = []
category_stats = {
    "Hacking & Access": 0,
    "Phishing & Social Eng.": 0,
    "Malware & Payloads": 0,
    "Data Breaches & Markets": 0,
    "Insider Threats": 0
}

# Системный промпт
SYSTEM_PROMPT = """You are an elite AI Cybersecurity Moderation, Threat Intelligence, and Incident Detection System. Your sole purpose is to analyze chat logs in real-time, detect malicious cyber activities, pre-attack preparations, discussions of cybercrime, and evaluate risk probability across Uzbek (Latin/Cyrillic), Russian, and English.

CRITICAL RISK CATEGORIES TO DETECT:
1. Unauthorized Access & Hacking: Exploits, RCE, SQLi, XSS, buffer overflows, brute-force, RATs, botnets, DDoS.
2. Phishing & Social Engineering: Fake login portals, credential harvesting, carding, crypto-drainers.
3. Malware & Payloads: Ransomware, trojans, infostealers, reverse shells.
4. Data Breaches & Underground Markets: Buying/selling database dumps, leaked PII, stolen credentials.
5. Insider Threats: Data exfiltration plans, corporate sabotage.

STRICT OUTPUT FORMAT RULES:
- If safe, respond ONLY with: [OK]
- If a threat is detected, respond ONLY with this exact template:
[TRIGGER] | Category: <Category Name> | Risk Level: <Low/Medium/High> | Probability: <0-100%> | Reason: <One sentence explanation in English>
"""

def check_via_ollama(text_to_analyze):
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser Content to analyze:\n\"{text_to_analyze}\""
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 150}
    }
    for attempt in range(2):
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=60)
            if response.status_code == 200:
                res_text = response.json().get("response", "").strip()
                if res_text:
                    return res_text
        except Exception as e:
            print(f"Ollama error (attempt {attempt+1}): {e}")
    return "[OK]"

def parse_category_and_update_stats(verdict):
    """Парсит категорию из вердикта ИИ и обновляет статистику для графиков"""
    global category_stats
    match = re.search(r'Category:\s*([^|]+)', verdict)
    if match:
        cat_raw = match.group(1).strip().lower()
        if "access" in cat_raw or "hack" in cat_raw:
            category_stats["Hacking & Access"] += 1
        elif "phish" in cat_raw or "social" in cat_raw:
            category_stats["Phishing & Social Eng."] += 1
        elif "malware" in cat_raw or "payload" in cat_raw:
            category_stats["Malware & Payloads"] += 1
        elif "breach" in cat_raw or "market" in cat_raw:
            category_stats["Data Breaches & Markets"] += 1
        else:
            category_stats["Insider Threats"] += 1

def save_evidence_to_file(source, user_name, username, user_id, chat_title, message_text, ai_verdict):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (
        f"=== CYBER INCIDENT [{source}] ===\n"
        f"Time: {timestamp}\n"
        f"Source/Chat: {chat_title}\n"
        f"User: {user_name} (@{username}) | ID: {user_id}\n"
        f"Message: {message_text}\n"
        f"AI Verdict: {ai_verdict}\n"
        f"==================================\n\n"
    )
    with open("cyber_evidences.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)


# ==========================================
# === TELEGRAM BOT ЛОГИКА ===
# ==========================================
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_telegram_messages(message):
    if message.from_user.is_bot:
        return

    user_id = message.from_user.id
    user_text = message.text

    if user_id not in user_histories:
        user_histories[user_id] = []
    user_histories[user_id].append(user_text)
    if len(user_histories[user_id]) > MAX_HISTORY_LENGTH:
        user_histories[user_id].pop(0)

    formatted_history = "\n".join([f"- {msg}" for msg in user_histories[user_id]])
    ai_verdict = check_via_ollama(formatted_history)

    if "[TRIGGER]" in ai_verdict:
        user_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        username = message.from_user.username or "no_username"
        chat_title = message.chat.title or "Private Chat"
        
        save_evidence_to_file("TELEGRAM", user_name, username, user_id, chat_title, user_text, ai_verdict)
        parse_category_and_update_stats(ai_verdict)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        incidents_db.insert(0, {
            "time": timestamp,
            "source": f"Telegram: {chat_title}",
            "user": f"{user_name} (@{username})",
            "text": user_text,
            "verdict": ai_verdict
        })
        
        alert_msg = (
            f"🚨 CYBER THREAT DETECTED (Telegram)!\n\n"
            f"📍 Group: {chat_title}\n"
            f"👤 Suspect: {user_name} (@{username}) | ID: `{user_id}`\n"
            f"📝 Message: {user_text}\n\n"
            f"🔍 AI Analysis:\n{ai_verdict}"
        )
        try:
            bot.send_message(ADMIN_CHAT_ID, alert_msg)
        except Exception as e:
            print(f"Failed to send Telegram alert: {e}")

def run_telegram_bot():
    print("🤖 Telegram Bot polling started in background...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)


# ==========================================
# === WEB DASHBOARD (FLASK + CHARTS) ===
# ==========================================
TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Cyber-Warden Enterprise SOC</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Подключаем Chart.js для крутых графиков -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-slate-950 text-slate-100 font-sans">
    <div class="container mx-auto px-6 py-8">
        <!-- Шапка -->
        <header class="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
            <div>
                <h1 class="text-3xl font-black tracking-wider text-red-500 flex items-center gap-3">
                    🛡️ CYBER-WARDEN <span class="text-xs bg-red-950 border border-red-600 text-red-400 px-2 py-1 rounded">SOC ENTERPRISE</span>
                </h1>
                <p class="text-xs text-slate-400 mt-1">Autonomous Local AI Threat Intelligence & Incident Response Platform</p>
            </div>
            <div class="flex items-center gap-3 bg-slate-900 border border-slate-800 px-4 py-2 rounded-lg">
                <span class="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                <span class="text-sm font-medium text-slate-300">Node: <strong class="text-green-400">Ollama (qwen2.5:3b)</strong></span>
            </div>
        </header>

        <!-- Карточки статистики -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg">
                <h3 class="text-slate-400 text-xs uppercase tracking-wider font-bold">Active Vectors</h3>
                <p class="text-2xl font-black mt-2 text-indigo-400">Telegram & Web</p>
            </div>
            <div class="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg">
                <h3 class="text-slate-400 text-xs uppercase tracking-wider font-bold">Total Threat Incidents</h3>
                <p class="text-3xl font-black mt-2 text-red-500" id="stat-threats">{{ incidents|length }}</p>
            </div>
            <div class="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg">
                <h3 class="text-slate-400 text-xs uppercase tracking-wider font-bold">Defense Status</h3>
                <p class="text-3xl font-black mt-2 text-emerald-400">ACTIVE</p>
            </div>
            <div class="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg">
                <h3 class="text-slate-400 text-xs uppercase tracking-wider font-bold">AI Latency</h3>
                <p class="text-3xl font-black mt-2 text-amber-400">~1.2s</p>
            </div>
        </div>

        <!-- Секция графиков -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <!-- График категорий (Круговая диаграмма) -->
            <div class="bg-slate-900 p-6 rounded-xl border border-slate-800 lg:col-span-1 flex flex-col items-center justify-center">
                <h3 class="text-lg font-bold mb-4 text-slate-200 self-start">Threat Categories Breakdown</h3>
                <div class="w-full h-64 flex justify-center">
                    <canvas id="threatPieChart"></canvas>
                </div>
            </div>
            <!-- Симулятор веб-форума -->
            <div class="bg-slate-900 p-6 rounded-xl border border-slate-800 lg:col-span-2 flex flex-col justify-between">
                <div>
                    <h3 class="text-lg font-bold mb-2 text-indigo-400">💬 Web Forum / Chat Threat Simulator</h3>
                    <p class="text-xs text-slate-400 mb-4">Inject test forum messages or payloads here to evaluate the local AI classification in real time.</p>
                </div>
                <form id="test-form" class="space-y-4">
                    <input type="text" id="msg-input" placeholder="Type test post (e.g. SQL injection, exploit payload, phishing link)..." 
                           class="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-indigo-500">
                    <div class="flex justify-between items-center">
                        <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 px-6 py-2.5 rounded-lg font-bold text-sm transition shadow-md">Run AI Inspection</button>
                        <span class="text-xs text-slate-500">Model: qwen2.5:3b (Strict Context Rules)</span>
                    </div>
                </form>
                <div id="result-box" class="mt-4 p-3 rounded-lg bg-slate-950 border border-slate-800 text-sm hidden"></div>
            </div>
        </div>

        <!-- Таблица инцидентов в реальном времени -->
        <div class="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg">
            <h2 class="text-xl font-bold mb-4 text-red-400 flex items-center gap-2">
                <span>🚨</span> Real-Time Threat Incidents Log
            </h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 text-slate-400 text-xs uppercase tracking-wider">
                            <th class="py-3 px-4">Timestamp</th>
                            <th class="py-3 px-4">Vector Source</th>
                            <th class="py-3 px-4">Suspect / Author</th>
                            <th class="py-3 px-4">Payload Content</th>
                            <th class="py-3 px-4">AI Threat Verdict</th>
                        </tr>
                    </thead>
                    <tbody id="incidents-table" class="text-sm">
                        {% if incidents %}
                            {% for inc in incidents %}
                            <tr class="border-b border-slate-850 hover:bg-slate-850/50 transition">
                                <td class="py-3 px-4 text-xs text-slate-400">{{ inc.time }}</td>
                                <td class="py-3 px-4 text-xs font-bold text-yellow-400">{{ inc.source }}</td>
                                <td class="py-3 px-4">{{ inc.user }}</td>
                                <td class="py-3 px-4 font-mono text-xs text-slate-300">{{ inc.text }}</td>
                                <td class="py-3 px-4 text-red-400 font-mono text-xs font-semibold">{{ inc.verdict }}</td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr class="border-b border-slate-850 text-slate-500">
                                <td colspan="5" class="py-6 text-center">No security threats intercepted yet. System is actively scanning...</td>
                            </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Данные для круговой диаграммы из Flask бэкенда
        const statsData = {
            labels: ['Hacking & Access', 'Phishing & Social', 'Malware & Payloads', 'Data Breaches', 'Insider Threats'],
            datasets: [{
                data: [
                    {{ stats['Hacking & Access'] }},
                    {{ stats['Phishing & Social Eng.'] }},
                    {{ stats['Malware & Payloads'] }},
                    {{ stats['Data Breaches & Markets'] }},
                    {{ stats['Insider Threats'] }}
                ],
                backgroundColor: ['#ef4444', '#f97316', '#eab308', '#8b5cf6', '#06b6d4'],
                borderWidth: 0
            }]
        };

        const ctx = document.getElementById('threatPieChart').getContext('2d');
        const threatPieChart = new Chart(ctx, {
            type: 'doughnut',
            data: statsData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#94a3b8',
                            font: { size: 10 }
                        }
                    }
                }
            }
        });

        // Симулятор отправки сообщения
        document.getElementById('test-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('msg-input');
            const resultBox = document.getElementById('result-box');
            const text = input.value.trim();
            if(!text) return;

            resultBox.classList.remove('hidden');
            resultBox.innerHTML = '<span class="text-yellow-400 font-mono">⚡ Analyzing payload via Local AI node...</span>';

            const response = await fetch('/api/check', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text})
            });
            const data = await response.json();
            
            if(data.verdict.includes('[TRIGGER]')) {
                resultBox.innerHTML = `<span class="text-red-400 font-bold">⚠️ THREAT INTERCEPTED:</span> <code class="text-xs font-mono text-red-300">${data.verdict}</code>`;
                setTimeout(() => location.reload(), 1800); // Перезагружаем чтобы обновить график и таблицу
            } else {
                resultBox.innerHTML = `<span class="text-emerald-400 font-bold">✅ SAFE:</span> Message passed security inspection.`;
            }
            input.value = '';
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(TEMPLATE, incidents=incidents_db, stats=category_stats)

@app.route('/api/check', methods=['POST'])
def api_check():
    data = request.json
    text = data.get('text', '')
    verdict = check_via_ollama(text)
    
    if "[TRIGGER]" in verdict:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        parse_category_and_update_stats(verdict)
        incidents_db.insert(0, {
            "time": timestamp,
            "source": "Web Simulator SOC",
            "user": "SOC Analyst (@admin)",
            "text": text,
            "verdict": verdict
        })
        save_evidence_to_file("WEB_SIMULATOR", "SOC Analyst", "admin", 0, "Web Portal", text, verdict)
        
    return jsonify({"verdict": verdict})


if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()

    print("🚀 Cyber-Warden Enterprise SOC running at http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)