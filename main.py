import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import os

# --- إعدادات الاتصال بالسيرفر ---
SERVER_IP = "194.45.197.196"
SERVER_PORT = "30120"
BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}/players.json"

# آيدي سيرفر الديسكورد حقك لمزامنة الأوامر فوراً
GUILD_ID = 1510735912185630812  # <--- ضع آيدي سيرفرك هنا (أرقام فقط)

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
    print(f"✅ البوت شغال ومتصل باسم: {bot.user.name}")

# دالة الجلب المباشرة عبر الـ IP والـ Port
async def fetch_fivem_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # وقت انتظار صارم (3 ثوانٍ) لمنع تعليق البوت نهائياً
    timeout = aiohttp.ClientTimeout(total=3)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(BASE_URL, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            print(f"❌ عطل في جلب البيانات من الـ IP: {e}")
            return None

# --- أمر /players ---
@bot.tree.command(name="players", description="يعرض قائمة اللاعبين المتواجدين في السيرفر حالياً")
async def players(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    
    players_data = await fetch_fivem_data()
    
    if players_data is None:
        await interaction.followup.send("❌ فشل الاتصال بخوادم السيرفر. تأكد من الـ IP والـ Port أو جدار حماية السيرفر.")
        return

    total_players = len(players_data)
    player_list_text = ""
    
    for player in players_data[:25]:
        player_list_text += f"`[{player.get('id', '?')}]`: {player.get('name', 'Unknown')}\n"

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
    await interaction.response.defer(thinking=True)
    
    players_data = await fetch_fivem_data()
    
    if players_data is None:
        await interaction.followup.send("❌ فشل جلب البيانات.")
        return

    target_player = None
    for player in players_data:
        if player.get('id') == server_id:
            target_player = player
            break

    if not target_player:
        await interaction.followup.send(f"❌ لم يتم العثور على لاعب بالـ ID: `{server_id}` متصل حالياً.")
        return

    identifiers = target_player.get('identifiers', [])
    formatted_identifiers = json.dumps(identifiers, indent=2)

    embed = discord.Embed(title="FiveM Bot", color=discord.Color.from_rgb(114, 137, 218))
    embed.set_author(name="ID Search")
    embed.add_field(name="Username:", value=f"`{target_player.get('name')}`", inline=True)
    embed.add_field(name="Server ID:", value=f"`{target_player.get('id')}`", inline=True)
    embed.add_field(name="Ping:", value=f"`{target_player.get('ping', '?')}`", inline=True)
    embed.add_field(name="Identifiers:", value=f"```json\n{formatted_identifiers}\n```", inline=False)
    
    embed.set_footer(text=f"Server IP: {SERVER_IP}:{SERVER_PORT}")
    await interaction.followup.send(embed=embed)

TOKEN = os.environ.get('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ خطأ: لم يتم العثور على التوكن في متغيرات البيئة!")
