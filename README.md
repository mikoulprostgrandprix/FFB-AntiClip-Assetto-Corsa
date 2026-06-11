Installation
Unzip
Paste in assetto corsa folder
apps/python

# FFBClipX complete manual

This guide explains the full FFBClipX interface in English:
- buttons
- checkboxes
- adjustable values
- status information
- saved configuration files

The French version is available in `GUIDE_REGLAGES_FR.md`.

## 1. What FFBClipX does

FFBClipX helps reduce force feedback clipping in Assetto Corsa.

The app watches the FFB signal, estimates a useful target, and adjusts car FFB gain to:
- keep as much detail as possible
- avoid frequent saturation
- adapt behavior to the car, track, and session

## 2. Interface layout

The app has 2 levels:
- the main HUD
- the `Options` window, split into 4 tabs:
- `Drive`
- `Adaptive`
- `Protection`
- `Tools`

## 3. Main HUD elements

### `FFBClipX`

Application title.

### Car / track line

Shows the loaded car and track.

Example:
- `gp_2026_amr26 | rt_suzuka / layout_f1_2026`

### `Mode badge`

Shows a compact state summary:
- `AUTO` or `MANUAL`
- current adaptive mode
- `DYN` if dynamic mode is enabled

### `Torque target (Nm)` or `FFB Strength`

Main HUD control.

Depending on mode:
- with `Direct Drive mode = ON`, the value is in `Nm`
- with `Direct Drive mode = OFF`, the value is in `%`

This is the active target for the current car.

Range:
- DD: `3` to `50 Nm`
- non DD: `10` to `120 %`

### Message line

Shows the main status message:
- auto mode active
- clipping protected or not
- reset
- rollback
- learning status

### Detail line

Shows a short summary:
- `Race` or `Qualif` profile
- response curve mode
- display mode

### `Combo / Default / Safety` line

Summary of 3 values:
- `Combo`: stored baseline for the current car/track combination
- `Default`: global default target
- `Safety`: allowed min / max range

### `Wet / Kerb / Diag / Cal` line

Summary of advanced features:
- wet mode state
- kerb filter state
- diagnostic dashboard state
- calibration helper state

### Graph

Displays the signal according to display mode:
- `Off`: no useful graph
- `Graph`: real-time graph
- `Histogram`: statistical distribution

In the real-time graph:
- red line: target
- green line: observed force

### `Mode: Auto` button

Toggles between:
- `Auto`: FFBClip adjusts gain automatically
- `Manual`: FFBClip no longer tries to prevent clipping

Recommendation:
- keep `Auto` in most cases

### `Dynamic: ON/OFF` button

Enables or disables fast reaction to short clipping spikes.

Useful for:
- kerbs
- compressions
- sudden load peaks

### `Reset` button

Returns the current target to the default value.

Effect:
- resets the histogram
- restores the baseline target

### `Options` button

Opens or closes the advanced settings window.

## 4. `Drive` tab

### `Manual override`

Checkbox.

Effect:
- enables manual mode
- disables automatic anti-clipping protection

### `Direct Drive mode`

Checkbox.

Effect:
- `OFF`: the app works in percentage
- `ON`: the app works in `Nm`

Use `ON` when your wheelbase is configured around a known real torque value.

### `Run in background`

Checkbox.

Effect:
- the app keeps running even when its window is not in focus

### `CSV logging`

Checkbox.

Effect:
- writes runtime data to `Config/ffbclip_runtime_log.csv`

Useful for:
- debugging
- session analysis

### `Default FFB strength (%)` or `Default torque target (Nm)`

Spinner.

Range:
- DD: `3` to `50`
- non DD: `10` to `120`

Role:
- sets the global starting target
- acts as the base before contextual adaptation

### `Hardware max torque`

Spinner available in DD mode.

Range:
- `3` to `50 Nm`

Role:
- represents the real maximum torque of the wheelbase

Important:
- if this value is wrong, all DD conversions become wrong

### `Display mode`

Cyclic button.

