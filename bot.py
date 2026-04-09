#!/usr/bin/env python3
"""
🏰 Ghosts Palace - 𝒉𝒂𝒗𝒂𝒏𝒂 𝑪𝒉𝒂𝒕🦩
"""

import asyncio, random, logging, json, os, html
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
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

# تم تغيير جميع الـ GIFs لتكون مرعبة، سينمائية، وتناسب أجواء الغموض
GIFS={
    "start": "https://media.giphy.com/media/l41K3o5TzvmhZwd4A/giphy.gif", # قصر مرعب من الخارج
    "night": "https://media.giphy.com/media/13HBDk1F8X4dQQ/giphy.gif", # ضباب وغابة مظلمة
    "day": "https://media.giphy.com/media/3o7aD2d7hy9ktXNDP2/giphy.gif", # شروق شاحب ومرعب
    "vote": "https://media.giphy.com/media/3o7TKrEzvLbgzGmMle/giphy.gif", # نظرات حكم وتوتر
    "death_criminal": "https://media.giphy.com/media/xT9KVqVCDHN6CG9lEc/giphy.gif", # قاتل متسلسل
    "death_ghost": "https://media.giphy.com/media/5tsjxsQxgZPzjhiOQp/giphy.gif", # ظهور شبح مفزع
    "death_poison": "https://media.giphy.com/media/3o6nUX2WltBtsXXNqU/giphy.gif", # جمجمة وسم
    "death_batman": "https://media.giphy.com/media/l3q2XhfQ8oCkm1Ts4/giphy.gif", # رصاصة/ظل
    "death_generic": "https://media.giphy.com/media/xT0xeJpnrWC3XWblEk/giphy.gif", # جثة/دماء
    "death_vote": "https://media.giphy.com/media/l2YWvNxkX6mE311aU/giphy.gif", # مشنقة/إعدام
    "win_village": "https://media.giphy.com/media/3o7TKRBB3E7IdVNLm8/giphy.gif", # ناجون مرهقون
    "win_evil": "https://media.giphy.com/media/Y4yWtyQtxMeJ8GlUQm/giphy.gif", # ابتسامة شريرة شيطانية
    "win_dracula": "https://media.giphy.com/media/10peyLigdvj38I/giphy.gif", # مصاص دماء كلاسيكي مرعب
    "truce": "https://media.giphy.com/media/3o7TKyVQnEEI0b4ZTW/giphy.gif", # هدوء ما قبل العاصفة
    "dog_transform": "https://media.giphy.com/media/3o7TKwmnDgQb5jemjK/giphy.gif", # تحول ذئب
    "blood_moon": "https://media.giphy.com/media/xT0xeQ1ZUQ0cbRUby8/giphy.gif", # قمر دموي سينمائي
    "storm": "https://media.giphy.com/media/26FPCXdkvDbKBbgOI/giphy.gif" # رعد وعاصفة قوية
}

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
START_IMAGE_PATH=os.path.join(BASE_DIR,"start_cover.jpg")

NIGHT_MESSAGES=["🌙 <b>حلّ الليل…</b>\n🌲 الرياح تعصف بين الأشجار، وهناك من يتحرك في الظلام.\n🔒 الأبواب أُغلقت… والأنفاس محبوسة.","🌑 <b>الظلام يبتلع القرية…</b>\n🐾 خطوات خفية تقترب، ورائحة الموت تملأ المكان.","🌙 <b>القمر اكتمل الليلة…</b>\n👤 ظل يتحرك بين البيوت… أحدهم لن يرى الصباح.","🌌 <b>النجوم تختبئ خلف الغيوم…</b>\n🐺 عواء بعيد يقشعرّ الأبدان…"]
DAY_MESSAGES=["🌅 <b>أشرقت الشمس…</b>\n☀️ ضوء النهار يكشف ما حاول الليل إخفاءه.","🌤️ <b>الفجر يطرد الظلام…</b>\n👀 لكن بعض الوجوه مفقودة.","☀️ <b>الشمس تبزغ من جديد…</b>\n😓 التوتر يسيطر على القرية… من نثق به اليوم؟"]
SUSPENSE=["😰 التوتر يزداد في القرية…","🌲 شيء ما يتحرك بين الأشجار…","👁️ هل لاحظتم تلك النظرات المريبة؟","🤫 الصمت أحيانًا أخطر من الكلام…","⚡ الأجواء مشحونة… شيء سيحدث!","🎭 الأقنعة ستسقط عاجلاً أم آجلاً…"]
RANDOM_EVENTS={"blood_moon":{"name":"🔴 قمر دموي!","desc":"القمر الدموي يكشف هوية لاعب عشوائي!","chance":0.12},"storm":{"name":"⛈️ عاصفة مدمرة!","desc":"العاصفة منعت القتل هذه الليلة!","chance":0.08},"fog":{"name":"🌫️ ضباب كثيف!","desc":"الضباب يمنع الحارس من الحماية!","chance":0.10}}

@dataclass
class RoleDef:
    name:RoleName; display:str; emoji:str; team:Team; has_night_action:bool; description:str; priority:int

ROLE_DEFS={
    RoleName.CRIMINAL:RoleDef(RoleName.CRIMINAL,"المجرم","🔪",Team.EVIL,True,"يقتل لاعبًا كل ليلة",1),
    RoleName.GHOST_KILLER:RoleDef(RoleName.GHOST_KILLER,"الشبح القاتل","👻",Team.EVIL,True,"يقتل بصمت (يصعب اكتشافه)",2),
    RoleName.MAID:RoleDef(RoleName.MAID,"العرّافة","🤵‍♀️",Team.VILLAGER,True,"تكشف دور لاعب كل ليلة",10),
    RoleName.CHEF:RoleDef(RoleName.CHEF,"الشيف","🧑‍🍳",Team.EVIL,True,"يسمم لاعبًا (يموت الليلة التالية)",3),
    RoleName.THIEF:RoleDef(RoleName.THIEF,"اللص","🥷",Team.VILLAGER,True,"يسرق دور لاعب (مرة واحدة)",4),
    RoleName.POLICE:RoleDef(RoleName.POLICE,"الشرطي","👮‍♀️",Team.VILLAGER,True,"يكتشف القتلة",11),
    RoleName.DOORMAN:RoleDef(RoleName.DOORMAN,"البواب","🧑‍✈️",Team.VILLAGER,True,"يوقف التصويت ويعلن هدنة (مرة واحدة)",12),
    RoleName.NEIGHBOR:RoleDef(RoleName.NEIGHBOR,"الجارة","😘",Team.VILLAGER,True,"تراقب لاعبًا لتعرف إن غادر منزله",13),
    RoleName.FOREST_GUARD:RoleDef(RoleName.FOREST_GUARD,"حارس الغابة","🧙‍♀️",Team.VILLAGER,True,"يحمي لاعبًا من القتل",5),
    RoleName.MADMAN:RoleDef(RoleName.MADMAN,"المجنون","🤡",Team.VILLAGER,False,"تصويته عشوائي دائمًا",99),
    RoleName.GROCER:RoleDef(RoleName.GROCER,"صاحب البقالة","🧌",Team.SOLO,False,"يفوز وحده إذا تم إعدامه",99),
    RoleName.BATMAN:RoleDef(RoleName.BATMAN,"باتمان","🦹‍♂️",Team.VILLAGER,True,"يمتلك طلقتين لقتل أي شخص",6),
    RoleName.WITCH:RoleDef(RoleName.WITCH,"الساحرة","🧝‍♀️",Team.VILLAGER,True,"تربط مصير لاعبين ببعضهما",7),
    RoleName.PRINCE:RoleDef(RoleName.PRINCE,"الأمير","🫅",Team.VILLAGER,False,"ينجو من أول عملية إعدام",99),
    RoleName.PAINTER:RoleDef(RoleName.PAINTER,"الرسام","👩‍🎨",Team.VILLAGER,False,"مواطن عادي",99),
    RoleName.CHIEF:RoleDef(RoleName.CHIEF,"المختار","💂‍♂️",Team.VILLAGER,False,"مواطن عادي بصوت مسموع",99),
    RoleName.DRACULA:RoleDef(RoleName.DRACULA,"دراكولا","🧛",Team.DRACULA,True,"يحول لاعبًا لمصاص دماء ليلاً",8),
    RoleName.DOG:RoleDef(RoleName.DOG,"الكلب","🐶",Team.VILLAGER,False,"يتحول لذئب شرس إذا هوجم",99),
}

