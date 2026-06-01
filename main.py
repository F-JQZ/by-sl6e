import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import os
import math

# ============================================================
#  إعدادات السيرفر
# ============================================================
SERVER_IP   = "194.45.197.196"
SERVER_PORT = "30120"
GUILD_ID    = 1510735912185630812  # <-- ضع آيدي سيرفرك هنا

BASE_URL        = f"http://{SERVER_IP}:{SERVER_PORT}/players.json"
INFO_URL        = f"http://{SERVER_IP}:{SERVER_PORT}/info.json"
FIVEM_THUMBNAIL = "https://i.imgur.com/F4LkFHJ.png"
PLAYERS_PER_PAGE = 20
TIMEOUT_SEC      = 5

# ============================================================
#  ألوان الـ embed
# ============================================================
COLOR_DEFAULT = 0x5865F2   # بنفسجي FiveM
COLOR_ERROR   = 0xED4245   # أحمر خطأ
COLOR_SUCCESS = 0x57F287   # أخضر نجاح

# ============================================================
#  مساعدات استخراج المعرفات
# ============================================================
def extract_identifier(identifiers: list, prefix: str) -> str:
    for ident in identifiers:
        if ident.startswith(prefix):
            return ident.replace(prefix, "")
    return None

def format_identifiers(identifiers: list) -> str:
    """يُنسّق المعرفات بشكل مرتّب مع أيقونات."""
    lines = []
    mapping = {
        "steam:"   : ("🟠 Steam",   None),
        "discord:" : ("🔵 Discord", None),
        "license:" : ("🔑 License", None),
        "license2:": ("🔑 License2", None),
        "xbl:"     : ("🟢 Xbox",    None),
        "live:"    : ("🟢 Live",    None),
        "ip:"      : ("🌐 IP",      None),
    }
    for ident in identifiers:
        matched = False
        for prefix, (label, _) in mapping.items():
            if ident.startswith(prefix):
                value = ident.replace(prefix, "")
                lines.append(f"{label}: `{value}`")
                matched = True
                break
        if not matched:
            lines.append(f"🔹 `{ident}`")
    return "\n".join(lines) if lines else "لا توجد معرّفات"


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
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("✅ تم مزامنة الأوامر بنجاح.")


bot = FiveMBot()


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{SERVER_IP}:{SERVER_PORT}"
        )
    )
    print(f"✅ البوت شغال: {bot.user.name}  |  {SERVER_IP}:{SERVER_PORT}")


# ============================================================
#  جلب بيانات السيرفر
# ============================================================
async def fetch_players() -> list | None:
    headers = {"User-Agent": "Mozilla/5.0"}
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SEC)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(BASE_URL, headers=headers) as r:
                if r.status == 200:
                    return await r.json(content_type=None)
        except Exception as e:
            print(f"❌ fetch_players error: {e}")
    return None

async def fetch_info() -> dict | None:
    headers = {"User-Agent": "Mozilla/5.0"}
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SEC)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(INFO_URL, headers=headers) as r:
                if r.status == 200:
                    return await r.json(content_type=None)
        except Exception as e:
            print(f"❌ fetch_info error: {e}")
    return None


# ============================================================
#  embed الخطأ
# ============================================================
def error_embed(message: str) -> discord.Embed:
    embed = discord.Embed(
        title="FiveM Bot",
        description=message,
        color=COLOR_ERROR
    )
    embed.set_thumbnail(url=FIVEM_THUMBNAIL)
    embed.set_footer(text=f"Server: {SERVER_IP}:{SERVER_PORT}")
    return embed


