from textual.screen import Screen
from textual.widgets import Static, Button, Header, Footer, Select, Input
from textual.containers import Container, Horizontal
from textual import events
from db_utils import get_saps_from_config, import_questions_list_to_db
from auth_mi import run_zebra_ai_client

class GetQuestionsScreen(Screen):
    def update_sap_dropdown(self):
        from db_utils import get_saps_from_config, count_questions_for_sap
        saps = get_saps_from_config()
        sap_options = []
        advisory_sap = saps.get('advisory_sap', '')
        technical_sap = saps.get('technical_sap', '')
        advisory_resource_sap = saps.get('advisory_resource_sap', '')
        if advisory_sap:
            count = count_questions_for_sap(advisory_sap)
            sap_options.append((f"Advisory SAP: {advisory_sap} ({count} entries)", advisory_sap))
        if technical_sap:
            count = count_questions_for_sap(technical_sap)
            sap_options.append((f"Technical SAP: {technical_sap} ({count} entries)", technical_sap))
        if advisory_resource_sap:
            count = count_questions_for_sap(advisory_resource_sap)
            sap_options.append((f"Advisory w/ Resource Awareness SAP: {advisory_resource_sap} ({count} entries)", advisory_resource_sap))
        sap_select = self.query_one("#sap_select", Select)
        sap_select.options = sap_options
        # Optionally, keep the current selection if possible
        if sap_select.value not in [v for _, v in sap_options]:
            sap_select.value = sap_options[0][1] if sap_options else None

    def compose(self):
        saps = get_saps_from_config()
        from db_utils import count_questions_for_sap
        # Prepare SAP options with counts
        sap_options = []
        advisory_sap = saps.get('advisory_sap', '')
        technical_sap = saps.get('technical_sap', '')
        advisory_resource_sap = saps.get('advisory_resource_sap', '')
        if advisory_sap:
            count = count_questions_for_sap(advisory_sap)
            sap_options.append((f"Advisory SAP: {advisory_sap} ({count} entries)", advisory_sap))
        if technical_sap:
            count = count_questions_for_sap(technical_sap)
            sap_options.append((f"Technical SAP: {technical_sap} ({count} entries)", technical_sap))
        if advisory_resource_sap:
            count = count_questions_for_sap(advisory_resource_sap)
            sap_options.append((f"Advisory w/ Resource Awareness SAP: {advisory_resource_sap} ({count} entries)", advisory_resource_sap))

        yield Header()
        yield Container(
            Static("[bold yellow]Make sure you are on VPN[/bold yellow]", id="vpn_banner"),  # VPN banner
            Static("[red]Warning: This operation may take a long time, especially if you select a large number of cases.[/red]", id="long_op_warning"),
            Static("Get Questions by SAP", classes="title", id="get_questions_title"),
            Static("Select SAP:", id="sap_label"),
            Select(
                options=sap_options,
                prompt="Choose SAP",
                id="sap_select"
            ),
            Static("Number of Cases:", id="cases_label"),
            Input(placeholder="Enter number of cases", id="cases_input", value="10"),
            Horizontal(
                Button("Get Questions", id="get_questions_btn", variant="success"),
                Button("Delete Questions for this SAP", id="delete_questions_btn", variant="error"),
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
            self.update_sap_dropdown()
        elif event.button.id == "delete_questions_btn":
            sap_full_path = self.query_one("#sap_select", Select).value
            questions_output = self.query_one("#questions_output", Static)
            if not sap_full_path:
                questions_output.update("[red]Please select a SAP to delete questions for.[/red]")
                return
            try:
                from db_utils import delete_questions_for_sap
            except ImportError:
                questions_output.update("[red]Delete function not implemented in db_utils.py.[/red]")
                return
            try:
                deleted_count = delete_questions_for_sap(sap_full_path)
                questions_output.update(f"[red]{deleted_count} questions deleted for this SAP.[/red]")
            except Exception as e:
                questions_output.update(f"[red]Error deleting questions: {str(e)}[/red]")
            self.update_sap_dropdown()

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
    #delete_questions_btn {
        background: #b71c1c;
        color: white;
        border: solid #b71c1c;
    }
    #questions_output {
        margin-top: 2;
    }
    """