DEATH_MSGS={RoleName.MAID:"امتلكت الحقيقة… لكن لم تنقذ نفسك.",RoleName.CHEF:"السم كان سلاحك، والآن تذوقت الموت.",RoleName.THIEF:"سرقت الأدوار، لكن الموت سرق حياتك.",RoleName.POLICE:"بحثت عن الحقيقة… ووجدتك الظلال.",RoleName.DOORMAN:"أغلقت الأبواب… لكن الموت دخل من النافذة.",RoleName.NEIGHBOR:"راقبت الجميع، لكنك لم تراقبي ظهرك.",RoleName.FOREST_GUARD:"حميت الآخرين، وتُركت وحيداً في الظلام.",RoleName.MADMAN:"نشرت الفوضى، والآن التهمتك.",RoleName.GROCER:"أُغلقت أبواب البقالة للأبد.",RoleName.BATMAN:"حتى الأبطال يسقطون في هذه القرية.",RoleName.WITCH:"تعاويذك لم تكن كافية لردع الموت.",RoleName.DOG:"عواء أخير... ثم صمت.",RoleName.PRINCE:"حتى التاج الملكي لم يمنع سيل الدماء.",RoleName.PAINTER:"رسمت نهايتك باللون الأحمر.",RoleName.CHIEF:"سقط المختار، وسقطت معه القرية.",RoleName.DRACULA:"حتى أسياد الظلام يلقون حتفهم.",RoleName.CRIMINAL:"سقطت أخيرًا، وانتهت جرائمك.",RoleName.GHOST_KILLER:"حتى الأشباح تتلاشى في النهاية."}

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
        return f"{rd.emoji} <b>{rd.display}</b>{x}"

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
        self.players[uid]=Player(user_id=uid,name=html.escape(name)); return True
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
    try:
        kw.setdefault("parse_mode", "HTML")
        return await bot.send_message(chat_id=cid,text=text,**kw)
    except TelegramError as e: logger.error(f"Send fail {cid}:{e}"); return None

async def sdm(bot,uid,text,**kw):
    try: 
        kw.setdefault("parse_mode", "HTML")
        return await bot.send_message(chat_id=uid,text=text,**kw)
    except TelegramError as e: logger.warning(f"DM fail {uid}:{e}"); return None

async def sgif(bot,cid,gk,cap,**kw):
    kw.setdefault("parse_mode", "HTML")
    try: return await bot.send_animation(chat_id=cid,animation=GIFS.get(gk,GIFS["start"]),caption=cap,**kw)
    except: return await ssend(bot,cid,cap,**kw)

async def sgif_dm(bot,uid,gk,cap,**kw):
    kw.setdefault("parse_mode", "HTML")
    try: return await bot.send_animation(chat_id=uid,animation=GIFS.get(gk,GIFS["start"]),caption=cap,**kw)
    except: return await sdm(bot,uid,cap,**kw)

async def send_start_cover(bot,cid,caption,**kw):
    kw.setdefault("parse_mode", "HTML")
    try:
        if os.path.exists(START_IMAGE_PATH):
            with open(START_IMAGE_PATH,"rb") as f:
                return await bot.send_photo(chat_id=cid,photo=f,caption=caption,**kw)
    except Exception as e: pass
    try: return await bot.send_animation(chat_id=cid,animation=GIFS.get("start"),caption=caption,**kw)
    except Exception: return await ssend(bot,cid,caption,**kw)

def lobby_text(g):
    pl="".join(f"• 👤 <i>{p.name}</i>\n" for p in g.players.values()) or "<i>⏳ بانتظار الشجعان...</i>\n"
    c=len(g.players); st="🟢 <b>يمكن بدء اللعبة الآن!</b>" if c>=Game.MIN_PLAYERS else f"⏳ <i>نحتاج {Game.MIN_PLAYERS-c} ضحايا إضافيين...</i>"
    return f"🏰 <b>Ghosts Palace - 𝒉𝒂𝒗𝒂𝒏𝒂 𝑪𝒉𝒂𝒕🦩</b>\n\n<blockquote>🎭 <b>لعبة رعب وغموض جديدة!</b>\n👻 <i>من سيبقى حياً حتى الفجر؟</i></blockquote>\n👥 <b>اللاعبون ({c}/{Game.MAX_PLAYERS}):</b>\n{pl}\n{st}"

def lobby_kb(g):
    c=len(g.players); b=[[InlineKeyboardButton("🎮 انضم للعبة!",callback_data=f"join_{g.chat_id}")]]
    if c>=Game.MIN_PLAYERS: b.append([InlineKeyboardButton("🚀 ابدأ اللعبة!",callback_data=f"sg_{g.chat_id}")])
    b.append([InlineKeyboardButton("❌ إلغاء",callback_data=f"cg_{g.chat_id}")]); return InlineKeyboardMarkup(b)

async def update_lobby(bot,g):
    if not g.lobby_msg_id: return
    try: await bot.edit_message_text(chat_id=g.chat_id,message_id=g.lobby_msg_id,text=lobby_text(g),parse_mode="HTML",reply_markup=lobby_kb(g))
    except: pass

# ── Commands ──
async def cmd_start(update,context):
    if update.effective_chat.type=="private":
        await update.message.reply_text("🏰 <b>مرحبًا بك في Ghosts Palace!</b>\n\n<blockquote>👻 <b>لعبة مافيا مبنية على الغموض والرعب!</b>\n\n📌 <b>كيف تلعب:</b>\n1️⃣ أضفني لمجموعة\n2️⃣ اكتب /start لفتح لعبة\n3️⃣ اللاعبين ينضمون بالزر\n4️⃣ ابدأ اللعبة واستمتع بقضاء ليلة مرعبة!</blockquote>\n\n🎮 الأوامر المتاحة: /role - /alive - /stats - /leaderboard",parse_mode="HTML"); return
    cid=update.effective_chat.id; ex=gm.get(cid)
    if ex and ex.phase!=Phase.GAME_OVER: await update.message.reply_text("⚠️ <b>يوجد لعبة قائمة بالفعل!</b>",parse_mode="HTML"); return
    g=gm.create(cid)
    try: await send_start_cover(context.bot, cid, "👻 <b>الأشباح تستيقظ...</b>\n🏰 <b>القصر يفتح أبوابه...</b>\n\n🌑 <i>استعدّوا لليلة طويلة مظلمة.</i>", parse_mode="HTML")
    except Exception: pass
    await asyncio.sleep(1)
    m=await ssend(context.bot,cid,lobby_text(g),parse_mode="HTML",reply_markup=lobby_kb(g))
    if m: g.lobby_msg_id=m.message_id

