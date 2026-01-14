from textual.app import App
from pathlib import Path
from db_utils import init_db, init_config_db, config_exists, get_config_values, get_uncategorized_questions_from_db

from config_screen import ConfigScreen
from menu_screen import MenuScreen
from question_categorizer_screen import QuestionCategorizerScreen
from csv_import_screen import CsvImportScreen

class MainApp(App):
    def show_csv_import_screen(self):
        csv_files = [f for f in Path('.').glob('*.csv')]
        if csv_files:
            self.push_screen(CsvImportScreen())
        else:
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