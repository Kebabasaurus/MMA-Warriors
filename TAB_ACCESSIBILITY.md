# Accessible Tab Styling

MMA Warriors uses Tkinter/ttk rather than CSS. All visible in-game notebooks inherit the shared `TNotebook.Tab` rules in `UIMixin.configure_style`; the hidden main-navigation notebook remains unchanged.

## State treatment

In ttk terminology, `selected` is the current tab and `active` is pointer hover.

| Player-visible state | Surface | Text | Additional cue |
|---|---|---|---|
| Inactive | Theme `button` | Theme `button_text` (with an AA fallback) | Flat, two-pixel theme-line edge |
| Hover | Theme `panel_dark` | Automatically chosen `#111111` or `#ffffff` | Raised edge and theme-gold outline |
| Current / selected | Whichever of theme `gold` or `red` is most distinct from the inactive surface | Automatically chosen `#111111` or `#ffffff` | Two-pixel text-color outline, raised edge, and one-pixel expansion toward the content |
| Keyboard focus | Existing state colors | Existing state text | Focus border uses the selected surface color, at least 4.93:1 against every inactive surface |
| Disabled | Theme `button` | Theme `muted` (with an AA fallback) | Inactive geometry |

The tab font is Tahoma 9 bold with 16 × 6 pixels of padding. The current tab is therefore communicated by background luminance, foreground inversion, outline, elevation, and its connection to the content—not color alone.

Visual shorthand:

```text
Inactive     [  TAB LABEL  ]     dark/recessed theme button surface
Hover        [  TAB LABEL  ]     stronger theme wash + raised outline
Current     ╔══ TAB LABEL ══╗    bright highlight + 2 px high-contrast edge
             content panel
```

## Theme values and WCAG ratios

Pairs are written as `background / foreground`. Ratios use the WCAG 2.x relative-luminance formula and are rounded to two decimals. Normal tab text must reach 4.5:1; the selected-vs-inactive surface change and keyboard focus indicator must reach 3:1.

| Theme | Inactive pair | Hover pair | Current pair | Current vs inactive |
|---|---|---|---|---:|
| Fight Night | `#28313c / #f3f6f8` · 12.13:1 | `#2d3540 / #ffffff` · 12.39:1 | `#d5a84b / #111111` · 8.57:1 | 5.98:1 |
| Classic Green | `#111111 / #f6f6ed` · 17.38:1 | `#0f4f17 / #ffffff` · 9.76:1 | `#f0c44c / #111111` · 11.42:1 | 11.42:1 |
| Light Office | `#c8c0b3 / #111111` · 10.47:1 | `#5a564e / #ffffff` · 7.30:1 | `#8e1f1b / #ffffff` · 8.89:1 | 4.93:1 |
| Matrix | `#0e2414 / #c9ffd7` · 14.65:1 | `#0f2b18 / #ffffff` · 15.23:1 | `#8cffb0 / #111111` · 15.33:1 | 13.31:1 |
| Champion | `#302312 / #fff0cf` · 13.54:1 | `#3a2a12 / #ffffff` · 13.82:1 | `#f3c45f / #111111` · 11.57:1 | 9.36:1 |
| UFC | `#2c2c2c / #ffffff` · 13.97:1 | `#3a3a3a / #ffffff` · 11.37:1 | `#f4f4f4 / #111111` · 17.17:1 | 12.70:1 |
| Cage Warriors | `#28323f / #fff6dc` · 12.03:1 | `#cc9b22 / #111111` · 7.44:1 | `#f3c94f / #111111` · 11.94:1 | 8.21:1 |
| PFL | `#1d3342 / #f0fbff` · 12.43:1 | `#0b6f86 / #ffffff` · 5.78:1 | `#f0f7ff / #111111` · 17.49:1 | 12.12:1 |
| BAMMA | `#353026 / #fff4e2` · 12.04:1 | `#d66f16 / #111111` · 5.53:1 | `#ffe0a6 / #111111` · 14.81:1 | 10.28:1 |
| ONE Championship | `#303030 / #ffffff` · 13.20:1 | `#7a0d14 / #ffffff` · 11.08:1 | `#f4d276 / #111111` · 12.88:1 | 9.00:1 |
| RIZIN | `#382a28 / #fff3e3` · 12.54:1 | `#a81720 / #ffffff` · 7.48:1 | `#f0d4aa / #111111` · 13.22:1 | 9.61:1 |
| KSW | `#283c50 / #eff7ff` · 10.48:1 | `#ca1d2c / #ffffff` · 5.64:1 | `#e8f2ff / #111111` · 16.70:1 | 10.03:1 |
| LFA | `#29485d / #f3fbff` · 9.20:1 | `#d33a35 / #ffffff` · 4.74:1 | `#e7f4ff / #111111` · 16.89:1 | 8.62:1 |
| Oktagon | `#373423 / #fff7de` · 11.69:1 | `#c69a24 / #111111` · 7.24:1 | `#fff0b1 / #111111` · 16.50:1 | 10.94:1 |
| BRAVE | `#294c3b / #f7ffe9` · 9.33:1 | `#b78b20 / #111111` · 6.05:1 | `#fff0a1 / #111111` · 16.39:1 | 8.32:1 |
| ACA | `#314a37 / #f4faee` · 9.12:1 | `#497c43 / #ffffff` · 4.94:1 | `#e7e6c1 / #111111` · 14.82:1 | 7.61:1 |
| Boxing | `#4a2e22 / #fff0dc` · 11.00:1 | `#a72b1c / #ffffff` · 6.99:1 | `#f5c66d / #111111` · 11.85:1 | 7.73:1 |
| Kickboxing | `#2b5356 / #effffd` · 8.24:1 | `#db5b20 / #111111` · 4.97:1 | `#f7e3a5 / #111111` · 14.82:1 | 6.66:1 |
| Muay Thai | `#593225 / #fff1dd` · 9.90:1 | `#c84819 / #ffffff` · 4.78:1 | `#f3c45d / #111111` · 11.57:1 | 6.74:1 |
| Wrestling | `#315675 / #f2f9ff` · 7.27:1 | `#d39a22 / #111111` · 7.57:1 | `#ffe79a / #111111` · 15.42:1 | 6.31:1 |
| BJJ | `#3b4371 / #f5f3ff` · 8.60:1 | `#7652aa / #ffffff` · 5.90:1 | `#ddd5ff / #111111` · 13.52:1 | 6.75:1 |
| Sky Sports | `#28528a / #f4f8ff` · 7.40:1 | `#1b5cba / #ffffff` · 6.39:1 | `#eef5ff / #111111` · 17.21:1 | 7.18:1 |
| ESPN | `#393939 / #ffffff` · 11.55:1 | `#9d9d9d / #111111` · 6.96:1 | `#f1f1f1 / #111111` · 16.72:1 | 10.23:1 |
| BBC Sport | `#3e3e3e / #ffffff` · 10.70:1 | `#494949 / #ffffff` · 9.00:1 | `#ffe53b / #111111` · 14.86:1 | 8.42:1 |

All inactive, hover, current, and disabled text pairs meet WCAG AA. Across the current palette set, the lowest normal-text ratio is LFA hover at 4.74:1. Light Office intentionally uses burgundy rather than gold for the current tab because burgundy creates the stronger state change against its warm light inactive surface; every other theme uses its gold token.

## Companion database editor

The standalone Universe Database Editor keeps its existing blue/green identity but uses the same geometry cues: 9-point bold labels, two-pixel borders, raised hover/current states, and one-pixel selected expansion. Its inactive pair is `#102236 / #e6f2f2` and its current pair is `#32d583 / #062116`; both exceed AA.