async def cmd_join(update,context):
    if update.effective_chat.type=="private": return
    g=gm.get(update.effective_chat.id)
    if not g or g.phase!=Phase.LOBBY: await update.message.reply_text("⚠️ لا توجد لعبة مفتوحة حالياً!"); return
    u=update.effective_user; name=u.first_name or u.username or f"U{u.id}"
    if g.add_player(u.id,name): await update_lobby(context.bot,g)
    else: await update.message.reply_text("⚠️ أنت منضم بالفعل، أو اللعبة ممتلئة!")

async def cmd_startgame(update,context):
    if update.effective_chat.type=="private": return
    cid=update.effective_chat.id; g=gm.get(cid)
    if not g or g.phase!=Phase.LOBBY: return
    if len(g.players)<Game.MIN_PLAYERS: await update.message.reply_text(f"⚠️ <b>نحتاج {Game.MIN_PLAYERS} لاعبين على الأقل!</b>", parse_mode="HTML"); return
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
            if p.is_vampire: extra="\n🧛 <i>لقد تم تحويلك لمصاص دماء!</i>"
            if p.dog_transformed: extra="\n🐺 <i>لقد تحولت إلى ذئب!</i>"
            msg = f"🎭 <b>تذكير بدورك:</b>\n<blockquote>{rd.emoji} <b>{rd.display}</b>\n📝 {rd.description}\n👥 <b>فريقك:</b> {tt.get(p.team.value if p.team else 'villager','❓')}{extra}</blockquote>"
            await sdm(context.bot,uid,msg,parse_mode="HTML")
            if update.effective_chat.type!="private": await update.message.reply_text("📩 <b>تم إرسال دورك في الخاص!</b>",parse_mode="HTML")
            return
    await update.message.reply_text("⚠️ لست مسجلاً في أي لعبة نشطة!")

async def cmd_alive(update,context):
    if update.effective_chat.type=="private": return
    g=gm.get(update.effective_chat.id)
    if not g or g.phase in (Phase.LOBBY,Phase.GAME_OVER): await update.message.reply_text("⚠️ لا توجد لعبة نشطة!"); return
    alive=g.alive_players; dead=[p for p in g.players.values() if not p.alive]
    t=f"👥 <b>الأحياء ({len(alive)}):</b>\n<blockquote>" + "\n".join(f"✅ <i>{p.name}</i>" for p in alive) + "</blockquote>"
    if dead: t+=f"\n💀 <b>الأموات ({len(dead)}):</b>\n<blockquote>" + "\n".join(f"☠️ <i>{p.name}</i>" for p in dead) + "</blockquote>"
    await update.message.reply_text(t,parse_mode="HTML")

async def cmd_stats(update,context):
    uid=str(update.effective_user.id); s=load_stats()
    if uid not in s: await update.message.reply_text("📊 <b>لا توجد إحصائيات لك بعد!</b>", parse_mode="HTML"); return
    d=s[uid]; wr=(d.get('wins',0)/d.get('games',1))*100 if d.get('games',0)>0 else 0
    t = f"📊 <b>إحصائياتك يا {d['name']}:</b>\n<blockquote>🎮 ألعاب لعبتها: <b>{d.get('games',0)}</b>\n🏆 مرات الفوز: <b>{d.get('wins',0)}</b>\n💀 مرات الخسارة: <b>{d.get('losses',0)}</b>\n📈 نسبة الفوز: <b>{wr:.0f}%</b>\n🔪 ضحاياك: <b>{d.get('kills',0)}</b>\n🛡️ مرات النجاة: <b>{d.get('survived',0)}</b>\n⭐ حصلت على MVP: <b>{d.get('mvp',0)} مرة</b></blockquote>"
    await update.message.reply_text(t,parse_mode="HTML")

async def cmd_leaderboard(update,context):
    s=load_stats()
    if not s: await update.message.reply_text("📊 لا توجد إحصائيات بعد!"); return
    sp=sorted(s.items(),key=lambda x:x[1].get("wins",0),reverse=True)[:10]
    medals=["🥇","🥈","🥉"]
    lines=[f"{medals[i] if i<3 else f'<b>#{i+1}</b>'} <b>{d['name']}</b> — 🏆{d.get('wins',0)} | 🔪{d.get('kills',0)} | ⭐{d.get('mvp',0)}" for i,(u,d) in enumerate(sp)]
    t = f"🏆 <b>لوحة الشرف لأفضل القتلة والناجين:</b>\n<blockquote>" + "\n".join(lines) + "</blockquote>"
    await update.message.reply_text(t,parse_mode="HTML")

async def cmd_endgame(update,context):
    if update.effective_chat.type=="private": return
    cid=update.effective_chat.id; g=gm.get(cid)
    if not g: await update.message.reply_text("⚠️ لا توجد لعبة لإنهائها!"); return
    g.phase=Phase.GAME_OVER
    if g._task and not g._task.done(): g._task.cancel()
    rt="\n".join(f"{'💀' if not p.alive else '✅'} <i>{p.name}</i> — {p.display_role}" for p in g.players.values())
    await ssend(context.bot,cid,f"🛑 <b>تم إنهاء اللعبة قسرياً!</b>\n\n<blockquote>🎭 <b>الأدوار كانت:</b>\n{rt}</blockquote>\n\n<i>اكتب /start للعبة جديدة!</i>",parse_mode="HTML")
    gm.remove(cid)

async def cmd_players(update,context):
    if update.effective_chat.type=="private": return
    g=gm.get(update.effective_chat.id)
    if not g: await update.message.reply_text("⚠️ لا توجد لعبة!"); return
    if g.phase==Phase.LOBBY:
        t="👥 <b>اللاعبون المنضمون:</b>\n<blockquote>" + "\n".join(f"• <i>{p.name}</i>" for p in g.players.values()) + f"</blockquote>\n📊 المجموع: <b>{len(g.players)}/{Game.MAX_PLAYERS}</b>"
    else:
        t="👥 <b>حالة اللاعبين:</b>\n<blockquote>" + "\n".join(f"{'✅' if p.alive else '💀'} <i>{p.name}</i>" for p in g.players.values()) + f"</blockquote>\n📊 الأحياء: <b>{len(g.alive_players)}/{len(g.players)}</b>"
    await update.message.reply_text(t,parse_mode="HTML")

