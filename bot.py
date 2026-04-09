#!/usr/bin/env python3
"""
🏰 Ghosts Palace - 𝒉𝒂𝒗𝒂𝒏𝒂 𝑪𝒉𝒂𝒕🦩
A fully-featured async Telegram bot for Ghosts Palace game.
Uses python-telegram-bot v20+ (async).
"""

import asyncio
import random
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)
from telegram.error import TelegramError, BadRequest

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════
# ENUMS & CONSTANTS
# ══════════════════════════════════════════════

class Phase(Enum):
    LOBBY = auto()
    NIGHT = auto()
    DAY = auto()
    VOTING = auto()
    GAME_OVER = auto()


class Team(Enum):
    VILLAGER = "villager"
    EVIL = "evil"
    DRACULA = "dracula"
    SOLO = "solo"  # صاحب البقالة


class RoleName(Enum):
    CRIMINAL = "criminal"
    GHOST_KILLER = "ghost_killer"
    MAID = "maid"
    CHEF = "chef"
    THIEF = "thief"
    POLICE = "police"
    DOORMAN = "doorman"
    NEIGHBOR = "neighbor"
    FOREST_GUARD = "forest_guard"
    MADMAN = "madman"
    GROCER = "grocer"
    BATMAN = "batman"
    WITCH = "witch"
    PRINCE = "prince"
    PAINTER = "painter"
    CHIEF = "chief"
    DRACULA = "dracula"
    DOG = "dog"


# ─────────────────────────────────────────────
# Role definitions
# ─────────────────────────────────────────────

@dataclass
class RoleDef:
    name: RoleName
    display: str
    emoji: str
    team: Team
    has_night_action: bool
    description: str
    priority: int  # lower = acts first at night


ROLE_DEFS: Dict[RoleName, RoleDef] = {
    RoleName.CRIMINAL: RoleDef(
        RoleName.CRIMINAL, "المجرم", "🔪", Team.EVIL, True,
        "يقتل لاعبًا كل ليلة", 1
    ),
    RoleName.GHOST_KILLER: RoleDef(
        RoleName.GHOST_KILLER, "الشبح القاتل", "👻", Team.EVIL, True,
        "يقتل لاعبًا + صعب اكتشافه", 2
    ),
    RoleName.MAID: RoleDef(
        RoleName.MAID, "الخادمة (العرّافة)", "🤵‍♀️", Team.VILLAGER, True,
        "تكشف دور لاعب", 10
    ),
    RoleName.CHEF: RoleDef(
        RoleName.CHEF, "الشيف", "🧑‍🍳", Team.EVIL, True,
        "يسمم لاعبًا (قتل غير مباشر – يموت الليلة التالية)", 3
    ),
    RoleName.THIEF: RoleDef(
        RoleName.THIEF, "اللص", "🥷", Team.VILLAGER, True,
        "يسرق دور لاعب (مرة واحدة)", 4
    ),
    RoleName.POLICE: RoleDef(
        RoleName.POLICE, "الشرطي", "👮‍♀️", Team.VILLAGER, True,
        "يعرف إن كان اللاعب قاتلًا أم لا", 11
    ),
    RoleName.DOORMAN: RoleDef(
        RoleName.DOORMAN, "البواب", "🧑‍✈️", Team.VILLAGER, True,
        "يوقف التصويت (هدنة) – مرة واحدة", 12
    ),
    RoleName.NEIGHBOR: RoleDef(
        RoleName.NEIGHBOR, "الجارة", "😘", Team.VILLAGER, True,
        "تزور لاعبًا وتعرف إن كان خرج من بيته", 13
    ),
    RoleName.FOREST_GUARD: RoleDef(
        RoleName.FOREST_GUARD, "حارس الغابة", "🧙‍♀️", Team.VILLAGER, True,
        "يحمي لاعبًا (لا يكرر نفس الشخص)", 5
    ),
    RoleName.MADMAN: RoleDef(
        RoleName.MADMAN, "مجنون الغابة", "🤡", Team.VILLAGER, False,
        "تصويته عشوائي", 99
    ),
    RoleName.GROCER: RoleDef(
        RoleName.GROCER, "صاحب البقالة المهجورة", "🧌", Team.SOLO, False,
        "إذا تم التصويت عليه يفوز وحده", 99
    ),
    RoleName.BATMAN: RoleDef(
        RoleName.BATMAN, "باتمان", "🦹‍♂️", Team.VILLAGER, True,
        "لديه طلقتان قتل", 6
    ),
    RoleName.WITCH: RoleDef(
        RoleName.WITCH, "الساحرة", "🧝‍♀️", Team.VILLAGER, True,
        "تربط لاعبين (يموتان معًا)", 7
    ),
    RoleName.PRINCE: RoleDef(
        RoleName.PRINCE, "الأمير", "🫅", Team.VILLAGER, False,
        "يحتاج تصويتين للإعدام", 99
    ),
    RoleName.PAINTER: RoleDef(
        RoleName.PAINTER, "الرسام", "👩‍🎨", Team.VILLAGER, False,
        "بدون قدرة خاصة", 99
    ),
    RoleName.CHIEF: RoleDef(
        RoleName.CHIEF, "مختار الغابة", "💂‍♂️", Team.VILLAGER, False,
        "بدون قدرة خاصة", 99
    ),
    RoleName.DRACULA: RoleDef(
        RoleName.DRACULA, "دراكولا", "🧛", Team.DRACULA, True,
        "يحول لاعبًا إلى مصاص دماء", 8
    ),
    RoleName.DOG: RoleDef(
        RoleName.DOG, "الكلب", "🐶", Team.VILLAGER, False,
        "إذا تم استهدافه بالقتل يتحول لذئب (شرير)", 99
    ),
}

# Death messages per role
DEATH_MESSAGES: Dict[RoleName, str] = {
    RoleName.MAID: (
        "🩸 لقد تم قتلك هذه الليلة…\n"
        "🌑 الظلام كان قاتمًا، ولم يكن هناك مهرب.\n"
        "💀 حكايتك ستبقى في ذاكرة القرية.\n"
        "🤵‍♀️ كنت الخادمة (العرّافة)…\n"
        "🔍 امتلكت الحقيقة…\n"
        "😔 لكن لم تستطع إنقاذ نفسك.\n"
        "👁️ هل استخدمت معلوماتك بشكل كافٍ؟"
    ),
    RoleName.CHEF: (
        "🧑‍🍳 كنت الشيف…\n"
        "☠️ السم كان سلاحك.\n"
        "😈 لكنك لم تنجُ حتى النهاية."
    ),
    RoleName.THIEF: "🥷 كنت اللص..\n😔 لم تستطع النجاة",
    RoleName.POLICE: "👮‍♀️ كنت الشرطي…\n🔎 بحثت عن الحقيقة…",
    RoleName.DOORMAN: "🧑‍✈️ كنت البواب…\n🛑 حاولت إيقاف الفوضى…",
    RoleName.NEIGHBOR: "😘 كنت الجارة…\n🏠 اقتربت من الجميع…",
    RoleName.FOREST_GUARD: "🧙‍♀️ كنت حارس الغابة…\n🛡️ حميت الآخرين…",
    RoleName.MADMAN: "🤡 كنت مجنون الغابة…\n🎲 نشرت الفوضى…",
    RoleName.GROCER: "🧌 كنت صاحب البقالة المهجورة…",
    RoleName.BATMAN: "🦹‍♂️ كنت باتمان…",
    RoleName.WITCH: "🧝‍♀️ كنت الساحرة…",
    RoleName.DOG: "🐶 كنت الكلب…",
    RoleName.PRINCE: "🫅 كنت الأمير…",
    RoleName.PAINTER: "👩‍🎨 كنت الرسام…",
    RoleName.CHIEF: "💂‍♂️ كنت مختار الغابة…",
    RoleName.DRACULA: "🧛 كنت دراكولا…",
    RoleName.CRIMINAL: "🔪 كنت المجرم…\n😈 القتل كان حرفتك…",
    RoleName.GHOST_KILLER: "👻 كنت الشبح القاتل…\n🌑 لكن حتى الأشباح تموت…",
}


# ══════════════════════════════════════════════
# PLAYER CLASS
# ══════════════════════════════════════════════

