import discord
from discord.ext import commands
import os
import json

# Pobiera token ze zmiennych środowiskowych
TOKEN = os.getenv("TOKEN")

# Ustawiamy uprawnienia bota
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== PLIK DO PRZECHOWYWANIA REKRUTANTÓW ==========
RECRUITERS_FILE = "recruiters.json"

def load_recruiters():
    """Wczytuje listę rekrutantów z pliku"""
    try:
        with open(RECRUITERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_recruiters(recruiters):
    """Zapisuje listę rekrutantów do pliku"""
    with open(RECRUITERS_FILE, "w") as f:
        json.dump(recruiters, f)

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
    channel = discord.utils.get(member.guild.text_channels, name="ogólny")
    if channel is None:
        channel = discord.utils.get(member.guild.text_channels, name="powitania")
    if channel is None:
        channel = member.guild.system_channel
    if channel is None:
        channel = member.guild.text_channels[0]
    
    embed = discord.Embed(
        title=f"👋 Witaj {member.name}!",
        description=f"Witamy na serwerze **{member.guild.name}**! 🎉",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    embed.add_field(name="📅 Dołączyłeś/aś", value=f"<t:{int(member.joined_at.timestamp())}:F>", inline=True)
    embed.add_field(name="👥 Liczba użytkowników", value=f"{member.guild.member_count}", inline=True)
    
    await channel.send(embed=embed)

# ========== ZARZĄDZANIE REKRUTANTAMI ==========

@bot.command()
@commands.has_permissions(administrator=True)
async def addrecruiter(ctx, member: discord.Member):
    """Dodaje rekrutanta (tylko admin)
    Użycie: !addrecruiter @użytkownik"""
    
    recruiters = load_recruiters()
    
    if member.id in recruiters:
        await ctx.send(f"❌ {member.mention} jest już rekrutantem!")
        return
    
    recruiters.append(member.id)
    save_recruiters(recruiters)
    
    embed = discord.Embed(
        title="✅ DODANO REKRUTANTA",
        description=f"{member.mention} został dodany do zespołu rekrutacyjnego!",
        color=discord.Color.green()
    )
    embed.add_field(name="Uprawnienia", value="Może używać komend rekrutacyjnych: `!podanie` i `!etap2`", inline=False)
    await ctx.send(embed=embed)
    
    # Wyślij PW do nowego rekrutanta
    try:
        pw_embed = discord.Embed(
            title="🎉 Zostałeś rekrutantem!",
            description=f"Gratulacje! Zostałeś dodany do zespołu rekrutacyjnego na serwerze **{ctx.guild.name}**.",
            color=discord.Color.green()
        )
        pw_embed.add_field(name="📋 Twoje komendy:", value="`!podanie true/fail @użytkownik`\n`!etap2 true/fail @użytkownik`", inline=False)
        await member.send(embed=pw_embed)
    except:
        pass

@bot.command()
@commands.has_permissions(administrator=True)
async def removerecruiter(ctx, member: discord.Member):
    """Usuwa rekrutanta (tylko admin)
    Użycie: !removerecruiter @użytkownik"""
    
    recruiters = load_recruiters()
    
    if member.id not in recruiters:
        await ctx.send(f"❌ {member.mention} nie jest rekrutantem!")
        return
    
    recruiters.remove(member.id)
    save_recruiters(recruiters)
    
    embed = discord.Embed(
        title="❌ USUNIĘTO REKRUTANTA",
        description=f"{member.mention} został usunięty z zespołu rekrutacyjnego.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)
    
    # Wyślij PW do usuniętego rekrutanta
    try:
        pw_embed = discord.Embed(
            title="ℹ️ Zmiana uprawnień",
            description=f"Zostałeś usunięty z zespołu rekrutacyjnego na serwerze **{ctx.guild.name}**.",
            color=discord.Color.orange()
        )
        await member.send(embed=pw_embed)
    except:
        pass

@bot.command()
async def recruiters(ctx):
    """Pokazuje listę rekrutantów"""
    recruiters = load_recruiters()
    
    if not recruiters:
        await ctx.send("📋 Brak rekrutantów w bazie.")
        return
    
    embed = discord.Embed(
        title="📋 LISTA REKRUTANTÓW",
        color=discord.Color.blue()
    )
    
    rekruterzy = []
    for recruiter_id in recruiters:
        member = ctx.guild.get_member(recruiter_id)
        if member:
            rekruterzy.append(f"• {member.mention} ({member.name})")
        else:
            rekruterzy.append(f"• Nieznany użytkownik (ID: {recruiter_id})")
    
    embed.description = "\n".join(rekruterzy)
    await ctx.send(embed=embed)

# ========== SPRAWDZANIE UPRAWNIEŃ ==========

def is_recruiter_or_admin(ctx):
    """Sprawdza czy użytkownik jest rekrutantem lub adminem"""
    if ctx.author.guild_permissions.administrator:
        return True
    recruiters = load_recruiters()
    return ctx.author.id in recruiters

# ========== KOMENDY REKRUTACYJNE ==========

async def send_recruitment_result(ctx, member, status, stage, success):
    """Wysyła wyniki rekrutacji na kanał i PW"""
    
    if stage == "podanie":
        if success:
            title = "✅ PODANIE ZAAKCEPTOWANE"
            color = discord.Color.green()
            status_text = "Zaakceptowano ✅"
            message = "Twoje podanie zostało zaakceptowane!"
        else:
            title = "❌ PODANIE ODRZUCONE"
            color = discord.Color.red()
            status_text = "Nie zaakceptowano ❌"
            message = "Twoje podanie nie zostało zaakceptowane."
    else:  # etap2
        if success:
            title = "✅ ETAP 2 - ZALICZONY"
            color = discord.Color.green()
            status_text = "Przeszedł 2 etap ✅"
            message = "Gratulacje! Przeszedłeś/łaś 2 etap rekrutacji!"
        else:
            title = "❌ ETAP 2 - NIEZALICZONY"
            color = discord.Color.red()
            status_text = "Nie przeszedł 2 etapu ❌"
            message = "Niestety nie przeszedłeś/łaś 2 etapu rekrutacji."
    
    # Embed na kanale
    embed = discord.Embed(
        title=title,
        description=f"Wynik rekrutacji dla {member.mention}",
        color=color
    )
    embed.add_field(name="Status", value=f"**{status_text}**", inline=False)
    embed.add_field(name="Wiadomość", value=message, inline=False)
    embed.add_field(name="Rekrutujący", value=ctx.author.mention, inline=False)
    embed.set_footer(text=f"Decyzja podjęta: {ctx.author.name}")
    
    await ctx.send(embed=embed)
    
    # Wyślij PW do kandydata
    try:
        pw_embed = discord.Embed(
            title=title,
            description=f"Otrzymałeś wynik rekrutacji na serwerze **{ctx.guild.name}**.",
            color=color
        )
        pw_embed.add_field(name="Twój wynik", value=status_text, inline=False)
        pw_embed.add_field(name="Wiadomość", value=message, inline=False)
        pw_embed.add_field(name="Rekrutujący", value=ctx.author.name, inline=False)
        
        await member.send(embed=pw_embed)
    except:
        pass
    
    # Wyślij PW do rekrutującego (potwierdzenie)
    try:
        confirmation_embed = discord.Embed(
            title="✅ Potwierdzenie wysłania",
            description=f"Wynik rekrutacji dla {member.name} został wysłany.",
            color=discord.Color.green()
        )
        confirmation_embed.add_field(name="Ocena", value=status_text, inline=False)
        await ctx.author.send(embed=confirmation_embed)
    except:
        pass

@bot.command()
@commands.check(is_recruiter_or_admin)
async def podanie(ctx, status: str, member: discord.Member):
    """Ocenia podanie kandydata
    Użycie: !podanie fail @użytkownik
    Użycie: !podanie true @użytkownik"""
    
    if status.lower() == "fail":
        await send_recruitment_result(ctx, member, "podanie", "podanie", False)
    elif status.lower() == "true":
        await send_recruitment_result(ctx, member, "podanie", "podanie", True)
    else:
        await ctx.send("❌ Nieprawidłowy status! Użyj `!podanie fail @użytkownik` lub `!podanie true @użytkownik`")

@bot.command()
@commands.check(is_recruiter_or_admin)
async def etap2(ctx, status: str, member: discord.Member):
    """Ocenia 2 etap rekrutacji
    Użycie: !etap2 fail @użytkownik
    Użycie: !etap2 true @użytkownik"""
    
    if status.lower() == "fail":
        await send_recruitment_result(ctx, member, "etap2", "etap2", False)
    elif status.lower() == "true":
        await send_recruitment_result(ctx, member, "etap2", "etap2", True)
    else:
        await ctx.send("❌ Nieprawidłowy status! Użyj `!etap2 fail @użytkownik` lub `!etap2 true @użytkownik`")

# ========== KOMENDA POMOCY ==========

@bot.command()
async def helpme(ctx):
    """Pokazuje dostępne komendy"""
    is_recruiter = is_recruiter_or_admin(ctx)
    
    embed = discord.Embed(
        title="🤖 Pomoc - dostępne komendy",
        description="Lista komend które możesz używać:",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="📌 Podstawowe:", value="`!ping` - sprawdza czy bot działa\n`!hello` - bot się przywita", inline=False)
    
    if is_recruiter:
        embed.add_field(name="📝 Rekrutacja (rekrutanci/admin):", value="`!podanie true/fail @użytkownik` - ocena podania\n`!etap2 true/fail @użytkownik` - ocena 2 etapu", inline=False)
    
    if ctx.author.guild_permissions.administrator:
        embed.add_field(name="👑 Zarządzanie rekrutantami (admin):", value="`!addrecruiter @użytkownik` - dodaje rekrutanta\n`!removerecruiter @użytkownik` - usuwa rekrutanta\n`!recruiters` - lista rekrutantów", inline=False)
        embed.add_field(name="🔧 Admin:", value="`!say [wiadomość]` - bot wysyła wiadomość\n`!setwelcome_role @rola` - ustawia rolę dla nowych", inline=False)
    
    await ctx.send(embed=embed)

# ========== PROSTE KOMENDY ==========

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
