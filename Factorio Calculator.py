import sys
from PySide2.QtWidgets import QApplication
from main import MainController
from model import FactorioDB
from view import RecipeCreationPage


class App(QApplication):
    def __init__(self):
        super(App, self).__init__()
        self.model = FactorioDB()
        self.controller = MainController(self.model)
        self.view = RecipeCreationPage(self.controller)
        self.view.resize(800, 600)
        self.view.show()


if __name__ == '__main__':
    app = App()
    sys.exit(app.exec_())
