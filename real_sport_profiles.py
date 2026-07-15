"""Curated, deterministic profiles for the real-name child-sport rosters.

Ratings represent prime competitive ability inside the athlete's own sport, not
MMA ability or fame.  Records are a fixed database snapshot where dependable
career totals are commonly published; sports without one universal pro ledger
use a conservative seeded circuit record.  The profile metadata is copied into
the editable universe JSON, so custom universes can change every value.
"""

SPORT_PROFILE_VERSION = 1


# One explicit rating for every athlete in the matching built-in roster order.
# The scale uses 99 only for genuine all-time standard-setting careers.
SPORT_RATINGS = {
    "Boxing": [
        97, 96, 94, 96, 96, 94, 96, 94, 93, 92, 95, 96, 94, 93, 93, 92, 92,
        91, 92, 91, 95, 90, 94, 94, 92, 90, 89, 86, 88, 90, 87, 86, 91, 87,
        87, 87, 87, 86, 89, 84, 94, 92, 91, 89, 90, 89, 90, 92, 91, 89,
    ],
    "Kickboxing": [
        96, 97, 94, 95, 93, 90, 95, 94, 94, 92, 96, 94, 94, 94, 95, 92, 91,
        92, 93, 90, 92, 89, 91, 90, 91, 88, 85, 91, 95, 87, 86, 94, 93, 94,
        93, 91, 90, 88, 91, 88, 89, 84, 88, 84, 86, 89, 90, 86, 87, 86,
    ],
    "Muay Thai": [
        98, 97, 97, 95, 93, 95, 94, 92, 94, 96, 94, 94, 97, 93, 96, 94, 94,
        95, 94, 96, 93, 92, 95, 96, 92, 94, 91, 91, 95, 94, 90, 88, 89, 92,
        93, 91, 91, 90, 92, 89, 95, 91, 90, 92, 87, 88, 88, 89, 91, 86,
    ],
    "Lethwei": [96, 89, 95, 91, 96, 93, 88, 94, 90, 88, 87, 89, 86, 90, 85, 84, 85, 83, 82, 82],
    "Wrestling": [
        99, 98, 97, 96, 98, 99, 96, 97, 95, 94, 96, 97, 96, 94, 94, 95, 94,
        95, 94, 94, 95, 96, 97, 94, 96, 97, 92, 91, 91, 98, 99, 94, 91, 91,
        93, 97, 90, 94, 95, 93, 92, 91, 90, 90, 92, 90, 89, 88, 88, 93,
    ],
    "Brazilian Jiu-Jitsu": [
        99, 99, 98, 98, 97, 99, 97, 95, 95, 96, 94, 97, 96, 95, 94, 96, 96,
        93, 94, 98, 92, 90, 92, 96, 94, 93, 94, 95, 94, 96, 94, 92, 96, 94,
        90, 95, 97, 96, 97, 97, 96, 94, 92, 93, 91, 94, 93, 93, 91, 96,
    ],
}