Order:
- `Off`
- `Graph`
- `Histogram`

### `Graph refresh (Hz)`

Spinner.

Range:
- `1` to `30`

Role:
- graph refresh rate

### `Dynamic threshold (%)`

Spinner.

Range:
- `10` to `300`

Role:
- threshold used by dynamic mode

Interpretation:
- lower = more protective
- higher = more permissive

### `Dynamic intensity`

Spinner.

Range:
- `50` to `500`

Role:
- reaction speed of dynamic mode

Interpretation:
- lower = smoother
- higher = more aggressive

### `Preset snapshot`

Checkbox.

Effect:
- allows a settings snapshot to be saved into `FFBClip.ini`

### `Session report`

Checkbox.

Effect:
- writes a text session report to `Config/ffbclip_session_report.txt`

## 5. `Adaptive` tab

### `Adaptive mode`

Cyclic button.

Order:
- `Classic`
- `Lock`
- `Hybrid`

Role:
- `Classic`: continuous adaptation
- `Lock`: learns a baseline and locks it
- `Hybrid`: learns a baseline and allows controlled variation around it

Note:
- changing this mode resets learning

### `Profile mode`

Cyclic button.

Values:
- `Race`
- `Qualif`

Role:
- allows slightly different behavior depending on context

Note:
- clicking it disables `Auto session profile`

### `Learn laps`

Spinner.

Range:
- `1` to `20`

Role:
- number of laps used for learning

### `Lock percentile`

Spinner.

Range:
- `1` to `50`

Role:
- percentile used to compute the baseline in `Lock` mode

Interpretation:
- lower = more conservative
- higher = stronger but with more clipping risk

### `Hybrid band (%)`

Spinner.

Range:
- `5` to `50`

Role:
- allowed variation around the locked baseline in `Hybrid` mode

### `Confidence gate (%)`

Spinner.

Range:
- `50` to `98`

Role:
- minimum confidence required before a lock is accepted

### `Phase learning`

Checkbox.

Role:
- splits learning by speed / load phases

Note:
- changing this resets learning

### `Show confidence`

Checkbox.

Role:
- shows learning confidence in the UI

### `Confidence gate`

Checkbox.

Role:
- enables or disables the confidence threshold logic

### `Setup-aware learn`

Checkbox.

Role:
- resets learning when a significant setup change is detected

### `Auto reset combo`

Checkbox.

Role:
- resets learning when the car / track combination changes

### `Auto session profile`

Checkbox.

Role:
- automatically picks `Race` or `Qualif` based on the session when possible

### `Profile shaping`

Checkbox.

Role:
- applies a mild correction based on the active profile

### `Rollback gate`

Checkbox.

Role:
- allows fallback to a safer value when confidence is not high enough

## 6. `Protection` tab

### `Outlier filter`

Checkbox.

Role:
- filters abnormal spikes so one peak does not corrupt the logic

### `Anti oscillation`

Checkbox.

Role:
- avoids overly frequent micro-adjustments

### `Safety limits`

Checkbox.

Role:
- enables minimum and maximum gain bounds

### `Endurance ceiling`

Checkbox.

Role:
- progressively reduces the allowed top end during long sessions

### `Safety floor (%)`

Spinner.

Range:
- `20` to `150`

Role:
- minimum allowed gain

### `Safety ceiling (%)`

Spinner.

Range:
- `80` to `300`

Role:
- maximum allowed gain

### `Deadband (%)`

Spinner.

Range:
- `0` to `20`

Role:
- ignores corrections that are too small

### `Min interval (ms)`

Spinner.

Range:
- `50` to `1000`

Role:
- minimum delay between two corrections

### `Endurance start (min)`

Spinner.

Range:
- `10` to `240`

Role:
- time at which endurance reduction begins

### `Max endurance drop (%)`

Spinner.

Range:
- `0` to `30`

Role:
- maximum reduction allowed in endurance mode

### `Wet softening`

Checkbox.

Role:
- softens behavior when grip drops

### `Kerb filter`

Checkbox.

