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

GIFS={"start":"https://media.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif","night":"https://media.giphy.com/media/3o7TKwmnDgQb5jemjK/giphy.gif","day":"https://media.giphy.com/media/26BRBKqUiq586bRVm/giphy.gif","vote":"https://media.giphy.com/media/l2JejfEHGGBRhifi8/giphy.gif","death_criminal":"https://media.giphy.com/media/3o72F8t9TDi2xVnxOE/giphy.gif","death_ghost":"https://media.giphy.com/media/l2JejfEHGGBRhifi8/giphy.gif","death_poison":"https://media.giphy.com/media/3oEjHGr1Fhz0kyv8Ig/giphy.gif","death_batman":"https://media.giphy.com/media/l3q2XhfQ8oCkm1Ts4/giphy.gif","death_generic":"https://media.giphy.com/media/xT0xeJpnrWC3XWblEk/giphy.gif","death_vote":"https://media.giphy.com/media/3o72F8t9TDi2xVnxOE/giphy.gif","win_village":"https://media.giphy.com/media/26u4cqiYI30juCOGY/giphy.gif","win_evil":"https://media.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif","win_dracula":"https://media.giphy.com/media/l2JejfEHGGBRhifi8/giphy.gif","truce":"https://media.giphy.com/media/26BRBKqUiq586bRVm/giphy.gif","dog_transform":"https://media.giphy.com/media/3o7TKwmnDgQb5jemjK/giphy.gif","blood_moon":"https://media.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif","storm":"https://media.giphy.com/media/3o7TKwmnDgQb5jemjK/giphy.gif"}


BASE_DIR=os.path.dirname(os.path.abspath(__file__))
START_IMAGE_PATH=os.path.join(BASE_DIR,"start_cover.jpg")

NIGHT_MESSAGES=["🌙 حلّ الليل…\n🌲 الرياح تعصف بين الأشجار…\n👁️ هناك من يراقب… وهناك من يتحرك في الظلام.\n🔒 الأبواب أُغلقت… والأنفاس محبوسة.\n🎭 أصحاب الأدوار الليلية… الوقت لكم الآن.","🌑 الظلام يبتلع القرية…\n🦉 صوت بومة يكسر الصمت…\n🐾 خطوات خفية تقترب…\n💨 رائحة الخوف تملأ المكان.\n🎭 حان وقت الأدوار الليلية.","🌙 القمر اكتمل الليلة…\n🕯️ شمعة وحيدة تضيء النافذة…\n👤 ظل يتحرك بين البيوت…\n🔇 حتى الريح توقفت عن الهمس.\n🎭 افعلوا ما يجب فعله… قبل الفجر.","🌌 النجوم تختبئ خلف الغيوم…\n🐺 عواء بعيد يقشعرّ الأبدان…\n🚪 باب يُفتح… ثم يُغلق بصمت…\n😰 أحدهم لن يرى الصباح.\n🎭 استخدموا قدراتكم بحكمة."]
DAY_MESSAGES=["🌅 أشرقت الشمس…\n☀️ ضوء النهار يكشف ما حاول الليل إخفاءه.\n🗣️ حان وقت النقاش!","🌤️ الفجر يطرد الظلام…\n🐓 صياح الديك يعلن يومًا جديدًا…\n👀 لكن بعض الوجوه مفقودة.\n🗣️ ابدأوا النقاش!","☀️ الشمس تبزغ من جديد…\n😓 التوتر يسيطر على القرية…\n🤔 من نثق به اليوم?\n🗣️ وقت الحقيقة!"]
SUSPENSE=["😰 التوتر يزداد في القرية…","🌲 شيء ما يتحرك بين الأشجار…","👁️ هل لاحظتم تلك النظرات المريبة?","🤫 الصمت أحيانًا أخطر من الكلام…","⚡ الأجواء مشحونة… شيء سيحدث!","🎭 الأقنعة ستسقط عاجلاً أم آجلاً…","🐾 آثار أقدام غريبة بالقرب من بيت أحدهم…"]
RANDOM_EVENTS={"blood_moon":{"name":"🔴 قمر دموي!","desc":"القمر الدموي يكشف هوية لاعب عشوائي!","chance":0.12},"storm":{"name":"⛈️ عاصفة مدمرة!","desc":"العاصفة منعت القتل هذه الليلة!","chance":0.08},"fog":{"name":"🌫️ ضباب كثيف!","desc":"الضباب يمنع الحارس من الحماية!","chance":0.10}}

@dataclass
class RoleDef:
    name:RoleName; display:str; emoji:str; team:Team; has_night_action:bool; description:str; priority:int

ROLE_DEFS={
    RoleName.CRIMINAL:RoleDef(RoleName.CRIMINAL,"المجرم","🔪",Team.EVIL,True,"يقتل لاعبًا كل ليلة",1),
    RoleName.GHOST_KILLER:RoleDef(RoleName.GHOST_KILLER,"الشبح القاتل","👻",Team.EVIL,True,"يقتل لاعبًا + صعب اكتشافه",2),
    RoleName.MAID:RoleDef(RoleName.MAID,"الخادمة (العرّافة)","🤵‍♀️",Team.VILLAGER,True,"تكشف دور لاعب",10),
    RoleName.CHEF:RoleDef(RoleName.CHEF,"الشيف","🧑‍🍳",Team.EVIL,True,"يسمم لاعبًا (يموت الليلة التالية)",3),
    RoleName.THIEF:RoleDef(RoleName.THIEF,"اللص","🥷",Team.VILLAGER,True,"يسرق دور لاعب (مرة واحدة)",4),
    RoleName.POLICE:RoleDef(RoleName.POLICE,"الشرطي","👮‍♀️",Team.VILLAGER,True,"يعرف إن كان اللاعب قاتلًا أم لا",11),
    RoleName.DOORMAN:RoleDef(RoleName.DOORMAN,"البواب","🧑‍✈️",Team.VILLAGER,True,"يوقف التصويت (هدنة) – مرة واحدة",12),
    RoleName.NEIGHBOR:RoleDef(RoleName.NEIGHBOR,"الجارة","😘",Team.VILLAGER,True,"تزور لاعبًا وتعرف إن كان خرج من بيته",13),
    RoleName.FOREST_GUARD:RoleDef(RoleName.FOREST_GUARD,"حارس الغابة","🧙‍♀️",Team.VILLAGER,True,"يحمي لاعبًا (لا يكرر نفس الشخص)",5),
    RoleName.MADMAN:RoleDef(RoleName.MADMAN,"مجنون الغابة","🤡",Team.VILLAGER,False,"تصويته عشوائي",99),
    RoleName.GROCER:RoleDef(RoleName.GROCER,"صاحب البقالة المهجورة","🧌",Team.SOLO,False,"إذا تم التصويت عليه يفوز وحده",99),
    RoleName.BATMAN:RoleDef(RoleName.BATMAN,"باتمان","🦹‍♂️",Team.VILLAGER,True,"لديه طلقتان قتل",6),
    RoleName.WITCH:RoleDef(RoleName.WITCH,"الساحرة","🧝‍♀️",Team.VILLAGER,True,"تربط لاعبين (يموتان معًا)",7),
    RoleName.PRINCE:RoleDef(RoleName.PRINCE,"الأمير","🫅",Team.VILLAGER,False,"يحتاج تصويتين للإعدام",99),
    RoleName.PAINTER:RoleDef(RoleName.PAINTER,"الرسام","👩‍🎨",Team.VILLAGER,False,"بدون قدرة خاصة",99),
    RoleName.CHIEF:RoleDef(RoleName.CHIEF,"مختار الغابة","💂‍♂️",Team.VILLAGER,False,"بدون قدرة خاصة",99),
    RoleName.DRACULA:RoleDef(RoleName.DRACULA,"دراكولا","🧛",Team.DRACULA,True,"يحول لاعبًا إلى مصاص دماء",8),
    RoleName.DOG:RoleDef(RoleName.DOG,"الكلب","🐶",Team.VILLAGER,False,"إذا تم استهدافه يتحول لذئب",99),
}

