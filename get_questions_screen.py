from textual.screen import Screen
from textual.widgets import Static, Button, Header, Footer, Select, Input
from textual.containers import Container, Horizontal
from textual import events
from db_utils import get_saps_from_config, import_questions_list_to_db
from auth_mi import run_zebra_ai_client

class GetQuestionsScreen(Screen):
    def compose(self):
        saps = get_saps_from_config()
        yield Header()
        yield Container(
            Static("[bold yellow]Make sure you are on VPN[/bold yellow]", id="vpn_banner"),  # VPN banner
            Static("[red]Warning: This operation may take a long time, especially if you select a large number of cases.[/red]", id="long_op_warning"),
            Static("Get Questions by SAP", classes="title", id="get_questions_title"),
            Static("Select SAP:", id="sap_label"),
            Select(
                options=[
                    (f"Advisory SAP: {saps.get('advisory_sap', '')}", saps.get("advisory_sap", "")),
                    (f"Technical SAP: {saps.get('technical_sap', '')}", saps.get("technical_sap", "")),
                    (f"Advisory w/ Resource Awareness SAP: {saps.get('advisory_resource_sap', '')}", saps.get("advisory_resource_sap", ""))
                ],
                prompt="Choose SAP",
                id="sap_select"
            ),
            Static("Number of Cases:", id="cases_label"),
            Input(placeholder="Enter number of cases", id="cases_input", value="10"),
            Horizontal(
                Button("Get Questions", id="get_questions_btn", variant="success"),
                Button("Back to Menu", id="back_to_menu", variant="primary"),
                id="get_questions_buttons"
            ),
            Static("", id="questions_output"),
            id="get_questions_container"
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "back_to_menu":
            from menu_screen import MenuScreen
            self.app.push_screen(MenuScreen())
        elif event.button.id == "get_questions_btn":
            sap_full_path = self.query_one("#sap_select", Select).value
            cases_input = self.query_one("#cases_input", Input).value
            try:
                number_of_cases = int(cases_input)
            except ValueError:
                number_of_cases = 10
            questions_output = self.query_one("#questions_output", Static)
            # Show working banner
            questions_output.update("[yellow]Working... this may take awhile.[/yellow]")
            self.refresh()
            try:
                # Get questions from ZebraAI
                questions = run_zebra_ai_client(sap_full_path=sap_full_path, number_of_cases=number_of_cases)
                if questions:
                    # Import questions into the database, avoiding duplicates
                    import_questions_list_to_db(questions, sap_full_path)
                    questions_output.update(f"[green]{len(questions)} questions extracted and imported into the database.[/green]")
                else:
                    questions_output.update("[red]No questions found or error occurred.[/red]")
            except Exception as e:
                questions_output.update(f"[red]Error: {str(e)}[/red]")

    async def on_key(self, event: events.Key):
        if event.key == "ctrl+c":
            self.app.exit()

    CSS = """
    #get_questions_container {
        align: center middle;
        height: 100%;
        width: 100%;
    }
    #vpn_banner {
        text-align: center;
        margin-bottom: 1;
        color: yellow;
    }
    #long_op_warning {
        text-align: center;
        margin-bottom: 1;
        color: red;
    }
    #get_questions_title {
        text-align: center;
        margin-bottom: 1;
    }
    #sap_label, #cases_label {
        margin-top: 1;
        margin-bottom: 0;
    }
    #get_questions_buttons {
        align: center middle;
        margin-top: 1;
    }
    Select, Input {
        margin-bottom: 1;
        width: 100%;
    }
    Button {
        margin: 0 1;
        min-width: 10;
        padding: 0 1;
    }
    #questions_output {
        margin-top: 2;
    }
    """