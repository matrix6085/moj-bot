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
    # Wybierz kanał powitalny
    channel = discord.utils.get(member.guild.text_channels, name="ogólny")
    if channel is None:
        channel = discord.utils.get(member.guild.text_channels, name="powitania")
    if channel is None:
        channel = member.guild.system_channel
    if channel is None:
        channel = member.guild.text_channels[0]
    
    # Wysyła wiadomość powitalną
    embed = discord.Embed(
        title=f"👋 Witaj {member.name}!",
        description=f"Witamy na serwerze **{member.guild.name}**! 🎉",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    embed.add_field(name="📅 Dołączyłeś/aś", value=f"<t:{int(member.joined_at.timestamp())}:F>", inline=True)
    embed.add_field(name="👥 Liczba użytkowników", value=f"{member.guild.member_count}", inline=True)
    
    await channel.send(embed=embed)

# ========== KOMENDY REKRUTACYJNE ==========

# 2️⃣ PODANIE - ODRZUCENIE (czerwona)
@bot.command()
@commands.has_permissions(administrator=True)
async def podanie(ctx, status: str, member: discord.Member):
    """Ocenia podanie kandydata
    Użycie: !podanie fail @użytkownik
    Użycie: !podanie true @użytkownik"""
    
    if status.lower() == "fail":
        embed = discord.Embed(
            title="❌ PODANIE ODRZUCONE",
            description=f"Wynik rekrutacji dla {member.mention}",
            color=discord.Color.red()
        )
        embed.add_field(name="Status", value="**Nie zaakceptowano** ❌", inline=False)
        embed.add_field(name="Wiadomość", value="Twoje podanie nie zostało zaakceptowane.", inline=False)
        embed.set_footer(text=f"Decyzja podjęta przez: {ctx.author.name}")
        
        await ctx.send(embed=embed)
        
        # Opcjonalnie: wyślij prywatną wiadomość do kandydata
        try:
            await member.send(embed=embed)
        except:
            pass  # Jeśli nie można wysłać DM
    
    elif status.lower() == "true":
        embed = discord.Embed(
            title="✅ PODANIE ZAAKCEPTOWANE",
            description=f"Wynik rekrutacji dla {member.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Status", value="**Zaakceptowano** ✅", inline=False)
        embed.add_field(name="Wiadomość", value="Twoje podanie zostało zaakceptowane!", inline=False)
        embed.set_footer(text=f"Decyzja podjęta przez: {ctx.author.name}")
        
        await ctx.send(embed=embed)
        
        try:
            await member.send(embed=embed)
        except:
            pass
    
    else:
        await ctx.send("❌ Nieprawidłowy status! Użyj `!podanie fail @użytkownik` lub `!podanie true @użytkownik`")

# 3️⃣ ETAP 2 - OCENA
@bot.command()
@commands.has_permissions(administrator=True)
async def etap2(ctx, status: str, member: discord.Member):
    """Ocenia 2 etap rekrutacji
    Użycie: !etap2 fail @użytkownik
    Użycie: !etap2 true @użytkownik"""
    
    if status.lower() == "fail":
        embed = discord.Embed(
            title="❌ ETAP 2 - NIEZALICZONY",
            description=f"Wynik 2 etapu rekrutacji dla {member.mention}",
            color=discord.Color.red()
        )
        embed.add_field(name="Status", value="**Nie przeszedł 2 etapu** ❌", inline=False)
        embed.add_field(name="Wiadomość", value="Niestety nie przeszedłeś/łaś 2 etapu rekrutacji.", inline=False)
        embed.set_footer(text=f"Decyzja podjęta przez: {ctx.author.name}")
        
        await ctx.send(embed=embed)
        
        try:
            await member.send(embed=embed)
        except:
            pass
    
    elif status.lower() == "true":
        embed = discord.Embed(
            title="✅ ETAP 2 - ZALICZONY",
            description=f"Wynik 2 etapu rekrutacji dla {member.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Status", value="**Przeszedł 2 etap** ✅", inline=False)
        embed.add_field(name="Wiadomość", value="Gratulacje! Przeszedłeś/łaś 2 etap rekrutacji!", inline=False)
        embed.set_footer(text=f"Decyzja podjęta przez: {ctx.author.name}")
        
        await ctx.send(embed=embed)
        
        try:
            await member.send(embed=embed)
        except:
            pass
    
    else:
        await ctx.send("❌ Nieprawidłowy status! Użyj `!etap2 fail @użytkownik` lub `!etap2 true @użytkownik`")

# 4️⃣ KOMENDA POMOCY (zaktualizowana)
@bot.command()
async def helpme(ctx):
    """Pokazuje dostępne komendy"""
    embed = discord.Embed(
        title="🤖 Pomoc - dostępne komendy",
        description="Lista komend które możesz używać:",
        color=discord.Color.blue()
    )
    embed.add_field(name="📌 Podstawowe:", value="`!ping` - sprawdza czy bot działa\n`!hello` - bot się przywita", inline=False)
    embed.add_field(name="📝 Rekrutacja (tylko admin):", value="`!podanie true/fail @użytkownik` - ocena podania\n`!etap2 true/fail @użytkownik` - ocena 2 etapu", inline=False)
    embed.add_field(name="🔧 Admin (tylko admin):", value="`!say [wiadomość]` - bot wysyła wiadomość\n`!setwelcome_role @rola` - ustawia rolę dla nowych", inline=False)
    await ctx.send(embed=embed)

# 5️⃣ PROSTE KOMENDY
@bot.command()
async def ping(ctx):
    """Sprawdza opóźnienie bota"""
    await ctx.send(f"Pong! 🏓 Opóźnienie: {round(bot.latency * 1000)}ms")

@bot.command()
async def hello(ctx):
    """Bot się przywita"""
    await ctx.send(f"Cześć {ctx.author.mention}! 👋")

@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, *, wiadomosc):
    """Bot wysyła wiadomość którą mu przekażesz (tylko admin)"""
    await ctx.message.delete()
    await ctx.send(wiadomosc)

@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcome_role(ctx, rola: discord.Role):
    """Ustawia rolę która będzie nadawana nowym członkom"""
    global WELCOME_ROLE_ID
    WELCOME_ROLE_ID = rola.id
    await ctx.send(f"✅ Ustawiono rolę {rola.mention} dla nowych członków")

# Zmienna globalna dla roli
WELCOME_ROLE_ID = None

# Uruchomienie bota
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ BŁĄD: Nieprawidłowy token!")
    except Exception as e:
        print(f"❌ BŁĄD: {e}")