DEATH_MSGS={RoleName.MAID:"🤵‍♀️ كنت الخادمة…\n🔍 امتلكت الحقيقة… لكن لم تنقذ نفسك.",RoleName.CHEF:"🧑‍🍳 كنت الشيف…\n☠️ السم كان سلاحك.",RoleName.THIEF:"🥷 كنت اللص..\n😔 لم تنجُ",RoleName.POLICE:"👮‍♀️ كنت الشرطي…\n🔎 بحثت عن الحقيقة…",RoleName.DOORMAN:"🧑‍✈️ كنت البواب…\n🛑 حاولت إيقاف الفوضى…",RoleName.NEIGHBOR:"😘 كنت الجارة…\n🏠 اقتربت من الجميع…",RoleName.FOREST_GUARD:"🧙‍♀️ كنت حارس الغابة…\n🛡️ حميت الآخرين…",RoleName.MADMAN:"🤡 كنت مجنون الغابة…\n🎲 نشرت الفوضى…",RoleName.GROCER:"🧌 كنت صاحب البقالة…",RoleName.BATMAN:"🦹‍♂️ كنت باتمان…\n🦇 حتى الأبطال يسقطون.",RoleName.WITCH:"🧝‍♀️ كنت الساحرة…\n✨ السحر لم يحمِك.",RoleName.DOG:"🐶 كنت الكلب…",RoleName.PRINCE:"🫅 كنت الأمير…\n👑 حتى التاج لم يحمِك.",RoleName.PAINTER:"👩‍🎨 كنت الرسام…",RoleName.CHIEF:"💂‍♂️ كنت مختار الغابة…",RoleName.DRACULA:"🧛 كنت دراكولا…\n🩸 حتى مصاصو الدماء يموتون.",RoleName.CRIMINAL:"🔪 كنت المجرم…\n😈 سقطت أخيرًا.",RoleName.GHOST_KILLER:"👻 كنت الشبح القاتل…\n🌑 حتى الأشباح تتلاشى."}

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
    user_id:int; name:str; role:Optional[RoleName]=None; alive:bool=True
    poisoned:bool=False; protected:bool=False; prince_lives:int=1
    batman_bullets:int=2; doorman_used:bool=False; thief_used:bool=False
    is_vampire:bool=False; dog_transformed:bool=False; visited_target:Optional[int]=None
    kills:int=0; saves:int=0; investigations:int=0
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
        if self.is_vampire: x=" 🧛"
        if self.dog_transformed: x=" 🐺"
        return f"{rd.emoji} {rd.display}{x}"

class Game:
    MIN_PLAYERS=4; MAX_PLAYERS=18; NIGHT_DUR=90; VOTE_DUR=90; DISC_DUR=60; LAST_WORDS_DUR=20
    def __init__(self,cid):
        self.chat_id=cid; self.phase=Phase.LOBBY; self.players:Dict[int,Player]={}
        self.round_num=0; self.night_actions:Dict[str,Any]={}; self.night_kills=[]
        self.guard_last=None; self.truce=False; self.votes:Dict[int,int]={}
        self.vote_msg_id=None; self.lobby_msg_id=None; self.witch_links:Dict[int,int]={}
        self._task=None; self.log_entries:List[LogEntry]=[]; self.event=None
        self.storm=False; self.fog=False
        self.vote_event=None; self.vote_closed=False; self.vote_expected=set()
    def add_player(self,uid,name):
        if uid in self.players or self.phase!=Phase.LOBBY or len(self.players)>=self.MAX_PLAYERS: return False
        self.players[uid]=Player(user_id=uid,name=name); return True
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
            del self.games[cid]

gm=GameManager()

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
    pl="".join(f"  {i}. {p.name}\n" for i,p in enumerate(g.players.values(),1)) or "  ⏳ لا يوجد لاعبين…\n"
    c=len(g.players); st="🟢 يمكن بدء اللعبة!" if c>=Game.MIN_PLAYERS else f"⏳ يحتاج {Game.MIN_PLAYERS-c} إضافيين"
    return f"🏰 *Ghosts Palace - 𝒉𝒂𝒗𝒂𝒏𝒂 𝑪𝒉𝒂𝒕🦩*\n━━━━━━━━━━━━━━━━━━━━\n\n🎭 *لعبة جديدة!*\n👻 من سيبقى حيًا?\n\n👥 *اللاعبون ({c}/{Game.MAX_PLAYERS}):*\n{pl}\n{st}\n━━━━━━━━━━━━━━━━━━━━"

def lobby_kb(g):
    c=len(g.players); b=[[InlineKeyboardButton("🎮 انضم للعبة!",callback_data=f"join_{g.chat_id}")]]
    if c>=Game.MIN_PLAYERS: b.append([InlineKeyboardButton("🚀 ابدأ اللعبة!",callback_data=f"sg_{g.chat_id}")])
    b.append([InlineKeyboardButton("❌ إلغاء",callback_data=f"cg_{g.chat_id}")]); return InlineKeyboardMarkup(b)

async def update_lobby(bot,g):
    if not g.lobby_msg_id: return
    try: await bot.edit_message_text(chat_id=g.chat_id,message_id=g.lobby_msg_id,text=lobby_text(g),parse_mode="Markdown",reply_markup=lobby_kb(g))
    except: pass

