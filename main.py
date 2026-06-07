import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
import math
import asyncio
import ssl

# ============================================================
#  إعدادات السيرفر
# ============================================================
SERVER_IP   = "roqzrp"
SERVER_PORT = "30120"
GUILD_ID    = 1510735912185630812

BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}/players.json"
INFO_URL = f"http://{SERVER_IP}:{SERVER_PORT}/info.json"

# صورة FiveM بديلة (من CDN رسمي)
FIVEM_THUMBNAIL  = "https://cdn.discordapp.com/emojis/1060951257456812082.png"
PLAYERS_PER_FIELD = 25   # عدد اللاعبين في كل حقل داخل الـ embed
TIMEOUT_SEC       = 10   # رفعنا الـ timeout

COLOR_DEFAULT = 0x5865F2
COLOR_ERROR   = 0xED4245
COLOR_SUCCESS = 0x57F287

# ============================================================
#  مساعدات
# ============================================================
def extract_identifier(identifiers: list, prefix: str):
    for ident in identifiers:
        if ident.startswith(prefix):
            return ident.replace(prefix, "")
    return None

def format_identifiers(identifiers: list) -> str:
    lines = []
    mapping = {
        "steam:"   : "🟠 Steam",
        "discord:" : "🔵 Discord",
        "license:" : "🔑 License",
        "license2:": "🔑 License2",
        "xbl:"     : "🟢 Xbox",
        "live:"    : "🟢 Live",
        "ip:"      : "🌐 IP",
    }
    for ident in identifiers:
        matched = False
        for prefix, label in mapping.items():
            if ident.startswith(prefix):
                lines.append(f"{label}: `{ident.replace(prefix,'')}`")
                matched = True
                break
        if not matched:
            lines.append(f"🔹 `{ident}`")
    return "\n".join(lines) if lines else "لا توجد معرّفات"

def error_embed(message: str) -> discord.Embed:
    embed = discord.Embed(title="FiveM Bot", description=message, color=COLOR_ERROR)
    embed.set_footer(text=f"Server: {SERVER_IP}:{SERVER_PORT}")
    return embed

# ============================================================
#  جلب البيانات — مع عدة محاولات وهيدرات متعددة
# ============================================================
HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"},
    {"User-Agent": "FiveM/1.0 (compatible)"},
    {"User-Agent": "curl/7.88.1"},
]

async def fetch_players():
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SEC)
    for headers in HEADERS_LIST:
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                async with session.get(BASE_URL, headers=headers) as r:
                    if r.status == 200:
                        return await r.json(content_type=None)
        except Exception as e:
            print(f"⚠️ محاولة فاشلة ({headers['User-Agent'][:20]}): {e}")
    return None

async def fetch_info():
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SEC)
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.get(INFO_URL, headers=HEADERS_LIST[0]) as r:
                if r.status == 200:
                    return await r.json(content_type=None)
    except Exception as e:
        print(f"❌ fetch_info: {e}")
    return None

# ============================================================
#  بناء embed القائمة الكاملة
# ============================================================
def build_full_players_embed(players_data: list) -> list[discord.Embed]:
    total = len(players_data)
    embeds = []

    chunks = [players_data[i:i+PLAYERS_PER_FIELD] for i in range(0, total, PLAYERS_PER_FIELD)]
    FIELDS_PER_EMBED = 5
    embed_chunks = [chunks[i:i+FIELDS_PER_EMBED] for i in range(0, len(chunks), FIELDS_PER_EMBED)]

    for idx, group in enumerate(embed_chunks):
        if idx == 0:
            embed = discord.Embed(
                title="FiveM Bot",
                description=(
                    "Become a **patron** today to get the benefits of **FiveM Bot Pro**.\n"
                    f"Learn more [here](https://fivem.net).\n\n"
                    f"**Player List • TOTAL: {total} players**"
                ),
                color=COLOR_DEFAULT
            )
        else:
            embed = discord.Embed(color=COLOR_DEFAULT)

        for chunk in group:
            lines = "".join(f"[{str(p.get('id','?')).ljust(4)}] {p.get('name','Unknown')}\n" for p in chunk)
            start_id = chunk[0].get('id', '?')
            end_id   = chunk[-1].get('id', '?')
            embed.add_field(
                name=f"Players ({start_id} → {end_id})",
                value=f"```gml\n{lines}
```",
                inline=False
            )

        embed.set_footer(text=f"Server: {SERVER_IP}:{SERVER_PORT}")
        embeds.append(embed)

    return embeds

# ============================================================
#  البوت
# ============================================================
class FiveMBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        if GUILD_ID:
            try:
                guild = discord.Object(id=GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print(f"✅ مزامنة فورية للسيرفر: {GUILD_ID}")
            except discord.Forbidden:
                print("⚠️ فشلت المزامنة الفورية، جاري التحويل للمزامنة العالمية...")
                await self.tree.sync()
                print("✅ مزامنة عالمية تمت بنجاح.")
        else:
            await self.tree.sync()
            print("✅ مزامنة عالمية.")

bot = FiveMBot()

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="BY SL6E & ABO 5LOOD"
        )
    )
    print(f"✅ البوت شغال: {bot.user.name}  |  {SERVER_IP}:{SERVER_PORT}")

# ============================================================
#  أمر /connect الجديد للاتصال بالسيرفر
# ============================================================
@bot.tree.command(name="connect", description="الحصول على رابط وكود الاتصال المباشر بالسيرفر")
async def cmd_connect(interaction: discord.Interaction):
    # كود الاتصال الافتراضي (يمكنك تعديله إلى f"connect {SERVER_IP}" فقط إذا كان السيرفر لا يتطلب البورت في الـ Console)
    connect_code = f"connect {SERVER_IP}:{SERVER_PORT}"
    
    # رابط فتح اللعبة تلقائياً والدخول للسيرفر
    cfx_url = f"https://cfx.re/join/{SERVER_IP}"

    embed = discord.Embed(
        title="🎮 الاتصال بسيرفر ROQZ RP",
        description="يمكنك دخول السيرفر مباشرة عبر إحدى الطرق التالية:",
        color=COLOR_SUCCESS
    )
    
    embed.add_field(
        name="📌 عبر الكونسول (F8)", 
        value=f"قم بنسخ الكود التالي ولصقه داخل الـ Console في اللعبة:\n
