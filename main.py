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

BOT_TOKEN = os.environ.get(“BOT_TOKEN”, “YOUR_BOT_TOKEN_HERE”)
WEB_APP_URL = os.environ.get(“RAILWAY_PUBLIC_DOMAIN”, os.environ.get(“WEB_APP_URL”, “localhost:5000”))
if WEB_APP_URL and not WEB_APP_URL.startswith(“http”):
WEB_APP_URL = “https://” + WEB_APP_URL
PORT = int(os.environ.get(“PORT”, “5000”))
DB_FILE = “database.json”

logging.basicConfig(
format=”%(asctime)s - %(name)s - %(levelname)s - %(message)s”,
level=logging.INFO,
)
logger = logging.getLogger(**name**)

def load_db():
if os.path.exists(DB_FILE):
with open(DB_FILE, “r”, encoding=“utf-8”) as f:
return json.load(f)
return {“users”: {}, “links”: {}, “messages”: {}}

def save_db(db):
with open(DB_FILE, “w”, encoding=“utf-8”) as f:
json.dump(db, f, ensure_ascii=False, indent=2)

def generate_link_id(user_id):
raw = str(user_id) + “-” + str(time.time())
return hashlib.md5(raw.encode()).hexdigest()[:8]

async def start(update, context):
user = update.effective_user
db = load_db()

```
if context.args and len(context.args) > 0:
    link_id = context.args[0]
    if link_id in db.get("links", {}):
        context.user_data["sending_to"] = link_id
        await update.message.reply_text(
            "* :envelope_with_arrow: Send your anonymous message*\n\n"
            "Write your message now and it will be sent anonymously\n\n"
            "Write your message:",
            parse_mode="Markdown",
        )
        return

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
    [InlineKeyboardButton("Create link", callback_data="create_link")],
    [InlineKeyboardButton("My stats", callback_data="my_stats")],
    [InlineKeyboardButton("How it works?", callback_data="how_it_works")],
]

await update.message.reply_text(
    "Hello " + user.first_name + "!\n\n"
    "*Anonymous Message Bot*\n\n"
    "Create your own anonymous link and share it with friends!\n\n"
    "Choose from the menu:",
    parse_mode="Markdown",
    reply_markup=InlineKeyboardMarkup(keyboard),
)
```

async def button_handler(update, context):
query = update.callback_query
await query.answer()

```
user = query.from_user
user_id = str(user.id)
db = load_db()

if query.data == "create_link":
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
    tg_link = "https://t.me/" + bot_username + "?start=" + link_id
    web_link = WEB_APP_URL + "/send/" + link_id

    keyboard = [
        [InlineKeyboardButton("Share link", switch_inline_query="Send me anonymous message\n" + tg_link)],
        [InlineKeyboardButton("Main menu", callback_data="main_menu")],
    ]

    await query.edit_message_text(
        "*Link created!*\n\n"
        "Telegram link:\n`" + tg_link + "`\n\n"
        "Web link:\n`" + web_link + "`\n\n"
        "Share with your friends!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

elif query.data == "my_stats":
    user_data = db.get("users", {}).get(user_id, {})
    msg_count = user_data.get("message_count", 0)
    has_link = any(d.get("owner") == user_id for d in db.get("links", {}).values())

    keyboard = [[InlineKeyboardButton("Main menu", callback_data="main_menu")]]

    status_text = "Active" if has_link else "No link"

    await query.edit_message_text(
        "*Your Stats*\n\n"
        "Name: " + user.first_name + "\n"
        "Messages received: " + str(msg_count) + "\n"
        "Link status: " + status_text + "\n",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

elif query.data == "how_it_works":
    keyboard = [
        [InlineKeyboardButton("Create link", callback_data="create_link")],
        [InlineKeyboardButton("Main menu", callback_data="main_menu")],
    ]

    await query.edit_message_text(
        "*How does it work?*\n\n"
        "1. Create your anonymous link\n"
        "2. Share it with friends\n"
        "3. Friend clicks and writes a message\n"
        "4. You receive it here anonymously!\n\n"
        "Privacy: No one can know who sent the message.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

elif query.data == "main_menu":
    keyboard = [
        [InlineKeyboardButton("Create link", callback_data="create_link")],
        [InlineKeyboardButton("My stats", callback_data="my_stats")],
        [InlineKeyboardButton("How it works?", callback_data="how_it_works")],
    ]

    await query.edit_message_text(
        "*Anonymous Message Bot*\n\nChoose from the menu:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
```

