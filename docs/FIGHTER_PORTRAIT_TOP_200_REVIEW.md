# Rating positions 101–200: real-fighter portrait review

Reviewed 7 September 2026. This cohort is selected from the shipped default
universe by rating descending then name ascending. It is a database order, not a
claim about the live sport ranking.

## What this means

Every one of these 100 database records now has a complete authored cosmetic
vector in `fighter_portraits/ranked_101_200.py`. The directions are based on
the fighter's real, publicly available promotional/photoshoot appearance, rather
than using their country or a generic generated look. The priority is the visible
identity at the game scale: hair silhouette and colour, baldness, beard state,
skin palette, and broad face/neck proportion. It intentionally does not infer
appearance from nationality or change any rating, ability, popularity, gender
record, simulation field, random stream, or saved identity.

The renderer is a small comic portrait, so this is a likeness direction—not a
promise of a photographic reproduction. At 72px especially, hair, beard and
overall silhouette carry far more useful recognition than a fine facial detail.

## Reference basis

Current promotion profile portraits were the primary references where available:
[UFC athlete profiles](https://www.ufc.com/athletes/all),
[PFL fighter/rankings profiles](https://pflmma.com/rankings), and
[ONE athlete profiles](https://www.onefc.com/athletes/). Historical competitors
and promotion-specific archive rows were checked against recent professional
press/promotional portraits when a current promotion profile was unavailable.
Reference photos are not copied, downloaded, or shipped with the game.

The following is the visual direction applied; it is a useful correction ledger
for future real-photo review, not a demographic classification:

| Ranks | Fighters | Real-appearance anchor used in the portrait |
|---|---|---|
| 101–110 | Benson Henderson; Ciryl Gane; Eddie Alvarez; Gegard Mousasi; Henry Cejudo; Ian Machado Garry; Irene Aldana; Israel Adesanya; Jake Shields; Loopy Godinez | Henderson's dark braids and beard; Gane/Alvarez/Mousasi/Shields' shaved heads; Garry's very light close buzz; Aldana/Godinez's long dark hair; Adesanya's tight buzz; Cejudo's dark fade/beard. |
| 111–120 | Murad Ramazanov; Quinton Jackson; Randy Couture; Regian Eersel; Rickson Gracie; Robbie Lawler; Sean O'Malley; Sean Strickland; Serghei Spivac; T.J. Dillashaw | Short dark hair and beards where present; Jackson/Couture's shaved heavy silhouettes; Eersel's long locs; Gracie's dark waves; Lawler/Strickland's close crops; O'Malley's long dyed signature hair. |
| 121–130 | Tawanchai PK Saenchai; Wanderlei Silva; Yana Santos; Abdoul Abdouraguimov; Abdul-Aziz Abdulvakhabov; Ailin Perez; Archie Colgan; Brendan Allen; Carlos Ulberg; Chris Weidman | Tawanchai's compact black crop; Silva's close shaved head; Santos' long blonde waves; the two short dark-bearded Caucasus profiles; Perez's long dark hair; Colgan's coiled taper; Allen/Weidman's short bearded cuts; Ulberg's close dark curls. |
| 131–140 | Christian Lee; Cory Sandhagen; Curtis Blaydes; Dakota Ditcheva; Denis Goltsov; Dustin Poirier; Kevin Randleman; Khalil Rountree Jr.; Kyoji Horiguchi; Leon Edwards | Lee/Horiguchi's compact black cuts; Sandhagen's close light crop; Blaydes/Randleman/Rountree's heavy, short-haired silhouettes; Ditcheva's long dark hair; Goltsov's short hair/beard; Poirier's close beard; Edwards' short textured hair. |
| 141–150 | Lerone Murphy; Luke Trainer; Mackenzie Dern; Magomed Umalatov; Manel Kape; Mark Kerr; Mauricio Ruffy; Robert Whittaker; Salahdine Parnasse; Stipe Miocic | Murphy's short textured cut; Trainer's light short hair/beard; Dern's long blonde waves; Umalatov/Kape's dark cropped beard looks; Kerr/Miocic's bald heavyweight profiles; Ruffy's dark curls; Whittaker's short dark beard; Parnasse's close cut. |
| 151–160 | Superlek Kiatmoo9; Tatsuro Taira; Taylor Lapilus; Aaron Pico; Angela Lee; Askar Askarov; Benoit Saint Denis; Bogdan Guskov; Brandon Royval; Carlos Condit | Superlek/Taira's short black cuts; Lapilus' fade; Pico's cropped brown hair; Lee's long dark waves; Askarov/Guskov's short bearded profiles; Saint Denis' longer textured cut; Royval's longer dark hair; Condit's long blonde waves and goatee. |
| 161–170 | Chuck Liddell; Cris Cyborg; Cung Le; Dan Hooker; Douglas Lima; Dovletdzhan Yagshimuradov; Francis Ngannou; Gabriel Bonfim; Gillian Robertson; Glover Teixeira | Liddell's blonde mohawk; Cyborg/Robertson's long hair; Le/Teixeira/Ngannou's shaved or very close cuts; Hooker's light mullet; Lima/Yagshimuradov's close dark beards; Bonfim's dark curls. |
| 171–180 | Jailton Almeida; Kiamrian Abbasov; Luana Santos; Marat Gafurov; Marvin Vettori; Movlid Khaybulaev; Nate Diaz; Nick Diaz; Paddy Pimblett; Patchy Mix | Almeida's short/shaved beard look; Abbasov's close dark beard; Santos' tied-back dark hair; Gafurov's longer dark hair; Vettori's dense crop/beard; Khaybulaev's shaved profile; the Diaz brothers' short dark looks; Pimblett's blonde mop; Mix's braided rows. |
| 181–190 | Rafael dos Anjos; Rashad Evans; Reinier de Ridder; Salamat Isbulaev; Sergei Kharitonov; Sergei Pavlovich; Sergio Pettis; Shamil Musaev; Song Yadong; Superbon Singha Mawynn | dos Anjos' close beard; Evans' shaved head; de Ridder's light close hair; Isbulaev/Musaev's cropped beards; Kharitonov's shaved head; Pavlovich's reddish beard/hair; Pettis' fade; Song/Superbon's compact black cuts. |
| 191–200 | Valentin Moldavsky; Alistair Overeem; Andrei Arlovski; Asu Almabayev; Bo Nickal | Moldavsky/Overeem's close heavyweight cuts; Arlovski's long dark hair and beard; Almabayev's compact black crop; Nickal's short light-brown crop. |

Legend, Strikeforce and Contender-series rows retain an independent copy of the
real fighter's direction. They are not aliases: a later period-specific correction
can change one record without unexpectedly changing another.

## Labelled visual review

Open the self-contained [labelled HTML gallery](../analysis/portraits/top_101_200_2026_09/review.html).
It renders the exact runtime code at 180px and labels every fighter in rank order,
from 101 Benson Henderson through 200 Bo Nickal LFA. The matching 72, 98 and
104px contact sheets plus the complete identity manifest are alongside it.

Regenerate the review (repeat with `--cell 72`, `98`, or `104` as needed):

```powershell
py -3 analysis/portraits/generate_portrait_contact_sheet.py --review-set top-rated --offset 100 --count 100 --columns 10 --cell 180 --out analysis/portraits/top_101_200_2026_09/portraits_180.png --manifest analysis/portraits/top_101_200_2026_09/identities.json --html analysis/portraits/top_101_200_2026_09/review.html
```

No catalogue IDs, generated country distributions, database records, ratings,
combat code, or persistence format are changed by this cohort. The female
no-facial-hair guard applies independently after these authored vectors merge.
