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
TRANSCRIPTS_FOLDER = "transcripts"

# Utwórz folder na transkrypty jeśli nie istnieje
if not os.path.exists(TRANSCRIPTS_FOLDER):
    os.makedirs(TRANSCRIPTS_FOLDER)

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

# ========== FUNKCJE DO TRANSCRIPT ==========

async def save_transcript(channel, ticket_id):
    """Zapisuje transkrypt ticketu do pliku"""
    messages = []
    async for message in channel.history(limit=None, oldest_first=True):
        messages.append(message)
    
    if not messages:
        return None
    
    # Przygotuj zawartość transkryptu
    transcript_lines = []
    transcript_lines.append(f"=== TRANSCRIPT TICKETU {ticket_id} ===")
    transcript_lines.append(f"Kanał: #{channel.name}")
    transcript_lines.append(f"Data utworzenia: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    transcript_lines.append("=" * 50)
    transcript_lines.append("")
    
    for msg in messages:
        timestamp = msg.created_at.strftime("%H:%M:%S")
        author = msg.author.name
        content = msg.content if msg.content else "[EMBED/ZAŁĄCZNIK]"
        transcript_lines.append(f"[{timestamp}] {author}: {content}")
        
        # Dodaj załączniki jeśli są
        if msg.attachments:
            for att in msg.attachments:
                transcript_lines.append(f"  → Załącznik: {att.url}")
    
    transcript_lines.append("")
    transcript_lines.append("=" * 50)
    transcript_lines.append(f"Koniec transkryptu - {len(messages)} wiadomości")
    
    # Zapisz do pliku
    filename = f"{TRANSCRIPTS_FOLDER}/ticket_{ticket_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(transcript_lines))
    
    return filename

async def send_transcript_to_user(user, filename, ticket_id):
    """Wysyła transkrypt do użytkownika na PW"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Jeśli plik jest za duży, wyślij jako załącznik
        if len(content) > 1900:
            await user.send(f"📋 **Transkrypt ticketu #{ticket_id}**")
            await user.send(file=discord.File(filename))
        else:
            embed = discord.Embed(
                title=f"📋 Transkrypt ticketu #{ticket_id}",
                description=f"```\n{content[:1800]}\n```",
                color=discord.Color.blue()
            )
            await user.send(embed=embed)
        return True
    except Exception as e:
        print(f"Błąd wysyłania transkryptu: {e}")
        return False

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
async def setticketfooter(ctx, url: str = None):
    config = load_config()
    config["ticket_footer_image"] = url
    save_config(config)
    await ctx.send(f"✅ Ustawiono obrazek ticketu" if url else "✅ Usunięto obrazek ticketu")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setticketlogo(ctx, url: str = None):
    config = load_config()
    config["ticket_logo_url"] = url
    save_config(config)
    await ctx.send(f"✅ Ustawiono logo ticketu" if url else "✅ Usunięto logo ticketu")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setticketcategory(ctx, category_id: int):
    config = load_config()
    config["ticket_category"] = category_id
    save_config(config)
    category = ctx.guild.get_channel(category_id)
    await ctx.send(f"✅ Ustawiono kategorię ticketów na {category.name}" if category else f"⚠️ Ustawiono ID {category_id}")
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
        title="🎫 Vireona Hub × TICKET",
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
        
        for member in interaction.guild.members:
            if member.guild_permissions.administrator:
                overwrites[member] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        
        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )
        
        ticket_id = len(tickets) + 1
        ticket_data = {
            "id": ticket_id,
            "user_id": interaction.user.id,
            "channel_id": channel.id,
            "status": "open",
            "created_at": datetime.now().isoformat()
        }
        tickets.append(ticket_data)
        save_tickets(tickets)
        
        # ========== PIĘKNY EMBED TICKETU ==========
        
        user_id_str = str(interaction.user.id)
        masked_id = f"||{user_id_str[:3]}XXXXXX{user_id_str[-3:]}||"
        
        # Czarne tło na tytule
        title_text = "```\n🎫 Vireona Hub × TICKET\n```"
        
        logo_url = config.get("ticket_logo_url")
        
        embed = discord.Embed(
            description=title_text,
            color=0x5865f2
        )
        
        if logo_url:
            embed.set_thumbnail(url=logo_url)
        
        # Dopasowanie długości nicku
        nick_length = len(interaction.user.name)
        nick_spacing = " " * (20 - nick_length) if nick_length < 20 else ""
        
        embed.add_field(
            name="**🎫 INFORMACJE O KLIENCIE:**",
            value=f"> **🔔 Ping:** {interaction.user.mention}\n> **🔔 Nick:** **{interaction.user.name}**{nick_spacing}\n> **🔔 ID:** {masked_id}",
            inline=False
        )
        
        embed.add_field(
            name="**🎫 INFORMACJE O POMOCY:**",
            value="> **📌 Wybrane podanie:** `Administracja`\n> \n> **📝 Opisz swoją sprawę poniżej.**\n> Administracja odpowie tak szybko jak to możliwe.",
            inline=False
        )
        
        if config.get("ticket_footer_image"):
            embed.set_image(url=config["ticket_footer_image"])
        
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        embed.set_footer(
            text=f"{interaction.guild.name} • {current_time}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        close_button = discord.ui.Button(label="🔒 Zamknij Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
        
        async def close_callback(interaction_close):
            await close_ticket(interaction_close, channel, ticket_id)
        
        close_button.callback = close_callback
        
        view = discord.ui.View(timeout=None)
        view.add_item(close_button)
        
        # Ping bez dodatkowego tekstu
        await channel.send(f"||@everyone||")
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket został utworzony! {channel.mention}", ephemeral=True)
        
    finally:
        await asyncio.sleep(1)
        active_tickets_lock[user_id] = False

async def close_ticket(interaction, channel, ticket_id):
    """Zamyka ticket i zapisuje transkrypt"""
    tickets = load_tickets()
    
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            ticket["status"] = "closed"
            break
    
    save_tickets(tickets)
    
    # Zapisz transkrypt
    transcript_file = await save_transcript(channel, ticket_id)
    
    # Wyślij transkrypt do użytkownika
    user = interaction.guild.get_member(ticket["user_id"])
    if user and transcript_file:
        await send_transcript_to_user(user, transcript_file, ticket_id)
    
    # Wyślij transkrypt na kanał admina (opcjonalnie)
    # Możesz dodać kanał do zapisywania transkryptów
    
    embed = discord.Embed(
        title="🔒 Ticket zamknięty",
        description=f"Ten ticket zostanie usunięty za 5 sekund.\nTranskrypt został wysłany na PW.",
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
    if interaction.type == discord.InteractionType.component:
        if interaction.data["custom_id"] == "create_ticket":
            await create_ticket(interaction)
        elif interaction.data["custom_id"] == "close_ticket":
            channel = interaction.channel
            # Znajdź ID ticketu
            tickets = load_tickets()
            ticket_id = None
            for ticket in tickets:
                if ticket["channel_id"] == channel.id:
                    ticket_id = ticket["id"]
                    break
            if ticket_id:
                await close_ticket(interaction, channel, ticket_id)

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
async def showconfig(ctx):
    config = load_config()
    
    embed = discord.Embed(
        title="⚙️ Konfiguracja serwera",
        color=discord.Color.blue()
    )
    
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
    
    if config["ticket_footer_image"]:
        embed.add_field(name="🖼️ Obrazek ticketu", value="Ustawiony", inline=False)
    else:
        embed.add_field(name="🖼️ Obrazek ticketu", value="❌ Nie ustawiono", inline=False)
    
    if config["ticket_logo_url"]:
        embed.add_field(name="🖼️ Logo ticketu", value="Ustawione", inline=False)
    else:
        embed.add_field(name="🖼️ Logo ticketu", value="❌ Nie ustawiono", inline=False)
    
    await ctx.send(embed=embed)
    await ctx.message.delete()

# ========== KOMENDA POMOCY ==========

@bot.command()
async def helpme(ctx):
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
    await ctx.send(f"Pong! 🏓 Opóźnienie: {round(bot.latency * 1000)}ms")

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
    except discord.LoginFailure:
        print("❌ BŁĄD: Nieprawidłowy token!")
    except Exception as e:
        print(f"❌ BŁĄD: {e}")