# ============================================================
#  /players
# ============================================================
@bot.tree.command(name="players", description="عرض قائمة اللاعبين المتصلين بالسيرفر")
@app_commands.describe(page="رقم الصفحة (افتراضي: 1)")
async def cmd_players(interaction: discord.Interaction, page: int = 1):
    await interaction.response.defer(thinking=True)

    # ---- شرط: الصفحة يجب أن تكون رقم موجب ----
    if page < 1:
        await interaction.followup.send(embed=error_embed("❌ رقم الصفحة يجب أن يكون **1** أو أكبر."))
        return

    players_data = await fetch_players()

    if players_data is None:
        await interaction.followup.send(embed=error_embed(
            "❌ **فشل الاتصال بالسيرفر**\n"
            "تأكد من صحة الـ IP والـ Port، أو أن السيرفر يعمل."
        ))
        return

    total_players = len(players_data)

    # ---- شرط: لا يوجد لاعبون ----
    if total_players == 0:
        await interaction.followup.send(embed=error_embed("⚠️ لا يوجد لاعبون متصلون حالياً."))
        return

    total_pages = math.ceil(total_players / PLAYERS_PER_PAGE)

    # ---- شرط: الصفحة تتجاوز الحد ----
    if page > total_pages:
        await interaction.followup.send(embed=error_embed(
            f"❌ الصفحة `{page}` غير موجودة.\n"
            f"الصفحات المتاحة: **1 – {total_pages}**"
        ))
        return

    start = (page - 1) * PLAYERS_PER_PAGE
    page_players = players_data[start: start + PLAYERS_PER_PAGE]

    lines = ""
    for p in page_players:
        pid  = str(p.get("id", "?")).ljust(4)
        name = p.get("name", "Unknown")
        lines += f"[{pid}] {name}\n"

    embed = discord.Embed(
        title="FiveM Bot",
        description=(
            "Become a **patron** today to get the benefits of **FiveM Bot Pro**.\n"
            f"Learn more [here](https://fivem.net).\n\n"
            f"**Player List • TOTAL: {total_players} players • PAGE: {page}/{total_pages}**"
        ),
        color=COLOR_DEFAULT
    )
    embed.set_thumbnail(url=FIVEM_THUMBNAIL)
    embed.add_field(
        name="Player List",
        value=f"```gml\n{lines}```",
        inline=False
    )
    embed.set_footer(text=f"Server: {SERVER_IP}:{SERVER_PORT}")
    await interaction.followup.send(embed=embed)


# ============================================================
#  /id  — البحث عن لاعب بالـ Server ID
# ============================================================
@bot.tree.command(name="id", description="البحث عن لاعب داخل السيرفر عبر الـ Server ID")
@app_commands.describe(server_id="الـ ID الخاص باللاعب داخل السيرفر")
async def cmd_id(interaction: discord.Interaction, server_id: int):
    await interaction.response.defer(thinking=True)

    # ---- شرط: الـ ID يجب أن يكون موجباً ----
    if server_id <= 0:
        await interaction.followup.send(embed=error_embed("❌ الـ ID يجب أن يكون رقماً موجباً."))
        return

    players_data = await fetch_players()
    if players_data is None:
        await interaction.followup.send(embed=error_embed("❌ فشل جلب بيانات السيرفر."))
        return

    # ---- إيجاد اللاعب ----
    target = next((p for p in players_data if p.get("id") == server_id), None)

    if not target:
        await interaction.followup.send(embed=error_embed(
            f"❌ لا يوجد لاعب بالـ ID **{server_id}** متصل حالياً.\n"
            f"⚡ إجمالي المتصلين: **{len(players_data)}** لاعب"
        ))
        return

    identifiers = target.get("identifiers", [])

    # --- استخراج Steam و Discord ---
    steam_raw   = extract_identifier(identifiers, "steam:")
    discord_raw = extract_identifier(identifiers, "discord:")
    license_raw = extract_identifier(identifiers, "license:")

    steam_value   = f"`{steam_raw}`"   if steam_raw   else "`غير مرتبط`"
    discord_value = f"<@{discord_raw}> (`{discord_raw}`)" if discord_raw else "`غير مرتبط`"
    license_value = f"`{license_raw}`" if license_raw else "`—`"

    embed = discord.Embed(
        title="FiveM Bot",
        description=(
            "Have feedback or suggestions? Fill out the "
            "[FiveM Bot feedback form](https://fivem.net) "
            "and help improve the service for all."
        ),
        color=COLOR_DEFAULT
    )
    embed.set_author(name="ID Search")
    embed.set_thumbnail(url=FIVEM_THUMBNAIL)

    # --- معلومات أساسية (inline) ---
    embed.add_field(name="Username",   value=f"`{target.get('name', 'Unknown')}`", inline=True)
    embed.add_field(name="Server ID",  value=f"`{target.get('id', '?')}`",         inline=True)
    embed.add_field(name="Ping",       value=f"`{target.get('ping', '?')} ms`",    inline=True)

    # --- Steam و Discord ---
    embed.add_field(name="🟠 Steam",   value=steam_value,   inline=True)
    embed.add_field(name="🔵 Discord", value=discord_value, inline=True)
    embed.add_field(name="🔑 License", value=license_value, inline=True)

    # --- كل المعرفات ---
    embed.add_field(
        name="📋 All Identifiers",
        value=format_identifiers(identifiers),
        inline=False
    )

    embed.set_footer(text=f"Server: {SERVER_IP}:{SERVER_PORT}")
    await interaction.followup.send(embed=embed)


