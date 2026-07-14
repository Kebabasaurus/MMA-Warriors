import os
import sys
from pathlib import Path


BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent))
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
ASSET_DIR = BUNDLE_DIR / "assets" if (BUNDLE_DIR / "assets").exists() else APP_DIR / "assets"
APP_ICON_ICO = ASSET_DIR / "app_icon.ico"
APP_ICON_PNG = ASSET_DIR / "app_icon.png"
GAME_NAME = "MMA Warriors"


def _select_data_dir():
    """Keep portable builds self-contained, with a safe fallback for protected folders."""
    probe = APP_DIR / ".mma_warriors_write_test"
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        probe.write_text("ok", encoding="ascii")
        probe.unlink(missing_ok=True)
        return APP_DIR
    except OSError:
        fallback_root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        fallback = fallback_root / GAME_NAME
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


DATA_DIR = _select_data_dir()
SAVE_FILE = DATA_DIR / "savegame.json"
SAVE_DIR = DATA_DIR / "Saves"
DATABASE_DIR = DATA_DIR / "Databases"
LOG_DIR = DATA_DIR / "Logs"
CRASH_DIR = LOG_DIR / "Crashes"
PLAYER_PROMOTION_NAME = "BAMMA"
WEIGHTS = ["Flyweight", "Bantamweight", "Featherweight", "Lightweight", "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"]
WEIGHT_LIMITS = {
    "Flyweight": 125,
    "Bantamweight": 135,
    "Featherweight": 145,
    "Lightweight": 155,
    "Welterweight": 170,
    "Middleweight": 185,
    "Light Heavyweight": 205,
    "Heavyweight": 265,
}
REGIONS = ["USA", "Canada", "Brazil", "Mexico", "UK", "Europe", "Japan", "Australia", "Asia"]
# These are world-market buckets rather than passports.  They keep generated
# fighters rooted in a believable local scene while still allowing realistic
# migration between neighbouring and culturally connected markets.
REGIONAL_MIGRATION_LINKS = {
    "USA": ["Canada", "Mexico", "Brazil", "UK", "Europe"],
    "Canada": ["USA", "UK", "Europe"],
    "Brazil": ["USA", "Mexico", "Europe"],
    "Mexico": ["USA", "Canada", "Brazil"],
    "UK": ["Europe", "USA", "Canada", "Australia"],
    "Europe": ["UK", "USA", "Canada", "Asia"],
    "Japan": ["Asia", "Australia", "USA"],
    "Australia": ["New Zealand", "Asia", "UK", "USA"],
    "Asia": ["Japan", "Australia", "Europe", "USA"],
}
REGION_COUNTRIES = {
    "USA": "United States", "Canada": "Canada", "Brazil": "Brazil", "Mexico": "Mexico",
    "UK": "United Kingdom", "Europe": "Europe", "Japan": "Japan", "Australia": "Australia",
    "Asia": "Asia", "New Zealand": "New Zealand", "Africa": "Africa",
}
REGION_CITIES = {
    "USA": ["Las Vegas", "New York", "Los Angeles", "Dallas", "Miami", "Chicago"],
    "Canada": ["Toronto", "Montreal", "Vancouver", "Calgary"],
    "Brazil": ["Rio de Janeiro", "Sao Paulo", "Curitiba", "Brasilia"],
    "Mexico": ["Mexico City", "Guadalajara", "Monterrey", "Tijuana"],
    "UK": ["London", "Manchester", "Liverpool", "Cardiff", "Glasgow"],
    "Europe": ["Paris", "Berlin", "Warsaw", "Dublin", "Madrid", "Amsterdam"],
    "Japan": ["Tokyo", "Osaka", "Saitama", "Yokohama"],
    "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth"],
    "Asia": ["Bangkok", "Phuket", "Singapore", "Manila", "Seoul"],
}
REGION_PROMO_BENEFITS = {
    "USA": {"media": 1.12, "gate": 1.10, "morale": 2},
    "Canada": {"media": 1.02, "gate": 1.04, "morale": 2},
    "Brazil": {"media": 1.06, "gate": 1.08, "morale": 3},
    "Mexico": {"media": 1.04, "gate": 1.05, "morale": 3},
    "UK": {"media": 1.05, "gate": 1.06, "morale": 2},
    "Europe": {"media": 1.02, "gate": 1.03, "morale": 2},
    "Japan": {"media": 1.03, "gate": 1.07, "morale": 3},
    "Australia": {"media": 1.03, "gate": 1.05, "morale": 2},
    "Asia": {"media": 1.04, "gate": 1.06, "morale": 3},
}
CARD_TIERS = ["Main Card", "Prelims", "Early Prelims"]
STYLES = [
    "Boxer", "Kickboxer", "Dutch Kickboxer", "Muay Thai", "Karate", "Taekwondo", "Sanda",
    "Wrestler", "Freestyle Wrestler", "Catch Wrestler", "BJJ", "Luta Livre", "Sambo", "Judo",
    "Grappler", "Submission Grappler", "Well-Rounded", "MMA Generalist",
]
TRAITS = [
    "Fan Favourite", "Fragile", "Clutch", "Slow Starter", "Big Finisher", "Marketable", "Gym Rat", "Erratic",
    "Weight Bully", "Cardio Machine", "Fast Starter", "Comeback Artist", "Iron Chin", "Glass Cannon",
    "Submission Ace", "Knockout Artist", "Pressure Fighter", "Counter Specialist", "Showman", "Trash Talker",
    "Quiet Professional", "Coach Favourite", "Bad Weight Cut", "Injury Magnet", "Media Natural", "Gym Leader",
    "Front Runner", "Late Bloomer", "Veteran Savvy", "Prospect Mindset", "Short Notice Hero", "Title Mentality",
    "Technical Learner", "Warrior Spirit", "Fast Healer", "Slow Healer",
    "Adaptable", "Momentum Fighter", "Regional Star", "Overlooked Talent", "Body Hunter", "Leg Kicker",
    "Cage Specialist", "Elbow Specialist", "Scramble Artist", "Fight Finisher",
]
BEHAVIOURS = ["Pressure", "Counter", "Volume", "Control", "Submission Hunter", "Sprawl And Brawl", "Dynamic Attacker", "Cautious"]
POSITIONS = ["range", "pocket", "clinch", "cage", "guard", "half guard", "side control", "mount", "back control"]
CAMPS = [
    "Independent", "Iron Vale", "Blackstone MMA", "Nova Uniao", "Sakuraba Dojo", "Northstar Combat",
    "Kings Road", "Altitude Fight Team", "American Top Team", "AKA", "City Kickboxing",
    "Team Alpha Male", "Tiger Muay Thai", "Chute Boxe", "Tristar", "Jackson Wink",
    "Shootbox Japan", "London Shootfighters", "Mexico City Combat", "Sydney Elite MMA",
]
CAMP_QUALITY = {
    "Independent": 42,
    "Iron Vale": 58,
    "Blackstone MMA": 72,
    "Nova Uniao": 84,
    "Sakuraba Dojo": 76,
    "Northstar Combat": 68,
    "Kings Road": 63,
    "Altitude Fight Team": 79,
    "American Top Team": 88,
    "AKA": 86,
    "City Kickboxing": 87,
    "Team Alpha Male": 82,
    "Tiger Muay Thai": 84,
    "Chute Boxe": 83,
    "Tristar": 82,
    "Jackson Wink": 80,
    "Shootbox Japan": 78,
    "London Shootfighters": 77,
    "Mexico City Combat": 74,
    "Sydney Elite MMA": 76,
    "Ultimate Fighting Championship": 82,
    "Professional Fighters League": 74,
    "Cage Warriors": 66,
    "ONE Championship": 78,
    "RIZIN Fighting Federation": 72,
    "KSW": 70,
    "Legacy Fighting Alliance": 62,
    "Oktagon MMA": 70,
    "BRAVE Combat Federation": 64,
    "Absolute Championship Akhmat": 66,
    "BAMMA": 66,
    "UFC": 82,
    "PFL": 74,
}
FIRST_NAMES = ["Adam", "Alex", "Andre", "Anton", "Arman", "Bruno", "Caleb", "Carlos", "Cesar", "Damon", "Diego", "Dorian", "Ethan", "Felix", "Gabe", "Gareth", "Hector", "Ibrahim", "Ivan", "Jalen", "Jonas", "Kaito", "Khalil", "Leon", "Luca", "Mateo", "Mikael", "Niko", "Omar", "Pavel", "Rafael", "Rashad", "Renato", "Samir", "Santiago", "Silas", "Tariq", "Theo", "Thiago", "Viktor", "Yuri", "Zane",
    "Aaron", "Adrian", "Ahmad", "Aleksandr", "Alvaro", "Amir", "Antonio", "Artur", "Basir", "Benjamin", "Brandon", "Cameron", "Damian", "Daniel", "Dario", "Declan", "Dominic", "Eduardo", "Elias", "Emre", "Enzo", "Farid", "Fernando", "Francis", "Gabriel", "Gideon", "Hamza", "Hugo", "Ismael", "Jackson", "Jamal", "Javier", "Joaquin", "Karim", "Kieran", "Lachlan", "Lorenzo", "Luis", "Malik", "Marco", "Marcus", "Martin", "Mauricio", "Miguel", "Nabil", "Nathan", "Nelson", "Noah", "Oleg", "Patrick", "Quentin", "Raul", "Reece", "Ricardo", "Roman", "Ruben", "Ryan", "Salvatore", "Scott", "Sean", "Sergio", "Stefan", "Terrence", "Tomas", "Trevor", "Usman", "Valerio", "Vicente", "Wade", "Wesley", "Xavier", "Youssef", "Zachary", "Abdi", "Bilal", "Chinedu", "Daoud", "Eamon", "Farhan", "Goran", "Hadi", "Idris", "Jiri", "Koen"]