BOXING_RECORDS = {
    "Floyd Mayweather Jr": (50, 0, 0), "Manny Pacquiao": (62, 8, 2), "Canelo Alvarez": (63, 3, 2),
    "Terence Crawford": (42, 0, 0), "Oleksandr Usyk": (24, 0, 0), "Vasiliy Lomachenko": (18, 3, 0),
    "Naoya Inoue": (31, 0, 0), "Gennady Golovkin": (42, 2, 1), "Wladimir Klitschko": (64, 5, 0),
    "Vitali Klitschko": (45, 2, 0), "Lennox Lewis": (41, 2, 1), "Roy Jones Jr": (66, 10, 0),
    "Bernard Hopkins": (55, 8, 2), "Oscar De La Hoya": (39, 6, 0), "Juan Manuel Marquez": (56, 7, 1),
    "Erik Morales": (52, 9, 0), "Marco Antonio Barrera": (67, 7, 0), "Miguel Cotto": (41, 6, 0),
    "Felix Trinidad": (42, 3, 0), "Shane Mosley": (49, 10, 1), "Andre Ward": (32, 0, 0),
    "Sergey Kovalev": (35, 5, 1), "Artur Beterbiev": (21, 1, 0), "Dmitry Bivol": (24, 1, 0),
    "Tyson Fury": (34, 2, 1), "Anthony Joshua": (29, 4, 0), "Deontay Wilder": (44, 4, 1),
    "Andy Ruiz Jr": (35, 2, 0), "Zhilei Zhang": (27, 3, 1), "Joseph Parker": (36, 3, 0),
    "Jermell Charlo": (35, 2, 1), "Jermall Charlo": (34, 0, 0), "Errol Spence Jr": (28, 1, 0),
    "Keith Thurman": (31, 1, 0), "Shawn Porter": (31, 4, 1), "Danny Garcia": (37, 3, 0),
    "Amir Khan": (34, 6, 0), "Kell Brook": (40, 3, 0), "Timothy Bradley": (33, 2, 1),
    "Devon Alexander": (27, 8, 1), "Roman Gonzalez": (52, 4, 0), "Nonito Donaire": (42, 8, 0),
    "Juan Francisco Estrada": (45, 4, 0), "Srisaket Sor Rungvisai": (58, 6, 1), "Kazuto Ioka": (31, 3, 1),
    "Donnie Nietes": (43, 2, 6), "Mikey Garcia": (40, 2, 0), "Gervonta Davis": (30, 0, 1),
    "Shakur Stevenson": (24, 0, 0), "Devin Haney": (32, 0, 0),
}

KICKBOXING_RECORDS = {
    "Ernesto Hoost": (99, 21, 1), "Giorgio Petrosyan": (106, 3, 2), "Semmy Schilt": (43, 6, 1),
    "Peter Aerts": (106, 35, 2), "Remy Bonjasky": (78, 20, 0), "Badr Hari": (106, 17, 0),
    "Buakaw Banchamek": (244, 24, 14), "Andy Hug": (38, 9, 0), "Ramon Dekkers": (186, 36, 2),
    "Rob Kaman": (98, 12, 4), "Rico Verhoeven": (66, 10, 0), "Tenshin Nasukawa": (44, 0, 0),
    "Sitthichai Sitsongpeenong": (129, 36, 5), "Superbon Singha Mawynn": (116, 37, 0),
    "Chingiz Allazov": (61, 6, 0), "Artem Levin": (56, 6, 2), "Nieky Holzken": (95, 18, 0),
    "Masato Kobayashi": (55, 6, 2), "Andy Souwer": (161, 23, 1), "Mike Zambidis": (158, 24, 0),
    "Mirko Cro Cop": (26, 8, 0), "Gokhan Saki": (82, 18, 0), "Tyrone Spong": (107, 7, 1),
    "Jerome Le Banner": (87, 23, 2), "Jorina Baars": (49, 1, 3), "Lucia Rijker": (36, 0, 1),
    "Anissa Meksen": (103, 6, 0), "Cedric Doumbe": (75, 7, 1), "Marat Grigorian": (67, 14, 1),
    "Ray Sefo": (56, 22, 1), "Mark Hunt": (30, 13, 0), "Alistair Overeem": (11, 4, 0),
}

MUAY_THAI_RECORDS = {
    "Samart Payakaroon": (129, 19, 2), "Dieselnoi Chor Thanasukarn": (110, 5, 0), "Saenchai": (327, 49, 2),
    "Buakaw Banchamek": (244, 24, 14), "Rodtang Jitmuangnon": (272, 43, 10),
    "Nong-O Gaiyanghadao": (268, 56, 1), "Sam-A Gaiyanghadao": (373, 48, 9),
    "Petchmorakot Petchyindee": (171, 35, 2), "Superbon Singha Mawynn": (116, 37, 0),
    "Superlek Kiatmuu9": (136, 29, 4), "Yodsanklai Fairtex": (202, 74, 4), "Ramon Dekkers": (186, 36, 2),
    "Apidej Sit-Hirun": (340, 10, 1), "Namsaknoi Yudthagarngamtorn": (280, 15, 5),
    "Kaensak Sor Ploenjit": (208, 40, 2), "Somrak Khamsing": (150, 20, 3),
    "Karuhat Sor Supawan": (190, 40, 5), "Petchboonchu FA Group": (240, 52, 3),
    "Anuwat Kaewsamrit": (180, 42, 4), "Panpayak Jitmuangnon": (248, 42, 3),
    "Tawanchai PK Saenchai": (132, 32, 2), "Seksan Or Kwanmuang": (200, 75, 6),
    "Liam Harrison": (92, 26, 2), "John Wayne Parr": (99, 35, 1), "Nadaka Yoshinari": (61, 6, 1),
}

