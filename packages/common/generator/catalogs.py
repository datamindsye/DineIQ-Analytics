"""Deterministic generator for reference catalogs, master records, and configuration entities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np

from packages.common.generator.config import GeneratorConfig
from packages.core.contracts.dataset_contract import (
    CANONICAL_CATEGORIES,
    DINING_TYPES,
)

CITIES_METRO: list[dict[str, Any]] = [
    {
        "city": "Chicago",
        "state": "IL",
        "postal": "60601",
        "lat": 41.881832,
        "lon": -87.623177,
        "tier": "urban",
    },
    {
        "city": "New York",
        "state": "NY",
        "postal": "10001",
        "lat": 40.712776,
        "lon": -74.005974,
        "tier": "urban",
    },
    {
        "city": "Los Angeles",
        "state": "CA",
        "postal": "90001",
        "lat": 34.052235,
        "lon": -118.243683,
        "tier": "urban",
    },
    {
        "city": "Houston",
        "state": "TX",
        "postal": "77001",
        "lat": 29.760427,
        "lon": -95.369804,
        "tier": "suburban",
    },
    {
        "city": "Phoenix",
        "state": "AZ",
        "postal": "85001",
        "lat": 33.448376,
        "lon": -112.074036,
        "tier": "suburban",
    },
    {
        "city": "Philadelphia",
        "state": "PA",
        "postal": "19101",
        "lat": 39.952583,
        "lon": -75.165222,
        "tier": "urban",
    },
    {
        "city": "San Antonio",
        "state": "TX",
        "postal": "78201",
        "lat": 29.424122,
        "lon": -98.493629,
        "tier": "suburban",
    },
    {
        "city": "San Diego",
        "state": "CA",
        "postal": "92101",
        "lat": 32.715736,
        "lon": -117.161087,
        "tier": "suburban",
    },
    {
        "city": "Dallas",
        "state": "TX",
        "postal": "75201",
        "lat": 32.776665,
        "lon": -96.796989,
        "tier": "urban",
    },
    {
        "city": "San Jose",
        "state": "CA",
        "postal": "95101",
        "lat": 37.338207,
        "lon": -121.886330,
        "tier": "suburban",
    },
    {
        "city": "Austin",
        "state": "TX",
        "postal": "78701",
        "lat": 30.267153,
        "lon": -97.743057,
        "tier": "urban",
    },
    {
        "city": "Jacksonville",
        "state": "FL",
        "postal": "32099",
        "lat": 30.332184,
        "lon": -81.655647,
        "tier": "suburban",
    },
    {
        "city": "Fort Worth",
        "state": "TX",
        "postal": "76101",
        "lat": 32.755489,
        "lon": -97.330765,
        "tier": "suburban",
    },
    {
        "city": "Columbus",
        "state": "OH",
        "postal": "43201",
        "lat": 39.961178,
        "lon": -82.998795,
        "tier": "suburban",
    },
    {
        "city": "Charlotte",
        "state": "NC",
        "postal": "28201",
        "lat": 35.227085,
        "lon": -80.843124,
        "tier": "suburban",
    },
    {
        "city": "Indianapolis",
        "state": "IN",
        "postal": "46201",
        "lat": 39.768402,
        "lon": -86.158066,
        "tier": "suburban",
    },
    {
        "city": "San Francisco",
        "state": "CA",
        "postal": "94101",
        "lat": 37.774929,
        "lon": -122.419418,
        "tier": "urban",
    },
    {
        "city": "Seattle",
        "state": "WA",
        "postal": "98101",
        "lat": 47.606209,
        "lon": -122.332069,
        "tier": "urban",
    },
    {
        "city": "Denver",
        "state": "CO",
        "postal": "80201",
        "lat": 39.739236,
        "lon": -104.990250,
        "tier": "suburban",
    },
    {
        "city": "Nashville",
        "state": "TN",
        "postal": "37201",
        "lat": 36.162663,
        "lon": -86.781601,
        "tier": "suburban",
    },
]

FIRST_NAMES: list[str] = [
    "James",
    "Mary",
    "John",
    "Patricia",
    "Robert",
    "Jennifer",
    "Michael",
    "Linda",
    "William",
    "Elizabeth",
    "David",
    "Barbara",
    "Richard",
    "Susan",
    "Joseph",
    "Jessica",
    "Thomas",
    "Sarah",
    "Charles",
    "Karen",
    "Christopher",
    "Nancy",
    "Daniel",
    "Lisa",
    "Matthew",
    "Betty",
    "Anthony",
    "Margaret",
    "Mark",
    "Sandra",
    "Donald",
    "Ashley",
    "Steven",
    "Kimberly",
    "Paul",
    "Emily",
    "Andrew",
    "Donna",
    "Joshua",
    "Michelle",
]

LAST_NAMES: list[str] = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Perez",
    "Thompson",
    "White",
    "Harris",
    "Sanchez",
    "Clark",
    "Ramirez",
    "Lewis",
    "Robinson",
    "Walker",
]

DISH_TEMPLATES: dict[str, list[tuple[str, float, float, int]]] = {
    "Appetizers": [
        ("Truffle Fries", 8.50, 2.20, 0),
        ("Buffalo Wings", 14.00, 4.20, 2),
        ("Calamari Fritti", 13.50, 4.00, 0),
        ("Artisan Garlic Bread", 6.50, 1.40, 0),
        ("Bruschetta Pomodoro", 9.00, 2.10, 0),
        ("Spinach Artichoke Dip", 11.50, 3.10, 0),
        ("Loaded Potato Skins", 10.00, 2.80, 0),
        ("Spicy Edamame", 7.00, 1.50, 2),
        ("Pork Potstickers", 11.00, 3.20, 1),
        ("Crispy Mozzarella Bites", 9.50, 2.40, 0),
        ("Shrimp Cocktail", 16.00, 6.00, 0),
        ("Duck Spring Rolls", 12.50, 3.80, 1),
        ("Avocado Tartare", 13.00, 3.50, 0),
        ("Stuffed Mushrooms", 10.50, 2.90, 0),
        ("Charcuterie Board", 22.00, 8.50, 0),
    ],
    "Entrees": [
        ("Prime Wagyu Burger", 18.50, 6.50, 0),
        ("Pan Seared Salmon", 26.00, 9.00, 0),
        ("Ribeye Steak 12oz", 34.00, 13.50, 0),
        ("Roasted Half Chicken", 21.00, 6.20, 0),
        ("Braised Beef Short Ribs", 29.50, 11.00, 0),
        ("Grilled Pork Chop", 23.00, 7.20, 0),
        ("Mediterranean Lamb Chops", 32.00, 12.00, 0),
        ("Crispy Duck Breast", 28.00, 10.00, 0),
        ("BBQ Smoked Brisket", 25.00, 9.50, 1),
        ("Vegetarian Grain Bowl", 16.00, 3.80, 0),
        ("Stuffed Bell Peppers", 17.50, 4.20, 0),
        ("Pan Roasted Sea Bass", 33.00, 12.50, 0),
        ("Chicken Parmesan Classic", 20.00, 5.80, 0),
        ("Beef Tenderloin Medallions", 36.00, 14.00, 0),
        ("Herb Crusted Halibut", 31.00, 11.50, 0),
    ],
    "Seafood Specialties": [
        ("Lobster Tail Thermidor", 42.00, 18.00, 0),
        ("Grilled Jumbo Shrimp", 25.00, 8.50, 1),
        ("Crispy Beer Battered Cod", 18.00, 5.50, 0),
        ("Seafood Paella", 30.00, 11.00, 1),
        ("Chilean Sea Bass", 35.00, 14.00, 0),
        ("Blackened Ahi Tuna", 27.00, 9.80, 2),
        ("Scallop Risotto", 29.00, 10.50, 0),
        ("Maryland Crab Cakes", 28.00, 11.00, 0),
        ("Mussels White Wine Garlic", 19.50, 6.20, 0),
        ("Grilled Octopus", 24.00, 8.20, 1),
        ("Fish and Chips Traditional", 17.00, 5.20, 0),
        ("Spicy Crab Boil", 32.00, 12.50, 3),
        ("Clam Linguine", 22.00, 6.80, 0),
        ("Oysters Rockerfeller", 26.00, 9.50, 0),
        ("Crispy Fried Calamari Basket", 16.50, 5.00, 1),
    ],
    "Pasta & Noodles": [
        ("Fettuccine Alfredo", 17.00, 4.00, 0),
        ("Spaghetti Carbonara", 19.00, 4.80, 0),
        ("Penne all Arrabbiata", 16.00, 3.20, 3),
        ("Rigatoni Bolognese", 21.00, 5.90, 0),
        ("Truffle Mushroom Tagliatelle", 23.00, 6.80, 0),
        ("Pad Thai Chicken", 16.50, 4.20, 2),
        ("Beef Pho Noodle Soup", 15.50, 3.90, 1),
        ("Ramen Tonkotsu", 16.00, 4.10, 1),
        ("Lobster Ravioli", 27.00, 9.50, 0),
        ("Four Cheese Lasagna", 18.50, 4.70, 0),
        ("Spicy Dan Dan Noodles", 15.00, 3.50, 3),
        ("Gnocchi Gorgonzola", 19.50, 5.20, 0),
        ("Singapore Street Noodles", 16.00, 3.80, 2),
        ("Pappardelle Wild Boar", 24.00, 7.50, 0),
        ("Shrimp Scampi Angel Hair", 22.50, 6.80, 0),
    ],
    "Sandwiches & Burgers": [
        ("Classic Bacon Cheeseburger", 15.00, 4.50, 0),
        ("Smoked Pulled Pork Bun", 14.50, 4.10, 1),
        ("Crispy Buttermilk Chicken Bun", 14.00, 3.80, 2),
        ("Philly Cheesesteak", 16.50, 5.20, 0),
        ("French Dip Baguette", 17.00, 5.50, 0),
        ("Reuben Sandwich on Rye", 15.50, 4.80, 0),
        ("Grilled Portobello Burger", 13.50, 3.20, 0),
        ("Black Bean Quinoa Burger", 13.00, 3.00, 1),
        ("Double Smashed Cheeseburger", 16.00, 5.00, 0),
        ("Turkey Avocado Club", 14.50, 4.20, 0),
        ("Nashville Hot Chicken Sandwich", 15.00, 4.20, 4),
        ("Cubano Toasted Sandwich", 15.50, 4.60, 0),
        ("Truffle Swiss Burger", 17.50, 5.80, 0),
        ("Spicy Italian Grinder", 14.00, 4.00, 2),
        ("Lobster Roll New England", 26.00, 10.50, 0),
    ],
    "Side Dishes": [
        ("Creamed Spinach", 6.50, 1.50, 0),
        ("Garlic Mashed Potatoes", 5.50, 1.20, 0),
        ("Grilled Asparagus", 7.50, 2.00, 0),
        ("Roasted Brussels Sprouts", 7.00, 1.80, 0),
        ("Crispy Onion Rings", 6.00, 1.40, 0),
        ("House Caesar Salad Side", 6.50, 1.50, 0),
        ("Sweet Potato Wedges", 6.00, 1.30, 0),
        ("Steamed Seasonal Vegetables", 5.50, 1.20, 0),
        ("Macaroni & Cheese Bowl", 8.00, 2.20, 0),
        ("Charred Corn Elote", 6.50, 1.60, 1),
        ("Cole Slaw Creamy", 4.50, 0.90, 0),
        ("Sauteed Wild Mushrooms", 8.50, 2.50, 0),
        ("Tater Tots Seasoned", 5.50, 1.10, 0),
        ("Basmati Fragrant Rice", 4.50, 0.80, 0),
        ("Quinoa Pilaf Herb", 6.00, 1.40, 0),
    ],
    "Desserts": [
        ("Molten Chocolate Lava Cake", 9.50, 2.40, 0),
        ("New York Cheesecake", 8.50, 2.10, 0),
        ("Classic Tiramisu", 9.00, 2.30, 0),
        ("Vanilla Bean Creme Brulee", 8.50, 2.00, 0),
        ("Warm Apple Crisp Tart", 8.00, 1.80, 0),
        ("Churros with Dulce de Leche", 7.50, 1.60, 0),
        ("Key Lime Pie", 8.00, 1.90, 0),
        ("Gelato Tasting Trio", 7.00, 1.50, 0),
        ("Pecan Bourbon Tart", 9.00, 2.40, 0),
        ("Sticky Toffee Pudding", 8.50, 2.10, 0),
        ("Chocolate Raspberry Mousse", 8.50, 2.20, 0),
        ("Matcha Green Tea Crepe Cake", 9.50, 2.60, 0),
        ("Berry Pavlova Nest", 8.00, 1.90, 0),
        ("Banana Foster Bread Pudding", 8.50, 2.00, 0),
        ("Sorbet Trio Citrus", 6.50, 1.30, 0),
    ],
    "Non-Alcoholic Beverages": [
        ("Fresh Pressed Lemonade", 4.50, 0.60, 0),
        ("Cold Brew Iced Coffee", 5.00, 0.80, 0),
        ("Artisan Sparkling Water", 4.00, 0.50, 0),
        ("Peach Iced Tea Brewed", 4.00, 0.50, 0),
        ("Ginger Beer Crafted", 4.50, 0.70, 0),
        ("Mango Mint Aqua Fresca", 5.00, 0.90, 0),
        ("Matcha Iced Latte", 5.50, 1.10, 0),
        ("Italian Soda Blood Orange", 4.50, 0.70, 0),
        ("Hot Cocoa Marshmallow", 4.50, 0.70, 0),
        ("Loose Leaf Herbal Tea Pot", 4.50, 0.50, 0),
        ("Espresso Double Shot", 4.00, 0.60, 0),
        ("Cappuccino Froth", 5.00, 0.90, 0),
        ("Berry Hibiscus Cooler", 5.00, 0.80, 0),
        ("Coconut Lime Soda", 4.50, 0.70, 0),
        ("Arnold Palmer Half and Half", 4.00, 0.50, 0),
    ],
    "Bar & Cocktails": [
        ("Smoked Old Fashioned", 14.50, 2.80, 0),
        ("Spicy Mezcalita", 13.50, 2.60, 2),
        ("Signature Espresso Martini", 14.00, 2.70, 0),
        ("Classic Dry Gin Martini", 13.00, 2.40, 0),
        ("Moscow Mule Copper Mug", 12.00, 2.10, 0),
        ("Aperol Spritz Prosecco", 12.50, 2.30, 0),
        ("Kentucky Bourbon Sour", 13.00, 2.50, 0),
        ("Craft Hazy IPA Draft", 8.00, 1.60, 0),
        ("Crisp Pilsner Draft", 7.00, 1.30, 0),
        ("Pinot Noir Sonoma Glass", 13.00, 3.20, 0),
        ("Cabernet Sauvignon Napa Glass", 15.00, 3.90, 0),
        ("Sauvignon Blanc Marlborough Glass", 12.00, 2.80, 0),
        ("Chardonnay Oak Reserve Glass", 13.00, 3.00, 0),
        ("Prosecco Brut Sparkling Glass", 11.00, 2.40, 0),
        ("Sangria Pitcher Shareable", 28.00, 6.00, 0),
    ],
    "Chef Specials": [
        ("Tomahawk Ribeye 32oz for Two", 95.00, 38.00, 0),
        ("Whole Roasted Crispy Branzino", 38.00, 14.00, 0),
        ("A5 Miyazaki Wagyu Strip 6oz", 75.00, 28.00, 0),
        ("Black Truffle Handmade Risotto", 32.00, 9.50, 0),
        ("Pan Roasted Rack of Venison", 44.00, 17.00, 0),
        ("Maine Seafood Tower Deluxe", 85.00, 35.00, 0),
        ("Duck Confit Cassoulet", 34.00, 12.00, 0),
        ("Pan Seared Turbot Fillet", 42.00, 16.00, 0),
        ("Veal Chop Milanese Bone In", 40.00, 15.00, 0),
        ("Seared Foie Gras Brioche", 29.00, 11.00, 0),
        ("Whole Stuffed Maine Lobster", 55.00, 22.00, 0),
        ("Osso Buco Saffron Risotto", 39.00, 14.50, 0),
        ("Spanish Iberian Pork Secreto", 36.00, 13.50, 0),
        ("Truffled Wild Morel Pasta", 34.00, 10.50, 0),
        ("Chef Seven Course Tasting Preview", 110.00, 40.00, 0),
    ],
}

RAW_INGREDIENTS: list[tuple[str, str, str, float]] = [
    ("Ground Wagyu Beef", "Meat & Poultry", "kg", 12.50),
    ("Prime Ribeye Loins", "Meat & Poultry", "kg", 24.00),
    ("Chicken Breast Free Range", "Meat & Poultry", "kg", 7.20),
    ("Pork Shoulder Bone-in", "Meat & Poultry", "kg", 6.50),
    ("Atlantic Salmon Fillets", "Meat & Poultry", "kg", 18.00),
    ("Jumbo Shrimp 16/20", "Meat & Poultry", "kg", 16.50),
    ("Maine Lobster Tails", "Meat & Poultry", "kg", 38.00),
    ("Russet Potatoes", "Produce", "kg", 1.20),
    ("Fresh Asparagus", "Produce", "kg", 4.50),
    ("Roma Tomatoes", "Produce", "kg", 2.20),
    ("Fresh Mozzarella Log", "Dairy", "kg", 7.80),
    ("Heavy Cream 36%", "Dairy", "L", 4.20),
    ("Parmigiano Reggiano Wheel", "Dairy", "kg", 22.00),
    ("Extra Virgin Olive Oil", "Dry Goods", "L", 8.50),
    ("Semolina Flour 50lb", "Dry Goods", "kg", 1.10),
    ("Arborio Rice", "Dry Goods", "kg", 2.80),
    ("Coffee Beans Whole Espresso", "Beverage Supplies", "kg", 14.00),
    ("Bio-degradable Takeaway Box", "Packaging", "units", 0.35),
    ("Paper Drink Cups 16oz", "Packaging", "units", 0.15),
    ("Napkins Recycled Case", "Packaging", "boxes", 22.00),
]


def generate_menu_categories(
    config: GeneratorConfig, rng: np.random.Generator
) -> list[dict[str, Any]]:
    """Generate 10 canonical menu category records."""
    categories: list[dict[str, Any]] = []
    base_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    for idx, cat_name in enumerate(CANONICAL_CATEGORIES, start=1):
        source_id = f"CAT-{idx:03d}"
        categories.append(
            {
                "source_category_id": source_id,
                "category_name": cat_name,
                "description": f"Standard culinary category for {cat_name.lower()}",
                "display_order": idx,
                "is_active": True,
                "created_at": base_time,
            }
        )
    return categories


def generate_restaurants(config: GeneratorConfig, rng: np.random.Generator) -> list[dict[str, Any]]:
    """Generate restaurant branches with realistic capacities, locations, and dining types."""
    restaurants: list[dict[str, Any]] = []
    target_count = config.scale.num_restaurants
    base_date = config.start_date - timedelta(days=365)
    base_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    for idx in range(1, target_count + 1):
        metro = CITIES_METRO[(idx - 1) % len(CITIES_METRO)]
        dining_type = DINING_TYPES[(idx - 1) % len(DINING_TYPES)]

        # Urban flagships have higher capacity
        if metro["tier"] == "urban":
            capacity = int(rng.integers(120, 220))
        else:
            capacity = int(rng.integers(60, 130))

        mgr_first = FIRST_NAMES[(idx * 3) % len(FIRST_NAMES)]
        mgr_last = LAST_NAMES[(idx * 7) % len(LAST_NAMES)]

        restaurants.append(
            {
                "source_restaurant_id": f"REST-{idx:04d}",
                "location_name": f"{metro['city']} {dining_type} #{idx}",
                "city": metro["city"],
                "state_region": metro["state"],
                "postal_code": metro["postal"],
                "seating_capacity": capacity,
                "dining_type": dining_type,
                "manager_name": f"{mgr_first} {mgr_last}",
                "opening_date": base_date + timedelta(days=int(rng.integers(0, 180))),
                "latitude": metro["lat"],
                "longitude": metro["lon"],
                "is_active": True,
                "created_at": base_time,
            }
        )
    return restaurants


def generate_menu_items(
    config: GeneratorConfig,
    categories: list[dict[str, Any]],
    rng: np.random.Generator,
) -> list[dict[str, Any]]:
    """Generate dish catalog matching BCG quadrants (Stars, Plowhorses, Puzzles, Dogs)."""
    items: list[dict[str, Any]] = []
    target_count = config.scale.num_menu_items
    base_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    item_idx = 1
    # Distribute items evenly across the 10 canonical categories
    while item_idx <= target_count:
        for cat in categories:
            if item_idx > target_count:
                break
            cat_name = cat["category_name"]
            templates = DISH_TEMPLATES.get(cat_name, DISH_TEMPLATES["Entrees"])
            template_idx = (item_idx - 1) % len(templates)
            name, base_price, base_cost, spice = templates[template_idx]

            # Modulate pricing for variety if repeating templates
            cycle = (item_idx - 1) // len(templates)
            if cycle > 0:
                name = f"{name} Style {cycle + 1}"
                base_price = round(base_price * (1.0 + 0.1 * cycle), 2)
                base_cost = round(base_cost * (1.0 + 0.08 * cycle), 2)

            is_seasonal = item_idx % 8 == 0
            allergens = (
                "Gluten, Dairy"
                if item_idx % 3 == 0
                else ("Seafood" if "Seafood" in cat_name else None)
            )

            items.append(
                {
                    "source_menu_item_id": f"DISH-{item_idx:04d}",
                    "source_category_id": cat["source_category_id"],
                    "item_name": name,
                    "description": f"Freshly crafted {name.lower()} prepared to order.",
                    "current_base_price": float(base_price),
                    "current_base_cost": float(base_cost),
                    "prep_time_minutes": int(rng.integers(8, 25)),
                    "is_seasonal": is_seasonal,
                    "is_active": True,
                    "spiciness_level": spice,
                    "allergens": allergens,
                    "created_at": base_time,
                }
            )
            item_idx += 1
    return items


def generate_pricing_history(
    config: GeneratorConfig,
    menu_items: list[dict[str, Any]],
    rng: np.random.Generator,
) -> list[dict[str, Any]]:
    """Generate Slowly Changing Dimension Type 2 price and cost changes over the timeline."""
    history: list[dict[str, Any]] = []
    target_count = config.scale.num_pricing_history
    start_dt = datetime.combine(config.start_date, datetime.min.time(), tzinfo=timezone.utc)
    prc_idx = 1

    # First, baseline launch record for each menu item
    for item in menu_items:
        current_p = item["current_base_price"]
        current_c = item["current_base_cost"]
        # 30% of items had a cheaper introductory price earlier in history
        had_earlier_price = int(item["source_menu_item_id"].split("-")[1]) % 3 == 0

        if had_earlier_price and prc_idx < target_count:
            # Historical prior record
            prior_p = round(current_p * 0.90, 2)
            prior_c = round(current_c * 0.88, 2)
            split_dt = start_dt + timedelta(days=int(rng.integers(60, 180)))

            history.append(
                {
                    "source_pricing_history_id": f"PRC-{prc_idx:06d}",
                    "source_menu_item_id": item["source_menu_item_id"],
                    "source_restaurant_id": None,
                    "base_price": prior_p,
                    "base_cost": prior_c,
                    "effective_from": start_dt - timedelta(days=90),
                    "effective_to": split_dt,
                    "change_reason": "Introductory catalog launch pricing",
                    "created_at": start_dt - timedelta(days=90),
                }
            )
            prc_idx += 1

            # Current active record
            history.append(
                {
                    "source_pricing_history_id": f"PRC-{prc_idx:06d}",
                    "source_menu_item_id": item["source_menu_item_id"],
                    "source_restaurant_id": None,
                    "base_price": current_p,
                    "base_cost": current_c,
                    "effective_from": split_dt,
                    "effective_to": None,
                    "change_reason": "Supply chain ingredient inflation adjustment",
                    "created_at": split_dt,
                }
            )
            prc_idx += 1
        else:
            # Single continuous price
            history.append(
                {
                    "source_pricing_history_id": f"PRC-{prc_idx:06d}",
                    "source_menu_item_id": item["source_menu_item_id"],
                    "source_restaurant_id": None,
                    "base_price": current_p,
                    "base_cost": current_c,
                    "effective_from": start_dt - timedelta(days=180),
                    "effective_to": None,
                    "change_reason": "Catalog standard baseline price",
                    "created_at": start_dt - timedelta(days=180),
                }
            )
            prc_idx += 1

        if prc_idx > target_count and len(history) >= len(menu_items):
            break

    # If target_count is larger, generate branch-specific and seasonal pricing adjustments
    rest_count = config.scale.num_restaurants
    while prc_idx <= target_count:
        item = menu_items[(prc_idx - 1) % len(menu_items)]
        current_p = item["current_base_price"]
        current_c = item["current_base_cost"]

        rest_id = f"REST-{((prc_idx % rest_count) + 1):04d}" if rest_count > 0 else None
        adjusted_p = round(current_p * float(rng.choice([1.05, 1.08, 0.95, 1.10])), 2)
        adjusted_c = round(current_c * float(rng.choice([1.02, 1.05, 0.98])), 2)

        start_day = int(rng.integers(30, max(31, config.scale.history_days - 60)))
        from_dt = start_dt + timedelta(days=start_day)
        to_dt = from_dt + timedelta(days=int(rng.integers(14, 60)))

        reasons = [
            "Urban flagship location premium tier",
            "Seasonal summer menu repricing",
            "Local branch operational overhead adjustment",
            "Holiday promotional dining window",
            "Chef specialty kitchen test rate",
        ]

        history.append(
            {
                "source_pricing_history_id": f"PRC-{prc_idx:06d}",
                "source_menu_item_id": item["source_menu_item_id"],
                "source_restaurant_id": rest_id,
                "base_price": adjusted_p,
                "base_cost": adjusted_c,
                "effective_from": from_dt,
                "effective_to": to_dt,
                "change_reason": reasons[prc_idx % len(reasons)],
                "created_at": from_dt,
            }
        )
        prc_idx += 1

    return history[:target_count]


def generate_promotions(
    config: GeneratorConfig,
    menu_items: list[dict[str, Any]],
    categories: list[dict[str, Any]],
    rng: np.random.Generator,
) -> list[dict[str, Any]]:
    """Generate marketing campaigns including standard discounts and intentional promo traps."""
    promotions: list[dict[str, Any]] = []
    target_count = config.scale.num_promotions
    base_date = config.start_date
    promo_trap_count = config.anomalies.promotion_trap_count if config.enable_anomalies else 0

    campaign_themes = [
        ("Summer Kickoff Special", "SUMMER25", "Percentage", 15.00, 30),
        ("Lunchtime Combo Saver", "LUNCHDEAL", "Fixed Amount", 3.50, 45),
        ("Weekend Feast Coupon", "WEEKEND10", "Percentage", 10.00, 60),
        ("Appetizer Bonanza BOGO", "BOGOAPPS", "Buy One Get One", 100.00, 21),
        ("Chef Tasting Experience", "CHEFVIP", "Fixed Amount", 15.00, 30),
        ("Holiday Family Bundle", "HOLIDAY20", "Percentage", 20.00, 40),
        ("Autumn Harvest Discount", "FALLHARVEST", "Fixed Amount", 5.00, 30),
        ("Direct Delivery Incentive", "DELIVERFREE", "Fixed Amount", 4.00, 60),
    ]

    for idx in range(1, target_count + 1):
        theme_idx = (idx - 1) % len(campaign_themes)
        name, code, d_type, d_val, duration = campaign_themes[theme_idx]

        # Is this one of the designated promotion traps?
        is_trap = idx <= promo_trap_count
        if is_trap:
            name = f"Extreme Deep Discount Promo Trap #{idx}"
            code = f"TRAP{idx * 50}"
            d_type = "Percentage"
            d_val = 50.00  # 50% discount triggers negative margin trap on high cost dishes

        start_offset = int((idx - 1) * (config.scale.history_days // max(1, target_count)))
        promo_start = base_date + timedelta(days=start_offset)
        promo_end = promo_start + timedelta(days=duration)

        linked_dish = (
            menu_items[(idx * 3) % len(menu_items)]["source_menu_item_id"] if idx % 2 == 0 else None
        )
        linked_cat = (
            categories[(idx * 2) % len(categories)]["source_category_id"]
            if not linked_dish
            else None
        )

        promotions.append(
            {
                "source_promotion_id": f"PROMO-{idx:04d}",
                "campaign_name": name,
                "promo_code": code,
                "discount_type": d_type,
                "discount_value": float(d_val),
                "start_date": promo_start,
                "end_date": promo_end,
                "minimum_order_amount": 25.00 if is_trap else 15.00,
                "source_category_id": linked_cat,
                "source_menu_item_id": linked_dish,
                "applicable_channel": "Delivery Direct" if idx % 3 == 0 else None,
                "is_active": True,
                "is_misleading": is_trap,
                "created_at": datetime.combine(
                    promo_start - timedelta(days=7), datetime.min.time(), tzinfo=timezone.utc
                ),
            }
        )
    return promotions


def generate_customers(config: GeneratorConfig, rng: np.random.Generator) -> list[dict[str, Any]]:
    """Generate customer profiles with loyalty tiers, contact info, and realistic missing data."""
    customers: list[dict[str, Any]] = []
    target_count = config.scale.num_customers
    start_date = config.start_date
    history_days = config.scale.history_days

    # Tier probability distribution: Bronze (40%), Silver (25%), Gold (15%), Platinum (5%), None (15%)
    tier_choices = ["Bronze", "Silver", "Gold", "Platinum", "None"]
    tier_probs = [0.40, 0.25, 0.15, 0.05, 0.15]
    channel_choices = ["Dine-in", "Takeaway", "Delivery Direct", "Delivery Aggregator"]

    missing_contact_rate = (
        config.anomalies.missing_customer_contact_rate if config.enable_anomalies else 0.0
    )

    for idx in range(1, target_count + 1):
        first_name = FIRST_NAMES[int(rng.integers(0, len(FIRST_NAMES)))]
        last_name = LAST_NAMES[int(rng.integers(0, len(LAST_NAMES)))]
        reg_offset = int(rng.integers(-365, history_days))
        reg_date = start_date + timedelta(days=reg_offset)

        tier = str(rng.choice(tier_choices, p=tier_probs))
        pref_channel = str(rng.choice(channel_choices))
        city = CITIES_METRO[int(rng.integers(0, len(CITIES_METRO)))]["city"]

        # Inject realistic missing values
        has_missing_contact = rng.random() < missing_contact_rate
        email = (
            None
            if has_missing_contact and idx % 2 == 0
            else f"{first_name.lower()}.{last_name.lower()}{idx}@example.com"
        )
        phone = (
            None
            if has_missing_contact and idx % 2 != 0
            else f"+1-555-{int(rng.integers(100, 999)):03d}-{int(rng.integers(1000, 9999)):04d}"
        )

        customers.append(
            {
                "source_customer_id": f"CUST-{idx:08d}",
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "registration_date": reg_date,
                "loyalty_tier": tier,
                "preferred_channel": pref_channel,
                "home_city": city,
                "is_active": True,
                "created_at": datetime.combine(reg_date, datetime.min.time(), tzinfo=timezone.utc),
            }
        )
    return customers


def generate_inventory(
    config: GeneratorConfig,
    restaurants: list[dict[str, Any]],
    rng: np.random.Generator,
) -> list[dict[str, Any]]:
    """Generate tracked ingredient stock balances per restaurant location."""
    inventory: list[dict[str, Any]] = []
    target_count = config.scale.num_inventory_records
    base_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    inv_idx = 1
    items_per_rest = max(1, target_count // len(restaurants))
    for rest in restaurants:
        rest_idx = int(rest["source_restaurant_id"].split("-")[1])
        cycle = 0
        for item_in_rest in range(items_per_rest):
            if inv_idx > target_count:
                break
            raw_idx = item_in_rest % len(RAW_INGREDIENTS)
            if raw_idx == 0 and item_in_rest > 0:
                cycle += 1

            base_name, cat, uom, cost = RAW_INGREDIENTS[raw_idx]
            ing_name = base_name if cycle == 0 else f"{base_name} Select #{cycle + 1}"

            stock = round(float(rng.uniform(20.0, 150.0)), 2)
            threshold = round(stock * 0.30, 2)
            reorder_qty = round(stock * 0.60, 2)

            inventory.append(
                {
                    "source_inventory_id": f"INV-REST{rest_idx:02d}-{inv_idx:04d}",
                    "source_restaurant_id": rest["source_restaurant_id"],
                    "ingredient_name": ing_name,
                    "ingredient_category": cat,
                    "current_stock_quantity": stock,
                    "unit_of_measure": uom,
                    "reorder_threshold": threshold,
                    "reorder_quantity": reorder_qty,
                    "unit_purchase_cost": cost,
                    "last_restock_date": config.start_date
                    + timedelta(days=int(rng.integers(0, 30))),
                    "created_at": base_time,
                    "updated_at": base_time,
                }
            )
            inv_idx += 1

    return inventory
