from anytree import Node, RenderTree, find_by_attr, PreOrderIter


class MainController:
    def __init__(self, model):
        self.model = model
        return

    def add_item(self, item_name: str, power_value_kw: int):
        if power_value_kw < 0:
            print("Power value cannot be negative.")
        else:
            self.model.add_item(item_name, power_value_kw)

    def add_recipe(self, recipe_speed: int, products: list, machine_types: list, ingredients: list = None):
        recipe_ids = self.model.get_recipe_ids_by_product(products[0]["Name"])
        for product in products:
            product["Amount"] = float(product["Amount"])
        for ingredient in ingredients:
            ingredient["Amount"] = float(ingredient["Amount"])

        for recipe_id in recipe_ids:
            new_products = self.model.get_products_by_recipe_id(str(recipe_id[0]))
            new_list = []
            new_list2 = []
            for new_product in new_products:
                new_list.append({"Name": new_product[0], "Amount": new_product[1]})
            if sorted(products, key=lambda k: k['Name']) == sorted(new_list, key=lambda k: k['Name']):
                new_ingredients = self.model.get_ingredients_by_recipe_id(str(recipe_id[0]))
                for new_ingredient in new_ingredients:
                    new_list2.append({"Name": new_ingredient[0], "Amount": new_ingredient[1]})
                if sorted(ingredients, key=lambda k: k['Name']) == sorted(new_list2, key=lambda k: k['Name']):
                    print("recipe already exists")
                    return False
        self.model.add_recipe(recipe_speed, products, machine_types, ingredients)

    def add_machine_variant(self, machine_type, variant_num, crafting_speed, max_power_usage):
        self.model.add_machine_variant(machine_type, variant_num, crafting_speed, max_power_usage)

    def add_machine_type(self, machine_type: str, variants: list):
        self.model.add_machine_type(machine_type)
        for variant in variants:
            self.add_machine_variant(machine_type,
                                     variant["version"],
                                     variant["crafting_speed"],
                                     variant["max_power_usage"])

    def ask_yes_or_no(self, question: str):
        while True:
            choice = input(question + " (y/n)")
            if choice is "n":
                return False
            elif choice is "y":
                return True
            else:
                print("unknown option use (y/n)")

    # Retrieves a nodes data from the database.
    def get_node_stats(self, node):
        node.amount_produced = float(self.model.get_product_quantity(node.name, str(node.recipe_id))[0][0])
        node.power_per_item = int(self.model.get_item_power_value(node.name)[0][0])
        node.recipe_speed = self.model.get_recipe_speed(str(node.recipe_id))[0][0]
        node.machine_types = self.model.get_allowed_machine_type(str(node.recipe_id))
        machine_type_index = 0
        # todo error: if theres only one type but its say level 2 instead of 1, this crashes.
        if len(node.machine_types) > 1:
            print(node.machine_types)
            machine_type_index = int(input("enter the number of the type u want for " + node.name + ": ")) - 1
        machine_type = node.machine_types[machine_type_index][0]
        variants = self.model.get_machine_variants(machine_type)
        variant_index = 0
        if len(variants) > 1:
            print(variants)
            variant_index = int(input("enter the number of the type u want for " + node.name + ": ")) - 1
        variant_name = variants[variant_index][0]
        node.machine_crafting_speed = self.model.get_variant_crafting_speed(machine_type, variant_name)[0][0]
        node.machine_power_cost = self.model.get_variant_max_energy_usage(machine_type, variant_name)[0][0]
        if node.parent is not None:
            node.amount_required = self.model.get_ingredient_quantity(str(node.parent.recipe_id), node.name)[0][0]
        return node

    # checks if the recipe was already used.
    # prevents infinite loops by recipes that produce a product used by recipes used to craft it
    def check_if_recipe_already_used(self, product_node, recipe_id):
        ancestors = product_node.ancestors
        for node in ancestors:
            if "recipe id" in node.name:
                if node.recipe_id == recipe_id[0]:
                    product_node.recursive_processing = True
                    product_node.recursive_recipe_id = node.recipe_id
                    return True
        return False

    # Generates a tree starting at start_product as the root product.
    # Recipe branches are then created off the product for each recipe that makes the product.
    # From each recipe branch are ingredient branches which are also products of other recipes.
    # Repeats until there are no more ingredient branches possible.
    def generate_product_tree(self, start_product):
        root_node = Node(start_product, recursive_processing=False)
        product_nodes = [root_node]
        while True:
            if len(product_nodes) == 0:
                break
            new_product_nodes = []
            # For each product, find all the recipes that produce it.
            for product_node in product_nodes:
                recipe_ids = self.model.get_recipe_ids_by_product(str(product_node.name))
                # For each recipe, create a node with its ID and attach it to the product node.
                # Then find all the ingredients required for the recipe.
                for recipe_id in recipe_ids:
                    if not self.check_if_recipe_already_used(product_node, recipe_id):
                        recipe_node = Node("recipe id: " + str(recipe_id[0]), parent=product_node,
                                           recipe_id=recipe_id[0])
                        ingredients = self.model.get_ingredients_by_recipe_id(str(recipe_id[0]))
                        # For each ingredient, create a node with its name and attach it to the recipe node.
                        # Then add the ingredient to the next list of products
                        for ingredient_node in ingredients:
                            ingredient_node = Node(ingredient_node[0], parent=recipe_node, recursive_processing=False)
                            new_product_nodes.append(ingredient_node)
            product_nodes = new_product_nodes
        return root_node

    # Prints a tree and shows the current position in the tree
    def render_tree_position(self, tree, current_node):
        for pre, fill, node in RenderTree(tree):
            if node.name == current_node:
                print("\033[94m %s%s \033[0m" % (pre, node.name))
            else:
                print("%s%s" % (pre, node.name))

    # Prompts a user to filter through a product tree, choosing which recipes and machines to use.
    def filter_product_tree(self, root_node):
        # todo if an item has no recipe return an error message instead of crashing
        for node in PreOrderIter(root_node):
            if "recipe_id" not in node.name:
                while True:
                    if len(node.children) > 1:
                        self.render_tree_position(root_node, node.name)
                        id = int(input("Enter the ID of the recipe you want to use to make " + node.name + ": "))
                    else:
                        id = node.children[0].recipe_id
                    recipe_node = find_by_attr(node, id, name="recipe_id", maxlevel=2)
                    if recipe_node is not None:
                        node.recipe_id = id
                        self.get_node_stats(node)
                        break
                    else:
                        print("Invalid ID")
                children = []
                for child in recipe_node.children:
                    children.append(child)
                node.children = children
        return root_node

    def size_column(self, text):
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

    def print_table(self, tree):
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
            name += self.size_column(node.name)
            gain += self.size_column(str(node.gain))
            cost += self.size_column(str(node.cost))
            cumulative_cost += self.size_column(str(node.cumulative_cost))
            net += self.size_column(str(node.net))
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

    def calculate_energy_cost_gain(self):
        final_product = input("enter the product: ")
        tree = self.generate_product_tree(final_product)
        filtered_tree = self.filter_product_tree(tree)

        # calculate cost and gain for each node
        for node in PreOrderIter(filtered_tree):
            if node.parent is None:
                node.times_crafted = 1
            else:
                node.times_crafted = (node.amount_required / node.amount_produced) * node.parent.times_crafted

            if node.recursive_processing and self.ask_yes_or_no("Recursively use {}?".format(node.name)):
                ancestor = find_by_attr(filtered_tree, node.recursive_recipe_id, name="recipe_id")
                node.amount_required = (node.amount_required - (ancestor.amount_produced / node.times_crafted))
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
        self.print_table(filtered_tree)

    def get_items(self):
        items = self.model.get_items()
        tuple_free_items = []
        for item in items:
            tuple_free_items.append(item[0])
        return tuple_free_items

    def get_machine_types(self):
        types = self.model.get_machine_types()
        tuple_free_types = []
        for machine_type in types:
            tuple_free_types.append(machine_type[0])
        return tuple_free_types