LETHWEI_RECORDS = {
    "Tun Tun Min": (57, 4, 1), "Dave Leduc": (29, 5, 6), "Saw Nga Man": (74, 12, 8),
    "Too Too": (38, 8, 5), "Tway Ma Shaung": (93, 5, 12), "Soe Lin Oo": (71, 4, 3),
    "Cyrus Washington": (44, 15, 2), "Lone Chaw": (72, 8, 10), "Artur Saladiak": (25, 7, 1),
}

WRESTLING_RECORDS = {
    "Aleksandr Karelin": (887, 2, 0), "Buvaisar Saitiev": (312, 9, 0), "John Smith": (154, 7, 0),
    "Jordan Burroughs": (194, 19, 0), "Abdulrashid Sadulaev": (161, 3, 0), "Mijain Lopez": (158, 8, 0),
    "Dan Gable": (181, 1, 0), "Cael Sanderson": (159, 0, 0), "Saori Yoshida": (206, 3, 0),
    "Kaori Icho": (189, 5, 0), "Bruce Baumgartner": (191, 13, 0), "Osamu Watanabe": (189, 0, 0),
}

BJJ_RECORDS = {
    "Roger Gracie": (76, 7, 3), "Marcelo Garcia": (85, 17, 1), "Marcus Almeida": (128, 13, 1),
    "Leandro Lo": (91, 28, 4), "Andre Galvao": (80, 18, 4), "Gordon Ryan": (108, 9, 3),
    "Rafael Mendes": (78, 7, 1), "Guilherme Mendes": (55, 12, 0), "Bruno Malfacine": (71, 9, 0),
    "Rodolfo Vieira": (100, 9, 1), "Alexandre Ribeiro": (94, 17, 2), "Saulo Ribeiro": (72, 15, 0),
    "Bernardo Faria": (83, 23, 1), "Lucas Lepri": (98, 17, 1), "Rickson Gracie": (48, 0, 0),
    "Mikey Musumeci": (62, 6, 1), "Nicholas Meregali": (90, 12, 2), "Mica Galvao": (87, 7, 1),
    "Craig Jones": (59, 21, 2), "Gabi Garcia": (71, 5, 1), "Beatriz Mesquita": (98, 12, 1),
}

RECORDS_BY_SPORT = {
    "Boxing": BOXING_RECORDS, "Kickboxing": KICKBOXING_RECORDS, "Muay Thai": MUAY_THAI_RECORDS,
    "Lethwei": LETHWEI_RECORDS, "Wrestling": WRESTLING_RECORDS, "Brazilian Jiu-Jitsu": BJJ_RECORDS,
}


