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
CONFIG_FILE = "config.json"
TICKETS_FILE = "tickets.json"

def load_config():
    """Wczytuje konfigurację serwera"""
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "welcome_channel": None,
            "welcome_role": None,
            "ticket_category": None,
            "ticket_panel_channel": None,
            "ticket_footer_image": None,
            "ticket_logo_url": None
        }

def save_config(config):
    """Zapisuje konfigurację serwera"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def load_tickets():
    """Wczytuje listę ticketów"""
    try:
        with open(TICKETS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_tickets(tickets):
    """Zapisuje listę ticketów"""
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

# ========== SYSTEM TICKETÓW ==========

active_tickets_lock = {}

@bot.command()
@commands.has_permissions(administrator=True)
async def setticketfooter(ctx, url: str = None):
    """Ustawia obrazek na dole ticketu (URL)
    Użycie: !setticketfooter https://example.com/obrazek.png"""
    config = load_config()
    config["ticket_footer_image"] = url
    save_config(config)
    
    if url:
        await ctx.send(f"✅ Ustawiono obrazek ticketu")
    else:
        await ctx.send(f"✅ Usunięto obrazek ticketu")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setticketlogo(ctx, url: str = None):
    """Ustawia logo w lewym górnym rogu ticketu (URL)
    Użycie: !setticketlogo https://example.com/logo.png"""
    config = load_config()
    config["ticket_logo_url"] = url
    save_config(config)
    
    if url:
        await ctx.send(f"✅ Ustawiono logo ticketu")
    else:
        await ctx.send(f"✅ Usunięto logo ticketu")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setticketcategory(ctx, category_id: int):
    """Ustawia kategorię dla ticketów używając ID"""
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
    """Ustawia kanał z panelem ticketów i wysyła panel"""
    config = load_config()
    config["ticket_panel_channel"] = channel.id
    save_config(config)
    
    await send_ticket_panel(channel)
    await ctx.send(f"✅ Panel ticketów został wysłany na {channel.mention}")
    await ctx.message.delete()