# ── Callbacks ──
async def join_cb(update,context):
    q=update.callback_query; d=q.data
    if d.startswith("join_"):
        cid=int(d.split("_")[1]); g=gm.get(cid)
        if not g or g.phase!=Phase.LOBBY: await q.answer("⚠️ غير متاحة!",show_alert=True); return
        u=q.from_user; name=u.first_name or u.username or f"U{u.id}"
        if u.id in g.players: await q.answer("⚠️ أنت منضم بالفعل!",show_alert=True); return
        if g.add_player(u.id,name):
            test=await sdm(context.bot,u.id,"✅ <b>تم انضمامك للعبة بنجاح!</b> ⏳ <i>انتظر بدء الجولة في المجموعة.</i>")
            if not test:
                if u.id in g.players: del g.players[u.id]
                bi=await context.bot.get_me()
                await q.answer(f"⚠️ يجب عليك بدء محادثة مع البوت أولاً!\nاضغط هنا: @{bi.username}",show_alert=True); return
            await q.answer(f"✅ انضممت يا {name}!",show_alert=False); await update_lobby(context.bot,g)
        else: await q.answer("⚠️ اللعبة ممتلئة!",show_alert=True)
    elif d.startswith("sg_"):
        cid=int(d.split("_")[1]); g=gm.get(cid)
        if not g or g.phase!=Phase.LOBBY: await q.answer("⚠️ غير متاحة!",show_alert=True); return
        if len(g.players)<Game.MIN_PLAYERS: await q.answer(f"⚠️ نحتاج {Game.MIN_PLAYERS} لاعبين!",show_alert=True); return
        await q.answer("🚀 جاري بدء اللعبة...")
        try: await context.bot.edit_message_reply_markup(chat_id=cid,message_id=g.lobby_msg_id,reply_markup=None)
        except: pass
        await start_logic(context.bot,g,cid)
    elif d.startswith("cg_"):
        cid=int(d.split("_")[1]); g=gm.get(cid)
        if g and g.phase==Phase.LOBBY:
            lid=g.lobby_msg_id; gm.remove(cid); await q.answer("❌ تم الإلغاء!",show_alert=True)
            try: await context.bot.edit_message_text(chat_id=cid,message_id=lid,text="❌ <b>تم إلغاء اللعبة.</b>\n<i>اكتب /start لفتح لعبة جديدة.</i>",parse_mode="HTML")
            except: pass