async def handle_message(update, context):
user = update.effective_user
db = load_db()

```
link_id = context.user_data.get("sending_to")

if link_id and link_id in db.get("links", {}):
    link_data = db["links"][link_id]
    owner_id = link_data["owner"]
    message_text = update.message.text

    if str(user.id) == owner_id:
        await update.message.reply_text("You cannot send a message to yourself!")
        context.user_data.pop("sending_to", None)
        return

    msg_id = hashlib.md5((str(time.time()) + "-" + str(user.id)).encode()).hexdigest()[:10]
    db.setdefault("messages", {})[msg_id] = {
        "link_id": link_id,
        "text": message_text,
        "timestamp": datetime.now().isoformat(),
    }
    db.setdefault("users", {}).setdefault(owner_id, {})
    db["users"][owner_id]["message_count"] = db["users"][owner_id].get("message_count", 0) + 1
    save_db(db)

    try:
        await context.bot.send_message(
            chat_id=int(owner_id),
            text=(
                "*New anonymous message!*\n\n"
                + message_text + "\n\n"
                "---\n"
                "_Via Anonymous Bot_"
            ),
            parse_mode="Markdown",
        )
        await update.message.reply_text(
            "*Message sent successfully!*\n\n"
            "The recipient will never know your identity\n\n"
            "You can send another message or /start for menu",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error("Send error: " + str(e))
        await update.message.reply_text("Error occurred. Try again.")

    context.user_data.pop("sending_to", None)
    return

await update.message.reply_text("Press /start to begin!")
```

async def mylink(update, context):
user_id = str(update.effective_user.id)
db = load_db()

```
for lid, data in db.get("links", {}).items():
    if data.get("owner") == user_id:
        bot_username = (await context.bot.get_me()).username
        link = "https://t.me/" + bot_username + "?start=" + lid
        await update.message.reply_text("Your link:\n`" + link + "`", parse_mode="Markdown")
        return

await update.message.reply_text("No link yet! Press /start to create one.")
```

app = Flask(**name**)

@app.route(”/”)
def home():
return “<h1>Anonymous Bot is running!</h1>”

@app.route(”/send/<link_id>”)
def send_page(link_id):
db = load_db()
link_data = db.get(“links”, {}).get(link_id)

```
if link_data:
    name = link_data.get("name", "Unknown")
    return PAGE_HTML.replace("RECIPIENT_NAME", name).replace("LINK_ID_VALUE", link_id)
else:
    return "<h1>Invalid link</h1>"
```

@app.route(”/api/send”, methods=[“POST”])
def api_send():
data = request.get_json()
link_id = data.get(“link_id”)
message_text = data.get(“message”, “”).strip()

```
if not link_id or not message_text:
    return jsonify({"success": False, "error": "Missing data"})

if len(message_text) > 1000:
    return jsonify({"success": False, "error": "Message too long"})

db = load_db()
link_data = db.get("links", {}).get(link_id)
if not link_data:
    return jsonify({"success": False, "error": "Invalid link"})

owner_id = link_data["owner"]

msg_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
db.setdefault("messages", {})[msg_id] = {
    "link_id": link_id,
    "text": message_text,
    "timestamp": datetime.now().isoformat(),
}
db.setdefault("users", {}).setdefault(owner_id, {})
db["users"][owner_id]["message_count"] = db["users"][owner_id].get("message_count", 0) + 1
save_db(db)

try:
    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    http_requests.post(url, json={
        "chat_id": int(owner_id),
        "text": (
            "*New anonymous message!*\n\n"
            + message_text + "\n\n"
            "---\n"
            "_Via Web Page_\n"
            "_Anonymous Bot_"
        ),
        "parse_mode": "Markdown",
    })
except Exception as e:
    logger.error("Telegram error: " + str(e))
    return jsonify({"success": False, "error": "Send error"})

return jsonify({"success": True})
```