@dataclass
class Player:
    user_id: int
    name: str
    role: Optional[RoleName] = None
    alive: bool = True
    # Special state
    poisoned: bool = False  # Chef poison (dies next night)
    protected: bool = False  # Forest guard protection
    prince_lives: int = 1  # extra life for prince
    batman_bullets: int = 2
    doorman_used: bool = False
    thief_used: bool = False
    witch_linked_to: Optional[int] = None  # user_id of linked player
    is_vampire: bool = False  # converted by Dracula
    dog_transformed: bool = False  # became wolf
    visited_target: Optional[int] = None  # Neighbor visit

    @property
    def role_def(self) -> Optional[RoleDef]:
        if self.role:
            return ROLE_DEFS[self.role]
        return None

    @property
    def team(self) -> Optional[Team]:
        if self.is_vampire:
            return Team.DRACULA
        if self.dog_transformed:
            return Team.EVIL
        if self.role:
            return ROLE_DEFS[self.role].team
        return None

    @property
    def display_role(self) -> str:
        if self.role:
            rd = ROLE_DEFS[self.role]
            extra = ""
            if self.is_vampire:
                extra = " 🧛(مصاص دماء)"
            if self.dog_transformed:
                extra = " 🐺(ذئب)"
            return f"{rd.emoji} {rd.display}{extra}"
        return "❓"


# ══════════════════════════════════════════════
# GAME CLASS
# ══════════════════════════════════════════════

class Game:
    """Manages a single game instance in a chat group."""

    MIN_PLAYERS = 4
    MAX_PLAYERS = 18
    NIGHT_DURATION = 60  # seconds
    VOTE_DURATION = 60

    def __init__(self, chat_id: int):
        self.chat_id: int = chat_id
        self.phase: Phase = Phase.LOBBY
        self.players: Dict[int, Player] = {}
        self.round_num: int = 0

        # Night action tracking
        self.night_actions: Dict[str, any] = {}
        self.night_kills: List[int] = []
        self.guard_last_protected: Optional[int] = None
        self.truce_active: bool = False  # doorman truce

        # Voting
        self.votes: Dict[int, int] = {}  # voter_id -> target_id
        self.vote_message_id: Optional[int] = None
        self.lobby_message_id: Optional[int] = None

        # Witch links
        self.witch_links: Dict[int, int] = {}  # player_a -> player_b

        # Tasks
        self._phase_task: Optional[asyncio.Task] = None

    def add_player(self, user_id: int, name: str) -> bool:
        if user_id in self.players or self.phase != Phase.LOBBY:
            return False
        if len(self.players) >= self.MAX_PLAYERS:
            return False
        self.players[user_id] = Player(user_id=user_id, name=name)
        return True

    @property
    def alive_players(self) -> List[Player]:
        return [p for p in self.players.values() if p.alive]

    @property
    def alive_evil(self) -> List[Player]:
        return [p for p in self.alive_players if p.team in (Team.EVIL, Team.DRACULA)]

    @property
    def alive_villagers(self) -> List[Player]:
        return [p for p in self.alive_players if p.team == Team.VILLAGER]

    def get_player(self, user_id: int) -> Optional[Player]:
        return self.players.get(user_id)

    # ── Role assignment ──
    def assign_roles(self):
        player_count = len(self.players)
        role_pool: List[RoleName] = []

        # Core roles (4+ players)
        role_pool.append(RoleName.CRIMINAL)
        role_pool.append(RoleName.MAID)

        if player_count >= 5:
            role_pool.append(RoleName.POLICE)
        if player_count >= 6:
            role_pool.append(RoleName.FOREST_GUARD)
        if player_count >= 7:
            role_pool.append(RoleName.CHEF)
        if player_count >= 8:
            role_pool.append(RoleName.DOORMAN)
            role_pool.append(RoleName.NEIGHBOR)
        if player_count >= 9:
            role_pool.append(RoleName.GHOST_KILLER)
        if player_count >= 10:
            role_pool.append(RoleName.THIEF)
            role_pool.append(RoleName.BATMAN)
        if player_count >= 11:
            role_pool.append(RoleName.WITCH)
            role_pool.append(RoleName.PRINCE)
        if player_count >= 12:
            role_pool.append(RoleName.DRACULA)
            role_pool.append(RoleName.DOG)
        if player_count >= 13:
            role_pool.append(RoleName.GROCER)
        if player_count >= 14:
            role_pool.append(RoleName.MADMAN)

        # Fill remaining with basic villager roles
        fillers = [RoleName.PAINTER, RoleName.CHIEF]
        while len(role_pool) < player_count:
            role_pool.append(random.choice(fillers))

        # Trim if too many
        role_pool = role_pool[:player_count]
        random.shuffle(role_pool)

        for player, role in zip(self.players.values(), role_pool):
            player.role = role
            if role == RoleName.PRINCE:
                player.prince_lives = 1
            if role == RoleName.BATMAN:
                player.batman_bullets = 2

    # ── Win condition checks ──
    def check_win(self) -> Optional[str]:
        alive = self.alive_players
        if not alive:
            return "evil"

        evil_count = len([p for p in alive if p.team in (Team.EVIL,)])
        dracula_count = len([p for p in alive if p.team == Team.DRACULA])
        village_count = len([p for p in alive if p.team == Team.VILLAGER])
        solo_count = len([p for p in alive if p.team == Team.SOLO])

        total_non_evil = village_count + solo_count

        # Dracula wins: all alive are vampires/dracula team
        if dracula_count > 0 and evil_count == 0 and village_count == 0 and solo_count == 0:
            return "dracula"

        # Evil wins: evil >= villagers (and no dracula)
        if evil_count >= total_non_evil and dracula_count == 0:
            return "evil"

        # Evil + dracula combined dominate
        if (evil_count + dracula_count) >= total_non_evil and (evil_count + dracula_count) > 0:
            if dracula_count > evil_count:
                return "dracula"
            if evil_count > 0:
                return "evil"

        # Village wins: no evil and no dracula
        if evil_count == 0 and dracula_count == 0:
            return "village"

        return None


# ══════════════════════════════════════════════
# GAME MANAGER
# ══════════════════════════════════════════════

class GameManager:
    """Manages multiple game instances across different chats."""

    def __init__(self):
        self.games: Dict[int, Game] = {}

    def get_game(self, chat_id: int) -> Optional[Game]:
        return self.games.get(chat_id)

    def create_game(self, chat_id: int) -> Game:
        game = Game(chat_id)
        self.games[chat_id] = game
        return game

    def remove_game(self, chat_id: int):
        if chat_id in self.games:
            game = self.games[chat_id]
            if game._phase_task and not game._phase_task.done():
                game._phase_task.cancel()
            del self.games[chat_id]


# ══════════════════════════════════════════════
# BOT HANDLERS
# ══════════════════════════════════════════════

gm = GameManager()


# ── Helper: safe send ──
async def safe_send(bot: Bot, chat_id: int, text: str, **kwargs):
    try:
        return await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except TelegramError as e:
        logger.error(f"Failed to send to {chat_id}: {e}")
        return None


async def safe_send_dm(bot: Bot, user_id: int, text: str, **kwargs):
    try:
        return await bot.send_message(chat_id=user_id, text=text, **kwargs)
    except TelegramError as e:
        logger.warning(f"Cannot DM user {user_id}: {e}")
        return None


# ─────────────────────────────────────────────
# GIF URL for game start animation
# ─────────────────────────────────────────────
GAME_START_GIF = "https://media.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif"
NIGHT_GIF = "https://media.giphy.com/media/3o7TKwmnDgQb5jemjK/giphy.gif"
VOTE_GIF = "https://media.giphy.com/media/26BRBKqUiq586bRVm/giphy.gif"
DEATH_CRIMINAL_GIF = "https://media.giphy.com/media/3o72F8t9TDi2xVnxOE/giphy.gif"
DEATH_GHOST_GIF = "https://media.giphy.com/media/l2JejfEHGGBRhifi8/giphy.gif"
DEATH_GENERIC_GIF = "https://media.giphy.com/media/xT0xeJpnrWC3XWblEk/giphy.gif"
DEATH_POISON_GIF = "https://media.giphy.com/media/3oEjHGr1Fhz0kyv8Ig/giphy.gif"
DEATH_BATMAN_GIF = "https://media.giphy.com/media/l3q2XhfQ8oCkm1Ts4/giphy.gif"


