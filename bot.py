#!/usr/bin/env python3
"""
🎭 لعبة التحديات — havana Chat 🦩
صراحة / جرأة / رهان — البوت هو الحكم
"""

import asyncio, random, logging, json, os
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from telegram.error import TelegramError

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8712365309:AAExk4vAUogk2L5wgozuE-cSq3TdEHcOSWg"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
START_IMAGE_PATH = os.path.join(BASE_DIR, "start_cover.jpg")
STATS_FILE = "dare_stats.json"
MIN_PLAYERS = 2
MAX_PLAYERS = 20
CHALLENGE_TIME = 90       # seconds to complete challenge
MUTE_DURATIONS = [120, 180, 240, 300]

SHAME_TITLES = [
    "جبان القروب 🐔", "أبو الفضايح 😂", "ملك الهروب 🏃",
    "خايف من ظلّو 👻", "فرّار معتمد 🚪", "بطل التهرّب 🏆",
    "قلبو أرنب 🐰", "مانو جريء 😬", "أضعف حلقة ⛓", "ما بيقدر 🙈",
]
FUNNY_NAMES = [
    "أبو فضيحة", "الجبان الصغير", "خيّو خايف", "فرّوج القروب",
    "بطل الهروب", "مسكين ما قدر", "أرنوب", "ضعيف القلب",
    "يا عيب الشوم", "هارب من التحدي",
]

class PunishType(Enum):
    MUTE = auto(); RENAME = auto(); SHAME = auto()

class ChallengeType(Enum):
    TRUTH = "truth"; DARE = "dare"; BET = "bet"

class Phase(Enum):
    LOBBY = auto(); CHOOSING = auto(); WAITING_CHALLENGE = auto()
    EXECUTING = auto(); JUDGING = auto(); PUNISHING = auto(); GAME_OVER = auto()

@dataclass
class Player:
    user_id: int; name: str; username: str = ""
    shame_title: str = ""; punishments: int = 0; completed: int = 0; played: bool = False
    @property
    def tag(self):
        if self.username: return f"@{self.username}"
        return f"[{self.name}](tg://user?id={self.user_id})"
    @property
    def display(self):
        return f"{self.name} ({self.shame_title})" if self.shame_title else self.name

class Game:
    def __init__(self, cid):
        self.chat_id = cid; self.phase = Phase.LOBBY
        self.players: Dict[int, Player] = {}
        self.play_order: List[int] = []; self.current_idx = 0
        self.current_type: Optional[ChallengeType] = None
        self.current_challenge = ""; self.challenge_author: Optional[int] = None
        self.challenge_writer: Optional[int] = None  # the player chosen to write the challenge
        self.lobby_msg_id: Optional[int] = None; self._lobby_is_photo = False
        self._task = None; self._lobby_task = None; self._timeout_task = None

    def add_player(self, uid, name, username=""):
        if uid in self.players or self.phase != Phase.LOBBY or len(self.players) >= MAX_PLAYERS:
            return False
        self.players[uid] = Player(user_id=uid, name=name, username=username)
        return True

    @property
    def current_player(self):
        if not self.play_order or self.current_idx >= len(self.play_order): return None
        return self.players.get(self.play_order[self.current_idx])

    def start_game(self):
        self.play_order = list(self.players.keys())
        random.shuffle(self.play_order)
        self.current_idx = 0; self.phase = Phase.CHOOSING

    def next_player(self):
        self.current_idx += 1
        self.current_type = None; self.current_challenge = ""; self.challenge_author = None; self.challenge_writer = None
        if self.current_idx >= len(self.play_order):
            self.phase = Phase.GAME_OVER; return False
        self.phase = Phase.CHOOSING; return True

class GameManager:
    def __init__(self): self.games: Dict[int, Game] = {}
    def get(self, cid): return self.games.get(cid)
    def create(self, cid): g = Game(cid); self.games[cid] = g; return g
    def remove(self, cid):
        if cid in self.games:
            g = self.games[cid]
            for t in [g._task, g._lobby_task, g._timeout_task]:
                if t and not t.done(): t.cancel()
            del self.games[cid]

gm = GameManager()

# ── Helpers ──
def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: pass
    return {}