FEMALE_FIRST_NAMES = ["Alexa", "Ariane", "Bruna", "Carla", "Cory", "Dakota", "Erin", "Fatima", "Gloria", "Holly", "Iasmin", "Jasmine", "Joanne", "Karolina", "Ketlen", "Lauren", "Lucia", "Manon", "Mayra", "Molly", "Natalia", "Norma", "Paula", "Raquel", "Rose", "Sabrina", "Tabatha", "Valentina", "Viviane", "Yan",
    "Adriana", "Aisha", "Alina", "Amara", "Anya", "Beatriz", "Camila", "Celeste", "Chloe", "Daniela", "Daria", "Elena", "Elif", "Emma", "Esme", "Farah", "Fernanda", "Francesca", "Georgia", "Hana", "Indira", "Ines", "Isabel", "Katerina", "Kiara", "Lina", "Luciana", "Maja", "Mariana", "Marta", "Maya", "Nadia", "Naomi", "Niamh", "Noelle", "Olivia", "Petra", "Priya", "Renata", "Rhea", "Romina", "Salma", "Samira", "Sara", "Sofia", "Sonya", "Talia", "Tereza", "Valeria", "Veronika", "Victoria", "Wiktoria", "Ximena", "Yasmin", "Zaina", "Zoe", "Amina", "Brigitte", "Celine", "Dalia"]