# ── Start Logic ──
async def start_logic(bot,g,cid):
    g.assign_roles(); plist="🎭 <b>قائمة اللاعبين:</b>\n<blockquote>"; fails=[]
    tt={"villager":"الأبرياء 🛡️","evil":"الأشرار 😈","dracula":"دراكولا 🧛","solo":"وحيد 🧌"}
    for p in g.players.values():
        plist+=f"• <i>{p.name}</i>\n"; rd=p.role_def
        r=await sdm(bot,p.user_id,f"🎭 <b>دورك في هذه اللعبة:</b>\n\n<blockquote>{rd.emoji} <b>{rd.display}</b>\n📝 {rd.description}\n👥 <b>فريقك:</b> {tt.get(rd.team.value,'❓')}</blockquote>\n\n⚠️ <i>لا تكشف دورك لأحد!</i>\n💡 للعودة لمعرفة دورك لاحقاً اكتب /role",parse_mode="HTML")
        if not r: fails.append(p.name)
        update_stat(p.user_id,p.name,"games")
    plist+="</blockquote>"
    await ssend(bot,cid,f"🎲 <b>تم توزيع الأدوار وبدأت اللعبة!</b>\n\n{plist}\n📩 <b>تأكدوا من الرسائل الخاصة لمعرفة أدواركم!</b>\n\n💡 <i>استخدم الأوامر: /role | /alive | /stats</i>",parse_mode="HTML")
    if fails:
        bi=await bot.get_me()
        await ssend(bot,cid,"⚠️ <b>تنبيه هام!</b>\n\nلم أتمكن من إرسال الدور لهؤلاء اللاعبين (الخاص مغلق):\n<blockquote>" + "\n".join(f"• {n}" for n in fails) + f"</blockquote>\n\n📩 افتحوا البوت من هنا: https://t.me/{bi.username}\n⏳ ثم أرسلوا /start من جديد.",parse_mode="HTML")
        g.phase=Phase.GAME_OVER; gm.remove(cid); return
    evils=[p for p in g.players.values() if p.role_def.team==Team.EVIL]
    if len(evils)>1:
        for ep in evils:
            others=[f"<i>{o.name}</i> ({o.role_def.emoji} {o.role_def.display})" for o in evils if o.user_id!=ep.user_id]
            await sdm(bot,ep.user_id,"😈 <b>حلفاء الشر (فريقك):</b>\n<blockquote>" + "\n".join(f"• {o}" for o in others) + "</blockquote>",parse_mode="HTML")
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
        emsg=""
        for ek,ed in RANDOM_EVENTS.items():
            if random.random()<ed["chance"] and g.round_num>1:
                g.event=ek
                if ek=="storm": g.storm=True
                elif ek=="fog": g.fog=True
                emsg=f"\n\n<blockquote>{ed['name']}\n<i>{ed['desc']}</i></blockquote>"; break
        await sgif(bot,g.chat_id,"night",f"🌙 <b>الليلة {g.round_num}</b>\n\n{random.choice(NIGHT_MESSAGES)}{emsg}\n\n⏳ <i>الظلام يخيم... لديكم {Game.NIGHT_DUR} ثانية لاستخدام قدراتكم في الخاص.</i>",parse_mode="HTML")
        if g.event=="blood_moon":
            rp=random.choice(g.alive_players); await asyncio.sleep(2)
            await ssend(bot,g.chat_id,f"🔴 <b>ضوء القمر الدموي يسقط على أحدهم:</b>\n👤 لقد اتضح أن <i>{rp.name}</i> هو <b>{rp.display_role}</b>!",parse_mode="HTML")
            g.log("night","قمر دموي","",f"{rp.name}={rp.display_role}")
        for p in g.alive_players: await send_night(bot,g,p)
        th=Game.NIGHT_DUR//3
        await asyncio.sleep(th)
        await ssend(bot,g.chat_id,f"⏳ <i>متبقي {th*2} ثانية... أسرعوا في الظلام!</i>")
        await asyncio.sleep(th)
        await ssend(bot,g.chat_id,f"🔥 <b>آخر {th} ثانية!</b> ⚠️ <i>تأكدوا من قراراتكم الآن!</i>",parse_mode="HTML")
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
    if role==RoleName.CRIMINAL: text="🔪 <b>اختر ضحيتك لهذه الليلة:</b>"; cp="nc"
    elif role==RoleName.GHOST_KILLER: text="👻 <b>اختر من ستنتزع روحه بصمت:</b>"; cp="ng"
    elif role==RoleName.MAID: text="🤵‍♀️ <b>اختر من تريدين كشف هويته:</b>"; cp="nm"
    elif role==RoleName.CHEF: text="🧑‍🍳 <b>اختر من ستضع السم في طعامه:</b>"; cp="nch"
    elif role==RoleName.THIEF:
        if player.thief_used: return
        text="🥷 <b>اختر من ستسرق دوره (مرة واحدة):</b>"; cp="nt"
    elif role==RoleName.POLICE: text="👮‍♀️ <b>اختر شخصاً للتحقيق معه:</b>"; cp="np"
    elif role==RoleName.DOORMAN:
        if player.doorman_used: return
        kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ نعم، إعلان هدنة!",callback_data=f"nd_{g.chat_id}_y")],[InlineKeyboardButton("❌ لا",callback_data=f"nd_{g.chat_id}_n")]])
        await sdm(bot,player.user_id,"🧑‍✈️ <b>هل تريد إعلان هدنة وإيقاف التصويت نهاراً؟ (مرة واحدة)</b>",reply_markup=kb,parse_mode="HTML"); return
    elif role==RoleName.NEIGHBOR: text="😘 <b>اختر من ستراقبين منزله الليلة:</b>"; cp="nn"
    elif role==RoleName.FOREST_GUARD:
        if g.fog: await sdm(bot,player.user_id,"🌫️ <b>الضباب الكثيف يمنعك من الخروج والحماية الليلة!</b>",parse_mode="HTML"); return
        targets=[p for p in targets if p.user_id!=g.guard_last]
        if not targets: return
        text="🧙‍♀️ <b>اختر من تريد حمايته الليلة:</b>"; cp="nfg"
    elif role==RoleName.BATMAN:
        if player.batman_bullets<=0: return
        text=f"🦹‍♂️ <b>اختر هدفاً (متبقي {player.batman_bullets} طلقات):</b>"; cp="nb"
    elif role==RoleName.WITCH: text="🧝‍♀️ <b>اختر الضحية الأولى لربط مصيرها:</b>"; cp="nw1"
    elif role==RoleName.DRACULA:
        targets=[p for p in targets if not p.is_vampire and p.role!=RoleName.DRACULA]
        if not targets: return
        text="🧛 <b>اختر من ستعضه لتحويله إلى مصاص دماء:</b>"; cp="ndr"
    else: return
    btns=[]; row=[]
    for i,t in enumerate(targets):
        row.append(InlineKeyboardButton(t.name,callback_data=f"{cp}_{g.chat_id}_{t.user_id}"))
        if len(row)==2 or i==len(targets)-1: btns.append(row); row=[]
    btns.append([InlineKeyboardButton("⏭️ تخطي",callback_data=f"{cp}_{g.chat_id}_skip")])
    await sdm(bot,player.user_id,text,reply_markup=InlineKeyboardMarkup(btns),parse_mode="HTML")

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
        if not g or g.phase!=Phase.NIGHT: await q.edit_message_text("⚠️ <b>انتهى وقت الليل.</b>",parse_mode="HTML"); return
        uid=q.from_user.id; p=g.get_player(uid)
        if not p or not p.alive: return
        ak=f"{at}_{uid}"
        if ak in g.night_actions and at!="nw1": await q.edit_message_text("✅ <b>تم تسجيل قرارك مسبقاً!</b>",parse_mode="HTML"); return
        if tv=="skip" or tv=="n": g.night_actions[ak]="skip"; await q.edit_message_text("⏭️ <i>تم تخطي الإجراء الليلة.</i>",parse_mode="HTML"); return
        if tv=="y" and at=="nd":
            g.night_actions[ak]="truce"; g.truce=True; p.doorman_used=True
            g.log("night","هدنة",p.name,""); await q.edit_message_text("🛑 <b>تم تفعيل الهدنة! لن يكون هناك إعدام غداً.</b>",parse_mode="HTML"); return
        tid=int(tv); tgt=g.get_player(tid)
        if at=="nc": g.night_actions[ak]=tid; g.log("night","قتل",p.name,tgt.name if tgt else "?"); await q.edit_message_text(f"🔪 هدفك للقتل الليلة: <b>{tgt.name if tgt else '?'}</b>",parse_mode="HTML")
        elif at=="ng": g.night_actions[ak]=tid; g.log("night","قتل شبح",p.name,tgt.name if tgt else "?"); await q.edit_message_text(f"👻 ستخنق <b>{tgt.name if tgt else '?'}</b> بصمت...",parse_mode="HTML")
        elif at=="nm":
            g.night_actions[ak]=tid
            if tgt:
                if tgt.role==RoleName.GHOST_KILLER:
                    fk=random.choice([RoleName.PAINTER,RoleName.CHIEF,RoleName.NEIGHBOR]); rd=ROLE_DEFS[fk]
                    await q.edit_message_text(f"🔍 نتيجة الكشف: <b>{tgt.name}</b> دوره هو {rd.emoji} {rd.display} (مضلل)",parse_mode="HTML")
                else: p.investigations+=1; await q.edit_message_text(f"🔍 نتيجة الكشف: <b>{tgt.name}</b> دوره هو {tgt.display_role}",parse_mode="HTML")
        elif at=="nch": g.night_actions[ak]=tid; await q.edit_message_text(f"☠️ قمت بوضع السم في طعام <b>{tgt.name if tgt else '?'}</b>",parse_mode="HTML")
        elif at=="nt":
            g.night_actions[ak]=tid; p.thief_used=True
            if tgt: sr=tgt.role; tgt.role=RoleName.PAINTER; p.role=sr; await q.edit_message_text(f"🥷 <b>نجحت!</b> سرقت دور <i>{tgt.name}</i>!\n🎭 دورك الجديد أصبح: {p.display_role}",parse_mode="HTML")
        elif at=="np":
            g.night_actions[ak]=tid
            if tgt:
                ik=tgt.team in (Team.EVIL,Team.DRACULA)
                if tgt.role==RoleName.GHOST_KILLER: ik=False
                r="🔴 <b>مجرم وخطير!</b>" if ik else "🟢 <b>بريء ومسالم.</b>"
                if ik: p.investigations+=1
                await q.edit_message_text(f"🔎 نتيجة التحقيق لـ <b>{tgt.name}</b>: {r}",parse_mode="HTML")
        elif at=="nn": g.night_actions[ak]=tid; p.visited_target=tid; await q.edit_message_text(f"😘 ستقومين بمراقبة <b>{tgt.name if tgt else '?'}</b> الليلة.",parse_mode="HTML")
        elif at=="nfg":
            g.night_actions[ak]=tid
            if tgt: tgt.protected=True; g.guard_last=tid; await q.edit_message_text(f"🛡️ ستقوم بحماية <b>{tgt.name}</b> من الموت.",parse_mode="HTML")
        elif at=="nb":
            g.night_actions[ak]=tid; p.batman_bullets-=1
            await q.edit_message_text(f"🦹‍♂️ أطلقت النار على <b>{tgt.name if tgt else '?'}</b>! (متبقي: {p.batman_bullets})",parse_mode="HTML")
        elif at=="nw1":
            g.night_actions[f"w1_{uid}"]=tid
            t2=[x for x in g.alive_players if x.user_id!=uid and x.user_id!=tid]
            if t2:
                btns=[]; row=[]
                for i,t in enumerate(t2):
                    row.append(InlineKeyboardButton(t.name,callback_data=f"nw2_{cid}_{t.user_id}"))
                    if len(row)==2 or i==len(t2)-1: btns.append(row); row=[]
                btns.append([InlineKeyboardButton("⏭️ تخطي",callback_data=f"nw2_{cid}_skip")])
                await q.edit_message_text(f"🧝‍♀️ الضحية الأولى: <b>{tgt.name if tgt else '?'}</b>.\nالآن اختر الضحية الثانية للربط:",reply_markup=InlineKeyboardMarkup(btns),parse_mode="HTML")
        elif at=="nw2":
            ft=g.night_actions.get(f"w1_{uid}")
            if ft: g.witch_links[ft]=tid; g.witch_links[tid]=ft; t1=g.get_player(ft); await q.edit_message_text(f"🧝‍♀️ <b>تم التعويذة!</b> ارتبط مصير <b>{t1.name if t1 else '?'}</b> مع <b>{tgt.name if tgt else '?'}</b>!",parse_mode="HTML")
        elif at=="ndr": g.night_actions[ak]=tid; await q.edit_message_text(f"🧛 قمت بعض <b>{tgt.name if tgt else '?'}</b> ليتحول إلى مصاص دماء.",parse_mode="HTML")
    except Exception as e: logger.error(f"Night cb err:{e}",exc_info=True)

