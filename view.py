from PySide2 import QtCore, QtWidgets, QtGui
import sys


class RecipeCreationPage(QtWidgets.QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.permanent_inputs = []
        self.temporary_inputs = []
        self.items = self.controller.get_items()
        self.machine_types = self.controller.get_machine_types()

        # create all elements
        self.main_layout = QtWidgets.QGridLayout()

        create_button = QtWidgets.QPushButton("Create Recipe")
        create_button.clicked.connect(self.add_new_recipe)

        cancel_button = QtWidgets.QPushButton("Clear All")
        cancel_button.clicked.connect(self.clear_all)

        label = QtWidgets.QLabel("Recipe Speed (seconds)")

        self.textbox = QtWidgets.QLineEdit()
        self.permanent_inputs.append(self.textbox)
        validator = QtGui.QDoubleValidator(0, 180, 1)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.textbox.setValidator(validator)

        self.product_column = self.create_product_column()
        self.machine_type_column = self.create_machine_type_column()
        self.ingredient_column = self.create_ingredient_column()

        # set all elements
        self.main_layout.addWidget(create_button, 0, 0)
        self.main_layout.addWidget(cancel_button, 0, 2)
        self.main_layout.addWidget(self.textbox, 1, 0)
        self.main_layout.addWidget(label, 1, 1)

        self.main_layout.setRowStretch(5, 1)

        self.main_layout.addLayout(self.product_column, 2, 0, 1)
        self.main_layout.addLayout(self.machine_type_column, 2, 1, 1)
        self.main_layout.addLayout(self.ingredient_column, 2, 2, 1)
        self.setLayout(self.main_layout)

    def create_product_column(self):
        v_box_layout = QtWidgets.QVBoxLayout()

        # first row
        row1 = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("Products")
        add_button = QtWidgets.QPushButton("Add Another")
        add_button.clicked.connect(lambda: self.add_new_row(v_box_layout, 2, self.items))

        row1.addWidget(title_label)
        row1.addWidget(add_button)
        v_box_layout.addLayout(row1)

        # second row
        row2 = QtWidgets.QHBoxLayout()
        column_name1 = QtWidgets.QLabel("Name")
        column_name2 = QtWidgets.QLabel("Amount")

        row2.addWidget(column_name1)
        row2.addWidget(column_name2)
        v_box_layout.addLayout(row2)

        # third row
        row3 = QtWidgets.QHBoxLayout()
        user_input1 = QtWidgets.QLineEdit()
        completer = QtWidgets.QCompleter(self.items)
        user_input1.setCompleter(completer)
        user_input2 = QtWidgets.QLineEdit()
        validator = QtGui.QDoubleValidator(0, 999, 1)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        user_input2.setValidator(validator)

        row3.addWidget(user_input1)
        row3.addWidget(user_input2)
        self.permanent_inputs.append(user_input1)
        self.permanent_inputs.append(user_input2)
        v_box_layout.addLayout(row3)

        return v_box_layout

    def create_machine_type_column(self):
        v_box_layout = QtWidgets.QVBoxLayout()

        # first row
        row1 = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("Machine Types")
        add_button = QtWidgets.QPushButton("Add Another")
        add_button.clicked.connect(lambda: self.add_new_row(v_box_layout, 1, self.machine_types))

        row1.addWidget(title_label)
        row1.addWidget(add_button)
        v_box_layout.addLayout(row1)

        # second row
        row2 = QtWidgets.QHBoxLayout()
        column_name1 = QtWidgets.QLabel("Type")

        row2.addWidget(column_name1)
        v_box_layout.addLayout(row2)

        # third row
        row3 = QtWidgets.QHBoxLayout()
        user_input1 = QtWidgets.QLineEdit()
        completer = QtWidgets.QCompleter(self.machine_types)
        user_input1.setCompleter(completer)

        row3.addWidget(user_input1)
        self.permanent_inputs.append(user_input1)
        v_box_layout.addLayout(row3)

        return v_box_layout

    def create_ingredient_column(self):
        v_box_layout = QtWidgets.QVBoxLayout()

        # first row
        row1 = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("Ingredients")
        add_button = QtWidgets.QPushButton("Add Another")
        add_button.clicked.connect(lambda: self.add_new_row(v_box_layout, 2, self.items))

        row1.addWidget(title_label)
        row1.addWidget(add_button)
        v_box_layout.addLayout(row1)

        # second row
        row2 = QtWidgets.QHBoxLayout()
        column_name1 = QtWidgets.QLabel("Name")
        column_name2 = QtWidgets.QLabel("Amount")

        row2.addWidget(column_name1)
        row2.addWidget(column_name2)
        v_box_layout.addLayout(row2)

        # third row
        row3 = QtWidgets.QHBoxLayout()
        user_input1 = QtWidgets.QLineEdit()
        completer = QtWidgets.QCompleter(self.items)
        user_input1.setCompleter(completer)
        user_input2 = QtWidgets.QLineEdit()
        validator = QtGui.QDoubleValidator(0, 999, 1)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        user_input2.setValidator(validator)

        row3.addWidget(user_input1)
        row3.addWidget(user_input2)
        self.permanent_inputs.append(user_input1)
        self.permanent_inputs.append(user_input2)
        v_box_layout.addLayout(row3)

        return v_box_layout

    def add_new_row(self, parent, length, filter):
        row = QtWidgets.QHBoxLayout()
        for i in range(0, length):
            text_area = QtWidgets.QLineEdit()
            if i == 0:
                filter = QtWidgets.QCompleter(filter)
                text_area.setCompleter(filter)
            elif i == 1:
                validator = QtGui.QDoubleValidator(0, 999, 1)
                validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
                text_area.setValidator(validator)
            row.addWidget(text_area)
            self.temporary_inputs.append(text_area)
        delete_but = QtWidgets.QPushButton("X")
        delete_but.clicked.connect(lambda: self.delete_layout_and_all_widgets(row))
        row.addWidget(delete_but)
        self.temporary_inputs.append(delete_but)
        parent.insertLayout(parent.count(), row)

    def clear_all(self):
        for perm_input in self.permanent_inputs:
            perm_input.setText("")

        for temp_input in self.temporary_inputs:
            temp_input.deleteLater()
        self.temporary_inputs = []

    def delete_layout_and_all_widgets(self, row):
        while row.count():
            child = row.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                self.temporary_inputs.remove(child.widget())
        parent = row.parent()
        parent.removeItem(row)
        parent.update()

    def add_new_recipe(self):
        v_box_layouts = self.main_layout.children()
        recipe_speed = self.textbox.text()
        products = self.get_recipe_data(v_box_layouts[0])
        machine_types = self.get_recipe_data(v_box_layouts[1])
        ingredients = self.get_recipe_data(v_box_layouts[2])
        print(recipe_speed)
        print(products)
        print(machine_types)
        print(ingredients)
        self.controller.add_recipe(recipe_speed, products, machine_types, ingredients)
        # self.clear_all()

    # gets all entrys of data from one part of the recipe (products, machine types, or ingredients)
    def get_recipe_data(self, v_box_layout):
        items = []
        for h_box_layout in v_box_layout.children()[1:]:
            item = {}
            for i in range(0, h_box_layout.count()):
                widget = h_box_layout.itemAt(i).widget()
                widget_type = widget.__class__.__name__
                if widget_type == "QLineEdit":
                    text = widget.text()
                    category_name = v_box_layout.children()[1].itemAt(i).widget().text()
                    item[category_name] = text
            if item:
                items.append(item)
        return items


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = RecipeCreationPage()

    widget.resize(1280, 720)
    widget.show()

    sys.exit(app.exec_())