def build_lobby_text(game: Game) -> str:
    """Build the lobby message text with current player list."""
    player_list = ""
    for i, p in enumerate(game.players.values(), 1):
        player_list += f"  {i}. {p.name}\n"
    if not player_list:
        player_list = "  ⏳ لا يوجد لاعبين بعد...\n"

    count = len(game.players)
    status = "🟢 يمكن بدء اللعبة!" if count >= Game.MIN_PLAYERS else f"⏳ يحتاج {Game.MIN_PLAYERS - count} لاعبين إضافيين"

    return (
        "🏰 *Ghosts Palace - 𝒉𝒂𝒗𝒂𝒏𝒂 𝑪𝒉𝒂𝒕🦩*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎭 *لعبة جديدة بدأت!*\n"
        "👻 من سيبقى حيًا حتى النهاية؟\n\n"
        f"👥 *اللاعبون ({count}/{Game.MAX_PLAYERS}):*\n"
        f"{player_list}\n"
        f"{status}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )


def build_lobby_keyboard(game: Game) -> InlineKeyboardMarkup:
    """Build the lobby inline keyboard."""
    count = len(game.players)
    buttons = [[InlineKeyboardButton("🎮 انضم للعبة!", callback_data=f"join_{game.chat_id}")]]
    if count >= Game.MIN_PLAYERS:
        buttons.append([InlineKeyboardButton("🚀 ابدأ اللعبة!", callback_data=f"startgame_{game.chat_id}")])
    buttons.append([InlineKeyboardButton("❌ إلغاء اللعبة", callback_data=f"cancelgame_{game.chat_id}")])
    return InlineKeyboardMarkup(buttons)


# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "🏰 مرحبًا بك في Ghosts Palace - 𝒉𝒂𝒗𝒂𝒏𝒂 𝑪𝒉𝒂𝒕🦩!\n\n"
            "أضفني إلى مجموعة واستخدم الأوامر التالية:\n"
            "/start - بدء جلسة جديدة\n"
            "/join - الانضمام للعبة\n"
            "/startgame - بدء اللعبة\n\n"
            "⚠️ يجب أن تبدأ محادثة خاصة معي أولاً حتى أستطيع إرسال دورك!"
        )
        return

    chat_id = update.effective_chat.id
    existing = gm.get_game(chat_id)
    if existing and existing.phase != Phase.GAME_OVER:
        await update.message.reply_text("⚠️ يوجد لعبة قائمة بالفعل في هذه المجموعة!")
        return

    game = gm.create_game(chat_id)

    # Send GIF animation first
    try:
        await context.bot.send_animation(
            chat_id=chat_id,
            animation=GAME_START_GIF,
            caption="👻 *الأشباح تستيقظ...*\n🏰 *القصر يفتح أبوابه...*",
            parse_mode="Markdown",
        )
    except TelegramError as e:
        logger.warning(f"Could not send GIF: {e}")

    await asyncio.sleep(1)

    # Send lobby message with join button
    lobby_msg = await safe_send(
        context.bot, chat_id,
        build_lobby_text(game),
        parse_mode="Markdown",
        reply_markup=build_lobby_keyboard(game),
    )
    if lobby_msg:
        game.lobby_message_id = lobby_msg.message_id


# ─────────────────────────────────────────────
# /join (text command fallback)
# ─────────────────────────────────────────────
async def cmd_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("⚠️ هذا الأمر يعمل في المجموعات فقط!")
        return

    chat_id = update.effective_chat.id
    game = gm.get_game(chat_id)
    if not game or game.phase != Phase.LOBBY:
        await update.message.reply_text("⚠️ لا توجد لعبة مفتوحة. استخدم /start أولاً!")
        return

    user = update.effective_user
    name = user.first_name or user.username or f"User{user.id}"

    if game.add_player(user.id, name):
        # Update the lobby message with new player list
        await update_lobby_message(context.bot, game)
        await update.message.reply_text(f"✅ {name} انضم للعبة!")
    else:
        await update.message.reply_text("⚠️ أنت منضم بالفعل أو اللعبة ممتلئة!")


# ─────────────────────────────────────────────
# Join button callback
# ─────────────────────────────────────────────
async def join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("join_"):
        chat_id = int(data.split("_")[1])
        game = gm.get_game(chat_id)
        if not game or game.phase != Phase.LOBBY:
            await query.answer("⚠️ اللعبة غير متاحة!", show_alert=True)
            return

        user = query.from_user
        name = user.first_name or user.username or f"User{user.id}"

        if user.id in game.players:
            await query.answer("⚠️ أنت منضم بالفعل!", show_alert=True)
            return

        if game.add_player(user.id, name):
            await query.answer(f"✅ تم انضمامك يا {name}!", show_alert=True)
            await update_lobby_message(context.bot, game)
        else:
            await query.answer("⚠️ اللعبة ممتلئة!", show_alert=True)

    elif data.startswith("startgame_"):
        chat_id = int(data.split("_")[1])
        game = gm.get_game(chat_id)
        if not game or game.phase != Phase.LOBBY:
            await query.answer("⚠️ اللعبة غير متاحة!", show_alert=True)
            return

        if len(game.players) < Game.MIN_PLAYERS:
            await query.answer(f"⚠️ يحتاج {Game.MIN_PLAYERS} لاعبين على الأقل!", show_alert=True)
            return

        await query.answer("🚀 جاري بدء اللعبة...")

        # Remove lobby buttons
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=game.lobby_message_id,
                reply_markup=None,
            )
        except TelegramError:
            pass

        await start_game_logic(context.bot, game, chat_id, context)

    elif data.startswith("cancelgame_"):
        chat_id = int(data.split("_")[1])
        game = gm.get_game(chat_id)
        if game and game.phase == Phase.LOBBY:
            gm.remove_game(chat_id)
            await query.answer("❌ تم إلغاء اللعبة!", show_alert=True)
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=game.lobby_message_id,
                    text="❌ *تم إلغاء اللعبة!*\n\nاستخدم /start لبدء لعبة جديدة.",
                    parse_mode="Markdown",
                )
            except TelegramError:
                pass
        else:
            await query.answer("⚠️ لا توجد لعبة للإلغاء!", show_alert=True)


async def update_lobby_message(bot: Bot, game: Game):
    """Update the lobby message with current player list."""
    if not game.lobby_message_id:
        return
    try:
        await bot.edit_message_text(
            chat_id=game.chat_id,
            message_id=game.lobby_message_id,
            text=build_lobby_text(game),
            parse_mode="Markdown",
            reply_markup=build_lobby_keyboard(game),
        )
    except TelegramError as e:
        logger.warning(f"Could not update lobby message: {e}")


# ─────────────────────────────────────────────
# /startgame (text command fallback)
# ─────────────────────────────────────────────
async def cmd_startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    chat_id = update.effective_chat.id
    game = gm.get_game(chat_id)
    if not game or game.phase != Phase.LOBBY:
        await update.message.reply_text("⚠️ لا توجد لعبة في مرحلة الانتظار!")
        return

    if len(game.players) < Game.MIN_PLAYERS:
        await update.message.reply_text(
            f"⚠️ لا يوجد عدد كافٍ! يحتاج {Game.MIN_PLAYERS} لاعبين على الأقل.\n"
            f"👥 الحالي: {len(game.players)}"
        )
        return

    # Remove lobby buttons
    try:
        if game.lobby_message_id:
            await context.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=game.lobby_message_id,
                reply_markup=None,
            )
    except TelegramError:
        pass

    await start_game_logic(context.bot, game, chat_id, context)


