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
            "ticket_logo_url": None,
            "ticket_panel_image": None,
            "claim_role": None,
            "problem_emoji": "❌",
            "wspolpraca_emoji": "🤝",
            "kontakt_emoji": "📞"
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

# ========== FUNKCJE DO TRANSCRIPT ==========

async def save_transcript(channel, ticket_id):
    messages = []
    async for message in channel.history(limit=None, oldest_first=True):
        messages.append(message)
    
    if not messages:
        return None
    
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
        
        if msg.attachments:
            for att in msg.attachments:
                transcript_lines.append(f"  → Załącznik: {att.url}")
    
    transcript_lines.append("")
    transcript_lines.append("=" * 50)
    transcript_lines.append(f"Koniec transkryptu - {len(messages)} wiadomości")
    
    filename = f"{TRANSCRIPTS_FOLDER}/ticket_{ticket_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(transcript_lines))
    
    return filename

async def send_transcript_to_user(user, filename, ticket_id):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        
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
claimed_tickets = {}

@bot.command()
@commands.has_permissions(administrator=True)
async def setclaimrole(ctx, role: discord.Role):
    config = load_config()
    config["claim_role"] = role.id
    save_config(config)
    await ctx.send(f"✅ Ustawiono rolę do przejmowania ticketów na {role.mention}")
    await ctx.message.delete()

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
async def setticketpanelimage(ctx, url: str = None):
    """Ustawia obrazek w panelu ticketów pod przyciskami"""
    config = load_config()
    config["ticket_panel_image"] = url
    save_config(config)
    await ctx.send(f"✅ Ustawiono obrazek panelu ticketów" if url else "✅ Usunięto obrazek panelu ticketów")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setproblememoji(ctx, emoji: str):
    """Ustawia emotkę dla przycisku Problem"""
    config = load_config()
    config["problem_emoji"] = emoji
    save_config(config)
    await ctx.send(f"✅ Ustawiono emotkę dla Problemu: {emoji}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setwspolpracaemoji(ctx, emoji: str):
    """Ustawia emotkę dla przycisku Współpraca"""
    config = load_config()
    config["wspolpraca_emoji"] = emoji
    save_config(config)
    await ctx.send(f"✅ Ustawiono emotkę dla Współpracy: {emoji}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setkontaktemoji(ctx, emoji: str):
    """Ustawia emotkę dla przycisku Kontakt z administracją"""
    config = load_config()
    config["kontakt_emoji"] = emoji
    save_config(config)
    await ctx.send(f"✅ Ustawiono emotkę dla Kontaktu: {emoji}")
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
    """Wysyła panel ticketów na wskazany kanał"""
    config = load_config()
    
    # Główny embed panelu
    embed = discord.Embed(
        title="**KONTAKT Z ADMINISTRACJĄ**",
        description="**Aby skontaktować się z Administracją, wybierz odpowiednią kategorię, z podanych poniżej, Twój bilet automatycznie zostanie dostarczony do osób zajmujących się Twoją sprawą.**",
        color=0x5865f2
    )
    
    # Dodaj obrazek panelu jeśli jest ustawiony
    if config.get("ticket_panel_image"):
        embed.set_image(url=config["ticket_panel_image"])
    
    embed.set_footer(text="Pingowanie Administracji równe jest z przerwą 7 dni na discordzie.")
    
    # Przyciski kategorii (szare - secondary)
    view = discord.ui.View(timeout=None)
    
    # Pobierz emotki z configu
    problem_emoji = config.get("problem_emoji", "❌")
    wspolpraca_emoji = config.get("wspolpraca_emoji", "🤝")
    kontakt_emoji = config.get("kontakt_emoji", "📞")
    
    problem_button = discord.ui.Button(label="Problem", style=discord.ButtonStyle.secondary, custom_id="category_problem", emoji=problem_emoji)
    wspolpraca_button = discord.ui.Button(label="Współpraca", style=discord.ButtonStyle.secondary, custom_id="category_wspolpraca", emoji=wspolpraca_emoji)
    kontakt_button = discord.ui.Button(label="Kontakt z administracją", style=discord.ButtonStyle.secondary, custom_id="category_kontakt", emoji=kontakt_emoji)
    
    async def problem_callback(interaction):
        await show_category_form(interaction, "Problem")
    
    async def wspolpraca_callback(interaction):
        await show_category_form(interaction, "Współpraca")
    
    async def kontakt_callback(interaction):
        await show_category_form(interaction, "Kontakt z administracją")
    
    problem_button.callback = problem_callback
    wspolpraca_button.callback = wspolpraca_callback
    kontakt_button.callback = kontakt_callback
    
    view.add_item(problem_button)
    view.add_item(wspolpraca_button)
    view.add_item(kontakt_button)
    
    await channel.send(embed=embed, view=view)

async def show_category_form(interaction, category):
    """Pokazuje formularz dla wybranej kategorii"""
    modal = discord.ui.Modal(title=f"Formularz - {category}")
    
    modal.add_item(discord.ui.TextInput(
        label="Dodatkowe informacje",
        placeholder="Napisz tutaj swoją sprawę...",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    ))
    
    async def modal_callback(interaction_modal):
        await create_ticket(interaction_modal, category, modal.children[0].value)
    
    modal.on_submit = modal_callback
    await interaction.response.send_modal(modal)

async def create_ticket(interaction, category, additional_info):
    """Tworzy nowy ticket z wybraną kategorią"""
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
        category_channel = None
        if config["ticket_category"]:
            category_channel = interaction.guild.get_channel(config["ticket_category"])
        
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
        
        # Dodaj rolę która może przejmować tickety
        claim_role_id = config.get("claim_role")
        if claim_role_id:
            claim_role = interaction.guild.get_role(claim_role_id)
            if claim_role:
                for member in interaction.guild.members:
                    if claim_role in member.roles:
                        overwrites[member] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        
        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category_channel,
            overwrites=overwrites
        )
        
        ticket_id = len(tickets) + 1
        ticket_data = {
            "id": ticket_id,
            "user_id": interaction.user.id,
            "channel_id": channel.id,
            "category": category,
            "additional_info": additional_info,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "claimed_by": None
        }
        tickets.append(ticket_data)
        save_tickets(tickets)
        
        # ========== PIĘKNY EMBED TICKETU ==========
        
        user_id_str = str(interaction.user.id)
        masked_id = f"`{user_id_str}`"
        
        # Tytuł z czarną ramką
        title_text = "```\n🎫 Vireona Hub × TICKET\n```"
        
        logo_url = config.get("ticket_logo_url")
        
        embed = discord.Embed(
            description=title_text,
            color=0x5865f2
        )
        
        if logo_url:
            embed.set_thumbnail(url=logo_url)
        
        # Nick z widoczną czarną ramką
        nick_text = f"```\n{interaction.user.name}\n```"
        
        embed.add_field(
            name="**🎫 INFORMACJE O KLIENCIE:**",
            value=f"> **🔔 Ping:** {interaction.user.mention}\n> **🔔 Nick:** {nick_text}\n> **🔔 ID:** {masked_id}",
            inline=False
        )
        
        # Dodaj kategorię i dodatkowe informacje
        embed.add_field(
            name="**🎫 INFORMACJE O POMOCY:**",
            value=f"> **📌 Kategoria:** `{category}`\n> \n> **📝 Dodatkowe informacje:**\n> {additional_info}",
            inline=False
        )
        
        if config.get("ticket_footer_image"):
            embed.set_image(url=config["ticket_footer_image"])
        
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        embed.set_footer(
            text=f"{interaction.guild.name} • {current_time}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        # Przyciski
        view = discord.ui.View(timeout=None)
        
        claim_button = discord.ui.Button(label="🔧 Przejmij ticket", style=discord.ButtonStyle.secondary, custom_id="claim_ticket")
        close_button = discord.ui.Button(label="🔒 Zamknij Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
        
        async def claim_callback(interaction_claim):
            await claim_ticket(interaction_claim, channel, ticket_id)
        
        async def close_callback(interaction_close):
            await show_close_reason(interaction_close, channel, ticket_id)
        
        claim_button.callback = claim_callback
        close_button.callback = close_callback
        
        view.add_item(claim_button)
        view.add_item(close_button)
        
        # Wyślij wiadomość z pingiem i embedem razem
        await channel.send(f"||@everyone||", embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket został utworzony! {channel.mention}", ephemeral=True)
        
    finally:
        await asyncio.sleep(1)
        active_tickets_lock[user_id] = False

async def claim_ticket(interaction, channel, ticket_id):
    """Przejmuje ticket przez uprawnioną rolę"""
    config = load_config()
    claim_role_id = config.get("claim_role")
    
    if not claim_role_id:
        await interaction.response.send_message("❌ Nie ustawiono roli do przejmowania ticketów!", ephemeral=True)
        return
    
    claim_role = interaction.guild.get_role(claim_role_id)
    if not claim_role or claim_role not in interaction.user.roles:
        await interaction.response.send_message("❌ Nie masz uprawnień do przejmowania ticketów!", ephemeral=True)
        return
    
    tickets = load_tickets()
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            ticket["claimed_by"] = interaction.user.id
            break
    
    save_tickets(tickets)
    claimed_tickets[channel.id] = interaction.user.id
    
    embed = discord.Embed(
        title="🔧 Ticket przejęty",
        description=f"Ticket został przejęty przez {interaction.user.mention}",
        color=discord.Color.green()
    )
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Przejąłeś ticket!", ephemeral=True)

async def show_close_reason(interaction, channel, ticket_id):
    """Pokazuje formularz z powodem zamknięcia"""
    modal = discord.ui.Modal(title="Powód zamknięcia ticketu")
    
    modal.add_item(discord.ui.TextInput(
        label="Podaj powód zamknięcia",
        placeholder="Np. Sprawa rozwiązana, Brak odpowiedzi itp.",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=500
    ))
    
    async def modal_callback(interaction_modal):
        await close_ticket(interaction_modal, channel, ticket_id, modal.children[0].value)
    
    modal.on_submit = modal_callback
    await interaction.response.send_modal(modal)

async def close_ticket(interaction, channel, ticket_id, reason):
    """Zamyka ticket i zapisuje transkrypt"""
    
    # Wyślij wiadomość z ładowaniem
    loading_msg = await channel.send("⏳ **Zamykanie ticketu...** <a:loading:>")
    
    tickets = load_tickets()
    user_id = None
    
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            ticket["status"] = "closed"
            ticket["close_reason"] = reason
            user_id = ticket["user_id"]
            break
    
    save_tickets(tickets)
    
    # Zapisz transkrypt
    transcript_file = await save_transcript(channel, ticket_id)
    
    # Wyślij transkrypt do użytkownika (tylko raz)
    user = interaction.guild.get_member(user_id)
    if user and transcript_file:
        await send_transcript_to_user(user, transcript_file, ticket_id)
    
    embed = discord.Embed(
        title="🔒 Ticket zamknięty",
        description=f"**Powód zamknięcia:** {reason}\n\nTen ticket zostanie usunięty za 5 sekund.\nTranskrypt został wysłany na PW.",
        color=discord.Color.red()
    )
    await loading_msg.edit(content="", embed=embed)
    
    try:
        await interaction.response.send_message("✅ Ticket zostanie zamknięty.", ephemeral=True)
    except:
        pass
    
    await asyncio.sleep(5)
    await channel.delete()

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data["custom_id"] == "category_problem":
            await show_category_form(interaction, "Problem")
        elif interaction.data["custom_id"] == "category_wspolpraca":
            await show_category_form(interaction, "Współpraca")
        elif interaction.data["custom_id"] == "category_kontakt":
            await show_category_form(interaction, "Kontakt z administracją")
        elif interaction.data["custom_id"] == "claim_ticket":
            channel = interaction.channel
            tickets = load_tickets()
            for ticket in tickets:
                if ticket["channel_id"] == channel.id:
                    await claim_ticket(interaction, channel, ticket["id"])
                    break
        elif interaction.data["custom_id"] == "close_ticket":
            channel = interaction.channel
            tickets = load_tickets()
            for ticket in tickets:
                if ticket["channel_id"] == channel.id:
                    await show_close_reason(interaction, channel, ticket["id"])
                    break

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
    
    if config["ticket_panel_image"]:
        embed.add_field(name="🖼️ Obrazek panelu", value="Ustawiony", inline=False)
    else:
        embed.add_field(name="🖼️ Obrazek panelu", value="❌ Nie ustawiono", inline=False)
    
    if config["claim_role"]:
        role = ctx.guild.get_role(config["claim_role"])
        embed.add_field(name="🔧 Rola do przejmowania", value=role.mention if role else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="🔧 Rola do przejmowania", value="❌ Nie ustawiono", inline=False)
    
    embed.add_field(name="😀 Emotki przycisków", value=f"Problem: {config.get('problem_emoji', '❌')}\nWspółpraca: {config.get('wspolpraca_emoji', '🤝')}\nKontakt: {config.get('kontakt_emoji', '📞')}", inline=False)
    
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
                        value="`!setwelcomechannel #kanał` - kanał powitalny\n"
                              "`!setwelcomerole @rola` - rola dla nowych\n"
                              "`!setticketcategory ID` - kategoria ticketów\n"
                              "`!setticketpanel #kanał` - panel ticketów\n"
                              "`!setticketfooter URL` - obrazek na dole ticketu\n"
                              "`!setticketlogo URL` - logo w lewym górnym rogu\n"
                              "`!setticketpanelimage URL` - obrazek w panelu\n"
                              "`!setclaimrole @rola` - rola do przejmowania\n"
                              "`!setproblememoji 😀` - emotka Problemu\n"
                              "`!setwspolpracaemoji 😀` - emotka Współpracy\n"
                              "`!setkontaktemoji 😀` - emotka Kontaktu\n"
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
