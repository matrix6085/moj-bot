import discord
from discord.ext import commands
import os

# Pobiera token ze zmiennych środowiskowych
TOKEN = os.getenv("TOKEN")

# Ustawiamy uprawnienia bota
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== ZDARZENIA ==========

@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")
    print(f"🌐 Bot działa na {len(bot.guilds)} serwerach")
    print("------")

# 1️⃣ WITANIE NOWYCH CZŁONKÓW
@bot.event
async def on_member_join(member):
    """Wysyła powitanie gdy ktoś dołączy"""
    # Wybierz kanał powitalny (możesz zmienić nazwę kanału)
    channel = discord.utils.get(member.guild.text_channels, name="ogólny")
    
    # Jeśli nie ma kanału "ogólny", spróbuj "powitania" lub pierwszy kanał
    if channel is None:
        channel = discord.utils.get(member.guild.text_channels, name="powitania")
    if channel is None:
        channel = member.guild.system_channel  # kanał systemowy
    if channel is None:
        channel = member.guild.text_channels[0]  # pierwszy dostępny kanał
    
    # Wysyła wiadomość powitalną
    embed = discord.Embed(
        title=f"👋 Witaj {member.name}!",
        description=f"Witamy na serwerze **{member.guild.name}**! 🎉\nCieszymy się, że dołączyłeś/aś!",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    embed.add_field(name="📅 Dołączyłeś/aś", value=f"<t:{int(member.joined_at.timestamp())}:F>", inline=True)
    embed.add_field(name="👥 Jesteś {ty} użytkownikiem", value=f"Jesteś {member.guild.member_count} osobą na serwerze!", inline=True)
    
    await channel.send(embed=embed)
    
    # OPCJONALNIE: Nadaj domyślną rolę (odkomentuj jeśli chcesz)
    # default_role = discord.utils.get(member.guild.roles, name="Nowy")
    # if default_role:
    #     await member.add_roles(default_role)
    #     print(f"Nadano rolę {default_role.name} użytkownikowi {member.name}")

# 2️⃣ WIADOMOŚCI OD ADMINA
@bot.command()
@commands.has_permissions(administrator=True)  # Tylko admin może używać
async def say(ctx, *, wiadomosc):
    """Bot wysyła wiadomość którą mu przekażesz (tylko admin)"""
    # Usuwa komendę admina (żeby nie było widać)
    await ctx.message.delete()
    # Bot wysyła wiadomość
    await ctx.send(wiadomosc)

# 3️⃣ WIADOMOŚCI NA OKREŚLONY KANAŁ
@bot.command()
@commands.has_permissions(administrator=True)
async def sayto(ctx, kanal: discord.TextChannel, *, wiadomosc):
    """Bot wysyła wiadomość na wskazany kanał
    Użycie: !sayto #kanał Treść wiadomości"""
    await ctx.message.delete()
    await kanal.send(wiadomosc)
    await ctx.send(f"✅ Wiadomość wysłana na kanał {kanal.mention}", delete_after=3)

# 4️⃣ NADANIE ROLI PRZY WEJŚCIU (AKTYWNE)
@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcome_role(ctx, rola: discord.Role):
    """Ustawia rolę która będzie nadawana nowym członkom
    Użycie: !setwelcome_role @NazwaRoli"""
    global WELCOME_ROLE_ID
    WELCOME_ROLE_ID = rola.id
    await ctx.send(f"✅ Ustawiono rolę {rola.mention} dla nowych członków")

# Wersja z automatycznym nadawaniem roli (odkomentuj on_member_join i zmień na to):
"""
@bot.event
async def on_member_join(member):
    # Nadaj rolę jeśli jest ustawiona
    if WELCOME_ROLE_ID:
        role = member.guild.get_role(WELCOME_ROLE_ID)
        if role:
            await member.add_roles(role)
            print(f"Nadano rolę {role.name} użytkownikowi {member.name}")
    
    # Reszta powitania...
"""

# 5️⃣ PROSTE KOMENDY (dla testów)
@bot.command()
async def ping(ctx):
    """Sprawdza opóźnienie bota"""
    await ctx.send(f"Pong! 🏓 Opóźnienie: {round(bot.latency * 1000)}ms")

@bot.command()
async def hello(ctx):
    """Bot się przywita"""
    await ctx.send(f"Cześć {ctx.author.mention}! 👋")

@bot.command()
async def helpme(ctx):
    """Pokazuje dostępne komendy"""
    embed = discord.Embed(
        title="🤖 Pomoc - dostępne komendy",
        description="Lista komend które możesz używać:",
        color=discord.Color.blue()
    )
    embed.add_field(name="!ping", value="Sprawdza czy bot działa", inline=False)
    embed.add_field(name="!hello", value="Bot się przywita", inline=False)
    embed.add_field(name="!say [wiadomość]", value="Bot wysyła wiadomość (tylko admin)", inline=False)
    embed.add_field(name="!sayto #kanał [wiadomość]", value="Bot wysyła wiadomość na wskazany kanał (admin)", inline=False)
    embed.add_field(name="!setwelcome_role @rola", value="Ustawia rolę dla nowych członków (admin)", inline=False)
    await ctx.send(embed=embed)

# Uruchomienie bota
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ BŁĄD: Nieprawidłowy token!")
    except Exception as e:
        print(f"❌ BŁĄD: {e}")
