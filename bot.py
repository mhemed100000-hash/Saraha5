#!/usr/bin/env python3
"""
🏰 Ghosts Palace - 𝒉𝒂𝒗𝒂𝒏𝒂 𝑪𝒉𝒂𝒕🦩
"""

import asyncio, random, logging, json, os, time
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase(Enum):
    LOBBY=auto(); NIGHT=auto(); DAY=auto(); VOTING=auto(); LAST_WORDS=auto(); GAME_OVER=auto()

class Team(Enum):
    VILLAGER="villager"; EVIL="evil"; DRACULA="dracula"; SOLO="solo"

class RoleName(Enum):
    CRIMINAL="criminal"; GHOST_KILLER="ghost_killer"; MAID="maid"; CHEF="chef"
    THIEF="thief"; POLICE="police"; DOORMAN="doorman"; NEIGHBOR="neighbor"
    FOREST_GUARD="forest_guard"; MADMAN="madman"; GROCER="grocer"; BATMAN="batman"
    WITCH="witch"; PRINCE="prince"; PAINTER="painter"; CHIEF="chief"
    DRACULA="dracula"; DOG="dog"

GIFS={
    "start":"https://media.tenor.com/bGfM0wo_LAYAAAAC/haunted-house-dark.gif",
    "night":"https://media.tenor.com/v8_jl9a-1BEAAAAC/dark-forest-night.gif",
    "day":"https://media.tenor.com/yl2JsSzf4HMAAAAC/sunrise-morning.gif",
    "vote":"https://media.tenor.com/Xp3lV36LzrkAAAAC/court-judge.gif",
    "death_criminal":"https://media.tenor.com/KJj0bCCqLqkAAAAC/knife-dark.gif",
    "death_ghost":"https://media.tenor.com/pFC2-DnV-K0AAAAC/ghost-horror.gif",
    "death_poison":"https://media.tenor.com/5maMW4Y6KGQAAAAC/poison-potion.gif",
    "death_batman":"https://media.tenor.com/f0esMvO45VMAAAAC/batman-dark-knight.gif",
    "death_generic":"https://media.tenor.com/MKBwuxHsHpMAAAAC/rip-grave.gif",
    "death_vote":"https://media.tenor.com/mfjEKGYaucIAAAAC/guillotine-execution.gif",
    "win_village":"https://media.tenor.com/u-FFU3mUBWsAAAAC/celebration-fireworks.gif",
    "win_evil":"https://media.tenor.com/XlFHm39ATdgAAAAC/evil-laugh-dark.gif",
    "win_dracula":"https://media.tenor.com/iUWmVXdMf4gAAAAC/dracula-vampire.gif",
    "truce":"https://media.tenor.com/zO2-v0-SXw0AAAAC/peace-handshake.gif",
    "dog_transform":"https://media.tenor.com/Db4CaZoUI8UAAAAC/werewolf-transformation.gif",
    "blood_moon":"https://media.tenor.com/tGOVXY-VVS4AAAAC/blood-moon-red-moon.gif",
    "storm":"https://media.tenor.com/qViez0k7oGAAAAAC/storm-lightning.gif",
}


BASE_DIR=os.path.dirname(os.path.abspath(__file__))
START_IMAGE_PATH=os.path.join(BASE_DIR,"start_cover.jpg")

NIGHT_MESSAGES=[
    "حلّ الظلام على القصر…\nالرياح تعصف والأبواب تُغلق.\nمن يتحرك في الظل؟\n\nأصحاب الأدوار الليلية، الوقت لكم.",
    "الظلام يبتلع كل شيء…\nصوت خطوات يقترب ببطء.\nأحدهم يراقب… وأحدهم يتحرك.\n\nنفّذوا مهامكم قبل الفجر.",
    "القمر وحده يشهد على ما يحدث…\nشمعة خافتة وظل يعبر النافذة.\nالصمت أثقل من أي صرخة.\n\nافعلوا ما يجب فعله.",
    "النجوم اختفت والريح سكنت…\nعواء بعيد يكسر الصمت.\nباب يُفتح… ثم يُغلق.\n\nاستخدموا قدراتكم بحكمة."
]
DAY_MESSAGES=[
    "أشرقت الشمس وكشفت ما أخفاه الليل.\nالوجوه متوترة… والأسئلة كثيرة.\n\nحان وقت النقاش.",
    "الفجر يطرد الظلام… لكن ليس الشكوك.\nبعض الوجوه مفقودة اليوم.\n\nابدأوا النقاش.",
    "يوم جديد في القصر…\nالتوتر واضح على الجميع.\nمن يستحق الثقة؟\n\nوقت المواجهة."
]
SUSPENSE=[
    "😨 التوتر يتصاعد…",
    "🌲 شيء ما يتحرك في الخلفية…",
    "👁 هل لاحظتم تلك النظرات؟",
    "🤫 الصمت أحياناً أخطر من الكلام…",
    "🎭 الأقنعة ستسقط عاجلاً أم آجلاً…",
    "🐾 آثار أقدام غريبة عند باب أحدهم…",
    "🕯 شمعة انطفأت فجأة… من أطفأها؟",
    "💀 رائحة الموت تقترب…",
    "🔮 العرّافة تعرف شيئاً… لكنها صامتة.",
    "⚰ أحدهم يحفر قبراً مسبقاً…",
    "🗡 السكين لا تزال دافئة…",
    "🌑 الظلام يعرف أسراركم جميعاً…",
    "👤 ظلّ يراقبكم من بعيد…",
    "🚪 باب يُفتح ببطء… من هناك؟",
]
RANDOM_EVENTS={
    "blood_moon":{"name":"🔴 قمر دموي","desc":"القمر الأحمر يكشف هوية لاعب عشوائي!","chance":0.12},
    "storm":{"name":"⛈ عاصفة هوجاء","desc":"العاصفة أوقفت كل شيء… لا قتل الليلة.","chance":0.08},
    "fog":{"name":"🌫 ضباب كثيف","desc":"الضباب يعطّل حارس الغابة عن الحماية.","chance":0.10}
}

@dataclass
class RoleDef:
    name:RoleName; display:str; emoji:str; team:Team; has_night_action:bool; description:str; priority:int

ROLE_DEFS={
    RoleName.CRIMINAL:RoleDef(RoleName.CRIMINAL,"المجرم","🗡",Team.EVIL,True,"يختار ضحية لقتلها كل ليلة",1),
    RoleName.GHOST_KILLER:RoleDef(RoleName.GHOST_KILLER,"الشبح","👤",Team.EVIL,True,"يقتل بصمت ولا يُكشف بسهولة",2),
    RoleName.MAID:RoleDef(RoleName.MAID,"العرّافة","🔮",Team.VILLAGER,True,"تكشف الدور الحقيقي للاعب واحد",10),
    RoleName.CHEF:RoleDef(RoleName.CHEF,"الشيف","☠",Team.EVIL,True,"يسمّم لاعباً فيموت الليلة التالية",3),
    RoleName.THIEF:RoleDef(RoleName.THIEF,"اللص","🎭",Team.VILLAGER,True,"يسرق دور لاعب آخر (مرة واحدة)",4),
    RoleName.POLICE:RoleDef(RoleName.POLICE,"المحقق","🔍",Team.VILLAGER,True,"يتحقق إن كان اللاعب من الأشرار",11),
    RoleName.DOORMAN:RoleDef(RoleName.DOORMAN,"الحارس","🚫",Team.VILLAGER,True,"يُعلن هدنة تلغي التصويت (مرة واحدة)",12),
    RoleName.NEIGHBOR:RoleDef(RoleName.NEIGHBOR,"الجارة","👁",Team.VILLAGER,True,"تزور لاعباً وتعرف إن غادر بيته",13),
    RoleName.FOREST_GUARD:RoleDef(RoleName.FOREST_GUARD,"حارس الغابة","🛡",Team.VILLAGER,True,"يحمي لاعباً من القتل (لا يكرر نفسه)",5),
    RoleName.MADMAN:RoleDef(RoleName.MADMAN,"المجنون","🃏",Team.VILLAGER,False,"تصويته عشوائي ولا يتحكم فيه",99),
    RoleName.GROCER:RoleDef(RoleName.GROCER,"صاحب البقالة","🎪",Team.SOLO,False,"إذا أُعدم بالتصويت يفوز وحده",99),
    RoleName.BATMAN:RoleDef(RoleName.BATMAN,"القنّاص","🎯",Team.VILLAGER,True,"يملك طلقتين لقتل من يشاء",6),
    RoleName.WITCH:RoleDef(RoleName.WITCH,"الساحرة","⛓",Team.VILLAGER,True,"تربط لاعبين… إذا مات أحدهما مات الآخر",7),
    RoleName.PRINCE:RoleDef(RoleName.PRINCE,"الأمير","👑",Team.VILLAGER,False,"يحتاج تصويتين للإعدام",99),
    RoleName.PAINTER:RoleDef(RoleName.PAINTER,"الرسام","🖌",Team.VILLAGER,False,"مواطن عادي بلا قدرة",99),
    RoleName.CHIEF:RoleDef(RoleName.CHIEF,"المختار","📜",Team.VILLAGER,False,"مواطن عادي بلا قدرة",99),
    RoleName.DRACULA:RoleDef(RoleName.DRACULA,"دراكولا","🦇",Team.DRACULA,True,"يحوّل لاعباً إلى مصاص دماء",8),
    RoleName.DOG:RoleDef(RoleName.DOG,"الكلب","🐾",Team.VILLAGER,False,"إذا استُهدف بالقتل يتحول لذئب شرير",99),
}

