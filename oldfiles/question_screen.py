import csv
import sqlite3
import datetime
import uuid
from pathlib import Path
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Header, Footer, Input, Select
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual import events


DB_FILE = "questions.db"

CATEGORIES = [
    "Scoping",
    "Advisory",
    "Advisory+ARG",
    "Troubleshooting",
    "Skip",
    "Case Handling",
    "Another Product",
    "N/A"
]

DB_COLUMNS = [
    "guid",
    "question",
    "category",
    "aI_response",
    "evaluation_text",
    "extra_column1",
    "extra_column2",
    "extra_column3",
    "timestamp"
]

# --- Initialize the database ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guid TEXT UNIQUE,
            question TEXT,
            category TEXT,
            aI_response TEXT,
            evaluation_text TEXT,
            extra_column1 TEXT,
            extra_column2 TEXT,
            extra_column3 TEXT,
            SAPFullPath TEXT,
            timestamp TEXT
        )
    """)
    # Add SAPFullPath column if it doesn't exist
    c.execute("PRAGMA table_info(questions)")
    columns = [col[1] for col in c.fetchall()]
    if "SAPFullPath" not in columns:
        c.execute("ALTER TABLE questions ADD COLUMN SAPFullPath TEXT")
    conn.commit()
    conn.close()

# --- Get GUIDs of categorized questions ---
def get_categorized_guids():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT guid FROM questions WHERE category IS NOT NULL AND category != ''")
    rows = c.fetchall()
    conn.close()
    return set(row[0] for row in rows)

# --- Save a row of data to the database ---
def save_to_db(row):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Update the row where guid matches
    c.execute("""
        UPDATE questions
        SET category = ?, aI_response = ?, evaluation_text = ?, extra_column1 = ?, extra_column2 = ?, extra_column3 = ?, timestamp = ?
        WHERE guid = ?
    """, (row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[0]))
    conn.commit()
    conn.close()

# --- Read questions from a CSV file ---
def read_questions(csv_file):
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        return [row[0] for row in reader if row and row[0].strip()]

# --- Import questions from a CSV file to the database ---
def import_questions_to_db(csv_file):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            question = row[0].strip()
            if not question:
                continue
            # Check if question already exists
            c.execute("SELECT guid FROM questions WHERE question = ?", (question,))
            result = c.fetchone()
            if not result:
                guid = str(uuid.uuid4())
                c.execute(
                    "INSERT INTO questions (guid, question, category, aI_response, evaluation_text, extra_column1, extra_column2, extra_column3, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (guid, question, '', '', '', '', '', '', '')
                )
    conn.commit()
    conn.close()

# --- Get uncategorized questions from the database ---
def get_uncategorized_questions_from_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT guid, question, SAPFullPath FROM questions WHERE category IS NULL OR category = ''")
    rows = c.fetchall()
    conn.close()
    return [{"guid": row[0], "question": row[1], "sap": row[2]} for row in rows]

# --- Initialize the configuration database ---
def init_config_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS configuration (
            key TEXT PRIMARY KEY,
            value TEXT,
            last_updated TEXT
        )
    """)
    conn.commit()
    conn.close()

# --- Check if configuration exists ---
def config_exists():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM configuration")
    count = c.fetchone()[0]
    conn.close()
    return count > 0

# --- Save configuration to the database ---
def save_config(alias, advisory_sap, technical_sap, advisory_resource_sap):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    c.execute("INSERT OR REPLACE INTO configuration (key, value, last_updated) VALUES (?, ?, ?)", ("alias", alias, now))
    c.execute("INSERT OR REPLACE INTO configuration (key, value, last_updated) VALUES (?, ?, ?)", ("advisory_sap", advisory_sap, now))
    c.execute("INSERT OR REPLACE INTO configuration (key, value, last_updated) VALUES (?, ?, ?)", ("technical_sap", technical_sap, now))
    c.execute("INSERT OR REPLACE INTO configuration (key, value, last_updated) VALUES (?, ?, ?)", ("advisory_resource_sap", advisory_resource_sap, now))
    conn.commit()
    conn.close()

# --- Get SAPs from configuration table ---
def get_saps_from_config():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key, value FROM configuration WHERE key IN ('advisory_sap', 'technical_sap', 'advisory_resource_sap')")
    saps = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return saps

