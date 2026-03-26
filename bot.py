import discord
from discord.ext import commands
import os
import json
from datetime import datetime
import asyncio

# Pobiera token ze zmiennych środowiskowych
TOKEN = os.getenv("TOKEN")

# Ustawiamy uprawnienia bota
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== PLIKI DO PRZECHOWYWANIA DANYCH ==========
RECRUITERS_FILE = "recruiters.json"
CONFIG_FILE = "config.json"
TICKETS_FILE = "tickets.json"

def load_recruiters():
    try:
        with open(RECRUITERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_recruiters(recruiters):
    with open(RECRUITERS_FILE, "w") as f:
        json.dump(recruiters, f)

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "welcome_channel": None,
            "welcome_role": None,
            "accepted_role": None,
            "etap2_role1": None,
            "etap2_role2": None,
            "remove_role": None,
            "ticket_category": None,
            "ticket_panel_channel": None
        }

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def load_tickets():
    try:
        with open(TICKETS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_tickets(tickets):
    with open(TICKETS_FILE, "w") as f:
        json.dump(tickets, f)

# ========== ZDARZENIA ==========

@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")
    print(f"🌐 Bot działa na {len(bot.guilds)} serwerach")
    print("------")

@bot.event
async def on_member_join(member):
    config = load_config()
    
    if config["welcome_role"]:
        role = member.guild.get_role(config["welcome_role"])
        if role:
            try:
                await member.add_roles(role)
                print(f"Nadano rolę {role.name} użytkownikowi {member.name}")
            except:
                print(f"Nie udało się nadać roli {member.name}")
    
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

# ========== SYSTEM TICKETÓW ==========

active_tickets_lock = {}

@bot.command()
@commands.has_permissions(administrator=True)
async def setticketcategory(ctx, category_id: int):
    config = load_config()
    config["ticket_category"] = category_id
    save_config(config)
    category = ctx.guild.get_channel(category_id)
    if category:
        await ctx.send(f"✅ Ustawiono kategorię ticketów na {category.name}")
    else:
        await ctx.send(f"⚠️ Ustawiono ID {category_id}, ale nie znaleziono kategorii")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setticketpanel(ctx, channel: discord.TextChannel):
    config = load_config()
    config["ticket_panel_channel"] = channel.id
    save_config(config)
    await send_ticket_panel(channel)
    await ctx.send(f"✅ Panel ticketów został wysłany na {channel.mention}")
    await ctx.message.delete()

async def send_ticket_panel(channel):
    embed = discord.Embed(
        title="🎫 Podanie",
        description="Kliknij przycisk poniżej, aby napisać podanie.",
        color=discord.Color.green()
    )
    embed.add_field(name="📝 Napisz Podanie", value="Użyj wzoru z kanału wzór-podania", inline=False)
    embed.add_field(name="🔧 Jak użyć?", value="Kliknij przycisk **'Podanie'** poniżej.", inline=False)
    embed.set_footer(text="Możesz mieć tylko jeden otwarty ticket na raz!")
    
    view = discord.ui.View(timeout=None)
    button = discord.ui.Button(label="🎫 Podanie", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    
    async def button_callback(interaction):
        await create_ticket(interaction)
    
    button.callback = button_callback
    view.add_item(button)
    await channel.send(embed=embed, view=view)

async def create_ticket(interaction):
    user_id = interaction.user.id
    if user_id in active_tickets_lock and active_tickets_lock[user_id]:
        await interaction.response.send_message("⏳ Twój ticket jest już w trakcie tworzenia!", ephemeral=True)
        return
    
    active_tickets_lock[user_id] = True
    
    try:
        config = load_config()
        tickets = load_tickets()
        
        for ticket in tickets:
            if ticket["user_id"] == interaction.user.id and ticket["status"] == "open":
                channel = interaction.guild.get_channel(ticket["channel_id"])
                if channel:
                    await interaction.response.send_message(f"❌ Masz już otwarty ticket! {channel.mention}", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Masz już otwarty ticket!", ephemeral=True)
                return
        
        category = None
        if config["ticket_category"]:
            category = interaction.guild.get_channel(config["ticket_category"])
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }
        
        recruiters = load_recruiters()
        for recruiter_id in recruiters:
            recruiter = interaction.guild.get_member(recruiter_id)
            if recruiter:
                overwrites[recruiter] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        
        for member in interaction.guild.members:
            if member.guild_permissions.administrator:
                overwrites[member] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        
        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )
        
        ticket_data = {
            "user_id": interaction.user.id,
            "channel_id": channel.id,
            "status": "open",
            "created_at": datetime.now().isoformat()
        }
        tickets.append(ticket_data)
        save_tickets(tickets)
        
        embed = discord.Embed(
            title="🎫 Ticket otwarty",
            description=f"Witaj {interaction.user.mention}!",
            color=discord.Color.green()
        )
        embed.add_field(name="📝 Postaraj się z podaniem", value="Wkrótce ktoś sprawdzi twoje podanie.", inline=False)
        embed.add_field(name="🔒 Zamknięcie ticketu", value="Gdy podanie zostanie rozpatrzone kliknij 'Zamknij Ticket' poniżej.", inline=False)
        
        close_button = discord.ui.Button(label="🔒 Zamknij Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
        
        async def close_callback(interaction_close):
            await close_ticket(interaction_close, channel)
        
        close_button.callback = close_callback
        view = discord.ui.View(timeout=None)
        view.add_item(close_button)
        
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket został utworzony! {channel.mention}", ephemeral=True)
        
    finally:
        await asyncio.sleep(1)
        active_tickets_lock[user_id] = False

async def close_ticket(interaction, channel):
    tickets = load_tickets()
    for ticket in tickets:
        if ticket["channel_id"] == channel.id:
            ticket["status"] = "closed"
            break
    save_tickets(tickets)
    
    embed = discord.Embed(title="🔒 Ticket zamknięty", description="Ten ticket zostanie usunięty za 5 sekund.", color=discord.Color.red())
    await channel.send(embed=embed)
    
    try:
        await interaction.response.send_message("✅ Ticket zostanie zamknięty.", ephemeral=True)
    except:
        pass
    
    await asyncio.sleep(5)
    await channel.delete()

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data["custom_id"] == "create_ticket":
            await create_ticket(interaction)
        elif interaction.data["custom_id"] == "close_ticket":
            channel = interaction.channel
            await close_ticket(interaction, channel)

# ========== KONFIGURACJA SERWERA ==========

@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcomechannel(ctx, channel: discord.TextChannel):
    config = load_config()
    config["welcome_channel"] = channel.id
    save_config(config)
    await ctx.send(f"✅ Ustawiono kanał powitalny na {channel.mention}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcomerole(ctx, role: discord.Role):
    config = load_config()
    config["welcome_role"] = role.id
    save_config(config)
    await ctx.send(f"✅ Ustawiono rolę powitalną na {role.mention}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setacceptedrole(ctx, role: discord.Role):
    config = load_config()
    config["accepted_role"] = role.id
    save_config(config)
    await ctx.send(f"✅ Ustawiono rolę dla zaakceptowanych na {role.mention}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setetap2role1(ctx, role: discord.Role):
    config = load_config()
    config["etap2_role1"] = role.id
    save_config(config)
    await ctx.send(f"✅ Ustawiono pierwszą rolę dla 2 etapu na {role.mention}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setetap2role2(ctx, role: discord.Role):
    config = load_config()
    config["etap2_role2"] = role.id
    save_config(config)
    await ctx.send(f"✅ Ustawiono drugą rolę dla 2 etapu na {role.mention}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setremoverole(ctx, role: discord.Role):
    config = load_config()
    config["remove_role"] = role.id
    save_config(config)
    await ctx.send(f"✅ Ustawiono rolę do usunięcia po 2 etapie: {role.mention}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def showconfig(ctx):
    config = load_config()
    embed = discord.Embed(title="⚙️ Konfiguracja serwera", color=discord.Color.blue())
    
    if config["welcome_channel"]:
        channel = bot.get_channel(config["welcome_channel"])
        embed.add_field(name="📢 Kanał powitalny", value=channel.mention if channel else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="📢 Kanał powitalny", value="❌ Nie ustawiono", inline=False)
    
    if config["welcome_role"]:
        role = ctx.guild.get_role(config["welcome_role"])
        embed.add_field(name="🎭 Rola dla nowych", value=role.mention if role else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="🎭 Rola dla nowych", value="❌ Nie ustawiono", inline=False)
    
    if config["accepted_role"]:
        role = ctx.guild.get_role(config["accepted_role"])
        embed.add_field(name="✅ Rola po akceptacji podania", value=role.mention if role else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="✅ Rola po akceptacji podania", value="❌ Nie ustawiono", inline=False)
    
    etap2_roles = []
    if config["etap2_role1"]:
        role = ctx.guild.get_role(config["etap2_role1"])
        etap2_roles.append(role.mention if role else "Nie znaleziono")
    if config["etap2_role2"]:
        role = ctx.guild.get_role(config["etap2_role2"])
        etap2_roles.append(role.mention if role else "Nie znaleziono")
    embed.add_field(name="🎖️ Role po 2 etapie", value="\n".join(etap2_roles) if etap2_roles else "❌ Nie ustawiono", inline=False)
    
    if config["remove_role"]:
        role = ctx.guild.get_role(config["remove_role"])
        embed.add_field(name="🗑️ Rola do usunięcia po 2 etapie", value=role.mention if role else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="🗑️ Rola do usunięcia po 2 etapie", value="❌ Nie ustawiono", inline=False)
    
    if config["ticket_category"]:
        category = ctx.guild.get_channel(config["ticket_category"])
        embed.add_field(name="🎫 Kategoria ticketów", value=category.name if category else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="🎫 Kategoria ticketów", value="❌ Nie ustawiono", inline=False)
    
    if config["ticket_panel_channel"]:
        channel = bot.get_channel(config["ticket_panel_channel"])
        embed.add_field(name="📋 Kanał panelu ticketów", value=channel.mention if channel else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="📋 Kanał panelu ticketów", value="❌ Nie ustawiono", inline=False)
    
    await ctx.send(embed=embed)
    await ctx.message.delete()

# ========== ZARZĄDZANIE REKRUTANTAMI ==========

@bot.command()
@commands.has_permissions(administrator=True)
async def addrecruiter(ctx, member: discord.Member):
    recruiters = load_recruiters()
    if member.id in recruiters:
        await ctx.send(f"❌ {member.mention} jest już rekrutantem!")
        await ctx.message.delete()
        return
    recruiters.append(member.id)
    save_recruiters(recruiters)
    embed = discord.Embed(title="✅ DODANO REKRUTANTA", description=f"{member.mention} został dodany do zespołu rekrutacyjnego!", color=discord.Color.green())
    await ctx.send(embed=embed)
    await ctx.message.delete()
    try:
        await member.send(f"🎉 Zostałeś rekrutantem na serwerze {ctx.guild.name}!")
    except:
        pass

@bot.command()
@commands.has_permissions(administrator=True)
async def removerecruiter(ctx, member: discord.Member):
    recruiters = load_recruiters()
    if member.id not in recruiters:
        await ctx.send(f"❌ {member.mention} nie jest rekrutantem!")
        await ctx.message.delete()
        return
    recruiters.remove(member.id)
    save_recruiters(recruiters)
    embed = discord.Embed(title="❌ USUNIĘTO REKRUTANTA", description=f"{member.mention} został usunięty z zespołu rekrutacyjnego.", color=discord.Color.red())
    await ctx.send(embed=embed)
    await ctx.message.delete()

@bot.command()
async def recruiters(ctx):
    recruiters = load_recruiters()
    if not recruiters:
        await ctx.send("📋 Brak rekrutantów w bazie.")
        return
    embed = discord.Embed(title="📋 LISTA REKRUTANTÓW", color=discord.Color.blue())
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
    if ctx.author.guild_permissions.administrator:
        return True
    recruiters = load_recruiters()
    return ctx.author.id in recruiters

# ========== KOMENDY REKRUTACYJNE ==========

async def send_recruitment_result(ctx, member, stage, success):
    config = load_config()
    
    if stage == "podanie":
        if success:
            title = "✅ PODANIE ZAAKCEPTOWANE"
            color = discord.Color.green()
            status_text = "Zaakceptowano ✅"
            message = "Twoje podanie zostało zaakceptowane!"
            if config["accepted_role"]:
                role = member.guild.get_role(config["accepted_role"])
                if role:
                    try:
                        await member.add_roles(role)
                        await ctx.send(f"🎭 Nadano rolę {role.mention} użytkownikowi {member.mention}", delete_after=5)
                    except:
                        pass
        else:
            title = "❌ PODANIE ODRZUCONE"
            color = discord.Color.red()
            status_text = "Nie zaakceptowano ❌"
            message = "Twoje podanie nie zostało zaakceptowane."
    else:
        if success:
            title = "✅ ETAP 2 - ZALICZONY"
            color = discord.Color.green()
            status_text = "Przeszedł 2 etap ✅"
            message = "Gratulacje! Przeszedłeś/łaś 2 etap rekrutacji!"
            if config["remove_role"]:
                role = member.guild.get_role(config["remove_role"])
                if role and role in member.roles:
                    try:
                        await member.remove_roles(role)
                        await ctx.send(f"🗑️ Usunięto rolę {role.mention} użytkownikowi {member.mention}", delete_after=5)
                    except:
                        pass
            roles_added = []
            if config["etap2_role1"]:
                role = member.guild.get_role(config["etap2_role1"])
                if role:
                    try:
                        await member.add_roles(role)
                        roles_added.append(role.mention)
                    except:
                        pass
            if config["etap2_role2"]:
                role = member.guild.get_role(config["etap2_role2"])
                if role:
                    try:
                        await member.add_roles(role)
                        roles_added.append(role.mention)
                    except:
                        pass
            if roles_added:
                await ctx.send(f"🎭 Nadano role: {', '.join(roles_added)} użytkownikowi {member.mention}", delete_after=5)
        else:
            title = "❌ ETAP 2 - NIEZALICZONY"
            color = discord.Color.red()
            status_text = "Nie przeszedł 2 etapu ❌"
            message = "Niestety nie przeszedłeś/łaś 2 etapu rekrutacji."
    
    embed = discord.Embed(title=title, description=f"Wynik rekrutacji dla {member.mention}", color=color)
    embed.add_field(name="Status", value=f"**{status_text}**", inline=False)
    embed.add_field(name="Wiadomość", value=message, inline=False)
    embed.add_field(name="Rekrutujący", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)
    
    try:
        await member.send(embed=embed)
    except:
        pass
    try:
        await ctx.author.send(f"✅ Wynik dla {member.name} został wysłany: {status_text}")
    except:
        pass

@bot.command()
@commands.check(is_recruiter_or_admin)
async def podanie(ctx, status: str, member: discord.Member):
    await ctx.message.delete()
    if status.lower() == "fail":
        await send_recruitment_result(ctx, member, "podanie", False)
    elif status.lower() == "true":
        await send_recruitment_result(ctx, member, "podanie", True)
    else:
        await ctx.send("❌ Użyj `!podanie fail @użytkownik` lub `!podanie true @użytkownik`", delete_after=5)

@bot.command()
@commands.check(is_recruiter_or_admin)
async def etap2(ctx, status: str, member: discord.Member):
    await ctx.message.delete()
    if status.lower() == "fail":
        await send_recruitment_result(ctx, member, "etap2", False)
    elif status.lower() == "true":
        await send_recruitment_result(ctx, member, "etap2", True)
    else:
        await ctx.send("❌ Użyj `!etap2 fail @użytkownik` lub `!etap2 true @użytkownik`", delete_after=5)

# ========== KOMENDA REKRUTACJA OPEN ==========

@bot.command()
@commands.has_permissions(administrator=True)
async def rekrutacja_open(ctx):
    """Wysyła ogłoszenie o otwarciu rekrutacji z pingiem roli o ID 1486772105965207725"""
    
    ROLE_ID = 1486772105965207725
    role = ctx.guild.get_role(ROLE_ID)
    
    if not role:
        await ctx.send("❌ Nie znaleziono roli o ID 1486772105965207725!")
        await ctx.message.delete()
        return
    
    embed = discord.Embed(
        title="🔴 REKRUTACJA OTWARTA!",
        description="Rekrutacja została właśnie otwarta!",
        color=discord.Color.red()
    )
    embed.add_field(
        name="📝 Jak wziąć udział?",
        value="Wejdź na kanał **poczekalnia** i kliknij przycisk **'Podanie'**.",
        inline=False
    )
    embed.add_field(
        name="⏰ Czas trwania",
        value="Rekrutacja będzie otwarta przez ograniczony czas. Nie zwlekaj!",
        inline=False
    )
    embed.set_footer(text="Powodzenia!")
    
    await ctx.send(f"{role.mention} 🔴 **REKRUTACJA OTWARTA!** 🔴")
    await ctx.send(embed=embed)
    await ctx.message.delete()
    print("✅ Komenda rekrutacja_open wykonana!")

@bot.command()
@commands.has_permissions(administrator=True)
async def rekrutacja_closed(ctx):
    """Wysyła ogłoszenie o zamknięciu rekrutacji"""
    
    embed = discord.Embed(
        title="⚫ REKRUTACJA ZAMKNIĘTA",
        description="Rekrutacja została właśnie zamknięta.",
        color=discord.Color.dark_gray()
    )
    embed.add_field(
        name="📝 Co dalej?",
        value="Dziękujemy wszystkim za udział! Osoby które złożyły podanie otrzymają odpowiedź wkrótce.",
        inline=False
    )
    embed.set_footer(text=f"Ogłoszenie wysłane przez {ctx.author.name}")
    
    await ctx.send(embed=embed)
    await ctx.message.delete()
    print("✅ Komenda rekrutacja_closed wykonana!")

# ========== KOMENDA POMOCY ==========

@bot.command()
async def helpme(ctx):
    is_recruiter = is_recruiter_or_admin(ctx)
    
    embed = discord.Embed(title="🤖 Pomoc - Dostępne komendy", color=discord.Color.blue())
    
    embed.add_field(name="📌 Podstawowe:", value="`!ping` - sprawdza bota\n`!hello` - przywitanie\n`!helpme` - pokazuje tę pomoc", inline=False)
    
    if is_recruiter:
        embed.add_field(name="📝 Rekrutacja (rekrutanci/admin):", value="`!podanie true/fail @użytkownik` - ocena podania\n`!etap2 true/fail @użytkownik` - ocena 2 etapu", inline=False)
    
    if ctx.author.guild_permissions.administrator:
        embed.add_field(name="⚙️ Konfiguracja serwera (admin):", 
                        value="`!setwelcomechannel #kanał` - kanał powitalny\n`!setwelcomerole @rola` - rola dla nowych\n`!setacceptedrole @rola` - rola po akceptacji\n`!setetap2role1 @rola` - pierwsza rola po 2 etapie\n`!setetap2role2 @rola` - druga rola po 2 etapie\n`!setremoverole @rola` - rola do usunięcia\n`!setticketcategory ID` - kategoria ticketów\n`!setticketpanel #kanał` - panel ticketów\n`!showconfig` - pokazuje konfigurację", inline=False)
        embed.add_field(name="👑 Zarządzanie rekrutantami (admin):", value="`!addrecruiter @user` - dodaje rekrutanta\n`!removerecruiter @user` - usuwa rekrutanta\n`!recruiters` - lista rekrutantów", inline=False)
        embed.add_field(name="🔴 Komendy rekrutacji (admin):", value="`!rekrutacja-open` - otwiera rekrutację\n`!rekrutacja-closed` - zamyka rekrutację", inline=False)
        embed.add_field(name="🔧 Inne admin:", value="`!say [wiadomość]` - bot wysyła wiadomość", inline=False)
    
    await ctx.send(embed=embed)

# ========== PROSTE KOMENDY ==========

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! 🏓 {round(bot.latency * 1000)}ms")

@bot.command()
async def hello(ctx):
    await ctx.send(f"Cześć {ctx.author.mention}! 👋")

@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, *, wiadomosc):
    await ctx.message.delete()
    await ctx.send(wiadomosc)

# ========== URUCHOMIENIE ==========

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ BŁĄD: {e}")
