import os
import json
import sys
from pathlib import Path


BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent))
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
ASSET_DIR = BUNDLE_DIR / "assets" if (BUNDLE_DIR / "assets").exists() else APP_DIR / "assets"
APP_ICON_ICO = ASSET_DIR / "app_icon.ico"
APP_ICON_PNG = ASSET_DIR / "app_icon.png"
GAME_NAME = "MMA Warriors"
GAME_START_YEAR = 2026
CALENDAR_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
CALENDAR_MONTH_ABBREVIATIONS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


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
COMBAT_SPORT_ROSTER_TARGET_MULTIPLIER = 2
ROLLING_SAVE_SLOT_COUNT = 2
# Keep a lightweight, searchable index of completed cards for the life of a
# save. Full commentary remains deliberately short-lived, but a card should
# never vanish from the results database simply because its replay aged out.
RESULT_INDEX_LIMIT = 100000
GLOBAL_RESULT_REPLAY_LIMIT = 2000
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
        "Jem Mace": "Middleweight", "John L Sullivan": "Heavyweight", "Tom Cribb": "Heavyweight",
        "Daniel Mendoza": "Lightweight", "James Figg": "Light Heavyweight", "Jack Broughton": "Heavyweight",
        "Tom Sayers": "Heavyweight", "William Bendigo Thompson": "Middleweight", "Jem Belcher": "Lightweight",
        "Tom Molineaux": "Heavyweight", "John C Heenan": "Heavyweight", "Tom Spring": "Middleweight",
        "Ben Caunt": "Heavyweight", "Jake Kilrain": "Heavyweight", "Bobby Gunn": "Cruiserweight",
        "Luis Palomino": "Lightweight", "Lorenzo Hunt": "Middleweight", "Christine Ferea": "Flyweight",
        "Britain Hart": "Featherweight", "Arnold Adams": "Heavyweight", "Reggie Barnett Jr": "Bantamweight",
        "Joey Beltran": "Cruiserweight", "David Mundell": "Middleweight", "Dat Nguyen": "Lightweight",
        "Austin Trout": "Super Welterweight", "Paddy Ryan": "Heavyweight", "John Gentleman Jackson": "Middleweight",
        "Hen Pearce": "Lightweight", "Bartley Gorman": "Middleweight", "James Deaf Burke": "Welterweight",
        "Jem Ward": "Featherweight", "Joe Goss": "Heavyweight", "Tom King": "Heavyweight", "Peter Jackson": "Heavyweight",
        "Mick Terrill": "Heavyweight", "Kai Stewart": "Featherweight", "Francesco Ricchi": "Middleweight",
        "Artem Lobov": "Featherweight", "Jason Knight": "Featherweight", "Thiago Alves": "Welterweight",
        "Alan Belcher": "Heavyweight", "Shannon Ritch": "Heavyweight",
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
        "Shwe War Tun": "Openweight", "Thway Thit Win Hlaing": "Openweight", "Shwe Du Wun": "Openweight",
        "Win Tun": "Featherweight", "Shan La Tway": "Openweight", "Antonio Faria": "Lightweight",
        "Saw Htoo Aung": "Lightweight", "Souris Manfredi": "Bantamweight", "Julija Stoliarenko": "Bantamweight",
        "Tha Pyay Nyo": "Welterweight", "Yan Naing Tun": "Welterweight", "Ba Htoo Maung": "Middleweight",
        "Shwe Yar Man": "Openweight", "Thant Zin": "Featherweight", "Salai Thang Khwi Shein": "Lightweight",
        "Thet Win Aung": "Welterweight", "Nguyen Tran Duy Nhat": "Featherweight", "Maisha Katz": "Bantamweight",
        "Shwe Sin Min": "Bantamweight",
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
REGIONS = ["USA", "Canada", "Brazil", "Mexico", "UK", "Europe", "Russia", "Japan", "South Korea", "Australia", "Asia", "Middle East", "Africa"]
# Weighted population pool keeps small markets from becoming as prolific as
# the USA or broad Asia/Europe buckets merely because they have their own map entry.
REGION_GENERATION_POOL = (
    ["USA"] * 18 + ["Europe"] * 14 + ["Asia"] * 12 + ["Brazil"] * 10 +
    ["UK"] * 8 + ["Japan"] * 7 + ["Russia"] * 6 + ["Mexico"] * 5 +
    ["Canada"] * 5 + ["South Korea"] * 4 + ["Australia"] * 4 +
    ["Middle East"] * 4 + ["Africa"] * 3
)
# These are world-market buckets rather than passports.  They keep generated
# fighters rooted in a believable local scene while still allowing realistic
# migration between neighbouring and culturally connected markets.
REGIONAL_MIGRATION_LINKS = {
    "USA": ["Canada", "Mexico", "Brazil", "UK", "Europe"],
    "Canada": ["USA", "UK", "Europe"],
    "Brazil": ["USA", "Mexico", "Europe"],
    "Mexico": ["USA", "Canada", "Brazil"],
    "UK": ["Europe", "USA", "Canada", "Australia"],
    "Europe": ["UK", "USA", "Canada", "Russia", "Middle East", "Africa"],
    "Russia": ["Europe", "Asia", "Middle East"],
    "Japan": ["Asia", "South Korea", "Australia", "USA"],
    "South Korea": ["Japan", "Asia", "USA"],
    "Australia": ["Asia", "Japan", "UK", "USA"],
    "Asia": ["Japan", "South Korea", "Australia", "Russia", "Middle East", "USA"],
    "Middle East": ["Europe", "Asia", "Russia", "Africa"],
    "Africa": ["Europe", "Middle East", "Brazil", "UK"],
}
REGION_COUNTRIES = {
    "USA": "United States", "Canada": "Canada", "Brazil": "Brazil", "Mexico": "Mexico",
    "UK": "United Kingdom", "Europe": "Europe", "Japan": "Japan", "Australia": "Australia",
    "Asia": "Asia", "Russia": "Russia", "South Korea": "South Korea",
    "Middle East": "Middle East", "New Zealand": "New Zealand", "Africa": "Africa",
}
REGION_CITIES = {
    "USA": ["Las Vegas", "New York", "Los Angeles", "Dallas", "Miami", "Chicago", "Atlanta", "Boston", "Denver", "Detroit", "Houston", "Nashville", "New Orleans", "Philadelphia", "Phoenix", "Seattle"],
    "Canada": ["Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton", "Halifax", "Hamilton", "Ottawa", "Quebec City", "Winnipeg"],
    "Brazil": ["Rio de Janeiro", "Sao Paulo", "Curitiba", "Brasilia", "Belo Horizonte", "Campinas", "Fortaleza", "Manaus", "Porto Alegre", "Salvador"],
    "Mexico": ["Mexico City", "Guadalajara", "Monterrey", "Tijuana", "Cancun", "Chihuahua", "Leon", "Puebla"],
    "UK": ["London", "Manchester", "Liverpool", "Cardiff", "Glasgow", "Belfast", "Birmingham", "Bristol", "Edinburgh", "Leeds", "Newcastle", "Sheffield"],
    "Europe": ["Paris", "Marseille", "Berlin", "Hamburg", "Warsaw", "Krakow", "Dublin", "Madrid", "Barcelona", "Amsterdam", "Rome", "Milan", "Prague", "Belgrade", "Zagreb", "Stockholm", "Oslo", "Helsinki", "Athens", "Lisbon", "Bucharest", "Sofia", "Tbilisi", "Vienna", "Brussels"],
    "Russia": ["Moscow", "Saint Petersburg", "Sochi", "Kazan", "Grozny", "Makhachkala", "Khasavyurt", "Derbent", "Vladikavkaz", "Yekaterinburg", "Novosibirsk", "Omsk", "Perm", "Rostov-on-Don", "Samara", "Ufa"],
    "Japan": ["Tokyo", "Osaka", "Saitama", "Yokohama", "Fukuoka", "Hiroshima", "Kobe", "Nagoya", "Sapporo", "Sendai"],
    "South Korea": ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Gwangju", "Suwon", "Ulsan"],
    "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra", "Darwin", "Gold Coast", "Hobart", "Newcastle"],
    "Asia": ["Bangkok", "Phuket", "Singapore", "Manila", "Cebu City", "Beijing", "Shanghai", "Guangzhou", "Hanoi", "Ho Chi Minh City", "Jakarta", "Bandung", "Kuala Lumpur", "Ulaanbaatar", "Almaty", "Astana", "Tashkent", "Bishkek", "Mumbai", "New Delhi"],
    "Middle East": ["Manama", "Abu Dhabi", "Dubai", "Riyadh", "Jeddah", "Doha", "Beirut", "Amman", "Tehran", "Shiraz", "Baghdad", "Erbil", "Istanbul", "Ankara"],
    "Africa": ["Johannesburg", "Cape Town", "Durban", "Lagos", "Abuja", "Cairo", "Alexandria", "Nairobi", "Mombasa", "Casablanca", "Rabat", "Accra", "Dakar", "Douala", "Kampala", "Dar es Salaam", "Addis Ababa", "Tunis"],
}