ARCHETYPES = {
    "boxing_technician": ("Boxer", "Technical Learner", "Counter", {"punch_technique": 7, "footwork": 6, "adaptability": 5}),
    "boxing_defensive": ("Boxer", "Counter Specialist", "Counter", {"head_movement": 10, "guard_defence": 9, "footwork": 8, "composure": 6}),
    "boxing_pressure": ("Boxer", "Body Hunter", "Pressure", {"punch_power": 7, "creative_punches": 6, "punch_technique": 5, "conditioning": 6, "killer_instinct": 4}),
    "boxing_power": ("Boxer", "Knockout Artist", "Pressure", {"punch_power": 11, "killer_instinct": 9, "strength": 5}),
    "boxing_volume": ("Boxer", "Cardio Machine", "Volume", {"hand_speed": 9, "conditioning": 10, "punch_technique": 6}),
    "boxing_adaptable": ("Boxer", "Adaptable", "Dynamic Attacker", {"adaptability": 10, "feints": 8, "footwork": 7, "punch_technique": 7}),
    "kick_technical": ("Kickboxer", "Technical Learner", "Counter", {"high_kick_technique": 8, "low_kick_technique": 8, "footwork": 7, "kick_defence": 7}),
    "kick_dutch": ("Dutch Kickboxer", "Pressure Fighter", "Pressure", {"punch_technique": 7, "low_kick_power": 8, "low_kick_technique": 8, "conditioning": 5}),
    "kick_power": ("Kickboxer", "Knockout Artist", "Dynamic Attacker", {"punch_power": 8, "high_kick_power": 10, "killer_instinct": 8}),
    "kick_karate": ("Karate", "Showman", "Counter", {"high_kick_speed": 10, "creative_kicks": 10, "footwork": 8}),
    "kick_counter": ("Kickboxer", "Counter Specialist", "Counter", {"kick_defence": 9, "head_movement": 7, "composure": 7, "high_kick_technique": 7, "low_kick_technique": 7}),
    "thai_femur": ("Muay Thai", "Counter Specialist", "Counter", {"high_kick_technique": 9, "low_kick_technique": 9, "footwork": 9, "adaptability": 5}),
    "thai_mat": ("Muay Thai", "Knockout Artist", "Pressure", {"punch_power": 10, "low_kick_power": 8, "killer_instinct": 8}),
    "thai_khao": ("Muay Thai", "Pressure Fighter", "Control", {"knees": 11, "thai_plum": 10, "clinch_control": 9, "conditioning": 7}),
    "thai_tae": ("Muay Thai", "Leg Kicker", "Counter", {"high_kick_power": 10, "low_kick_power": 10, "low_kick_technique": 9, "high_kick_technique": 8}),
    "thai_sok": ("Muay Thai", "Elbow Specialist", "Pressure", {"elbows": 11, "dirty_boxing": 8, "clinch_control": 6, "killer_instinct": 6}),
    "thai_bouk": ("Muay Thai", "Warrior Spirit", "Pressure", {"resilience": 10, "chin_strength": 9, "conditioning": 8, "punch_power": 6}),
    "lethwei_brawler": ("Muay Thai", "Iron Chin", "Pressure", {"punch_power": 10, "dirty_boxing": 11, "elbows": 8, "resilience": 10, "chin_strength": 10}),
    "lethwei_technical": ("Muay Thai", "Warrior Spirit", "Dynamic Attacker", {"high_kick_technique": 7, "low_kick_technique": 7, "elbows": 8, "dirty_boxing": 8, "composure": 5}),
    "wrestling_freestyle": ("Freestyle Wrestler", "Technical Learner", "Control", {"takedowns": 9, "takedown_setup": 9, "chain_wrestling": 9, "scrambles": 6}),
    "wrestling_greco": ("Wrestler", "Title Mentality", "Control", {"throws": 11, "clinch_takedowns": 10, "clinch_control": 9, "strength": 7}),
    "wrestling_pressure": ("Freestyle Wrestler", "Cardio Machine", "Pressure", {"chain_wrestling": 10, "conditioning": 10, "cage_wrestling": 7}),
    "wrestling_explosive": ("Freestyle Wrestler", "Fast Starter", "Pressure", {"takedowns": 10, "takedown_speed": 10, "slams": 9, "strength": 8, "reflexes": 5}),
    "bjj_complete": ("BJJ", "Title Mentality", "Control", {"positional_ability": 9, "submission_attack": 9, "submission_defence_detail": 8, "transitions": 8}),
    "bjj_guard": ("BJJ", "Submission Ace", "Submission Hunter", {"guard_work": 11, "submission_attack": 9, "flexibility": 8, "back_control": 6}),
    "bjj_passer": ("BJJ", "Pressure Fighter", "Control", {"top_control": 10, "positional_ability": 11, "transitions": 8, "mount_control": 8, "strength": 5}),
    "bjj_leglocks": ("Submission Grappler", "Fight Finisher", "Submission Hunter", {"leg_locks": 12, "submission_attack": 10, "transitions": 7}),
    "bjj_scrambler": ("Submission Grappler", "Scramble Artist", "Dynamic Attacker", {"scrambles": 11, "transitions": 9, "back_control": 8, "conditioning": 6}),
}


