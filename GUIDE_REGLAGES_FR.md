# Manuel complet FFBClipX

Ce guide decrit l'ensemble de l'interface FFBClipX en francais:
- les boutons
- les cases a cocher
- les valeurs reglables
- les informations affichees
- les fichiers de sauvegarde

Le guide anglais equivalent est disponible dans `GUIDE_SETTINGS_EN.md`.

## 1. Role de FFBClipX

FFBClipX aide a limiter le clipping du retour de force dans Assetto Corsa.

L'application surveille le signal FFB, estime une cible utile, puis ajuste le gain voiture pour:
- garder le plus de detail possible
- eviter les saturations trop frequentes
- adapter le comportement selon la voiture, le circuit et la session

## 2. Organisation de l'interface

L'application est divisee en 2 niveaux:
- le HUD principal
- la fenetre `Options`, elle-meme divisee en 4 onglets:
- `Drive`
- `Adaptive`
- `Protection`
- `Tools`

## 3. Elements du HUD principal

### `FFBClipX`

Titre de l'application.

### Ligne voiture / circuit

Affiche la voiture et le circuit charges.

Exemple:
- `gp_2026_amr26 | rt_suzuka / layout_f1_2026`

### `Mode badge`

Affiche un resume de l'etat courant:
- `AUTO` ou `MANUAL`
- mode adaptatif actif
- `DYN` si le mode dynamique est actif

### `Torque target (Nm)` ou `FFB Strength`

Controle principal du HUD.

Selon le mode:
- en `Direct Drive mode = ON`, la valeur est en `Nm`
- en `Direct Drive mode = OFF`, la valeur est en `%`

Cette valeur represente la cible active pour la voiture courante.

Plage:
- DD: `3` a `50 Nm`
- non DD: `10` a `120 %`

### Ligne message

Affiche le message d'etat principal:
- mode auto actif
- clipping protege ou non
- reset
- rollback
- apprentissage

### Ligne detail

Affiche un resume rapide:
- profil `Race` ou `Qualif`
- mode de courbe
- mode d'affichage

### Ligne `Combo / Default / Safety`

Resume de 3 valeurs:
- `Combo`: point de depart memorise pour la combinaison voiture/circuit
- `Default`: cible par defaut
- `Safety`: plage mini / maxi autorisee par les limites de securite

### Ligne `Wet / Kerb / Diag / Cal`

Resume des fonctions avancees:
- etat du mode pluie
- etat du filtre vibreurs
- etat du dashboard diagnostic
- etat du helper de calibration

### Graphe

Affiche le signal selon le mode d'affichage:
- `Off`: pas de graphe utile
- `Graph`: courbe en temps reel
- `Histogram`: repartition statistique du signal

Dans le graphe temps reel:
- ligne rouge: cible
- ligne verte: force observee

### Bouton `Mode: Auto`

Bascule entre:
- `Auto`: FFBClip ajuste le gain automatiquement
- `Manual`: FFBClip n'essaie plus d'empecher le clipping

Recommandation:
- laisser `Auto` dans la plupart des cas

### Bouton `Dynamic: ON/OFF`

Active ou desactive la reaction rapide aux pics brefs de clipping.

Quand l'activer:
- clipping sur vibreurs
- compressions
- gros appuis soudains

### Bouton `Reset`

Remet la cible actuelle sur la valeur par defaut.

Effet:
- reset de l'histogramme
- retour a la cible de base

Important:
- n'efface pas l'apprentissage
- ne supprime pas la valeur `Lock`
- ne supprime pas les donnees sauvegardees du combo courant
- sert seulement a revenir rapidement a la cible par defaut pendant la session

### Bouton `Options`

Ouvre ou ferme la fenetre de configuration avancee.

## 4. Onglet `Drive`

### `Manual override`

Case a cocher.

Effet:
- active le mode manuel
- desactive la protection automatique contre le clipping

### `Direct Drive mode`

Case a cocher.

Effet:
- `OFF`: l'application travaille en pourcentage
- `ON`: l'application travaille en `Nm`

Utiliser `ON` si ton volant est regle autour d'un couple reel connu.

### `Run in background`

Case a cocher.

Effet:
- l'app continue a tourner meme si sa fenetre n'est pas active

### `CSV logging`

Case a cocher.

Effet:
- enregistre des donnees runtime dans `Config/ffbclip_runtime_log.csv`

Utile pour:
- debug
- analyse de session

### `Default FFB strength (%)` ou `Default torque target (Nm)`

Spinner.

Plage:
- DD: `3` a `50`
- non DD: `10` a `120`

Role:
- definit la cible de depart generale
- sert de base avant les adaptations contextuelles

### `Hardware max torque`

Spinner disponible en mode DD.

Plage:
- `3` a `50 Nm`

