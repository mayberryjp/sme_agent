from textual.screen import Screen
from textual.widgets import Static, Button, Header, Footer, Select
from textual.containers import Container, Horizontal
from textual import events
from pathlib import Path
from db_utils import get_saps_from_config, import_questions_to_db_with_sap, get_uncategorized_questions_from_db

class CsvImportScreen(Screen):
    def compose(self):
        csv_files = [f for f in Path('.').glob('*.csv')]
        saps = get_saps_from_config()
        yield Header()
        yield Container(
            Static("CSV Import", classes="title", id="csv_import_title"),
            Static(
                "If you want to stop being asked to import CSV files, then remove CSV files from the project directory.",
                id="csv_info",
            ),
            Static("Select a CSV file to import questions:", id="csv_label"),
            Select(
                options=[(f.name, f.name) for f in csv_files],
                prompt="Choose CSV file",
                id="csv_select"
            ),
            Static("Select SAP to associate with these questions:", id="sap_label"),
            Select(
                options=[
                    (f"Advisory SAP: {saps.get('advisory_sap', '')}", saps.get("advisory_sap", "")),
                    (f"Technical SAP: {saps.get('technical_sap', '')}", saps.get("technical_sap", "")),
                    (f"Advisory w/ Resource Awareness SAP: {saps.get('advisory_resource_sap', '')}", saps.get("advisory_resource_sap", ""))
                ],
                prompt="Choose SAP",
                id="sap_select"
            ),
            Horizontal(
                Button("Import", id="import_btn", variant="success", disabled=not bool(csv_files)),
                Button("Back to Menu", id="back_to_menu", variant="primary"),
                id="csv_import_buttons"
            ),
            id="csv_import_container"
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "back_to_menu":
            from menu_screen import MenuScreen
            self.app.push_screen(MenuScreen())
        elif event.button.id == "import_btn":
            csv_filename = self.query_one("#csv_select", Select).value
            sap_full_path = self.query_one("#sap_select", Select).value
            if csv_filename and sap_full_path:
                import_questions_to_db_with_sap(csv_filename, sap_full_path)
            from question_categorizer_screen import QuestionCategorizerScreen
            uncategorized = get_uncategorized_questions_from_db()
            self.app.push_screen(QuestionCategorizerScreen(uncategorized))

    async def on_key(self, event: events.Key):
        if event.key == "ctrl+c":
            await self.action_quit()

    CSS = """
    #csv_import_container {
        align: center middle;
        height: 100%;
        width: 100%;
    }
    #csv_import_title {
        text-align: center;
        margin-bottom: 1;
    }
    #csv_info, #csv_label, #sap_label {
        margin-top: 1;
        margin-bottom: 0;
    }
    #csv_import_buttons {
        align: center middle;
        margin-top: 1;
    }
    Select {
        margin-bottom: 1;
        width: 100%;
    }
    Button {
        margin: 0 1;
        min-width: 10;
        padding: 0 1;
    }
    """