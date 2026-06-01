import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import os
import asyncio

# --- إعدادات الاتصال بالسيرفر ---
SERVER_IP = "194.45.197.196" 
SERVER_PORT = "30120"  
CFX_ID = ""  # 💡 نصيحة: إذا استمر الخطأ، ضع هنا الـ Cfx Join ID الخاص بسيرفرك (الأحرف التي بعد cfx.re/join/)

if CFX_ID:
    BASE_URL = f"https://servers-live.fivem.net/api/servers/single/{CFX_ID}"
else:
    BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}"

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
        print(f"✅ تم بنجاح مزامنة الأوامر الفورية.")

bot = FiveMBot()

@bot.event
async def on_ready():
    print(f"✅ البوت متصل الآن كـ: {bot.user.name}")

# دالة الجلب مع تحديد وقت انتظار صارم (3 ثوانٍ فقط) لتجنب تعليق الديسكورد
async def fetch_fivem_data(endpoint):
    url = BASE_URL if CFX_ID else f"{BASE_URL}/{endpoint}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # وضعنا الـ timeout هنا 4 ثوانٍ كحد أقصى
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=4)) as response:
                if response.status == 200:
                    data = await response.json()
                    if CFX_ID and endpoint == "players.json":
                        return data.get('Data', {}).get('players', [])
                    return data
                return None
        except Exception as e:
            print(f"❌ خطأ أثناء الاتصال بالـ API: {e}")
            return None

# --- أمر /players ---
@bot.tree.command(name="players", description="يعرض قائمة اللاعبين المتواجدين في السيرفر حالياً")
async def players(interaction: discord.Interaction):
    # 1. الرد المبدئي الفوري لإعلام الديسكورد أن البوت شغال (يمنع رسالة التطبيق لم يستجب)
    await interaction.response.send_message("⏳ جاري سحب قائمة اللاعبين من السيرفر، يرجى الانتظار...", ephemeral=True)
    
    players_data = await fetch_fivem_data("players.json")
    if players_data is None:
        await interaction.edit_original_response(content="❌ **فشل في الاتصال بالسيرفر.**\nتأكد من أن السيرفر شغال، أو جرب استخدام الـ `CFX_ID` داخل الكود بدلاً من الـ IP المباشر بسبب جدار الحماية.")
        return

    total_players = len(players_data)
    player_list_text = ""
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
    
    # تعديل الرسالة المبدئية وإرسال الـ Embed المنسق
    await interaction.edit_original_response(content=None, embed=embed)

# --- أمر /id ---
@bot.tree.command(name="id", description="البحث عن معلومات لاعب محدد داخل السيرفر بواسطة الـ ID")
@app_commands.describe(server_id="ايدي اللاعب داخل السيرفر (Server ID)")
async def id_search(interaction: discord.Interaction, server_id: int):
    await interaction.response.send_message(f"⏳ جاري البحث عن اللاعب صاحب الأيدي `{server_id}`...", ephemeral=True)
    
    players_data = await fetch_fivem_data("players.json")
    if players_data is None:
        await interaction.edit_original_response(content="❌ **فشل في جلب البيانات من السيرفر.**")
        return

    target_player = None
    for player in players_data:
        if player['id'] == server_id:
            target_player = player
            break

    if not target_player:
        await interaction.edit_original_response(content=f"❌ لم يتم العثور على لاعب بالـ ID: `{server_id}` متصل حالياً في السيرفر.")
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
        
    await interaction.edit_original_response(content=None, embed=embed)

TOKEN = os.environ.get('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ خطأ: لم يتم العثور على التوكن في متغيرات البيئة!")