DEATH_MSGS={
    RoleName.MAID:"كانت العرّافة… عرفت الحقيقة لكنها لم تنقذ نفسها.",
    RoleName.CHEF:"كان الشيف… السمّ كان سلاحه المفضل.",
    RoleName.THIEF:"كان اللص… لم تنفعه خفّة يده.",
    RoleName.POLICE:"كان المحقق… بحث عن الحقيقة حتى آخر لحظة.",
    RoleName.DOORMAN:"كان الحارس… حاول حماية النظام.",
    RoleName.NEIGHBOR:"كانت الجارة… اقتربت من الجميع أكثر مما ينبغي.",
    RoleName.FOREST_GUARD:"كان حارس الغابة… حمى غيره ونسي نفسه.",
    RoleName.MADMAN:"كان المجنون… عاش في الفوضى ومات فيها.",
    RoleName.GROCER:"كان صاحب البقالة… سرّه ذهب معه.",
    RoleName.BATMAN:"كان القنّاص… حتى أفضل الرماة يسقطون.",
    RoleName.WITCH:"كانت الساحرة… السحر لم يكن كافياً.",
    RoleName.DOG:"كان الكلب… أوفى من حوله لكن الوفاء لم يحمه.",
    RoleName.PRINCE:"كان الأمير… حتى التاج لا يوقف الموت.",
    RoleName.PAINTER:"كان الرسام… لوحته الأخيرة بقيت بلا توقيع.",
    RoleName.CHIEF:"كان المختار… القرية فقدت قائدها.",
    RoleName.DRACULA:"كان دراكولا… حتى مصاصو الدماء لهم نهاية.",
    RoleName.CRIMINAL:"كان المجرم… سقط أخيراً.",
    RoleName.GHOST_KILLER:"كان الشبح… تلاشى في الظلام للأبد.",
}

# ══════════════════════════════════════════════
STATS_FILE="player_stats.json"
def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE,"r",encoding="utf-8") as f: return json.load(f)
    except: pass
    return {}
def save_stats(s):
    try:
        with open(STATS_FILE,"w",encoding="utf-8") as f: json.dump(s,f,ensure_ascii=False,indent=2)
    except: pass
def update_stat(uid,name,key,val=1):
    s=load_stats(); u=str(uid)
    if u not in s: s[u]={"name":name,"wins":0,"losses":0,"kills":0,"survived":0,"games":0,"mvp":0}
    s[u]["name"]=name; s[u][key]=s[u].get(key,0)+val; save_stats(s)

@dataclass
class LogEntry:
    rnd:int; phase:str; action:str; actor:str=""; target:str=""

@dataclass
class Player:
    user_id:int; name:str; username:str=""; role:Optional[RoleName]=None; alive:bool=True
    poisoned:bool=False; protected:bool=False; prince_lives:int=1
    batman_bullets:int=2; doorman_used:bool=False; thief_used:bool=False
    is_vampire:bool=False; dog_transformed:bool=False; visited_target:Optional[int]=None
    kills:int=0; saves:int=0; investigations:int=0
    @property
    def tag(self):
        if self.username: return f"@{self.username}"
        return f"[{self.name}](tg://user?id={self.user_id})"
    @property
    def role_def(self): return ROLE_DEFS.get(self.role)
    @property
    def team(self):
        if self.is_vampire: return Team.DRACULA
        if self.dog_transformed: return Team.EVIL
        return ROLE_DEFS[self.role].team if self.role else None
    @property
    def display_role(self):
        if not self.role: return "❓"
        rd=ROLE_DEFS[self.role]; x=""
        if self.is_vampire: x=" 🦇"
        if self.dog_transformed: x=" ⟫ ذئب"
        return f"{rd.emoji} {rd.display}{x}"

class Game:
    MIN_PLAYERS=4; MAX_PLAYERS=18; NIGHT_DUR=90; VOTE_DUR=90; DISC_DUR=60; LAST_WORDS_DUR=20
    def __init__(self,cid):
        self.chat_id=cid; self.phase=Phase.LOBBY; self.players:Dict[int,Player]={}
        self.round_num=0; self.night_actions:Dict[str,Any]={}; self.night_kills=[]
        self.pending_actions:Dict[str,Any]={}  # actions from LAST night that execute THIS night
        self.guard_last=None; self.truce=False; self.votes:Dict[int,int]={}
        self.vote_msg_id=None; self.lobby_msg_id=None; self.witch_links:Dict[int,int]={}
        self._task=None; self._lobby_task=None; self.log_entries:List[LogEntry]=[]; self.event=None
        self.storm=False; self.fog=False
        self.vote_event=None; self.vote_closed=False; self.vote_expected=set()
    def add_player(self,uid,name,username=""):
        if uid in self.players or self.phase!=Phase.LOBBY or len(self.players)>=self.MAX_PLAYERS: return False
        self.players[uid]=Player(user_id=uid,name=name,username=username); return True
    def log(self,ph,act,actor="",target=""): self.log_entries.append(LogEntry(self.round_num,ph,act,actor,target))
    @property
    def alive_players(self): return [p for p in self.players.values() if p.alive]
    def get_player(self,uid): return self.players.get(uid)
    def assign_roles(self):
        n=len(self.players); pool=[]
        pool.append(RoleName.CRIMINAL); pool.append(RoleName.MAID)
        if n>=5: pool.append(RoleName.POLICE)
        if n>=6: pool.append(RoleName.FOREST_GUARD)
        if n>=7: pool.append(RoleName.CHEF)
        if n>=8: pool+=[RoleName.DOORMAN,RoleName.NEIGHBOR]
        if n>=9: pool.append(RoleName.GHOST_KILLER)
        if n>=10: pool+=[RoleName.THIEF,RoleName.BATMAN]
        if n>=11: pool+=[RoleName.WITCH,RoleName.PRINCE]
        if n>=12: pool+=[RoleName.DRACULA,RoleName.DOG]
        if n>=13: pool.append(RoleName.GROCER)
        if n>=14: pool.append(RoleName.MADMAN)
        while len(pool)<n: pool.append(random.choice([RoleName.PAINTER,RoleName.CHIEF]))
        pool=pool[:n]; random.shuffle(pool)
        for p,r in zip(self.players.values(),pool):
            p.role=r
            if r==RoleName.PRINCE: p.prince_lives=1
            if r==RoleName.BATMAN: p.batman_bullets=2
    def check_win(self):
        alive=self.alive_players
        if not alive: return "evil"
        ev=len([p for p in alive if p.team==Team.EVIL])
        dr=len([p for p in alive if p.team==Team.DRACULA])
        vi=len([p for p in alive if p.team==Team.VILLAGER])
        so=len([p for p in alive if p.team==Team.SOLO])
        nonevil=vi+so
        if dr>0 and ev==0 and vi==0 and so==0: return "dracula"
        if ev>=nonevil and dr==0: return "evil"
        if (ev+dr)>=nonevil and (ev+dr)>0: return "dracula" if dr>ev else "evil"
        if ev==0 and dr==0: return "village"
        return None
    def calc_mvp(self):
        best=None; bs=-1
        for p in self.players.values():
            sc=p.kills*3+p.saves*4+p.investigations*2+(5 if p.alive else 0)
            if sc>bs: bs=sc; best=p
        return best if best and bs>0 else None

