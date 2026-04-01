“””
بوت صارحني - Telegram Anonymous Message Bot
ملف واحد جاهز للرفع على Railway
“””

import os
import json
import hashlib
import time
import logging
from datetime import datetime
from threading import Thread
from flask import Flask, request, jsonify, render_template_string
import requests as http_requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application,
CommandHandler,
MessageHandler,
CallbackQueryHandler,
filters,
ContextTypes,
)

# ─── Configuration ───────────────────────────────────────────────

BOT_TOKEN = os.environ.get(“BOT_TOKEN”, “YOUR_BOT_TOKEN_HERE”)
WEB_APP_URL = os.environ.get(“RAILWAY_PUBLIC_DOMAIN”, os.environ.get(“WEB_APP_URL”, “localhost:5000”))
if WEB_APP_URL and not WEB_APP_URL.startswith(“http”):
WEB_APP_URL = f”https://{WEB_APP_URL}”
PORT = int(os.environ.get(“PORT”, 5000))
DB_FILE = “database.json”

logging.basicConfig(
format=”%(asctime)s - %(name)s - %(levelname)s - %(message)s”,
level=logging.INFO,
)
logger = logging.getLogger(**name**)

# ─── Simple JSON Database ────────────────────────────────────────

def load_db():
if os.path.exists(DB_FILE):
with open(DB_FILE, “r”, encoding=“utf-8”) as f:
return json.load(f)
return {“users”: {}, “links”: {}, “messages”: {}}

def save_db(db):
with open(DB_FILE, “w”, encoding=“utf-8”) as f:
json.dump(db, f, ensure_ascii=False, indent=2)

def generate_link_id(user_id: int) -> str:
raw = f”{user_id}-{time.time()}”
return hashlib.md5(raw.encode()).hexdigest()[:8]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# TELEGRAM BOT HANDLERS

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
user = update.effective_user
db = load_db()

```
# Deep link - someone wants to send anonymous message
if context.args and len(context.args) > 0:
    link_id = context.args[0]
    if link_id in db.get("links", {}):
        context.user_data["sending_to"] = link_id
        await update.message.reply_text(
            "✉️ *أرسل رسالتك المجهولة*\n\n"
            "اكتب رسالتك الآن وسيتم إرسالها بشكل مجهول تماماً 🤫\n\n"
            "💬 اكتب رسالتك:",
            parse_mode="Markdown",
        )
        return

# Normal start
user_id = str(user.id)
if user_id not in db.get("users", {}):
    db.setdefault("users", {})[user_id] = {
        "name": user.first_name,
        "username": user.username,
        "joined": datetime.now().isoformat(),
        "message_count": 0,
    }
    save_db(db)

keyboard = [
    [InlineKeyboardButton("🔗 إنشاء رابط صراحة", callback_data="create_link")],
    [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats")],
    [InlineKeyboardButton("❓ كيف يعمل البوت؟", callback_data="how_it_works")],
]

await update.message.reply_text(
    f"مرحباً {user.first_name}! 👋\n\n"
    f"🔮 *بوت صارحني*\n\n"
    f"أنشئ رابط صراحة خاص بك وشاركه مع أصدقائك\n"
    f"ليرسلوا لك رسائل مجهولة! 💌\n\n"
    f"اختر من القائمة:",
    parse_mode="Markdown",
    reply_markup=InlineKeyboardMarkup(keyboard),
)
```

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