def save_stats(s):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f: json.dump(s, f, ensure_ascii=False, indent=2)
    except: pass

def update_stat(uid, name, key, val=1):
    s = load_stats(); u = str(uid)
    if u not in s: s[u] = {"name": name, "games": 0, "completed": 0, "punished": 0, "chickened": 0}
    s[u]["name"] = name; s[u][key] = s[u].get(key, 0) + val; save_stats(s)

async def is_admin(bot, cid, uid):
    try:
        m = await bot.get_chat_member(cid, uid)
        return m.status in ("administrator", "creator")
    except: return False

async def ssend(bot, cid, text, **kw):
    try: return await bot.send_message(chat_id=cid, text=text, **kw)
    except TelegramError as e: logger.error(f"Send fail: {e}"); return None

async def sdm(bot, uid, text, **kw):
    try: return await bot.send_message(chat_id=uid, text=text, **kw)
    except TelegramError as e: logger.warning(f"DM fail: {e}"); return None

# ── Punishment ──
async def execute_punishment(bot, g, player):
    ptype = random.choice([PunishType.MUTE, PunishType.RENAME, PunishType.SHAME])
    cid = g.chat_id; result = ""

    if ptype == PunishType.MUTE:
        dur = random.choice(MUTE_DURATIONS); mins = dur // 60
        try:
            from datetime import datetime, timedelta
            from telegram import ChatPermissions
            until = datetime.utcnow() + timedelta(seconds=dur)
            await bot.restrict_chat_member(cid, player.user_id,
                permissions=ChatPermissions(can_send_messages=False), until_date=until)
            result = f"🔇 تم كتم {player.tag} لمدة {mins} دقيقة!"
        except TelegramError as e:
            logger.warning(f"Mute fail: {e}")
            result = f"🔇 ما قدرت أكتمه — تأكدوا إني أدمن!"

    elif ptype == PunishType.RENAME:
        new_name = random.choice(FUNNY_NAMES)
        try:
            await bot.set_chat_administrator_custom_title(cid, player.user_id, new_name)
            result = f"📝 تم تغيير لقب {player.tag} لـ «{new_name}»!"
        except TelegramError:
            player.shame_title = new_name
            result = f"📝 {player.tag} صار اسمه «{new_name}» لباقي اللعبة!"

    elif ptype == PunishType.SHAME:
        title = random.choice(SHAME_TITLES)
        player.shame_title = title
        result = f"🏷 {player.tag} حصل على لقب: *{title}*"

    player.punishments += 1
    return result

# ── Lobby ──
def lobby_text(g):
    pl = "".join(f"  {i}. {p.tag}\n" for i, p in enumerate(g.players.values(), 1))
    pl = pl or "  ما في حدا لسا…\n"
    c = len(g.players)
    st = "🟢 جاهزين للبدء!" if c >= MIN_PLAYERS else f"⏳ بدنا {MIN_PLAYERS - c} لاعبين كمان"
    return (f"🎭 *لعبة التحديات* — 𝘩𝘢𝘷𝘢𝘯𝘢 𝘊𝘩𝘢𝘵 🦩\n\n"
            f"🔥 صراحة · جرأة · رهان\n💀 اللي ما بينفّذ بيتعاقب!\n\n"
            f"👥 *اللاعبين* ({c}/{MAX_PLAYERS}):\n{pl}\n{st}")

def lobby_kb(g):
    c = len(g.players)
    b = [[InlineKeyboardButton("◉ انضم للعبة", callback_data=f"join_{g.chat_id}")]]
    if c >= MIN_PLAYERS: b.append([InlineKeyboardButton("▶ يلا نبدأ!", callback_data=f"sg_{g.chat_id}")])
    b.append([InlineKeyboardButton("✕ إلغاء", callback_data=f"cg_{g.chat_id}")])
    return InlineKeyboardMarkup(b)