LAST_NAMES = ["Almeida", "Archer", "Barrera", "Bennett", "Costa", "Dawson", "Eklund", "Foster", "Garcia", "Graves", "Hughes", "Ishii", "Keller", "Kowalski", "Lima", "Madsen", "Mendoza", "Novak", "Okada", "Petrov", "Quinn", "Ramos", "Reyes", "Santos", "Silva", "Sokolov", "Torres", "Vargas", "Volkov", "Ward", "Yamada", "Yilmaz", "Andrade", "Blanchfield", "Fiorot", "Grasso", "Namajunas", "Shevchenko", "Weili",
    "Abdullah", "Adebayo", "Ahmed", "Akhtar", "Aoki", "Arslan", "Barros", "Bianchi", "Boulahrouz", "Campbell", "Carvalho", "Chen", "Choi", "DelaCruz", "Demir", "Diop", "Dubois", "Eze", "Ferreira", "Fischer", "Gomes", "Gupta", "Haddad", "Hansen", "Hassan", "Ibrahim", "Ivanov", "Jankovic", "Jensen", "Kaur", "Khan", "Kim", "Kovac", "Leclerc", "Liu", "Lopez", "Mahmud", "Martinez", "Mensah", "Moretti", "Mustafa", "Nakamura", "Nguyen", "Nunes", "Okoye", "Oliveira", "Orlov", "Park", "Pereira", "Popescu", "Rahman", "Richter", "Rossi", "Sato", "Schmidt", "Shah", "Singh", "Sousa", "Suzuki", "Tanaka", "Tavares", "Teixeira", "Valdez", "VanderMerwe", "Wang", "Williams", "Youssef", "Zaman", "Zielinski", "Araujo", "Bakker", "Cisse", "Duarte", "ElMasri", "Fadel", "Girard", "Hasegawa", "Ionescu"]
