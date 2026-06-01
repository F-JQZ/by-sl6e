import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json

# إعدادات السيرفر (ضع الـ IP والـ Port الخاص بسيرفرك هنا)
SERVER_IP = "194.45.197.196" 
SERVER_PORT = "30120"
BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}"

class FiveMBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # عمل مزامنة للأوامر (Slash Commands)
        await self.tree.sync()
        print(f"Synced slash commands successfully.")

bot = FiveMBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="Fetching players..."))

# دالة مساعدة لجلب البيانات من سيرفر FiveM بأداء عالي
async def fetch_fivem_data(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

# --- 1. أمر عرض قائمة اللاعبين ---
@bot.tree.command(name="players", description="يعرض قائمة اللاعبين المتواجدين في السيرفر حالياً")
async def players(interaction: discord.Interaction):
    await interaction.response.defer() # تأخير الرد حتى لا ينتهي وقت المحاولة أثناء جلب البيانات

    players_data = await fetch_fivem_data("players.json")
    if not players_data:
        await interaction.followup.send("❌ فشل في الاتصال بالسيرفر، تأكد من أن السيرفر يعمل والـ IP/Port صحيح.")
        return

    total_players = len(players_data)
    
    # بناء القائمة النصية للاعبين بنفس التنسيق الموجود بالصورة
    player_list_text = ""
    for player in players_data[:25]: # حد أقصى 25 لاعب في الصفحة الأولى لمنع تخطي حجم الـ Embed
        player_list_text += f"`[{player['id']}]`: {player['name']}\n"

    if not player_list_text:
        player_list_text = "لا يوجد لاعبين متصلين حالياً."

    embed = discord.Embed(
        title="FiveM Bot",
        description=f"Become a **patron** today to get the benefits of **FiveM Bot Pro**.\nLearn more [here](https://fivem.net).\n\n**Player List • TOTAL: {total_players} players • PAGE: 1/1**",
        color=discord.Color.from_rgb(114, 137, 218) # نفس اللون الأزرق بالصورة
    )
    embed.set_author(name="FiveM", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.add_field(name="Player List", value=f"```gml\n{player_list_text}```", inline=False)
    
    # أيقونة السيرفر التعبيرية (لوجو افتراضي)
    embed.set_thumbnail(url="https://cfx-re.svgshare.com/img/fivem.png") 

    await interaction.followup.send(embed=embed)

# --- 2. أمر البحث عن لاعب محدد ---
@bot.tree.command(name="id", description="البحث عن معلومات لاعب محدد داخل السيرفر بواسطة الـ ID")
@app_commands.describe(server_id="ايدي اللاعب داخل السيرفر (Server ID)")
async def id_search(interaction: discord.Interaction, server_id: int):
    await interaction.response.defer()

    players_data = await fetch_fivem_data("players.json")
    if not players_data:
        await interaction.followup.send("❌ فشل في جلب البيانات من السيرفر.")
        return

    # البحث عن اللاعب المطلوب داخل القائمة
    target_player = None
    for player in players_data:
        if player['id'] == server_id:
            target_player = player
            break

    if not target_player:
        await interaction.followup.send(f"❌ لم يتم العثور على لاعب بالـ ID: `{server_id}` في السيرفر حالياً.")
        return

    # تصفية المعرفات (Identifiers) وترتيبها بشكل مصفوفة نصية جميله
    identifiers = target_player.get('identifiers', [])
    
    # تحويل المصفوفة لشكل جيسون منسق كما بالصورة الثانية
    formatted_identifiers = json.dumps(identifiers, indent=2)

    embed = discord.Embed(title="FiveM Bot", color=discord.Color.from_rgb(114, 137, 218))
    embed.set_author(name="ID Search")
    embed.description = "Have feedback or suggestions? Fill out the [FiveM Bot feedback form]() and help improve the service for all."
    
    # إضافة الحقول (الاسم، الآيدي، البنق)
    embed.add_field(name="Username:", value=f"`{target_player['name']}`", inline=True)
    embed.add_field(name="Server ID:", value=f"`{target_player['id']}`", inline=True)
    embed.add_field(name="Ping:", value=f"`{target_player['ping']}`", inline=True)
    
    # إضافة المعرفات داخل بلوك كود أخضر (json)
    embed.add_field(name="Identifiers:", value=f"```json\n{formatted_identifiers}\n```", inline=False)
    
    # الفوتر والـ IP بالأسفل
    embed.set_footer(text=f"Server IP: {SERVER_IP}:{SERVER_PORT}")
    embed.set_thumbnail(url="https://cfx-re.svgshare.com/img/fivem.png")

    await interaction.followup.send(embed=embed)

# ضع التوكن الخاص ببوتك هنا
bot.run("YOUR_BOT_TOKEN")