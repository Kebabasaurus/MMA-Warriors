## 15. Common Change Recipes

### Add a persistent fighter or promotion field

```text
model default
  -> seed value
  -> serialize
  -> legacy load default/repair
  -> viewer or simulation consumer
  -> old-save + round-trip smoke assertions
```

### Add a new core promotion

```text
shipped universe company + fighter ownership data
  -> authored Python roster data and fallback promotion seed spec
  -> old-save repair
  -> executive/strategy/identity/broadcaster data
  -> champion and division viability
  -> universe validation + smoke expectations
  -> README/changelog
```

### Add a new fight result path

```text
simulate_fight result
  -> finish/result presentation
  -> apply_result
  -> injury/ranking/finance updates
  -> record_season_result
  -> event and promotion history
  -> save/load regression
```

### Change a shared UI header or tab

```text
build widget with flexible geometry
  -> refresh every field independently
  -> verify long values and spectator mode
  -> verify keyboard/mouse states across representative themes
  -> check maximized and narrower supported widths
```

