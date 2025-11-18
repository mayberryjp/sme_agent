import csv
import sqlite3
import datetime
import uuid
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Static, Button, Header, Footer
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual import events

CSV_FILE = "questions.csv"
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
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_categorized_guids():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT guid FROM questions WHERE category IS NOT NULL AND category != ''")
    rows = c.fetchall()
    conn.close()
    return set(row[0] for row in rows)

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

def read_questions(csv_file):
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        return [row[0] for row in reader if row and row[0].strip()]

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

def get_uncategorized_questions_from_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT guid, question FROM questions WHERE category IS NULL OR category = ''")
    rows = c.fetchall()
    conn.close()
    return [{"guid": row[0], "question": row[1]} for row in rows]

class QuestionCategorizerApp(App):
    question_index = reactive(0)

    def __init__(self, questions):
        super().__init__()
        self.questions = questions

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Question Categorizer", classes="title", id="title"),
            Static("", id="question"),
            Horizontal(
                *[Button(cat, id=f"cat_{i}", variant="primary") for i, cat in enumerate(CATEGORIES)],
                id="category_buttons"
            ),
            Horizontal(
                Button("Go Back", id="go_back", variant="warning"),
                id="nav_buttons"
            ),
            id="main_container"
        )
        yield Footer()

    def on_mount(self):
        self.update_question()

    def update_question(self):
        question_obj = self.questions[self.question_index] if self.question_index < len(self.questions) else None
        question_widget = self.query_one("#question", Static)
        if question_obj:
            # Use a softer color
            question_widget.update(f"\n\n[bold light_steel_blue]{question_obj['question']}[/bold light_steel_blue]\n")
        else:
            question_widget.update("\n\n[bold magenta]All questions done![/bold magenta]\n")
        for i, cat in enumerate(CATEGORIES):
            btn = self.query_one(f"#cat_{i}", Button)
            btn.disabled = question_obj is None

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "go_back":
            # Go back to previous question if possible
            if self.question_index > 0:
                self.question_index -= 1
                self.update_question()
            return

        if self.question_index >= len(self.questions):
            return
        category = str(event.button.label)
        question_obj = self.questions[self.question_index]
        guid = question_obj["guid"]
        question = question_obj["question"]

        # Debug prints
        print(f"[DEBUG] guid: {repr(guid)}")
        print(f"[DEBUG] category: {repr(category)}")
        print(f"[DEBUG] question: {repr(question)}")

        timestamp = datetime.datetime.now().isoformat()
        row = [guid, question, category, "", "", "", "", "", timestamp]
        save_to_db(row)
        self.question_index += 1
        self.update_question()

    async def on_key(self, event: events.Key):
        if event.key == "ctrl+c":
            await self.action_quit()

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

if __name__ == "__main__":
    init_db()
    if not Path(CSV_FILE).exists():
        print(f"CSV file '{CSV_FILE}' not found. Please create it with one question per line.")
    else:
        import_questions_to_db(CSV_FILE)
        uncategorized = get_uncategorized_questions_from_db()
        QuestionCategorizerApp(uncategorized).run()