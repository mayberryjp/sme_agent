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
                Button("Export Questions", id="menu_export", variant="primary"),
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
        elif event.button.id == "menu_export":
            await self.export_questions_to_json()

    async def export_questions_to_json(self):
        import sqlite3, json
        categories = ["Scoping", "Advisory", "Advisory+ARG", "Troubleshooting"]
        db_file = "questions.db"
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        for cat in categories:
            c.execute("SELECT question, SAPFullPath FROM questions WHERE category = ?", (cat,))
            rows = [row for row in c.fetchall() if row[0]]
            # Group questions by the second segment of SAPFullPath
            sap_groups = {}
            for question, sap_full_path in rows:
                sap_name = "Unknown"
                if sap_full_path:
                    parts = sap_full_path.split('/')
                    if len(parts) > 1:
                        sap_name = parts[1].strip()
                sap_groups.setdefault(sap_name, []).append(question)
            for sap_name, questions in sap_groups.items():
                data = {
                    "name": f"{sap_name} {cat} Question Answer set",
                    "questionsAndAnswers": [
                        {"question": q, "answer": ""} for q in questions
                    ]
                }
                safe_sap = sap_name.lower().replace('+','_').replace(' ','_').replace('/','_')
                filename = f"export_{safe_sap}_{cat.lower().replace('+','_').replace(' ','_')}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        conn.close()

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