Role:
- represente le couple max reel du materiel

Important:
- si cette valeur est fausse, toutes les conversions DD deviennent fausses

### `Display mode`

Bouton cyclique.

Ordre:
- `Off`
- `Graph`
- `Histogram`

### `Graph refresh (Hz)`

Spinner.

Plage:
- `1` a `30`

Role:
- frequence de rafraichissement du graphe

### `Dynamic threshold (%)`

Spinner.

Plage:
- `10` a `300`

Role:
- seuil du mode dynamique

Interpretation:
- plus bas = reaction plus protectrice
- plus haut = reaction plus permissive

### `Dynamic intensity`

Spinner.

Plage:
- `50` a `500`

Role:
- vitesse de reaction du mode dynamique

Interpretation:
- plus bas = plus doux
- plus haut = plus agressif

### `Preset snapshot`

Case a cocher.

Effet:
- autorise la sauvegarde d'un instantane de reglages dans `FFBClip.ini`

### `Session report`

Case a cocher.

Effet:
- genere un rapport texte de session dans `Config/ffbclip_session_report.txt`

## 5. Onglet `Adaptive`

### `Adaptive mode`

Bouton cyclique.

Ordre:
- `Classic`
- `Lock`
- `Hybrid`

Role:
- `Classic`: adaptation continue
- `Lock`: apprend une base puis la verrouille
- `Hybrid`: apprend une base puis autorise une variation limitee autour

Note:
- changer ce mode reinitialise l'apprentissage

### `Profile mode`

Bouton cyclique.

Valeurs:
- `Race`
- `Qualif`

Role:
- permet une legere variation de comportement selon le contexte

Note:
- cliquer dessus desactive `Auto session profile`

### `Learn laps`

Spinner.

Plage:
- `1` a `20`

Role:
- nombre de tours utilises pour apprendre

### `Lock percentile`

Spinner.

Plage:
- `1` a `50`

Role:
- percentile utilise pour calculer la base en mode `Lock`

Interpretation:
- plus bas = plus prudent
- plus haut = plus fort mais plus risqe de clipping

### `Hybrid band (%)`

Spinner.

Plage:
- `5` a `50`

Role:
- amplitude autorisee autour de la base verrouillee en mode `Hybrid`

### `Confidence gate (%)`

Spinner.

Plage:
- `50` a `98`

Role:
- confiance minimale necessaire avant d'autoriser le verrouillage

### `Phase learning`

Case a cocher.

Role:
- segmente l'apprentissage par zones de vitesse / charge

Note:
- changer cet etat reinitialise l'apprentissage

### `Show confidence`

Case a cocher.

Role:
- affiche la confiance d'apprentissage dans l'interface

### `Confidence gate`

Case a cocher.

Role:
- active ou desactive le verrou base sur le seuil de confiance

### `Setup-aware learn`

Case a cocher.

Role:
- reinitialise l'apprentissage si un changement important de setup est detecte

### `Auto reset combo`

Case a cocher.

Role:
- reinitialise l'apprentissage lors d'un changement voiture/circuit

### `Auto session profile`

Case a cocher.

Role:
- choisit automatiquement `Race` ou `Qualif` selon la session si possible

### `Profile shaping`

Case a cocher.

Role:
- applique une legere correction selon le profil courant

### `Rollback gate`

Case a cocher.

Role:
- autorise l'utilisation d'une valeur de secours si la confiance n'est pas suffisante

## 6. Onglet `Protection`

### `Outlier filter`

Case a cocher.

Role:
- filtre les pointes aberrantes pour eviter qu'un pic unique fausse la logique

### `Anti oscillation`

Case a cocher.

Role:
- evite les micro-corrections trop frequentes

### `Safety limits`

Case a cocher.

Role:
- active un plancher et un plafond de gain

### `Endurance ceiling`

Case a cocher.

Role:
- reduit progressivement le plafond de force sur les longues sessions

### `Safety floor (%)`

Spinner.

Plage:
- `20` a `150`

Role:
- gain minimum autorise

### `Safety ceiling (%)`

Spinner.

Plage:
- `80` a `300`

Role:
- gain maximum autorise

### `Deadband (%)`

Spinner.

Plage:
- `0` a `20`

Role:
- ignore les corrections trop petites

### `Min interval (ms)`

Spinner.

Plage:
- `50` a `1000`

Role:
- intervalle minimal entre deux corrections

### `Endurance start (min)`

Spinner.

Plage:
- `10` a `240`

Role:
- moment ou la reduction d'endurance commence

### `Max endurance drop (%)`

Spinner.

Plage:
- `0` a `30`

Role:
- reduction maximale autorisee en endurance

### `Wet softening`

Case a cocher.

Role:
- adoucit le comportement si le grip chute

### `Kerb filter`

Case a cocher.