# ── Resolve Night ──
async def resolve_night(bot,g):
    killed=[]; msgs=[]
    if not g.storm:
        for k,v in g.night_actions.items():
            if k.startswith("nc_") and v!="skip" and isinstance(v,int):
                t=g.get_player(v)
                if t and t.alive and not t.protected:
                    if t.role==RoleName.DOG and not t.dog_transformed: t.dog_transformed=True; msgs.append("🌙 <b>في عمق الليل… صرخة تمزق السكون!</b>\n🐶→🐺 أحدهم هاجم الكلب، فتحول إلى ذئب مفترس!")
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
                    if t.role==RoleName.DOG and not t.dog_transformed: t.dog_transformed=True; msgs.append("🐶→🐺 هجوم خفي أيقظ الوحش بالداخل! الكلب تحول لذئب!")
                    else: killed.append(v)
        for k,v in g.night_actions.items():
            if k.startswith("nb_") and v!="skip" and isinstance(v,int):
                t=g.get_player(v)
                if t and t.alive and v not in killed: killed.append(v)
    else:
        await sgif(bot,g.chat_id,"storm","⛈️ <b>عاصفة هوجاء ضربت القرية!</b>\nالجميع بقوا في منازلهم... لم يُقتل أحد الليلة!",parse_mode="HTML")
    
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
                await sdm(bot,t.user_id,"🧛 <b>أنياب انغرزت في عنقك... لقد تحولت!</b>\n😈 أنت الآن مصاص دماء وتعمل مع دراكولا!",parse_mode="HTML")
    
    # Neighbor
    for p in g.alive_players:
        if p.visited_target:
            t=g.get_player(p.visited_target)
            if t:
                left=any(k.endswith(f"_{t.user_id}") and v!="skip" for k,v in g.night_actions.items())
                await sdm(bot,p.user_id,f"😘 <b>نتيجة المراقبة:</b>\n{t.name} {'🚪 <b>لم يكن في منزله الليلة!</b>' if left else '🏠 <b>كان نائماً في بيته.</b>'}",parse_mode="HTML")
    
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
        await ssend(bot,g.chat_id,"🌅 <b>أشرقت الشمس…</b>\n😳 الجميع على قيد الحياة! العناية الإلهية تدخلت الليلة.",parse_mode="HTML")
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
                await sgif(bot,g.chat_id,f"death_{kt}",f"💀 <b>اكتشاف جثة!</b>\n\n<blockquote>جثة <b>{p.name}</b> ملقاة على الأرض… ملامح الرعب تملأ وجهه.\n\n🎭 كان دوره: {p.display_role}\n<i>{dm}</i></blockquote>",parse_mode="HTML")
                dmt={"criminal":"🔪 <b>المجرم طعنك بلا رحمة!</b>","ghost":"👻 <b>شبح أسود خنقك في نومك!</b>","batman":"🦹‍♂️ <b>رصاصة مجهولة استقرت في رأسك!</b>","poison":"☠️ <b>السم مزق أحشاءك!</b>","generic":"💀 <b>لقد لقيت حتفك!</b>"}
                await sgif_dm(bot,p.user_id,f"death_{kt}",f"🩸 {dmt.get(kt,dmt['generic'])}\n\n🎭 دورك كان: {p.display_role}\n👻 أنت الآن شبح، يمكنك مشاهدة اللعبة فقط.",parse_mode="HTML")
                g.log("night","مقتل",kt,p.name); await asyncio.sleep(2)
    for m in msgs: await sgif(bot,g.chat_id,"dog_transform",m,parse_mode="HTML"); await asyncio.sleep(2)
    w=g.check_win()
    if w: await announce_win(bot,g,w); return
    await asyncio.sleep(3); g._task=asyncio.create_task(run_day(bot,g))