# ── Commands ──
async def cmd_start(update,context):
    if update.effective_chat.type=="private":
        await update.message.reply_text("🏰 *مرحبًا بك في Ghosts Palace!*\n━━━━━━━━━━━━━━━━━━━━\n\n👻 لعبة غموض وإثارة جماعية!\n\n📌 *كيف تلعب:*\n1️⃣ أضفني لمجموعة\n2️⃣ اكتب /start لفتح لعبة\n3️⃣ اللاعبين ينضمون بالزر\n4️⃣ ابدأ اللعبة واستمتع!\n\n🎮 /role /alive /stats /leaderboard\n\n⚠️ تأكد إنك بدأت محادثة معي!",parse_mode="Markdown"); return
    cid=update.effective_chat.id; ex=gm.get(cid)
    if ex and ex.phase!=Phase.GAME_OVER: await update.message.reply_text("⚠️ يوجد لعبة قائمة!"); return
    g=gm.create(cid)
    try:
        await send_start_cover(context.bot, cid, "👻 *الأشباح تستيقظ...*\n🏰 *القصر يفتح أبوابه...*\n\n🌑 استعدّوا لليلة طويلة داخل القصر.", parse_mode="Markdown")
    except Exception:
        pass
    await asyncio.sleep(1)
    m=await ssend(context.bot,cid,lobby_text(g),parse_mode="Markdown",reply_markup=lobby_kb(g))
    if m: g.lobby_msg_id=m.message_id

async def cmd_join(update,context):
    if update.effective_chat.type=="private": return
    g=gm.get(update.effective_chat.id)
    if not g or g.phase!=Phase.LOBBY: await update.message.reply_text("⚠️ لا توجد لعبة مفتوحة!"); return
    u=update.effective_user; name=u.first_name or u.username or f"U{u.id}"
    if g.add_player(u.id,name): await update_lobby(context.bot,g); await update.message.reply_text(f"✅ {name} انضم!")
    else: await update.message.reply_text("⚠️ منضم بالفعل أو ممتلئة!")

async def cmd_startgame(update,context):
    if update.effective_chat.type=="private": return
    cid=update.effective_chat.id; g=gm.get(cid)
    if not g or g.phase!=Phase.LOBBY: return
    if len(g.players)<Game.MIN_PLAYERS: await update.message.reply_text(f"⚠️ يحتاج {Game.MIN_PLAYERS} لاعبين!"); return
    try:
        if g.lobby_msg_id: await context.bot.edit_message_reply_markup(chat_id=cid,message_id=g.lobby_msg_id,reply_markup=None)
    except: pass
    await start_logic(context.bot,g,cid)

async def cmd_role(update,context):
    uid=update.effective_user.id
    for g in gm.games.values():
        p=g.get_player(uid)
        if p and p.role and g.phase not in (Phase.LOBBY,Phase.GAME_OVER):
            rd=p.role_def; tt={"villager":"الأبرياء 🛡️","evil":"الأشرار 😈","dracula":"دراكولا 🧛","solo":"وحيد 🧌"}
            extra=""
            if p.is_vampire: extra="\n🧛 تم تحويلك لمصاص دماء!"
            if p.dog_transformed: extra="\n🐺 تحولت إلى ذئب!"
            await sdm(context.bot,uid,f"🎭 *تذكير بدورك:*\n\n{rd.emoji} *{rd.display}*\n📝 {rd.description}\n👥 فريقك: {tt.get(p.team.value if p.team else 'villager','❓')}{extra}",parse_mode="Markdown")
            if update.effective_chat.type!="private": await update.message.reply_text("📩 تم إرسال دورك في الخاص!")
            return
    await update.message.reply_text("⚠️ لست في لعبة نشطة!")

async def cmd_alive(update,context):
    if update.effective_chat.type=="private": return
    g=gm.get(update.effective_chat.id)
    if not g or g.phase in (Phase.LOBBY,Phase.GAME_OVER): await update.message.reply_text("⚠️ لا توجد لعبة نشطة!"); return
    alive=g.alive_players; dead=[p for p in g.players.values() if not p.alive]
    t=f"👥 *الأحياء ({len(alive)}):*\n"+"\n".join(f"  ✅ {p.name}" for p in alive)
    if dead: t+=f"\n\n💀 *الأموات ({len(dead)}):*\n"+"\n".join(f"  ☠️ {p.name}" for p in dead)
    await update.message.reply_text(t,parse_mode="Markdown")

async def cmd_stats(update,context):
    uid=str(update.effective_user.id); s=load_stats()
    if uid not in s: await update.message.reply_text("📊 لا توجد إحصائيات بعد!"); return
    d=s[uid]; wr=(d.get('wins',0)/d.get('games',1))*100 if d.get('games',0)>0 else 0
    await update.message.reply_text(f"📊 *إحصائياتك:*\n━━━━━━━━━━━━━━━━\n🎮 ألعاب: {d.get('games',0)}\n🏆 فوز: {d.get('wins',0)} | 💀 خسارة: {d.get('losses',0)}\n📈 نسبة الفوز: {wr:.0f}%\n🔪 قتل: {d.get('kills',0)} | 🛡️ نجاة: {d.get('survived',0)}\n⭐ MVP: {d.get('mvp',0)}\n━━━━━━━━━━━━━━━━",parse_mode="Markdown")

async def cmd_leaderboard(update,context):
    s=load_stats()
    if not s: await update.message.reply_text("📊 لا إحصائيات بعد!"); return
    sp=sorted(s.items(),key=lambda x:x[1].get("wins",0),reverse=True)[:10]
    medals=["🥇","🥈","🥉"]
    lines=[f"{medals[i] if i<3 else f'#{i+1}'} *{d['name']}* — 🏆{d.get('wins',0)} 🔪{d.get('kills',0)} ⭐{d.get('mvp',0)}" for i,(u,d) in enumerate(sp)]
    await update.message.reply_text(f"🏆 *المتصدرين:*\n━━━━━━━━━━━━━━━━\n\n"+"\n".join(lines)+"\n\n━━━━━━━━━━━━━━━━",parse_mode="Markdown")

async def cmd_endgame(update,context):
    if update.effective_chat.type=="private": return
    cid=update.effective_chat.id; g=gm.get(cid)
    if not g: await update.message.reply_text("⚠️ لا توجد لعبة!"); return
    g.phase=Phase.GAME_OVER
    if g._task and not g._task.done(): g._task.cancel()
    rt="\n".join(f"{'💀' if not p.alive else '✅'} {p.name} — {p.display_role}" for p in g.players.values())
    await ssend(context.bot,cid,f"🛑 تم إنهاء اللعبة!\n\n🎭 *الأدوار:*\n{rt}\n\n/start للعبة جديدة!",parse_mode="Markdown")
    gm.remove(cid)