```
user = query.from_user
user_id = str(user.id)
db = load_db()

if query.data == "create_link":
    # Check existing link
    existing_link = None
    for lid, data in db.get("links", {}).items():
        if data.get("owner") == user_id:
            existing_link = lid
            break

    if existing_link:
        link_id = existing_link
    else:
        link_id = generate_link_id(user.id)
        db.setdefault("links", {})[link_id] = {
            "owner": user_id,
            "name": user.first_name,
            "created": datetime.now().isoformat(),
        }
        save_db(db)

    bot_username = (await context.bot.get_me()).username
    tg_link = f"https://t.me/{bot_username}?start={link_id}"
    web_link = f"{WEB_APP_URL}/send/{link_id}"

    keyboard = [
        [InlineKeyboardButton("📤 مشاركة الرابط", switch_inline_query=f"أرسلي رسالة مجهولة 💌\n{tg_link}")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")],
    ]

    await query.edit_message_text(
        f"✅ *تم إنشاء رابط الصراحة!*\n\n"
        f"🔗 رابط التلجرام:\n`{tg_link}`\n\n"
        f"🌐 رابط الويب:\n`{web_link}`\n\n"
        f"شارك أي رابط مع أصدقائك! 💬",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

elif query.data == "my_stats":
    user_data = db.get("users", {}).get(user_id, {})
    msg_count = user_data.get("message_count", 0)
    has_link = any(d.get("owner") == user_id for d in db.get("links", {}).values())

    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]]

    await query.edit_message_text(
        f"📊 *إحصائياتك*\n\n"
        f"👤 الاسم: {user.first_name}\n"
        f"📩 الرسائل المستلمة: {msg_count}\n"
        f"🔗 حالة الرابط: {'🟢 فعال' if has_link else '🔴 لا يوجد'}\n",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

elif query.data == "how_it_works":
    keyboard = [
        [InlineKeyboardButton("🔗 إنشاء رابط", callback_data="create_link")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")],
    ]

    await query.edit_message_text(
        "❓ *كيف يعمل بوت صارحني؟*\n\n"
        "1️⃣ أنشئ رابط الصراحة الخاص بك\n"
        "2️⃣ شارك الرابط مع أصدقائك\n"
        "3️⃣ صديقك يضغط الرابط ويكتب رسالة\n"
        "4️⃣ تصلك الرسالة هنا بشكل مجهول!\n\n"
        "🔒 لا يمكن معرفة هوية المرسل نهائياً",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

elif query.data == "main_menu":
    keyboard = [
        [InlineKeyboardButton("🔗 إنشاء رابط صراحة", callback_data="create_link")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats")],
        [InlineKeyboardButton("❓ كيف يعمل البوت؟", callback_data="how_it_works")],
    ]

    await query.edit_message_text(
        "🔮 *بوت صارحني*\n\nاختر من القائمة:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
```

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
user = update.effective_user
db = load_db()

```
link_id = context.user_data.get("sending_to")

if link_id and link_id in db.get("links", {}):
    link_data = db["links"][link_id]
    owner_id = link_data["owner"]
    message_text = update.message.text

    # Don't let user send to themselves
    if str(user.id) == owner_id:
        await update.message.reply_text("❌ لا يمكنك إرسال رسالة لنفسك!")
        context.user_data.pop("sending_to", None)
        return

    # Save message
    msg_id = hashlib.md5(f"{time.time()}-{user.id}".encode()).hexdigest()[:10]
    db.setdefault("messages", {})[msg_id] = {
        "link_id": link_id,
        "text": message_text,
        "timestamp": datetime.now().isoformat(),
    }
    db.setdefault("users", {}).setdefault(owner_id, {})
    db["users"][owner_id]["message_count"] = db["users"][owner_id].get("message_count", 0) + 1
    save_db(db)

    # Send to owner
    try:
        await context.bot.send_message(
            chat_id=int(owner_id),
            text=(
                f"💌 *رسالة مجهولة جديدة!*\n\n"
                f"📝 {message_text}\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🔮 _عبر بوت صارحني_"
            ),
            parse_mode="Markdown",
        )
        await update.message.reply_text(
            "✅ *تم إرسال رسالتك بنجاح!* 💚\n\n"
            "لن يعرف المستلم هويتك أبداً 🤫\n\n"
            "💬 يمكنك إرسال رسالة أخرى أو /start للقائمة",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Send error: {e}")
        await update.message.reply_text("❌ حدث خطأ. حاول مرة أخرى.")

    context.user_data.pop("sending_to", None)
    return

await update.message.reply_text("💡 اضغط /start للبدء!")
```