if __name__ == '__main__':
    from model import FactorioDB
    controller = MainController(FactorioDB())
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
            controller.add_item(item_name, power)

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
                products.append({'Product Name': product, 'Amount': quantity})
                if controller.ask_yes_or_no("Add another product?") is False:
                    break
            # get ingredients for recipe
            while True:
                if controller.ask_yes_or_no("Add another ingredient?") is False:
                    break
                print("Creating ingredient...")
                ingredient = input("Enter the ingredient name: ")
                quantity = input("Enter the amount of {} needed by the recipe: ".format(ingredient))
                ingredients.append({'Ingredient Name': ingredient, 'Amount': quantity})
            # get allowed machine types used to craft recipe
            while True:
                machine_type = input("Enter a type of machine used in the recipe")
                types.append(machine_type)
                if controller.ask_yes_or_no("Add another machine type?") is False:
                    break
            controller.add_recipe(recipe_speed, products, ingredients, types)

        elif chosen_option is "3":
            machine_type = input("enter the machine name without version: ")
            variants = []
            while True:
                version = input("enter the machine version (1/2/3/etc): ")
                crafting_speed = input("enter the variants crafting speed: ")
                max_power_usage = input("enter the machines max power usage (kw/s)")
                variants.append({"version": version, "crafting_speed": crafting_speed, "max_power_usage": max_power_usage})
                if controller.ask_yes_or_no("Add another variant?") is False:
                    break
            controller.add_machine_type(machine_type, variants)

        elif chosen_option is "4":
            machine_type = input("enter the machine name without version: ")
            version = input("enter the machine version (1/2/3/etc): ")
            crafting_speed = input("enter the variants crafting speed: ")
            max_power_usage = input("enter the machines max power usage (kw/s)")
            controller.add_machine_variant(machine_type, version, crafting_speed, max_power_usage)
        elif chosen_option is "5":
            controller.calculate_energy_cost_gain()
        else:
            print("Unknown option.\n")
