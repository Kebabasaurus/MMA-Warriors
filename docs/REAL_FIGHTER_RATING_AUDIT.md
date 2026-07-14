# Real Fighter Rating Audit

Updated: July 2026

## What Was Wrong

Real fighters used the same random detailed-skill generator as generated fighters. This
could give a real striker elite wrestling or ground skills, assign traits unrelated to
their career, and change their effective overall between new saves.

## Calibration Rule

Real fighters now use deterministic, named profiles:

- `rating` is intended final in-game competitive overall, rather than fame or legacy.
- A style template shapes standing, wrestling, ground, clinch, mental, and physical skill groups.
- Named overrides add known strengths such as Makhachev's top control, Topuria's boxing,
  Volkanovski's conditioning, or Oliveira's submission game.
- A final normalization keeps detailed skill sheets from inflating the named rating.
- Profiles apply once to saves made before this change (`rating_profile_version = 2`).

## Rating Bands

| Overall | Meaning |
| --- | --- |
| 92-94 | Current world-leading / elite historical active ability |
| 88-91 | Championship-level contender |
| 84-87 | Ranked, dangerous international level |
| 79-83 | Strong roster fighter / regional champion level |
| 74-78 | Quality prospect or regional contender |
| Below 74 | Developmental or lower-card level |

## Sample Checks

| Fighter | Overall | Style | Trait |
| --- | ---: | --- | --- |
| Islam Makhachev | 94 | Sambo | Title Mentality |
| Alexander Volkanovski | 93 | Well-Rounded | Cardio Machine |
| Ilia Topuria | 93 | Boxer | Knockout Artist |
| Tom Aspinall | 92 | Well-Rounded | Big Finisher |
| Alex Pereira | 91 | Kickboxer | Knockout Artist |
| Khamzat Chimaev | 91 | Wrestler | Big Finisher |
| Dakota Ditcheva | 86 | Muay Thai | Knockout Artist |
| Nicolas Leblond | 78 | Well-Rounded | Clutch |

## Roster Additions

The audit added current depth to UFC, PFL, and Cage Warriors. Notable additions include
Manel Kape, Song Yadong, Jean Silva, Youssef Zalal, Aaron Pico, Gabriel Bonfim, Leon
Edwards, Kamaru Usman, Israel Adesanya, Derrick Lewis, Shamil Musaev, Gadzhi Rabadanov,
Sergio Pettis, and the current Cage Warriors champions Nicolas Leblond, Weslley Maia,
Nikita Bagley, Ieuan Davies, and Sean Clancy Jr.