PAGE_HTML = “””<!DOCTYPE html>

<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Anonymous Message</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:sans-serif;min-height:100vh;background:#0a0a1a;color:#fff;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:24px;padding:40px 30px;width:100%;max-width:500px}
.logo{text-align:center;margin-bottom:30px}
.logo .icon{font-size:56px;margin-bottom:10px}
.logo h1{font-size:32px;color:#a78bfa}
.logo p{color:rgba(255,255,255,0.5);font-size:14px;margin-top:5px}
.recipient{text-align:center;margin-bottom:25px;padding:15px;background:rgba(167,139,250,0.1);border-radius:16px}
.recipient span{color:#a78bfa;font-weight:700;font-size:18px}
textarea{width:100%;min-height:150px;padding:18px;border:2px solid rgba(255,255,255,0.08);border-radius:16px;background:rgba(0,0,0,0.3);color:#fff;font-size:16px;resize:vertical;outline:none;direction:rtl;font-family:sans-serif}
textarea:focus{border-color:rgba(167,139,250,0.5)}
textarea::placeholder{color:rgba(255,255,255,0.25)}
.btn{width:100%;padding:16px;margin-top:20px;border:none;border-radius:16px;font-size:18px;font-weight:700;cursor:pointer;background:linear-gradient(135deg,#8b5cf6,#ec4899);color:#fff}
.btn:disabled{opacity:0.5}
#successBox{display:none;text-align:center;padding:20px}
#successBox h2{font-size:22px;color:#10b981;margin-bottom:8px}
#successBox p{color:rgba(255,255,255,0.5)}
.again{margin-top:20px;padding:12px 30px;border:1px solid rgba(167,139,250,0.3);border-radius:12px;background:transparent;color:#a78bfa;font-size:15px;cursor:pointer}
</style>
</head>
<body>
<div class="card">
<div class="logo">
<div class="icon">&#x1F48C;</div>
<h1>Anonymous Message</h1>
<p>Send your message secretly</p>
</div>
<div id="formBox">
<div class="recipient"><span>RECIPIENT_NAME</span></div>
<textarea id="msg" placeholder="Write your message here..." maxlength="1000"></textarea>
<button class="btn" id="sendBtn" onclick="sendMsg()">Send Message</button>
</div>
<div id="successBox">
<h2>Sent successfully!</h2>
<p>Your message was delivered anonymously</p>
<button class="again" onclick="resetForm()">Send another message</button>
</div>
</div>
<script>
function sendMsg(){
var t=document.getElementById("msg").value.trim();
if(!t)return;
var b=document.getElementById("sendBtn");
b.disabled=true;
b.textContent="Sending...";
fetch("/api/send",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({link_id:"LINK_ID_VALUE",message:t})
}).then(function(r){return r.json()}).then(function(d){
if(d.success){
document.getElementById("formBox").style.display="none";
document.getElementById("successBox").style.display="block";
}else{alert(d.error||"Error")}
b.disabled=false;b.textContent="Send Message";
}).catch(function(){alert("Connection error");b.disabled=false;b.textContent="Send Message"});
}
function resetForm(){
document.getElementById("msg").value="";
document.getElementById("formBox").style.display="block";
document.getElementById("successBox").style.display="none";
}
</script>
</body>
</html>"""

def run_flask():
app.run(host=“0.0.0.0”, port=PORT, debug=False)

def main():
flask_thread = Thread(target=run_flask, daemon=True)
flask_thread.start()
logger.info(“Web server started on port “ + str(PORT))

```
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("mylink", mylink))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

logger.info("Telegram bot started!")
application.run_polling(allowed_updates=Update.ALL_TYPES)
```

if **name** == “**main**”:
main()