async def start_game_logic(bot: Bot, game: Game, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Shared game start logic for both command and button."""
    # Assign roles
    game.assign_roles()

    # Send roles via DM
    player_list_text = "🎭 *اللاعبون:*\n"
    dm_failures = []
    for p in game.players.values():
        player_list_text += f"• {p.name}\n"
        role_def = p.role_def
        dm_text = (
            f"🎭 *دورك في هذه اللعبة:*\n\n"
            f"{role_def.emoji} *{role_def.display}*\n"
            f"📝 {role_def.description}\n"
            f"👥 فريقك: {'الأبرياء 🛡️' if role_def.team == Team.VILLAGER else 'الأشرار 😈' if role_def.team == Team.EVIL else 'دراكولا 🧛' if role_def.team == Team.DRACULA else 'وحيد 🧌'}\n\n"
            f"⚠️ لا تكشف دورك لأحد!"
        )
        result = await safe_send_dm(bot, p.user_id, dm_text, parse_mode="Markdown")
        if not result:
            dm_failures.append(p.name)

    await safe_send(
        bot, chat_id,
        f"🎲 *تم توزيع الأدوار!*\n\n{player_list_text}\n"
        f"📩 تحقق من الرسائل الخاصة لمعرفة دورك!\n"
        f"👥 عدد اللاعبين: {len(game.players)}",
        parse_mode="Markdown",
    )

    if dm_failures:
        await safe_send(
            bot, chat_id,
            "⚠️ لم أستطع إرسال الدور لهؤلاء اللاعبين (يجب أن يبدأوا محادثة خاصة معي أولاً):\n"
            + "\n".join(f"• {n}" for n in dm_failures)
        )

    # Notify evil players about each other
    evil_players = [p for p in game.players.values() if p.role_def.team == Team.EVIL]
    if len(evil_players) > 1:
        for ep in evil_players:
            others = [f"{o.name} ({o.role_def.emoji} {o.role_def.display})" for o in evil_players if o.user_id != ep.user_id]
            await safe_send_dm(
                bot, ep.user_id,
                f"😈 *فريق الأشرار:*\n" + "\n".join(f"• {o}" for o in others),
                parse_mode="Markdown"
            )

    await asyncio.sleep(3)

    # Start night phase
    game._phase_task = asyncio.create_task(run_night(bot, game))


# ══════════════════════════════════════════════
# NIGHT PHASE
# ══════════════════════════════════════════════

async def run_night(bot: Bot, game: Game):
    try:
        game.phase = Phase.NIGHT
        game.round_num += 1
        game.night_actions = {}
        game.night_kills = []
        game.truce_active = False

        # Reset protection
        for p in game.alive_players:
            p.protected = False
            p.visited_target = None

        await safe_send(
            bot, game.chat_id,
            f"🌙 *الليلة {game.round_num}*\n\n"
            "🌙 حلّ الليل…\n"
            "🌲 الرياح تعصف بين الأشجار…\n"
            "👁️ هناك من يراقب… وهناك من يتحرك في الظلام.\n"
            "🔒 الأبواب أُغلقت… والأنفاس محبوسة.\n"
            "🎭 أصحاب الأدوار الليلية… الوقت لكم الآن.\n"
            "⏳ لكن تذكروا… ليس كل من خرج في الليل سيعود.",
            parse_mode="Markdown",
        )

        # Send night action buttons to each player with a night action
        for player in game.alive_players:
            await send_night_action(bot, game, player)

        # Wait for night actions
        await asyncio.sleep(Game.NIGHT_DURATION // 2)

        await safe_send(
            bot, game.chat_id,
            "⏳ الوقت يمر…\n"
            "⚠️ إذا لم تستخدم قدرتك الآن، قد تضيع فرصتك!\n"
            "🌙 الظلام لا ينتظر أحد…"
        )

        await asyncio.sleep(Game.NIGHT_DURATION // 2)

        # Resolve night
        await resolve_night(bot, game)

    except asyncio.CancelledError:
        logger.info(f"Night phase cancelled for chat {game.chat_id}")
    except Exception as e:
        logger.error(f"Error in night phase: {e}", exc_info=True)
        await safe_send(bot, game.chat_id, f"⚠️ حدث خطأ: {e}")


async def send_night_action(bot: Bot, game: Game, player: Player):
    """Send night-action inline buttons to a player via DM."""
    role = player.role
    if not role:
        return

    rd = ROLE_DEFS[role]
    targets = [p for p in game.alive_players if p.user_id != player.user_id]

    if not targets:
        return

    # Determine if this player has a night action
    if role == RoleName.CRIMINAL:
        text = "🔪 اختر لاعبًا لقتله هذه الليلة:"
        callback_prefix = "night_criminal"
    elif role == RoleName.GHOST_KILLER:
        text = "👻 اختر لاعبًا لقتله (كشبح):"
        callback_prefix = "night_ghost"
    elif role == RoleName.MAID:
        text = "🤵‍♀️ اختر لاعبًا لكشف دوره:"
        callback_prefix = "night_maid"
    elif role == RoleName.CHEF:
        text = "🧑‍🍳 اختر لاعبًا لتسميمه (سيموت الليلة القادمة):"
        callback_prefix = "night_chef"
    elif role == RoleName.THIEF:
        if player.thief_used:
            return
        text = "🥷 اختر لاعبًا لسرقة دوره (مرة واحدة فقط!):"
        callback_prefix = "night_thief"
    elif role == RoleName.POLICE:
        text = "👮‍♀️ اختر لاعبًا للتحقيق معه:"
        callback_prefix = "night_police"
    elif role == RoleName.DOORMAN:
        if player.doorman_used:
            return
        text = "🧑‍✈️ هل تريد إعلان هدنة (إيقاف التصويت) هذه الجولة?"
        buttons = [[InlineKeyboardButton("✅ نعم - هدنة!", callback_data=f"night_doorman_{game.chat_id}_yes")],
                    [InlineKeyboardButton("❌ لا", callback_data=f"night_doorman_{game.chat_id}_no")]]
        await safe_send_dm(bot, player.user_id, text, reply_markup=InlineKeyboardMarkup(buttons))
        return
    elif role == RoleName.NEIGHBOR:
        text = "😘 اختر لاعبًا لزيارته (لمعرفة إن كان خرج من بيته):"
        callback_prefix = "night_neighbor"
    elif role == RoleName.FOREST_GUARD:
        guard_targets = [p for p in targets if p.user_id != game.guard_last_protected]
        if not guard_targets:
            return
        targets = guard_targets
        text = "🧙‍♀️ اختر لاعبًا لحمايته هذه الليلة:"
        callback_prefix = "night_guard"
    elif role == RoleName.BATMAN:
        if player.batman_bullets <= 0:
            return
        text = f"🦹‍♂️ اختر لاعبًا لقتله (متبقي: {player.batman_bullets} طلقة):"
        callback_prefix = "night_batman"
    elif role == RoleName.WITCH:
        text = "🧝‍♀️ اختر لاعبَين لربطهما (الأول):"
        callback_prefix = "night_witch1"
    elif role == RoleName.DRACULA:
        non_vampire_targets = [p for p in targets if not p.is_vampire and p.role != RoleName.DRACULA]
        if not non_vampire_targets:
            return
        targets = non_vampire_targets
        text = "🧛 اختر لاعبًا لتحويله إلى مصاص دماء:"
        callback_prefix = "night_dracula"
    else:
        return  # No night action

    buttons = []
    row = []
    for i, t in enumerate(targets):
        row.append(InlineKeyboardButton(
            t.name, callback_data=f"{callback_prefix}_{game.chat_id}_{t.user_id}"
        ))
        if len(row) == 2 or i == len(targets) - 1:
            buttons.append(row)
            row = []

    # Add skip button
    buttons.append([InlineKeyboardButton("⏭️ تخطي", callback_data=f"{callback_prefix}_{game.chat_id}_skip")])

    await safe_send_dm(bot, player.user_id, text, reply_markup=InlineKeyboardMarkup(buttons))


# ── Night action callback handler ──
async def night_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    parts = data.split("_")
    # Format: night_<role>_<chat_id>_<target_id or skip or yes/no>
    # Some have extra parts like night_witch1

    try:
        if data.startswith("night_witch1_"):
            action_type = "night_witch1"
            rest = data[len("night_witch1_"):]
        elif data.startswith("night_witch2_"):
            action_type = "night_witch2"
            rest = data[len("night_witch2_"):]
        elif data.startswith("night_criminal_"):
            action_type = "night_criminal"
            rest = data[len("night_criminal_"):]
        elif data.startswith("night_ghost_"):
            action_type = "night_ghost"
            rest = data[len("night_ghost_"):]
        elif data.startswith("night_maid_"):
            action_type = "night_maid"
            rest = data[len("night_maid_"):]
        elif data.startswith("night_chef_"):
            action_type = "night_chef"
            rest = data[len("night_chef_"):]
        elif data.startswith("night_thief_"):
            action_type = "night_thief"
            rest = data[len("night_thief_"):]
        elif data.startswith("night_police_"):
            action_type = "night_police"
            rest = data[len("night_police_"):]
        elif data.startswith("night_doorman_"):
            action_type = "night_doorman"
            rest = data[len("night_doorman_"):]
        elif data.startswith("night_neighbor_"):
            action_type = "night_neighbor"
            rest = data[len("night_neighbor_"):]
        elif data.startswith("night_guard_"):
            action_type = "night_guard"
            rest = data[len("night_guard_"):]
        elif data.startswith("night_batman_"):
            action_type = "night_batman"
            rest = data[len("night_batman_"):]
        elif data.startswith("night_dracula_"):
            action_type = "night_dracula"
            rest = data[len("night_dracula_"):]
        else:
            return

        # Parse chat_id and target
        rest_parts = rest.split("_")
        chat_id = int(rest_parts[0])
        target_value = rest_parts[1]  # user_id or "skip" or "yes"/"no"

        game = gm.get_game(chat_id)
        if not game or game.phase != Phase.NIGHT:
            await query.edit_message_text("⚠️ هذا الإجراء لم يعد صالحًا.")
            return

        user_id = query.from_user.id
        player = game.get_player(user_id)
        if not player or not player.alive:
            await query.edit_message_text("⚠️ أنت لست في هذه اللعبة أو ميت.")
            return

        # Check if already acted
        action_key = f"{action_type}_{user_id}"
        if action_key in game.night_actions and action_type != "night_witch1":
            await query.edit_message_text("✅ لقد اتخذت قرارك بالفعل!")
            return

        if target_value == "skip":
            game.night_actions[action_key] = "skip"
            await query.edit_message_text("⏭️ تم التخطي.")
            return

        # ── Process each action type ──
        if action_type == "night_criminal":
            target_id = int(target_value)
            game.night_actions[action_key] = target_id
            target = game.get_player(target_id)
            await query.edit_message_text(f"🔪 سيتم محاولة قتل {target.name if target else '?'} هذه الليلة.")

        elif action_type == "night_ghost":
            target_id = int(target_value)
            game.night_actions[action_key] = target_id
            target = game.get_player(target_id)
            await query.edit_message_text(f"👻 سيتم محاولة قتل {target.name if target else '?'} بصمت.")

        elif action_type == "night_maid":
            target_id = int(target_value)
            game.night_actions[action_key] = target_id
            target = game.get_player(target_id)
            if target:
                # Ghost killer appears as villager to maid
                if target.role == RoleName.GHOST_KILLER:
                    fake_role = random.choice([RoleName.PAINTER, RoleName.CHIEF, RoleName.NEIGHBOR])
                    rd = ROLE_DEFS[fake_role]
                    await query.edit_message_text(f"🔍 دور {target.name}: {rd.emoji} {rd.display}")
                else:
                    await query.edit_message_text(f"🔍 دور {target.name}: {target.display_role}")
            else:
                await query.edit_message_text("⚠️ اللاعب غير موجود.")

        elif action_type == "night_chef":
            target_id = int(target_value)
            game.night_actions[action_key] = target_id
            target = game.get_player(target_id)
            await query.edit_message_text(f"☠️ تم تسميم {target.name if target else '?'}. سيموت الليلة القادمة.")

        elif action_type == "night_thief":
            target_id = int(target_value)
            game.night_actions[action_key] = target_id
            target = game.get_player(target_id)
            player.thief_used = True
            if target:
                # Steal their role
                stolen_role = target.role
                target.role = RoleName.PAINTER  # becomes basic villager
                player.role = stolen_role
                await query.edit_message_text(
                    f"🥷 سرقت دور {target.name}!\n"
                    f"🎭 دورك الجديد: {player.display_role}"
                )
            else:
                await query.edit_message_text("⚠️ فشلت السرقة.")

        elif action_type == "night_police":
            target_id = int(target_value)
            game.night_actions[action_key] = target_id
            target = game.get_player(target_id)
            if target:
                is_killer = target.team in (Team.EVIL, Team.DRACULA)
                # Ghost killer fools the police too
                if target.role == RoleName.GHOST_KILLER:
                    is_killer = False
                result = "🔴 قاتل!" if is_killer else "🟢 بريء"
                await query.edit_message_text(f"🔎 نتيجة التحقيق مع {target.name}: {result}")
            else:
                await query.edit_message_text("⚠️ اللاعب غير موجود.")

        elif action_type == "night_doorman":
            if target_value == "yes":
                game.night_actions[action_key] = "truce"
                game.truce_active = True
                player.doorman_used = True
                await query.edit_message_text("🛑 تم تفعيل الهدنة! لن يكون هناك تصويت هذه الجولة.")
            else:
                await query.edit_message_text("تم التجاهل.")

        elif action_type == "night_neighbor":
            target_id = int(target_value)
            game.night_actions[action_key] = target_id
            player.visited_target = target_id
            target = game.get_player(target_id)
            # Will resolve after night: if target had a night action and used it, they "left home"
            await query.edit_message_text(f"😘 ستزورين {target.name if target else '?'} هذه الليلة.")

        elif action_type == "night_guard":
            target_id = int(target_value)
            game.night_actions[action_key] = target_id
            target = game.get_player(target_id)
            if target:
                target.protected = True
                game.guard_last_protected = target_id
                await query.edit_message_text(f"🛡️ ستحمي {target.name} هذه الليلة.")
            else:
                await query.edit_message_text("⚠️ اللاعب غير موجود.")

        elif action_type == "night_batman":
            target_id = int(target_value)
            game.night_actions[action_key] = target_id
            player.batman_bullets -= 1
            target = game.get_player(target_id)
            await query.edit_message_text(
                f"🦹‍♂️ أطلقت النار على {target.name if target else '?'}!\n"
                f"🔫 متبقي: {player.batman_bullets} طلقة"
            )

        elif action_type == "night_witch1":
            target_id = int(target_value)
            # Store first target, ask for second
            game.night_actions[f"witch1_{user_id}"] = target_id
            target = game.get_player(target_id)

            # Show second target selection
            targets2 = [p for p in game.alive_players if p.user_id != user_id and p.user_id != target_id]
            if targets2:
                buttons = []
                row = []
                for i, t in enumerate(targets2):
                    row.append(InlineKeyboardButton(
                        t.name, callback_data=f"night_witch2_{chat_id}_{t.user_id}"
                    ))
                    if len(row) == 2 or i == len(targets2) - 1:
                        buttons.append(row)
                        row = []
                buttons.append([InlineKeyboardButton("⏭️ تخطي", callback_data=f"night_witch2_{chat_id}_skip")])
                await query.edit_message_text(
                    f"🧝‍♀️ تم اختيار {target.name if target else '?'} كأول لاعب.\n"
                    f"اختر اللاعب الثاني للربط:",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            else:
                await query.edit_message_text("⚠️ لا يوجد لاعب ثانٍ للربط.")

        elif action_type == "night_witch2":
            target_id = int(target_value)
            first_target = game.night_actions.get(f"witch1_{user_id}")
            if first_target:
                game.witch_links[first_target] = target_id
                game.witch_links[target_id] = first_target
                game.night_actions[f"night_witch_{user_id}"] = (first_target, target_id)
                t1 = game.get_player(first_target)
                t2 = game.get_player(target_id)
                await query.edit_message_text(
                    f"🧝‍♀️ تم ربط {t1.name if t1 else '?'} مع {t2.name if t2 else '?'}!\n"
                    "💀 إذا مات أحدهما، يموت الآخر!"
                )
            else:
                await query.edit_message_text("⚠️ خطأ في الربط.")

        elif action_type == "night_dracula":
            target_id = int(target_value)
            game.night_actions[action_key] = target_id
            target = game.get_player(target_id)
            await query.edit_message_text(f"🧛 ستحاول تحويل {target.name if target else '?'} إلى مصاص دماء.")

    except Exception as e:
        logger.error(f"Night action error: {e}", exc_info=True)
        try:
            await query.edit_message_text(f"⚠️ حدث خطأ. حاول مرة أخرى.")
        except Exception:
            pass


# ── Resolve night actions ──
async def resolve_night(bot: Bot, game: Game):
    killed: List[int] = []
    messages: List[str] = []

    # 1) Forest Guard protection already applied via buttons

    # 2) Process kills: Criminal
    for key, val in game.night_actions.items():
        if key.startswith("night_criminal_") and val != "skip" and isinstance(val, int):
            target = game.get_player(val)
            if target and target.alive and not target.protected:
                if target.role == RoleName.DOG and not target.dog_transformed:
                    # Dog transforms into wolf
                    target.dog_transformed = True
                    messages.append(
                        "🌙 في عمق الليل…\n"
                        "🐶 صرخة ألم تحولت إلى…\n"
                        "🐺 عواء مرعب!\n"
                        f"😨 الكلب..\n"
                        "⚠️ لقد أصبح ذئبًا!"
                    )
                else:
                    killed.append(val)

    # 3) Ghost killer
    for key, val in game.night_actions.items():
        if key.startswith("night_ghost_") and val != "skip" and isinstance(val, int):
            target = game.get_player(val)
            if target and target.alive and not target.protected and val not in killed:
                if target.role == RoleName.DOG and not target.dog_transformed:
                    target.dog_transformed = True
                    messages.append(
                        "🌙 في عمق الليل…\n"
                        "🐶 صرخة ألم تحولت إلى…\n"
                        "🐺 عواء مرعب!\n"
                        f"😨 الكلب..\n"
                        "⚠️ لقد أصبح ذئبًا!"
                    )
                else:
                    killed.append(val)

    # 4) Batman kills
    for key, val in game.night_actions.items():
        if key.startswith("night_batman_") and val != "skip" and isinstance(val, int):
            target = game.get_player(val)
            if target and target.alive and val not in killed:
                killed.append(val)

    # 5) Chef poison (mark for next night)
    for key, val in game.night_actions.items():
        if key.startswith("night_chef_") and val != "skip" and isinstance(val, int):
            target = game.get_player(val)
            if target and target.alive:
                target.poisoned = True

    # 6) Kill poisoned players (from PREVIOUS night's poison)
    for p in game.alive_players:
        if p.poisoned and p.user_id not in killed:
            # Check if this was poisoned last round (not this round)
            # We mark poisoned=True this round, they die next resolve
            # So we need a flag to differentiate. Let's use a counter.
            pass
    # Actually, let's refine: poison takes effect immediately next night resolve
    # The chef poisons NOW, the player dies NEXT night.
    # We'll handle this by checking poisoned flag at the START of next night resolve.
    # For now, handle previously poisoned players:
    for key, val in list(game.night_actions.items()):
        if key.startswith("poison_pending_"):
            uid = int(key.split("_")[-1])
            target = game.get_player(uid)
            if target and target.alive and uid not in killed and not target.protected:
                killed.append(uid)
                target.poisoned = False

    # Set up poison for next round
    for key, val in game.night_actions.items():
        if key.startswith("night_chef_") and val != "skip" and isinstance(val, int):
            game.night_actions[f"poison_pending_{val}"] = True

    # 7) Dracula conversion
    for key, val in game.night_actions.items():
        if key.startswith("night_dracula_") and val != "skip" and isinstance(val, int):
            target = game.get_player(val)
            if target and target.alive and val not in killed:
                target.is_vampire = True
                await safe_send_dm(
                    bot, target.user_id,
                    "🧛 لقد تم تحويلك إلى مصاص دماء!\n"
                    "😈 أنت الآن في فريق دراكولا!\n"
                    "🌑 ساعد دراكولا على السيطرة على القرية."
                )

    # 8) Neighbor results
    for p in game.alive_players:
        if p.visited_target:
            target = game.get_player(p.visited_target)
            if target:
                # Check if target used a night action (i.e., "left home")
                target_acted = any(
                    k.endswith(f"_{target.user_id}") or
                    (isinstance(v, int) and k.startswith("night_") and not k.startswith("poison_"))
                    for k, v in game.night_actions.items()
                    if k.startswith(f"night_") and k.split("_")[-2] == str(game.chat_id)
                )
                # Simpler: check if target has a night action role and they acted
                target_left = False
                for k in game.night_actions:
                    parts = k.split("_")
                    if len(parts) >= 3:
                        try:
                            actor_id = int(parts[-1])
                            if actor_id == target.user_id:
                                target_left = True
                                break
                        except (ValueError, IndexError):
                            pass
                # Actually, check by role's action key format
                for k, v in game.night_actions.items():
                    if k.endswith(f"_{target.user_id}") and v != "skip":
                        target_left = True
                        break

                if target_left:
                    await safe_send_dm(bot, p.user_id, f"😘 زرت {target.name}… لكنه لم يكن في بيته! 🚪")
                else:
                    await safe_send_dm(bot, p.user_id, f"😘 زرت {target.name}… كان في بيته بأمان 🏠")

    # 9) Apply witch links: if someone dies and is linked, the other dies too
    additional_kills = []
    for uid in killed:
        if uid in game.witch_links:
            linked_uid = game.witch_links[uid]
            if linked_uid not in killed and linked_uid not in additional_kills:
                linked_player = game.get_player(linked_uid)
                if linked_player and linked_player.alive:
                    additional_kills.append(linked_uid)
    killed.extend(additional_kills)

    # 10) Apply deaths
    unique_killed = list(dict.fromkeys(killed))  # preserve order, remove dupes
    for uid in unique_killed:
        player = game.get_player(uid)
        if player:
            player.alive = False

    # ── Announce results ──
    if not unique_killed:
        await safe_send(
            bot, game.chat_id,
            "🌅 أشرقت الشمس…\n"
            "😳 الجميع على قيد الحياة!\n"
            "🌲 لكن التوتر يزداد…\n"
            "👁️ يبدو أن أحدهم كان مستهدفًا… ونجا بأعجوبة!"
        )
    else:
        for uid in unique_killed:
            player = game.get_player(uid)
            if player:
                death_msg = DEATH_MESSAGES.get(player.role, "💀 رحل عنا…")

                # Determine which GIF and killer type for this death
                killer_type = "generic"
                for key, val in game.night_actions.items():
                    if isinstance(val, int) and val == uid:
                        if "criminal" in key:
                            killer_type = "criminal"
                        elif "ghost" in key:
                            killer_type = "ghost"
                        elif "batman" in key:
                            killer_type = "batman"
                        elif "poison" in key or "chef" in key:
                            killer_type = "poison"

                # Pick the right GIF
                if killer_type == "criminal":
                    death_gif = DEATH_CRIMINAL_GIF
                elif killer_type == "ghost":
                    death_gif = DEATH_GHOST_GIF
                elif killer_type == "batman":
                    death_gif = DEATH_BATMAN_GIF
                elif killer_type == "poison":
                    death_gif = DEATH_POISON_GIF
                else:
                    death_gif = DEATH_GENERIC_GIF

                # Send death GIF in group
                try:
                    await bot.send_animation(
                        chat_id=game.chat_id,
                        animation=death_gif,
                        caption=(
                            f"💀 تم العثور على جثة *{player.name}*\n"
                            f"😨 ملامح الرعب على وجهه… وكأنه رأى شيئًا قبل موته!\n"
                            f"🗣️ من التالي؟ ومن القاتل?\n\n"
                            f"🎭 هويته: {player.display_role}\n\n"
                            f"{death_msg}"
                        ),
                        parse_mode="Markdown",
                    )
                except TelegramError:
                    # Fallback to text if GIF fails
                    await safe_send(
                        bot, game.chat_id,
                        f"💀 تم العثور على جثة *{player.name}*\n"
                        f"😨 ملامح الرعب على وجهه… وكأنه رأى شيئًا قبل موته!\n"
                        f"🗣️ من التالي؟ ومن القاتل?\n\n"
                        f"🎭 هويته: {player.display_role}\n\n"
                        f"{death_msg}",
                        parse_mode="Markdown",
                    )

                # DM the killed player with a death notification + GIF
                dm_death_text = ""
                if killer_type == "criminal":
                    dm_death_text = (
                        "🔪 *لقد تم قتلك!*\n\n"
                        "🌑 في عمق الليل… اقترب منك المجرم بصمت…\n"
                        "💀 لم تستطع الهرب.\n"
                        "😔 انتهت رحلتك في هذه اللعبة.\n\n"
                        f"🎭 كان دورك: {player.display_role}\n"
                        "👻 يمكنك متابعة اللعبة كمتفرج."
                    )
                elif killer_type == "ghost":
                    dm_death_text = (
                        "👻 *لقد قتلك الشبح!*\n\n"
                        "🌑 شعرت بنسمة باردة… ثم لا شيء…\n"
                        "💀 الشبح أخذ روحك بصمت مطلق.\n"
                        "😔 لم يسمع أحد صرختك.\n\n"
                        f"🎭 كان دورك: {player.display_role}\n"
                        "👻 يمكنك متابعة اللعبة كمتفرج."
                    )
                elif killer_type == "batman":
                    dm_death_text = (
                        "🦹‍♂️ *باتمان أطلق النار عليك!*\n\n"
                        "💥 رصاصة واحدة كانت كافية…\n"
                        "💀 سقطت أرضًا.\n\n"
                        f"🎭 كان دورك: {player.display_role}\n"
                        "👻 يمكنك متابعة اللعبة كمتفرج."
                    )
                elif killer_type == "poison":
                    dm_death_text = (
                        "☠️ *لقد مت مسمومًا!*\n\n"
                        "🧑‍🍳 السم تسلل إلى جسدك ببطء…\n"
                        "💀 لم تستطع مقاومته.\n\n"
                        f"🎭 كان دورك: {player.display_role}\n"
                        "👻 يمكنك متابعة اللعبة كمتفرج."
                    )
                else:
                    dm_death_text = (
                        "💀 *لقد تم قتلك!*\n\n"
                        "🌑 الظلام ابتلعك…\n"
                        "😔 انتهت رحلتك.\n\n"
                        f"🎭 كان دورك: {player.display_role}\n"
                        "👻 يمكنك متابعة اللعبة كمتفرج."
                    )

                # Send DM with GIF
                try:
                    await bot.send_animation(
                        chat_id=player.user_id,
                        animation=death_gif,
                        caption=dm_death_text,
                        parse_mode="Markdown",
                    )
                except TelegramError:
                    await safe_send_dm(bot, player.user_id, dm_death_text, parse_mode="Markdown")

                await asyncio.sleep(2)

    # Extra messages (dog transformation etc.)
    for msg in messages:
        await safe_send(bot, game.chat_id, msg)
        await asyncio.sleep(2)

    # ── Check win condition ──
    winner = game.check_win()
    if winner:
        await announce_winner(bot, game, winner)
        return

    # ── Move to day phase ──
    await asyncio.sleep(3)
    game._phase_task = asyncio.create_task(run_day(bot, game))


# ══════════════════════════════════════════════
# DAY PHASE
# ══════════════════════════════════════════════

async def run_day(bot: Bot, game: Game):
    try:
        game.phase = Phase.DAY

        alive_text = "\n".join(f"• {p.name}" for p in game.alive_players)
        await safe_send(
            bot, game.chat_id,
            f"🌅 *النهار - الجولة {game.round_num}*\n\n"
            f"☀️ أشرقت الشمس على القرية...\n"
            f"🗣️ حان وقت النقاش!\n\n"
            f"👥 الأحياء ({len(game.alive_players)}):\n{alive_text}\n\n"
            f"⏳ لديكم 30 ثانية للنقاش قبل بدء التصويت...",
            parse_mode="Markdown",
        )

        # Discussion period
        await asyncio.sleep(30)

        # Check for truce
        if game.truce_active:
            await safe_send(
                bot, game.chat_id,
                "🛑 تم إعلان هدنة!\n"
                "🚫 لا يوجد تصويت في هذه الجولة.\n"
                "🌲 الجميع يعود للنقاش فقط…\n"
                "استعدوا لما هو قادم!"
            )
            await asyncio.sleep(5)
            game._phase_task = asyncio.create_task(run_night(bot, game))
            return

        # Start voting
        await run_voting(bot, game)

    except asyncio.CancelledError:
        logger.info(f"Day phase cancelled for chat {game.chat_id}")
    except Exception as e:
        logger.error(f"Error in day phase: {e}", exc_info=True)
        await safe_send(bot, game.chat_id, f"⚠️ حدث خطأ: {e}")


# ══════════════════════════════════════════════
# VOTING PHASE
# ══════════════════════════════════════════════

async def run_voting(bot: Bot, game: Game):
    try:
        game.phase = Phase.VOTING
        game.votes = {}

        alive = game.alive_players
        buttons = []
        row = []
        for i, p in enumerate(alive):
            row.append(InlineKeyboardButton(
                f"{p.name}", callback_data=f"vote_{game.chat_id}_{p.user_id}"
            ))
            if len(row) == 2 or i == len(alive) - 1:
                buttons.append(row)
                row = []
        buttons.append([InlineKeyboardButton("⏭️ تخطي التصويت", callback_data=f"vote_{game.chat_id}_skip")])

        msg = await safe_send(
            bot, game.chat_id,
            "⚖️ *بدأ التصويت!*\n\n"
            "⚖️ اختاروا شخصًا تعتقدون أنه مشبوه.\n"
            "⏳ لديكم 60 ثانية للتصويت!\n\n"
            "وقت التصويت بدأ!\n"
            "⏳ لديكم 60 ثانية فقط لاختيار الشخص الذي تعتقدون أنه الخطر الأكبر في القرية.\n"
            "⚖️ كل صوت مهم… كل قرار قد يغير مصير اللعبة!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        if msg:
            game.vote_message_id = msg.message_id

        # Wait 40s, then send reminder
        await asyncio.sleep(20)

        await safe_send(
            bot, game.chat_id,
            "⚡ العد التنازلي مستمر!\n"
            "⏱️ 40 ثانية متبقية…\n"
            "👁️ تذكروا، ليس كل من يبدو بريئًا فعلاً كذلك!"
        )

        await asyncio.sleep(40)

        # Handle madman's random vote
        for p in alive:
            if p.role == RoleName.MADMAN and p.alive and p.user_id not in game.votes:
                possible = [t for t in alive if t.user_id != p.user_id]
                if possible:
                    game.votes[p.user_id] = random.choice(possible).user_id

        # Resolve votes
        await resolve_votes(bot, game)

    except asyncio.CancelledError:
        logger.info(f"Voting cancelled for chat {game.chat_id}")
    except Exception as e:
        logger.error(f"Error in voting: {e}", exc_info=True)
        await safe_send(bot, game.chat_id, f"⚠️ حدث خطأ: {e}")


# ── Vote callback ──
async def vote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if not data.startswith("vote_"):
        return

    parts = data.split("_")
    try:
        chat_id = int(parts[1])
        target_value = parts[2]
    except (IndexError, ValueError):
        return

    game = gm.get_game(chat_id)
    if not game or game.phase != Phase.VOTING:
        await query.answer("⚠️ التصويت انتهى!", show_alert=True)
        return

    voter_id = query.from_user.id
    voter = game.get_player(voter_id)
    if not voter or not voter.alive:
        await query.answer("⚠️ لا يمكنك التصويت!", show_alert=True)
        return

    # Madman always votes randomly (override their choice)
    if voter.role == RoleName.MADMAN:
        possible = [p for p in game.alive_players if p.user_id != voter_id]
        if possible:
            target_id = random.choice(possible).user_id
            game.votes[voter_id] = target_id
            target = game.get_player(target_id)
            await query.answer(f"🤡 صوّت (عشوائيًا) لـ {target.name if target else '?'}!", show_alert=True)
            await safe_send(
                context.bot, chat_id,
                f"✅ {voter.name} صوّت!"
            )
        return

    if target_value == "skip":
        game.votes[voter_id] = -1  # skip
        await query.answer("⏭️ تم تخطي التصويت!", show_alert=True)
        await safe_send(context.bot, chat_id, f"✅ {voter.name} امتنع عن التصويت.")
        return

    target_id = int(target_value)
    game.votes[voter_id] = target_id
    target = game.get_player(target_id)

    await query.answer(f"✅ صوّت لـ {target.name if target else '?'}!", show_alert=True)
    await safe_send(
        context.bot, chat_id,
        f"✅ {voter.name} صوّت!"
    )


# ── Resolve votes ──
async def resolve_votes(bot: Bot, game: Game):
    if not game.votes:
        await safe_send(
            bot, game.chat_id,
            "⚖️ لم يصوّت أحد!\n"
            "🌙 استعدوا لليلة القادمة…"
        )
        game._phase_task = asyncio.create_task(run_night(bot, game))
        return

    # Count votes
    vote_counts: Dict[int, int] = {}
    for voter_id, target_id in game.votes.items():
        if target_id == -1:
            continue
        vote_counts[target_id] = vote_counts.get(target_id, 0) + 1

    if not vote_counts:
        await safe_send(
            bot, game.chat_id,
            "⚖️ جميع الأصوات كانت امتناعًا!\n"
            "🌙 استعدوا لليلة القادمة…"
        )
        game._phase_task = asyncio.create_task(run_night(bot, game))
        return

    # Find max votes
    max_votes = max(vote_counts.values())
    top_targets = [uid for uid, count in vote_counts.items() if count == max_votes]

    # Vote summary
    summary_lines = []
    for uid, count in sorted(vote_counts.items(), key=lambda x: -x[1]):
        p = game.get_player(uid)
        if p:
            summary_lines.append(f"• {p.name}: {count} صوت")
    summary = "\n".join(summary_lines)

    if len(top_targets) > 1:
        # Tie - no execution
        await safe_send(
            bot, game.chat_id,
            f"⚖️ *نتائج التصويت:*\n{summary}\n\n"
            "⚖️ تعادل! لا يوجد إعدام هذه الجولة.\n"
            "🌙 استعدوا لليلة القادمة…",
            parse_mode="Markdown",
        )
        game._phase_task = asyncio.create_task(run_night(bot, game))
        return

    target_id = top_targets[0]
    target = game.get_player(target_id)

    if not target:
        game._phase_task = asyncio.create_task(run_night(bot, game))
        return

    # ── Special cases ──

    # Grocer wins if voted out
    if target.role == RoleName.GROCER and target.alive:
        target.alive = False
        await safe_send(
            bot, game.chat_id,
            f"⚖️ *نتائج التصويت:*\n{summary}\n\n"
            "🧌 مفاجأة صادمة!!\n"
            f"تم إعدام صاحب البقالة المهجورة… *{target.name}*\n"
            "😈 وبذلك يفوز وحده!!\n"
            "💀 جميع اللاعبين خسروا…",
            parse_mode="Markdown",
        )
        await announce_winner(bot, game, "grocer", target.name)
        return

    # Prince survives first vote
    if target.role == RoleName.PRINCE and target.prince_lives > 0:
        target.prince_lives -= 1
        await safe_send(
            bot, game.chat_id,
            f"⚖️ *نتائج التصويت:*\n{summary}\n\n"
            "👑 محاولة إعدام الأمير!\n"
            f"لكن *{target.name}* الأمير نجا هذه المرة!\n"
            "المفاجآت لم تنتهِ بعد…\n"
            "🌙 استعدوا لليلة القادمة…",
            parse_mode="Markdown",
        )
        game._phase_task = asyncio.create_task(run_night(bot, game))
        return

    # Normal execution
    target.alive = False
    death_msg = DEATH_MESSAGES.get(target.role, "💀 رحل عنا…")

    await safe_send(
        bot, game.chat_id,
        f"⚖️ *نتائج التصويت:*\n{summary}\n\n"
        "⚖️ تم التصويت…\n"
        f"💀 تم إعدام: *{target.name}*\n"
        f"🎭 كانت هويته: {target.display_role}\n"
        "🌲 هل كان مذنبًا… أم ضحية بريئة؟\n\n"
        f"{death_msg}\n\n"
        "🌙 استعدوا لليلة القادمة…",
        parse_mode="Markdown",
    )

    # Witch link: if executed player is linked, kill the other too
    if target.user_id in game.witch_links:
        linked_uid = game.witch_links[target.user_id]
        linked = game.get_player(linked_uid)
        if linked and linked.alive:
            linked.alive = False
            linked_death_msg = DEATH_MESSAGES.get(linked.role, "💀 رحل عنا…")
            await asyncio.sleep(2)
            await safe_send(
                bot, game.chat_id,
                f"🧝‍♀️ *الرابط السحري!*\n"
                f"💀 بسبب ربط الساحرة، مات أيضًا: *{linked.name}*\n"
                f"🎭 هويته: {linked.display_role}\n\n"
                f"{linked_death_msg}",
                parse_mode="Markdown",
            )

    # Check win
    winner = game.check_win()
    if winner:
        await asyncio.sleep(3)
        await announce_winner(bot, game, winner)
        return

    await asyncio.sleep(3)
    game._phase_task = asyncio.create_task(run_night(bot, game))


# ══════════════════════════════════════════════
# WINNER ANNOUNCEMENT
# ══════════════════════════════════════════════

async def announce_winner(bot: Bot, game: Game, winner: str, grocer_name: str = ""):
    game.phase = Phase.GAME_OVER

    if winner == "village":
        text = (
            "🏆 انتهت اللعبة!\n"
            "🎉 فاز الأبرياء!\n"
            "🛡️ تم القضاء على جميع الأشرار.\n"
            "🌲 عادت القرية إلى السلام…"
        )
    elif winner == "evil":
        text = (
            "💀 انتهت اللعبة!\n"
            "😈 فاز الأشرار!\n"
            "🩸 سيطر الظلام على القرية…\n"
            "🌑 لا أحد نجا…"
        )
    elif winner == "dracula":
        text = (
            "🧛‍♂️ الليل لم ينتهِ…\n"
            "🩸 القرية أصبحت تحت حكم مصاصي الدماء…\n"
            "🌑 دراكولا انتصر…\n"
            "⚰️ مرحبًا بكم في الظلام الأبدي."
        )
    elif winner == "grocer":
        text = (
            "🧌 مفاجأة صادمة!!\n"
            f"😈 فاز {grocer_name} - صاحب البقالة المهجورة - وحده!!\n"
            "💀 جميع اللاعبين خسروا…"
        )
    else:
        text = "🏁 انتهت اللعبة!"

    # Show all roles
    roles_text = "\n".join(
        f"{'💀' if not p.alive else '✅'} {p.name} — {p.display_role}"
        for p in game.players.values()
    )

    await safe_send(
        bot, game.chat_id,
        f"{text}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🎭 *كشف الأدوار:*\n{roles_text}\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"استخدم /start لبدء لعبة جديدة!",
        parse_mode="Markdown",
    )

    gm.remove_game(game.chat_id)


# ══════════════════════════════════════════════
# CALLBACK ROUTER
# ══════════════════════════════════════════════

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route all callback queries to the right handler."""
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data
    if data.startswith("night_"):
        await night_action_callback(update, context)
    elif data.startswith("vote_"):
        await vote_callback(update, context)
    elif data.startswith("join_") or data.startswith("startgame_") or data.startswith("cancelgame_"):
        await join_callback(update, context)
    else:
        await query.answer("⚠️ إجراء غير معروف", show_alert=True)


# ══════════════════════════════════════════════
# /endgame (admin command)
# ══════════════════════════════════════════════

async def cmd_endgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return
    chat_id = update.effective_chat.id
    game = gm.get_game(chat_id)
    if game:
        game.phase = Phase.GAME_OVER
        if game._phase_task and not game._phase_task.done():
            game._phase_task.cancel()

        roles_text = "\n".join(
            f"{'💀' if not p.alive else '✅'} {p.name} — {p.display_role}"
            for p in game.players.values()
        )
        await safe_send(
            context.bot, chat_id,
            f"🛑 تم إنهاء اللعبة!\n\n"
            f"🎭 *كشف الأدوار:*\n{roles_text}\n\n"
            f"استخدم /start لبدء لعبة جديدة!",
            parse_mode="Markdown",
        )
        gm.remove_game(chat_id)
    else:
        await update.message.reply_text("⚠️ لا توجد لعبة قائمة!")


# ══════════════════════════════════════════════
# /players
# ══════════════════════════════════════════════

async def cmd_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return
    chat_id = update.effective_chat.id
    game = gm.get_game(chat_id)
    if not game:
        await update.message.reply_text("⚠️ لا توجد لعبة قائمة!")
        return

    if game.phase == Phase.LOBBY:
        text = "👥 *اللاعبون المنضمون:*\n"
        text += "\n".join(f"• {p.name}" for p in game.players.values())
        text += f"\n\n📊 العدد: {len(game.players)}/{Game.MAX_PLAYERS}"
    else:
        text = "👥 *اللاعبون:*\n"
        text += "\n".join(
            f"{'✅' if p.alive else '💀'} {p.name}"
            for p in game.players.values()
        )
        text += f"\n\n📊 الأحياء: {len(game.alive_players)}/{len(game.players)}"

    await update.message.reply_text(text, parse_mode="Markdown")


# ══════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════

def main():
    TOKEN = "8712365309:AAExk4vAUogk2L5wgozuE-cSq3TdEHcOSWg"

    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("join", cmd_join))
    app.add_handler(CommandHandler("startgame", cmd_startgame))
    app.add_handler(CommandHandler("endgame", cmd_endgame))
    app.add_handler(CommandHandler("players", cmd_players))

    # Callback queries
    app.add_handler(CallbackQueryHandler(callback_router))

    logger.info("🐺 Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