class GameManager:
    def __init__(self): self.games:Dict[int,Game]={}
    def get(self,cid): return self.games.get(cid)
    def create(self,cid): g=Game(cid); self.games[cid]=g; return g
    def remove(self,cid):
        if cid in self.games:
            g=self.games[cid]
            if g._task and not g._task.done(): g._task.cancel()
            if g._lobby_task and not g._lobby_task.done(): g._lobby_task.cancel()
            del self.games[cid]

gm=GameManager()

async def is_admin(bot,cid,uid):
    """Check if user is admin or creator in the chat."""
    try:
        member=await bot.get_chat_member(cid,uid)
        return member.status in ("administrator","creator")
    except: return False

async def ssend(bot,cid,text,**kw):
    try: return await bot.send_message(chat_id=cid,text=text,**kw)
    except TelegramError as e: logger.error(f"Send fail {cid}:{e}"); return None

async def sdm(bot,uid,text,**kw):
    try: return await bot.send_message(chat_id=uid,text=text,**kw)
    except TelegramError as e: logger.warning(f"DM fail {uid}:{e}"); return None

async def sgif(bot,cid,gk,cap,**kw):
    try: return await bot.send_animation(chat_id=cid,animation=GIFS.get(gk,GIFS["start"]),caption=cap,**kw)
    except: return await ssend(bot,cid,cap,**kw)

async def sgif_dm(bot,uid,gk,cap,**kw):
    try: return await bot.send_animation(chat_id=uid,animation=GIFS.get(gk,GIFS["start"]),caption=cap,**kw)
    except: return await sdm(bot,uid,cap,**kw)


async def send_start_cover(bot,cid,caption,**kw):
    try:
        if os.path.exists(START_IMAGE_PATH):
            with open(START_IMAGE_PATH,"rb") as f:
                return await bot.send_photo(chat_id=cid,photo=f,caption=caption,**kw)
    except Exception as e:
        logger.warning(f"Start image fail {cid}:{e}")
    try:
        return await bot.send_animation(chat_id=cid,animation=GIFS.get("start"),caption=caption,**kw)
    except Exception:
        return await ssend(bot,cid,caption,**kw)

def lobby_text(g):
    pl="".join(f"  {i}. {p.tag}\n" for i,p in enumerate(g.players.values(),1)) or "  لا يوجد لاعبين بعد…\n"
    c=len(g.players); st="🟢 يمكن بدء اللعبة" if c>=Game.MIN_PLAYERS else f"⏳ يحتاج {Game.MIN_PLAYERS-c} لاعبين إضافيين"
    return f"🏰 *𝐆𝐡𝐨𝐬𝐭𝐬 𝐏𝐚𝐥𝐚𝐜𝐞* — 𝘩𝘢𝘷𝘢𝘯𝘢 𝘊𝘩𝘢𝘵 🦩\n\n🎭 لعبة جديدة بانتظاركم\n💀 من سيبقى حياً حتى الصباح؟\n\n👥 *اللاعبون* ({c}/{Game.MAX_PLAYERS}):\n{pl}\n{st}"

def lobby_kb(g):
    c=len(g.players); b=[[InlineKeyboardButton("◉ انضم للعبة",callback_data=f"join_{g.chat_id}")]]
    if c>=Game.MIN_PLAYERS: b.append([InlineKeyboardButton("▶ ابدأ اللعبة",callback_data=f"sg_{g.chat_id}")])
    b.append([InlineKeyboardButton("✕ إلغاء",callback_data=f"cg_{g.chat_id}")]); return InlineKeyboardMarkup(b)

async def update_lobby(bot,g):
    if not g.lobby_msg_id: return
    try: await bot.edit_message_text(chat_id=g.chat_id,message_id=g.lobby_msg_id,text=lobby_text(g),parse_mode="Markdown",reply_markup=lobby_kb(g))
    except: pass

async def lobby_refresh_loop(bot,g):
    """Re-sends lobby message + cover image every 90 seconds so it stays visible."""
    try:
        while g.phase==Phase.LOBBY:
            await asyncio.sleep(90)
            if g.phase!=Phase.LOBBY: break
            # Delete old lobby message
            try:
                if g.lobby_msg_id: await bot.delete_message(chat_id=g.chat_id,message_id=g.lobby_msg_id)
            except: pass
            # Re-send cover image
            try: await send_start_cover(bot,g.chat_id,"🏰 *لا تزال اللعبة مفتوحة!*\nانضموا قبل أن تبدأ…",parse_mode="Markdown")
            except: pass
            await asyncio.sleep(1)
            # Re-send lobby with buttons
            m=await ssend(bot,g.chat_id,lobby_text(g),parse_mode="Markdown",reply_markup=lobby_kb(g))
            if m: g.lobby_msg_id=m.message_id
    except asyncio.CancelledError: pass
    except Exception as e: logger.error(f"Lobby refresh err: {e}")

# ── Commands ──
async def cmd_start(update,context):
    if update.effective_chat.type=="private":
        # Handle deep link: /start join_CHATID
        if context.args and len(context.args)>0 and context.args[0].startswith("join_"):
            try:
                cid=int(context.args[0].split("_",1)[1])
                g=gm.get(cid)
                if not g or g.phase!=Phase.LOBBY:
                    await update.message.reply_text("اللعبة غير متاحة حالياً. ارجع للمجموعة وانضم من جديد.")
                    return
                u=update.effective_user; name=u.first_name or u.username or f"U{u.id}"; uname=u.username or ""
                if u.id in g.players:
                    await update.message.reply_text("أنت منضم بالفعل. انتظر بدء اللعبة.")
                    return
                if g.add_player(u.id,name,uname):
                    await update.message.reply_text(f"تم انضمامك يا *{name}*\nانتظر بدء اللعبة في المجموعة.",parse_mode="Markdown")
                    await update_lobby(context.bot,g)
                    await ssend(context.bot,cid,f"*{name}* انضم للعبة.",parse_mode="Markdown")
                else:
                    await update.message.reply_text("اللعبة ممتلئة أو غير متاحة.")
            except Exception as e:
                logger.error(f"Deep link join error: {e}")
                await update.message.reply_text("حصل خطأ. ارجع للمجموعة وحاول مرة ثانية.")
            return
        await update.message.reply_text("🏰 *𝐆𝐡𝐨𝐬𝐭𝐬 𝐏𝐚𝐥𝐚𝐜𝐞* 🦩\n\n👻 لعبة غموض وإثارة جماعية.\n\n📌 *كيف تلعب:*\n١. أضفني لمجموعة\n٢. اكتب /start لفتح لعبة\n٣. اللاعبون ينضمون بالزر\n٤. ابدأ اللعبة واستمتع\n\n🎮 *الأوامر:* /role · /alive · /stats · /leaderboard",parse_mode="Markdown"); return
    cid=update.effective_chat.id; ex=gm.get(cid)
    if ex and ex.phase!=Phase.GAME_OVER: await update.message.reply_text("يوجد لعبة قائمة بالفعل."); return
    if not await is_admin(context.bot,cid,update.effective_user.id):
        await update.message.reply_text("المشرفون فقط يمكنهم بدء لعبة جديدة."); return
    g=gm.create(cid)
    try:
        await send_start_cover(context.bot, cid, "*الأشباح تستيقظ…*\n*القصر يفتح أبوابه…*\n\nاستعدّوا لليلة لن تُنسى.", parse_mode="Markdown")
    except Exception:
        pass
    await asyncio.sleep(1)
    m=await ssend(context.bot,cid,lobby_text(g),parse_mode="Markdown",reply_markup=lobby_kb(g))
    if m: g.lobby_msg_id=m.message_id
    g._lobby_task=asyncio.create_task(lobby_refresh_loop(context.bot,g))