async def cmd_players(update,context):
    if update.effective_chat.type=="private": return
    g=gm.get(update.effective_chat.id)
    if not g: await update.message.reply_text("⚠️ لا توجد لعبة!"); return
    if g.phase==Phase.LOBBY:
        t="👥 *المنضمون:*\n"+"\n".join(f"• {p.name}" for p in g.players.values())+f"\n\n📊 {len(g.players)}/{Game.MAX_PLAYERS}"
    else:
        t="👥 *اللاعبون:*\n"+"\n".join(f"{'✅' if p.alive else '💀'} {p.name}" for p in g.players.values())+f"\n\n📊 أحياء: {len(g.alive_players)}/{len(g.players)}"
    await update.message.reply_text(t,parse_mode="Markdown")

# ── Callbacks ──
async def join_cb(update,context):
    q=update.callback_query; d=q.data
    if d.startswith("join_"):
        cid=int(d.split("_")[1]); g=gm.get(cid)
        if not g or g.phase!=Phase.LOBBY: await q.answer("⚠️ غير متاحة!",show_alert=True); return
        u=q.from_user; name=u.first_name or u.username or f"U{u.id}"
        if u.id in g.players: await q.answer("⚠️ منضم بالفعل!",show_alert=True); return
        if g.add_player(u.id,name):
            test=await sdm(context.bot,u.id,"✅ تم انضمامك! ⏳ انتظر بدء اللعبة.")
            if not test:
                if u.id in g.players: del g.players[u.id]
                bi=await context.bot.get_me()
                await q.answer(f"⚠️ افتح البوت أولاً @{bi.username} واضغط Start!",show_alert=True); return
            await q.answer(f"✅ انضممت يا {name}!",show_alert=True); await update_lobby(context.bot,g)
        else: await q.answer("⚠️ ممتلئة!",show_alert=True)
    elif d.startswith("sg_"):
        cid=int(d.split("_")[1]); g=gm.get(cid)
        if not g or g.phase!=Phase.LOBBY: await q.answer("⚠️ غير متاحة!",show_alert=True); return
        if len(g.players)<Game.MIN_PLAYERS: await q.answer(f"⚠️ يحتاج {Game.MIN_PLAYERS}!",show_alert=True); return
        await q.answer("🚀 جاري البدء...")
        try: await context.bot.edit_message_reply_markup(chat_id=cid,message_id=g.lobby_msg_id,reply_markup=None)
        except: pass
        await start_logic(context.bot,g,cid)
    elif d.startswith("cg_"):
        cid=int(d.split("_")[1]); g=gm.get(cid)
        if g and g.phase==Phase.LOBBY:
            lid=g.lobby_msg_id; gm.remove(cid); await q.answer("❌ تم الإلغاء!",show_alert=True)
            try: await context.bot.edit_message_text(chat_id=cid,message_id=lid,text="❌ *تم إلغاء اللعبة!*\n\n/start للعبة جديدة.",parse_mode="Markdown")
            except: pass

# ── Start Logic ──
async def start_logic(bot,g,cid):
    g.assign_roles(); plist="🎭 *اللاعبون:*\n"; fails=[]
    tt={"villager":"الأبرياء 🛡️","evil":"الأشرار 😈","dracula":"دراكولا 🧛","solo":"وحيد 🧌"}
    for p in g.players.values():
        plist+=f"• {p.name}\n"; rd=p.role_def
        r=await sdm(bot,p.user_id,f"🎭 *دورك:*\n\n{rd.emoji} *{rd.display}*\n📝 {rd.description}\n👥 فريقك: {tt.get(rd.team.value,'❓')}\n\n⚠️ لا تكشف دورك!\n💡 /role للتذكير",parse_mode="Markdown")
        if not r: fails.append(p.name)
        update_stat(p.user_id,p.name,"games")
    await ssend(bot,cid,f"🎲 *تم توزيع الأدوار!*\n\n{plist}\n📩 تحقق من الخاص!\n👥 عدد: {len(g.players)}\n\n💡 /role /alive /stats",parse_mode="Markdown")
    if fails:
        bi=await bot.get_me()
        await ssend(bot,cid,"⚠️ *تنبيه!*\n\nلم أرسل الدور لـ:\n"+"\n".join(f"• {n}" for n in fails)+f"\n\n📩 افتحوا البوت: https://t.me/{bi.username}\n⏳ أعيدوا بـ /start",parse_mode="Markdown")
        g.phase=Phase.GAME_OVER; gm.remove(cid); return
    evils=[p for p in g.players.values() if p.role_def.team==Team.EVIL]
    if len(evils)>1:
        for ep in evils:
            others=[f"{o.name} ({o.role_def.emoji} {o.role_def.display})" for o in evils if o.user_id!=ep.user_id]
            await sdm(bot,ep.user_id,"😈 *فريق الأشرار:*\n"+"\n".join(f"• {o}" for o in others),parse_mode="Markdown")
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
        await sgif(bot,g.chat_id,"night",f"🌙 *الليلة {g.round_num}*\n\n{random.choice(NIGHT_MESSAGES)}{emsg}\n\n⏳ لديكم {Game.NIGHT_DUR} ثانية.",parse_mode="Markdown")
        if g.event=="blood_moon":
            rp=random.choice(g.alive_players); await asyncio.sleep(2)
            await ssend(bot,g.chat_id,f"🔴 *القمر الدموي يكشف:*\n👤 {rp.name} هو {rp.display_role}!",parse_mode="Markdown")
            g.log("night","قمر دموي","",f"{rp.name}={rp.display_role}")
        for p in g.alive_players: await send_night(bot,g,p)
        th=Game.NIGHT_DUR//3
        await asyncio.sleep(th)
        await ssend(bot,g.chat_id,f"⏳ متبقي {th*2} ثانية! استخدموا قدراتكم!")
        await asyncio.sleep(th)
        await ssend(bot,g.chat_id,f"🔥 *آخر {th} ثانية!* ⚠️ قرروا الآن!",parse_mode="Markdown")
        await asyncio.sleep(th)
        await ssend(bot,g.chat_id,random.choice(SUSPENSE))
        await asyncio.sleep(2)
        await resolve_night(bot,g)
    except asyncio.CancelledError: pass
    except Exception as e: logger.error(f"Night err:{e}",exc_info=True); await ssend(bot,g.chat_id,f"⚠️ خطأ: {e}")

