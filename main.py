import os
from dotenv import load_dotenv
import mysql.connector
from anytree import Node, RenderTree, find_by_attr, PreOrderIter


def add_item(item_name: str, power_value_kw: int):
    try:
        if power_value_kw < 0:
            print("Power value cannot be negative.")
        else:
            cursor.callproc("add_new_item", (item_name, power_value_kw))
            connection.commit()
            print("Success: added item", item_name)
    except mysql.connector.Error as error:
        print("Failed to add a new item:\n", error)


def create_executemany_data_format(data):
    formatted_data = ()
    for item in data:
        formatted_data = formatted_data + (item,)
    return formatted_data


def add_recipe(recipe_speed, products, ingredients, machine_types ):
    try:
        stmt = "insert into recipes(`recipe speed`) values (%s);"
        data = (recipe_speed,)
        cursor.execute(stmt, data)
        recipe_id = cursor.lastrowid

        stmt2 = "insert into products(`item name`, `recipe id`, `quantity`) values(%s, %s, %s);"
        data2 = []
        for product in products:
            formatted_data = create_executemany_data_format([product["name"], recipe_id, product["amt"]])
            data2.append(formatted_data)
        cursor.executemany(stmt2, data2)

        if ingredients is not None:
            stmt3 = "insert into ingredients(`recipe id`, `item name`, `quantity`) values(%s, %s, %s);"
            data3 = []
            for ingredient in ingredients:
                formatted_data = create_executemany_data_format([recipe_id, ingredient["name"], ingredient["amt"]])
                data3.append(formatted_data)
            cursor.executemany(stmt3, data3)

        stmt4 = "insert into `allowed machine types`(`recipe id`, `machine type`) values(%s, %s);"
        data4 = []
        for type in machine_types:
            formatted_data = create_executemany_data_format([recipe_id, type])
            data4.append(formatted_data)
        cursor.executemany(stmt4, data4)

        connection.commit()
    except mysql.connector.Error as error:
        print(error)
        connection.rollback()


def add_machine_variant(machine_type, variant_num, crafting_speed, max_power_usage):
    try:
        stmt = "insert into `machine variant` (`variant name`, `machine type`, `crafting speed`, `max energy usage (kw/s)`) values (%s, %s, %s, %s);"
        data = (variant_num, machine_type, crafting_speed, max_power_usage)
        cursor.execute(stmt, data)
        connection.commit()
    except mysql.connector.Error as error:
        print(error)
        connection.rollback()


def add_machine_type(machine_type, variants=[]):
    try:
        stmt = 'insert into `machine types` (`type`) values(%s);'
        data = (machine_type,)
        cursor.execute(stmt, data)
        connection.commit()
        for variant in variants:
            add_machine_variant(machine_type, variant["version"], variant["crafting_speed"], variant["max_power_usage"])

    except mysql.connector.Error as error:
        print(error)
        connection.rollback()


def ask_yes_or_no(object_to_add):
    while True:
        choice = input("Add another " + object_to_add + "? (y/n)")
        if choice is "n":
            return False
        elif choice is "y":
            return True
        else:
            print("unknown option use (y/n)")


def execute_mysql_statement(statement):
    cursor.execute(statement)
    return cursor.fetchall()


# Retrieves a nodes data from the database.
def get_node_stats(node):
    stmt = ('select quantity from products where `item name` = "' + node.name + '" and `recipe id` = ' +
            str(node.recipe_id) + ';')
    node.amount_produced = float(execute_mysql_statement(stmt)[0][0])
    stmt = 'select `power value (kw)` from items where `item name` = "' + node.name + '";'
    node.power_per_item = int(execute_mysql_statement(stmt)[0][0])
    stmt = 'select `recipe speed` from recipes where `recipe id` = ' + str(node.recipe_id) + ';'
    node.recipe_speed = execute_mysql_statement(stmt)[0][0]
    stmt = 'select `machine type` from `allowed machine types` where `recipe id` = ' + str(node.recipe_id) + ';'
    node.machine_types = execute_mysql_statement(stmt)
    machine_type_index = 0
    # todo error: if theres only one type but its say level 2 instead of 1, this crashes.
    if len(node.machine_types) > 1:
        print(node.machine_types)
        machine_type_index = int(input("enter the number of the type u want for " + node.name + ": ")) - 1
    machine_type = node.machine_types[machine_type_index][0]
    stmt = ('select `crafting speed` from `machine variant` where `variant name` = 1 ' +
            'and `machine type` = "' + machine_type + '";')
    node.machine_crafting_speed = execute_mysql_statement(stmt)[0][0]
    stmt = ('select `max energy usage (kw/s)` from `machine variant` where `variant name` = 1 ' +
            'and `machine type` = "' + machine_type + '";')
    node.machine_power_cost = execute_mysql_statement(stmt)[0][0]
    if node.parent is not None:
        stmt = ("select quantity from ingredients where `recipe id` = " + str(node.parent.recipe_id) +
                " and `item name` = '" + node.name + "';")
        node.amount_required = execute_mysql_statement(stmt)[0][0]
    return node