# ============================================================
#  /search  — البحث عن لاعب بالاسم
# ============================================================
@bot.tree.command(name="search", description="البحث عن لاعب بالاسم")
@app_commands.describe(name="اسم اللاعب أو جزء منه")
async def cmd_search(interaction: discord.Interaction, name: str):
    await interaction.response.defer(thinking=True)

    # ---- شرط: طول الاسم ----
    if len(name.strip()) < 2:
        await interaction.followup.send(embed=error_embed("❌ اكتب على الأقل **حرفين** للبحث."))
        return

    players_data = await fetch_players()
    if players_data is None:
        await interaction.followup.send(embed=error_embed("❌ فشل جلب بيانات السيرفر."))
        return

    query   = name.strip().lower()
    results = [p for p in players_data if query in p.get("name", "").lower()]

    # ---- شرط: لا نتائج ----
    if not results:
        await interaction.followup.send(embed=error_embed(
            f"❌ لم يُعثر على لاعب يحتوي اسمه على **\"{name}\"**."
        ))
        return

    # ---- شرط: كثير جداً ----
    MAX_RESULTS = 15
    truncated = len(results) > MAX_RESULTS
    results   = results[:MAX_RESULTS]

    lines = ""
    for p in results:
        pid  = str(p.get("id", "?")).ljust(4)
        pname = p.get("name", "Unknown")
        ping = p.get("ping", "?")
        lines += f"[{pid}] {pname}  (ping: {ping}ms)\n"

    note = f"\n⚠️ تم عرض أول {MAX_RESULTS} نتيجة فقط." if truncated else ""

    embed = discord.Embed(
        title="FiveM Bot",
        description=f"**نتائج البحث عن: \"{name}\"** — {len(results)} نتيجة{note}",
        color=COLOR_SUCCESS
    )
    embed.set_author(name="Name Search")
    embed.set_thumbnail(url=FIVEM_THUMBNAIL)
    embed.add_field(
        name="Results",
        value=f"```gml\n{lines}```",
        inline=False
    )
    embed.set_footer(text=f"Server: {SERVER_IP}:{SERVER_PORT}")
    await interaction.followup.send(embed=embed)


# ============================================================
#  /stats  — إحصائيات السيرفر
# ============================================================
@bot.tree.command(name="stats", description="إحصائيات السيرفر العامة")
async def cmd_stats(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    players_data, info_data = None, None
    import asyncio
    players_data, info_data = await asyncio.gather(fetch_players(), fetch_info())

    if players_data is None:
        await interaction.followup.send(embed=error_embed("❌ السيرفر غير متاح حالياً."))
        return

    total_players = len(players_data)
    max_players   = info_data.get("vars", {}).get("sv_maxClients", "?") if info_data else "?"
    hostname      = info_data.get("vars", {}).get("sv_hostname", "Unknown") if info_data else "Unknown"
    server_name   = info_data.get("name", hostname) if info_data else hostname

    avg_ping = 0
    if total_players:
        pings    = [p.get("ping", 0) for p in players_data if isinstance(p.get("ping"), int)]
        avg_ping = round(sum(pings) / len(pings)) if pings else 0

    embed = discord.Embed(
        title="FiveM Bot",
        description=f"**Server Statistics**",
        color=COLOR_DEFAULT
    )
    embed.set_author(name="Server Stats")
    embed.set_thumbnail(url=FIVEM_THUMBNAIL)
    embed.add_field(name="🖥️ Server Name", value=f"`{server_name}`",              inline=False)
    embed.add_field(name="👥 Players",     value=f"`{total_players} / {max_players}`", inline=True)
    embed.add_field(name="📶 Avg Ping",    value=f"`{avg_ping} ms`",              inline=True)
    embed.add_field(name="🌐 Address",     value=f"`{SERVER_IP}:{SERVER_PORT}`",  inline=True)
    embed.set_footer(text=f"Server: {SERVER_IP}:{SERVER_PORT}")
    await interaction.followup.send(embed=embed)


# ============================================================
#  تشغيل البوت
# ============================================================
TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ خطأ: DISCORD_TOKEN غير موجود في متغيرات البيئة!")
