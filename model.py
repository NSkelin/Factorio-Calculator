import os
from dotenv import load_dotenv
import mysql.connector


class FactorioDB:
    def __init__(self):
        load_dotenv()
        self.connection = mysql.connector.connect(
            host='127.0.0.1',
            user=os.getenv("USER"),
            password=os.getenv("PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        self.cursor = self.connection.cursor()

    def execute_mysql_statement(self, statement):
        self.cursor.execute(statement)
        return self.cursor.fetchall()

    def create_executemany_data_format(self, data):
        formatted_data = ()
        for item in data:
            formatted_data = formatted_data + (item,)
        return formatted_data

    def add_item(self, item_name: str, power_value_kw: int):
        try:
            self.cursor.callproc("add_new_item", (item_name, power_value_kw))
            self.connection.commit()
        except mysql.connector.Error as error:
            print("Failed to add a new item:\n", error)

    def add_recipe(self, recipe_speed: int, products: list, machine_types: list, ingredients: list = None):
        try:
            stmt = "insert into recipes(`recipe speed`) values (%s);"
            data = (recipe_speed,)
            self.cursor.execute(stmt, data)
            recipe_id = self.cursor.lastrowid

            stmt2 = "insert into products(`item name`, `recipe id`, `quantity`) values(%s, %s, %s);"
            data2 = []
            for product in products:
                formatted_data = self.create_executemany_data_format([product["Name"], recipe_id, product["Amount"]])
                data2.append(formatted_data)
            self.cursor.executemany(stmt2, data2)

            if ingredients is not None:
                stmt3 = "insert into ingredients(`recipe id`, `item name`, `quantity`) values(%s, %s, %s);"
                data3 = []
                for ingredient in ingredients:
                    formatted_data = self.create_executemany_data_format([recipe_id, ingredient["Name"], ingredient["Amount"]])
                    data3.append(formatted_data)
                self.cursor.executemany(stmt3, data3)

            stmt4 = "insert into `allowed machine types`(`recipe id`, `machine type`) values(%s, %s);"
            data4 = []
            for machine_type in machine_types:
                formatted_data = self.create_executemany_data_format([recipe_id, machine_type["Type"]])
                data4.append(formatted_data)
            self.cursor.executemany(stmt4, data4)

            self.connection.commit()
        except mysql.connector.Error as error:
            print(error)
            self.connection.rollback()

    def add_machine_variant(self, machine_type, variant_num, crafting_speed, max_power_usage):
        try:
            stmt = "insert into `machine variant` (`variant name`, `machine type`, `crafting speed`," \
                   " `max energy usage (kw/s)`) values (%s, %s, %s, %s);"
            data = (variant_num, machine_type, crafting_speed, max_power_usage)
            self.cursor.execute(stmt, data)
            self.connection.commit()
        except mysql.connector.Error as error:
            print(error)
            self.connection.rollback()

    def add_machine_type(self, machine_type):
        try:
            stmt = 'insert into `machine types` (`type`) values(%s);'
            data = (machine_type,)
            self.cursor.execute(stmt, data)
            self.connection.commit()
        except mysql.connector.Error as error:
            print(error)
            self.connection.rollback()

    def get_items(self):
        stmt = "select `item name` from items;"
        items = self.execute_mysql_statement(stmt)
        return items

    def get_machine_types(self):
        stmt = "select `type` from `machine types`;"
        types = self.execute_mysql_statement(stmt)
        return types

    def get_recipe_ids_by_product(self, product: str):
        stmt = "select `recipe id` from products where `item name` = '" + product + "';"
        recipe_ids = self.execute_mysql_statement(stmt)
        return recipe_ids

    def get_products_by_recipe_id(self, recipe_id):
        stmt = "select `item name`, `quantity` from products where `recipe id` = " + recipe_id + ";"
        return self.execute_mysql_statement(stmt)

    def get_ingredients_by_recipe_id(self, recipe_id: str):
        stmt = "select `item name`, `quantity` from ingredients where `recipe id` = " + recipe_id + ";"
        ingredients = self.execute_mysql_statement(stmt)
        return ingredients

    def get_product_quantity(self, product_name: str, recipe_id: str):
        stmt = ('select quantity from products where `item name` = "' + product_name + '" and `recipe id` = ' +
                recipe_id + ';')
        product_quantity = self.execute_mysql_statement(stmt)
        return product_quantity

    def get_item_power_value(self, item_name: str):
        stmt = 'select `power value (kw)` from items where `item name` = "' + item_name + '";'
        return self.execute_mysql_statement(stmt)

    def get_recipe_speed(self, recipe_id: str):
        stmt = 'select `recipe speed` from recipes where `recipe id` = ' + recipe_id + ';'
        return self.execute_mysql_statement(stmt)

    def get_allowed_machine_type(self, recipe_id: str):
        stmt = 'select `machine type` from `allowed machine types` where `recipe id` = ' + recipe_id + ';'
        return self.execute_mysql_statement(stmt)

    def get_machine_variants(self, machine_type):
        stmt = ('select * from `machine variant` where `machine type` = "' + machine_type + '";')
        return self.execute_mysql_statement(stmt)

    def get_variant_crafting_speed(self, machine_type, variant_name):
        stmt = ('select `crafting speed` from `machine variant` where `variant name` = ' + variant_name +
                ' and `machine type` = "' + machine_type + '";')
        return self.execute_mysql_statement(stmt)

    def get_variant_max_energy_usage(self, machine_type, variant_name):
        stmt = ('select `max energy usage (kw/s)` from `machine variant` where `variant name` = ' + variant_name +
                ' and `machine type` = "' + machine_type + '";')
        print(stmt)
        return self.execute_mysql_statement(stmt)

    def get_ingredient_quantity(self, recipe_id, ingredient_name):
        stmt = ("select quantity from ingredients where `recipe id` = " + recipe_id +
                " and `item name` = '" + ingredient_name + "';")
        return self.execute_mysql_statement(stmt)