def _names(text):
    return {name.strip() for name in text.split("|") if name.strip()}


ARCHETYPE_GROUPS = {
    "boxing_defensive": _names("Floyd Mayweather Jr|Bernard Hopkins|Andre Ward|Dmitry Bivol|Shakur Stevenson|Winky Wright"),
    "boxing_pressure": _names("Canelo Alvarez|Gennady Golovkin|Miguel Cotto|Errol Spence Jr|Shawn Porter|Marco Antonio Barrera|Srisaket Sor Rungvisai"),
    "boxing_power": _names("Naoya Inoue|Deontay Wilder|Artur Beterbiev|Felix Trinidad|Gervonta Davis|Julian Jackson"),
    "boxing_volume": _names("Manny Pacquiao|Joe Calzaghe|Amir Khan|Roman Gonzalez|Aaron Pryor"),
    "boxing_adaptable": _names("Terence Crawford|Oleksandr Usyk|Vasiliy Lomachenko|Roy Jones Jr|Lennox Lewis|Juan Manuel Marquez|Oscar De La Hoya"),
    "kick_dutch": _names("Ernesto Hoost|Peter Aerts|Ramon Dekkers|Rob Kaman|Nieky Holzken|Andy Souwer|Robin van Roosmalen|Albert Kraus|Murthel Groenhart"),
    "kick_power": _names("Badr Hari|Mike Zambidis|Mirko Cro Cop|Gokhan Saki|Tyrone Spong|Jerome Le Banner|Mark Hunt|Alistair Overeem|Jamal Ben Saddik"),
    "kick_karate": _names("Andy Hug|Tenshin Nasukawa|Francisco Filho|Sam Greco"),
    "kick_counter": _names("Giorgio Petrosyan|Rico Verhoeven|Sitthichai Sitsongpeenong|Superbon Singha Mawynn|Chingiz Allazov|Artem Levin|Anissa Meksen|Cedric Doumbe"),
    "thai_femur": _names("Samart Payakaroon|Saenchai|Nong-O Gaiyanghadao|Sam-A Gaiyanghadao|Superlek Kiatmuu9|Somrak Khamsing|Karuhat Sor Supawan|Lerdsila Chumpairtour|Panpayak Jitmuangnon|Tawanchai PK Saenchai|Attachai Fairtex|Nadaka Yoshinari"),
    "thai_mat": _names("Rodtang Jitmuangnon|Ramon Dekkers|Anuwat Kaewsamrit|Sagat Petchyindee|Coban Lookchaomaesaitong|Kulabdam Sor Jor Piek Uthai"),
    "thai_khao": _names("Dieselnoi Chor Thanasukarn|Petchmorakot Petchyindee|Petchboonchu FA Group|Yodwicha Por Boonsit|Chamuakpetch Haphalung"),
    "thai_tae": _names("Buakaw Banchamek|Yodsanklai Fairtex|Apidej Sit-Hirun|Singdam Kiatmuu9|Sakmongkol Sithchuchok|Petchtanong Petchfergus|Petchdam Petchyindee"),
    "thai_sok": _names("Yodwicha Por Boonsit|Seksan Or Kwanmuang|Muangthai PK Saenchai"),
    "thai_bouk": _names("Seksan Or Kwanmuang|Liam Harrison|John Wayne Parr|Dany Bill"),
    "lethwei_technical": _names("Too Too|Soe Lin Oo|Cyrus Washington|Artur Saladiak|Sasha Moisa|Naimjon Tuhtaboyev"),
    "wrestling_greco": _names("Aleksandr Karelin|Mijain Lopez|Hamid Sourian|Roman Vlasov|Rulon Gardner|Ghasem Rezaei|Komeil Ghasemi"),
    "wrestling_pressure": _names("Jordan Burroughs|Buvaisar Saitiev|David Taylor|Hassan Yazdani|Zaurbek Sidakov|Dan Gable|Kenny Monday"),
    "wrestling_explosive": _names("Abdulrashid Sadulaev|Kyle Snyder|Gable Steveson|Artur Taymazov|Ivan Yarygin|Henry Cejudo|Bo Nickal|Yoel Romero"),
    "bjj_guard": _names("Marcelo Garcia|Rafael Mendes|Guilherme Mendes|Bruno Malfacine|Royler Gracie|Jean Jacques Machado|Mikey Musumeci|Lachlan Giles|Paulo Miyao|Joao Miyao|Beatriz Mesquita"),
    "bjj_passer": _names("Roger Gracie|Marcus Almeida|Rodolfo Vieira|Bernardo Faria|Lucas Lepri|Fabio Gurgel|Nicholas Meregali|Kaynan Duarte|Tainan Dalpra|Gabi Garcia"),
    "bjj_leglocks": _names("Gordon Ryan|Craig Jones|Garry Tonon|Eddie Bravo"),
    "bjj_scrambler": _names("Leandro Lo|Andre Galvao|Roberto Cyborg Abreu|Fernando Terere|Mica Galvao|Kron Gracie"),
}

