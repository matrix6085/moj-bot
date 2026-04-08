import discord
from discord.ext import commands
import os
import json
from datetime import datetime
import asyncio

# --------------------- TOKEN ---------------------
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --------------------- PLIKI KONFIGURACYJNE ---------------------
CONFIG_FILE = "config.json"
TICKETS_FILE = "tickets.json"
TRANSCRIPTS_FOLDER = "transcripts"

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
            "welcome_image": None,
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

# --------------------- FUNKCJE POMOCNICZE ---------------------
async def save_transcript(channel, ticket_id):
    messages = []
    async for message in channel.history(limit=None, oldest_first=True):
        messages.append(message)
    if not messages:
        return None
    lines = [f"=== TRANSCRIPT TICKETU {ticket_id} ===",
             f"Kanał: #{channel.name}",
             f"Data utworzenia: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
             "="*50, ""]
    for msg in messages:
        timestamp = msg.created_at.strftime("%H:%M:%S")
        author = msg.author.name
        content = msg.content if msg.content else "[EMBED/ZAŁĄCZNIK]"
        lines.append(f"[{timestamp}] {author}: {content}")
        if msg.attachments:
            for att in msg.attachments:
                lines.append(f"  → Załącznik: {att.url}")
    lines.extend(["", "="*50, f"Koniec transkryptu - {len(messages)} wiadomości"])
    filename = f"{TRANSCRIPTS_FOLDER}/ticket_{ticket_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return filename

async def send_transcript_to_user(user, filename, ticket_id):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > 1900:
            await user.send(f"📋 **Transkrypt ticketu #{ticket_id}**")
            await user.send(file=discord.File(filename))
        else:
            embed = discord.Embed(title=f"📋 Transkrypt ticketu #{ticket_id}", description=f"```\n{content[:1800]}\n```", color=discord.Color.blue())
            await user.send(embed=embed)
        return True
    except:
        return False

