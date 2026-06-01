import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import os

# --- إعدادات الاتصال بالسيرفر ---
# الطريقة الأولى: الـ IP والـ Port المباشر للسيرفر
SERVER_IP = "194.45.197.196" 
SERVER_PORT = "30120"  # تأكد إذا كان السيرفر يستعمل بورت آخر للـ API (مثل 30120 أو بورت الاستضافة)

# الطريقة الثانية: إذا كان السيرفر محمي، ضع الـ Cfx Join ID هنا (الأحرف والرقام اللي بعد cfx.re/join/)
# مثال: لو الرابط cfx.re/join/abc1234 ضع "abc1234"
CFX_ID = "" 

# تحديد الرابط الأساسي بناءً على المدخلات
if CFX_ID:
    BASE_URL = f"https://servers-live.fivem.net/api/servers/single/{CFX_ID}"
else:
    BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}"

# آيدي السيرفر الخاص بك لتظهر الأوامر فوراً
GUILD_ID = 123456789012345678  # <--- ضع آيدي سيرفر الديسكورد حقك هنا

class FiveMBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        intents.members = True
        intents.presences = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(f"✅ تم بنجاح مزامنة الأوامر في ديسكورد.")

bot = FiveMBot()

@bot.event
async def on_ready():
    print(f"✅ البوت متصل الآن باسم: {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="Fetching players..."))

# دالة ذكية لجلب البيانات وتحديد سبب المشكلة إذا فشلت
async def fetch_fivem_data(endpoint):
    # إذا كنا نستخدم Cfx ID، البنية تختلف قليلاً في الـ API الرسمي
    if CFX_ID:
        url = BASE_URL
    else:
        url = f"{BASE_URL}/{endpoint}"
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=7) as response:
                print(f"طلب البيانات من: {url} -> كود الاستجابة: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    # إذا كنا نستخدم Cfx API، البيانات تكون بداخل حقل 'Data'
                    if CFX_ID:
                        if endpoint == "players.json":
                            return data.get('Data', {}).get('players', [])
                    return data
                return None
        except Exception as e:
            print(f"❌ خطأ أثناء الاتصال بالـ API: {e}")
            return None

# --- أمر /players ---
@bot.tree.command(name="players", description="يعرض قائمة اللاعبين المتواجدين في السيرفر حالياً")
async def players(interaction: discord.Interaction):
    await interaction.response.defer()
    
    players_data = await fetch_fivem_data("players.json")
    if players_data is None:
        await interaction.followup.send("❌ فشل في الاتصال بالسيرفر، تأكد من الـ IP والـ Port أو جرب وضع الـ Cfx ID بالكود.")
        return

    total_players = len(players_data)
    player_list_text = ""
    
    # جلب أول 25 لاعب
    for player in players_data[:25]:
        player_list_text += f"`[{player['id']}]`: {player['name']}\n"

    if not player_list_text:
        player_list_text = "لا يوجد لاعبين متصلين حالياً."

    embed = discord.Embed(
        title="FiveM Bot",
        description=f"Become a **patron** today to get the benefits of **FiveM Bot Pro**.\nLearn more [here](https://fivem.net).\n\n**Player List • TOTAL: {total_players} players • PAGE: 1/1**",
        color=discord.Color.from_rgb(114, 137, 218)
    )
    embed.add_field(name="Player List", value=f"```gml\n{player_list_text}```", inline=False)
    await interaction.followup.send(embed=embed)

# --- أمر /id ---
@bot.tree.command(name="id", description="البحث عن معلومات لاعب محدد داخل السيرفر بواسطة الـ ID")
@app_commands.describe(server_id="ايدي اللاعب داخل السيرفر (Server ID)")
async def id_search(interaction: discord.Interaction, server_id: int):
    await interaction.response.defer()
    
    players_data = await fetch_fivem_data("players.json")
    if players_data is None:
        await interaction.followup.send("❌ فشل في جلب البيانات من السيرفر.")
        return

    target_player = None
    for player in players_data:
        if player['id'] == server_id:
            target_player = player
            break

    if not target_player:
        await interaction.followup.send(f"❌ لم يتم العثور على لاعب بالـ ID: `{server_id}` متصل حالياً.")
        return

    identifiers = target_player.get('identifiers', [])
    formatted_identifiers = json.dumps(identifiers, indent=2)

    embed = discord.Embed(title="FiveM Bot", color=discord.Color.from_rgb(114, 137, 218))
    embed.set_author(name="ID Search")
    embed.add_field(name="Username:", value=f"`{target_player['name']}`", inline=True)
    embed.add_field(name="Server ID:", value=f"`{target_player['id']}`", inline=True)
    embed.add_field(name="Ping:", value=f"`{target_player['ping']}`", inline=True)
    embed.add_field(name="Identifiers:", value=f"```json\n{formatted_identifiers}\n```", inline=False)
    
    if CFX_ID:
        embed.set_footer(text=f"Server Cfx ID: {CFX_ID}")
    else:
        embed.set_footer(text=f"Server IP: {SERVER_IP}:{SERVER_PORT}")
        
    await interaction.followup.send(embed=embed)

TOKEN = os.environ.get('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ خطأ: لم يتم العثور على التوكن في متغيرات البيئة!")
