# embed_builder.py
import discord
from discord import Colour, Embed
from typing import List, Dict

embed_dict = {}

bank_emoji = "<:set_type_bank:1083033459339047043>"
rail_emoji = "<:set_type_rail:1083033466423222313>"
indu_emoji = "<:set_type_ind:1083033464221225020>"
trdp_emoji = "<:set_type_trd_post:1083033469392789604>"
hide_emoji = "<:set_type_hideout:1083033462405070900>"
outlaw_red = "<:outlaw_red:1084157141205659709>"
outlaw_orng = "<:outlaw_orange:1084157136323485766>"
outlaw_yell = "<:outlaw_yellow:1084157144171036762>"
outlaw_purp = "<:outlaw_purple:1084157138953318490>"
lawman_teal = "<:lawman_teal:1084157133853044746>"
lawman_pink = "<:lawman_pink:1084157131651026984>"
robber_blue = "<:robber_baron_blue:1084157145836163103>"
robber_bro = "<:robber_baron_brown:1084157148130447372>"
robber_gold = "<:robber_baron_gold:1084157150479261779>"
robber_grn = "<:robber_baron_green:1084157152895176725>"


def get_embed_dict() -> Dict[str, List[Embed]]:
    return embed_dict

def build_embeds() -> List[discord.app_commands.Choice]:
    embed_choices = []

    embed_choices.append(discord.app_commands.Choice(name="Region Control", value="001"))
    embed_dict["001"] = [region_control_embed1, region_control_embed2, region_control_embed3, region_control_embed4, region_control_embed5]

    embed_choices.append(discord.app_commands.Choice(name="Job Board", value="002"))
    embed_dict["002"] = [daily_jobs_embed]

    return embed_choices

# Region Control
region_control_embed1 = discord.Embed(title="Region: Lemoyne", description="", color=discord.Colour.blue())
region_control_embed1.add_field(name=f"    {bank_emoji} Saint Denis Bank", value=f"None", inline=False)
region_control_embed1.add_field(name=f"    {rail_emoji} Rhodes Rail Station", value=f"None", inline=False)
region_control_embed1.add_field(name=f"    {indu_emoji} Caliga Hall", value=f"{robber_blue} Robber Baron", inline=False)
region_control_embed1.add_field(name=f"    {trdp_emoji} Lagras Trading Post", value=f"None", inline=False)
region_control_embed1.add_field(name=f"    {hide_emoji} Clemens Point", value=f"{outlaw_orng} Outlaw", inline=False)
region_control_embed2 = discord.Embed(title="Region: New Hanover", description="", color=discord.Colour.green())
region_control_embed2.add_field(name=f"    {bank_emoji} Bank of Valentine", value=f"{robber_grn} Robber Baron", inline=False)
region_control_embed2.add_field(name=f"    {rail_emoji} Emerald Station", value=f"{lawman_pink} Lawman", inline=False)
region_control_embed2.add_field(name=f"    {indu_emoji} Heartland Oil Fields", value=f"None", inline=False)
region_control_embed2.add_field(name=f"    {trdp_emoji} Van Horn Trading Post", value=f"None", inline=False)
region_control_embed2.add_field(name=f"    {hide_emoji} Horseshoe Overlook", value=f"{outlaw_red} Outlaw", inline=False)
region_control_embed3 = discord.Embed(title="Region: Ambarino", description="", color=discord.Colour.yellow())
region_control_embed3.add_field(name=f"    {bank_emoji} Bank of Colter", value=f"None", inline=False)
region_control_embed3.add_field(name=f"    {rail_emoji} Bacchus Station", value=f"None", inline=False)
region_control_embed3.add_field(name=f"    {indu_emoji} Jameson Mining & Coal", value=f"None", inline=False)
region_control_embed3.add_field(name=f"    {trdp_emoji} Colter Trading Post", value=f"None", inline=False)
region_control_embed3.add_field(name=f"    {hide_emoji} Ewing Basin", value=f"None", inline=False)
region_control_embed4 = discord.Embed(title="Region: West Elizabeth", description="", color=discord.Colour.orange())
region_control_embed4.add_field(name=f"    {bank_emoji} Blackwater Bank", value=f"None", inline=False)
region_control_embed4.add_field(name=f"    {rail_emoji} Riggs Station", value=f"None", inline=False)
region_control_embed4.add_field(name=f"    {indu_emoji} Hobb's Taxidermy", value=f"{robber_gold} Robber Baron", inline=False)
region_control_embed4.add_field(name=f"    {trdp_emoji} Manzanita Post", value=f"None", inline=False)
region_control_embed4.add_field(name=f"    {hide_emoji} Chochinay", value=f"{outlaw_yell} Outlaw", inline=False)
region_control_embed5 = discord.Embed(title="Region: New Austin", description="", color=discord.Colour.brand_red())
region_control_embed5.add_field(name=f"    {bank_emoji} Bank of Armadillo", value=f"None", inline=False)
region_control_embed5.add_field(name=f"    {rail_emoji} Mercer Rail Station", value=f"None", inline=False)
region_control_embed5.add_field(name=f"    {indu_emoji} MacFarlane's Ranch", value=f"None", inline=False)
region_control_embed5.add_field(name=f"    {trdp_emoji} Tumbleweed Trading Post", value=f"None", inline=False)
region_control_embed5.add_field(name=f"    {hide_emoji} Rathskeller Fork", value=f"None", inline=False)

# Daily Jobs
daily_jobs_embed = discord.Embed(title="", description="", color=discord.Colour.blue())
daily_jobs_embed.add_field(name="", value="")
daily_jobs_embed.add_field(name="", value="")
