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

# Non-MMA circuits do not share MMA's eight-division ladder.  The value is the
# maximum competition weight in pounds; ``None`` means an open-ended class.
# These keys are also the canonical, save-stable labels used by sport titles,
# rankings and matchmaking.
COMBAT_SPORT_WEIGHT_CLASSES = {
    "Boxing": {
        "Male": [
            ("Minimumweight", 105), ("Light Flyweight", 108), ("Flyweight", 112),
            ("Super Flyweight", 115), ("Bantamweight", 118), ("Super Bantamweight", 122),
            ("Featherweight", 126), ("Super Featherweight", 130), ("Lightweight", 135),
            ("Super Lightweight", 140), ("Welterweight", 147), ("Super Welterweight", 154),
            ("Middleweight", 160), ("Super Middleweight", 168), ("Light Heavyweight", 175),
            ("Cruiserweight", 200), ("Heavyweight", None),
        ],
    },
    "Kickboxing": {
        "Male": [
            ("Flyweight", 121), ("Bantamweight", 132), ("Featherweight", 143),
            ("Lightweight", 154), ("Welterweight", 170), ("Middleweight", 187),
            ("Light Heavyweight", 209), ("Heavyweight", None),
        ],
    },
    "Muay Thai": {
        "Male": [
            ("Mini Flyweight", 105), ("Flyweight", 112), ("Bantamweight", 118),
            ("Super Bantamweight", 122), ("Featherweight", 126), ("Super Featherweight", 130),
            ("Lightweight", 135), ("Super Lightweight", 140), ("Welterweight", 147),
            ("Middleweight", 160), ("Heavyweight", None),
        ],
    },
    "Lethwei": {
        "Male": [
            ("Flyweight", 112), ("Bantamweight", 119), ("Featherweight", 126),
            ("Lightweight", 132), ("Welterweight", 148), ("Middleweight", 165),
            ("Cruiserweight", 185), ("Openweight", None),
        ],
    },
    "Wrestling": {
        "Male": [("57 kg", 126), ("65 kg", 143), ("70 kg", 154), ("74 kg", 163), ("79 kg", 174), ("86 kg", 190), ("97 kg", 214), ("130 kg", 287)],
        "Female": [("50 kg", 110), ("53 kg", 117), ("57 kg", 126), ("59 kg", 130), ("62 kg", 137), ("68 kg", 150), ("72 kg", 159), ("76 kg", 168)],
    },
    "Brazilian Jiu-Jitsu": {
        "Male": [
            ("Roosterweight", 127), ("Light Featherweight", 141), ("Featherweight", 154),
            ("Lightweight", 168), ("Middleweight", 182), ("Medium Heavyweight", 195),
            ("Heavyweight", 208), ("Super Heavyweight", 222), ("Ultra Heavyweight", None),
        ],
        "Female": [
            ("Roosterweight", 107), ("Light Featherweight", 118), ("Featherweight", 129),
            ("Lightweight", 141), ("Middleweight", 152), ("Medium Heavyweight", 163),
            ("Heavyweight", 175), ("Super Heavyweight", None),
        ],
    },
}

# Striking circuits use the same ladder for women.  Keeping the alias in the
# source of truth avoids UI-only exceptions and makes generated women eligible
# for the same real championships.
for _sport in ("Boxing", "Kickboxing", "Muay Thai", "Lethwei"):
    COMBAT_SPORT_WEIGHT_CLASSES[_sport]["Female"] = list(COMBAT_SPORT_WEIGHT_CLASSES[_sport]["Male"])