# --- Get all configuration values ---
def get_config_values():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key, value FROM configuration")
    values = dict(c.fetchall())
    conn.close()
    return values

# --- Configuration screen ---
class ConfigScreen(Screen):
    def __init__(self, initial_values=None):
        super().__init__()
        self.initial_values = initial_values or {}

    def compose(self) -> ComposeResult:
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
            self.app.push_screen(MenuScreen())  # Go to menu after saving

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

# --- Question Categorizer Screen ---
class QuestionCategorizerScreen(Screen):
    question_index = reactive(0)

    def __init__(self, questions):
        super().__init__()
        self.questions = questions

    def compose(self) -> ComposeResult:
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
            question_widget.update("\n\n[bold magenta]All questions done![/bold magenta]\n")
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

# --- Menu Screen ---
class MenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Main Menu", classes="title", id="menu_title"),
            Horizontal(
                Button("Configuration", id="menu_config", variant="primary"),
                Button("Import CSV", id="menu_import", variant="primary"),
                Button("Questions", id="menu_questions", variant="primary"),
                id="menu_buttons"
            ),
            id="menu_container"
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "menu_config":
            config_values = get_config_values()
            self.app.push_screen(ConfigScreen(initial_values=config_values))
        elif event.button.id == "menu_import":
            self.app.push_screen(CsvImportScreen())  # <-- Always show import screen!
        elif event.button.id == "menu_questions":
            uncategorized = get_uncategorized_questions_from_db()
            self.app.push_screen(QuestionCategorizerScreen(uncategorized))

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

# --- CSV Import Screen ---
class CsvImportScreen(Screen):
    def compose(self) -> ComposeResult:
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
                Button("Import", id="import_btn", variant="success", disabled=not bool(csv_files)),  # Disable if no CSVs
                Button("Back to Menu", id="back_to_menu", variant="primary"),
                id="csv_import_buttons"
            ),
            id="csv_import_container"
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "back_to_menu":
            self.app.push_screen(MenuScreen())
        elif event.button.id == "import_btn":
            csv_filename = self.query_one("#csv_select", Select).value
            sap_full_path = self.query_one("#sap_select", Select).value
            if csv_filename and sap_full_path:
                import_questions_to_db_with_sap(csv_filename, sap_full_path)
            uncategorized = get_uncategorized_questions_from_db()
            self.app.push_screen(QuestionCategorizerScreen(uncategorized))

    async def on_key(self, event: events.Key):
        if event.key == "ctrl+c":
            await self.app.action_quit()

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

# Add this function to import questions with SAP association:
def import_questions_to_db_with_sap(csv_file, sap_full_path):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            question = row[0].strip()
            if not question:
                continue
            # Check if question already exists
            c.execute("SELECT guid FROM questions WHERE question = ?", (question,))
            result = c.fetchone()
            if not result:
                guid = str(uuid.uuid4())
                c.execute(
                    "INSERT INTO questions (guid, question, category, aI_response, evaluation_text, extra_column1, extra_column2, extra_column3, SAPFullPath, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (guid, question, '', '', '', '', '', '', sap_full_path, '')
                )
            else:
                # Update SAPFullPath if question exists
                c.execute(
                    "UPDATE questions SET SAPFullPath = ? WHERE question = ?",
                    (sap_full_path, question)
                )
    conn.commit()
    conn.close()

# --- Main App ---
class MainApp(App):
    def show_csv_import_screen(self):
        csv_files = [f for f in Path('.').glob('*.csv')]
        if csv_files:
            self.push_screen(CsvImportScreen())
        else:
            # If no CSVs, go to menu or categorizer
            if not config_exists():
                config_values = get_config_values()
                self.push_screen(ConfigScreen(initial_values=config_values))
            else:
                uncategorized = get_uncategorized_questions_from_db()
                self.push_screen(QuestionCategorizerScreen(uncategorized))

    def on_mount(self):
        csv_files = [f for f in Path('.').glob('*.csv')]
        if csv_files:
            self.show_csv_import_screen()
        elif not config_exists():
            config_values = get_config_values()
            self.push_screen(ConfigScreen(initial_values=config_values))
        else:
            uncategorized = get_uncategorized_questions_from_db()
            self.push_screen(QuestionCategorizerScreen(uncategorized))

if __name__ == "__main__":
    init_db()
    init_config_db()
    MainApp().run()