async def cmd_join(update,context):
    if update.effective_chat.type=="private": return
    g=gm.get(update.effective_chat.id)
    if not g or g.phase!=Phase.LOBBY: await update.message.reply_text("لا توجد لعبة مفتوحة."); return
    u=update.effective_user; name=u.first_name or u.username or f"U{u.id}"; uname=u.username or ""
    if g.add_player(u.id,name,uname): await update_lobby(context.bot,g); await update.message.reply_text(f"☑ {name} انضم.")
    else: await update.message.reply_text("منضم بالفعل أو اللعبة ممتلئة.")

async def cmd_startgame(update,context):
    if update.effective_chat.type=="private": return
    cid=update.effective_chat.id; g=gm.get(cid)
    if not g or g.phase!=Phase.LOBBY: return
    if not await is_admin(context.bot,cid,update.effective_user.id):
        await update.message.reply_text("المشرفون فقط يمكنهم بدء اللعبة."); return
    if len(g.players)<Game.MIN_PLAYERS: await update.message.reply_text(f"يحتاج {Game.MIN_PLAYERS} لاعبين على الأقل."); return
    try:
        if g.lobby_msg_id: await context.bot.edit_message_reply_markup(chat_id=cid,message_id=g.lobby_msg_id,reply_markup=None)
    except: pass
    await start_logic(context.bot,g,cid)

async def cmd_role(update,context):
    uid=update.effective_user.id
    for g in gm.games.values():
        p=g.get_player(uid)
        if p and p.role and g.phase not in (Phase.LOBBY,Phase.GAME_OVER):
            rd=p.role_def; tt={"villager":"الأبرياء","evil":"الأشرار","dracula":"دراكولا","solo":"مستقل"}
            extra=""
            if p.is_vampire: extra="\n\nتم تحويلك لمصاص دماء."
            if p.dog_transformed: extra="\n\nتحوّلت إلى ذئب."
            await sdm(context.bot,uid,f"🎭 *تذكير بدورك:*\n\n{rd.emoji} *{rd.display}*\n📝 {rd.description}\n\n👥 الفريق: {tt.get(p.team.value if p.team else 'villager','—')}{extra}",parse_mode="Markdown")
            if update.effective_chat.type!="private": await update.message.reply_text("تم إرسال دورك في الخاص.")
            return
    await update.message.reply_text("لست في لعبة نشطة.")

async def cmd_alive(update,context):
    if update.effective_chat.type=="private": return
    g=gm.get(update.effective_chat.id)
    if not g or g.phase in (Phase.LOBBY,Phase.GAME_OVER): await update.message.reply_text("لا توجد لعبة نشطة."); return
    alive=g.alive_players; dead=[p for p in g.players.values() if not p.alive]
    t=f"🟢 *الأحياء* ({len(alive)}):\n"+"\n".join(f"  ● {p.tag}" for p in alive)
    if dead: t+=f"\n\n💀 *الأموات* ({len(dead)}):\n"+"\n".join(f"  ✕ {p.tag}" for p in dead)
    await update.message.reply_text(t,parse_mode="Markdown")

async def cmd_stats(update,context):
    uid=str(update.effective_user.id); s=load_stats()
    if uid not in s: await update.message.reply_text("لا توجد إحصائيات بعد."); return
    d=s[uid]; wr=(d.get('wins',0)/d.get('games',1))*100 if d.get('games',0)>0 else 0
    await update.message.reply_text(f"📊 *إحصائياتك:*\n\n🎮 ألعاب: {d.get('games',0)}\n🏆 فوز: {d.get('wins',0)}  ·  💀 خسارة: {d.get('losses',0)}\n📈 نسبة الفوز: {wr:.0f}%\n🗡 قتل: {d.get('kills',0)}  ·  🛡 نجاة: {d.get('survived',0)}\n⭐ MVP: {d.get('mvp',0)}",parse_mode="Markdown")

async def cmd_leaderboard(update,context):
    s=load_stats()
    if not s: await update.message.reply_text("لا توجد إحصائيات بعد."); return
    sp=sorted(s.items(),key=lambda x:x[1].get("wins",0),reverse=True)[:10]
    medals=["🥇","🥈","🥉"]
    lines=[f"{medals[i] if i<3 else f'#{i+1}'} *{d['name']}* — 🏆 {d.get('wins',0)} · 🗡 {d.get('kills',0)} · ⭐ {d.get('mvp',0)}" for i,(u,d) in enumerate(sp)]
    await update.message.reply_text(f"🏆 *المتصدرين:*\n\n"+"\n".join(lines),parse_mode="Markdown")

async def cmd_endgame(update,context):
    if update.effective_chat.type=="private": return
    cid=update.effective_chat.id; g=gm.get(cid)
    if not g: await update.message.reply_text("لا توجد لعبة."); return
    if not await is_admin(context.bot,cid,update.effective_user.id):
        await update.message.reply_text("المشرفون فقط يمكنهم إنهاء اللعبة."); return
    g.phase=Phase.GAME_OVER
    if g._task and not g._task.done(): g._task.cancel()
    rt="\n".join(f"{'  💀' if not p.alive else '  ☑'} {p.tag} — {p.display_role}" for p in g.players.values())
    await ssend(context.bot,cid,f"🛑 *تم إنهاء اللعبة*\n\n🎭 *الأدوار:*\n{rt}\n\n🔄 /start للعبة جديدة",parse_mode="Markdown")
    gm.remove(cid)

async def cmd_players(update,context):
    if update.effective_chat.type=="private": return
    g=gm.get(update.effective_chat.id)
    if not g: await update.message.reply_text("لا توجد لعبة."); return
    if g.phase==Phase.LOBBY:
        t="👥 *المنضمون:*\n"+"\n".join(f"  {p.tag}" for p in g.players.values())+f"\n\n📊 {len(g.players)}/{Game.MAX_PLAYERS}"
    else:
        t="👥 *اللاعبون:*\n"+"\n".join(f"{'  ☑' if p.alive else '  💀'} {p.tag}" for p in g.players.values())+f"\n\n📊 أحياء: {len(g.alive_players)}/{len(g.players)}"
    await update.message.reply_text(t,parse_mode="Markdown")

# ── Callbacks ──
async def join_cb(update,context):
    q=update.callback_query; d=q.data
    if d.startswith("join_"):
        cid=int(d.split("_")[1]); g=gm.get(cid)
        if not g or g.phase!=Phase.LOBBY: await q.answer("غير متاحة.",show_alert=True); return
        u=q.from_user; name=u.first_name or u.username or f"U{u.id}"; uname=u.username or ""
        if u.id in g.players: await q.answer("منضم بالفعل.",show_alert=True); return
        if g.add_player(u.id,name,uname):
            test=await sdm(context.bot,u.id,"☑ تم انضمامك. انتظر بدء اللعبة.")
            if not test:
                if u.id in g.players: del g.players[u.id]
                bi=await context.bot.get_me()
                deep_link=f"https://t.me/{bi.username}?start=join_{cid}"
                kb=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 افتح البوت وانضم!",url=deep_link)]])
                await q.answer("اضغط الزر لفتح البوت أولاً.",show_alert=True)
                try: await context.bot.send_message(chat_id=cid,text=f"*{name}*، افتح البوت أولاً ثم انضم:",parse_mode="Markdown",reply_markup=kb)
                except: pass
                return
            await q.answer(f"انضممت يا {name}.",show_alert=True); await update_lobby(context.bot,g)
        else: await q.answer("اللعبة ممتلئة.",show_alert=True)
    elif d.startswith("sg_"):
        cid=int(d.split("_")[1]); g=gm.get(cid)
        if not g or g.phase!=Phase.LOBBY: await q.answer("غير متاحة.",show_alert=True); return
        if not await is_admin(context.bot,cid,q.from_user.id):
            await q.answer("المشرفون فقط يمكنهم بدء اللعبة.",show_alert=True); return
        if len(g.players)<Game.MIN_PLAYERS: await q.answer(f"يحتاج {Game.MIN_PLAYERS} لاعبين.",show_alert=True); return
        await q.answer("جاري البدء…")
        try: await context.bot.edit_message_reply_markup(chat_id=cid,message_id=g.lobby_msg_id,reply_markup=None)
        except: pass
        await start_logic(context.bot,g,cid)
    elif d.startswith("cg_"):
        cid=int(d.split("_")[1]); g=gm.get(cid)
        if not g or g.phase!=Phase.LOBBY: await q.answer("غير متاحة.",show_alert=True); return
        if not await is_admin(context.bot,cid,q.from_user.id):
            await q.answer("المشرفون فقط يمكنهم إلغاء اللعبة.",show_alert=True); return
        lid=g.lobby_msg_id; gm.remove(cid); await q.answer("تم الإلغاء.",show_alert=True)
        try: await context.bot.edit_message_text(chat_id=cid,message_id=lid,text="*تم إلغاء اللعبة.*\n\n/start للعبة جديدة.",parse_mode="Markdown")
        except: pass