# ══════════════════════════════════════════════
# DAY
async def run_day(bot,g):
    try:
        g.phase=Phase.DAY
        at="\n".join(f"• <i>{p.name}</i>" for p in g.alive_players)
        msg = f"🌅 <b>الجولة {g.round_num} بدأت</b>\n\n<i>{random.choice(DAY_MESSAGES)}</i>\n\n👥 <b>الأحياء ({len(g.alive_players)}):</b>\n<blockquote>{at}</blockquote>\n\n⏳ <b>أمامكم {Game.DISC_DUR} ثانية للنقاش وتوجيه الاتهامات…</b>\n🗳️ وبعدها سيُفتح باب التصويت لتحديد من سيُعدم."
        await sgif(bot,g.chat_id,"day",msg,parse_mode="HTML")
        for p in g.alive_players:
            if p.role in (RoleName.CRIMINAL, RoleName.GHOST_KILLER, RoleName.BATMAN):
                await sdm(bot,p.user_id,"⏳ <b>النهار يمر بسرعة...</b>\n\n🩸 استعد للتصويت بحذر حتى لا تُكشف هويتك.",parse_mode="HTML")
        await asyncio.sleep(Game.DISC_DUR//2)
        await ssend(bot,g.chat_id,f"<i>{random.choice(SUSPENSE)}</i>",parse_mode="HTML")
        await asyncio.sleep(Game.DISC_DUR//2)
        if g.truce:
            await sgif(bot,g.chat_id,"truce","🛑 <b>البواب يعلن الهدنة!</b>\n🚫 لا يوجد تصويت ولا إعدام في هذا النهار.\n🌲 عودوا لمنازلكم واستعدوا لليلة جديدة...",parse_mode="HTML")
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
        await sgif(bot,g.chat_id,"vote","⚖️ <b>حان وقت المحاكمة!</b>\n\n📩 <i>تفقدوا رسائلكم الخاصة للتصويت.</i>\n⏳ التصويت سري، ولكن سيتم كشف أصوات الجميع في النهاية.\n(إذا صوت الجميع، تُعلن النتيجة فوراً)",parse_mode="HTML")
        for p in alive:
            tgts=[x for x in alive if x.user_id!=p.user_id]; btns=[]; row=[]
            for i,t in enumerate(tgts):
                row.append(InlineKeyboardButton(t.name,callback_data=f"v_{g.chat_id}_{t.user_id}"))
                if len(row)==2 or i==len(tgts)-1: btns.append(row); row=[]
            btns.append([InlineKeyboardButton("⏭️ الامتناع عن التصويت",callback_data=f"v_{g.chat_id}_skip")])
            await sdm(bot,p.user_id,f"⚖️ <b>محكمة القرية</b>\n🎯 من تظن أنه القاتل؟\n⏳ <i>أمامك {Game.VOTE_DUR} ثانية.</i>",parse_mode="HTML",reply_markup=InlineKeyboardMarkup(btns))
        try:
            await asyncio.wait_for(g.vote_event.wait(), timeout=Game.VOTE_DUR)
        except asyncio.TimeoutError: pass
        g.vote_closed=True
        
        for p in alive:
            if p.role==RoleName.MADMAN and p.alive and p.user_id not in g.votes:
                ps=[t for t in alive if t.user_id!=p.user_id]
                if ps: g.votes[p.user_id]=random.choice(ps).user_id
        
        if g.votes:
            vr="🗳️ <b>سجلات المحكمة (كشف الأصوات):</b>\n<blockquote>"
            for vi,ti in g.votes.items():
                vt=g.get_player(vi)
                if ti==-1: vr+=f"⚪ <i>{vt.name}</i> ← فضل الصمت (امتنع)\n"
                else: tt=g.get_player(ti); vr+=f"🩸 <i>{vt.name}</i> اتهم ➡️ <b>{tt.name if tt else '?'}</b>\n"
            for p in alive:
                if p.user_id not in g.votes: vr+=f"❌ <i>{p.name}</i> ← لم يحضر المحاكمة\n"
            vr+="</blockquote>"
            await ssend(bot,g.chat_id,vr,parse_mode="HTML")
        await resolve_votes(bot,g)
    except asyncio.CancelledError: pass
    except Exception as e: logger.error(f"Vote err:{e}",exc_info=True)

async def vote_cb(update,context):
    q=update.callback_query; d=q.data
    if not d.startswith("v_"): return
    pp=d.split("_"); cid=int(pp[1]); tv=pp[2]
    g=gm.get(cid)
    if not g or g.phase!=Phase.VOTING or g.vote_closed: await q.answer("⚠️ انتهى وقت التصويت!",show_alert=True); return
    vid=q.from_user.id; vt=g.get_player(vid)
    if not vt: await q.answer("⚠️ لست من ضمن الأحياء!",show_alert=True); return
    if not vt.alive: await q.answer("💀 الأشباح لا تصوت!",show_alert=True); return
    if vid in g.votes: await q.answer("⚠️ قمت بالإدلاء بصوتك مسبقاً!",show_alert=True); return
    
    if vt.role==RoleName.MADMAN:
        ps=[p for p in g.alive_players if p.user_id!=vid]
        if ps:
            g.votes[vid]=random.choice(ps).user_id
            await q.edit_message_text("🤡 <i>ضحكة جنونية... تم التصويت عشوائياً!</i>",parse_mode="HTML")
            if g.vote_expected and g.vote_expected.issubset(g.votes.keys()) and g.vote_event and not g.vote_event.is_set():
                g.vote_event.set()
        return
        
    if tv=="skip":
        g.votes[vid]=-1
        await q.edit_message_text("⏭️ <b>اخترت الامتناع عن التصويت.</b>",parse_mode="HTML")
    else:
        tid=int(tv); g.votes[vid]=tid; tgt=g.get_player(tid)
        await q.edit_message_text(f"✅ قمت باتهام <b>{tgt.name if tgt else '?'}</b>.\n⏳ انتظر نتيجة المحكمة...",parse_mode="HTML")
        
    if g.vote_expected and g.vote_expected.issubset(g.votes.keys()) and g.vote_event and not g.vote_event.is_set():
        g.vote_event.set()

async def resolve_votes(bot,g):
    if not g.votes:
        await ssend(bot,g.chat_id,"⚖️ <b>لم يصوت أحد! المحكمة تُرفع.</b>\n🌙 الظلام يعود...",parse_mode="HTML")
        g._task=asyncio.create_task(run_night(bot,g)); return
    vc={}
    for vi,ti in g.votes.items():
        if ti!=-1: vc[ti]=vc.get(ti,0)+1
    if not vc:
        await ssend(bot,g.chat_id,"⚖️ <b>الجميع امتنعوا عن التصويت!</b>\n🌙 العودة للظلام...",parse_mode="HTML")
        g._task=asyncio.create_task(run_night(bot,g)); return
        
    mx=max(vc.values()); tops=[u for u,c in vc.items() if c==mx]
    slines=[]
    for u,c in sorted(vc.items(),key=lambda x:-x[1]):
        p=g.get_player(u)
        if p: bar="🟥"*c+"⬜"*(len(g.alive_players)-c); slines.append(f"• <i>{p.name}</i>: {bar} ({c})")
    summary="<blockquote>" + "\n".join(slines) + "</blockquote>"
    
    if len(tops)>1:
        await ssend(bot,g.chat_id,f"⚖️ <b>النتائج النهائية:</b>\n{summary}\n\n⚖️ <b>الأصوات تعادلت! لن يتم إعدام أحد اليوم.</b>\n🌙 استعدوا لليلة جديدة...",parse_mode="HTML")
        g._task=asyncio.create_task(run_night(bot,g)); return
        
    tid=tops[0]; tgt=g.get_player(tid)
    if not tgt: g._task=asyncio.create_task(run_night(bot,g)); return
    
    # Grocer
    if tgt.role==RoleName.GROCER and tgt.alive:
        tgt.alive=False
        await ssend(bot,g.chat_id,f"⚖️ <b>النتائج:</b>\n{summary}\n\n🧌 <b>مفاجأة مرعبة!!</b>\nلقد أعدمتم صاحب البقالة <b>{tgt.name}</b> عن طريق الخطأ!\n😈 <b>انفجر غضبه وأحرق القرية بمن فيها... فاز البقال وحده!!</b>\n💀 الجميع خسر...",parse_mode="HTML")
        await announce_win(bot,g,"grocer",tgt.name); return
        
    # Prince
    if tgt.role==RoleName.PRINCE and tgt.prince_lives>0:
        tgt.prince_lives-=1
        await ssend(bot,g.chat_id,f"⚖️ <b>النتائج:</b>\n{summary}\n\n👑 <b>مهلاً!</b> المحكوم عليه هو الأمير <b>{tgt.name}</b>!\nعفا عن نفسه بحصانته الملكية هذه المرة.\n🌙 عودوا للظلام...",parse_mode="HTML")
        g._task=asyncio.create_task(run_night(bot,g)); return
        
    # Last words
    g.phase=Phase.LAST_WORDS
    await ssend(bot,g.chat_id,f"⚖️ <b>النتائج:</b>\n{summary}\n\n⏳ المحكمة قررت إعدام <b>{tgt.name}</b>!\n🗣️ <b>لديك {Game.LAST_WORDS_DUR} ثانية لقول كلماتك الأخيرة قبل الموت...</b>",parse_mode="HTML")
    g.log("vote","محكوم",tgt.name,"")
    await asyncio.sleep(Game.LAST_WORDS_DUR)
    
    tgt.alive=False; dm=DEATH_MSGS.get(tgt.role,"💀 رحل في صمت…")
    await sgif(bot,g.chat_id,"death_vote",f"⚖️ <b>تم تنفيذ حكم الإعدام!</b>\n\n<blockquote>جثة <b>{tgt.name}</b> تتأرجح الآن.\n🎭 اتضح أن دوره هو: {tgt.display_role}\n\n<i>{dm}</i></blockquote>",parse_mode="HTML")
    g.log("vote","إعدام","",f"{tgt.name} ({tgt.display_role})")
    
    if tgt.user_id in g.witch_links:
        lu=g.witch_links[tgt.user_id]; lp=g.get_player(lu)
        if lp and lp.alive:
            lp.alive=False; ld=DEATH_MSGS.get(lp.role,"💀 رحل مع رفيقه…")
            await asyncio.sleep(2)
            await ssend(bot,g.chat_id,f"🧝‍♀️ <b>لعنة التعويذة!</b>\n💀 بسبب رابط الساحرة، سقط أيضاً: <b>{lp.name}</b>\n<blockquote>🎭 كان دوره: {lp.display_role}\n<i>{ld}</i></blockquote>",parse_mode="HTML")
            
    w=g.check_win()
    if w: await asyncio.sleep(3); await announce_win(bot,g,w); return
    await asyncio.sleep(3); g._task=asyncio.create_task(run_night(bot,g))

# ══════════════════════════════════════════════
# WINNER
# ══════════════════════════════════════════════
async def announce_win(bot, g, winner, gn=""):
    g.phase = Phase.GAME_OVER
    
    if winner == "village": 
        txt = "🏆 <b>انقشع ظلام القرية!</b>\n🎉 <b>الأبرياء انتصروا!</b>\n🛡️ تم القضاء على جميع الأشرار، وعاد السلام أخيراً إلى القصر."
        gk = "win_village"; wt = Team.VILLAGER
    elif winner == "evil": 
        txt = "💀 <b>القرية سقطت!</b>\n😈 <b>الأشرار هم المنتصرون!</b>\n🩸 الظلام ابتلع كل شيء… ولم ينجُ من الصالحين أحد."
        gk = "win_evil"; wt = Team.EVIL
    elif winner == "dracula": 
        txt = "🧛‍♂️ <b>الليل لن ينتهي أبدًا…</b>\n🩸 <b>دراكولا وجيشه انتصروا!</b>\n⚰️ مرحبًا بعصر الظلام الأبدي."
        gk = "win_dracula"; wt = Team.DRACULA
    elif winner == "grocer": 
        txt = f"🧌 <b>الكارثة حلت! فاز {gn} البقال وحده!!</b>\n💀 احترقت القرية عن بكرة أبيها…"
        gk = "win_evil"; wt = Team.SOLO
    else: 
        txt = "🏁 <b>انتهت اللعبة!</b>"
        gk = "win_village"; wt = None

    for p in g.players.values():
        if winner == "grocer":
            update_stat(p.user_id, p.name, "wins" if p.role == RoleName.GROCER else "losses")
        elif wt and p.team == wt: update_stat(p.user_id, p.name, "wins")
        else: update_stat(p.user_id, p.name, "losses")
        if p.alive: update_stat(p.user_id, p.name, "survived")
        if p.kills > 0: update_stat(p.user_id, p.name, "kills", p.kills)

    mvp = g.calc_mvp()
    mt = ""
    if mvp: 
        update_stat(mvp.user_id, mvp.name, "mvp")
        mt = f"\n\n<blockquote>⭐ <b>نجم الجولة الأبرز (MVP):</b>\n👤 <i>{mvp.name}</i> — {mvp.display_role}</blockquote>"

    rt = "\n".join(f"{'💀' if not p.alive else '✅'} <i>{p.name}</i> — {p.display_role}" for p in g.players.values())
    
    ls = ""
    ke = [e for e in g.log_entries if e.action in ("مقتل", "إعدام", "حماية", "تحويل", "قمر دموي", "هدنة")]
    if ke:
        ls = "\n\n<blockquote>📜 <b>سجل أحداث الدماء (مختصر):</b>\n"
        for e in ke[-8:]: 
            ls += f"🔹 ليلة/يوم {e.rnd}: {e.action}"
            ls += f" ({e.actor})" if e.actor else ""
            ls += f" ⬅️ {e.target}" if e.target else ""
            ls += "\n"
        ls += "</blockquote>"

    footer = "\n\n💡 <i>لعبة جديدة: /start | إحصائيات: /stats</i>"
    final_message = f"{txt}\n\n🎭 <b>الأدوار الكاملة:</b>\n<blockquote>{rt}</blockquote>{mt}{ls}{footer}"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="cmd_stats"), 
         InlineKeyboardButton("🏆 المتصدرين", callback_data="cmd_leaderboard")]
    ])

    try: await bot.send_animation(chat_id=g.chat_id, animation=GIFS.get(gk, GIFS["start"]), caption=final_message, parse_mode="HTML", reply_markup=kb)
    except: await ssend(bot, g.chat_id, final_message, parse_mode="HTML", reply_markup=kb)
    gm.remove(g.chat_id)