async def send_lobby_photo(bot, g):
    txt = lobby_text(g); kb = lobby_kb(g)
    try:
        if os.path.exists(START_IMAGE_PATH):
            with open(START_IMAGE_PATH, "rb") as f:
                m = await bot.send_photo(chat_id=g.chat_id, photo=f, caption=txt, parse_mode="Markdown", reply_markup=kb)
                if m: g.lobby_msg_id = m.message_id; g._lobby_is_photo = True
                return m
    except Exception as e: logger.warning(f"Lobby photo fail: {e}")
    m = await ssend(bot, g.chat_id, txt, parse_mode="Markdown", reply_markup=kb)
    if m: g.lobby_msg_id = m.message_id; g._lobby_is_photo = False
    return m

async def update_lobby(bot, g):
    if not g.lobby_msg_id: return
    try:
        if g._lobby_is_photo:
            await bot.edit_message_caption(chat_id=g.chat_id, message_id=g.lobby_msg_id,
                caption=lobby_text(g), parse_mode="Markdown", reply_markup=lobby_kb(g))
        else:
            await bot.edit_message_text(chat_id=g.chat_id, message_id=g.lobby_msg_id,
                text=lobby_text(g), parse_mode="Markdown", reply_markup=lobby_kb(g))
    except: pass

async def lobby_refresh_loop(bot, g):
    try:
        while g.phase == Phase.LOBBY:
            await asyncio.sleep(90)
            if g.phase != Phase.LOBBY: break
            try:
                if g.lobby_msg_id: await bot.delete_message(chat_id=g.chat_id, message_id=g.lobby_msg_id)
            except: pass
            await send_lobby_photo(bot, g)
    except asyncio.CancelledError: pass
    except Exception as e: logger.error(f"Lobby refresh: {e}")

# ── Game Flow ──
async def start_round(bot, g):
    p = g.current_player
    if not p: await end_game(bot, g); return
    g.phase = Phase.CHOOSING; p.played = True
    rn = g.current_idx + 1; total = len(g.play_order)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗣 صراحة", callback_data=f"ct_{g.chat_id}_truth"),
         InlineKeyboardButton("🔥 جرأة", callback_data=f"ct_{g.chat_id}_dare")],
        [InlineKeyboardButton("🎰 رهان", callback_data=f"ct_{g.chat_id}_bet")]
    ])
    await ssend(bot, g.chat_id,
        f"🎯 *الجولة {rn}/{total}*\n\nدور {p.tag}\n\nاختار نوع التحدي:",
        parse_mode="Markdown", reply_markup=kb)

async def ask_for_challenge(bot, g):
    p = g.current_player; g.phase = Phase.WAITING_CHALLENGE
    tname = {ChallengeType.TRUTH: "🗣 صراحة", ChallengeType.DARE: "🔥 جرأة", ChallengeType.BET: "🎰 رهان"}
    tdesc = {ChallengeType.TRUTH: "اكتب سؤال صراحة لـ", ChallengeType.DARE: "اكتب تحدي جرأة لـ", ChallengeType.BET: "اكتب رهان لـ"}
    # Pick a random player (not the current one) to write the challenge
    others = [pl for pl in g.players.values() if pl.user_id != p.user_id]
    if not others:
        await ssend(bot, g.chat_id, "ما في حدا ثاني يكتب التحدي!")
        if g.next_player(): await start_round(bot, g)
        else: await end_game(bot, g)
        return
    writer = random.choice(others)
    g.challenge_writer = writer.user_id
    await ssend(bot, g.chat_id,
        f"{tname.get(g.current_type, '🎭')}\n\n"
        f"🎲 البوت اختار {writer.tag} يكتب التحدي!\n\n"
        f"✍ {tdesc.get(g.current_type, 'اكتب تحدي لـ')} *{p.display}*\n"
        f"⏳ عندك 90 ثانية… اكتب التحدي بالشات 👇",
        parse_mode="Markdown")
    if g._timeout_task and not g._timeout_task.done(): g._timeout_task.cancel()
    g._timeout_task = asyncio.create_task(challenge_write_timeout(bot, g))

async def challenge_write_timeout(bot, g):
    try:
        await asyncio.sleep(90)
        if g.phase == Phase.WAITING_CHALLENGE:
            writer = g.players.get(g.challenge_writer)
            wname = writer.tag if writer else "اللاعب"
            await ssend(bot, g.chat_id, f"⏰ {wname} ما كتب التحدي بالوقت!\nننتقل للاعب التالي…")
            if g.next_player(): await asyncio.sleep(2); await start_round(bot, g)
            else: await end_game(bot, g)
    except asyncio.CancelledError: pass