REGIONAL_NAME_POOLS = {
    "Japan": {
        "male": ["Akira", "Daiki", "Haruto", "Hayato", "Hiroki", "Kenta", "Koji", "Masato", "Naoki", "Riku", "Ryota", "Shinya", "Shota", "Taiga", "Takumi", "Tatsuya", "Yuki", "Yuta"],
        "female": ["Aiko", "Akari", "Chihiro", "Hana", "Haruka", "Kaori", "Miku", "Mio", "Nana", "Rina", "Sakura", "Shiori", "Yui", "Yuka"],
        "last": ["Aoki", "Endo", "Fujita", "Hayashi", "Inoue", "Ito", "Kato", "Kobayashi", "Matsumoto", "Nakamura", "Nakagawa", "Sato", "Shimizu", "Suzuki", "Tanaka", "Watanabe", "Yamamoto", "Yoshida"],
    },
    "Asia": {
        "male": ["Anan", "Arthit", "Boonchai", "Chan", "Dae", "Hoon", "Jae", "Jin", "Kiet", "Min", "Narin", "Phan", "Ratcha", "Seok", "Somsak", "Tae", "Wei", "Xiang"],
        "female": ["Anong", "Ara", "Bai", "Dao", "Hye", "Jia", "Lan", "Mei", "Minji", "Nari", "Pim", "Sora", "Suda", "Xiu"],
        "last": ["Chen", "Choi", "Han", "Kim", "Lee", "Lim", "Nguyen", "Park", "Pham", "Saeed", "Tan", "Tran", "Wang", "Wong", "Yoon", "Zhang"],
    },
    "UK": {
        "male": ["Aidan", "Alfie", "Callum", "Cameron", "Declan", "Finlay", "Fraser", "Harvey", "Jamie", "Kieran", "Lewis", "Liam", "Owen", "Rhys", "Ross", "Scott", "Sean"],
        "female": ["Aimee", "Beth", "Caitlin", "Chloe", "Danielle", "Ellie", "Fiona", "Georgia", "Hannah", "Imogen", "Katie", "Lauren", "Maisie", "Niamh", "Paige", "Sophie"],
        "last": ["Armstrong", "Barlow", "Campbell", "Cavanagh", "Donnelly", "Fletcher", "Gilmour", "Hargreaves", "Henson", "Keegan", "McLeod", "Murray", "OConnor", "Patterson", "Ritchie", "Sweeney", "Wallace"],
    },
}
STANDING_SKILLS = ["footwork", "feints", "head_movement", "punch_power", "punch_technique", "hand_speed", "high_kick_power", "high_kick_technique", "high_kick_speed", "low_kick_power", "low_kick_technique", "low_kick_speed", "creative_punches", "creative_kicks", "guard_defence", "kick_defence"]
GROUND_SKILLS = ["guard_work", "scrambles", "transitions", "positional_ability", "ground_striking", "submission_attack", "submission_defence_detail", "top_control", "bottom_control", "back_control", "mount_control", "leg_locks"]
WRESTLING_SKILLS = ["takedowns", "takedown_setup", "takedown_speed", "takedown_defence_detail", "sprawl", "throws", "slams", "chain_wrestling", "cage_wrestling", "ride_control", "get_ups"]
CLINCH_SKILLS = ["clinch_control", "dirty_boxing", "elbows", "knees", "thai_plum", "cage_pressure", "clinch_takedowns", "clinch_defence"]
MENTAL_SKILLS = ["aggression", "composure", "consistency", "killer_instinct", "adaptability", "discipline", "dedication", "confidence"]
PHYSICAL_SKILLS = ["reach", "cut_immunity", "conditioning", "strength", "mobility", "flexibility", "reflexes", "chin_strength", "resilience", "stun_recovery", "weight_cutting", "natural_size"]
DETAILED_SKILL_GROUPS = {
    "Standing": STANDING_SKILLS,
    "Ground": GROUND_SKILLS,
    "Wrestling": WRESTLING_SKILLS,
    "Muay Thai Clinch": CLINCH_SKILLS,
    "Mental": MENTAL_SKILLS,
    "Physical": PHYSICAL_SKILLS,
}
GYM_SPECIALTY_SKILLS = {
    "Boxing": ("punch_power", "punch_technique", "hand_speed", "head_movement"),
    "Kickboxing": ("high_kick_power", "high_kick_technique", "low_kick_technique", "creative_kicks"),
    "Wrestling": ("takedowns", "takedown_setup", "chain_wrestling", "sprawl"),
    "BJJ": ("submission_attack", "guard_work", "back_control", "leg_locks"),
    "Clinch": ("clinch_control", "dirty_boxing", "knees", "clinch_takedowns"),
    "Conditioning": ("conditioning", "resilience", "stun_recovery", "weight_cutting"),
    "Prospect Development": ("dedication", "adaptability", "discipline", "confidence"),
    "Gameplanning": ("composure", "consistency", "fight_iq", "adaptability"),
}