Role:
- reduces certain kerb / impact spikes

### `Wet grip threshold (%)`

Spinner.

Range:
- `60` to `100`

Role:
- grip threshold below which wet softening starts to work

### `Wet softening (%)`

Spinner.

Range:
- `0` to `30`

Role:
- strength of wet softening

### `Kerb spike threshold (%)`

Spinner.

Range:
- `5` to `80`

Role:
- spike detection sensitivity

### `Kerb damp factor (%)`

Spinner.

Range:
- `35` to `100`

Role:
- reduction applied after a spike is detected

## 7. `Tools` tab

### `Response curves`

Checkbox.

Role:
- enables feel curve reshaping

### `Anti fatigue`

Checkbox.

Role:
- softens a force band to reduce fatigue over time

### `Response curve`

Cyclic button.

Order:
- `Linear`
- `Expo`
- `S-curve`

### `Curve strength (%)`

Spinner.

Range:
- `0` to `100`

Role:
- intensity of the selected curve

### `Fatigue low band (%)`

Spinner.

Range:
- `20` to `90`

Role:
- start of the anti-fatigue band

### `Fatigue high band (%)`

Spinner.

Range:
- `30` to `100`

Role:
- end of the anti-fatigue band

### `Fatigue reduction (%)`

Spinner.

Range:
- `0` to `35`

Role:
- reduction applied inside the anti-fatigue band

### `Diag dashboard`

Checkbox.

Role:
- enables extra diagnostic information

### `Diag refresh (s x100)`

Spinner.

Range:
- `25` to `500`

Role:
- diagnostic refresh interval

Interpretation:
- `100` = `1.00 s`

### `Calibration helper`

Checkbox.

Role:
- enables the calibration assistant

### `Calib warmup laps`

Spinner.

Range:
- `0` to `5`

Role:
- warmup laps before calibration learning

### `Calib learn laps`

Spinner.

Range:
- `1` to `10`

Role:
- laps used to learn calibration

### `Calib validation laps`

Spinner.

Range:
- `1` to `10`

Role:
- laps used to validate calibration consistency

## 8. Action buttons at the bottom of the options window

### `Start calib` / `Stop calib`

Starts or stops the calibration sequence.

### `Reset learn`

Clears learning data:
- history
- lock
- confidence

### `Rollback`

Applies a fallback value if one exists.

### `Close`

Closes the options window.

## 9. Configuration files

### `Config/FFBClip.ini`

Contains:
- global settings
- default target
- saved DD targets
- preset sections

Important sections:
- `[Options]`
- `[targetgains]`
- `[targettorquesnm]`
- `[Preset_*]`

### `Config/Combos.ini`

Contains:
- a stored value per car / track combination
- learned lock values

### `Config/ffbclip_runtime_log.csv`

Created when `CSV logging` is enabled.

### `Config/ffbclip_session_report.txt`

Created when `Session report` is enabled.

## 10. Recommended starting setup

### Simple DD baseline

- `Mode: Auto`
- `Direct Drive mode = ON`
- `Hardware max torque = real wheelbase torque`
- `Torque target = slightly below hardware limit`
- `Adaptive mode = Lock`
- `Learn laps = 3 to 5`
- `Lock percentile = 20 to 25`
- `Safety limits = ON`
- `Outlier filter = ON`
- `Confidence gate = ON`

### If clipping still happens

- lower the main target
- enable `Dynamic`
- try `Kerb filter`
- lower `Safety ceiling`

### If FFB feels too weak

- raise the main target slightly
- increase `Lock percentile`
- raise `Safety ceiling`

## 11. Very short summary

The most important settings are:
- `Torque target (Nm)` or `FFB Strength`
- `Default torque target (Nm)` or `Default FFB strength (%)`
- `Hardware max torque`
- `Dynamic`
- `Adaptive mode`
- `Safety limits`

If you want a healthy starting point:
- stay in `Auto`
- set `Hardware max torque` correctly
- keep a realistic main target
- enable protection features before increasing force