DEFAULT_ARCHETYPE = {
    "Boxing": "boxing_technician", "Kickboxing": "kick_technical", "Muay Thai": "thai_femur",
    "Lethwei": "lethwei_brawler", "Wrestling": "wrestling_freestyle", "Brazilian Jiu-Jitsu": "bjj_complete",
}

SOUTHPAWS = _names(
    "Manny Pacquiao|Oleksandr Usyk|Vasiliy Lomachenko|Pernell Whitaker|Marvin Hagler|Joe Calzaghe|"
    "Shakur Stevenson|Sergio Martinez|Giorgio Petrosyan|Mirko Cro Cop|Tenshin Nasukawa|"
    "Saenchai|Sam-A Gaiyanghadao|Yodsanklai Fairtex|Rafael Mendes|Craig Jones"
)
SWITCH = _names("Terence Crawford|Marvin Hagler|Tyson Fury|Samart Payakaroon|Buakaw Banchamek|Gordon Ryan|Mica Galvao")

PRIME_AGE_OVERRIDES = {
    "Floyd Mayweather Jr": 30, "Manny Pacquiao": 29, "Oleksandr Usyk": 31, "Terence Crawford": 30,
    "Naoya Inoue": 29, "Roy Jones Jr": 28, "Bernard Hopkins": 32, "Lennox Lewis": 31,
    "Ernesto Hoost": 31, "Giorgio Petrosyan": 29, "Rico Verhoeven": 31, "Tenshin Nasukawa": 24,
    "Samart Payakaroon": 27, "Dieselnoi Chor Thanasukarn": 26, "Saenchai": 29, "Rodtang Jitmuangnon": 25,
    "Aleksandr Karelin": 29, "Buvaisar Saitiev": 28, "Mijain Lopez": 31, "Jordan Burroughs": 28,
    "Saori Yoshida": 28, "Kaori Icho": 29, "Roger Gracie": 28, "Marcelo Garcia": 27,
    "Gordon Ryan": 27, "Rickson Gracie": 29, "Mikey Musumeci": 26, "Mica Galvao": 22,
}

FAME_BOOST = _names(
    "Floyd Mayweather Jr|Manny Pacquiao|Canelo Alvarez|Oleksandr Usyk|Naoya Inoue|Roy Jones Jr|"
    "Ernesto Hoost|Giorgio Petrosyan|Buakaw Banchamek|Rico Verhoeven|Saenchai|Rodtang Jitmuangnon|"
    "Aleksandr Karelin|Mijain Lopez|Jordan Burroughs|Saori Yoshida|Roger Gracie|Marcelo Garcia|Gordon Ryan|Rickson Gracie"
)


def _stable_number(text):
    return sum((index + 3) * ord(char) for index, char in enumerate(text))