async def present_challenge(bot, g):
    p = g.current_player; g.phase = Phase.EXECUTING
    te = {ChallengeType.TRUTH: "🗣", ChallengeType.DARE: "🔥", ChallengeType.BET: "🎰"}
    author = g.players.get(g.challenge_author)
    aname = author.tag if author else "مجهول"
    await ssend(bot, g.chat_id,
        f"{te.get(g.current_type, '🎭')} *التحدي لـ {p.display}*\n\n"
        f"📝 {g.current_challenge}\n\n"
        f"✍ من: {aname}\n"
        f"⏳ عندك *{CHALLENGE_TIME} ثانية* لتنفّذ!\n\nنفّذ التحدي بالشات أو أرسل دليل 👇",
        parse_mode="Markdown")
    if g._timeout_task and not g._timeout_task.done(): g._timeout_task.cancel()
    g._timeout_task = asyncio.create_task(execution_timeout(bot, g))

async def execution_timeout(bot, g):
    try:
        await asyncio.sleep(CHALLENGE_TIME)
        if g.phase == Phase.EXECUTING: await start_judging(bot, g)
    except asyncio.CancelledError: pass

async def start_judging(bot, g):
    p = g.current_player; g.phase = Phase.JUDGING
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("☑ نفّذ", callback_data=f"jg_{g.chat_id}_yes"),
        InlineKeyboardButton("❌ ما نفّذ", callback_data=f"jg_{g.chat_id}_no"),
    ]])
    await ssend(bot, g.chat_id,
        f"⏰ *انتهى الوقت!*\n\nهل {p.tag} نفّذ التحدي؟\n👥 صوّتوا:",
        parse_mode="Markdown", reply_markup=kb)
    if g._timeout_task and not g._timeout_task.done(): g._timeout_task.cancel()
    g._timeout_task = asyncio.create_task(judging_timeout(bot, g))

async def judging_timeout(bot, g):
    try:
        await asyncio.sleep(30)
        if g.phase == Phase.JUDGING: await punish_player(bot, g)
    except asyncio.CancelledError: pass

async def punish_player(bot, g):
    p = g.current_player; g.phase = Phase.PUNISHING
    result = await execute_punishment(bot, g, p)
    update_stat(p.user_id, p.name, "punished")
    update_stat(p.user_id, p.name, "chickened")
    await ssend(bot, g.chat_id,
        f"⚖ *العقوبة!*\n\n{result}\n\n😂 المرة الجاي نفّذ يا {p.tag}!",
        parse_mode="Markdown")
    await asyncio.sleep(4)
    if g.next_player(): await start_round(bot, g)
    else: await end_game(bot, g)

async def complete_challenge(bot, g):
    p = g.current_player; p.completed += 1
    update_stat(p.user_id, p.name, "completed")
    await ssend(bot, g.chat_id, f"🎉 *برافو!*\n\n{p.tag} نفّذ التحدي! احترام 💪", parse_mode="Markdown")
    await asyncio.sleep(3)
    if g.next_player(): await start_round(bot, g)
    else: await end_game(bot, g)

async def end_game(bot, g):
    g.phase = Phase.GAME_OVER
    lines = []
    for p in g.players.values():
        if p.punishments == 0 and p.completed > 0: st = "💪 بطل"
        elif p.punishments > 0: st = f"😂 تعاقب {p.punishments} مرة"
        else: st = "😐 ما سوا شي"
        shame = f" — {p.shame_title}" if p.shame_title else ""
        lines.append(f"  {p.tag}{shame}: {st}")
        update_stat(p.user_id, p.name, "games")
    results = "\n".join(lines)
    mvp = max(g.players.values(), key=lambda x: (x.completed, -x.punishments), default=None)
    mvp_t = f"\n\n⭐ *الأجرأ:* {mvp.tag} — نفّذ {mvp.completed} تحدي!" if mvp and mvp.completed > 0 else ""
    mp = max(g.players.values(), key=lambda x: x.punishments, default=None)
    mp_t = f"\n🐔 *الأجبن:* {mp.tag} — تعاقب {mp.punishments} مرة!" if mp and mp.punishments > 0 else ""
    await ssend(bot, g.chat_id,
        f"🏁 *انتهت اللعبة!*\n\n📊 *النتائج:*\n{results}{mvp_t}{mp_t}\n\n"
        f"📊 /stats · 🏆 /leaderboard\n🔄 /start للعبة جديدة", parse_mode="Markdown")
    gm.remove(g.chat_id)

