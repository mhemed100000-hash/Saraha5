import os
import json
import hashlib
import time
import logging
from datetime import datetime
from threading import Thread
from flask import Flask, request, jsonify
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

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEB_APP_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN", os.environ.get("WEB_APP_URL", "localhost:5000"))
if WEB_APP_URL and not WEB_APP_URL.startswith("http"):
    WEB_APP_URL = "https://" + WEB_APP_URL
PORT = int(os.environ.get("PORT", "5000"))
DB_FILE = "database.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "links": {}, "messages": {}}


def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def generate_link_id(user_id):
    raw = str(user_id) + "-" + str(time.time())
    return hashlib.md5(raw.encode()).hexdigest()[:8]


async def start(update, context):
    user = update.effective_user
    db = load_db()
    user_count = len(db.get("users", {}))

    if context.args and len(context.args) > 0:
        link_id = context.args[0]
        if link_id in db.get("links", {}):
            link_data = db["links"][link_id]
            owner_name = link_data.get("name", "\u0645\u062c\u0647\u0648\u0644")

            if str(user.id) == link_data.get("owner"):
                await update.message.reply_text(
                    "\u274c *\u0644\u0627 \u064a\u0645\u0643\u0646\u0643 \u0625\u0631\u0633\u0627\u0644 \u0631\u0633\u0627\u0644\u0629 \u0644\u0646\u0641\u0633\u0643!*\n\n"
                    "\U0001f4a1 \u0634\u0627\u0631\u0643 \u0631\u0627\u0628\u0637\u0643 \u0645\u0639 \u0623\u0635\u062f\u0642\u0627\u0626\u0643",
                    parse_mode="Markdown",
                )
                return

            context.user_data["sending_to"] = link_id
            await update.message.reply_text(
                "\u2709\ufe0f *\u0631\u0633\u0627\u0644\u0629 \u0645\u062c\u0647\u0648\u0644\u0629 \u0625\u0644\u0649 " + owner_name + "*\n\n"
                "\U0001f4dd \u0627\u0643\u062a\u0628 \u0631\u0633\u0627\u0644\u062a\u0643 \u0627\u0644\u0627\u0646\n"
                "\u0633\u064a\u062a\u0645 \u0625\u0631\u0633\u0627\u0644\u0647\u0627 \u0628\u0634\u0643\u0644 *\u0645\u062c\u0647\u0648\u0644 \u062a\u0645\u0627\u0645\u0627\u064b* \U0001f92b\n\n"
                "\U0001f4ac \u0627\u0643\u062a\u0628 \u0631\u0633\u0627\u0644\u062a\u0643:",
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
        [InlineKeyboardButton("\U0001f517 \u0625\u0646\u0634\u0627\u0621 \u0631\u0627\u0628\u0637 \u0635\u0631\u0627\u062d\u0629", callback_data="create_link")],
        [InlineKeyboardButton("\U0001f4ca \u0625\u062d\u0635\u0627\u0626\u064a\u0627\u062a\u064a", callback_data="my_stats")],
        [InlineKeyboardButton("\u2753 \u0643\u064a\u0641 \u064a\u0639\u0645\u0644 \u0627\u0644\u0628\u0648\u062a\u061f", callback_data="how_it_works")],
    ]

    await update.message.reply_text(
        "\u0645\u0631\u062d\u0628\u0627\u064b " + user.first_name + "! \U0001f44b\n\n"
        "\U0001f4e8 *\u0628\u0648\u062a \u0635\u0627\u0631\u062d\u0646\u064a*\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
        "\U0001f48c \u0623\u0646\u0634\u0626 \u0631\u0627\u0628\u0637 \u0635\u0631\u0627\u062d\u0629 \u062e\u0627\u0635 \u0628\u0643\n"
        "\u0648\u0634\u0627\u0631\u0643\u0647 \u0645\u0639 \u0623\u0635\u062f\u0642\u0627\u0626\u0643 \u0644\u064a\u0631\u0633\u0644\u0648\u0627 \u0644\u0643\n"
        "\u0631\u0633\u0627\u0626\u0644 \u0645\u062c\u0647\u0648\u0644\u0629! \U0001f92b\n\n"
        "\U0001f465 \u0639\u062f\u062f \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645\u064a\u0646: " + str(user_count) + "\n\n"
        "\u0627\u062e\u062a\u0631 \u0645\u0646 \u0627\u0644\u0642\u0627\u0626\u0645\u0629:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
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
            [InlineKeyboardButton("\U0001f4e4 \u0645\u0634\u0627\u0631\u0643\u0629 \u0627\u0644\u0631\u0627\u0628\u0637", switch_inline_query="\U0001f48c \u0623\u0631\u0633\u0644\u064a \u0631\u0633\u0627\u0644\u0629 \u0645\u062c\u0647\u0648\u0644\u0629:\n" + tg_link)],
            [
                InlineKeyboardButton("\U0001f504 \u062a\u062c\u062f\u064a\u062f", callback_data="renew_link"),
                InlineKeyboardButton("\U0001f5d1 \u062d\u0630\u0641", callback_data="delete_link"),
            ],
            [InlineKeyboardButton("\U0001f519 \u0627\u0644\u0642\u0627\u0626\u0645\u0629 \u0627\u0644\u0631\u0626\u064a\u0633\u064a\u0629", callback_data="main_menu")],
        ]
        await query.edit_message_text(
            "\u2705 *\u062a\u0645 \u0625\u0646\u0634\u0627\u0621 \u0631\u0627\u0628\u0637 \u0627\u0644\u0635\u0631\u0627\u062d\u0629!*\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "\U0001f517 *\u0631\u0627\u0628\u0637 \u0627\u0644\u062a\u0644\u064a\u062c\u0631\u0627\u0645:*\n`" + tg_link + "`\n\n"
            "\U0001f310 *\u0631\u0627\u0628\u0637 \u0627\u0644\u0648\u064a\u0628:*\n`" + web_link + "`\n\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            "\U0001f4e2 \u0634\u0627\u0631\u0643 \u0627\u0644\u0631\u0627\u0628\u0637 \u0645\u0639 \u0623\u0635\u062f\u0642\u0627\u0626\u0643!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "renew_link":
        for lid, data in list(db.get("links", {}).items()):
            if data.get("owner") == user_id:
                del db["links"][lid]
                break
        link_id = generate_link_id(user.id)
        db.setdefault("links", {})[link_id] = {"owner": user_id, "name": user.first_name, "created": datetime.now().isoformat()}
        save_db(db)
        bot_username = (await context.bot.get_me()).username
        tg_link = "https://t.me/" + bot_username + "?start=" + link_id
        keyboard = [
            [InlineKeyboardButton("\U0001f4e4 \u0645\u0634\u0627\u0631\u0643\u0629", switch_inline_query="\U0001f48c \u0623\u0631\u0633\u0644\u064a \u0631\u0633\u0627\u0644\u0629 \u0645\u062c\u0647\u0648\u0644\u0629:\n" + tg_link)],
            [InlineKeyboardButton("\U0001f519 \u0627\u0644\u0642\u0627\u0626\u0645\u0629", callback_data="main_menu")],
        ]
        await query.edit_message_text(
            "\U0001f504 *\u062a\u0645 \u062a\u062c\u062f\u064a\u062f \u0627\u0644\u0631\u0627\u0628\u0637!*\n\n\U0001f517 \u0627\u0644\u0631\u0627\u0628\u0637 \u0627\u0644\u062c\u062f\u064a\u062f:\n`" + tg_link + "`\n\n\u26a0\ufe0f \u0627\u0644\u0631\u0627\u0628\u0637 \u0627\u0644\u0642\u062f\u064a\u0645 \u0644\u0645 \u064a\u0639\u062f \u064a\u0639\u0645\u0644",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "delete_link":
        for lid, data in list(db.get("links", {}).items()):
            if data.get("owner") == user_id:
                del db["links"][lid]
                save_db(db)
                break
        keyboard = [
            [InlineKeyboardButton("\U0001f517 \u0625\u0646\u0634\u0627\u0621 \u0631\u0627\u0628\u0637 \u062c\u062f\u064a\u062f", callback_data="create_link")],
            [InlineKeyboardButton("\U0001f519 \u0627\u0644\u0642\u0627\u0626\u0645\u0629", callback_data="main_menu")],
        ]
        await query.edit_message_text(
            "\U0001f5d1 *\u062a\u0645 \u062d\u0630\u0641 \u0627\u0644\u0631\u0627\u0628\u0637*\n\n\u064a\u0645\u0643\u0646\u0643 \u0625\u0646\u0634\u0627\u0621 \u0631\u0627\u0628\u0637 \u062c\u062f\u064a\u062f",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "my_stats":
        user_data = db.get("users", {}).get(user_id, {})
        msg_count = user_data.get("message_count", 0)
        has_link = any(d.get("owner") == user_id for d in db.get("links", {}).values())
        join_date = user_data.get("joined", "")
        if join_date:
            try:
                join_date = datetime.fromisoformat(join_date).strftime("%Y/%m/%d")
            except Exception:
                join_date = "-"
        status_text = "\U0001f7e2 \u0641\u0639\u0627\u0644" if has_link else "\U0001f534 \u0644\u0627 \u064a\u0648\u062c\u062f"
        keyboard = [[InlineKeyboardButton("\U0001f519 \u0627\u0644\u0642\u0627\u0626\u0645\u0629", callback_data="main_menu")]]
        await query.edit_message_text(
            "\U0001f4ca *\u0625\u062d\u0635\u0627\u0626\u064a\u0627\u062a\u0643*\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "\U0001f464 *\u0627\u0644\u0627\u0633\u0645:* " + user.first_name + "\n"
            "\U0001f4e9 *\u0627\u0644\u0631\u0633\u0627\u0626\u0644:* " + str(msg_count) + "\n"
            "\U0001f517 *\u0627\u0644\u0631\u0627\u0628\u0637:* " + status_text + "\n"
            "\U0001f4c5 *\u0627\u0644\u0627\u0646\u0636\u0645\u0627\u0645:* " + join_date,
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "how_it_works":
        keyboard = [
            [InlineKeyboardButton("\U0001f517 \u0625\u0646\u0634\u0627\u0621 \u0631\u0627\u0628\u0637", callback_data="create_link")],
            [InlineKeyboardButton("\U0001f519 \u0627\u0644\u0642\u0627\u0626\u0645\u0629", callback_data="main_menu")],
        ]
        await query.edit_message_text(
            "\u2753 *\u0643\u064a\u0641 \u064a\u0639\u0645\u0644 \u0628\u0648\u062a \u0635\u0627\u0631\u062d\u0646\u064a\u061f*\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "1\ufe0f\u20e3 \u0623\u0646\u0634\u0626 \u0631\u0627\u0628\u0637 \u0627\u0644\u0635\u0631\u0627\u062d\u0629 \u0627\u0644\u062e\u0627\u0635 \u0628\u0643\n\n"
            "2\ufe0f\u20e3 \u0634\u0627\u0631\u0643\u0647 \u0645\u0639 \u0623\u0635\u062f\u0642\u0627\u0626\u0643\n\n"
            "3\ufe0f\u20e3 \u0635\u062f\u064a\u0642\u0643 \u064a\u0636\u063a\u0637 \u0627\u0644\u0631\u0627\u0628\u0637 \u0648\u064a\u0643\u062a\u0628 \u0631\u0633\u0627\u0644\u0629\n\n"
            "4\ufe0f\u20e3 \u062a\u0635\u0644\u0643 \u0627\u0644\u0631\u0633\u0627\u0644\u0629 \u0647\u0646\u0627 \u0628\u0634\u0643\u0644 \u0645\u062c\u0647\u0648\u0644!\n\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            "\U0001f512 \u0644\u0627 \u064a\u0645\u0643\u0646 \u0645\u0639\u0631\u0641\u0629 \u0647\u0648\u064a\u0629 \u0627\u0644\u0645\u0631\u0633\u0644 \u0646\u0647\u0627\u0626\u064a\u0627\u064b",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "main_menu":
        user_count = len(db.get("users", {}))
        keyboard = [
            [InlineKeyboardButton("\U0001f517 \u0625\u0646\u0634\u0627\u0621 \u0631\u0627\u0628\u0637 \u0635\u0631\u0627\u062d\u0629", callback_data="create_link")],
            [InlineKeyboardButton("\U0001f4ca \u0625\u062d\u0635\u0627\u0626\u064a\u0627\u062a\u064a", callback_data="my_stats")],
            [InlineKeyboardButton("\u2753 \u0643\u064a\u0641 \u064a\u0639\u0645\u0644 \u0627\u0644\u0628\u0648\u062a\u061f", callback_data="how_it_works")],
        ]
        await query.edit_message_text(
            "\U0001f4e8 *\u0628\u0648\u062a \u0635\u0627\u0631\u062d\u0646\u064a*\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "\U0001f465 \u0639\u062f\u062f \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645\u064a\u0646: " + str(user_count) + "\n\n"
            "\u0627\u062e\u062a\u0631 \u0645\u0646 \u0627\u0644\u0642\u0627\u0626\u0645\u0629:",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def handle_message(update, context):
    user = update.effective_user
    db = load_db()
    link_id = context.user_data.get("sending_to")

    if link_id and link_id in db.get("links", {}):
        link_data = db["links"][link_id]
        owner_id = link_data["owner"]
        message_text = update.message.text

        if str(user.id) == owner_id:
            await update.message.reply_text("\u274c \u0644\u0627 \u064a\u0645\u0643\u0646\u0643 \u0625\u0631\u0633\u0627\u0644 \u0631\u0633\u0627\u0644\u0629 \u0644\u0646\u0641\u0633\u0643!")
            context.user_data.pop("sending_to", None)
            return

        msg_id = hashlib.md5((str(time.time()) + "-" + str(user.id)).encode()).hexdigest()[:10]
        db.setdefault("messages", {})[msg_id] = {"link_id": link_id, "text": message_text, "timestamp": datetime.now().isoformat()}
        db.setdefault("users", {}).setdefault(owner_id, {})
        db["users"][owner_id]["message_count"] = db["users"][owner_id].get("message_count", 0) + 1
        save_db(db)

        try:
            msg_count = db["users"][owner_id].get("message_count", 0)
            await context.bot.send_message(
                chat_id=int(owner_id),
                text=(
                    "\U0001f48c *\u0631\u0633\u0627\u0644\u0629 \u0645\u062c\u0647\u0648\u0644\u0629 \u062c\u062f\u064a\u062f\u0629!*\n"
                    "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
                    "\U0001f4dd " + message_text + "\n\n"
                    "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
                    "\U0001f4e9 \u0627\u0644\u0631\u0633\u0627\u0644\u0629 \u0631\u0642\u0645: " + str(msg_count) + "\n"
                    "_\U0001f52e \u0639\u0628\u0631 \u0628\u0648\u062a \u0635\u0627\u0631\u062d\u0646\u064a_"
                ),
                parse_mode="Markdown",
            )

            reply_text = (
                "\u2705 *\u062a\u0645 \u0625\u0631\u0633\u0627\u0644 \u0631\u0633\u0627\u0644\u062a\u0643 \u0628\u0646\u062c\u0627\u062d .* \U0001f49a\n\n"
                "\u0644\u0646 \u064a\u0639\u0631\u0641 \u0627\u0644\u0645\u0633\u062a\u0644\u0645 \u0647\u0648\u064a\u062a\u0643 \u0623\u0628\u062f\u0627\u064b \U0001f92b\n\n"
                "\U0001f4ac \u064a\u0645\u0643\u0646\u0643 \u0625\u0631\u0633\u0627\u0644 \u0631\u0633\u0627\u0644\u0629 \u0623\u062e\u0631\u0649"
            )
            await update.message.reply_text(reply_text, parse_mode="Markdown")

        except Exception as e:
            logger.error("Send error: " + str(e))
            await update.message.reply_text("\u274c \u062d\u062f\u062b \u062e\u0637\u0623. \u062d\u0627\u0648\u0644 \u0645\u0631\u0629 \u0623\u062e\u0631\u0649.")

        context.user_data.pop("sending_to", None)
        return

    await update.message.reply_text("\U0001f4a1 \u0627\u0636\u063a\u0637 /start \u0644\u0644\u0628\u062f\u0621!")


async def mylink(update, context):
    user_id = str(update.effective_user.id)
    db = load_db()
    for lid, data in db.get("links", {}).items():
        if data.get("owner") == user_id:
            bot_username = (await context.bot.get_me()).username
            link = "https://t.me/" + bot_username + "?start=" + lid
            web_link = WEB_APP_URL + "/send/" + lid
            await update.message.reply_text(
                "\U0001f517 *\u0631\u0648\u0627\u0628\u0637\u0643:*\n\n"
                "\U0001f4f1 \u062a\u0644\u064a\u062c\u0631\u0627\u0645:\n`" + link + "`\n\n"
                "\U0001f310 \u0648\u064a\u0628:\n`" + web_link + "`",
                parse_mode="Markdown",
            )
            return
    await update.message.reply_text("\u274c \u0644\u0645 \u062a\u0646\u0634\u0626 \u0631\u0627\u0628\u0637 \u0628\u0639\u062f! \u0627\u0636\u063a\u0637 /start")


app = Flask(__name__)


@app.route("/")
def home():
    return "<h1>Bot is running!</h1>"


@app.route("/send/<link_id>")
def send_page(link_id):
    db = load_db()
    link_data = db.get("links", {}).get(link_id)
    if link_data:
        name = link_data.get("name", "\u0645\u062c\u0647\u0648\u0644")
        return PAGE_HTML.replace("RECIPIENT_NAME", name).replace("LINK_ID_VALUE", link_id)
    return ERROR_HTML


@app.route("/api/send", methods=["POST"])
def api_send():
    data = request.get_json()
    link_id = data.get("link_id")
    message_text = data.get("message", "").strip()
    if not link_id or not message_text:
        return jsonify({"success": False, "error": "\u0628\u064a\u0627\u0646\u0627\u062a \u0646\u0627\u0642\u0635\u0629"})
    if len(message_text) > 1000:
        return jsonify({"success": False, "error": "\u0627\u0644\u0631\u0633\u0627\u0644\u0629 \u0637\u0648\u064a\u0644\u0629 \u062c\u062f\u0627\u064b"})
    db = load_db()
    link_data = db.get("links", {}).get(link_id)
    if not link_data:
        return jsonify({"success": False, "error": "\u0627\u0644\u0631\u0627\u0628\u0637 \u063a\u064a\u0631 \u0635\u0627\u0644\u062d"})
    owner_id = link_data["owner"]
    msg_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
    db.setdefault("messages", {})[msg_id] = {"link_id": link_id, "text": message_text, "timestamp": datetime.now().isoformat()}
    db.setdefault("users", {}).setdefault(owner_id, {})
    db["users"][owner_id]["message_count"] = db["users"][owner_id].get("message_count", 0) + 1
    save_db(db)
    try:
        msg_count = db["users"][owner_id].get("message_count", 0)
        url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
        http_requests.post(url, json={
            "chat_id": int(owner_id),
            "text": (
                "\U0001f48c *\u0631\u0633\u0627\u0644\u0629 \u0645\u062c\u0647\u0648\u0644\u0629 \u062c\u062f\u064a\u062f\u0629!*\n"
                "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
                "\U0001f4dd " + message_text + "\n\n"
                "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
                "\U0001f4e9 \u0627\u0644\u0631\u0633\u0627\u0644\u0629 \u0631\u0642\u0645: " + str(msg_count) + "\n"
                "_\U0001f310 \u0639\u0628\u0631 \u0635\u0641\u062d\u0629 \u0627\u0644\u0648\u064a\u0628_\n"
                "_\U0001f52e \u0628\u0648\u062a \u0635\u0627\u0631\u062d\u0646\u064a_"
            ),
            "parse_mode": "Markdown",
        })
    except Exception as e:
        logger.error("Telegram error: " + str(e))
        return jsonify({"success": False, "error": "\u062e\u0637\u0623 \u0641\u064a \u0627\u0644\u0625\u0631\u0633\u0627\u0644"})
    return jsonify({"success": True})


PAGE_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>\u0635\u0627\u0631\u062d\u0646\u064a</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:sans-serif;min-height:100vh;background:#0a0a1a;color:#fff;overflow-x:hidden}
body::before{content:'';position:fixed;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle at 20% 50%,rgba(120,50,255,0.15) 0%,transparent 50%),radial-gradient(circle at 80% 20%,rgba(255,50,150,0.1) 0%,transparent 50%),radial-gradient(circle at 50% 80%,rgba(50,100,255,0.1) 0%,transparent 50%);z-index:0}
.container{position:relative;z-index:1;max-width:500px;margin:0 auto;padding:40px 20px;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center}
.card{background:rgba(255,255,255,0.05);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.08);border-radius:24px;padding:40px 30px;width:100%;animation:cardIn 0.8s ease}
@keyframes cardIn{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}
.logo{text-align:center;margin-bottom:30px}
.logo .icon{font-size:56px;margin-bottom:10px}
.logo h1{font-size:32px;color:#a78bfa}
.logo p{color:rgba(255,255,255,0.5);font-size:14px;margin-top:5px}
.recipient{text-align:center;margin-bottom:25px;padding:15px;background:rgba(167,139,250,0.1);border-radius:16px;border:1px solid rgba(167,139,250,0.15)}
.recipient span{color:#a78bfa;font-weight:700;font-size:18px}
.recipient p{color:rgba(255,255,255,0.5);font-size:13px;margin-top:4px}
textarea{width:100%;min-height:150px;padding:18px;border:2px solid rgba(255,255,255,0.08);border-radius:16px;background:rgba(0,0,0,0.3);color:#fff;font-size:16px;resize:vertical;outline:none;direction:rtl;font-family:sans-serif;transition:border-color 0.3s}
textarea:focus{border-color:rgba(167,139,250,0.5)}
textarea::placeholder{color:rgba(255,255,255,0.25)}
.count{text-align:left;font-size:12px;color:rgba(255,255,255,0.3);margin-top:8px}
.btn{width:100%;padding:16px;margin-top:20px;border:none;border-radius:16px;font-size:18px;font-weight:700;cursor:pointer;background:linear-gradient(135deg,#8b5cf6,#a855f7,#ec4899);color:#fff;transition:all 0.3s}
.btn:hover{transform:translateY(-2px);box-shadow:0 10px 40px rgba(139,92,246,0.3)}
.btn:disabled{opacity:0.5;cursor:not-allowed;transform:none}
#successBox{display:none;text-align:center;padding:20px;animation:sIn 0.5s ease}
@keyframes sIn{from{opacity:0;transform:scale(0.8)}to{opacity:1;transform:scale(1)}}
.check{width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,#10b981,#34d399);display:flex;align-items:center;justify-content:center;margin:0 auto 20px;font-size:40px}
#successBox h2{font-size:22px;margin-bottom:8px}
#successBox p{color:rgba(255,255,255,0.5);font-size:14px}
.again{margin-top:20px;padding:12px 30px;border:1px solid rgba(167,139,250,0.3);border-radius:12px;background:transparent;color:#a78bfa;font-size:15px;font-weight:600;cursor:pointer;transition:all 0.3s}
.again:hover{background:rgba(167,139,250,0.1)}
.footer{text-align:center;margin-top:30px;color:rgba(255,255,255,0.2);font-size:12px}
</style>
</head>
<body>
<div class="container">
<div class="card">
<div class="logo">
<div class="icon">&#x1F48C;</div>
<h1>\u0635\u0627\u0631\u062d\u0646\u064a</h1>
<p>\u0623\u0631\u0633\u0644 \u0631\u0633\u0627\u0644\u062a\u0643 \u0628\u0633\u0631\u064a\u0629 \u062a\u0627\u0645\u0629</p>
</div>
<div id="formBox">
<div class="recipient">
<span>RECIPIENT_NAME</span>
<p>\u0623\u0631\u0633\u0644 \u0631\u0633\u0627\u0644\u0629 \u0645\u062c\u0647\u0648\u0644\u0629</p>
</div>
<textarea id="msg" placeholder="\u0627\u0643\u062a\u0628 \u0631\u0633\u0627\u0644\u062a\u0643 \u0647\u0646\u0627..." maxlength="1000" oninput="document.getElementById('cc').textContent=this.value.length"></textarea>
<div class="count"><span id="cc">0</span>/1000</div>
<button class="btn" id="sendBtn" onclick="sendMsg()">\u0625\u0631\u0633\u0627\u0644 \u0627\u0644\u0631\u0633\u0627\u0644\u0629 &#x1F4E8;</button>
</div>
<div id="successBox">
<div class="check">&#x2713;</div>
<h2>\u062a\u0645 \u0627\u0644\u0625\u0631\u0633\u0627\u0644 \u0628\u0646\u062c\u0627\u062d! &#x1F389;</h2>
<p>\u0631\u0633\u0627\u0644\u062a\u0643 \u0648\u0635\u0644\u062a \u0628\u0634\u0643\u0644 \u0645\u062c\u0647\u0648\u0644 \u062a\u0645\u0627\u0645\u0627\u064b</p>
<button class="again" onclick="resetForm()">\u0625\u0631\u0633\u0627\u0644 \u0631\u0633\u0627\u0644\u0629 \u0623\u062e\u0631\u0649 &#x1F4AC;</button>
</div>
</div>
<div class="footer">\u0635\u0627\u0631\u062d\u0646\u064a \u0628\u0648\u062a &#x1F49C;</div>
</div>
<script>
function sendMsg(){
var t=document.getElementById("msg").value.trim();
if(!t)return;
var b=document.getElementById("sendBtn");
b.disabled=true;
b.textContent="\u062c\u0627\u0631\u064a \u0627\u0644\u0625\u0631\u0633\u0627\u0644...";
fetch("/api/send",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({link_id:"LINK_ID_VALUE",message:t})
}).then(function(r){return r.json()}).then(function(d){
if(d.success){
document.getElementById("formBox").style.display="none";
document.getElementById("successBox").style.display="block";
}else{alert(d.error||"\u062d\u062f\u062b \u062e\u0637\u0623")}
b.disabled=false;b.textContent="\u0625\u0631\u0633\u0627\u0644 \u0627\u0644\u0631\u0633\u0627\u0644\u0629";
}).catch(function(){alert("\u062e\u0637\u0623 \u0641\u064a \u0627\u0644\u0627\u062a\u0635\u0627\u0644");b.disabled=false;b.textContent="\u0625\u0631\u0633\u0627\u0644 \u0627\u0644\u0631\u0633\u0627\u0644\u0629";});
}
function resetForm(){
document.getElementById("msg").value="";
document.getElementById("cc").textContent="0";
document.getElementById("formBox").style.display="block";
document.getElementById("successBox").style.display="none";
}
</script>
</body>
</html>"""

ERROR_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>\u0635\u0627\u0631\u062d\u0646\u064a</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:sans-serif;min-height:100vh;background:#0a0a1a;color:#fff;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:24px;padding:40px 30px;width:100%;max-width:500px;text-align:center}
.icon{font-size:60px;margin-bottom:15px}
h2{font-size:20px;margin-bottom:8px}
p{color:rgba(255,255,255,0.5);font-size:14px}
</style>
</head>
<body>
<div class="card">
<div class="icon">&#x1F517;</div>
<h2>\u0627\u0644\u0631\u0627\u0628\u0637 \u063a\u064a\u0631 \u0635\u0627\u0644\u062d</h2>
<p>\u0647\u0630\u0627 \u0627\u0644\u0631\u0627\u0628\u0637 \u063a\u064a\u0631 \u0645\u0648\u062c\u0648\u062f \u0623\u0648 \u0645\u0646\u062a\u0647\u064a \u0627\u0644\u0635\u0644\u0627\u062d\u064a\u0629</p>
</div>
</body>
</html>"""


def run_flask():
    app.run(host="0.0.0.0", port=PORT, debug=False)


def main():
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Web server started on port " + str(PORT))
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mylink", mylink))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Telegram bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
