# Universe Database + Editor Design Brief

## Goal

Named fighters must be data-authored, easy to edit, and usable by the in-game Database Editor. Generated fighters can stay procedural, but real/named fighters should not depend on list position or generic templates for their ratings.

This applies to:

- MMA real fighters
- MMA legends
- independent/free-agent named fighters
- promotion rosters
- combat sport athletes
- Lethwei/Muay Thai additions

## Current issue

The starting database is now intentionally one file: `Databases/Default Universe.universe.json`. Its combat-sport section must not be mostly name lists. Example: `Oleksandr Usyk` must be an authored Boxing record, not a name that receives generated stats from a list index and random variance.

That is not good enough long term. Usyk, Canelo, Karelin, Saenchai, Gordon Ryan, real MMA fighters, etc. need explicit stats.

## Required database format

The database must support full editable fighter records.

Example:

```json
{
  "name": "Oleksandr Usyk",
  "database_type": "combat_sport",
  "sport": "Boxing",
  "generated": false,
  "region": "Europe",
  "nationality": "Ukrainian",
  "age": 31,
  "weight": "Heavyweight",
  "gender": "Male",
  "style": "Boxer",
  "stance": "Southpaw",
  "rating": 96,
  "potential": 97,
  "striking": 98,
  "wrestling": 58,
  "grappling": 52,
  "cardio": 96,
  "chin": 93,
  "power": 88,
  "fight_iq": 98,
  "popularity": 92,
  "star_quality": 94,
  "media_presence": 88,
  "professionalism": 94,
  "primary_discipline": "Boxing",
  "combat_background": "Boxing",
  "record_w": 22,
  "record_l": 0,
  "record_d": 0
}
```

The loader should still support old/simple entries temporarily:

```json
"Oleksandr Usyk"
```

But this should be treated as fallback only and flagged by validation as incomplete for named fighters.

## Easy editing requirement

The files must be human-editable without needing to touch Python.

Requirements:

- Pretty JSON with stable field order.
- Clear top-level grouping.
- No hidden stat generation for named fighters once a full record exists.
- Generated/procedural entries must be clearly marked with `"generated": true`.
- Real/named records must be clearly marked with `"generated": false`.
- Database files should be small enough to open in a normal editor.
- Avoid deeply nested structures that make one fighter hard to find.

The one-file universe uses a top-level `sections` object. Its `fighters` and `combat_sports` sections follow these concepts:

```json
{
  "schema": 2,
  "database_name": "Core MMA Fighter Database",
  "fighters": [
    { "name": "Islam Makhachev", "...": "..." },
    { "name": "Jon Jones", "...": "..." }
  ],
  "promotions": {
    "Ultimate Fighting Championship": ["Islam Makhachev", "Jon Jones"]
  }
}
```

Combat sport version:

```json
{
  "schema": 2,
  "database_name": "Combat Sport Fighter Database",
  "fighters": [
    { "name": "Oleksandr Usyk", "sport": "Boxing", "...": "..." },
    { "name": "Aleksandr Karelin", "sport": "Wrestling", "...": "..." }
  ],
  "sport_worlds": {
    "Boxing": {
      "promotion": "Global Boxing Championship",
      "roster": ["Oleksandr Usyk", "Canelo Alvarez"]
    }
  }
}
```

## In-game Database Editor requirements

The Database Editor needs to be updated as part of this work.

It should not only edit the active save. It should understand separated database files.

Required editor modes:

1. Active Save
   - Edits the currently loaded world/save.
   - Current behavior can remain.

2. Default Universe: MMA
   - Opens the `fighters` section of `Databases/Default Universe.universe.json`.
   - Edits named MMA fighters and promotion assignments.
   - Can add/remove fighters from promotion seed rosters.

3. Default Universe: Combat Sports
   - Opens the `combat_sports` section of `Databases/Default Universe.universe.json`.
   - Edits Boxing/Kickboxing/Muay Thai/Wrestling/BJJ/Lethwei athletes.
   - Can move athletes between sport rosters.

4. Generated Name Pools
   - Later optional mode for first/last names, regions, gyms, etc.

Editor UI requirements:

- Clear selector for database source.
- Filters for sport, promotion, gender, weight, generated/non-generated.
- Search by name.
- Sortable table.
- Double-click opens full fighter editor.
- Save button writes back to the selected database JSON.
- Validation button shows missing/bad fields.
- Duplicate-name warning.
- Required-field warning.
- “Open JSON file location” helper button.
- “Backup before save” automatic copy.

## Validation rules

Add a database validation function/test.

It should check:

- Every non-generated named fighter has explicit core stats.
- No duplicate names unless intentionally versioned.
- Required fields exist.
- Ratings are 1-99.
- Age is sane.
- Weight class is valid.
- Gender is valid.
- Sport is valid for combat-sport records.
- Promotion roster references point to existing fighters.
- Every core promotion can fill enough divisions.
- Every combat sport has enough athletes to run cards.

Required fields for named fighter records:

- `name`
- `generated`
- `age`
- `gender`
- `weight`
- `region`
- `nationality`
- `style`
- `record_w`
- `record_l`
- `record_d`
- `striking`
- `wrestling`
- `grappling`
- `cardio`
- `chin`
- `power`
- `fight_iq`
- `potential`
- `popularity`

Combat sport required additions:

- `sport`
- `primary_discipline`
- `combat_background`

## Migration plan

1. Create schema v2 loader.
   - Accept both old schema v1 and new schema v2.
   - Prefer explicit fighter records when available.
   - Use template generation only for old/simple entries.

2. Create export/converter script.
   - Read current code-based seed rows.
   - Instantiate fighters using current logic.
   - Export resulting full stats into JSON records.
   - Mark generated fallback entries separately.

3. Convert the MMA section in the Default Universe.
   - Player real roster.
   - UFC/PFL/ONE/RIZIN/KSW/etc.
   - free-agent named fighters.
   - legends.

4. Convert the combat-sports section in the Default Universe.
   - Boxing.
   - Kickboxing.
   - Muay Thai.
   - Lethwei.
   - Wrestling.
   - Brazilian Jiu-Jitsu.

5. Update Database Editor.
   - Add source selector.
   - Add JSON writeback.
   - Add validation UI.
   - Add automatic backup before saving.

6. Add smoke/validation tests.
   - Test new game loads from v2 databases.
   - Test old v1 simple list fallback still works.
   - Test editor save/readback.
   - Test combat sport worlds seed correctly.

7. Rebuild portable exe.
   - Include `Default Universe.universe.json` as the sole shipped starting database file.

## Important design rule

Do not remove procedural generation. It is still needed for:

- regen fighters
- academy prospects
- market replenishment
- regional feeder depth
- generated free agents

But named fighters should be authored data, not procedural approximations.
