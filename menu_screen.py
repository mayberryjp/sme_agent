from textual.screen import Screen
from textual.widgets import Static, Button, Header, Footer
from textual.containers import Container, Horizontal
from textual import events
from db_utils import get_config_values, get_uncategorized_questions_from_db

class MenuScreen(Screen):
    def compose(self):
        yield Header()
        yield Container(
            Static("Main Menu", classes="title", id="menu_title"),
            Horizontal(
                Button("Configuration", id="menu_config", variant="primary"),
                Button("Import Questions From CSV", id="menu_import", variant="primary"),
                Button("Screen Questions", id="menu_questions", variant="primary"),
                Button("Get Questions From ZebraAI", id="menu_get_questions", variant="primary"),
                id="menu_buttons"
            ),
            id="menu_container"
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "menu_config":
            from config_screen import ConfigScreen
            config_values = get_config_values()
            self.app.push_screen(ConfigScreen(initial_values=config_values))
        elif event.button.id == "menu_import":
            from csv_import_screen import CsvImportScreen
            self.app.push_screen(CsvImportScreen())
        elif event.button.id == "menu_questions":
            from question_categorizer_screen import QuestionCategorizerScreen
            uncategorized = get_uncategorized_questions_from_db()
            self.app.push_screen(QuestionCategorizerScreen(uncategorized))
        elif event.button.id == "menu_get_questions":
            from get_questions_screen import GetQuestionsScreen
            self.app.push_screen(GetQuestionsScreen())

    async def on_key(self, event: events.Key):
        if event.key == "ctrl+c":
            await self.action_quit()

    CSS = """
    #menu_container {
        align: center middle;
        height: 100%;
        width: 100%;
    }
    #menu_title {
        text-align: center;
        margin-bottom: 2;
    }
    #menu_buttons {
        align: center middle;
        margin-top: 2;
    }
    Button {
        margin: 0 2;
        min-width: 16;
        padding: 0 2;
    }
    """