# ── Router ──
async def cb_router(update,context):
    q=update.callback_query
    if not q or not q.data: return
    d=q.data
    
    if d == "cmd_stats":
        await q.answer("💡 لمعرفة إحصائياتك، قم بإرسال الأمر /stats في المجموعة!", show_alert=True)
        return
    elif d == "cmd_leaderboard":
        await q.answer("🏆 لمعرفة المتصدرين، قم بإرسال الأمر /leaderboard في المجموعة!", show_alert=True)
        return

    if any(d.startswith(p) for p in ["nc_","ng_","nm_","nch_","nt_","np_","nd_","nn_","nfg_","nb_","nw1_","nw2_","ndr_"]): await night_cb(update,context)
    elif d.startswith("v_"): await vote_cb(update,context)
    elif d.startswith("join_") or d.startswith("sg_") or d.startswith("cg_"): await join_cb(update,context)
    else: await q.answer("⚠️ حدث خطأ أو الزر غير معروف",show_alert=True)

def main():
    TOKEN="8712365309:AAExk4vAUogk2L5wgozuE-cSq3TdEHcOSWg" # يرجى تغيير التوكن بعد الانتهاء حفاظاً على الأمان
    app=Application.builder().token(TOKEN).build()
    async def post_init(application):
        from telegram import BotCommand
        await application.bot.set_my_commands([BotCommand("start","🏰 بدء لعبة جديدة"),BotCommand("join","🎮 انضمام للعبة"),BotCommand("startgame","🚀 تشغيل اللعبة"),BotCommand("players","👥 قائمة اللاعبين"),BotCommand("alive","✅ من بقي حياً؟"),BotCommand("role","🎭 تذكير بدوري"),BotCommand("stats","📊 إحصائياتي"),BotCommand("leaderboard","🏆 لوحة المتصدرين"),BotCommand("endgame","🛑 إنهاء اللعبة الحالية")])
        logger.info("✅ Commands registered!")
    app.post_init=post_init
    for cmd,fn in [("start",cmd_start),("join",cmd_join),("startgame",cmd_startgame),("endgame",cmd_endgame),("players",cmd_players),("alive",cmd_alive),("role",cmd_role),("stats",cmd_stats),("leaderboard",cmd_leaderboard)]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CallbackQueryHandler(cb_router))
    logger.info("🏰 Ghosts Palace Bot starting...")
    app.run_polling()

if __name__=="__main__": main()