# ── Start Logic ──
async def start_logic(bot,g,cid):
    # Stop lobby refresh
    if g._lobby_task and not g._lobby_task.done(): g._lobby_task.cancel()
    g.assign_roles(); plist="👥 *اللاعبون:*\n"; fails=[]
    tt={"villager":"🛡 الأبرياء","evil":"😈 الأشرار","dracula":"🦇 دراكولا","solo":"🎪 مستقل"}
    for p in g.players.values():
        plist+=f"  {p.tag}\n"; rd=p.role_def
        r=await sdm(bot,p.user_id,f"🎭 *دورك في هذه الجولة:*\n\n{rd.emoji} *{rd.display}*\n📝 {rd.description}\n\n👥 الفريق: {tt.get(rd.team.value,'—')}\n\n⚠ لا تكشف دورك لأحد.\n💡 /role للتذكير لاحقاً",parse_mode="Markdown")
        if not r: fails.append(p.name)
        update_stat(p.user_id,p.name,"games")
    await ssend(bot,cid,f"🎲 *تم توزيع الأدوار*\n\n{plist}\n📩 تحقق من الرسائل الخاصة.\n👥 عدد اللاعبين: {len(g.players)}\n\n💡 /role · /alive · /stats",parse_mode="Markdown")
    if fails:
        bi=await bot.get_me()
        fail_btns=[[InlineKeyboardButton(f"🚀 {n} - افتح البوت!",url=f"https://t.me/{bi.username}?start=hello")] for n in fails]
        await ssend(bot,cid,"*تنبيه*\n\nلم أستطع إرسال الدور لـ:\n"+"\n".join(f"  {n}" for n in fails)+f"\n\nافتحوا البوت من الأزرار ثم أعيدوا بـ /start",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(fail_btns))
        g.phase=Phase.GAME_OVER; gm.remove(cid); return
    evils=[p for p in g.players.values() if p.role_def.team==Team.EVIL]
    if len(evils)>1:
        for ep in evils:
            others=[f"  {o.name} — {o.role_def.emoji} {o.role_def.display}" for o in evils if o.user_id!=ep.user_id]
            await sdm(bot,ep.user_id,"*فريقك من الأشرار:*\n"+"\n".join(others),parse_mode="Markdown")
    g.log("start","بدأت اللعبة","",f"{len(g.players)} لاعب")
    await asyncio.sleep(3); g._task=asyncio.create_task(run_night(bot,g))

# ══════════════════════════════════════════════
# NIGHT
# ══════════════════════════════════════════════
async def run_night(bot,g):
    try:
        g.phase=Phase.NIGHT; g.round_num+=1; g.night_actions={}; g.night_kills=[]
        g.truce=False; g.storm=False; g.fog=False; g.event=None
        for p in g.alive_players: p.protected=False; p.visited_target=None
        # Random event
        emsg=""
        for ek,ed in RANDOM_EVENTS.items():
            if random.random()<ed["chance"] and g.round_num>1:
                g.event=ek
                if ek=="storm": g.storm=True
                elif ek=="fog": g.fog=True
                emsg=f"\n\n{ed['name']}\n{ed['desc']}"; break
        await sgif(bot,g.chat_id,"night",f"🌙 *الليلة {g.round_num}*\n\n{random.choice(NIGHT_MESSAGES)}{emsg}\n\n⏳ {Game.NIGHT_DUR} ثانية.",parse_mode="Markdown")
        if g.event=="blood_moon":
            rp=random.choice(g.alive_players); await asyncio.sleep(2)
            await ssend(bot,g.chat_id,f"🔴 *القمر الدموي يكشف:*\n{rp.tag} هو {rp.display_role}",parse_mode="Markdown")
            g.log("night","قمر دموي","",f"{rp.name}={rp.display_role}")
        for p in g.alive_players: await send_night(bot,g,p)
        th=Game.NIGHT_DUR//3
        await asyncio.sleep(th)
        await ssend(bot,g.chat_id,f"⏳ متبقي {th*2} ثانية…")
        await asyncio.sleep(th)
        await ssend(bot,g.chat_id,f"*آخر {th} ثانية* — قرروا الآن.",parse_mode="Markdown")
        await asyncio.sleep(th)
        await ssend(bot,g.chat_id,random.choice(SUSPENSE))
        await asyncio.sleep(2)
        await resolve_night(bot,g)
    except asyncio.CancelledError: pass
    except Exception as e: logger.error(f"Night err:{e}",exc_info=True); await ssend(bot,g.chat_id,f"خطأ تقني: {e}")

async def send_night(bot,g,player):
    role=player.role; targets=[p for p in g.alive_players if p.user_id!=player.user_id]
    if not targets: return
    cp=None; text=None
    if role==RoleName.CRIMINAL: text="🗡 اختر ضحيتك:"; cp="nc"
    elif role==RoleName.GHOST_KILLER: text="👤 اختر هدفك بصمت:"; cp="ng"
    elif role==RoleName.MAID: text="🔮 اختر لاعباً لكشف دوره:"; cp="nm"
    elif role==RoleName.CHEF: text="☠ اختر لاعباً لتسميمه:"; cp="nch"
    elif role==RoleName.THIEF:
        if player.thief_used: return
        text="🎭 اختر لاعباً لسرقة دوره:"; cp="nt"
    elif role==RoleName.POLICE: text="🔍 اختر لاعباً للتحقيق:"; cp="np"
    elif role==RoleName.DOORMAN:
        if player.doorman_used: return
        kb=InlineKeyboardMarkup([[InlineKeyboardButton("نعم، هدنة",callback_data=f"nd_{g.chat_id}_y")],[InlineKeyboardButton("لا",callback_data=f"nd_{g.chat_id}_n")]])
        await sdm(bot,player.user_id,"🚫 هل تعلن هدنة هذه الجولة؟",reply_markup=kb); return
    elif role==RoleName.NEIGHBOR: text="👁 اختر لاعباً لزيارته:"; cp="nn"
    elif role==RoleName.FOREST_GUARD:
        if g.fog: await sdm(bot,player.user_id,"الضباب يمنعك من الحماية هذه الليلة."); return
        targets=[p for p in targets if p.user_id!=g.guard_last]
        if not targets: return
        text="🛡 اختر لاعباً لحمايته:"; cp="nfg"
    elif role==RoleName.BATMAN:
        if player.batman_bullets<=0: return
        text=f"🎯 اختر هدفك ({player.batman_bullets} طلقة متبقية):"; cp="nb"
    elif role==RoleName.WITCH: text="⛓ اختر اللاعب الأول للربط:"; cp="nw1"
    elif role==RoleName.DRACULA:
        targets=[p for p in targets if not p.is_vampire and p.role!=RoleName.DRACULA]
        if not targets: return
        text="🦇 اختر لاعباً لتحويله:"; cp="ndr"
    else: return
    btns=[]; row=[]
    for i,t in enumerate(targets):
        row.append(InlineKeyboardButton(t.name,callback_data=f"{cp}_{g.chat_id}_{t.user_id}"))
        if len(row)==2 or i==len(targets)-1: btns.append(row); row=[]
    btns.append([InlineKeyboardButton("تخطي",callback_data=f"{cp}_{g.chat_id}_skip")])
    await sdm(bot,player.user_id,text,reply_markup=InlineKeyboardMarkup(btns))