async def mylink(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = str(update.effective_user.id)
db = load_db()

```
for lid, data in db.get("links", {}).items():
    if data.get("owner") == user_id:
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={lid}"
        await update.message.reply_text(f"🔗 رابطك:\n`{link}`", parse_mode="Markdown")
        return

await update.message.reply_text("❌ لم تنشئ رابط بعد! اضغط /start")
```

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# WEB SERVER (Flask)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

app = Flask(**name**)

WEB_PAGE = “””

<!DOCTYPE html>

<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>صارحني 💌</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Tajawal', sans-serif;
            min-height: 100vh;
            background: #0a0a1a;
            color: #fff;
            overflow-x: hidden;
        }
        body::before {
            content: '';
            position: fixed;
            top: -50%%; left: -50%%;
            width: 200%%; height: 200%%;
            background:
                radial-gradient(circle at 20%% 50%%, rgba(120,50,255,0.15) 0%%, transparent 50%%),
                radial-gradient(circle at 80%% 20%%, rgba(255,50,150,0.1) 0%%, transparent 50%%),
                radial-gradient(circle at 50%% 80%%, rgba(50,100,255,0.1) 0%%, transparent 50%%);
            animation: bg 20s ease-in-out infinite;
            z-index: 0;
        }
        @keyframes bg {
            0%%,100%% { transform: translate(0,0); }
            50%% { transform: translate(2%%,-2%%); }
        }
        .container {
            position: relative; z-index: 1;
            max-width: 500px; margin: 0 auto; padding: 40px 20px;
            min-height: 100vh;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }
        .card {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 24px;
            padding: 40px 30px; width: 100%%;
            animation: cardIn 0.8s cubic-bezier(0.16,1,0.3,1);
        }
        @keyframes cardIn {
            from { opacity:0; transform: translateY(30px) scale(0.95); }
            to { opacity:1; transform: translateY(0) scale(1); }
        }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo-icon { font-size: 56px; margin-bottom: 10px; animation: float 3s ease-in-out infinite; }
        @keyframes float { 0%%,100%% { transform: translateY(0); } 50%% { transform: translateY(-8px); } }
        .logo h1 {
            font-size: 32px; font-weight: 800;
            background: linear-gradient(135deg, #a78bfa, #ec4899, #8b5cf6);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .logo p { color: rgba(255,255,255,0.5); font-size: 14px; margin-top: 5px; }
        .recipient-info {
            text-align: center; margin-bottom: 25px; padding: 15px;
            background: rgba(167,139,250,0.1);
            border-radius: 16px; border: 1px solid rgba(167,139,250,0.15);
        }
        .recipient-info span { color: #a78bfa; font-weight: 700; font-size: 18px; }
        .recipient-info p { color: rgba(255,255,255,0.5); font-size: 13px; margin-top: 4px; }
        textarea {
            width: 100%%; min-height: 150px; padding: 18px;
            border: 2px solid rgba(255,255,255,0.08); border-radius: 16px;
            background: rgba(0,0,0,0.3); color: #fff;
            font-family: 'Tajawal', sans-serif; font-size: 16px;
            resize: vertical; outline: none; transition: border-color 0.3s; direction: rtl;
        }
        textarea:focus { border-color: rgba(167,139,250,0.5); }
        textarea::placeholder { color: rgba(255,255,255,0.25); }
        .char-count { text-align: left; font-size: 12px; color: rgba(255,255,255,0.3); margin-top: 8px; }
        .send-btn {
            width: 100%%; padding: 16px; margin-top: 20px; border: none; border-radius: 16px;
            font-family: 'Tajawal', sans-serif; font-size: 18px; font-weight: 700; cursor: pointer;
            background: linear-gradient(135deg, #8b5cf6, #a855f7, #ec4899);
            color: #fff; transition: all 0.3s; position: relative; overflow: hidden;
        }
        .send-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 40px rgba(139,92,246,0.3); }
        .send-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .send-btn .spinner {
            display: none; width: 22px; height: 22px;
            border: 3px solid rgba(255,255,255,0.3); border-top-color: #fff;
            border-radius: 50%%; animation: spin 0.8s linear infinite; margin: 0 auto;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .send-btn.loading span { display: none; }
        .send-btn.loading .spinner { display: block; }
        .success-state { display:none; text-align:center; padding:20px 0; animation: sIn 0.5s cubic-bezier(0.16,1,0.3,1); }
        @keyframes sIn { from { opacity:0; transform:scale(0.8); } to { opacity:1; transform:scale(1); } }
        .success-state .check {
            width:80px; height:80px; border-radius:50%%;
            background: linear-gradient(135deg,#10b981,#34d399);
            display:flex; align-items:center; justify-content:center;
            margin:0 auto 20px; font-size:40px;
        }
        .success-state h2 { font-size: 22px; margin-bottom: 8px; }
        .success-state p { color: rgba(255,255,255,0.5); font-size: 14px; }
        .send-another {
            margin-top: 20px; padding: 12px 30px;
            border: 1px solid rgba(167,139,250,0.3); border-radius: 12px;
            background: transparent; color: #a78bfa;
            font-family: 'Tajawal', sans-serif; font-size: 15px; font-weight: 600;
            cursor: pointer; transition: all 0.3s;
        }
        .send-another:hover { background: rgba(167,139,250,0.1); }
        .error-state { text-align: center; padding: 40px 0; }
        .error-state .icon { font-size: 60px; margin-bottom: 15px; }
        .error-state h2 { font-size: 20px; margin-bottom: 8px; }
        .error-state p { color: rgba(255,255,255,0.5); font-size: 14px; }
        .footer { text-align: center; margin-top: 30px; color: rgba(255,255,255,0.2); font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">
                <div class="logo-icon">💌</div>
                <h1>صارحني</h1>
                <p>أرسل رسالتك بسرية تامة</p>
            </div>

```
        %(content)s
    </div>
    <div class="footer">صارحني بوت 💜</div>
</div>

<script>
    var msgInput = document.getElementById('messageInput');
    if (msgInput) {
        msgInput.addEventListener('input', function() {
            document.getElementById('charCount').textContent = this.value.length;
        });
    }

    function sendMessage() {
        var text = document.getElementById('messageInput').value.trim();
        if (!text) return;
        var btn = document.getElementById('sendBtn');
        btn.classList.add('loading');
        btn.disabled = true;

        fetch('/api/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ link_id: '%(link_id)s', message: text })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.success) {
                document.getElementById('formState').style.display = 'none';
                document.getElementById('successState').style.display = 'block';
            } else {
                alert(data.error || 'حدث خطأ');
            }
            btn.classList.remove('loading');
            btn.disabled = false;
        })
        .catch(function() {
            alert('خطأ في الاتصال');
            btn.classList.remove('loading');
            btn.disabled = false;
        });
    }

    function resetForm() {
        document.getElementById('messageInput').value = '';
        document.getElementById('charCount').textContent = '0';
        document.getElementById('formState').style.display = 'block';
        document.getElementById('successState').style.display = 'none';
    }
</script>
```

</body>
</html>
"""

FORM_CONTENT = “””

<div id="formState">
    <div class="recipient-info">
        <span>%(name)s</span>
        <p>أرسل رسالة مجهولة</p>
    </div>
    <textarea id="messageInput" placeholder="اكتب رسالتك هنا... 💭" maxlength="1000"></textarea>
    <div class="char-count"><span id="charCount">0</span>/1000</div>
    <button class="send-btn" id="sendBtn" onclick="sendMessage()">
        <span>إرسال الرسالة 📨</span>
        <div class="spinner"></div>
    </button>
</div>
<div class="success-state" id="successState">
    <div class="check">✓</div>
    <h2>تم الإرسال بنجاح! 🎉</h2>
    <p>رسالتك وصلت بشكل مجهول تماماً</p>
    <button class="send-another" onclick="resetForm()">إرسال رسالة أخرى 💬</button>
</div>
"""

ERROR_CONTENT = “””

<div class="error-state">
    <div class="icon">🔗</div>
    <h2>الرابط غير صالح</h2>
    <p>هذا الرابط غير موجود أو منتهي الصلاحية</p>
</div>
"""

@app.route(”/”)
def home():
return “<h1 style='text-align:center;margin-top:50px;'>🔮 صارحني بوت يعمل!</h1>”

@app.route(”/send/<link_id>”)
def send_page(link_id):
db = load_db()
link_data = db.get(“links”, {}).get(link_id)

```
if link_data:
    content = FORM_CONTENT % {"name": link_data.get("name", "مجهول")}
    return WEB_PAGE % {"content": content, "link_id": link_id}
else:
    return WEB_PAGE % {"content": ERROR_CONTENT, "link_id": ""}
```

@app.route(”/api/send”, methods=[“POST”])
def api_send():
data = request.get_json()
link_id = data.get(“link_id”)
message_text = data.get(“message”, “”).strip()

```
if not link_id or not message_text:
    return jsonify({"success": False, "error": "بيانات ناقصة"})

if len(message_text) > 1000:
    return jsonify({"success": False, "error": "الرسالة طويلة جداً"})

db = load_db()
link_data = db.get("links", {}).get(link_id)
if not link_data:
    return jsonify({"success": False, "error": "الرابط غير صالح"})

owner_id = link_data["owner"]

# Save
msg_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:10]
db.setdefault("messages", {})[msg_id] = {
    "link_id": link_id,
    "text": message_text,
    "timestamp": datetime.now().isoformat(),
}
db.setdefault("users", {}).setdefault(owner_id, {})
db["users"][owner_id]["message_count"] = db["users"][owner_id].get("message_count", 0) + 1
save_db(db)

# Send via Telegram
try:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    http_requests.post(url, json={
        "chat_id": int(owner_id),
        "text": (
            f"💌 *رسالة مجهولة جديدة!*\n\n"
            f"📝 {message_text}\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🌐 _عبر صفحة الويب_\n"
            f"🔮 _بوت صارحني_"
        ),
        "parse_mode": "Markdown",
    })
except Exception as e:
    logger.error(f"Telegram error: {e}")
    return jsonify({"success": False, "error": "خطأ في الإرسال"})

return jsonify({"success": True})
```

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# MAIN - Run both bot and web server

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_flask():
app.run(host=“0.0.0.0”, port=PORT, debug=False)

def main():
# Start Flask in a background thread
flask_thread = Thread(target=run_flask, daemon=True)
flask_thread.start()
logger.info(f”🌐 Web server started on port {PORT}”)

```
# Start Telegram bot
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("mylink", mylink))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

logger.info("🤖 Telegram bot started!")
application.run_polling(allowed_updates=Update.ALL_TYPES)
```

if **name** == “**main**”:
main()
