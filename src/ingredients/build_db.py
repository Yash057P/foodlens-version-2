"""Build webapp/data/ingredients.json - knowledge base for all 101 Food-101 classes.

Each entry: approx calories (per typical serving), main ingredients, category,
and common allergens. Values are curated approximations for a student project;
they are NOT medical advice.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / ".." / "webapp" / "data" / "ingredients.json"


def dish(cal, ingredients, category, allergens=()):
    return {"calories": cal, "ingredients": ingredients, "category": category, "allergens": list(allergens)}


DB = {
    "apple_pie": dish(350, ["apples", "flour", "butter", "sugar", "cinnamon", "pie crust"], "Dessert", ["gluten", "dairy"]),
    "baby_back_ribs": dish(450, ["pork ribs", "bbq sauce", "brown sugar", "paprika", "garlic", "salt"], "Main", []),
    "baklava": dish(330, ["phyllo pastry", "pistachios", "walnuts", "honey", "butter", "sugar syrup"], "Dessert", ["gluten", "nuts", "dairy"]),
    "beef_carpaccio": dish(300, ["raw beef fillet", "parmesan", "arugula", "olive oil", "lemon", "capers"], "Main", ["dairy"]),
    "beef_tartare": dish(280, ["raw beef", "egg yolk", "capers", "shallots", "mustard", "sourdough toast"], "Main", ["egg", "gluten"]),
    "beet_salad": dish(180, ["beetroot", "goat cheese", "walnuts", "arugula", "olive oil", "balsamic"], "Salad", ["dairy", "nuts"]),
    "beignets": dish(390, ["flour", "yeast", "milk", "sugar", "butter", "powdered sugar"], "Dessert", ["gluten", "dairy"]),
    "bibimbap": dish(520, ["rice", "beef", "vegetables", "egg", "gochujang", "sesame oil", "kimchi"], "Main", ["egg", "sesame"]),
    "bread_pudding": dish(320, ["bread", "milk", "eggs", "sugar", "butter", "cinnamon", "raisins"], "Dessert", ["gluten", "dairy", "egg"]),
    "breakfast_burrito": dish(450, ["tortilla", "eggs", "potato", "cheese", "sausage", "salsa"], "Main", ["gluten", "dairy", "egg"]),
    "bruschetta": dish(220, ["baguette", "tomatoes", "garlic", "basil", "olive oil", "balsamic"], "Appetizer", ["gluten"]),
    "caesar_salad": dish(360, ["romaine lettuce", "croutons", "parmesan", "caesar dressing", "anchovies", "garlic"], "Salad", ["gluten", "dairy", "egg", "fish"]),
    "cannoli": dish(280, ["ricotta", "flour", "sugar", "chocolate chips", "candied peel", "pistachios"], "Dessert", ["gluten", "dairy", "nuts"]),
    "caprese_salad": dish(250, ["tomatoes", "mozzarella", "basil", "olive oil", "balsamic", "salt"], "Salad", ["dairy"]),
    "carrot_cake": dish(420, ["carrots", "flour", "walnuts", "cream cheese", "sugar", "cinnamon"], "Dessert", ["gluten", "dairy", "egg", "nuts"]),
    "ceviche": dish(200, ["raw fish", "lime juice", "cilantro", "red onion", "chili", "corn"], "Appetizer", ["fish"]),
    "cheese_plate": dish(400, ["assorted cheese", "crackers", "grapes", "nuts", "honey", "figs"], "Appetizer", ["dairy", "gluten", "nuts"]),
    "cheesecake": dish(480, ["cream cheese", "graham cracker crust", "sugar", "eggs", "butter"], "Dessert", ["dairy", "egg", "gluten"]),
    "chicken_curry": dish(460, ["chicken", "turmeric", "cumin", "ginger", "garlic", "onion", "coconut milk"], "Main", [""]),
    "chicken_quesadilla": dish(520, ["tortilla", "chicken", "cheddar", "bell pepper", "onion", "salsa"], "Main", ["gluten", "dairy"]),
    "chicken_wings": dish(430, ["chicken wings", "buffalo sauce", "butter", "flour", "celery", "blue cheese"], "Main", ["dairy", "gluten"]),
    "chocolate_cake": dish(400, ["flour", "cocoa", "eggs", "butter", "sugar", "milk", "chocolate"], "Dessert", ["gluten", "dairy", "egg"]),
    "chocolate_mousse": dish(350, ["chocolate", "cream", "eggs", "sugar", "butter"], "Dessert", ["dairy", "egg"]),
    "churros": dish(310, ["flour", "sugar", "cinnamon", "oil", "egg"], "Dessert", ["gluten", "egg"]),
    "clam_chowder": dish(380, ["clams", "potatoes", "cream", "bacon", "onion", "butter"], "Soup", ["dairy", "shellfish", "gluten"]),
    "club_sandwich": dish(510, ["bread", "chicken", "bacon", "lettuce", "tomato", "mayonnaise", "egg"], "Main", ["gluten", "dairy", "egg"]),
    "crab_cakes": dish(360, ["crab meat", "breadcrumbs", "egg", "mayonnaise", "mustard", "old bay"], "Main", ["shellfish", "gluten", "egg"]),
    "creme_brulee": dish(310, ["cream", "egg yolks", "sugar", "vanilla"], "Dessert", ["dairy", "egg"]),
    "croque_madame": dish(540, ["bread", "ham", "gruyere", "bechamel", "egg", "butter"], "Main", ["gluten", "dairy", "egg"]),
    "cup_cakes": dish(350, ["flour", "sugar", "butter", "eggs", "milk", "frosting"], "Dessert", ["gluten", "dairy", "egg"]),
    "deviled_eggs": dish(190, ["eggs", "mayonnaise", "mustard", "paprika", "vinegar"], "Appetizer", ["egg"]),
    "donuts": dish(390, ["flour", "sugar", "yeast", "milk", "egg", "glaze"], "Dessert", ["gluten", "dairy", "egg"]),
    "dumplings": dish(320, ["flour", "pork", "cabbage", "ginger", "garlic", "soy sauce"], "Appetizer", ["gluten", "soy"]),
    "edamame": dish(190, ["soybeans", "salt", "sesame oil"], "Appetizer", ["soy", "sesame"]),
    "eggs_benedict": dish(520, ["english muffin", "eggs", "ham", "hollandaise", "butter", "chives"], "Main", ["gluten", "dairy", "egg"]),
    "escargots": dish(260, ["snails", "garlic", "butter", "parsley"], "Appetizer", ["dairy"]),
    "falafel": dish(330, ["chickpeas", "onion", "garlic", "parsley", "cumin", "tahini"], "Main", ["sesame"]),
    "filet_mignon": dish(580, ["beef tenderloin", "butter", "thyme", "garlic", "salt", "pepper"], "Main", ["dairy"]),
    "fish_and_chips": dish(540, ["cod", "beer batter", "potatoes", "flour", "malt vinegar", "peas"], "Main", ["gluten", "fish"]),
    "foie_gras": dish(420, ["duck liver", "brioche", "fig", "salt", "pepper"], "Appetizer", ["gluten", ""]),
    "french_fries": dish(350, ["potatoes", "oil", "salt"], "Side", []),
    "french_onion_soup": dish(320, ["onions", "beef broth", "baguette", "gruyere", "butter"], "Soup", ["gluten", "dairy"]),
    "french_toast": dish(380, ["bread", "egg", "milk", "cinnamon", "butter", "maple syrup"], "Main", ["gluten", "dairy", "egg"]),
    "fried_calamari": dish(380, ["squid", "flour", "egg", "oil", "lemon", "marinara"], "Appetizer", ["shellfish", "gluten", "egg"]),
    "fried_rice": dish(420, ["rice", "egg", "soy sauce", "scallions", "peas", "sesame oil"], "Main", ["egg", "soy"]),
    "frozen_yogurt": dish(220, ["yogurt", "sugar", "fruit toppings"], "Dessert", ["dairy"]),
    "garlic_bread": dish(280, ["baguette", "butter", "garlic", "parsley"], "Side", ["gluten", "dairy"]),
    "gnocchi": dish(430, ["potatoes", "flour", "egg", "tomato sauce", "parmesan"], "Main", ["gluten", "dairy", "egg"]),
    "greek_salad": dish(240, ["tomatoes", "cucumber", "olives", "feta", "red onion", "olive oil"], "Salad", ["dairy"]),
    "grilled_cheese_sandwich": dish(430, ["bread", "cheese", "butter"], "Main", ["gluten", "dairy"]),
    "grilled_salmon": dish(380, ["salmon", "olive oil", "lemon", "dill", "garlic"], "Main", ["fish"]),
    "guacamole": dish(180, ["avocado", "lime", "tomato", "onion", "cilantro", "jalapeno"], "Appetizer", []),
    "gyoza": dish(300, ["flour", "pork", "cabbage", "ginger", "soy sauce", "wonton wrappers"], "Appetizer", ["gluten", "soy"]),
    "hamburger": dish(550, ["beef patty", "bun", "cheddar", "lettuce", "tomato", "ketchup"], "Main", ["gluten", "dairy"]),
    "hot_and_sour_soup": dish(220, ["tofu", "mushrooms", "vinegar", "chili", "egg", "bamboo shoots"], "Soup", ["egg", "soy"]),
    "hot_dog": dish(400, ["frankfurter", "bun", "mustard", "ketchup", "onions"], "Main", ["gluten"]),
    "huevos_rancheros": dish(460, ["eggs", "tortilla", "salsa", "beans", "cheese", "cilantro"], "Main", ["gluten", "dairy", "egg"]),
    "hummus": dish(200, ["chickpeas", "tahini", "olive oil", "garlic", "lemon"], "Appetizer", ["sesame"]),
    "ice_cream": dish(270, ["cream", "milk", "sugar", "vanilla"], "Dessert", ["dairy"]),
    "lasagna": dish(540, ["pasta", "ground beef", "tomato sauce", "ricotta", "mozzarella", "parmesan"], "Main", ["gluten", "dairy", "egg"]),
    "lobster_bisque": dish(390, ["lobster", "cream", "butter", "onion", "tomato paste", "brandy"], "Soup", ["dairy", "shellfish"]),
    "lobster_roll_sandwich": dish(460, ["lobster", "butter", "hot dog bun", "mayonnaise", "lemon"], "Main", ["gluten", "dairy", "shellfish"]),
    "macaroni_and_cheese": dish(520, ["pasta", "cheddar", "milk", "butter", "flour"], "Main", ["gluten", "dairy"]),
    "macarons": dish(290, ["almond flour", "egg whites", "sugar", "buttercream"], "Dessert", ["nuts", "egg", "dairy"]),
    "miso_soup": dish(120, ["miso paste", "tofu", "seaweed", "scallions", "dashi"], "Soup", ["soy"]),
    "mussels": dish(360, ["mussels", "white wine", "garlic", "butter", "shallots", "parsley"], "Main", ["shellfish", "dairy"]),
    "nachos": dish(560, ["tortilla chips", "cheese", "jalapenos", "beans", "guacamole", "sour cream"], "Snack", ["dairy", "gluten"]),
    "omelette": dish(280, ["eggs", "cheese", "butter", "vegetables", "herbs"], "Main", ["egg", "dairy"]),
    "onion_rings": dish(340, ["onions", "flour", "beer batter", "oil"], "Appetizer", ["gluten"]),
    "oysters": dish(180, ["oysters", "lemon", "mignonette"], "Appetizer", ["shellfish"]),
    "pad_thai": dish(480, ["rice noodles", "shrimp", "egg", "bean sprouts", "peanuts", "fish sauce"], "Main", ["egg", "peanuts", "fish"]),
    "paella": dish(520, ["rice", "saffron", "shrimp", "chicken", "squid", "peas"], "Main", ["shellfish"]),
    "pancakes": dish(350, ["flour", "milk", "egg", "butter", "maple syrup"], "Main", ["gluten", "dairy", "egg"]),
    "panna_cotta": dish(320, ["cream", "milk", "sugar", "gelatin", "vanilla"], "Dessert", ["dairy"]),
    "peking_duck": dish(480, ["duck", "pancakes", "hoisin", "scallions", "cucumber"], "Main", ["gluten"]),
    "pho": dish(320, ["rice noodles", "beef", "broth", "basil", "bean sprouts", "lime"], "Soup", ["gluten-free"]),
    "pizza": dish(480, ["dough", "tomato sauce", "mozzarella", "olive oil", "basil"], "Main", ["gluten", "dairy"]),
    "pork_chop": dish(420, ["pork chop", "butter", "garlic", "rosemary"], "Main", ["dairy"]),
    "poutine": dish(580, ["fries", "cheese curds", "gravy"], "Main", ["dairy", "gluten"]),
    "prime_rib": dish(700, ["beef rib roast", "rosemary", "garlic", "salt", "pepper"], "Main", []),
    "pulled_pork_sandwich": dish(450, ["pork shoulder", "bbq sauce", "bun", "coleslaw"], "Main", ["gluten"]),
    "ramen": dish(420, ["noodles", "broth", "pork belly", "egg", "scallions", "nori"], "Soup", ["gluten", "egg", "soy"]),
    "ravioli": dish(420, ["pasta", "ricotta", "spinach", "tomato sauce", "parmesan"], "Main", ["gluten", "dairy", "egg"]),
    "red_velvet_cake": dish(420, ["flour", "buttermilk", "cocoa", "butter", "cream cheese frosting"], "Dessert", ["gluten", "dairy", "egg"]),
    "risotto": dish(440, ["arborio rice", "chicken broth", "parmesan", "butter", "wine", "onion"], "Main", ["dairy"]),
    "samosa": dish(280, ["flour", "potatoes", "peas", "spices", "oil"], "Snack", ["gluten"]),
    "sashimi": dish(180, ["raw fish", "soy sauce", "wasabi", "ginger"], "Appetizer", ["fish", "soy"]),
    "scallops": dish(250, ["scallops", "butter", "garlic", "lemon"], "Main", ["shellfish", "dairy"]),
    "seaweed_salad": dish(130, ["seaweed", "sesame oil", "soy sauce", "rice vinegar"], "Salad", ["soy", "sesame"]),
    "shrimp_and_grits": dish(460, ["shrimp", "grits", "bacon", "cheddar", "butter", "lemon"], "Main", ["shellfish", "dairy"]),
    "spaghetti_bolognese": dish(520, ["spaghetti", "ground beef", "tomato sauce", "onion", "parmesan"], "Main", ["gluten", "dairy"]),
    "spaghetti_carbonara": dish(580, ["spaghetti", "eggs", "pancetta", "pecorino", "black pepper"], "Main", ["gluten", "egg", "dairy"]),
    "spring_rolls": dish(250, ["rice paper", "shrimp", "vegetables", "rice noodles", "dipping sauce"], "Appetizer", ["shellfish"]),
    "steak": dish(600, ["beef steak", "butter", "thyme", "garlic"], "Main", []),
    "strawberry_shortcake": dish(380, ["cake", "strawberries", "whipped cream", "sugar"], "Dessert", ["gluten", "dairy", "egg"]),
    "sushi": dish(320, ["rice", "raw fish", "seaweed", "soy sauce", "wasabi"], "Main", ["fish", "soy"]),
    "tacos": dish(400, ["tortilla", "beef", "lettuce", "cheese", "salsa", "cilantro"], "Main", ["gluten", "dairy"]),
    "takoyaki": dish(300, ["batter", "octopus", "scallions", "benito flakes", "takoyaki sauce"], "Snack", ["gluten", "shellfish", "egg"]),
    "tiramisu": dish(340, ["mascarpone", "ladyfingers", "coffee", "cocoa", "egg yolk"], "Dessert", ["dairy", "egg", "gluten"]),
    "tuna_tartare": dish(240, ["raw tuna", "sesame oil", "soy sauce", "avocado", "scallions"], "Appetizer", ["fish", "soy", "sesame"]),
    "waffles": dish(360, ["flour", "milk", "egg", "butter", "maple syrup"], "Main", ["gluten", "dairy", "egg"]),
}

HEADER = {
    "schema": "FoodLens ingredient knowledge base (approximations, not medical advice)",
    "num_classes": len(DB),
    "calories_units": "kcal per typical serving",
    "classes": DB,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(HEADER, indent=2), encoding="utf-8")
print(f"wrote {len(DB)} entries -> {OUT}")
missing = sorted({"apple_pie", "waffles"} - set(DB)) or []
print("done")