async def send_night(bot,g,player):
    role=player.role; targets=[p for p in g.alive_players if p.user_id!=player.user_id]
    if not targets: return
    cp=None; text=None
    if role==RoleName.CRIMINAL: text="🔪 اختر لاعبًا لقتله:"; cp="nc"
    elif role==RoleName.GHOST_KILLER: text="👻 اختر لاعبًا لقتله بصمت:"; cp="ng"
    elif role==RoleName.MAID: text="🤵‍♀️ اختر لاعبًا لكشف دوره:"; cp="nm"
    elif role==RoleName.CHEF: text="🧑‍🍳 اختر لاعبًا لتسميمه:"; cp="nch"
    elif role==RoleName.THIEF:
        if player.thief_used: return
        text="🥷 اختر لاعبًا لسرقة دوره:"; cp="nt"
    elif role==RoleName.POLICE: text="👮‍♀️ اختر لاعبًا للتحقيق:"; cp="np"
    elif role==RoleName.DOORMAN:
        if player.doorman_used: return
        kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ هدنة!",callback_data=f"nd_{g.chat_id}_y")],[InlineKeyboardButton("❌ لا",callback_data=f"nd_{g.chat_id}_n")]])
        await sdm(bot,player.user_id,"🧑‍✈️ هل تعلن هدنة?",reply_markup=kb); return
    elif role==RoleName.NEIGHBOR: text="😘 اختر لاعبًا لزيارته:"; cp="nn"
    elif role==RoleName.FOREST_GUARD:
        if g.fog: await sdm(bot,player.user_id,"🌫️ الضباب يمنعك من الحماية!"); return
        targets=[p for p in targets if p.user_id!=g.guard_last]
        if not targets: return
        text="🧙‍♀️ اختر لاعبًا لحمايته:"; cp="nfg"
    elif role==RoleName.BATMAN:
        if player.batman_bullets<=0: return
        text=f"🦹‍♂️ اختر هدفًا ({player.batman_bullets} طلقة):"; cp="nb"
    elif role==RoleName.WITCH: text="🧝‍♀️ اختر اللاعب الأول للربط:"; cp="nw1"
    elif role==RoleName.DRACULA:
        targets=[p for p in targets if not p.is_vampire and p.role!=RoleName.DRACULA]
        if not targets: return
        text="🧛 اختر لاعبًا لتحويله:"; cp="ndr"
    else: return
    btns=[]; row=[]
    for i,t in enumerate(targets):
        row.append(InlineKeyboardButton(t.name,callback_data=f"{cp}_{g.chat_id}_{t.user_id}"))
        if len(row)==2 or i==len(targets)-1: btns.append(row); row=[]
    btns.append([InlineKeyboardButton("⏭️ تخطي",callback_data=f"{cp}_{g.chat_id}_skip")])
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
        if not g or g.phase!=Phase.NIGHT: await q.edit_message_text("⚠️ انتهى الوقت."); return
        uid=q.from_user.id; p=g.get_player(uid)
        if not p or not p.alive: return
        ak=f"{at}_{uid}"
        if ak in g.night_actions and at!="nw1": await q.edit_message_text("✅ قررت بالفعل!"); return
        if tv=="skip" or tv=="n": g.night_actions[ak]="skip"; await q.edit_message_text("⏭️ تم التخطي."); return
        if tv=="y" and at=="nd":
            g.night_actions[ak]="truce"; g.truce=True; p.doorman_used=True
            g.log("night","هدنة",p.name,""); await q.edit_message_text("🛑 تم تفعيل الهدنة!"); return
        tid=int(tv); tgt=g.get_player(tid)
        if at=="nc": g.night_actions[ak]=tid; g.log("night","قتل",p.name,tgt.name if tgt else "?"); await q.edit_message_text(f"🔪 هدفك: {tgt.name if tgt else '?'}")
        elif at=="ng": g.night_actions[ak]=tid; g.log("night","قتل شبح",p.name,tgt.name if tgt else "?"); await q.edit_message_text(f"👻 هدفك: {tgt.name if tgt else '?'}")
        elif at=="nm":
            g.night_actions[ak]=tid
            if tgt:
                if tgt.role==RoleName.GHOST_KILLER:
                    fk=random.choice([RoleName.PAINTER,RoleName.CHIEF,RoleName.NEIGHBOR]); rd=ROLE_DEFS[fk]
                    await q.edit_message_text(f"🔍 {tgt.name}: {rd.emoji} {rd.display}")
                else: p.investigations+=1; await q.edit_message_text(f"🔍 {tgt.name}: {tgt.display_role}")
        elif at=="nch": g.night_actions[ak]=tid; await q.edit_message_text(f"☠️ تم تسميم {tgt.name if tgt else '?'}")
        elif at=="nt":
            g.night_actions[ak]=tid; p.thief_used=True
            if tgt: sr=tgt.role; tgt.role=RoleName.PAINTER; p.role=sr; await q.edit_message_text(f"🥷 سرقت دور {tgt.name}!\n🎭 دورك الجديد: {p.display_role}")
        elif at=="np":
            g.night_actions[ak]=tid
            if tgt:
                ik=tgt.team in (Team.EVIL,Team.DRACULA)
                if tgt.role==RoleName.GHOST_KILLER: ik=False
                r="🔴 قاتل!" if ik else "🟢 بريء"
                if ik: p.investigations+=1
                await q.edit_message_text(f"🔎 {tgt.name}: {r}")
        elif at=="nn": g.night_actions[ak]=tid; p.visited_target=tid; await q.edit_message_text(f"😘 ستزورين {tgt.name if tgt else '?'}")
        elif at=="nfg":
            g.night_actions[ak]=tid
            if tgt: tgt.protected=True; g.guard_last=tid; await q.edit_message_text(f"🛡️ تحمي {tgt.name}")
        elif at=="nb":
            g.night_actions[ak]=tid; p.batman_bullets-=1
            await q.edit_message_text(f"🦹‍♂️ أطلقت النار على {tgt.name if tgt else '?'}! (متبقي: {p.batman_bullets})")
        elif at=="nw1":
            g.night_actions[f"w1_{uid}"]=tid
            t2=[x for x in g.alive_players if x.user_id!=uid and x.user_id!=tid]
            if t2:
                btns=[]; row=[]
                for i,t in enumerate(t2):
                    row.append(InlineKeyboardButton(t.name,callback_data=f"nw2_{cid}_{t.user_id}"))
                    if len(row)==2 or i==len(t2)-1: btns.append(row); row=[]
                btns.append([InlineKeyboardButton("⏭️ تخطي",callback_data=f"nw2_{cid}_skip")])
                await q.edit_message_text(f"🧝‍♀️ الأول: {tgt.name if tgt else '?'}.\nاختر الثاني:",reply_markup=InlineKeyboardMarkup(btns))
        elif at=="nw2":
            ft=g.night_actions.get(f"w1_{uid}")
            if ft: g.witch_links[ft]=tid; g.witch_links[tid]=ft; t1=g.get_player(ft); await q.edit_message_text(f"🧝‍♀️ تم ربط {t1.name if t1 else '?'} + {tgt.name if tgt else '?'}!")
        elif at=="ndr": g.night_actions[ak]=tid; await q.edit_message_text(f"🧛 ستحول {tgt.name if tgt else '?'}")
    except Exception as e: logger.error(f"Night cb err:{e}",exc_info=True)