async def send_ticket_panel(channel):
    """Wysyła panel ticketów na wskazany kanał"""
    embed = discord.Embed(
        title="🎫 **Vireona Hub** × **TICKET**",
        description="Kliknij przycisk poniżej, aby otworzyć ticket.",
        color=0x2b2d31
    )
    embed.add_field(name="📝 Co to jest?", value="Ticket to prywatny kanał, gdzie możesz porozmawiać z administracją.", inline=False)
    embed.add_field(name="🔧 Jak użyć?", value="Kliknij przycisk **'Otwórz Ticket'** poniżej.", inline=False)
    embed.set_footer(text="Możesz mieć tylko jeden otwarty ticket na raz!")
    
    view = discord.ui.View(timeout=None)
    button = discord.ui.Button(label="🎫 Otwórz Ticket", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    
    async def button_callback(interaction):
        await create_ticket(interaction)
    
    button.callback = button_callback
    view.add_item(button)
    
    await channel.send(embed=embed, view=view)

async def create_ticket(interaction):
    """Tworzy nowy ticket - sprawdza czy użytkownik nie ma już otwartego"""
    user_id = interaction.user.id
    if user_id in active_tickets_lock and active_tickets_lock[user_id]:
        await interaction.response.send_message("⏳ Twój ticket jest już w trakcie tworzenia!", ephemeral=True)
        return
    
    active_tickets_lock[user_id] = True
    
    try:
        config = load_config()
        tickets = load_tickets()
        
        # Sprawdź czy użytkownik ma już otwarty ticket
        for ticket in tickets:
            if ticket["user_id"] == interaction.user.id and ticket["status"] == "open":
                channel = interaction.guild.get_channel(ticket["channel_id"])
                if channel:
                    await interaction.response.send_message(f"❌ Masz już otwarty ticket! {channel.mention}", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Masz już otwarty ticket!", ephemeral=True)
                return
        
        # Znajdź kategorię
        category = None
        if config["ticket_category"]:
            category = interaction.guild.get_channel(config["ticket_category"])
        
        # Stwórz kanał ticketu
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }
        
        # Dodaj adminów
        for member in interaction.guild.members:
            if member.guild_permissions.administrator:
                overwrites[member] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        
        # Utwórz kanał
        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )
        
        # Zapisz ticket
        ticket_data = {
            "user_id": interaction.user.id,
            "channel_id": channel.id,
            "status": "open",
            "created_at": datetime.now().isoformat()
        }
        tickets.append(ticket_data)
        save_tickets(tickets)
        
        # ========== PIĘKNY EMBED TICKETU ==========
        
        # Przygotuj zamazane ID (spoiler)
        user_id_str = str(interaction.user.id)
        masked_id = f"||{user_id_str[:3]}XXXXXX{user_id_str[-3:]}||"
        
        # Przygotuj logo
        logo_url = config.get("ticket_logo_url")
        
        # Tytuł z czarnym tłem
        title_text = "╔════════════════════════════════════════╗\n║          🎫 Vireona Hub × TICKET          ║\n╚════════════════════════════════════════╝"
        
        # Utwórz embed z niebieską linią po lewej
        embed = discord.Embed(
            description=f"```\n{title_text}\n```",
            color=0x5865f2
        )
        
        # Dodaj logo w miniaturce (lewy górny róg)
        if logo_url:
            embed.set_thumbnail(url=logo_url)
        
        # Sekcja 1: Informacje o kliencie
        embed.add_field(
            name="**🎫 INFORMACJE O KLIENCIE:**",
            value=f"> **🔔 Ping:** {interaction.user.mention}\n> **🔔 Nick:** **{interaction.user.name}**\n> **🔔 ID:** {masked_id}",
            inline=False
        )
        
        # Sekcja 2: Informacje o pomocy
        embed.add_field(
            name="**🎫 INFORMACJE O POMOCY:**",
            value="> **📌 Wybrane podanie:** `Administracja`\n> \n> **📝 Opisz swoją sprawę poniżej.**\n> Administracja odpowie tak szybko jak to możliwe.",
            inline=False
        )
        
        # Dodaj obrazek na dole jeśli jest ustawiony
        if config.get("ticket_footer_image"):
            embed.set_image(url=config["ticket_footer_image"])
        
        # Dodaj stopkę z nazwą serwera i datą
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        embed.set_footer(
            text=f"{interaction.guild.name} • {current_time}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        # Przycisk zamknięcia
        close_button = discord.ui.Button(label="🔒 Zamknij Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
        
        async def close_callback(interaction_close):
            await close_ticket(interaction_close, channel)
        
        close_button.callback = close_callback
        
        view = discord.ui.View(timeout=None)
        view.add_item(close_button)
        
        # Wyślij ping dla graczy z komendą /spoiler
        await channel.send(f"||@everyone|| 🎫 **Nowy ticket od {interaction.user.mention}**")
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket został utworzony! {channel.mention}", ephemeral=True)
        
    finally:
        await asyncio.sleep(1)
        active_tickets_lock[user_id] = False

async def close_ticket(interaction, channel):
    """Zamyka ticket"""
    tickets = load_tickets()
    
    # Aktualizuj status
    for ticket in tickets:
        if ticket["channel_id"] == channel.id:
            ticket["status"] = "closed"
            break
    
    save_tickets(tickets)
    
    embed = discord.Embed(
        title="🔒 Ticket zamknięty",
        description="Ten ticket zostanie usunięty za 5 sekund.",
        color=discord.Color.red()
    )
    await channel.send(embed=embed)
    
    try:
        await interaction.response.send_message("✅ Ticket zostanie zamknięty.", ephemeral=True)
    except:
        pass
    
    await asyncio.sleep(5)
    await channel.delete()

@bot.event
async def on_interaction(interaction):
    """Obsługuje przyciski ticketów"""
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
    """Ustawia kanał dla powitań"""
    config = load_config()
    config["welcome_channel"] = channel.id
    save_config(config)
    await ctx.send(f"✅ Ustawiono kanał powitalny na {channel.mention}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcomerole(ctx, role: discord.Role):
    """Ustawia rolę dla nowych członków"""
    config = load_config()
    config["welcome_role"] = role.id
    save_config(config)
    await ctx.send(f"✅ Ustawiono rolę powitalną na {role.mention}")
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
    
    # Kategoria ticketów
    if config["ticket_category"]:
        category = ctx.guild.get_channel(config["ticket_category"])
        embed.add_field(name="🎫 Kategoria ticketów", value=category.name if category else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="🎫 Kategoria ticketów", value="❌ Nie ustawiono", inline=False)
    
    # Kanał panelu ticketów
    if config["ticket_panel_channel"]:
        channel = bot.get_channel(config["ticket_panel_channel"])
        embed.add_field(name="📋 Kanał panelu ticketów", value=channel.mention if channel else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="📋 Kanał panelu ticketów", value="❌ Nie ustawiono", inline=False)
    
    # Obrazek ticketu
    if config["ticket_footer_image"]:
        embed.add_field(name="🖼️ Obrazek ticketu", value="Ustawiony", inline=False)
    else:
        embed.add_field(name="🖼️ Obrazek ticketu", value="❌ Nie ustawiono", inline=False)
    
    # Logo ticketu
    if config["ticket_logo_url"]:
        embed.add_field(name="🖼️ Logo ticketu", value="Ustawione", inline=False)
    else:
        embed.add_field(name="🖼️ Logo ticketu", value="❌ Nie ustawiono", inline=False)
    
    await ctx.send(embed=embed)
    await ctx.message.delete()

# ========== KOMENDA POMOCY ==========

@bot.command()
async def helpme(ctx):
    """Pokazuje dostępne komendy"""
    embed = discord.Embed(
        title="🤖 Pomoc - dostępne komendy",
        description="Lista komend które możesz używać:",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="📌 Podstawowe:", 
                    value="`!ping` - sprawdza czy bot działa\n`!hello` - bot się przywita\n`!helpme` - pokazuje tę pomoc", 
                    inline=False)
    
    if ctx.author.guild_permissions.administrator:
        embed.add_field(name="⚙️ Konfiguracja (admin):", 
                        value="`!setwelcomechannel #kanał` - ustawia kanał powitalny\n"
                              "`!setwelcomerole @rola` - ustawia rolę dla nowych członków\n"
                              "`!setticketcategory ID` - ustawia kategorię dla ticketów\n"
                              "`!setticketpanel #kanał` - ustawia kanał panelu ticketów\n"
                              "`!setticketfooter URL` - ustawia obrazek na dole ticketu\n"
                              "`!setticketlogo URL` - ustawia logo w lewym górnym rogu\n"
                              "`!showconfig` - pokazuje konfigurację", 
                        inline=False)
    
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

# ========== URUCHOMIENIE ==========

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ BŁĄD: Nieprawidłowy token!")
    except Exception as e:
        print(f"❌ BŁĄD: {e}")