# ── Commands ──
async def cmd_start(update, context):
    if update.effective_chat.type == "private":
        if context.args and context.args[0].startswith("join_"):
            try:
                cid = int(context.args[0].split("_", 1)[1]); g = gm.get(cid)
                if not g or g.phase != Phase.LOBBY:
                    await update.message.reply_text("اللعبة مو متاحة."); return
                u = update.effective_user; name = u.first_name or u.username or f"U{u.id}"; uname = u.username or ""
                if u.id in g.players:
                    await update.message.reply_text("إنت منضم. انتظر البدء."); return
                if g.add_player(u.id, name, uname):
                    await update.message.reply_text(f"☑ انضممت يا *{name}*!\nانتظر بالمجموعة.", parse_mode="Markdown")
                    await update_lobby(context.bot, g)
                    await ssend(context.bot, cid, f"☑ {name} انضم!", parse_mode="Markdown")
                else: await update.message.reply_text("اللعبة ممتلئة.")
            except Exception as e:
                logger.error(f"Deep link: {e}")
                await update.message.reply_text("صار خطأ.")
            return
        await update.message.reply_text(
            "🎭 *لعبة التحديات* 🦩\n\n🔥 صراحة · جرأة · رهان\n💀 اللي ما بينفّذ بيتعاقب!\n\n"
            "📌 *كيف تلعب:*\n١. ضيفني على مجموعة واعملني أدمن\n٢. اكتب /start\n"
            "٣. اللاعبين ينضمون\n٤. يلا العب!\n\n🎮 /stats · /leaderboard", parse_mode="Markdown")
        return
    cid = update.effective_chat.id
    ex = gm.get(cid)
    if ex and ex.phase != Phase.GAME_OVER: await update.message.reply_text("في لعبة شغّالة!"); return
    if not await is_admin(context.bot, cid, update.effective_user.id):
        await update.message.reply_text("بس المشرفين بيقدروا يبدأوا لعبة."); return
    try:
        bm = await context.bot.get_chat_member(cid, context.bot.id)
        if bm.status != "administrator":
            await update.message.reply_text("⚠ لازم أكون *أدمن* عشان أقدر أكتم وأعاقب!\nاعملني أدمن وحاول مرة ثانية.", parse_mode="Markdown")
            return
    except: pass
    g = gm.create(cid)
    await send_lobby_photo(context.bot, g)
    g._lobby_task = asyncio.create_task(lobby_refresh_loop(context.bot, g))

async def cmd_endgame(update, context):
    if update.effective_chat.type == "private": return
    cid = update.effective_chat.id; g = gm.get(cid)
    if not g: await update.message.reply_text("ما في لعبة."); return
    if not await is_admin(context.bot, cid, update.effective_user.id):
        await update.message.reply_text("بس المشرفين."); return
    await end_game(context.bot, g)

async def cmd_stats(update, context):
    uid = str(update.effective_user.id); s = load_stats()
    if uid not in s: await update.message.reply_text("ما عندك إحصائيات بعد!"); return
    d = s[uid]
    await update.message.reply_text(
        f"📊 *إحصائياتك:*\n\n🎮 ألعاب: {d.get('games',0)}\n💪 تحديات منفّذة: {d.get('completed',0)}\n"
        f"😂 عقوبات: {d.get('punished',0)}\n🐔 مرات الجبن: {d.get('chickened',0)}", parse_mode="Markdown")

async def cmd_leaderboard(update, context):
    s = load_stats()
    if not s: await update.message.reply_text("ما في إحصائيات بعد!"); return
    sp = sorted(s.items(), key=lambda x: x[1].get("completed", 0), reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"{medals[i] if i<3 else f'#{i+1}'} *{d['name']}* — 💪 {d.get('completed',0)} · 😂 {d.get('punished',0)}"
             for i, (u, d) in enumerate(sp)]
    await update.message.reply_text(f"🏆 *المتصدرين:*\n\n" + "\n".join(lines), parse_mode="Markdown")