# ── Resolve Night ──
async def resolve_night(bot,g):
    killed=[]; msgs=[]
    if not g.storm:
        for k,v in g.night_actions.items():
            if k.startswith("nc_") and v!="skip" and isinstance(v,int):
                t=g.get_player(v)
                if t and t.alive and not t.protected:
                    if t.role==RoleName.DOG and not t.dog_transformed: t.dog_transformed=True; msgs.append("🌙 في عمق الليل…\n🐶→🐺 الكلب تحول لذئب!")
                    else: killed.append(v)
                    for p in g.players.values():
                        if p.role==RoleName.CRIMINAL and p.alive: p.kills+=1
                elif t and t.protected:
                    for p in g.players.values():
                        if p.role==RoleName.FOREST_GUARD and p.alive: p.saves+=1
        for k,v in g.night_actions.items():
            if k.startswith("ng_") and v!="skip" and isinstance(v,int):
                t=g.get_player(v)
                if t and t.alive and not t.protected and v not in killed:
                    if t.role==RoleName.DOG and not t.dog_transformed: t.dog_transformed=True; msgs.append("🐶→🐺 الكلب تحول لذئب!")
                    else: killed.append(v)
        for k,v in g.night_actions.items():
            if k.startswith("nb_") and v!="skip" and isinstance(v,int):
                t=g.get_player(v)
                if t and t.alive and v not in killed: killed.append(v)
    else:
        await sgif(bot,g.chat_id,"storm","⛈️ *العاصفة منعت أي قتل!*\n😮 الجميع نجوا!",parse_mode="Markdown")
    # Poison
    for k,v in g.night_actions.items():
        if k.startswith("nch_") and v!="skip" and isinstance(v,int):
            t=g.get_player(v)
            if t and t.alive: t.poisoned=True
    for k,v in list(g.night_actions.items()):
        if k.startswith("pp_"):
            uid=int(k.split("_")[-1]); t=g.get_player(uid)
            if t and t.alive and uid not in killed and not t.protected: killed.append(uid); t.poisoned=False
    for k,v in g.night_actions.items():
        if k.startswith("nch_") and v!="skip" and isinstance(v,int): g.night_actions[f"pp_{v}"]=True
    # Dracula
    for k,v in g.night_actions.items():
        if k.startswith("ndr_") and v!="skip" and isinstance(v,int):
            t=g.get_player(v)
            if t and t.alive and v not in killed:
                t.is_vampire=True
                await sdm(bot,t.user_id,"🧛 *تحولت لمصاص دماء!*\n😈 أنت مع دراكولا الآن!",parse_mode="Markdown")
    # Neighbor
    for p in g.alive_players:
        if p.visited_target:
            t=g.get_player(p.visited_target)
            if t:
                left=any(k.endswith(f"_{t.user_id}") and v!="skip" for k,v in g.night_actions.items())
                await sdm(bot,p.user_id,f"😘 {t.name} {'لم يكن ببيته! 🚪' if left else 'كان ببيته 🏠'}")
    # Witch links
    extra=[]
    for uid in killed:
        if uid in g.witch_links:
            lu=g.witch_links[uid]; lp=g.get_player(lu)
            if lp and lp.alive and lu not in killed and lu not in extra: extra.append(lu)
    killed.extend(extra)
    uq=list(dict.fromkeys(killed))
    for uid in uq:
        p=g.get_player(uid)
        if p: p.alive=False
    if not uq and not g.storm:
        await ssend(bot,g.chat_id,"🌅 أشرقت الشمس…\n😳 الجميع على قيد الحياة!\n👁️ أحدهم نجا بأعجوبة!")
    else:
        for uid in uq:
            p=g.get_player(uid)
            if p:
                dm=DEATH_MSGS.get(p.role,"💀 رحل عنا…")
                kt="generic"
                for k,v in g.night_actions.items():
                    if isinstance(v,int) and v==uid:
                        if "nc" in k: kt="criminal"
                        elif "ng" in k: kt="ghost"
                        elif "nb" in k: kt="batman"
                        elif "pp" in k or "nch" in k: kt="poison"
                await sgif(bot,g.chat_id,f"death_{kt}",f"💀 جثة *{p.name}*\n😨 ملامح الرعب…\n🗣️ من القاتل?\n\n🎭 {p.display_role}\n\n{dm}",parse_mode="Markdown")
                dmt={"criminal":"🔪 *قتلك المجرم!*","ghost":"👻 *قتلك الشبح!*","batman":"🦹‍♂️ *باتمان أطلق عليك!*","poison":"☠️ *مت مسمومًا!*","generic":"💀 *لقد قُتلت!*"}
                await sgif_dm(bot,p.user_id,f"death_{kt}",f"{dmt.get(kt,dmt['generic'])}\n\n🎭 دورك: {p.display_role}\n👻 تابع كمتفرج.",parse_mode="Markdown")
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
        at="\n".join(f"  ✅ {p.name}" for p in g.alive_players)
        await sgif(bot,g.chat_id,"day",f"🌅 *الجولة {g.round_num}*\n\n{random.choice(DAY_MESSAGES)}\n\n👥 الأحياء ({len(g.alive_players)}):\n{at}\n\n⏳ {Game.DISC_DUR} ثانية للنقاش…\n🗳️ وبعدها يبدأ التصويت مباشرة.",parse_mode="Markdown")
        for p in g.alive_players:
            if p.role in (RoleName.CRIMINAL, RoleName.GHOST_KILLER, RoleName.BATMAN):
                await sdm(bot,p.user_id,"⏳ *بقيت دقيقة قبل التصويت...*\n\n🩸 اختر هدفك الآن إن كنت صاحب الضربة الليلية.\n👁️ هذه فرصتك الأخيرة قبل أن يبدأ النهار بالحكم.",parse_mode="Markdown")
        await asyncio.sleep(Game.DISC_DUR//2)
        await ssend(bot,g.chat_id,random.choice(SUSPENSE))
        await asyncio.sleep(Game.DISC_DUR//2)
        if g.truce:
            await sgif(bot,g.chat_id,"truce","🛑 هدنة!\n🚫 لا تصويت هذه الجولة.\n🌲 استعدوا!")
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
        await sgif(bot,g.chat_id,"vote","⚖️ *بدأ التصويت!*\n\n📩 أزرار التصويت في الخاص.\n⏳ إذا اكتملت الأصوات قبل الوقت ينتهي التصويت فورًا.\n🔒 سري… لكن النتيجة تكشف الكل!",parse_mode="Markdown")
        for p in alive:
            tgts=[x for x in alive if x.user_id!=p.user_id]; btns=[]; row=[]
            for i,t in enumerate(tgts):
                row.append(InlineKeyboardButton(t.name,callback_data=f"v_{g.chat_id}_{t.user_id}"))
                if len(row)==2 or i==len(tgts)-1: btns.append(row); row=[]
            btns.append([InlineKeyboardButton("⏭️ امتناع",callback_data=f"v_{g.chat_id}_skip")])
            await sdm(bot,p.user_id,f"⚖️ *صوّت الآن!*\n🎯 اختر الأخطر:\n⏳ {Game.VOTE_DUR} ثانية!\n✅ إذا اكتملت الأصوات ينتهي التصويت مباشرة.",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(btns))
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
            vr="🗳️ *كشف التصويت:*\n━━━━━━━━━━━━━━━━\n\n"
            for vi,ti in g.votes.items():
                vt=g.get_player(vi)
                if ti==-1: vr+=f"⚪ {vt.name} ← امتنع\n"
                else: tt=g.get_player(ti); vr+=f"🗳️ {vt.name} ➡️ {tt.name if tt else '?'}\n"
            for p in alive:
                if p.user_id not in g.votes: vr+=f"❌ {p.name} ← لم يصوّت\n"
            vr+="\n━━━━━━━━━━━━━━━━"
            await ssend(bot,g.chat_id,vr,parse_mode="Markdown")
        await resolve_votes(bot,g)
    except asyncio.CancelledError: pass
    except Exception as e: logger.error(f"Vote err:{e}",exc_info=True)

async def vote_cb(update,context):
    q=update.callback_query; d=q.data
    if not d.startswith("v_"): return
    pp=d.split("_"); cid=int(pp[1]); tv=pp[2]
    g=gm.get(cid)
    if not g or g.phase!=Phase.VOTING or g.vote_closed: await q.answer("⚠️ انتهى!",show_alert=True); return
    vid=q.from_user.id; vt=g.get_player(vid)
    if not vt: await q.answer("⚠️ لست باللعبة!",show_alert=True); return
    if not vt.alive: await q.answer("💀 أنت ميت!",show_alert=True); return
    if vid in g.votes: await q.answer("⚠️ صوّتت بالفعل!",show_alert=True); return
    if vt.role==RoleName.MADMAN:
        ps=[p for p in g.alive_players if p.user_id!=vid]
        if ps:
            g.votes[vid]=random.choice(ps).user_id
            await q.edit_message_text("🤡 تم! (عشوائي)")
            if g.vote_expected and g.vote_expected.issubset(g.votes.keys()) and g.vote_event and not g.vote_event.is_set():
                g.vote_event.set()
        return
    if tv=="skip":
        g.votes[vid]=-1
        await q.edit_message_text("⏭️ تم الامتناع.")
    else:
        tid=int(tv); g.votes[vid]=tid; tgt=g.get_player(tid)
        await q.edit_message_text(f"✅ صوّت ضد *{tgt.name if tgt else '?'}*\n⏳ انتظر النتائج…",parse_mode="Markdown")
    if g.vote_expected and g.vote_expected.issubset(g.votes.keys()) and g.vote_event and not g.vote_event.is_set():
        g.vote_event.set()


async def resolve_votes(bot,g):
    if not g.votes:
        await ssend(bot,g.chat_id,"⚖️ لم يصوّت أحد!\n🌙 استعدوا…")
        g._task=asyncio.create_task(run_night(bot,g)); return
    vc={}
    for vi,ti in g.votes.items():
        if ti!=-1: vc[ti]=vc.get(ti,0)+1
    if not vc:
        await ssend(bot,g.chat_id,"⚖️ كل الأصوات امتناع!\n🌙 استعدوا…")
        g._task=asyncio.create_task(run_night(bot,g)); return
    mx=max(vc.values()); tops=[u for u,c in vc.items() if c==mx]
    slines=[]
    for u,c in sorted(vc.items(),key=lambda x:-x[1]):
        p=g.get_player(u)
        if p: bar="▓"*c+"░"*(len(g.alive_players)-c); slines.append(f"  {p.name}: {bar} ({c})")
    summary="\n".join(slines)
    if len(tops)>1:
        await ssend(bot,g.chat_id,f"⚖️ *نتائج:*\n\n{summary}\n\n⚖️ تعادل! لا إعدام.\n🌙 استعدوا…",parse_mode="Markdown")
        g._task=asyncio.create_task(run_night(bot,g)); return
    tid=tops[0]; tgt=g.get_player(tid)
    if not tgt: g._task=asyncio.create_task(run_night(bot,g)); return
    # Grocer
    if tgt.role==RoleName.GROCER and tgt.alive:
        tgt.alive=False
        await ssend(bot,g.chat_id,f"⚖️ *نتائج:*\n\n{summary}\n\n🧌 مفاجأة!!\nإعدام صاحب البقالة *{tgt.name}*\n😈 يفوز وحده!!\n💀 الكل خسر…",parse_mode="Markdown")
        await announce_win(bot,g,"grocer",tgt.name); return
    # Prince
    if tgt.role==RoleName.PRINCE and tgt.prince_lives>0:
        tgt.prince_lives-=1
        await ssend(bot,g.chat_id,f"⚖️ *نتائج:*\n\n{summary}\n\n👑 الأمير *{tgt.name}* نجا!\n🌙 استعدوا…",parse_mode="Markdown")
        g._task=asyncio.create_task(run_night(bot,g)); return
    # Last words
    g.phase=Phase.LAST_WORDS
    await ssend(bot,g.chat_id,f"⚖️ *نتائج:*\n\n{summary}\n\n⏳ *{tgt.name}* سيُعدم!\n🗣️ *كلمة أخيرة!*\n💬 لديك {Game.LAST_WORDS_DUR} ثانية…",parse_mode="Markdown")
    g.log("vote","محكوم",tgt.name,"")
    await asyncio.sleep(Game.LAST_WORDS_DUR)
    tgt.alive=False; dm=DEATH_MSGS.get(tgt.role,"💀 رحل…")
    await sgif(bot,g.chat_id,"death_vote",f"⚖️ تم الإعدام…\n💀 *{tgt.name}*\n🎭 {tgt.display_role}\n🌲 مذنب أم بريء?\n\n{dm}",parse_mode="Markdown")
    g.log("vote","إعدام","",f"{tgt.name} ({tgt.display_role})")
    if tgt.user_id in g.witch_links:
        lu=g.witch_links[tgt.user_id]; lp=g.get_player(lu)
        if lp and lp.alive:
            lp.alive=False; ld=DEATH_MSGS.get(lp.role,"💀 رحل…")
            await asyncio.sleep(2)
            await ssend(bot,g.chat_id,f"🧝‍♀️ *الرابط!*\n💀 مات أيضًا: *{lp.name}*\n🎭 {lp.display_role}\n\n{ld}",parse_mode="Markdown")
    w=g.check_win()
    if w: await asyncio.sleep(3); await announce_win(bot,g,w); return
    await asyncio.sleep(3); g._task=asyncio.create_task(run_night(bot,g))

# ══════════════════════════════════════════════
# WINNER
# ══════════════════════════════════════════════
async def announce_win(bot, g, winner, gn=""):
    g.phase = Phase.GAME_OVER
    
    # 1. تحديد نصوص الفوز بتنسيق HTML
    if winner == "village": 
        txt = "🏆 <b>انتهت الجولة!</b>\n🎉 <b>فاز الأبرياء!</b>\n🛡️ تم القضاء على الأشرار.\n🌲 عاد السلام إلى القصر."
        gk = "win_village"; wt = Team.VILLAGER
    elif winner == "evil": 
        txt = "💀 <b>انتهت اللعبة!</b>\n😈 <b>فاز الأشرار!</b>\n🩸 سيطر الظلام…\n🌑 لم ينجُ أحد."
        gk = "win_evil"; wt = Team.EVIL
    elif winner == "dracula": 
        txt = "🧛‍♂️ <b>الليل لم ينتهِ…</b>\n🩸 <b>دراكولا انتصر!</b>\n⚰️ مرحبًا بالظلام الأبدي."
        gk = "win_dracula"; wt = Team.DRACULA
    elif winner == "grocer": 
        txt = f"🧌 <b>مفاجأة! فاز {gn} وحده!!</b>\n💀 الكل خسر…"
        gk = "win_evil"; wt = Team.SOLO
    else: 
        txt = "🏁 <b>انتهت!</b>"
        gk = "win_village"; wt = None

    for p in g.players.values():
        if winner == "grocer":
            update_stat(p.user_id, p.name, "wins" if p.role == RoleName.GROCER else "losses")
        elif wt and p.team == wt: update_stat(p.user_id, p.name, "wins")
        else: update_stat(p.user_id, p.name, "losses")
        if p.alive: update_stat(p.user_id, p.name, "survived")
        if p.kills > 0: update_stat(p.user_id, p.name, "kills", p.kills)

    # 2. تنسيق قسم الـ MVP بشكل احترافي
    mvp = g.calc_mvp()
    mt = ""
    if mvp: 
        update_stat(mvp.user_id, mvp.name, "mvp")
        mt = f"\n\n<blockquote>⭐ <b>نجم الجولة (MVP):</b>\n👤 {mvp.name} — {mvp.display_role}</blockquote>"

    # 3. تنسيق قائمة الأدوار
    rt = "\n".join(f"{'💀' if not p.alive else '✅'} {p.name} — {p.display_role}" for p in g.players.values())
    
    # 4. تنسيق الملخص داخل Blockquote
    ls = ""
    ke = [e for e in g.log_entries if e.action in ("مقتل", "إعدام", "حماية", "تحويل", "قمر دموي", "هدنة")]
    if ke:
        ls = "\n\n<blockquote>📜 <b>ملخص الأحداث:</b>\n"
        for e in ke[-8:]: 
            ls += f"🔹 ر{e.rnd}: {e.action}"
            ls += f" ({e.actor})" if e.actor else ""
            ls += f" ⬅️ {e.target}" if e.target else ""
            ls += "\n"
        ls += "</blockquote>"

    # إضافة إرشادات بسيطة في الأسفل
    footer = "\n\n💡 <i>لعبة جديدة: /start | إحصائيات: /stats | متصدرين: /leaderboard</i>"

    # تجميع الرسالة النهائية
    final_message = f"{txt}\n\n🎭 <b>الأدوار:</b>\n{rt}{mt}{ls}{footer}"

    # أزرار تفاعلية أسفل الرسالة
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="cmd_stats"), 
         InlineKeyboardButton("🏆 المتصدرين", callback_data="cmd_leaderboard")]
    ])

    try:
        await bot.send_animation(
            chat_id=g.chat_id,
            animation=GIFS.get(gk, GIFS["start"]),
            caption=final_message,
            parse_mode="HTML",
            reply_markup=kb
        )
    except:
        await ssend(bot, g.chat_id, final_message, parse_mode="HTML", reply_markup=kb)

    gm.remove(g.chat_id)

