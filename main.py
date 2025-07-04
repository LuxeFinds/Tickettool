import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, Select
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

GUILD_ID = 1389317134555025418
TEAM_CHANNEL_ID = 1389344563746832525
VOICE_CATEGORY_ID = 1389317135183909107
INVITE_LINK = "https://discord.gg/ZKexYTDG"
ALL_TEAMS_ROLE_ID = 1389348147842650112

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


class TeamCreateView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="🎫 Team erstellen", style=discord.ButtonStyle.green, custom_id="team_create"))


class DuoCheckView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="✅ Ja, Duo ist im Server", style=discord.ButtonStyle.success, custom_id="duo_in_dc"))
        self.add_item(Button(label="❌ Nein", style=discord.ButtonStyle.danger, custom_id="duo_not_in_dc"))


class DuoSelectView(View):
    def __init__(self, members):
        super().__init__(timeout=180)
        options = [
            discord.SelectOption(label=member.display_name, description=str(member), value=str(member.id))
            for member in members if not member.bot
        ]
        self.select = Select(placeholder="Wähle deinen Duo aus", options=options, min_values=1, max_values=1)
        self.select.callback = self.select_callback
        self.add_item(self.select)
        self.chosen_member = None

    async def select_callback(self, interaction: discord.Interaction):
        self.chosen_member = interaction.guild.get_member(int(self.select.values[0]))
        await interaction.response.send_modal(TeamRegisterModal(self.chosen_member))


class TeamRegisterModal(Modal, title="📝 Team Registrierung"):
    def __init__(self, duo_member):
        super().__init__()
        self.duo_member = duo_member
        self.team_name = TextInput(label="Teamname", required=True)
        self.fn_own = TextInput(label="Dein Fortnite Name", required=True)
        self.fn_duo = TextInput(label=f"Fortnite Name von {duo_member.display_name}", required=True)
        self.add_item(self.team_name)
        self.add_item(self.fn_own)
        self.add_item(self.fn_duo)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = await guild.create_role(name=self.team_name.value)
        await interaction.user.add_roles(role)
        await self.duo_member.add_roles(role)

        category = guild.get_channel(VOICE_CATEGORY_ID)
        all_teams_role = guild.get_role(ALL_TEAMS_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True),
        }

        if all_teams_role:
            overwrites[all_teams_role] = discord.PermissionOverwrite(view_channel=True)

        voice_channel = await guild.create_voice_channel(
            name=f"🔊 {self.team_name.value}",
            overwrites=overwrites,
            category=category,
            reason="Team Sprachkanal erstellt"
        )

        channel = guild.get_channel(TEAM_CHANNEL_ID)
        if channel:
            embed = discord.Embed(title="🎉 Neue Team-Anmeldung", color=discord.Color.blue())
            embed.add_field(name="📛 Teamname", value=self.team_name.value, inline=False)
            embed.add_field(name="👤 Spieler 1", value=f"{interaction.user.mention} | {self.fn_own.value}", inline=True)
            embed.add_field(name="👤 Spieler 2", value=f"{self.duo_member.mention} | {self.fn_duo.value}", inline=True)
            embed.add_field(name="🔊 Sprachkanal", value=voice_channel.mention)
            await channel.send(embed=embed)

        view = discord.ui.View()
        view.add_item(
            Button(label="Zum Sprachkanal", url=f"https://discord.com/channels/{guild.id}/{voice_channel.id}")
        )
        await interaction.response.send_message(
            f"✅ Team **{self.team_name.value}** wurde erstellt und Sprachkanal eingerichtet!",
            ephemeral=True,
            view=view,
        )


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data:
        return
    custom_id = interaction.data.get("custom_id")
    guild = bot.get_guild(GUILD_ID)
    if custom_id == "team_create":
        await interaction.response.send_message(
            "👥 Ist dein Duo im Discord-Server?", view=DuoCheckView(), ephemeral=True
        )
    elif custom_id == "duo_not_in_dc":
        await interaction.response.send_message(
            f"🔗 Lade deinen Duo bitte mit diesem Link ein:\n{INVITE_LINK}", ephemeral=True
        )
    elif custom_id == "duo_in_dc":
        members = [m for m in guild.members if not m.bot]
        await interaction.response.send_message(
            "Wähle deinen Duo aus der Liste aus:", view=DuoSelectView(members), ephemeral=True
        )


@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🎟️ Team Ticket-System",
        description="Klicke auf den Button, um ein Team zu registrieren.",
        color=discord.Color.blurple(),
    )
    file = discord.File("icon.png", filename="icon.png")
    embed.set_thumbnail(url="attachment://icon.png")
    await ctx.send(embed=embed, view=TeamCreateView(), file=file)


@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")


bot.run(TOKEN)