async def cmd_skip(update, context):
    if update.effective_chat.type == "private": return
    cid = update.effective_chat.id; g = gm.get(cid)
    if not g or g.phase in (Phase.LOBBY, Phase.GAME_OVER): return
    if not await is_admin(context.bot, cid, update.effective_user.id):
        await update.message.reply_text("بس المشرفين."); return
    if g._timeout_task and not g._timeout_task.done(): g._timeout_task.cancel()
    await ssend(context.bot, cid, "⏭ تم تخطي اللاعب.")
    if g.next_player(): await start_round(context.bot, g)
    else: await end_game(context.bot, g)

# ── Callbacks ──
async def join_cb(update, context):
    q = update.callback_query; d = q.data
    if d.startswith("join_"):
        cid = int(d.split("_")[1]); g = gm.get(cid)
        if not g or g.phase != Phase.LOBBY: await q.answer("مو متاحة.", show_alert=True); return
        u = q.from_user; name = u.first_name or u.username or f"U{u.id}"; uname = u.username or ""
        if u.id in g.players: await q.answer("إنت منضم!", show_alert=True); return
        if g.add_player(u.id, name, uname):
            test = await sdm(context.bot, u.id, "☑ انضممت! انتظر البدء.")
            if not test:
                if u.id in g.players: del g.players[u.id]
                bi = await context.bot.get_me()
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 افتح البوت", url=f"https://t.me/{bi.username}?start=join_{cid}")]])
                await q.answer("افتح البوت أولاً!", show_alert=True)
                try: await context.bot.send_message(chat_id=cid, text=f"*{name}* افتح البوت أولاً:", parse_mode="Markdown", reply_markup=kb)
                except: pass
                return
            await q.answer(f"انضممت يا {name}!", show_alert=True)
            await update_lobby(context.bot, g)
        else: await q.answer("ممتلئة!", show_alert=True)
    elif d.startswith("sg_"):
        cid = int(d.split("_")[1]); g = gm.get(cid)
        if not g or g.phase != Phase.LOBBY: await q.answer("مو متاحة.", show_alert=True); return
        if not await is_admin(context.bot, cid, q.from_user.id):
            await q.answer("بس المشرفين.", show_alert=True); return
        if len(g.players) < MIN_PLAYERS: await q.answer(f"بدنا {MIN_PLAYERS} لاعبين.", show_alert=True); return
        await q.answer("يلا نبدأ! 🔥")
        if g._lobby_task and not g._lobby_task.done(): g._lobby_task.cancel()
        try:
            if g.lobby_msg_id: await context.bot.delete_message(chat_id=cid, message_id=g.lobby_msg_id)
        except: pass
        g.start_game()
        pl = "\n".join(f"  {i}. {p.tag}" for i, p in enumerate(g.players.values(), 1))
        await ssend(context.bot, cid,
            f"🎭 *بدأت اللعبة!*\n\n👥 *اللاعبين:*\n{pl}\n\n🔄 ترتيب عشوائي\n"
            f"⏳ {CHALLENGE_TIME} ثانية لكل تحدي\n💀 اللي ما بينفّذ بيتعاقب!\n\nيلا نبدأ… 🔥", parse_mode="Markdown")
        for p in g.players.values(): update_stat(p.user_id, p.name, "games")
        await asyncio.sleep(3); await start_round(context.bot, g)
    elif d.startswith("cg_"):
        cid = int(d.split("_")[1]); g = gm.get(cid)
        if not g or g.phase != Phase.LOBBY: await q.answer("مو متاحة.", show_alert=True); return
        if not await is_admin(context.bot, cid, q.from_user.id):
            await q.answer("بس المشرفين.", show_alert=True); return
        lid = g.lobby_msg_id; gm.remove(cid); await q.answer("تم الإلغاء.", show_alert=True)
        try: await context.bot.delete_message(chat_id=cid, message_id=lid)
        except: pass
        await ssend(context.bot, cid, "❌ تم إلغاء اللعبة.\n\n/start للعبة جديدة")