# Generated fighters use country-level identities within the broader simulation
# markets. The region remains the economic and matchmaking bucket; country,
# nationality and hometown provide the human detail shown on profiles.
REGION_IDENTITY_PROFILES = {
    "USA": [("United States", "American", REGION_CITIES["USA"])],
    "Canada": [("Canada", "Canadian", REGION_CITIES["Canada"])],
    "Brazil": [("Brazil", "Brazilian", REGION_CITIES["Brazil"])],
    "Mexico": [("Mexico", "Mexican", REGION_CITIES["Mexico"])],
    "UK": [
        ("England", "English", ["London", "Manchester", "Liverpool", "Birmingham", "Bristol", "Leeds", "Newcastle", "Sheffield"]),
        ("Scotland", "Scottish", ["Glasgow", "Edinburgh", "Aberdeen", "Dundee"]),
        ("Wales", "Welsh", ["Cardiff", "Swansea", "Newport", "Wrexham"]),
        ("Northern Ireland", "Northern Irish", ["Belfast", "Derry", "Lisburn", "Newry"]),
    ],
    "Europe": [
        ("France", "French", ["Paris", "Marseille", "Lyon", "Toulouse"]),
        ("Germany", "German", ["Berlin", "Hamburg", "Munich", "Cologne"]),
        ("Poland", "Polish", ["Warsaw", "Krakow", "Gdansk", "Wroclaw"]),
        ("Ireland", "Irish", ["Dublin", "Cork", "Galway", "Limerick"]),
        ("Spain", "Spanish", ["Madrid", "Barcelona", "Valencia", "Seville"]),
        ("Netherlands", "Dutch", ["Amsterdam", "Rotterdam", "The Hague", "Utrecht"]),
        ("Italy", "Italian", ["Rome", "Milan", "Naples", "Turin"]),
        ("Czechia", "Czech", ["Prague", "Brno", "Ostrava", "Plzen"]),
        ("Serbia", "Serbian", ["Belgrade", "Novi Sad", "Nis", "Kragujevac"]),
        ("Croatia", "Croatian", ["Zagreb", "Split", "Rijeka", "Osijek"]),
        ("Sweden", "Swedish", ["Stockholm", "Gothenburg", "Malmo", "Uppsala"]),
        ("Norway", "Norwegian", ["Oslo", "Bergen", "Trondheim", "Stavanger"]),
        ("Finland", "Finnish", ["Helsinki", "Tampere", "Turku", "Oulu"]),
        ("Georgia", "Georgian", ["Tbilisi", "Batumi", "Kutaisi", "Rustavi"]),
        ("Romania", "Romanian", ["Bucharest", "Cluj-Napoca", "Iasi", "Timisoara"]),
    ],
    "Russia": [("Russia", "Russian", REGION_CITIES["Russia"])],
    "Japan": [("Japan", "Japanese", REGION_CITIES["Japan"])],
    "South Korea": [("South Korea", "South Korean", REGION_CITIES["South Korea"])],
    "Australia": [("Australia", "Australian", REGION_CITIES["Australia"])],
    "Asia": [
        ("Thailand", "Thai", ["Bangkok", "Phuket", "Pattaya", "Chiang Mai"]),
        ("Philippines", "Filipino", ["Manila", "Cebu City", "Davao City", "Quezon City"]),
        ("China", "Chinese", ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"]),
        ("Vietnam", "Vietnamese", ["Hanoi", "Ho Chi Minh City", "Da Nang", "Hai Phong"]),
        ("Indonesia", "Indonesian", ["Jakarta", "Bandung", "Surabaya", "Medan"]),
        ("Malaysia", "Malaysian", ["Kuala Lumpur", "Johor Bahru", "George Town", "Kota Kinabalu"]),
        ("Mongolia", "Mongolian", ["Ulaanbaatar", "Erdenet", "Darkhan", "Choibalsan"]),
        ("Kazakhstan", "Kazakh", ["Almaty", "Astana", "Shymkent", "Karaganda"]),
        ("Uzbekistan", "Uzbek", ["Tashkent", "Samarkand", "Bukhara", "Andijan"]),
        ("Kyrgyzstan", "Kyrgyz", ["Bishkek", "Osh", "Jalal-Abad", "Karakol"]),
        ("India", "Indian", ["Mumbai", "New Delhi", "Bengaluru", "Hyderabad"]),
        ("Singapore", "Singaporean", ["Singapore"]),
    ],
    "Middle East": [
        ("Bahrain", "Bahraini", ["Manama", "Riffa", "Muharraq"]),
        ("United Arab Emirates", "Emirati", ["Abu Dhabi", "Dubai", "Sharjah"]),
        ("Saudi Arabia", "Saudi", ["Riyadh", "Jeddah", "Dammam"]),
        ("Qatar", "Qatari", ["Doha", "Al Rayyan", "Al Wakrah"]),
        ("Lebanon", "Lebanese", ["Beirut", "Tripoli", "Sidon"]),
        ("Jordan", "Jordanian", ["Amman", "Zarqa", "Irbid"]),
        ("Iran", "Iranian", ["Tehran", "Shiraz", "Mashhad", "Isfahan"]),
        ("Iraq", "Iraqi", ["Baghdad", "Erbil", "Basra", "Mosul"]),
        ("Turkey", "Turkish", ["Istanbul", "Ankara", "Izmir", "Bursa"]),
    ],
    "Africa": [
        ("South Africa", "South African", ["Johannesburg", "Cape Town", "Durban", "Pretoria"]),
        ("Nigeria", "Nigerian", ["Lagos", "Abuja", "Kano", "Ibadan"]),
        ("Egypt", "Egyptian", ["Cairo", "Alexandria", "Giza", "Mansoura"]),
        ("Kenya", "Kenyan", ["Nairobi", "Mombasa", "Kisumu", "Nakuru"]),
        ("Morocco", "Moroccan", ["Casablanca", "Rabat", "Marrakesh", "Tangier"]),
        ("Ghana", "Ghanaian", ["Accra", "Kumasi", "Tamale", "Sekondi-Takoradi"]),
        ("Senegal", "Senegalese", ["Dakar", "Thies", "Saint-Louis", "Kaolack"]),
        ("Cameroon", "Cameroonian", ["Douala", "Yaounde", "Bamenda", "Bafoussam"]),
        ("Uganda", "Ugandan", ["Kampala", "Entebbe", "Jinja", "Mbarara"]),
        ("Tanzania", "Tanzanian", ["Dar es Salaam", "Arusha", "Mwanza", "Dodoma"]),
        ("Ethiopia", "Ethiopian", ["Addis Ababa", "Dire Dawa", "Gondar", "Mekelle"]),
        ("Tunisia", "Tunisian", ["Tunis", "Sfax", "Sousse", "Bizerte"]),
    ],
}
COUNTRY_NATIONALITIES = {
    country: nationality
    for profiles in REGION_IDENTITY_PROFILES.values()
    for country, nationality, _cities in profiles
}
COUNTRY_TO_REGION = {
    country: region
    for region, profiles in REGION_IDENTITY_PROFILES.items()
    for country, _nationality, _cities in profiles
}
COUNTRY_NATIONALITIES.update({
    "United Kingdom": "British", "United States of America": "American",
    "Republic of Ireland": "Irish", "Czech Republic": "Czech",
})
COUNTRY_TO_REGION.update({
    "United Kingdom": "UK", "United States of America": "USA",
    "Republic of Ireland": "Europe", "Czech Republic": "Europe",
    "New Zealand": "Australia",
})
REGION_PROMO_BENEFITS = {
    "USA": {"media": 1.12, "gate": 1.10, "morale": 2},
    "Canada": {"media": 1.02, "gate": 1.04, "morale": 2},
    "Brazil": {"media": 1.06, "gate": 1.08, "morale": 3},
    "Mexico": {"media": 1.04, "gate": 1.05, "morale": 3},
    "UK": {"media": 1.05, "gate": 1.06, "morale": 2},
    "Europe": {"media": 1.02, "gate": 1.03, "morale": 2},
    "Russia": {"media": 1.01, "gate": 1.04, "morale": 3},
    "Japan": {"media": 1.03, "gate": 1.07, "morale": 3},
    "South Korea": {"media": 1.03, "gate": 1.04, "morale": 3},
    "Australia": {"media": 1.03, "gate": 1.05, "morale": 2},
    "Asia": {"media": 1.04, "gate": 1.06, "morale": 3},
    "Middle East": {"media": 1.07, "gate": 1.05, "morale": 3},
    "Africa": {"media": 1.00, "gate": 1.03, "morale": 4},
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

# Expanded world-name bank. These 200 additional first names and 200 surnames
# increase combinatorial variety for generated careers without relying on name
# suffixes such as "2" or breaking the regional pools below.
EXTRA_MALE_FIRST_NAMES = [
    "Abel", "Abner", "Adil", "Afonso", "Aleksei", "Amadou", "Anwar", "Arif", "Arjun", "Arnaud",
    "Arsen", "Asher", "Bartosz", "Bekir", "Bennet", "Blaise", "Bojan", "Ciro", "Claudio", "Cole",
    "Conor", "Darius", "Dawid", "Demba", "Dmitri", "Emilio", "Eren", "Evren", "Fabian", "Faisal",
    "Fedor", "Florian", "Gavin", "Gianni", "Gustavo", "Henrik", "Iker", "Imran", "Ivo", "Jabari",
    "Jasper", "Jermaine", "Joao", "Jovan", "Kacper", "Kareem", "Kasim", "Kenji", "Kofi", "Kristian",
    "Lars", "Leandro", "Leif", "Levon", "Loren", "Lucien", "Magnus", "Mahmoud", "Manuel", "Marcel",
    "Marcin", "Marek", "Marius", "Mikhail", "Musa", "Nasser", "Nico", "Nordin", "Octavio", "Omarion",
    "Osvaldo", "Pablo", "Pascal", "Rami", "Rayan", "Remy", "Riaz", "Rocco", "Rory", "Said",
    "Sami", "Sander", "Sanjay", "Sorin", "Stanislav", "Suleiman", "Tadeusz", "Thierry", "Tobias", "Tomasz",
    "Umar", "Vasile", "Vlad", "Warren", "Yannik", "Yaroslav", "Zaid", "Zoltan", "Amin", "Dion",
]
EXTRA_FEMALE_FIRST_NAMES = [
    "Adela", "Adele", "Aditi", "Ayla", "Bianca", "Bina", "Carmen", "Cassia", "Demi", "Diana",
    "Ebru", "Eleni", "Elisa", "Elodie", "Fadwa", "Gabriela", "Halima", "Irene", "Iris", "Jade",
    "Jelena", "Jolene", "Karla", "Kaya", "Leila", "Liora", "Loretta", "Lourdes", "Lydia", "Madeline",
    "Mai", "Malika", "Marisol", "Meera", "Melina", "Mina", "Mirela", "Monica", "Nabila", "Nadine",
    "Nora", "Oksana", "Pia", "Qiana", "Rania", "Reina", "Roxana", "Sabine", "Sahana", "Selene",
    "Serena", "Shannon", "Sienna", "Simone", "Soraya", "Tania", "Tara", "Tatiana", "Tiffany", "Uma",
    "Vanessa", "Vera", "Wafa", "Yara", "Zara", "Aaliyah", "Abena", "Aurelia", "Aya", "Bahar",
    "Britt", "Chiara", "Cora", "Evelyn", "Freya", "Giulia", "Hafsa", "Iliana", "Jovana", "Khadija",
    "Larisa", "Leonie", "Livia", "Marlene", "Noura", "Oriana", "Parisa", "Rima", "Sana", "Tamara",
    "Ursula", "Zahra", "Zina", "Anika", "Carina", "Eman", "Helena", "Juna", "Khadra", "Laleh",
]
EXTRA_LAST_NAMES = [
    "Abreu", "Acosta", "Afolayan", "Aguilar", "Ahn", "Alvarez", "Amaral", "Andersson", "Antonov", "Arias",
    "Arroyo", "Asano", "Atkinson", "Avila", "Baba", "Bailey", "Balan", "Bartos", "Bashir", "Becker",
    "Benitez", "Berg", "Bhandari", "Bishop", "Bjelic", "Borges", "Boucher", "Bradley", "Brandt", "Brunetti",
    "Bueno", "Burke", "Byrne", "Cabral", "Cabrera", "Caldwell", "Cardoso", "Carrillo", "Castro", "Celik",
    "Chambers", "Chandra", "Chavez", "Cho", "Cohen", "Collins", "Conti", "Cordero", "Cruz", "Cunningham",
    "DaSilva", "Das", "Delgado", "Desai", "Dias", "Dixon", "Dobrev", "Dominguez", "Dunbar", "ElSayed",
    "Espinoza", "Estevez", "Evans", "Fabbri", "Farouk", "Fazio", "Figueroa", "Fonseca", "Ford", "Fournier",
    "Franco", "Fuentes", "Gallo", "Gao", "Gibson", "Gonzalez", "Graham", "Guerrero", "Hamada", "Harper",
    "Hayes", "Hernandez", "Hirano", "Hoffmann", "Holt", "Huang", "Ibarra", "Ito", "Jafari", "Jiang",
    "Johansson", "Kamal", "Kang", "Kapoor", "Karlsen", "Kawasaki", "Keita", "Khalaf", "Klein", "Kohler",
    "Kumar", "Larsen", "Lawson", "Levy", "Lin", "Lindberg", "Lozano", "Lund", "MacDonald", "Malone",
    "Marin", "Marques", "Meyer", "Miller", "Mirza", "Morales", "Mori", "Morrison", "Muller", "Navarro",
    "Nielsen", "Nikolov", "Nishimura", "Nordin", "Obasi", "Ochoa", "Okafor", "Olsen", "Onyango", "Ortega",
    "Osei", "Pacheco", "Palmer", "Papadopoulos", "Patel", "Pavlov", "Peck", "Peralta", "Pires", "Prasad",
    "Qureshi", "Rashid", "Reed", "Ribeiro", "Rojas", "Romero", "Roth", "Ruiz", "Sakamoto", "Salazar",
    "Sampson", "Sanchez", "Serrano", "Sharma", "Sikora", "Simmons", "Sloan", "Smedberg", "Solano", "Song",
    "Sorrentino", "Stark", "Stewart", "Strand", "Svensson", "Takahashi", "Tate", "Taylor", "Thompson", "Tomic",
    "Trujillo", "Ueda", "Ullman", "Valente", "Vasquez", "Vega", "Verma", "Vidal", "Villanueva", "Vukovic",
    "Walker", "Wallin", "West", "Wright", "Yamashita", "Yates", "Zafar", "Zhou", "Zubkov", "Matsuda",
    "Zoric", "Benson", "Cisneros", "DeLuca", "Erdogan", "Fleming", "Ghazali", "Hoxha", "Kowalczyk", "Lefevre",
]
FIRST_NAMES += EXTRA_MALE_FIRST_NAMES
FEMALE_FIRST_NAMES += EXTRA_FEMALE_FIRST_NAMES
LAST_NAMES += EXTRA_LAST_NAMES
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

# Regional pools take precedence over the global bank, so enrich them as well.
# This keeps future fighters recognisably local instead of merely random names
# assigned to a regional flag.
REGIONAL_NAME_POOLS["Japan"]["male"] += [
    "Atsushi", "Fumihiro", "Genki", "Issei", "Junpei", "Kazuya", "Kazuki", "Keisuke", "Kouhei", "Makoto",
    "Ren", "Satoru", "Shun", "Takeru", "Tomoya", "Yoshiki", "Yuji", "Yusuke", "Zen", "Ryusei",
]
REGIONAL_NAME_POOLS["Japan"]["female"] += [
    "Ami", "Ayaka", "Emi", "Hikari", "Honoka", "Kana", "Kanna", "Koharu", "Mao", "Mayu",
    "Misaki", "Nanami", "Nozomi", "Rei", "Riko", "Sayaka", "Suzune", "Tomomi", "Yuna", "Yuriko",
]
REGIONAL_NAME_POOLS["Japan"]["last"] += [
    "Arakawa", "Fukuda", "Hoshino", "Kaneko", "Kawamura", "Kikuchi", "Maeda", "Mori", "Morita", "Nagata",
    "Nishimura", "Ono", "Sakurai", "Takeda", "Ueda", "Ueno", "Yamashita", "Yamazaki", "Yokota", "Kuroda",
]
REGIONAL_NAME_POOLS["Asia"]["male"] += [
    "Anh", "Binh", "Byung", "Chai", "Dong", "Huy", "Kiet", "Kwang", "Long", "Ming", "Nam", "Preecha",
    "Quang", "Sang", "Thanh", "Tian", "Tuan", "Viet", "Won", "Yong", "Zhi", "Joon", "Kietchai", "Ramon",
]
REGIONAL_NAME_POOLS["Asia"]["female"] += [
    "Aeri", "Binh", "Chaiya", "Dara", "Eun", "Fang", "Hanae", "Jieun", "Kanya", "Linh", "Mali", "Nhi",
    "Ploy", "Quynh", "Rin", "Sangita", "Thao", "Thuy", "Vy", "Xiao", "Yen", "Ying", "Zhen", "Arisa",
]
REGIONAL_NAME_POOLS["Asia"]["last"] += [
    "Ahn", "Bui", "Cheng", "Dao", "DelaCruz", "Go", "Ho", "Hong", "Huang", "Kwon", "Lau", "Luu",
    "Manalo", "Nair", "Ong", "Pang", "Quach", "Ramos", "Santos", "Suwannarat", "Takahashi", "Tham", "Vu", "Xie",
]
REGIONAL_NAME_POOLS["UK"]["male"] += [
    "Angus", "Ben", "Bradley", "Connor", "Dylan", "Euan", "Gareth", "Glen", "Gregor", "Harry",
    "Jack", "Malcolm", "Mason", "Nathaniel", "Rory", "Sam", "Toby", "Tristan", "Wayne", "Will",
]
REGIONAL_NAME_POOLS["UK"]["female"] += [
    "Abigail", "Alicia", "Amber", "Briony", "Clare", "Elise", "Grace", "Hollie", "Isla", "Jodie",
    "Keira", "Leah", "Megan", "Nicola", "Orla", "Rebecca", "Rosie", "Sian", "Tegan", "Yvonne",
]
REGIONAL_NAME_POOLS["UK"]["last"] += [
    "Bennett", "Bradshaw", "Carter", "Clarke", "Dawson", "Dunlop", "Elliott", "Grant", "Hughes", "Ingram",
    "Jones", "Kerr", "Lennon", "Mackenzie", "Norton", "Price", "Reid", "Shaw", "Turner", "Wilkinson",
]
REGIONAL_NAME_POOLS.update({
    "USA": {
        "male": ["Austin", "Blake", "Bryce", "Chase", "Colton", "Derek", "Eli", "Grayson", "Hunter", "Isaac", "Jeremiah", "Jordan", "Logan", "Micah", "Miles", "Myles", "Preston", "Reid", "Shane", "Tanner"],
        "female": ["Addison", "Avery", "Brooke", "Danica", "Harper", "Jenna", "Kelsey", "Lacey", "Madison", "Morgan", "Peyton", "Quinn", "Riley", "Skylar", "Summer", "Taylor", "Teagan", "Trinity", "Whitney", "Zoey"],
        "last": ["Allen", "Baker", "Barnes", "Brooks", "Carter", "Coleman", "Cooper", "Davis", "Ellis", "Fletcher", "Griffin", "Harris", "Henderson", "Johnson", "King", "Lewis", "Mitchell", "Parker", "Robinson", "Russell", "Sanders", "Turner", "Watson", "Young"],
    },
    "Canada": {
        "male": ["Andre", "Benoit", "Brendan", "Corey", "Darren", "Etienne", "Grant", "Julien", "Landon", "Marc", "Mathieu", "Neil", "Pierre", "Rene", "Travis", "Tyler"],
        "female": ["Amelie", "Brianna", "Danielle", "Elise", "Genevieve", "Justine", "Laurie", "Maelle", "Melanie", "Monique", "Renee", "Sabrina", "Valerie", "Veronique", "Yvette", "Zoelle"],
        "last": ["Beaulieu", "Bouchard", "Cote", "Gagnon", "Lacroix", "Lambert", "Lavoie", "Leblanc", "Morin", "Pelletier", "Roy", "Tremblay", "Bennett", "Fraser", "MacKay", "McCarthy", "McKenzie", "OBrien", "Sinclair", "Tanner"],
    },
    "Brazil": {
        "male": ["Caio", "Danilo", "Edson", "Felipe", "Guilherme", "Joao", "Leandro", "Luiz", "Marcelo", "Matheus", "Otavio", "Ronaldo", "Thiago", "Vitor", "Weslley", "Yago"],
        "female": ["Aline", "Brenda", "Clarissa", "Daiane", "Elisa", "Flavia", "Gisele", "Iara", "Juliana", "Larissa", "Leticia", "Marina", "Priscila", "Roberta", "Talita", "Vanessa"],
        "last": ["Barbosa", "Batista", "Coelho", "Cunha", "Freitas", "Goncalves", "Leite", "Moraes", "Nascimento", "Neves", "Pinto", "Rocha", "Siqueira", "Viana", "Vieira", "Xavier", "Campos", "Macedo", "Peixoto", "Queiroz"],
    },
    "Mexico": {
        "male": ["Adan", "Cristian", "Efrain", "Esteban", "Gerardo", "Hector", "Isaias", "Jorge", "Manuel", "Noe", "Ramiro", "Rigoberto", "Saul", "Ulises", "Victor", "Yahir"],
        "female": ["Alejandra", "Belen", "Citlali", "Dulce", "Erika", "Guadalupe", "Itzel", "Jimena", "Karla", "Lourdes", "Montserrat", "Nayeli", "Paloma", "Rocio", "Yesenia", "Zulema"],
        "last": ["Arellano", "Cervantes", "Contreras", "Corona", "Galvan", "Herrera", "Juarez", "Lara", "Maldonado", "Mejia", "Molina", "Montoya", "Padilla", "Renteria", "Rosales", "Salgado", "Soto", "Tapia", "Trejo", "Zamora"],
    },
    "Europe": {
        "male": ["Andrei", "Boris", "Cem", "Dragan", "Emil", "Franco", "Giorgi", "Igor", "Jan", "Krzysztof", "Luka", "Milan", "Nikola", "Oskar", "Petar", "Radoslav", "Szymon", "Valentin", "Wojciech", "Zoran"],
        "female": ["Alena", "Branka", "Cosima", "Dominika", "Eva", "Gianna", "Iva", "Kinga", "Lena", "Magdalena", "Nika", "Oana", "Rada", "Saskia", "Tanja", "Ula", "Vesna", "Weronika", "Zofia", "Zsuzsa"],
        "last": ["Bartosz", "Bauer", "Benedetti", "Berger", "Bianchi", "Cerny", "Dimitrov", "Farkas", "Horvat", "Ilic", "Jovanovic", "Kaczmarek", "Kovalenko", "Mihajlovic", "Nowicki", "Pavlovic", "Radic", "Stojanov", "Todorov", "Wojcik", "Zelenka", "Zoric"],
    },
    "Australia": {
        "male": ["Bailey", "Blair", "Cooper", "Damon", "Hayden", "Jett", "Kai", "Kane", "Mitchell", "Ned", "Rylan", "Taj", "Trent", "Wade", "Zac", "Zander"],
        "female": ["Ashleigh", "Bree", "Charli", "Courtney", "Ella", "Gemma", "Hayley", "Jemma", "Kirra", "Maddie", "Poppy", "Sasha", "Tahlia", "Tess", "Willow", "Zali"],
        "last": ["Barrett", "Baxter", "Brennan", "Dalton", "Dempsey", "Donovan", "Farrell", "Holland", "Kavanagh", "Lawrence", "Maddox", "Morrissey", "Nolan", "OConnell", "Quade", "Rourke", "Sullivan", "Tierney", "Walsh", "Whelan"],
    },
})
REGIONAL_NAME_POOLS.update({
    "Russia": {
        "male": ["Aleksei", "Anatoly", "Artem", "Dmitri", "Evgeny", "Ibragim", "Magomed", "Mikhail", "Rustam", "Sergei", "Timur", "Vadim", "Viktor", "Yuri", "Aslan", "Roman", "Shamil", "Zaur", "Abdul", "Adam", "Albert", "Ali", "Alikhan", "Amir", "Andrei", "Arsen", "Artur", "Bagaudin", "Bekhan", "Danil", "Denis", "Eduard", "Gadzhimurad", "Gasan", "Islam", "Kamil", "Khabib", "Khamzat", "Kurban", "Marat", "Mavlet", "Musa", "Nikita", "Oleg", "Ramazan", "Rashid", "Renat", "Said", "Salman", "Sharapudin", "Tagir", "Umar", "Usman", "Vagab", "Vladimir", "Yaroslav", "Zelimkhan"],
        "female": ["Alina", "Anastasia", "Daria", "Elena", "Irina", "Karina", "Ksenia", "Natalia", "Olga", "Svetlana", "Tatiana", "Yana", "Ekaterina", "Marina", "Polina", "Valeria", "Vera", "Zoya", "Aida", "Amina", "Anna", "Diana", "Elizaveta", "Fatima", "Galina", "Inna", "Kristina", "Lada", "Leyla", "Lilia", "Margarita", "Milana", "Nadezhda", "Oksana", "Regina", "Sabina", "Sofia", "Tamara", "Viktoria", "Zarema"],
        "last": ["Abdulov", "Akhmedov", "Fedorov", "Ivanov", "Karpov", "Khasanov", "Kozlov", "Magomedov", "Mikhailov", "Orlov", "Petrov", "Sokolov", "Volkov", "Yusupov", "Bagaev", "Gusev", "Lebedev", "Morozov", "Nikolaev", "Pavlov", "Romanov", "Suleimanov", "Abdullaev", "Aliev", "Amagov", "Ankalaev", "Askarov", "Ataev", "Batradz", "Beterbiev", "Chimaev", "Dakaev", "Dudaev", "Emelianenko", "Evloev", "Gamzatov", "Gasanov", "Guseinov", "Ismailov", "Kadirov", "Kerimov", "Khalidov", "Khasbulaev", "Khizriev", "Kurbanov", "Magomedsharipov", "Makhachev", "Mineev", "Mirzaev", "Murtazaliev", "Nemkov", "Nurmagomedov", "Oezdemirov", "Rakhmonov", "Rasulov", "Safarov", "Saidov", "Salikhov", "Shabliy", "Sharaev", "Taisumov", "Tsarukyan", "Umalatov", "Vakhitov", "Vasilevsky", "Yan", "Zubairaev"],
    },
    "South Korea": {
        "male": ["Donghyun", "Hyun", "Jaehyun", "Jihoon", "Jin", "Joon", "Junseo", "Minho", "Sanghoon", "Seungwoo", "Taeyoung", "Youngjun", "Byungho", "Geonwoo", "Hajoon", "Seongmin", "Woojin", "Yongho"],
        "female": ["Chaeyoung", "Eunji", "Hana", "Hyejin", "Jiwon", "Minji", "Nari", "Seoyeon", "Sora", "Sujin", "Yejin", "Yuna", "Areum", "Bora", "Dahyun", "Gaeun", "Hyeri", "Soomin"],
        "last": ["Ahn", "Bae", "Choi", "Han", "Hong", "Jeong", "Kang", "Kim", "Kwon", "Lee", "Lim", "Park", "Shin", "Yoon", "Baek", "Cho", "Heo", "Hwang", "Jang", "Moon", "Seo", "Song"],
    },
    "Middle East": {
        "male": ["Abbas", "Adil", "Amir", "Faisal", "Hamza", "Hassan", "Ibrahim", "Khalid", "Mansour", "Omar", "Rami", "Samir", "Tariq", "Zayd", "Bilal", "Karim", "Nabil", "Yusuf"],
        "female": ["Aisha", "Amira", "Dalia", "Farah", "Hana", "Layla", "Mariam", "Nadia", "Noor", "Rania", "Salma", "Yasmin", "Dana", "Hala", "Lina", "Mona", "Reem", "Sara"],
        "last": ["Alavi", "Almasri", "Darwish", "Fakhreddine", "Habib", "Haddad", "Hakim", "Khalil", "Mansour", "Nasser", "Rahman", "Saleh", "Sharif", "Yousef", "Abadi", "Farhat", "Jaber", "Khatib", "Najjar", "Qasim", "Saad", "Zahran"],
    },
    "Africa": {
        "male": ["Ade", "Ayo", "Biko", "Chidi", "Dayo", "Emeka", "Idris", "Kofi", "Kwame", "Mandla", "Nuru", "Sibusiso", "Tendai", "Yemi", "Bongani", "Femi", "Jelani", "Thabo"],
        "female": ["Abena", "Adaeze", "Ama", "Amara", "Ayana", "Chiamaka", "Imani", "Lerato", "Nia", "Nomsa", "Thandi", "Zuri", "Adanna", "Efua", "Kendi", "Makena", "Naledi", "Sade"],
        "last": ["Abdalla", "Adebayo", "Diallo", "Kamara", "Mensah", "Mokoena", "Ndlovu", "Nkosi", "Okafor", "Osei", "Sissoko", "Traore", "Yeboah", "Zuma", "Banda", "Dlamini", "Kone", "Mbeki", "Mwangi", "Obi", "Sow", "Tembo"],
    },
})

# Keep every local scene deep enough to support century-long generation without
# leaning on the same handful of names. These additions take each regional bank
# to at least 40 male names, 40 female names and 50 surnames; Russia remains
# deliberately larger because several major and feeder pathways recruit there.
REGIONAL_NAME_POOL_EXPANSIONS = {
    "Japan": {
        "male": ["Kaito", "Minato"],
        "female": ["Asuka", "Eri", "Fumika", "Hinata", "Kasumi", "Miyu"],
        "last": ["Abe", "Chiba", "Ishida", "Kondo", "Miura", "Murakami", "Nakajima", "Ogawa", "Okada", "Sasaki", "Shibata", "Sugiyama"],
    },
    "Asia": {
        "female": ["Mina", "Priya"],
        "last": ["Abdullah", "Bautista", "Cheung", "Das", "Gupta", "Hernandez", "Lestari", "Rahman", "Singh", "Wijaya"],
    },
    "UK": {
        "male": ["Archie", "Curtis", "Jordan"],
        "female": ["Freya", "Lucy", "Molly", "Rhiannon"],
        "last": ["Atkinson", "Barker", "Davies", "Evans", "Foster", "Gallagher", "Hamilton", "Kavanagh", "Morgan", "Roberts", "Stewart", "Thomas", "Williams"],
    },
    "USA": {
        "male": ["Aaron", "Adrian", "Brandon", "Caleb", "Cody", "Dominic", "Ethan", "Gabriel", "Jared", "Jason", "Jonah", "Justin", "Marcus", "Nolan", "Parker", "Ramon", "Trevor", "Wesley", "Xavier", "Zane"],
        "female": ["Alexis", "Alyssa", "Brittany", "Camille", "Cassidy", "Cheyenne", "Dakota", "Elena", "Hailey", "Jasmine", "Kayla", "Kennedy", "Mackenzie", "Maya", "Natalie", "Reagan", "Savannah", "Shelby", "Sierra", "Vanessa"],
        "last": ["Adams", "Anderson", "Bailey", "Bell", "Bennett", "Bryant", "Butler", "Collins", "Cook", "Cox", "Edwards", "Fisher", "Foster", "Freeman", "Graham", "Gray", "Green", "Hayes", "Hill", "Howard", "Jenkins", "Morris", "Murphy", "Price", "Reed", "Rivera"],
    },
    "Canada": {
        "male": ["Adam", "Alexandre", "Antoine", "Calum", "Cedric", "Colin", "Dominic", "Elliot", "Eric", "Frederic", "Gavin", "Hugo", "Jean", "Jeremy", "Keegan", "Laurent", "Luc", "Nicolas", "Olivier", "Patrick", "Remi", "Samuel", "Simon", "Xavier"],
        "female": ["Alexandra", "Ariane", "Beatrice", "Camille", "Caroline", "Celine", "Charlotte", "Chantal", "Emilie", "Florence", "Gabrielle", "Isabelle", "Jacqueline", "Joelle", "Madeleine", "Marianne", "Nathalie", "Noemie", "Rosalie", "Simone", "Sophie", "Sylvie", "Therese", "Vivienne"],
        "last": ["Bergeron", "Bernier", "Caron", "Charbonneau", "Desjardins", "Dubois", "Dufour", "Fortin", "Fournier", "Gauthier", "Girard", "Gordon", "Grenier", "Leclerc", "Lemieux", "Mercier", "Paquette", "Parent", "Poirier", "Renaud", "Richard", "Savard", "Simard", "Thibault", "Vachon", "Wells", "Wilson", "Young", "Cloutier", "Lapointe"],
    },
    "Brazil": {
        "male": ["Adriano", "Alexandre", "Anderson", "Bruno", "Carlos", "Cesar", "Douglas", "Eduardo", "Fabio", "Fernando", "Gabriel", "Henrique", "Igor", "Jean", "Jose", "Lucas", "Marcos", "Murilo", "Paulo", "Pedro", "Rafael", "Renan", "Rodrigo", "Vinicius"],
        "female": ["Amanda", "Ana", "Beatriz", "Camila", "Carla", "Carolina", "Cristiane", "Daniela", "Debora", "Fernanda", "Gabriela", "Isabela", "Jessica", "Luana", "Mariana", "Mirela", "Natalia", "Patricia", "Rafaela", "Renata", "Sabrina", "Samara", "Taina", "Yasmin"],
        "last": ["Almeida", "Alves", "Amorim", "Andrade", "Araujo", "Cardoso", "Carvalho", "Castro", "Costa", "Dias", "Fernandes", "Ferreira", "Figueiredo", "Lima", "Lopes", "Martins", "Mendes", "Monteiro", "Moreira", "Nogueira", "Oliveira", "Pereira", "Ribeiro", "Rodrigues", "Santana", "Santos", "Silva", "Souza", "Teixeira", "Torres"],
    },
    "Mexico": {
        "male": ["Alejandro", "Alonso", "Angel", "Antonio", "Arturo", "Carlos", "Cesar", "Diego", "Eduardo", "Emiliano", "Enrique", "Fernando", "Francisco", "Gilberto", "Guillermo", "Jaime", "Jesus", "Jose", "Luis", "Marco", "Mauricio", "Rafael", "Ricardo", "Sergio"],
        "female": ["Adriana", "Ana", "Beatriz", "Camila", "Carolina", "Cecilia", "Claudia", "Daniela", "Diana", "Elena", "Fernanda", "Gabriela", "Isabel", "Jacqueline", "Jessica", "Laura", "Liliana", "Lucia", "Mariana", "Natalia", "Paola", "Renata", "Sofia", "Valeria"],
        "last": ["Aguilar", "Alvarez", "Bautista", "Cabrera", "Camacho", "Castillo", "Chavez", "Delgado", "Diaz", "Dominguez", "Escobar", "Espinoza", "Flores", "Garcia", "Gomez", "Gonzalez", "Gutierrez", "Hernandez", "Lopez", "Marquez", "Martinez", "Medina", "Morales", "Navarro", "Ortega", "Ramirez", "Reyes", "Rodriguez", "Romero", "Vargas"],
    },
    "Europe": {
        "male": ["Aleksandar", "Bartosz", "Bruno", "Damir", "Dario", "Filip", "Florian", "Goran", "Jakub", "Jiri", "Kristijan", "Laszlo", "Lorenzo", "Matej", "Matteo", "Michal", "Miroslav", "Nikolai", "Pavel", "Pieter"],
        "female": ["Adriana", "Aleksandra", "Anja", "Bianca", "Chiara", "Dajana", "Eliska", "Franziska", "Ines", "Ivana", "Jelena", "Katarina", "Klara", "Lucia", "Marta", "Milena", "Petra", "Romana", "Sanja", "Tea"],
        "last": ["Andersson", "Babic", "Blazek", "Boer", "Bonetti", "Boskovic", "Dabrowski", "DeVries", "Ferraro", "Gruber", "Hansen", "Havel", "Jensen", "Kovacs", "Kral", "Lombardi", "Markovic", "Novak", "Popescu", "Rossi", "Schmidt", "Svensson", "VanDijk", "Varga", "Vesely", "Weber", "Zajac", "Petrovic"],
    },
    "Australia": {
        "male": ["Angus", "Archie", "Ben", "Brodie", "Callan", "Cameron", "Darcy", "Ethan", "Flynn", "Hamish", "Harrison", "Heath", "Jack", "Jai", "Lachlan", "Liam", "Mason", "Noah", "Riley", "Ryan", "Sebastian", "Toby", "William", "Xavier"],
        "female": ["Abbey", "Alana", "Amelia", "Bridget", "Caitlin", "Chelsea", "Chloe", "Georgia", "Hannah", "Imogen", "Indiana", "Isla", "Jessica", "Kiara", "Lara", "Matilda", "Mia", "Olivia", "Ruby", "Sienna", "Sophie", "Stevie", "Tayla", "Zoe"],
        "last": ["Andrews", "Armstrong", "Bennett", "Brown", "Campbell", "Clarke", "Collins", "Cook", "Edwards", "Evans", "Fisher", "Fitzgerald", "Fraser", "Gibson", "Graham", "Harris", "Hayes", "Hudson", "Johnson", "Kelly", "Martin", "McDonald", "Mitchell", "Murphy", "Parker", "Reid", "Taylor", "Thompson", "Walker", "Wilson"],
    },
    "South Korea": {
        "male": ["Chulsoo", "Doyun", "Eunho", "Gwangsu", "Hyunwoo", "Jaemin", "Jisung", "Jongho", "Junho", "Kyungmin", "Minjun", "Seungho", "Sungmin", "Taehyun", "Wonho", "Youngho", "Yunseok", "Changmin", "Dongwook", "Kihyun", "Sangmin", "Seungmin"],
        "female": ["Bomin", "Chaewon", "Eunchae", "Eunseo", "Hayoon", "Heejin", "Hyemin", "Jisoo", "Jiyoung", "Kyunghee", "Minseo", "Nayoung", "Seohyun", "Seulgi", "Sohee", "Soyeon", "Yeonhee", "Yoonah", "Haeun", "Jimin", "Sunhee", "Yuri"],
        "last": ["Byun", "Cha", "Chun", "Do", "Eom", "Ha", "Ham", "Huh", "Im", "Jin", "Ko", "Koo", "Kwak", "Ma", "Min", "Na", "Nam", "Noh", "Oh", "Roh", "Ryu", "Son", "Yang", "Yu", "Won", "Yeo", "Tak", "Pyo"],
    },
    "Middle East": {
        "male": ["Ahmad", "Ali", "Anas", "Ayman", "Bashir", "Fadi", "Farid", "Hadi", "Haider", "Jamal", "Kamal", "Mahdi", "Malik", "Marwan", "Mustafa", "Nasser", "Qasim", "Rashid", "Saeed", "Walid", "Yahya", "Zain"],
        "female": ["Aaliyah", "Aya", "Dima", "Eman", "Fatima", "Ghada", "Hiba", "Iman", "Jamila", "Khadija", "Laila", "Lamia", "Leila", "Malak", "Marwa", "Noura", "Rasha", "Sahar", "Samira", "Sana", "Yara", "Zahra"],
        "last": ["Abbas", "Abdullah", "Ahmed", "Akhtar", "AlFarsi", "AlHassan", "AlKhalifa", "AlMansoori", "AlQasimi", "Amin", "Ansari", "Ashraf", "Aziz", "Bakri", "Barakat", "Bashir", "Daoud", "Fahmy", "Hamdan", "Hamidi", "Hussein", "Ibrahim", "Kader", "Karimi", "Mahmoud", "Masri", "Mirza", "Moussa"],
    },
    "Africa": {
        "male": ["Abdou", "Amadou", "Ayodele", "Babatunde", "Cheikh", "Chukwudi", "Demba", "Efe", "Ikenna", "Ismail", "Jabari", "Kamau", "Kelechi", "Lamin", "Malik", "Moussa", "Obinna", "Oluwaseun", "Sekou", "Tariq", "Temba", "Yannick"],
        "female": ["Aissatou", "Amina", "Amira", "Ayomide", "Binta", "Chioma", "Esi", "Fatou", "Hadiza", "Ifeoma", "Jamila", "Khadija", "Lindiwe", "Mariama", "Nana", "Ngozi", "Oluchi", "Simisola", "Tariro", "Thembeka", "Wanjiku", "Zainab"],
        "last": ["Abubakar", "Adeyemi", "Agbaje", "Akinola", "Amadou", "Asante", "Balogun", "Bassey", "Chukwu", "Coulibaly", "Diop", "Eze", "Fofana", "Ibrahim", "Kabila", "Keita", "Mabena", "Mahlangu", "Mbaye", "Musa", "Ndour", "Nwosu", "Ogunleye", "Onyango", "Sarr", "Toure", "Udo", "Wekesa"],
    },
}
for _region, _groups in REGIONAL_NAME_POOL_EXPANSIONS.items():
    for _group, _names in _groups.items():
        _existing = REGIONAL_NAME_POOLS[_region][_group]
        _existing.extend(name for name in _names if name not in _existing)

REGIONAL_NAME_POOL_MINIMUM_ADDITIONS = {
    "Japan": {
        "male": ["Akinori", "Daichi", "Haruki", "Hideki", "Kazuma", "Kenji", "Kota", "Ryo", "Shohei", "Yuma"],
        "female": ["Airi", "Chika", "Haruna", "Keiko", "Madoka", "Manami", "Megumi", "Natsuki", "Risa", "Yoko"],
    },
    "Asia": {
        "male": ["Arjun", "Bao", "Duy", "Farhan", "Harish", "Jian", "Pranav", "Surya", "Vannak"],
        "female": ["Anjali", "Devi", "Kavya", "Lian", "Mai", "Neha", "Rani", "Siti", "Trang", "Yuna"],
    },
    "UK": {
        "male": ["Adam", "Charlie", "Craig", "Daniel", "George", "James", "Luke", "Matthew", "Ryan", "Thomas"],
        "female": ["Alice", "Charlotte", "Daisy", "Emily", "Erin", "Louise", "Olivia", "Pippa", "Sarah", "Victoria"],
    },
    "USA": {
        "male": ["Aiden", "Cole", "Connor", "Dylan", "Gavin", "Ian", "Kyle", "Landon", "Mason", "Tyler"],
        "female": ["Autumn", "Brielle", "Carly", "Delaney", "Faith", "Lauren", "Naomi", "Paige", "Sydney", "Tessa"],
    },
    "Canada": {
        "male": ["Alain", "Charles", "David", "Felix", "Francis", "Georges", "Maxime", "Philippe", "Sebastien", "Vincent"],
        "female": ["Audrey", "Claire", "Dominique", "Evelyne", "Helene", "Julie", "Lise", "Marie", "Martine", "Odette"],
    },
    "Brazil": {
        "male": ["Andre", "Diego", "Emerson", "Ewerton", "Fabricio", "Gerson", "Junior", "Renato", "Rogerio", "Wellington"],
        "female": ["Barbara", "Bruna", "Cris", "Eduarda", "Geovana", "Ingrid", "Janaira", "Livia", "Monique", "Thais"],
    },
    "Mexico": {
        "male": ["Abel", "Agustin", "Benjamin", "Dario", "Gustavo", "Hugo", "Julio", "Leonardo", "Miguel", "Oscar"],
        "female": ["Alma", "Andrea", "Aurora", "Carmen", "Fabiola", "Graciela", "Lorena", "Marta", "Pilar", "Veronica"],
    },
    "Europe": {
        "male": ["Anton", "Dominik", "Erik", "Henrik", "Ivan", "Martin", "Patrik", "Rene", "Stefan", "Tomas"],
        "female": ["Agata", "Aneta", "Dagmar", "Helena", "Jana", "Marija", "Nina", "Sabina", "Silvia", "Tamara"],
    },
    "Australia": {
        "male": ["Aidan", "Caleb", "Connor", "Dylan", "Hugh", "Isaac", "Jake", "Joel", "Oliver", "Rhys"],
        "female": ["Alyssa", "Bianca", "Cassandra", "Eliza", "Grace", "Lucy", "Maya", "Paige", "Sarah", "Victoria"],
    },
    "Russia": {
        "female": ["Aleksandra", "Alla", "Arina", "Inessa", "Larisa", "Lyudmila", "Nina", "Roza", "Ulyana", "Yulia"],
    },
    "South Korea": {
        "male": ["Beomseok", "Daehyun", "Haneul", "Inseong", "Jaewon", "Jungwoo", "Minseok", "Seojun", "Taesung", "Wooseok"],
        "female": ["Ayoung", "Chaerin", "Eunyoung", "Hyerin", "Jieun", "Minkyung", "Seunghee", "Sohyun", "Yeji", "Yewon"],
    },
    "Middle East": {
        "male": ["Adnan", "Bassam", "Habib", "Jafar", "Laith", "Nadim", "Riad", "Sami", "Tamer", "Wassim"],
        "female": ["Abeer", "Asma", "Hind", "Inaya", "Jana", "Maya", "Muna", "Rima", "Shireen", "Zeinab"],
    },
    "Africa": {
        "male": ["Abel", "Boubacar", "Cedric", "Elijah", "Hamza", "Issa", "Joseph", "Mamadou", "Nelson", "Samuel"],
        "female": ["Adwoa", "Aicha", "Blessing", "Esther", "Halima", "Joy", "Mariam", "Mercy", "Nneka", "Sarah"],
    },
}
for _region, _groups in REGIONAL_NAME_POOL_MINIMUM_ADDITIONS.items():
    for _group, _names in _groups.items():
        _existing = REGIONAL_NAME_POOLS[_region][_group]
        _existing.extend(name for name in _names if name not in _existing)

try:
    _uk_name_payload = json.loads((ASSET_DIR / "uk_first_names.json").read_text(encoding="utf-8"))
except (OSError, ValueError, TypeError):
    _uk_name_payload = {}
_uk_neutral_names = _uk_name_payload.get("neutral", []) if isinstance(_uk_name_payload, dict) else []
for _group, _asset_group in (("male", "male"), ("female", "female")):
    _existing = REGIONAL_NAME_POOLS["UK"][_group]
    _incoming = (_uk_name_payload.get(_asset_group, []) if isinstance(_uk_name_payload, dict) else []) + _uk_neutral_names
    _existing.extend(name for name in _incoming if isinstance(name, str) and name and name not in _existing)

# Human-name data imported from the public corpora dataset. Norwegian data is
# gendered at source, while the shared North American entries are explicitly
# neutral. Surnames are safe to share across regional pools. Keeping the data
# in an asset makes future name-bank refreshes a data update rather than code.
try:
    _corpora_name_payload = json.loads((ASSET_DIR / "corpora_human_names.json").read_text(encoding="utf-8"))
except (OSError, ValueError, TypeError):
    _corpora_name_payload = {}


def _extend_unique_names(target, incoming):
    """Append valid names once, treating case-only variants as duplicates."""
    seen = {str(name).strip().casefold() for name in target if isinstance(name, str) and name.strip()}
    for name in incoming if isinstance(incoming, list) else []:
        if not isinstance(name, str):
            continue
        cleaned = name.strip()
        normalized = cleaned.casefold()
        if cleaned and normalized not in seen:
            target.append(cleaned)
            seen.add(normalized)


_extend_unique_names(REGIONAL_NAME_POOLS["Europe"]["male"], _corpora_name_payload.get("norwegian_male", []))
_extend_unique_names(REGIONAL_NAME_POOLS["Europe"]["female"], _corpora_name_payload.get("norwegian_female", []))
_extend_unique_names(REGIONAL_NAME_POOLS["Europe"]["last"], _corpora_name_payload.get("norwegian_last", []))
for _north_american_region in ("USA", "Canada", "Australia"):
    _extend_unique_names(REGIONAL_NAME_POOLS[_north_american_region]["male"], _corpora_name_payload.get("unisex_first_names", []))
    _extend_unique_names(REGIONAL_NAME_POOLS[_north_american_region]["female"], _corpora_name_payload.get("unisex_first_names", []))
    _extend_unique_names(REGIONAL_NAME_POOLS[_north_american_region]["last"], _corpora_name_payload.get("north_american_last", []))
for _hispanic_region in ("Brazil", "Mexico"):
    _extend_unique_names(REGIONAL_NAME_POOLS[_hispanic_region]["last"], _corpora_name_payload.get("hispanic_last", []))
_extend_unique_names(LAST_NAMES, _corpora_name_payload.get("north_american_last", []))
_extend_unique_names(LAST_NAMES, _corpora_name_payload.get("hispanic_last", []))
_extend_unique_names(LAST_NAMES, _corpora_name_payload.get("norwegian_last", []))

# Older hand-written banks used direct list concatenation. Normalize every
# shipped pool once so duplicate data cannot narrow the generator's real range.
for _name_bank in (FIRST_NAMES, FEMALE_FIRST_NAMES, LAST_NAMES):
    _deduplicated = []
    _extend_unique_names(_deduplicated, _name_bank)
    _name_bank[:] = _deduplicated
for _regional_groups in REGIONAL_NAME_POOLS.values():
    for _regional_bank in _regional_groups.values():
        _deduplicated = []
        _extend_unique_names(_deduplicated, _regional_bank)
        _regional_bank[:] = _deduplicated

# Name banks deliberately keep their shipped spellings, including accents and
# the packaged regional directories' exact casing. Two banks can therefore hold
# the same name in different forms ("Garcia" and "García"), which is fine here:
# fighter uniqueness is enforced on an accent- and case-folded identity when a
# fighter is actually named, in AdminMixin.fighter_name_key.

# --- Eurasian Fight Circuit -------------------------------------------------
# The Caucasus and Central Asia produce a distinctive talent profile: heavy
# amateur wrestling, judo, sambo and boxing backgrounds feeding into MMA. The
# circuit is modelled as a male-only feeder, so its sub-regions carry their own
# name banks, nationality mapping and style probability biases rather than
# reusing the generic "Russia" pool.
EURASIAN_FIGHT_CIRCUIT_NAME = "Eurasian Fight Circuit"
EURASIAN_FIGHT_CIRCUIT_DESCRIPTION = (
    "Eurasian Fight Circuit is a regional promotion recruiting fighters from the Caucasus and Central Asia. "
    "Known for producing elite wrestlers, combat sambo specialists, judoka and technically accomplished amateur "
    "boxers, it has become one of the world's most demanding proving grounds for emerging MMA talent."
)
try:
    _eurasian_name_payload = json.loads((ASSET_DIR / "eurasian_names.json").read_text(encoding="utf-8"))
except (OSError, ValueError, TypeError):
    _eurasian_name_payload = {}

EURASIAN_NAME_POOLS = {}
for _eur_region, _eur_groups in (_eurasian_name_payload.get("regions", {}) or {}).items():
    if not isinstance(_eur_groups, dict):
        continue
    _male, _last = [], []
    _extend_unique_names(_male, _eur_groups.get("first_names_male", []))
    _extend_unique_names(_last, _eur_groups.get("surnames_male", []))
    if _male and _last:
        EURASIAN_NAME_POOLS[_eur_region] = {"male": _male, "last": _last}

# Sourcing weights: primary republics and states supply most of the roster,
# secondary regions a steady trickle, rare ones the occasional outlier.
EURASIAN_REGION_WEIGHTS = {
    "Dagestan": 17, "Chechnya": 13, "Georgia": 11, "Azerbaijan": 10,
    "Kazakhstan": 10, "Uzbekistan": 9, "North Ossetia-Alania": 8,
    "Armenia": 6, "Kyrgyzstan": 5, "Tajikistan": 4, "Ingushetia": 3,
    "Kabardino-Balkaria": 2, "Karachay-Cherkessia": 1, "Turkmenistan": 1,
}

# Dagestan, Chechnya, Ingushetia, North Ossetia, Kabardino-Balkaria and
# Karachay-Cherkessia are constituent republics of Russia, so their fighters
# carry Russian nationality with the republic recorded as their origin.
EURASIAN_REGION_NATIONALITY = {
    "Dagestan": "Russian", "Chechnya": "Russian", "Ingushetia": "Russian",
    "North Ossetia-Alania": "Russian", "Kabardino-Balkaria": "Russian",
    "Karachay-Cherkessia": "Russian",
    "Georgia": "Georgian", "Armenia": "Armenian", "Azerbaijan": "Azerbaijani",
    "Kazakhstan": "Kazakh", "Uzbekistan": "Uzbek", "Kyrgyzstan": "Kyrgyz",
    "Tajikistan": "Tajik", "Turkmenistan": "Turkmen",
}

# Style biases are probabilities, not rules: a Dagestani kickboxer or Uzbek
# submission specialist should still turn up occasionally. Each entry is a
# (style, weight) list sampled per fighter.
_EUR_WRESTLE = [("Freestyle Wrestler", 16), ("Wrestler", 14), ("Catch Wrestler", 6)]
_EUR_WRESTLE_BOX = [("Well-Rounded", 14), ("MMA Generalist", 6)]
_EUR_SAMBO = [("Sambo", 13)]
_EUR_JUDO = [("Judo", 11)]
_EUR_BOX = [("Boxer", 10)]
_EUR_SUB = [("Submission Grappler", 2), ("Grappler", 2), ("BJJ", 1)]
_EUR_KICK = [("Kickboxer", 1), ("Muay Thai", 1), ("Dutch Kickboxer", 1)]
_EURASIAN_BASE_STYLES = _EUR_WRESTLE + _EUR_WRESTLE_BOX + _EUR_SAMBO + _EUR_JUDO + _EUR_BOX + _EUR_SUB + _EUR_KICK


def _eurasian_styles(**overrides):
    """Base circuit distribution with per-region multipliers applied."""
    return [(style, max(1, round(weight * overrides.get(style, 1.0)))) for style, weight in _EURASIAN_BASE_STYLES]


EURASIAN_REGION_STYLES = {
    # Freestyle wrestling and combat sambo heartland.
    "Dagestan": _eurasian_styles(**{"Freestyle Wrestler": 1.7, "Wrestler": 1.4, "Sambo": 1.4, "Judo": 0.5, "Boxer": 0.6}),
    "Chechnya": _eurasian_styles(**{"Freestyle Wrestler": 1.6, "Wrestler": 1.5, "Sambo": 1.3, "Judo": 0.6, "Boxer": 0.7}),
    "Ingushetia": _eurasian_styles(**{"Freestyle Wrestler": 1.6, "Wrestler": 1.5, "Sambo": 1.2, "Judo": 0.6, "Boxer": 0.7}),
    # Explosive wrestlers with powerful entries.
    "North Ossetia-Alania": _eurasian_styles(**{"Freestyle Wrestler": 1.8, "Wrestler": 1.5, "Judo": 0.6, "Boxer": 0.7}),
    "Kabardino-Balkaria": _eurasian_styles(**{"Wrestler": 1.4, "Judo": 1.3, "Sambo": 1.2, "Well-Rounded": 1.2}),
    "Karachay-Cherkessia": _eurasian_styles(**{"Wrestler": 1.4, "Judo": 1.3, "Sambo": 1.2, "Well-Rounded": 1.2}),
    # Judo, Chidaoba and Greco-Roman: throw and trip specialists.
    "Georgia": _eurasian_styles(**{"Judo": 3.0, "Wrestler": 1.2, "Freestyle Wrestler": 0.8, "Boxer": 0.6, "Submission Grappler": 1.5}),
    # Greco-Roman and boxing: clinch fighters with power punching.
    "Armenia": _eurasian_styles(**{"Wrestler": 1.5, "Boxer": 1.6, "Sambo": 1.2, "Judo": 0.8}),
    # Athletic wrestle-boxers with explosive takedowns.
    "Azerbaijan": _eurasian_styles(**{"Freestyle Wrestler": 1.4, "Well-Rounded": 1.5, "Judo": 1.2, "Boxer": 1.1}),
    # Elite amateur boxing systems.
    "Kazakhstan": _eurasian_styles(**{"Boxer": 2.6, "Well-Rounded": 1.4, "Sambo": 1.1, "Freestyle Wrestler": 0.7, "Wrestler": 0.8}),
    "Uzbekistan": _eurasian_styles(**{"Boxer": 2.3, "Judo": 1.4, "Sambo": 1.2, "Well-Rounded": 1.2, "Freestyle Wrestler": 0.7}),
    # Scramblers, pressure grapplers and submission hunters.
    "Kyrgyzstan": _eurasian_styles(**{"Freestyle Wrestler": 1.5, "Sambo": 1.3, "Submission Grappler": 2.0, "Grappler": 2.0, "Boxer": 0.7}),
    "Tajikistan": _eurasian_styles(**{"Wrestler": 1.5, "Sambo": 1.3, "Boxer": 1.1, "Judo": 0.8}),
    # Raw belt-wrestling clinch specialists.
    "Turkmenistan": _eurasian_styles(**{"Wrestler": 1.8, "Judo": 1.2, "Boxer": 0.6, "Well-Rounded": 0.6, "Submission Grappler": 0.5}),
}

# Generic "Russia" generation should still be able to draw on this data.
for _eur_region, _eur_pool in EURASIAN_NAME_POOLS.items():
    _extend_unique_names(REGIONAL_NAME_POOLS["Russia"]["male"], _eur_pool["male"])
    _extend_unique_names(REGIONAL_NAME_POOLS["Russia"]["last"], _eur_pool["last"])
    _extend_unique_names(LAST_NAMES, _eur_pool["last"])

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
    "Sambo": ("throws", "chain_wrestling", "top_control", "leg_locks"),
    "BJJ": ("submission_attack", "guard_work", "back_control", "leg_locks"),
    "Clinch": ("clinch_control", "dirty_boxing", "knees", "clinch_takedowns"),
    "Conditioning": ("conditioning", "resilience", "stun_recovery", "weight_cutting"),
    "Prospect Development": ("dedication", "adaptability", "discipline", "confidence"),
    "Gameplanning": ("composure", "consistency", "fight_iq", "adaptability"),
}
