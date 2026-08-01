import discord
from discord.ui import View, Button


class ToolApprovalView(View):
    def __init__(self, author: discord.Member, tool_name: str, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.author = author
        self.tool_name = tool_name
        self.is_approved = None

    @discord.ui.button(label="Pode fazer, Tédio", style=discord.ButtonStyle.success, emoji="✅")
    async def btn_autorizar(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Só quem me acordou pode autorizar isso.", ephemeral=True)
            return
        self.is_approved = True
        for c in self.children:
            c.disabled = True
        await interaction.response.edit_message(
            content=f"✅ **Af, bora lá. {interaction.user.mention} me fez usar `{self.tool_name}`.**",
            embed=None, view=self
        )
        self.stop()

    @discord.ui.button(label="Deixa quieto", style=discord.ButtonStyle.danger, emoji="❌")
    async def btn_cancelar(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Só quem me acordou pode cancelar isso.", ephemeral=True)
            return
        self.is_approved = False
        for c in self.children:
            c.disabled = True
        await interaction.response.edit_message(
            content=f"❌ **Ainda bem, menos trabalho. {interaction.user.mention} cancelou `{self.tool_name}`.**",
            embed=None, view=self
        )
        self.stop()