COMBAT_SPORT_REAL_DIVISIONS = {
    "Boxing": {
        "Floyd Mayweather Jr": "Super Featherweight", "Manny Pacquiao": "Featherweight",
        "Canelo Alvarez": "Super Middleweight", "Terence Crawford": "Welterweight",
        "Oleksandr Usyk": "Cruiserweight", "Vasiliy Lomachenko": "Super Featherweight",
        "Naoya Inoue": "Super Bantamweight", "Gennady Golovkin": "Middleweight",
        "Wladimir Klitschko": "Heavyweight", "Vitali Klitschko": "Heavyweight", "Lennox Lewis": "Heavyweight",
        "Roy Jones Jr": "Light Heavyweight", "Bernard Hopkins": "Middleweight", "Oscar De La Hoya": "Welterweight",
        "Juan Manuel Marquez": "Lightweight", "Erik Morales": "Featherweight", "Marco Antonio Barrera": "Featherweight",
        "Miguel Cotto": "Welterweight", "Felix Trinidad": "Welterweight", "Shane Mosley": "Lightweight",
        "Andre Ward": "Super Middleweight", "Sergey Kovalev": "Light Heavyweight",
        "Artur Beterbiev": "Light Heavyweight", "Dmitry Bivol": "Light Heavyweight",
        "Tyson Fury": "Heavyweight", "Anthony Joshua": "Heavyweight", "Deontay Wilder": "Heavyweight",
        "Andy Ruiz Jr": "Heavyweight", "Zhilei Zhang": "Heavyweight", "Joseph Parker": "Heavyweight",
        "Jermell Charlo": "Super Welterweight", "Jermall Charlo": "Middleweight", "Errol Spence Jr": "Welterweight",
        "Keith Thurman": "Welterweight", "Shawn Porter": "Welterweight", "Danny Garcia": "Super Lightweight",
        "Amir Khan": "Super Lightweight", "Kell Brook": "Welterweight", "Timothy Bradley": "Super Lightweight",
        "Devon Alexander": "Super Lightweight", "Roman Gonzalez": "Flyweight", "Nonito Donaire": "Bantamweight",
        "Juan Francisco Estrada": "Super Flyweight", "Srisaket Sor Rungvisai": "Super Flyweight",
        "Kazuto Ioka": "Super Flyweight", "Donnie Nietes": "Light Flyweight", "Mikey Garcia": "Lightweight",
        "Gervonta Davis": "Lightweight", "Shakur Stevenson": "Super Featherweight", "Devin Haney": "Lightweight",
    },
    "Kickboxing": {
        "Ernesto Hoost": "Heavyweight", "Giorgio Petrosyan": "Lightweight", "Semmy Schilt": "Heavyweight",
        "Peter Aerts": "Heavyweight", "Remy Bonjasky": "Heavyweight", "Badr Hari": "Heavyweight",
        "Buakaw Banchamek": "Lightweight", "Andy Hug": "Heavyweight", "Ramon Dekkers": "Featherweight",
        "Rob Kaman": "Middleweight", "Rico Verhoeven": "Heavyweight", "Tenshin Nasukawa": "Bantamweight",
        "Sitthichai Sitsongpeenong": "Lightweight", "Superbon Singha Mawynn": "Lightweight",
        "Chingiz Allazov": "Lightweight", "Artem Levin": "Middleweight", "Nieky Holzken": "Welterweight",
        "Masato Kobayashi": "Lightweight", "Andy Souwer": "Lightweight", "Mike Zambidis": "Lightweight",
        "Mirko Cro Cop": "Heavyweight", "Alexey Ignashov": "Heavyweight", "Gokhan Saki": "Light Heavyweight",
        "Tyrone Spong": "Light Heavyweight", "Jerome Le Banner": "Heavyweight", "Branko Cikatic": "Heavyweight",
        "Peter Graham": "Heavyweight", "Jorina Baars": "Featherweight", "Lucia Rijker": "Featherweight",
        "Denise Kielholtz": "Bantamweight", "Jemyma Betrian": "Bantamweight", "Anissa Meksen": "Flyweight",
        "Petchpanomrung Kiatmookao": "Featherweight", "Cedric Doumbe": "Welterweight",
        "Marat Grigorian": "Lightweight", "Robin van Roosmalen": "Lightweight", "Albert Kraus": "Lightweight",
        "Kaoklai Kaennorsing": "Middleweight", "Ray Sefo": "Heavyweight", "Mark Hunt": "Heavyweight",
        "Francisco Filho": "Heavyweight", "Kyotaro Fujimoto": "Heavyweight", "Daniel Ghita": "Heavyweight",
        "Hesdy Gerges": "Heavyweight", "Jamal Ben Saddik": "Heavyweight", "Murthel Groenhart": "Welterweight",
        "Alistair Overeem": "Heavyweight", "Sam Greco": "Heavyweight", "Stan Longinidis": "Heavyweight",
        "Joseph Valtellini": "Welterweight",
    },
    "Muay Thai": {
        "Samart Payakaroon": "Featherweight", "Dieselnoi Chor Thanasukarn": "Lightweight",
        "Saenchai": "Super Featherweight", "Buakaw Banchamek": "Middleweight",
        "Rodtang Jitmuangnon": "Super Featherweight", "Nong-O Gaiyanghadao": "Lightweight",
        "Sam-A Gaiyanghadao": "Bantamweight", "Petchmorakot Petchyindee": "Middleweight",
        "Superbon Singha Mawynn": "Middleweight", "Superlek Kiatmuu9": "Super Featherweight",
        "Yodsanklai Fairtex": "Middleweight", "Ramon Dekkers": "Super Lightweight",
        "Apidej Sit-Hirun": "Welterweight", "Sagat Petchyindee": "Welterweight",
        "Namsaknoi Yudthagarngamtorn": "Lightweight", "Namkabuan Nongkeepahuyuth": "Super Featherweight",
        "Kaensak Sor Ploenjit": "Bantamweight", "Somrak Khamsing": "Featherweight",
        "Pud Pad Noy Worawoot": "Lightweight", "Karuhat Sor Supawan": "Super Bantamweight",
        "Jomhod Kiatadisak": "Lightweight", "Orono Por Muang Ubon": "Lightweight",
        "Lerdsila Chumpairtour": "Bantamweight", "Petchboonchu FA Group": "Lightweight",
        "Singdam Kiatmuu9": "Lightweight", "Anuwat Kaewsamrit": "Featherweight",
        "Yodwicha Por Boonsit": "Super Lightweight", "Sangmanee Sor Tienpo": "Bantamweight",
        "Panpayak Jitmuangnon": "Bantamweight", "Tawanchai PK Saenchai": "Welterweight",
        "Seksan Or Kwanmuang": "Lightweight", "Liam Harrison": "Super Lightweight",
        "John Wayne Parr": "Middleweight", "Dany Bill": "Super Lightweight",
        "Coban Lookchaomaesaitong": "Lightweight", "Sakmongkol Sithchuchok": "Middleweight",
        "Kongtoranee Payakaroon": "Bantamweight", "Boonlai Sor Thanikul": "Super Bantamweight",
        "Oley Kiatoneway": "Super Bantamweight", "Hippy Singmanee": "Mini Flyweight",
        "Chamuakpetch Haphalung": "Featherweight", "Veeraphol Sahaprom": "Bantamweight",
        "Khaosai Galaxy": "Bantamweight", "Attachai Fairtex": "Super Featherweight",
        "Petchtanong Petchfergus": "Welterweight", "Petchdam Petchyindee": "Super Featherweight",
        "Capitan Petchyindee": "Welterweight", "Kulabdam Sor Jor Piek Uthai": "Super Lightweight",
        "Nadaka Yoshinari": "Bantamweight", "Somratsamee Manopgym": "Bantamweight",
    },
    "Lethwei": {
        "Tun Tun Min": "Openweight", "Dave Leduc": "Openweight", "Saw Nga Man": "Openweight",
        "Too Too": "Middleweight", "Tway Ma Shaung": "Openweight", "Soe Lin Oo": "Welterweight",
        "Cyrus Washington": "Middleweight", "Lone Chaw": "Openweight", "Shwe Sai": "Openweight",
        "Tun Lwin Moe": "Welterweight", "Mite Yine": "Featherweight", "Saw Ba Oo": "Welterweight",
        "Wan Chai": "Middleweight", "Kyar Ba Nyein": "Bantamweight", "Phoe Kay": "Cruiserweight",
        "Artur Saladiak": "Middleweight", "Sasha Moisa": "Middleweight", "Naimjon Tuhtaboyev": "Middleweight",
        "Akitoshi Tamura": "Welterweight", "Shunichi Shimizu": "Welterweight",
    },
    "Wrestling": {
        "Aleksandr Karelin": "130 kg", "Buvaisar Saitiev": "74 kg", "John Smith": "65 kg",
        "Jordan Burroughs": "74 kg", "Abdulrashid Sadulaev": "97 kg", "Mijain Lopez": "130 kg",
        "Sergei Beloglazov": "57 kg", "Arsen Fadzaev": "70 kg", "Hamid Sourian": "57 kg",
        "Artur Taymazov": "130 kg", "Valentin Yordanov": "57 kg", "Dan Gable": "70 kg",
        "Cael Sanderson": "86 kg", "Kyle Snyder": "97 kg", "David Taylor": "86 kg",
        "Hassan Yazdani": "86 kg", "Gable Steveson": "130 kg", "Geno Petriashvili": "130 kg",
        "Taha Akgul": "130 kg", "Rulon Gardner": "130 kg", "Bruce Baumgartner": "130 kg",
        "Makharbek Khadartsev": "97 kg", "Ivan Yarygin": "130 kg", "Yojiro Uetake": "57 kg",
        "Osamu Watanabe": "65 kg", "Levan Tediashvili": "97 kg", "Sushil Kumar": "70 kg",
        "Bajrang Punia": "65 kg", "Yogeshwar Dutt": "65 kg", "Saori Yoshida": "57 kg",
        "Kaori Icho": "68 kg", "Helen Maroulis": "57 kg", "Adeline Gray": "76 kg",
        "Tamyra Mensah-Stock": "68 kg", "Iryna Merleni": "50 kg", "Aleksandr Medved": "97 kg",
        "Elbrus Tedeyev": "70 kg", "Besik Kudukhov": "65 kg", "Zaurbek Sidakov": "74 kg",
        "Roman Vlasov": "79 kg", "Frank Chamizo": "74 kg", "Reza Yazdani": "97 kg",
        "Ghasem Rezaei": "97 kg", "Komeil Ghasemi": "130 kg", "Henry Cejudo": "57 kg",
        "Daniel Cormier": "97 kg", "Yoel Romero": "86 kg", "Ben Askren": "74 kg",
        "Bo Nickal": "86 kg", "Kenny Monday": "74 kg",
    },
    "Brazilian Jiu-Jitsu": {
        "Roger Gracie": "Ultra Heavyweight", "Marcelo Garcia": "Middleweight", "Marcus Almeida": "Ultra Heavyweight",
        "Leandro Lo": "Medium Heavyweight", "Andre Galvao": "Medium Heavyweight", "Gordon Ryan": "Ultra Heavyweight",
        "Rafael Mendes": "Featherweight", "Guilherme Mendes": "Light Featherweight",
        "Rubens Charles Maciel": "Featherweight", "Bruno Malfacine": "Roosterweight",
        "Roberto Cyborg Abreu": "Ultra Heavyweight", "Rodolfo Vieira": "Heavyweight",
        "Alexandre Ribeiro": "Heavyweight", "Saulo Ribeiro": "Medium Heavyweight",
        "Romulo Barral": "Medium Heavyweight", "Bernardo Faria": "Ultra Heavyweight",
        "Lucas Lepri": "Lightweight", "Robson Moura": "Light Featherweight", "Royler Gracie": "Featherweight",
        "Rickson Gracie": "Medium Heavyweight", "Royce Gracie": "Middleweight", "Carlos Gracie Jr": "Featherweight",
        "Carlson Gracie": "Medium Heavyweight", "Rolls Gracie": "Middleweight", "Jean Jacques Machado": "Middleweight",
        "Rigan Machado": "Heavyweight", "Vitor Shaolin Ribeiro": "Lightweight",
        "Murilo Bustamante": "Medium Heavyweight", "Mario Sperry": "Ultra Heavyweight",
        "Fabio Gurgel": "Medium Heavyweight", "Fernando Terere": "Middleweight", "Marcio Feitosa": "Featherweight",
        "Ronaldo Jacare Souza": "Medium Heavyweight", "Demian Maia": "Medium Heavyweight", "Kron Gracie": "Middleweight",
        "Mikey Musumeci": "Roosterweight", "Nicholas Meregali": "Ultra Heavyweight",
        "Felipe Pena": "Ultra Heavyweight", "Kaynan Duarte": "Ultra Heavyweight", "Mica Galvao": "Middleweight",
        "Tainan Dalpra": "Middleweight", "Craig Jones": "Medium Heavyweight", "Lachlan Giles": "Middleweight",
        "Garry Tonon": "Lightweight", "Eddie Bravo": "Lightweight", "Keenan Cornelius": "Medium Heavyweight",
        "Paulo Miyao": "Light Featherweight", "Joao Miyao": "Light Featherweight",
        "Gabi Garcia": "Super Heavyweight", "Beatriz Mesquita": "Lightweight",
    },
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