# Generates a tree starting at start_product as the root product.
# Recipe branches are then created off the product for each recipe that makes the product.
# From each recipe branch are ingredient branches which are also products of other recipes.
# Repeats until there are no more ingredient branches possible.
def generate_product_tree(start_product):
    try:
        root_node = Node(start_product)
        product_nodes = [root_node]
        while True:
            if len(product_nodes) == 0:
                break
            new_product_nodes = []
            # For each product, find all the recipes that produce it.
            for product_node in product_nodes:
                stmt = "select `recipe id` from products where `item name` = '" + product_node.name + "';"
                recipe_ids = execute_mysql_statement(stmt)
                # For each recipe, create a node with its ID and attach it to the product node.
                # Then find all the ingredients required for the recipe.
                for recipe_id in recipe_ids:
                    # checks if the recipe already exists in the nodes ancestors to prevent infinite loops
                    recipe_exists = False
                    ancestors = product_node.ancestors
                    for node in ancestors:
                        if "recipe id" in node.name:
                            if node.recipe_id == recipe_id[0]:
                                recipe_exists = True
                    # if the recipe doesnt already exist
                    if recipe_exists != True:
                        recipe_node = Node("recipe id: " + str(recipe_id[0]), parent=product_node,
                                           recipe_id=recipe_id[0])
                        stmt = "select `item name` from ingredients where `recipe id` = " + str(recipe_id[0]) + ";"
                        ingredients = execute_mysql_statement(stmt)
                        # For each ingredient, create a node with its name and attach it to the recipe node.
                        # Then add the ingredient to the next list of products
                        for ingredient_node in ingredients:
                            ingredient_node = Node(ingredient_node[0], parent=recipe_node)
                            new_product_nodes.append(ingredient_node)
            product_nodes = new_product_nodes
        return root_node
    except mysql.connector.Error as error:
        print(error)
        connection.rollback()


# Prints a tree and shows the current position in the tree
def render_tree_position(tree, current_node):
    for pre, fill, node in RenderTree(tree):
        if node.name == current_node:
            print("\033[94m %s%s \033[0m" % (pre, node.name))
        else:
            print("%s%s" % (pre, node.name))


# Prompts a user to filter through a product tree, choosing which recipes and machines to use.
def filter_product_tree(root_node, start_product):
    # todo if an item has no recipe return an error message instead of crashing
    try:
        for node in PreOrderIter(root_node):
            if "recipe_id" not in node.name:
                while True:
                    if len(node.children) > 1:
                        render_tree_position(root_node, node.name)
                        id = int(input("Enter the ID of the recipe you want to use to make " + node.name + ": "))
                    else:
                        id = node.children[0].recipe_id
                    recipe_node = find_by_attr(node, id, name="recipe_id", maxlevel=2)
                    if recipe_node is not None:
                        node.recipe_id = id
                        get_node_stats(node)
                        break
                    else:
                        print("Invalid ID")
                children = []
                for child in recipe_node.children:
                    children.append(child)
                node.children = children
        return root_node
    except mysql.connector.Error as error:
        print(error)
        connection.rollback()


def size_column(text):
    text_length = len(text)
    i = text_length
    new_str = " "
    new_str += text
    while True:
        if i >= 20:
            new_str += "|"
            break
        else:
            new_str += " "
            i += 1
    return new_str