# ── Night Callback ──
async def night_cb(update,context):
    q=update.callback_query; await q.answer(); d=q.data
    prefixes={"nc_":"nc","ng_":"ng","nm_":"nm","nch_":"nch","nt_":"nt","np_":"np","nd_":"nd","nn_":"nn","nfg_":"nfg","nb_":"nb","nw1_":"nw1","nw2_":"nw2","ndr_":"ndr"}
    at=None; rest=None
    for pf,a in prefixes.items():
        if d.startswith(pf): at=a; rest=d[len(pf):]; break
    if not at: return
    try:
        rp=rest.split("_"); cid=int(rp[0]); tv=rp[1]
        g=gm.get(cid)
        if not g or g.phase!=Phase.NIGHT: await q.edit_message_text("انتهى الوقت."); return
        uid=q.from_user.id; p=g.get_player(uid)
        if not p or not p.alive: return
        ak=f"{at}_{uid}"
        if ak in g.night_actions and at!="nw1": await q.edit_message_text("قررت بالفعل."); return
        if tv=="skip" or tv=="n": g.night_actions[ak]="skip"; await q.edit_message_text("تم التخطي."); return
        if tv=="y" and at=="nd":
            g.night_actions[ak]="truce"; g.truce=True; p.doorman_used=True
            g.log("night","هدنة",p.name,""); await q.edit_message_text("تم تفعيل الهدنة."); return
        tid=int(tv); tgt=g.get_player(tid)
        if at=="nc": g.night_actions[ak]=tid; g.log("night","قتل",p.name,tgt.name if tgt else "?"); await q.edit_message_text(f"🗡 هدفك: *{tgt.name if tgt else '?'}*",parse_mode="Markdown")
        elif at=="ng": g.night_actions[ak]=tid; g.log("night","قتل شبح",p.name,tgt.name if tgt else "?"); await q.edit_message_text(f"👤 هدفك: *{tgt.name if tgt else '?'}*",parse_mode="Markdown")
        elif at=="nm":
            g.night_actions[ak]=tid
            if tgt:
                if tgt.role==RoleName.GHOST_KILLER:
                    fk=random.choice([RoleName.PAINTER,RoleName.CHIEF,RoleName.NEIGHBOR]); rd=ROLE_DEFS[fk]
                    await q.edit_message_text(f"🔮 *{tgt.name}*: {rd.emoji} {rd.display}",parse_mode="Markdown")
                else: p.investigations+=1; await q.edit_message_text(f"🔮 *{tgt.name}*: {tgt.display_role}",parse_mode="Markdown")
        elif at=="nch": g.night_actions[ak]=tid; await q.edit_message_text(f"☠ تم تسميم *{tgt.name if tgt else '?'}*",parse_mode="Markdown")
        elif at=="nt":
            g.night_actions[ak]=tid; p.thief_used=True
            if tgt: sr=tgt.role; tgt.role=RoleName.PAINTER; p.role=sr; await q.edit_message_text(f"🎭 سرقت دور *{tgt.name}*\nدورك الجديد: {p.display_role}",parse_mode="Markdown")
        elif at=="np":
            g.night_actions[ak]=tid
            if tgt:
                ik=tgt.team in (Team.EVIL,Team.DRACULA)
                if tgt.role==RoleName.GHOST_KILLER: ik=False
                r="🔴 مشتبه به" if ik else "🟢 بريء"
                if ik: p.investigations+=1
                await q.edit_message_text(f"🔍 *{tgt.name}*: {r}",parse_mode="Markdown")
        elif at=="nn": g.night_actions[ak]=tid; p.visited_target=tid; await q.edit_message_text(f"👁 ستزورين *{tgt.name if tgt else '?'}*",parse_mode="Markdown")
        elif at=="nfg":
            g.night_actions[ak]=tid
            if tgt: tgt.protected=True; g.guard_last=tid; await q.edit_message_text(f"🛡 تحمي *{tgt.name}*",parse_mode="Markdown")
        elif at=="nb":
            g.night_actions[ak]=tid; p.batman_bullets-=1
            await q.edit_message_text(f"🎯 أطلقت النار على *{tgt.name if tgt else '?'}* (متبقي: {p.batman_bullets})",parse_mode="Markdown")
        elif at=="nw1":
            g.night_actions[f"w1_{uid}"]=tid
            t2=[x for x in g.alive_players if x.user_id!=uid and x.user_id!=tid]
            if t2:
                btns=[]; row=[]
                for i,t in enumerate(t2):
                    row.append(InlineKeyboardButton(t.name,callback_data=f"nw2_{cid}_{t.user_id}"))
                    if len(row)==2 or i==len(t2)-1: btns.append(row); row=[]
                btns.append([InlineKeyboardButton("تخطي",callback_data=f"nw2_{cid}_skip")])
                await q.edit_message_text(f"⛓ الأول: *{tgt.name if tgt else '?'}*\nاختر الثاني:",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(btns))
        elif at=="nw2":
            ft=g.night_actions.get(f"w1_{uid}")
            if ft: g.witch_links[ft]=tid; g.witch_links[tid]=ft; t1=g.get_player(ft); await q.edit_message_text(f"⛓ تم الربط: *{t1.name if t1 else '?'}* + *{tgt.name if tgt else '?'}*",parse_mode="Markdown")
        elif at=="ndr": g.night_actions[ak]=tid; await q.edit_message_text(f"🦇 ستحوّل *{tgt.name if tgt else '?'}*",parse_mode="Markdown")
    except Exception as e: logger.error(f"Night cb err:{e}",exc_info=True)

# ── Resolve Night ──
async def resolve_night(bot,g):
    # Execute PENDING actions (from last night), not current ones
    pa=g.pending_actions  # actions chosen LAST night
    na=g.night_actions     # actions chosen THIS night
    killed=[]; msgs=[]
    if not g.storm:
        for k,v in pa.items():
            if k.startswith("nc_") and v!="skip" and isinstance(v,int):
                t=g.get_player(v)
                if t and t.alive and not t.protected:
                    if t.role==RoleName.DOG and not t.dog_transformed: t.dog_transformed=True; msgs.append("في عمق الليل… الكلب تحوّل إلى ذئب.")
                    else: killed.append(v)
                    for p in g.players.values():
                        if p.role==RoleName.CRIMINAL and p.alive: p.kills+=1
                elif t and t.protected:
                    for p in g.players.values():
                        if p.role==RoleName.FOREST_GUARD and p.alive: p.saves+=1
        for k,v in pa.items():
            if k.startswith("ng_") and v!="skip" and isinstance(v,int):
                t=g.get_player(v)
                if t and t.alive and not t.protected and v not in killed:
                    if t.role==RoleName.DOG and not t.dog_transformed: t.dog_transformed=True; msgs.append("الكلب تحوّل إلى ذئب في الظلام.")
                    else: killed.append(v)
        for k,v in pa.items():
            if k.startswith("nb_") and v!="skip" and isinstance(v,int):
                t=g.get_player(v)
                if t and t.alive and v not in killed: killed.append(v)
    else:
        await sgif(bot,g.chat_id,"storm","⛈ *العاصفة أوقفت كل شيء!*\nلا قتل هذه الليلة… الجميع نجوا.",parse_mode="Markdown")
    # Poison (delayed: last night's poison kills now)
    for k,v in pa.items():
        if k.startswith("nch_") and v!="skip" and isinstance(v,int):
            t=g.get_player(v)
            if t and t.alive and v not in killed and not t.protected: killed.append(v)
    # Dracula (delayed)
    for k,v in pa.items():
        if k.startswith("ndr_") and v!="skip" and isinstance(v,int):
            t=g.get_player(v)
            if t and t.alive and v not in killed:
                t.is_vampire=True
                await sdm(bot,t.user_id,"*تحوّلت إلى مصاص دماء.*\nأنت مع دراكولا الآن.",parse_mode="Markdown")
    # Protection uses THIS night's choice (immediate)
    # (already applied in night_cb when player chooses)
    # Neighbor check uses THIS night's actions (immediate info)
    for p in g.alive_players:
        if p.visited_target:
            t=g.get_player(p.visited_target)
            if t:
                left=any(k.endswith(f"_{t.user_id}") and v!="skip" for k,v in na.items())
                await sdm(bot,p.user_id,f"👁 *{t.name}*: {'لم يكن في بيته' if left else 'كان في بيته'}",parse_mode="Markdown")
    # Maid/Police results already shown immediately in night_cb (no delay needed for info roles)
    # Witch links from pending
    for k,v in pa.items():
        if k.startswith("w1_"):
            uid=int(k.split("_")[1])
            w2k=f"nw2_{uid}"
            # find second target in pending
            for k2,v2 in pa.items():
                if k2.startswith("nw2_") and isinstance(v2,int):
                    if v and isinstance(v,int): g.witch_links[v]=v2; g.witch_links[v2]=v
    # Witch link kills
    extra=[]
    for uid in killed:
        if uid in g.witch_links:
            lu=g.witch_links[uid]; lp=g.get_player(lu)
            if lp and lp.alive and lu not in killed and lu not in extra: extra.append(lu)
    killed.extend(extra)
    # Save THIS night's actions as pending for NEXT night
    g.pending_actions=dict(na)
    uq=list(dict.fromkeys(killed))
    for uid in uq:
        p=g.get_player(uid)
        if p: p.alive=False
    if not uq and not g.storm:
        await ssend(bot,g.chat_id,"☀ أشرقت الشمس…\n😳 الجميع على قيد الحياة!\n🛡 أحدهم نجا بأعجوبة.")
    else:
        for uid in uq:
            p=g.get_player(uid)
            if p:
                dm=DEATH_MSGS.get(p.role,"رحل عنا…")
                kt="generic"
                for k,v in g.night_actions.items():
                    if isinstance(v,int) and v==uid:
                        if "nc" in k: kt="criminal"
                        elif "ng" in k: kt="ghost"
                        elif "nb" in k: kt="batman"
                        elif "pp" in k or "nch" in k: kt="poison"
                await sgif(bot,g.chat_id,f"death_{kt}",f"💀 *جثة عُثر عليها*\n\n{p.tag}\n🎭 {p.display_role}\n\n{dm}",parse_mode="Markdown")
                dmt={"criminal":"*قتلك المجرم.*","ghost":"*قتلك الشبح بصمت.*","batman":"*أطلق عليك القنّاص.*","poison":"*مت مسمومًا.*","generic":"*لقد قُتلت.*"}
                await sgif_dm(bot,p.user_id,f"death_{kt}",f"{dmt.get(kt,dmt['generic'])}\n\nدورك كان: {p.display_role}\nتابع كمتفرج.",parse_mode="Markdown")
                g.log("night","مقتل",kt,p.name); await asyncio.sleep(2)
    for m in msgs: await sgif(bot,g.chat_id,"dog_transform",m); await asyncio.sleep(2)
    w=g.check_win()
    if w: await announce_win(bot,g,w); return
    await asyncio.sleep(3); g._task=asyncio.create_task(run_day(bot,g))