# --------------------- ZDARZENIE POWITANIA ---------------------
@bot.event
async def on_member_join(member):
    config = load_config()
    # Nadanie roli
    if config.get("welcome_role"):
        role = member.guild.get_role(config["welcome_role"])
        if role:
            try:
                await member.add_roles(role)
            except:
                pass
    # Kanał powitalny
    channel_id = config.get("welcome_channel")
    if not channel_id:
        return
    channel = bot.get_channel(channel_id)
    if not channel:
        return
    member_count = member.guild.member_count
    embed = discord.Embed(
        title="✨ **Nowy Użytkownik!** ✨",
        description=(
            f"Witamy na serwerze **{member.guild.name}**! 🎉\n"
            f"Cieszymy się, że z nami jesteś. Mamy nadzieję, że zostaniesz z nami na dłużej!\n"
            f"Pamiętaj, aby zapoznać się z kanałami.\n\n"
            f"**Jesteś naszym {member_count}. użytkownikiem.**"
        ),
        color=0x5865f2
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    if config.get("welcome_image"):
        embed.set_image(url=config["welcome_image"])
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    embed.set_footer(
        text=f"{member.guild.name} • {current_time}",
        icon_url=member.guild.icon.url if member.guild.icon else None
    )
    await channel.send(f"{member.mention} 👋")
    await channel.send(embed=embed)

# --------------------- KOMENDY KONFIGURACYJNE ---------------------
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
async def setwelcomeimage(ctx, url: str = None):
    config = load_config()
    config["welcome_image"] = url
    save_config(config)
    await ctx.send(f"✅ Ustawiono obrazek powitania" if url else "✅ Usunięto obrazek powitania")
    await ctx.message.delete()

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
    config = load_config()
    config["ticket_panel_image"] = url
    save_config(config)
    await ctx.send(f"✅ Ustawiono obrazek panelu ticketów" if url else "✅ Usunięto obrazek panelu ticketów")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setproblememoji(ctx, emoji: str):
    config = load_config()
    config["problem_emoji"] = emoji
    save_config(config)
    await ctx.send(f"✅ Ustawiono emotkę dla Problemu: {emoji}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setwspolpracaemoji(ctx, emoji: str):
    config = load_config()
    config["wspolpraca_emoji"] = emoji
    save_config(config)
    await ctx.send(f"✅ Ustawiono emotkę dla Współpracy: {emoji}")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setkontaktemoji(ctx, emoji: str):
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

@bot.command()
@commands.has_permissions(administrator=True)
async def showconfig(ctx):
    config = load_config()
    embed = discord.Embed(title="⚙️ Konfiguracja serwera", color=discord.Color.blue())
    if config.get("welcome_channel"):
        ch = bot.get_channel(config["welcome_channel"])
        embed.add_field(name="📢 Kanał powitalny", value=ch.mention if ch else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="📢 Kanał powitalny", value="❌ Nie ustawiono", inline=False)
    if config.get("welcome_role"):
        r = ctx.guild.get_role(config["welcome_role"])
        embed.add_field(name="🎭 Rola dla nowych", value=r.mention if r else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="🎭 Rola dla nowych", value="❌ Nie ustawiono", inline=False)
    if config.get("ticket_category"):
        cat = ctx.guild.get_channel(config["ticket_category"])
        embed.add_field(name="🎫 Kategoria ticketów", value=cat.name if cat else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="🎫 Kategoria ticketów", value="❌ Nie ustawiono", inline=False)
    if config.get("ticket_panel_channel"):
        ch = bot.get_channel(config["ticket_panel_channel"])
        embed.add_field(name="📋 Kanał panelu ticketów", value=ch.mention if ch else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="📋 Kanał panelu ticketów", value="❌ Nie ustawiono", inline=False)
    embed.add_field(name="🖼️ Obrazek ticketu", value="Ustawiony" if config.get("ticket_footer_image") else "❌ Nie ustawiono", inline=False)
    embed.add_field(name="🖼️ Logo ticketu", value="Ustawione" if config.get("ticket_logo_url") else "❌ Nie ustawiono", inline=False)
    embed.add_field(name="🖼️ Obrazek panelu", value="Ustawiony" if config.get("ticket_panel_image") else "❌ Nie ustawiono", inline=False)
    if config.get("claim_role"):
        r = ctx.guild.get_role(config["claim_role"])
        embed.add_field(name="🔧 Rola do przejmowania", value=r.mention if r else "Nie znaleziono", inline=False)
    else:
        embed.add_field(name="🔧 Rola do przejmowania", value="❌ Nie ustawiono", inline=False)
    embed.add_field(name="😀 Emotki przycisków", value=f"Problem: {config.get('problem_emoji', '❌')}\nWspółpraca: {config.get('wspolpraca_emoji', '🤝')}\nKontakt: {config.get('kontakt_emoji', '📞')}", inline=False)
    await ctx.send(embed=embed)
    await ctx.message.delete()

# --------------------- PANEL I TICKETY ---------------------
active_tickets_lock = {}
claimed_tickets = {}

async def send_ticket_panel(channel):
    config = load_config()
    embed = discord.Embed(
        title="**KONTAKT Z ADMINISTRACJĄ**",
        description="**Aby skontaktować się z Administracją, wybierz odpowiednią kategorię, z podanych poniżej, Twój bilet automatycznie zostanie dostarczony do osób zajmujących się Twoją sprawą.**",
        color=0x5865f2
    )
    if config.get("ticket_panel_image"):
        embed.set_image(url=config["ticket_panel_image"])
    embed.set_footer(text="Pingowanie Administracji równe jest z przerwą 7 dni na discordzie.")
    view = discord.ui.View(timeout=None)
    problem_btn = discord.ui.Button(label="Problem", style=discord.ButtonStyle.secondary, custom_id="category_problem", emoji=config.get("problem_emoji", "❌"))
    wspolpraca_btn = discord.ui.Button(label="Współpraca", style=discord.ButtonStyle.secondary, custom_id="category_wspolpraca", emoji=config.get("wspolpraca_emoji", "🤝"))
    kontakt_btn = discord.ui.Button(label="Kontakt z administracją", style=discord.ButtonStyle.secondary, custom_id="category_kontakt", emoji=config.get("kontakt_emoji", "📞"))
    async def problem_cb(interaction):
        await show_category_form(interaction, "Problem")
    async def wspolpraca_cb(interaction):
        await show_category_form(interaction, "Współpraca")
    async def kontakt_cb(interaction):
        await show_category_form(interaction, "Kontakt z administracją")
    problem_btn.callback = problem_cb
    wspolpraca_btn.callback = wspolpraca_cb
    kontakt_btn.callback = kontakt_cb
    view.add_item(problem_btn)
    view.add_item(wspolpraca_btn)
    view.add_item(kontakt_btn)
    await channel.send(embed=embed, view=view)

async def show_category_form(interaction, category):
    modal = discord.ui.Modal(title=f"Formularz - {category}")
    modal.add_item(discord.ui.TextInput(
        label="Dodatkowe informacje",
        placeholder="Napisz tutaj swoją sprawę...",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    ))
    async def modal_cb(modal_interaction):
        await create_ticket(modal_interaction, category, modal.children[0].value)
    modal.on_submit = modal_cb
    await interaction.response.send_modal(modal)

async def create_ticket(interaction, category, additional_info):
    user_id = interaction.user.id
    if user_id in active_tickets_lock and active_tickets_lock[user_id]:
        await interaction.response.send_message("⏳ Twój ticket jest już w trakcie tworzenia!", ephemeral=True)
        return
    active_tickets_lock[user_id] = True
    try:
        config = load_config()
        tickets = load_tickets()
        for t in tickets:
            if t["user_id"] == user_id and t["status"] == "open":
                ch = interaction.guild.get_channel(t["channel_id"])
                await interaction.response.send_message(f"❌ Masz już otwarty ticket! {ch.mention if ch else ''}", ephemeral=True)
                return
        category_channel = None
        if config.get("ticket_category"):
            category_channel = interaction.guild.get_channel(config["ticket_category"])
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }
        for member in interaction.guild.members:
            if member.guild_permissions.administrator:
                overwrites[member] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
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
            "user_id": user_id,
            "channel_id": channel.id,
            "category": category,
            "additional_info": additional_info,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "claimed_by": None
        }
        tickets.append(ticket_data)
        save_tickets(tickets)
        # Embed ticketu
        title_text = "```\n🎫 Vireona Hub × TICKET\n```"
        embed = discord.Embed(description=title_text, color=0x5865f2)
        if config.get("ticket_logo_url"):
            embed.set_thumbnail(url=config["ticket_logo_url"])
        nick_ramka = f"`{interaction.user.name}`"
        embed.add_field(
            name="**🎫 INFORMACJE O KLIENCIE:**",
            value=f"> **🔔 Ping:** {interaction.user.mention}\n> **🔔 Nick:** {nick_ramka}\n> **🔔 ID:** `{interaction.user.id}`",
            inline=False
        )
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
        view = discord.ui.View(timeout=None)
        claim_btn = discord.ui.Button(label="🔧 Przejmij ticket", style=discord.ButtonStyle.secondary, custom_id="claim_ticket")
        close_btn = discord.ui.Button(label="🔒 Zamknij Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
        async def claim_cb(interaction_claim):
            await claim_ticket(interaction_claim, channel, ticket_id)
        async def close_cb(interaction_close):
            await show_close_reason(interaction_close, channel, ticket_id)
        claim_btn.callback = claim_cb
        close_btn.callback = close_cb
        view.add_item(claim_btn)
        view.add_item(close_btn)
        await channel.send(f"||@everyone||", embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket został utworzony! {channel.mention}", ephemeral=True)
    finally:
        await asyncio.sleep(1)
        active_tickets_lock[user_id] = False

async def claim_ticket(interaction, channel, ticket_id):
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
    for t in tickets:
        if t["id"] == ticket_id:
            t["claimed_by"] = interaction.user.id
            break
    save_tickets(tickets)
    claimed_tickets[channel.id] = interaction.user.id
    embed = discord.Embed(title="🔧 Ticket przejęty", description=f"Ticket został przejęty przez {interaction.user.mention}", color=discord.Color.green())
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Przejąłeś ticket!", ephemeral=True)

async def show_close_reason(interaction, channel, ticket_id):
    modal = discord.ui.Modal(title="Powód zamknięcia ticketu")
    modal.add_item(discord.ui.TextInput(
        label="Podaj powód zamknięcia",
        placeholder="Np. Sprawa rozwiązana, Brak odpowiedzi itp.",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=500
    ))
    async def modal_cb(modal_interaction):
        await close_ticket(modal_interaction, channel, ticket_id, modal.children[0].value)
    modal.on_submit = modal_cb
    await interaction.response.send_modal(modal)

async def close_ticket(interaction, channel, ticket_id, reason):
    loading_msg = await channel.send("⏳ **Zamykanie ticketu...** <a:loading:>")
    tickets = load_tickets()
    user_id = None
    for t in tickets:
        if t["id"] == ticket_id:
            t["status"] = "closed"
            t["close_reason"] = reason
            user_id = t["user_id"]
            break
    save_tickets(tickets)
    transcript_file = await save_transcript(channel, ticket_id)
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
        custom_id = interaction.data["custom_id"]
        if custom_id == "category_problem":
            await show_category_form(interaction, "Problem")
        elif custom_id == "category_wspolpraca":
            await show_category_form(interaction, "Współpraca")
        elif custom_id == "category_kontakt":
            await show_category_form(interaction, "Kontakt z administracją")
        elif custom_id == "claim_ticket":
            channel = interaction.channel
            tickets = load_tickets()
            for t in tickets:
                if t["channel_id"] == channel.id:
                    await claim_ticket(interaction, channel, t["id"])
                    break
        elif custom_id == "close_ticket":
            channel = interaction.channel
            tickets = load_tickets()
            for t in tickets:
                if t["channel_id"] == channel.id:
                    await show_close_reason(interaction, channel, t["id"])
                    break

# --------------------- PODSTAWOWE KOMENDY ---------------------
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

@bot.command()
async def helpme(ctx):
    embed = discord.Embed(title="🤖 Pomoc - dostępne komendy", color=discord.Color.blue())
    embed.add_field(name="📌 Podstawowe", value="`!ping`, `!hello`, `!helpme`", inline=False)
    if ctx.author.guild_permissions.administrator:
        embed.add_field(name="⚙️ Konfiguracja (admin)", 
                        value="`!setwelcomechannel #kanał`\n`!setwelcomerole @rola`\n`!setwelcomeimage URL`\n`!setticketcategory ID`\n`!setticketpanel #kanał`\n`!setticketfooter URL`\n`!setticketlogo URL`\n`!setticketpanelimage URL`\n`!setclaimrole @rola`\n`!setproblememoji 😀`\n`!setwspolpracaemoji 😀`\n`!setkontaktemoji 😀`\n`!showconfig`", inline=False)
    await ctx.send(embed=embed)

# --------------------- START ---------------------
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ BŁĄD: Nieprawidłowy token!")
    except Exception as e:
        print(f"❌ BŁĄD: {e}")