def print_table(tree):
    top = "---------------------"
    name = "| name               |"
    gain = "| gain               |"
    cost = "| cost               |"
    cumulative_cost = "| cumulative         |"
    net = "| net                |"
    bot = "---------------------"
    i = 0
    for node in PreOrderIter(tree):
        top += " ---------------------"
        name += size_column(node.name)
        gain += size_column(str(node.gain))
        cost += size_column(str(node.cost))
        cumulative_cost += size_column(str(node.cumulative_cost))
        net += size_column(str(node.net))
        bot += " ---------------------"
        if node.is_leaf:
            print(top)
            print(name)
            print(gain)
            print(cost)
            print(cumulative_cost)
            print(net)
            print(bot)
            top = "---------------------"
            name = "| name               |"
            gain = "| gain               |"
            cost = "| cost               |"
            cumulative_cost = "| cumulative         |"
            net = "| net                |"
            bot = "---------------------"


def calculate_energy_cost_gain():
    final_product = input("enter the product: ")
    tree = generate_product_tree(final_product)
    filtered_tree = filter_product_tree(tree, final_product)

    # calculate cost and gain for each node
    for node in PreOrderIter(filtered_tree):
        if "recipe id" not in node.name:
            if node.parent is None:
                node.times_crafted = 1
            else:
                node.times_crafted = (node.amount_required / node.amount_produced) * node.parent.times_crafted
            node.cost = (((node.machine_power_cost * node.recipe_speed) / node.machine_crafting_speed)
                         * node.times_crafted)
            node.gain = (node.power_per_item * node.amount_produced) * node.times_crafted

    # calculate the cumulative cost of a node from its descendants
    for node in PreOrderIter(filtered_tree):
        cumulative_cost = 0
        for descendant in node.descendants:
            cumulative_cost += descendant.cost
        node.cumulative_cost = cumulative_cost + node.cost
        node.net = node.gain - node.cumulative_cost
    print_table(filtered_tree)


load_dotenv()
connection = mysql.connector.connect(
    host='127.0.0.1',
    user=os.getenv("USER"),
    password=os.getenv("PASSWORD"),
    database=os.getenv("DB_NAME")
)
cursor = connection.cursor()

options = ["Quit", "Add item", "Add recipe", "Add machine type", "Add machine variant",
           "Calculate energy cost and gain for a recipe"]

while True:
    i = 0
    for option in options:
        print("{} -- {}".format(i, option))
        i += 1
    chosen_option = input("\nEnter the number corresponding to the option: ")
    if chosen_option is "0":
        print("\n{}".format(options[0]))
        break

    elif chosen_option is "1":
        print("\n{}".format(options[1]))
        item_name = input("Enter the items name: ")
        power = int(input("Enter the amount of power one {} generates (in kilowatts): ".format(item_name)))
        add_item(item_name, power)

    elif chosen_option is "2":
        print("\n{}".format(options[2]))
        products = []
        ingredients = []
        types = []
        recipe_speed = input("Enter the recipe craft speed: ")
        # get products for recipe
        while True:
            print("Creating product...")
            product = input("Enter the product name: ")
            quantity = input("Enter the amount of {} made by the recipe: ".format(product))
            products.append({'name': product, 'amt': quantity})
            if ask_yes_or_no("product") is False:
                break
        # get ingredients for recipe
        while True:
            if ask_yes_or_no("ingredient") is False:
                break
            print("Creating ingredient...")
            ingredient = input("Enter the ingredient name: ")
            quantity = input("Enter the amount of {} needed by the recipe: ".format(ingredient))
            ingredients.append({'name': ingredient, 'amt': quantity})
        # get allowed machine types used to craft recipe
        while True:
            machine_type = input("Enter a type of machine used in the recipe")
            types.append(machine_type)
            if ask_yes_or_no("machine type") is False:
                break
        add_recipe(recipe_speed, products, ingredients, types)

    elif chosen_option is "3":
        machine_type = input("enter the machine name without version: ")
        variants = []
        while True:
            version = input("enter the machine version (1/2/3/etc): ")
            crafting_speed = input("enter the variants crafting speed: ")
            max_power_usage = input("enter the machines max power usage (kw/s)")
            variants.append({"version": version, "crafting_speed": crafting_speed, "max_power_usage": max_power_usage})
            if ask_yes_or_no("variant") is False:
                break
        add_machine_type(machine_type, variants)

    elif chosen_option is "4":
        machine_type = input("enter the machine name without version: ")
        version = input("enter the machine version (1/2/3/etc): ")
        crafting_speed = input("enter the variants crafting speed: ")
        max_power_usage = input("enter the machines max power usage (kw/s)")
        add_machine_variant(machine_type, version, crafting_speed, max_power_usage)
    elif chosen_option is "5":
        calculate_energy_cost_gain()
    else:
        print("Unknown option.\n")
