from textual.screen import Screen
from textual.widgets import Static, Button, Header, Footer, Input
from textual.containers import Container
from textual import events
from db_utils import save_config

class ConfigScreen(Screen):
    def __init__(self, initial_values=None):
        super().__init__()
        self.initial_values = initial_values or {}

    def compose(self):
        yield Header()
        yield Container(
            Static("Configuration Setup", classes="title", id="title"),
            Static("Alias:", id="alias_label"),
            Input(
                placeholder="Enter your alias",
                id="alias_input",
                value=self.initial_values.get("alias", "")
            ),
            Static("Advisory SAP:", id="advisory_label"),
            Input(
                placeholder="Advisory SAP",
                id="advisory_input",
                value=self.initial_values.get("advisory_sap", "")
            ),
            Static("Technical SAP:", id="technical_label"),
            Input(
                placeholder="Technical SAP",
                id="technical_input",
                value=self.initial_values.get("technical_sap", "")
            ),
            Static("Advisory w/ Resource Awareness SAP:", id="advisory_resource_label"),
            Input(
                placeholder="Advisory w/ Resource Awareness SAP",
                id="advisory_resource_input",
                value=self.initial_values.get("advisory_resource_sap", "")
            ),
            Button("Save", id="save_config", variant="success"),
            id="config_container"
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save_config":
            alias = self.query_one("#alias_input", Input).value
            advisory_sap = self.query_one("#advisory_input", Input).value
            technical_sap = self.query_one("#technical_input", Input).value
            advisory_resource_sap = self.query_one("#advisory_resource_input", Input).value
            save_config(alias, advisory_sap, technical_sap, advisory_resource_sap)
            from menu_screen import MenuScreen
            self.app.push_screen(MenuScreen())

    async def on_key(self, event: events.Key):
        if event.key == "ctrl+c":
            await self.action_quit()

    CSS = """
    #config_container {
        align: center middle;
        height: 100%;
        width: 100%;
    }
    #title {
        text-align: center;
        margin-bottom: 1;
    }
    #alias_label, #advisory_label, #technical_label, #advisory_resource_label {
        margin-top: 1;
        margin-bottom: 0;
    }
    Input {
        margin-bottom: 0;
        margin-top: 0;
        padding: 0 0;
    }
    Button {
        margin: 1 0;
        min-width: 8;
        padding: 0 1;
    }
    """