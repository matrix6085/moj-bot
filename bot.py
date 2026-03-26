import discord
from discord.ext import commands
import os
import json

# Pobiera token ze zmiennych środowiskowych
TOKEN = os.getenv("TOKEN")

# Ustawiamy uprawnienia bota
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== PLIKI DO PRZECHOWYWANIA DANYCH ==========
RECRUITERS_FILE = "recruiters.json"
CONFIG_FILE = "config.json"

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

def load_config():
    """Wczytuje konfigurację serwera"""
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "welcome_channel": None,
            "welcome_role": None,
            "accepted_role": None,
            "etap2_role1": None,
            "etap2_role2": None
        }

def save_config(config):
    """Zapisuje konfigurację serwera"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

# ========== ZDARZENIA ==========

@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")
    print(f"🌐 Bot działa na {len(bot.guilds)} serwerach")
    print("------")

# 1️⃣ WITANIE NOWYCH CZŁONKÓW
@bot.event
async def on_member_join(member):
    """Wysyła powitanie gdy ktoś dołączy i nadaje rolę powitalną"""
    config = load_config()
    
    # Nadaj rolę powitalną jeśli jest ustawiona
    if config["welcome_role"]:
        role = member.guild.get_role(config["welcome_role"])
        if role:
            try:
                await member.add_roles(role)
                print(f"Nadano rolę {role.name} użytkownikowi {member.name}")
            except:
                print(f"Nie udało się nadać roli {member.name}")
    
    # Wyślij wiadomość powitalną na ustawionym kanale
    if config["welcome_channel"]:
        channel = bot.get_channel(config["welcome_channel"])
        if channel:
            embed = discord.Embed(
                title=f"👋 Witaj {member.name}!",
                description=f"Witamy na serwerze **{member.guild.name}**! 🎉",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            embed.add_field(name="📅 Dołączyłeś/aś", value=f"<t:{int(member.joined_at.timestamp())}:F>", inline=True)
            embed.add_field(name="👥 Liczba użytkowników", value=f"{member.guild.member_count}", inline=True)
            
            await channel.send(embed=embed)

# ========== KONFIGURACJA SERWERA ==========

@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcomechannel(ctx, channel: discord.TextChannel):
    """Ustawia kanał dla powitań
    Użycie: !setwelcomechannel #kanał"""
    
    config = load_config()
    config["welcome_channel"] = channel.id
    save_config(config)
    
    await ctx.send(f"✅ Ustawiono kanał powitalny na {channel.mention}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcomerole(ctx, role: discord.Role):
    """Ustawia rolę dla nowych członków (nadawana automatycznie przy wejściu)
    Użycie: !setwelcomerole @rola"""
    
    config = load_config()
    config["welcome_role"] = role.id
    save_config(config)
    
    await ctx.send(f"✅ Ustawiono rolę powitalną na {role.mention}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setacceptedrole(ctx, role: discord.Role):
    """Ustawia rolę nadawaną po zaakceptowaniu podania
    Użycie: !setacceptedrole @rola"""
    
    config = load_config()
    config["accepted_role"] = role.id
    save_config(config)
    
    await ctx.send(f"✅ Ustawiono rolę dla zaakceptowanych na {role.mention}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setetap2role1(ctx, role: discord.Role):
    """Ustawia pierwszą rolę nadawaną po zaliczeniu 2 etapu
    Użycie: !setetap2role1 @rola"""
    
    config = load_config()
    config["etap2_role1"] = role.id
    save_config(config)
    
    await ctx.send(f"✅ Ustawiono pierwszą rolę dla 2 etapu na {role.mention}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setetap2role2(ctx, role: discord.Role):
    """Ustawia drugą rolę nadawaną po zaliczeniu 2 etapu
    Użycie: !setetap2role2 @rola"""
    
    config = load_config()
    config["etap2_role2"] = role.id
    save_config(config)
    
    await ctx.send(f"✅ Ustawiono drugą rolę dla 2 etapu na {role.mention}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def showconfig(ctx):
    """Pokazuje aktualną konfigurację serwera"""
    config = load_config()
    
    embed = discord.Embed(
        title="⚙️ Konfiguracja serwera",
        color=discord.Color.blue()
    )
    
    # Kanał powitalny
    if config["welcome_channel"]:
        channel = bot.get_channel(config["welcome_channel"])
        embed.add_field(name="📢 Kanał powitalny", value=channel.mention if channel else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="📢 Kanał powitalny", value="❌ Nie ustawiono", inline=False)
    
    # Rola powitalna
    if config["welcome_role"]:
        role = ctx.guild.get_role(config["welcome_role"])
        embed.add_field(name="🎭 Rola dla nowych", value=role.mention if role else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="🎭 Rola dla nowych", value="❌ Nie ustawiono", inline=False)
    
    # Rola po akceptacji podania
    if config["accepted_role"]:
        role = ctx.guild.get_role(config["accepted_role"])
        embed.add_field(name="✅ Rola po akceptacji podania", value=role.mention if role else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="✅ Rola po akceptacji podania", value="❌ Nie ustawiono", inline=False)
    
    # Role po 2 etapie
    etap2_roles = []
    if config["etap2_role1"]:
        role = ctx.guild.get_role(config["etap2_role1"])
        etap2_roles.append(role.mention if role else "Nie znaleziono")
    if config["etap2_role2"]:
        role = ctx.guild.get_role(config["etap2_role2"])
        etap2_roles.append(role.mention if role else "Nie znaleziono")
    
    if etap2_roles:
        embed.add_field(name="🎖️ Role po 2 etapie", value="\n".join(etap2_roles), inline=False)
    else:
        embed.add_field(name="🎖️ Role po 2 etapie", value="❌ Nie ustawiono", inline=False)
    
    await ctx.send(embed=embed)
    await ctx.message.delete()

# ========== ZARZĄDZANIE REKRUTANTAMI ==========

@bot.command()
@commands.has_permissions(administrator=True)
async def addrecruiter(ctx, member: discord.Member):
    """Dodaje rekrutanta (tylko admin)"""
    
    recruiters = load_recruiters()
    
    if member.id in recruiters:
        await ctx.send(f"❌ {member.mention} jest już rekrutantem!")
        await ctx.message.delete()
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
    await ctx.message.delete()
    
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
    """Usuwa rekrutanta (tylko admin)"""
    
    recruiters = load_recruiters()
    
    if member.id not in recruiters:
        await ctx.send(f"❌ {member.mention} nie jest rekrutantem!")
        await ctx.message.delete()
        return
    
    recruiters.remove(member.id)
    save_recruiters(recruiters)
    
    embed = discord.Embed(
        title="❌ USUNIĘTO REKRUTANTA",
        description=f"{member.mention} został usunięty z zespołu rekrutacyjnego.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)
    await ctx.message.delete()
    
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
    config = load_config()
    
    if stage == "podanie":
        if success:
            title = "✅ PODANIE ZAAKCEPTOWANE"
            color = discord.Color.green()
            status_text = "Zaakceptowano ✅"
            message = "Twoje podanie zostało zaakceptowane!"
            
            # Nadaj rolę po akceptacji podania
            if config["accepted_role"]:
                role = member.guild.get_role(config["accepted_role"])
                if role:
                    try:
                        await member.add_roles(role)
                        await ctx.send(f"🎭 Nadano rolę {role.mention} użytkownikowi {member.mention}", delete_after=5)
                    except Exception as e:
                        print(f"Nie udało się nadać roli: {e}")
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
            
            # Nadaj dwie role po zaliczeniu 2 etapu
            roles_added = []
            
            if config["etap2_role1"]:
                role = member.guild.get_role(config["etap2_role1"])
                if role:
                    try:
                        await member.add_roles(role)
                        roles_added.append(role.mention)
                    except Exception as e:
                        print(f"Nie udało się nadać roli 1: {e}")
            
            if config["etap2_role2"]:
                role = member.guild.get_role(config["etap2_role2"])
                if role:
                    try:
                        await member.add_roles(role)
                        roles_added.append(role.mention)
                    except Exception as e:
                        print(f"Nie udało się nadać roli 2: {e}")
            
            # Poinformuj o nadanych rolach
            if roles_added:
                await ctx.send(f"🎭 Nadano role: {', '.join(roles_added)} użytkownikowi {member.mention}", delete_after=5)
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
            description=f"Otrzymałeś wynik rekrutacji na serwerze **{member.guild.name}**.",
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
    
    # Usuń wiadomość użytkownika
    await ctx.message.delete()
    
    if status.lower() == "fail":
        await send_recruitment_result(ctx, member, "podanie", "podanie", False)
    elif status.lower() == "true":
        await send_recruitment_result(ctx, member, "podanie", "podanie", True)
    else:
        await ctx.send("❌ Nieprawidłowy status! Użyj `!podanie fail @użytkownik` lub `!podanie true @użytkownik`", delete_after=5)

@bot.command()
@commands.check(is_recruiter_or_admin)
async def etap2(ctx, status: str, member: discord.Member):
    """Ocenia 2 etap rekrutacji
    Użycie: !etap2 fail @użytkownik
    Użycie: !etap2 true @użytkownik"""
    
    # Usuń wiadomość użytkownika
    await ctx.message.delete()
    
    if status.lower() == "fail":
        await send_recruitment_result(ctx, member, "etap2", "etap2", False)
    elif status.lower() == "true":
        await send_recruitment_result(ctx, member, "etap2", "etap2", True)
    else:
        await ctx.send("❌ Nieprawidłowy status! Użyj `!etap2 fail @użytkownik` lub `!etap2 true @użytkownik`", delete_after=5)

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
        embed.add_field(name="⚙️ Konfiguracja ról (admin):", 
                        value="`!setacceptedrole @rola` - ustawia rolę po akceptacji podania\n"
                              "`!setetap2role1 @rola` - ustawia pierwszą rolę po 2 etapie\n"
                              "`!setetap2role2 @rola` - ustawia drugą rolę po 2 etapie\n"
                              "`!setwelcomechannel #kanał` - ustawia kanał powitalny\n"
                              "`!setwelcomerole @rola` - ustawia rolę dla nowych\n"
                              "`!showconfig` - pokazuje konfigurację", inline=False)
        embed.add_field(name="👑 Zarządzanie rekrutantami (admin):", 
                        value="`!addrecruiter @użytkownik` - dodaje rekrutanta\n"
                              "`!removerecruiter @użytkownik` - usuwa rekrutanta\n"
                              "`!recruiters` - lista rekrutantów", inline=False)
        embed.add_field(name="🔧 Admin:", 
                        value="`!say [wiadomość]` - bot wysyła wiadomość", inline=False)
    
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

# Uruchomienie bota
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ BŁĄD: Nieprawidłowy token!")
    except Exception as e:
        print(f"❌ BŁĄD: {e}")