# ── Router ──
async def cb_router(update,context):
    q=update.callback_query
    if not q or not q.data: return
    d=q.data
    
    # معالجة أزرار شاشة النهاية (Endgame Buttons)
    if d == "cmd_stats":
        await q.answer("💡 لمعرفة إحصائياتك، قم بإرسال الأمر /stats في المجموعة!", show_alert=True)
        return
    elif d == "cmd_leaderboard":
        await q.answer("🏆 لمعرفة المتصدرين، قم بإرسال الأمر /leaderboard في المجموعة!", show_alert=True)
        return

    if any(d.startswith(p) for p in ["nc_","ng_","nm_","nch_","nt_","np_","nd_","nn_","nfg_","nb_","nw1_","nw2_","ndr_"]): await night_cb(update,context)
    elif d.startswith("v_"): await vote_cb(update,context)
    elif d.startswith("join_") or d.startswith("sg_") or d.startswith("cg_"): await join_cb(update,context)
    else: await q.answer("⚠️ غير معروف",show_alert=True)

def main():
    TOKEN="8712365309:AAExk4vAUogk2L5wgozuE-cSq3TdEHcOSWg"
    app=Application.builder().token(TOKEN).build()
    async def post_init(application):
        from telegram import BotCommand
        await application.bot.set_my_commands([BotCommand("start","🏰 لعبة جديدة"),BotCommand("join","🎮 انضم"),BotCommand("startgame","🚀 ابدأ"),BotCommand("players","👥 اللاعبين"),BotCommand("alive","✅ الأحياء"),BotCommand("role","🎭 دورك"),BotCommand("stats","📊 إحصائياتك"),BotCommand("leaderboard","🏆 المتصدرين"),BotCommand("endgame","🛑 إنهاء")])
        logger.info("✅ Commands registered!")
    app.post_init=post_init
    for cmd,fn in [("start",cmd_start),("join",cmd_join),("startgame",cmd_startgame),("endgame",cmd_endgame),("players",cmd_players),("alive",cmd_alive),("role",cmd_role),("stats",cmd_stats),("leaderboard",cmd_leaderboard)]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CallbackQueryHandler(cb_router))
    logger.info("🏰 Ghosts Palace Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__": main()