async def challenge_type_cb(update, context):
    q = update.callback_query; d = q.data
    if not d.startswith("ct_"): return
    parts = d.split("_"); cid = int(parts[1]); choice = parts[2]
    g = gm.get(cid)
    if not g or g.phase != Phase.CHOOSING: await q.answer("مو وقتها.", show_alert=True); return
    p = g.current_player
    if q.from_user.id != p.user_id: await q.answer("مو دورك!", show_alert=True); return
    tmap = {"truth": ChallengeType.TRUTH, "dare": ChallengeType.DARE, "bet": ChallengeType.BET}
    g.current_type = tmap.get(choice, ChallengeType.DARE)
    tnames = {"truth": "🗣 صراحة", "dare": "🔥 جرأة", "bet": "🎰 رهان"}
    await q.answer(f"اخترت {tnames.get(choice, '🎭')}!")
    try: await q.edit_message_text(f"☑ {p.tag} اختار *{tnames.get(choice, '🎭')}*", parse_mode="Markdown")
    except: pass
    await asyncio.sleep(1); await ask_for_challenge(context.bot, g)

async def judging_cb(update, context):
    q = update.callback_query; d = q.data
    if not d.startswith("jg_"): return
    parts = d.split("_"); cid = int(parts[1]); verdict = parts[2]
    g = gm.get(cid)
    if not g or g.phase != Phase.JUDGING: await q.answer("انتهى.", show_alert=True); return
    p = g.current_player
    if q.from_user.id == p.user_id: await q.answer("ما بتقدر تصوّت لحالك!", show_alert=True); return
    if g._timeout_task and not g._timeout_task.done(): g._timeout_task.cancel()
    voter = g.players.get(q.from_user.id)
    vname = voter.tag if voter else q.from_user.first_name
    if verdict == "yes":
        try: await q.edit_message_text(f"☑ {vname} قال إنو {p.tag} نفّذ!", parse_mode="Markdown")
        except: pass
        await complete_challenge(context.bot, g)
    else:
        try: await q.edit_message_text(f"❌ {vname} قال إنو {p.tag} ما نفّذ!", parse_mode="Markdown")
        except: pass
        await punish_player(context.bot, g)
    await q.answer()

# ── Message Handler ──
async def on_group_message(update, context):
    if not update.message or not update.message.text: return
    if update.effective_chat.type == "private": return
    cid = update.effective_chat.id; g = gm.get(cid)
    if not g: return
    uid = update.effective_user.id
    if g.phase == Phase.WAITING_CHALLENGE:
        p = g.current_player
        if not p: return
        # Only the chosen writer can write the challenge
        if uid != g.challenge_writer: return
        if g._timeout_task and not g._timeout_task.done(): g._timeout_task.cancel()
        g.current_challenge = update.message.text; g.challenge_author = uid
        await asyncio.sleep(1); await present_challenge(context.bot, g)

# ── Router ──
async def cb_router(update, context):
    q = update.callback_query
    if not q or not q.data: return
    d = q.data
    if d.startswith("join_") or d.startswith("sg_") or d.startswith("cg_"): await join_cb(update, context)
    elif d.startswith("ct_"): await challenge_type_cb(update, context)
    elif d.startswith("jg_"): await judging_cb(update, context)
    else: await q.answer("غير معروف.", show_alert=True)

# ── Main ──
def main():
    app = Application.builder().token(TOKEN).build()
    async def post_init(application):
        from telegram import BotCommand
        await application.bot.set_my_commands([
            BotCommand("start", "بدء لعبة جديدة"), BotCommand("endgame", "إنهاء اللعبة"),
            BotCommand("skip", "تخطي اللاعب الحالي"), BotCommand("stats", "إحصائياتك"),
            BotCommand("leaderboard", "المتصدرين"),
        ])
        logger.info("Bot started!")
    app.post_init = post_init
    for cmd, fn in [("start", cmd_start), ("endgame", cmd_endgame), ("stats", cmd_stats),
                    ("leaderboard", cmd_leaderboard), ("skip", cmd_skip)]:
        app.add_handler(CommandHandler(cmd, fn))
    app.add_handler(CallbackQueryHandler(cb_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, on_group_message))
    logger.info("🎭 Challenge Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__": main()