# ══════════════════════════════════════════════
# DAY
async def run_day(bot,g):
    try:
        g.phase=Phase.DAY
        at="\n".join(f"  ☑ {p.tag}" for p in g.alive_players)
        await sgif(bot,g.chat_id,"day",f"☀ *الجولة {g.round_num} — نهار*\n\n{random.choice(DAY_MESSAGES)}\n\n👥 *الأحياء* ({len(g.alive_players)}):\n{at}\n\n⏳ {Game.DISC_DUR} ثانية للنقاش…",parse_mode="Markdown")
        for p in g.alive_players:
            if p.role in (RoleName.CRIMINAL, RoleName.GHOST_KILLER, RoleName.BATMAN):
                await sdm(bot,p.user_id,"*بقيت دقيقة قبل التصويت…*\nاختر هدفك الآن إن لم تفعل.",parse_mode="Markdown")
        await asyncio.sleep(Game.DISC_DUR//2)
        await ssend(bot,g.chat_id,random.choice(SUSPENSE))
        await asyncio.sleep(Game.DISC_DUR//2)
        if g.truce:
            await sgif(bot,g.chat_id,"truce","🚫 *هدنة!*\nلا تصويت هذه الجولة.\n🌙 استعدوا للّيل القادم.")
            await asyncio.sleep(5); g._task=asyncio.create_task(run_night(bot,g)); return
        await run_vote(bot,g)
    except asyncio.CancelledError: pass
    except Exception as e: logger.error(f"Day err:{e}",exc_info=True)

# ══════════════════════════════════════════════
# VOTING (Private DM)
# ══════════════════════════════════════════════
async def run_vote(bot,g):
    try:
        g.phase=Phase.VOTING; g.votes={}; alive=g.alive_players
        g.vote_expected={p.user_id for p in alive}
        g.vote_closed=False
        g.vote_event=asyncio.Event()
        await sgif(bot,g.chat_id,"vote","⚖ *بدأ التصويت*\n\n📩 أزرار التصويت في الخاص.\n⏳ إذا اكتملت الأصوات ينتهي التصويت فوراً.\n🔒 التصويت سري… لكن النتيجة تُعلن للجميع.",parse_mode="Markdown")
        for p in alive:
            tgts=[x for x in alive if x.user_id!=p.user_id]; btns=[]; row=[]
            for i,t in enumerate(tgts):
                row.append(InlineKeyboardButton(t.name,callback_data=f"v_{g.chat_id}_{t.user_id}"))
                if len(row)==2 or i==len(tgts)-1: btns.append(row); row=[]
            btns.append([InlineKeyboardButton("امتناع",callback_data=f"v_{g.chat_id}_skip")])
            await sdm(bot,p.user_id,f"*صوّت الآن*\nاختر من تريد إعدامه.\n⏳ {Game.VOTE_DUR} ثانية.",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(btns))
        try:
            await asyncio.wait_for(g.vote_event.wait(), timeout=Game.VOTE_DUR)
        except asyncio.TimeoutError:
            pass
        g.vote_closed=True
        for p in alive:
            if p.role==RoleName.MADMAN and p.alive and p.user_id not in g.votes:
                ps=[t for t in alive if t.user_id!=p.user_id]
                if ps: g.votes[p.user_id]=random.choice(ps).user_id
        if g.votes:
            vr="📋 *ملخص التصويت:*\n\n"
            for vi,ti in g.votes.items():
                vt=g.get_player(vi)
                if ti==-1: vr+=f"⚪ {vt.tag} امتنع\n"
                else: tt=g.get_player(ti); vr+=f"🗳 {vt.tag} صوّت على {tt.tag if tt else '?'}\n"
            for p in alive:
                if p.user_id not in g.votes: vr+=f"❌ {p.tag} لم يصوّت\n"
            await ssend(bot,g.chat_id,vr,parse_mode="Markdown")
        await resolve_votes(bot,g)
    except asyncio.CancelledError: pass
    except Exception as e: logger.error(f"Vote err:{e}",exc_info=True)

async def vote_cb(update,context):
    q=update.callback_query; d=q.data
    if not d.startswith("v_"): return
    pp=d.split("_"); cid=int(pp[1]); tv=pp[2]
    g=gm.get(cid)
    if not g or g.phase!=Phase.VOTING or g.vote_closed: await q.answer("انتهى التصويت.",show_alert=True); return
    vid=q.from_user.id; vt=g.get_player(vid)
    if not vt: await q.answer("لست في اللعبة.",show_alert=True); return
    if not vt.alive: await q.answer("أنت خارج اللعبة.",show_alert=True); return
    if vid in g.votes: await q.answer("صوّتت بالفعل.",show_alert=True); return
    if vt.role==RoleName.MADMAN:
        ps=[p for p in g.alive_players if p.user_id!=vid]
        if ps:
            rt=random.choice(ps)
            g.votes[vid]=rt.user_id
            await q.edit_message_text("🃏 تم التصويت عشوائياً.")
            await ssend(context.bot,cid,f"🗳 {vt.tag} صوّت على {rt.tag}",parse_mode="Markdown")
            if g.vote_expected and g.vote_expected.issubset(g.votes.keys()) and g.vote_event and not g.vote_event.is_set():
                g.vote_event.set()
        return
    if tv=="skip":
        g.votes[vid]=-1
        await q.edit_message_text("تم الامتناع.")
        await ssend(context.bot,cid,f"⚪ {vt.tag} امتنع عن التصويت",parse_mode="Markdown")
    else:
        tid=int(tv); g.votes[vid]=tid; tgt=g.get_player(tid)
        await q.edit_message_text(f"☑ صوّتت ضد *{tgt.name if tgt else '?'}*\nانتظر النتائج…",parse_mode="Markdown")
        await ssend(context.bot,cid,f"🗳 {vt.tag} صوّت على {tgt.tag if tgt else '?'}",parse_mode="Markdown")
    if g.vote_expected and g.vote_expected.issubset(g.votes.keys()) and g.vote_event and not g.vote_event.is_set():
        g.vote_event.set()


async def resolve_votes(bot,g):
    if not g.votes:
        await ssend(bot,g.chat_id,"⚖ لم يصوّت أحد.\n🌙 استعدوا للّيل…")
        g._task=asyncio.create_task(run_night(bot,g)); return
    vc={}
    for vi,ti in g.votes.items():
        if ti!=-1: vc[ti]=vc.get(ti,0)+1
    if not vc:
        await ssend(bot,g.chat_id,"⚖ كل الأصوات امتناع.\n🌙 استعدوا للّيل…")
        g._task=asyncio.create_task(run_night(bot,g)); return
    mx=max(vc.values()); tops=[u for u,c in vc.items() if c==mx]
    slines=[]
    for u,c in sorted(vc.items(),key=lambda x:-x[1]):
        p=g.get_player(u)
        if p: bar="▓"*c+"░"*(len(g.alive_players)-c); slines.append(f"  {p.tag}: {bar} ({c})")
    summary="\n".join(slines)
    if len(tops)>1:
        await ssend(bot,g.chat_id,f"⚖ *نتائج التصويت*\n\n{summary}\n\n⚖ تعادل — لا إعدام اليوم.\n🌙 استعدوا للّيل…",parse_mode="Markdown")
        g._task=asyncio.create_task(run_night(bot,g)); return
    tid=tops[0]; tgt=g.get_player(tid)
    if not tgt: g._task=asyncio.create_task(run_night(bot,g)); return
    # Grocer
    if tgt.role==RoleName.GROCER and tgt.alive:
        tgt.alive=False
        await ssend(bot,g.chat_id,f"⚖ *نتائج التصويت*\n\n{summary}\n\n🎪 *مفاجأة!*\nأعدمتم صاحب البقالة {tgt.tag}\nيفوز وحده… والبقية يخسرون.",parse_mode="Markdown")
        await announce_win(bot,g,"grocer",tgt.name); return
    # Prince
    if tgt.role==RoleName.PRINCE and tgt.prince_lives>0:
        tgt.prince_lives-=1
        await ssend(bot,g.chat_id,f"⚖ *نتائج التصويت*\n\n{summary}\n\n👑 الأمير {tgt.tag} نجا من الإعدام.\n🌙 استعدوا للّيل…",parse_mode="Markdown")
        g._task=asyncio.create_task(run_night(bot,g)); return
    # Last words
    g.phase=Phase.LAST_WORDS
    await ssend(bot,g.chat_id,f"⚖ *نتائج التصويت*\n\n{summary}\n\n⏳ {tgt.tag} سيُعدم.\n🗣 كلمة أخيرة… {Game.LAST_WORDS_DUR} ثانية.",parse_mode="Markdown")
    g.log("vote","محكوم",tgt.name,"")
    await asyncio.sleep(Game.LAST_WORDS_DUR)
    tgt.alive=False; dm=DEATH_MSGS.get(tgt.role,"رحل…")
    await sgif(bot,g.chat_id,"death_vote",f"⚖ *تم الإعدام*\n\n💀 {tgt.tag}\n{tgt.display_role}\n\n{dm}",parse_mode="Markdown")
    g.log("vote","إعدام","",f"{tgt.name} ({tgt.display_role})")
    if tgt.user_id in g.witch_links:
        lu=g.witch_links[tgt.user_id]; lp=g.get_player(lu)
        if lp and lp.alive:
            lp.alive=False; ld=DEATH_MSGS.get(lp.role,"رحل…")
            await asyncio.sleep(2)
            await ssend(bot,g.chat_id,f"⛓ *الرابط!*\nمات أيضاً: {lp.tag}\n{lp.display_role}\n\n{ld}",parse_mode="Markdown")
    w=g.check_win()
    if w: await asyncio.sleep(3); await announce_win(bot,g,w); return
    await asyncio.sleep(3); g._task=asyncio.create_task(run_night(bot,g))

# ══════════════════════════════════════════════
# WINNER
# ══════════════════════════════════════════════
async def announce_win(bot,g,winner,gn=""):
    g.phase=Phase.GAME_OVER
    if winner=="village": txt="🏆 *انتهت اللعبة*\n\n🛡 انتصر الأبرياء!\nتم القضاء على الأشرار… السلام عاد للقصر."; gk="win_village"; wt=Team.VILLAGER
    elif winner=="evil": txt="💀 *انتهت اللعبة*\n\n😈 انتصر الأشرار!\nالظلام سيطر على القصر… لا أحد نجا."; gk="win_evil"; wt=Team.EVIL
    elif winner=="dracula": txt="🦇 *انتهت اللعبة*\n\n🩸 انتصر دراكولا!\nالليل لن ينتهي أبداً… مرحباً بالظلام الأبدي."; gk="win_dracula"; wt=Team.DRACULA
    elif winner=="grocer": txt=f"🎪 *انتهت اللعبة*\n\nفاز *{gn}* وحده!\nأعدمتم صاحب البقالة… والبقية خسروا."; gk="win_evil"; wt=Team.SOLO
    else: txt="🏁 *انتهت اللعبة*"; gk="win_village"; wt=None
    for p in g.players.values():
        if winner=="grocer":
            update_stat(p.user_id,p.name,"wins" if p.role==RoleName.GROCER else "losses")
        elif wt and p.team==wt: update_stat(p.user_id,p.name,"wins")
        else: update_stat(p.user_id,p.name,"losses")
        if p.alive: update_stat(p.user_id,p.name,"survived")
        if p.kills>0: update_stat(p.user_id,p.name,"kills",p.kills)
    mvp=g.calc_mvp(); mt=""
    if mvp: update_stat(mvp.user_id,mvp.name,"mvp"); mt=f"\n\n⭐ *MVP:* {mvp.tag} ({mvp.display_role})"
    rt="\n".join(f"{'  💀' if not p.alive else '  ☑'} {p.tag} — {p.display_role}" for p in g.players.values())
    # Log summary
    ls=""
    ke=[e for e in g.log_entries if e.action in ("مقتل","إعدام","حماية","تحويل","قمر دموي","هدنة")]
    if ke:
        ls="\n\n📜 *ملخص الأحداث:*\n"
        for e in ke[-8:]: ls+=f"  ر{e.rnd}: {e.action}"; ls+=f" ({e.actor})" if e.actor else ""; ls+=f" → {e.target}" if e.target else ""; ls+="\n"
    await sgif(bot,g.chat_id,gk,f"{txt}\n\n🎭 *الأدوار:*\n{rt}{mt}{ls}\n\n📊 /stats · 🏆 /leaderboard\n🔄 /start للعبة جديدة",parse_mode="Markdown")
    gm.remove(g.chat_id)

# ── Router ──
async def cb_router(update,context):
    q=update.callback_query
    if not q or not q.data: return
    d=q.data
    if any(d.startswith(p) for p in ["nc_","ng_","nm_","nch_","nt_","np_","nd_","nn_","nfg_","nb_","nw1_","nw2_","ndr_"]): await night_cb(update,context)
    elif d.startswith("v_"): await vote_cb(update,context)
    elif d.startswith("join_") or d.startswith("sg_") or d.startswith("cg_"): await join_cb(update,context)
    else: await q.answer("غير معروف.",show_alert=True)

def main():
    TOKEN="8712365309:AAExk4vAUogk2L5wgozuE-cSq3TdEHcOSWg"
    app=Application.builder().token(TOKEN).build()
    async def post_init(application):
        from telegram import BotCommand
        await application.bot.set_my_commands([BotCommand("start","لعبة جديدة"),BotCommand("join","انضم"),BotCommand("startgame","ابدأ اللعبة"),BotCommand("players","اللاعبون"),BotCommand("alive","الأحياء"),BotCommand("role","دورك"),BotCommand("stats","إحصائياتك"),BotCommand("leaderboard","المتصدرين"),BotCommand("endgame","إنهاء اللعبة")])
        logger.info("✅ Commands registered!")
    app.post_init=post_init
    for cmd,fn in [("start",cmd_start),("join",cmd_join),("startgame",cmd_startgame),("endgame",cmd_endgame),("players",cmd_players),("alive",cmd_alive),("role",cmd_role),("stats",cmd_stats),("leaderboard",cmd_leaderboard)]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CallbackQueryHandler(cb_router))
    logger.info("🏰 Ghosts Palace Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__": main()