def _default_record(sport, index, name):
    seed = _stable_number(f"{sport}:{name}")
    if sport == "Boxing":
        return max(18, 48 - index // 2 + seed % 9), index // 10 + seed % 4, seed % 2
    if sport == "Kickboxing":
        return max(25, 82 - index + seed % 20), 5 + index // 5 + seed % 7, seed % 3
    if sport == "Muay Thai":
        return max(70, 225 - index * 2 + seed % 40), 18 + index + seed % 18, seed % 8
    if sport == "Lethwei":
        return max(16, 55 - index + seed % 14), 2 + index // 3 + seed % 5, 2 + seed % 10
    if sport == "Wrestling":
        return max(35, 105 - index + seed % 30), 1 + index // 10 + seed % 6, 0
    return max(35, 108 - index + seed % 28), 2 + index // 7 + seed % 9, seed % 4


def _archetype_for(sport, name):
    for archetype, members in ARCHETYPE_GROUPS.items():
        if name in members and (
            archetype.startswith("boxing_") and sport == "Boxing"
            or archetype.startswith("kick_") and sport == "Kickboxing"
            or archetype.startswith("thai_") and sport == "Muay Thai"
            or archetype.startswith("lethwei_") and sport == "Lethwei"
            or archetype.startswith("wrestling_") and sport == "Wrestling"
            or archetype.startswith("bjj_") and sport == "Brazilian Jiu-Jitsu"
        ):
            return archetype
    return DEFAULT_ARCHETYPE[sport]


def build_fallback_sport_profile(sport, name, index=0, rating=None):
    """Build a stable editable profile for a custom-universe athlete.

    Built-in real athletes never use this path. It keeps user-added names
    deterministic until their profile is edited in the universe database.
    """
    if rating is None:
        rating = min(95, 82 - index // 8)
    rating = max(55, min(99, int(rating)))
    archetype = _archetype_for(sport, name)
    style, trait, behaviour, skill_mods = ARCHETYPES[archetype]
    age = PRIME_AGE_OVERRIDES.get(name, 27 + _stable_number(name) % 5)
    wins, losses, draws = RECORDS_BY_SPORT[sport].get(name, _default_record(sport, index, name))
    popularity = max(35, min(99, rating + (5 if name in FAME_BOOST else 1) - index // 18))
    seed = _stable_number(name)
    return {
        "version": SPORT_PROFILE_VERSION,
        "rating": rating,
        "prime_age": age,
        "prime_start": max(21, age - 4),
        "prime_end": max(33, age + 5),
        "record_w": wins,
        "record_l": losses,
        "record_d": draws,
        "style": style,
        "trait": trait,
        "behaviour": behaviour,
        "stance": "Switch" if name in SWITCH else "Southpaw" if name in SOUTHPAWS else "Orthodox",
        "archetype": archetype,
        "skill_mods": dict(skill_mods),
        "popularity": popularity,
        "star_quality": min(99, popularity + (seed % 5) - 1),
        "charisma": max(45, min(99, popularity - 9 + seed % 14)),
        "professionalism": max(55, min(99, 76 + seed % 20)),
        "media_presence": max(45, min(99, popularity - 5 + seed % 10)),
        "sponsor_appeal": max(45, min(99, popularity - 3 + seed % 8)),
        "injury_proneness": 8 + seed % 20,
        "finishing_instinct": max(60, min(99, rating + (7 if trait in ("Knockout Artist", "Fight Finisher", "Submission Ace") else 1))),
        "career_archetype": "Durable Career" if sport in ("Wrestling", "Brazilian Jiu-Jitsu") else "Balanced Development",
        "record_note": "Published career snapshot" if name in RECORDS_BY_SPORT[sport] else "Editable custom-universe estimate",
        "record_as_of": "2026-07-15",
    }


def build_real_sport_profiles(rosters):
    """Return an editable profile dictionary containing every built-in name."""
    profiles = {}
    for sport, names in rosters.items():
        ratings = SPORT_RATINGS[sport]
        if len(ratings) != len(names):
            raise ValueError(f"{sport} profile ratings ({len(ratings)}) do not match roster ({len(names)})")
        sport_profiles = {}
        for index, name in enumerate(names):
            sport_profiles[name] = build_fallback_sport_profile(sport, name, index=index, rating=ratings[index])
            if name not in RECORDS_BY_SPORT[sport]:
                sport_profiles[name]["record_note"] = "Conservative seeded circuit record"
            if name == "Rickson Gracie":
                sport_profiles[name]["record_note"] = "Historical BJJ ledger estimate; editable in the universe database"
        profiles[sport] = sport_profiles
    return profiles