Role:
- atténue certains pics sur vibreurs / chocs

### `Wet grip threshold (%)`

Spinner.

Plage:
- `60` a `100`

Role:
- seuil de grip sous lequel le mode pluie commence a agir

### `Wet softening (%)`

Spinner.

Plage:
- `0` a `30`

Role:
- intensite de l'adoucissement pluie

### `Kerb spike threshold (%)`

Spinner.

Plage:
- `5` a `80`

Role:
- sensibilite de detection des pics

### `Kerb damp factor (%)`

Spinner.

Plage:
- `35` a `100`

Role:
- reduction appliquee apres detection d'un pic

## 7. Onglet `Tools`

### `Response curves`

Case a cocher.

Role:
- active un remodelage de la courbe de ressenti

### `Anti fatigue`

Case a cocher.

Role:
- adoucit une plage d'effort pour reduire la fatigue

### `Response curve`

Bouton cyclique.

Ordre:
- `Linear`
- `Expo`
- `S-curve`

### `Curve strength (%)`

Spinner.

Plage:
- `0` a `100`

Role:
- intensite de la courbe choisie

### `Fatigue low band (%)`

Spinner.

Plage:
- `20` a `90`

Role:
- debut de la zone concernee par l'anti-fatigue

### `Fatigue high band (%)`

Spinner.

Plage:
- `30` a `100`

Role:
- fin de la zone concernee par l'anti-fatigue

### `Fatigue reduction (%)`

Spinner.

Plage:
- `0` a `35`

Role:
- reduction appliquee dans la zone anti-fatigue

### `Diag dashboard`

Case a cocher.

Role:
- active l'affichage de diagnostics supplementaires

### `Diag refresh (s x100)`

Spinner.

Plage:
- `25` a `500`

Role:
- cadence du diagnostic

Interpretation:
- `100` = `1.00 s`

### `Calibration helper`

Case a cocher.

Role:
- active l'assistant de calibration

### `Calib warmup laps`

Spinner.

Plage:
- `0` a `5`

Role:
- tours d'echauffement avant apprentissage

### `Calib learn laps`

Spinner.

Plage:
- `1` a `10`

Role:
- tours utilises pour apprendre la calibration

### `Calib validation laps`

Spinner.

Plage:
- `1` a `10`

Role:
- tours utilises pour verifier la calibration

## 8. Boutons d'action en bas de la fenetre options

### `Start calib` / `Stop calib`

Demarre ou arrete la sequence de calibration.

### `Reset learn`

Efface les donnees d'apprentissage:
- historique
- lock
- confiance

Portee:
- seulement pour la voiture actuelle
- seulement pour le circuit actuel
- supprime la donnee de `lock` sauvegardee pour ce combo

Difference avec `Reset`:
- `Reset` remet la cible active a la valeur par defaut sans effacer l'apprentissage
- `Reset learn` efface l'apprentissage du combo courant

### `Rollback`

Applique une valeur de secours si elle existe.

### `Close`

Ferme la fenetre d'options.

## 9. Fichiers de configuration

### `Config/FFBClip.ini`

Contient:
- reglages generaux
- cible par defaut
- cibles DD sauvegardees
- sections de presets

Sections importantes:
- `[Options]`
- `[targetgains]`
- `[targettorquesnm]`
- `[Preset_*]`

### `Config/Combos.ini`

Contient:
- une valeur memorisee par combinaison voiture/circuit
- les valeurs de lock apprises

### `Config/ffbclip_runtime_log.csv`

Cree si `CSV logging` est actif.

### `Config/ffbclip_session_report.txt`

Cree si `Session report` est actif.

## 10. Reglages conseilles pour commencer

### Base DD simple

- `Mode: Auto`
- `Direct Drive mode = ON`
- `Hardware max torque = couple reel du volant`
- `Torque target = un peu sous la limite materielle`
- `Adaptive mode = Lock`
- `Learn laps = 3 a 5`
- `Lock percentile = 20 a 25`
- `Safety limits = ON`
- `Outlier filter = ON`
- `Confidence gate = ON`

### Si tu as encore du clipping

- baisse la cible principale
- active `Dynamic`
- teste `Kerb filter`
- reduis `Safety ceiling`

### Si le FFB devient trop mou

- remonte legerement la cible
- augmente `Lock percentile`
- remonte `Safety ceiling`

## 11. Resume ultra-court

Les reglages les plus importants sont:
- `Torque target (Nm)` ou `FFB Strength`
- `Default torque target (Nm)` ou `Default FFB strength (%)`
- `Hardware max torque`
- `Dynamic`
- `Adaptive mode`
- `Safety limits`

Si tu veux un comportement sain:
- reste en `Auto`
- regle correctement le `Hardware max torque`
- garde une cible principale realiste
- active les protections avant d'augmenter la force
