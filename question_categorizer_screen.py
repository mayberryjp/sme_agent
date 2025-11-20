from textual.screen import Screen
from textual.widgets import Static, Button, Header, Footer
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual import events
from db_utils import CATEGORIES, save_to_db
import datetime

class QuestionCategorizerScreen(Screen):
    question_index = reactive(0)

    def __init__(self, questions):
        super().__init__()
        self.questions = questions

    def compose(self):
        yield Header()
        yield Container(
            Static("Question Categorizer", classes="title", id="title"),
            Static("", id="sap"),
            Static("", id="question"),
            Horizontal(
                *[Button(cat, id=f"cat_{i}", variant="primary") for i, cat in enumerate(CATEGORIES)],
                id="category_buttons"
            ),
            Horizontal(
                Button("Go Back", id="go_back", variant="warning"),
                Button("Menu", id="menu", variant="primary"),
                id="nav_buttons"
            ),
            id="main_container"
        )
        yield Footer()

    def on_mount(self):
        self.update_question()

    def update_question(self):
        question_obj = self.questions[self.question_index] if self.question_index < len(self.questions) else None
        sap_widget = self.query_one("#sap", Static)
        question_widget = self.query_one("#question", Static)
        if question_obj:
            sap_text = question_obj.get("sap", "")
            sap_widget.update(f"[bold light_steel_blue]SAP: {sap_text}[/bold light_steel_blue]")
            question_widget.update(f"[bold light_steel_blue]{question_obj['question']}[/bold light_steel_blue]\n")
        else:
            sap_widget.update("")
            question_widget.update(
                "\n\n[bold magenta]All questions done! Please press the menu button and add more questions[/bold magenta]\n"
            )
        for i, cat in enumerate(CATEGORIES):
            btn = self.query_one(f"#cat_{i}", Button)
            btn.disabled = question_obj is None

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "go_back":
            if self.question_index > 0:
                self.question_index -= 1
                self.update_question()
            return
        if event.button.id == "menu":
            from menu_screen import MenuScreen
            self.app.push_screen(MenuScreen())
            return
        if self.question_index >= len(self.questions):
            return
        category = str(event.button.label)
        question_obj = self.questions[self.question_index]
        guid = question_obj["guid"]
        question = question_obj["question"]
        timestamp = datetime.datetime.now().isoformat()
        row = [guid, question, category, "", "", "", "", "", timestamp]
        save_to_db(row)
        self.question_index += 1
        self.update_question()

    async def on_key(self, event: events.Key):
        if event.key == "ctrl+c":
            await self.app.action_quit()

    CSS = """
    #main_container {
        align: center middle;
        height: 100%;
        width: 100%;
    }
    #title {
        text-align: center;
        margin-bottom: 2;
    }
    #question {
        text-align: center;
        margin: 4 0 4 0;
        height: 7;
        width: 80%;
    }
    #category_buttons {
        align: center middle;
        margin-top: 2;
    }
    #nav_buttons {
        align: center middle;
        margin-top: 2;
    }
    Button {
        margin: 0 1;
        min-width: 10;
        padding: 0 1;
    }
    Button#go_back {
        color: yellow;
        border: solid yellow;
    }
    """