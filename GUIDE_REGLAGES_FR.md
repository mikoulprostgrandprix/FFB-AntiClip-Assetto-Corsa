# Guide des reglages FFBClipX

Ce document explique le fonctionnement de l'application et la signification de tous les reglages exposes dans l'interface et dans `Config/FFBClip.ini`.

## 1. A quoi sert FFBClipX

FFBClipX essaie de reduire le clipping du retour de force dans Assetto Corsa en ajustant automatiquement le gain FFB de la voiture.

En pratique, il observe le signal FFB, estime le niveau utile, puis corrige le gain voiture pour:

- eviter que le signal sature trop souvent
- conserver autant de detail que possible
- adapter le gain selon la voiture, le circuit et la session

## 2. Le point le plus important pour ton cas

Dans ta configuration actuelle:

- `ddtoggle = 1` -> mode Direct Drive actif
- `maxtorque = 18.0` -> ton couple max materiel est regle a 18 Nm
- `dynamicmode = 0` -> le mode dynamique est desactive
- `adaptivemode = 1` -> mode `Lock` actif

Tres important:

- en mode `Direct Drive`, si la cible de couple depasse le `max torque` materiel, l'application autorise volontairement du clipping
- si tu affiches `19 Nm` alors que `max torque = 18 Nm`, tu demandes deja plus que ce que la base doit fournir proprement

Donc, avant de chercher une autre option:

1. garde `Mode Auto`
2. garde `Manual override` desactive
3. mets la cible de couple a `18 Nm` ou moins
4. active `Dynamic mode` si tu veux mieux attraper les pics transitoires

## 3. Les trois valeurs a bien distinguer

Il y a trois notions importantes dans l'app:

- `TargetGain`:
  Valeur par defaut de depart. C'est ta base generale.
- `CarGainTarget`:
  Cible effective pour la voiture courante.
- `CarGain`:
  Gain actuellement applique a la voiture dans Assetto Corsa.

Dans la ligne d'etat `Gain T/S/A`:

- `T` = target calcule
- `S` = target lisse
- `A` = gain reel applique

## 4. Regles simples pour ne plus clipper

Si ton objectif est "le moins de clipping possible", pars sur ces regles:

1. `Manual override` doit rester desactive.
2. En DD, la cible de couple ne doit pas depasser `max torque`.
3. `Dynamic mode` peut etre active si tu as encore des pics courts.
4. `Adaptive mode = Lock` ou `Hybrid` est preferable a `Classic` pour stabiliser le comportement.
5. `Safety limits`, `Outlier filter`, `Confidence gate` et `Rollback` doivent rester actifs.
6. Si ca clippe encore, baisse la cible avant d'ajouter des artifices.

## 5. Explication de chaque reglage

## Onglet Drive

### Mode Auto / Manual override

- `Mode Auto`:
  L'application ajuste le gain automatiquement.
- `Manual override`:
  L'application n'essaie plus d'empecher le clipping. A eviter si tu veux la protection maximale.

### Direct Drive mode

A activer si tu regles la force en Nm et non en pourcentage.

- OFF:
  La cible FFB est geree en pourcentage.
- ON:
  La cible est geree en Nm.

En DD, `max torque` est la reference materielle du volant.

### Run in background

- OFF:
  L'app travaille surtout quand sa fenetre est rendue.
- ON:
  L'app continue a tourner meme si la fenetre n'est pas au premier plan.

### CSV logging

Ecrit un journal runtime dans:

- `Config/ffbclip_runtime_log.csv`

Pratique pour analyser le comportement, inutile pour la simple conduite.

### Default FFB strength (%) / Default torque target (Nm)

C'est la valeur de base de depart de l'application.

- si tu changes souvent de voiture, cette valeur sert de point de depart
- ce n'est pas forcement la valeur finale appliquee en piste

### Hardware max torque

Disponible en mode DD.

Doit representer le couple reel max de ton volant.

Exemple:

- base 18 Nm -> regle `18`
- base 20 Nm -> regle `20`

Si cette valeur est fausse, toute la logique DD devient fausse.

### Display mode

- `Off`:
  pas d'affichage special
- `Graph`:
  graphe temps reel
- `Histogram`:
  repartition du signal

### Graph refresh (Hz)

Frequence de rafraichissement du graphe.

- plus haut = plus fluide
- plus bas = plus leger

### Dynamic mode

Mode plus agressif contre les pics soudains.

- OFF:
  comportement plus stable et plus doux
- ON:
  reaction plus rapide aux pointes de clipping

Si tu as encore du clipping en entree de vibreurs, compressions ou grosses charges, c'est la premiere option a essayer.

### Dynamic threshold (%)

Limite haute du mode dynamique.

- plus bas = protection plus forte
- plus haut = plus de liberte, mais plus de risque de saturation

### Dynamic intensity

Vitesse de reaction du mode dynamique.

- plus faible = plus doux
- plus fort = plus reactif

Si tu montes trop haut, le gain peut devenir nerveux.

### Preset snapshot

Sauvegarde un instantane des reglages de base dans `FFBClip.ini`.

### Session report

Genere un petit rapport de session dans:

- `Config/ffbclip_session_report.txt`

## Onglet Adaptive

### Adaptive mode

- `Classic`:
  adaptation continue classique
- `Lock`:
  apprend pendant quelques tours puis verrouille une base
- `Hybrid`:
  apprend une base puis laisse une variation controlee autour

Pour la plupart des cas:

- `Lock` = stable
- `Hybrid` = stable mais un peu plus vivant

### Learn laps

Nombre de tours utilises pour apprendre la base.

- trop bas = apprentissage trop rapide et parfois faux
- trop haut = lent a converger

Bon point de depart:

- `3` a `5` tours

### Lock percentile

Percentile utilise pour calculer la base en mode `Lock`.

- plus bas = plus prudent, moins de clipping, moins de force
- plus haut = plus de force, plus de risque de saturation

Valeur souvent saine:

- `20` a `25`

### Hybrid band (%)

Amplitude autorisee autour de la base verrouillee en mode `Hybrid`.

- plus bas = plus stable
- plus haut = plus libre

### Profile mode

- `Race`
- `Qualif`

Le mode `Qualif` peut etre un peu plus agressif.

### Auto session profile

Permet a l'app de changer de profil selon la session si possible.

### Phase learning

Apprentissage par plages de vitesse:

- lent
- moyen
- rapide

Cela aide a construire un `Lock` plus intelligent.

### Show confidence

Affiche la confiance de l'apprentissage.

### Confidence gate

Empêche d'appliquer un verrouillage trop tot tant que l'apprentissage n'est pas assez fiable.

### Confidence gate (%)

Seuil de confiance minimal avant d'autoriser le `Lock`/`Hybrid`.

- plus haut = plus prudent
- plus bas = plus rapide

### Setup-aware learn

Remet l'apprentissage a zero si des parametres structurants changent.

### Auto reset combo

Reinitialise l'apprentissage quand le couple voiture/circuit change.

### Profile shaping

Petite correction selon le profil `Race` ou `Qualif`.

### Rollback gate

Si la confiance n'est pas suffisante, l'app peut revenir a une valeur de secours plus sure.

## Onglet Protection

### Outlier filter

Filtre les valeurs aberrantes.

Utile pour eviter qu'un pic unique fausse tout.

### Anti oscillation

Evite les micro-corrections trop frequentes.

### Safety limits

Active des bornes minimales et maximales de gain.

### Safety floor (%)

Gain minimum autorise.

- trop haut = la protection peut devenir moins efficace
- trop bas = la force peut devenir trop faible

### Safety ceiling (%)

Gain maximum autorise.

- plus bas = plus de securite anti-clipping
- plus haut = plus de force possible

### Deadband (%)

Ignore les corrections trop petites.

### Min interval (ms)

Temps minimal entre deux corrections.

### Endurance ceiling

Adoucit progressivement le plafond de force sur les longues sessions.

### Endurance start (min)

Moment a partir duquel la reduction d'endurance commence.

### Max endurance drop (%)

Reduction maximale autorisee.

### Wet softening

Adoucit le FFB si le grip chute fortement.

Ce n'est pas une vraie protection de clipping, plutot une adaptation aux conditions.

### Wet grip threshold (%)

Seuil de grip sous lequel l'adoucissement commence.

### Wet softening (%)

Intensite de l'adoucissement.

### Kerb filter

Freine certains pics tres brusques, souvent sur vibreurs ou gros chocs.

Peut aider si ton clipping vient surtout de gros spikes.

### Kerb spike threshold (%)

Sensibilite de detection des pics.

### Kerb damp factor (%)

Reduction appliquee quand un pic est detecte.

## Onglet Tools

### Response curves

Change la courbe de ressenti, pas la protection anti-clipping principale.

### Response curve

- `Linear`
- `Expo`
- `S-curve`

### Curve strength (%)

Force de la courbe choisie.

### Anti fatigue

Adoucit une certaine plage de forces pour moins fatiguer sur la duree.

Ce n'est pas un vrai outil anti-clipping.

### Fatigue low band (%)

Debut de la plage concernee.

### Fatigue high band (%)

Fin de la plage concernee.

### Fatigue reduction (%)

Reduction appliquee dans cette plage.

### Diag dashboard

Ajoute plus d'informations de diagnostic dans la ligne d'etat.

### Diag refresh

Frequence de mise a jour de ces diagnostics.

### Calibration helper

Active l'assistant de calibration.

### Start calib / Stop calib

Demarre ou stoppe la sequence de calibration.

### Calib warmup laps

Tours d'echauffement avant apprentissage.

### Calib learn laps

Tours utilises pour apprendre.

### Calib validation laps

Tours utilises pour verifier la coherence du resultat.

### Reset learn

Efface les donnees d'apprentissage.

### Rollback

Applique manuellement une valeur de secours si elle existe.

## 6. Fichiers de configuration

### `Config/FFBClip.ini`

Reglages generaux et presets.

### `Config/Combos.ini`

Memorise un point de depart par combinaison circuit + voiture.

### Section `[targetgains]` dans `FFBClip.ini`

Mémorise la cible de base par voiture.

## 7. Ce qui est active ou non chez toi

### Actif actuellement

- `Mode Auto`
- `Direct Drive mode`
- `Adaptive mode = Lock`
- `Outlier filter`
- `Anti oscillation`
- `Safety limits`
- `Phase learning`
- `Confidence gate`
- `Rollback`
- `Preset snapshot`
- `Session report`

### Desactive actuellement

- `Dynamic mode`
- `Endurance ceiling`
- `CSV logging`
- `Wet softening`
- `Kerb filter`
- `Response curves`
- `Anti fatigue`
- `Diag dashboard`
- `Calibration helper`

## 8. Ce qu'il faut activer si tu as encore du clipping

Ordre de priorite conseille:

1. baisse la cible de couple pour rester a `18 Nm` max si ton `max torque` vaut `18`
2. active `Dynamic mode`
3. si les gros pics viennent surtout des chocs et vibreurs, active `Kerb filter`
4. garde `Safety limits`, `Outlier filter`, `Confidence gate` et `Rollback` actifs
5. si le comportement reste trop flottant, essaie `Hybrid` au lieu de `Lock`

## 9. Reglage simple recommande pour commencer

Pour une base saine anti-clipping:

- `Mode Auto`
- `Manual override = OFF`
- `Direct Drive mode = ON`
- `Hardware max torque = 18`
- `Torque target = 16 a 18 Nm`
- `Dynamic mode = ON`
- `Adaptive mode = Lock`
- `Learn laps = 3`
- `Lock percentile = 20 a 25`
- `Confidence gate = ON`
- `Safety limits = ON`
- `Outlier filter = ON`

## 10. Symptomes et causes

### "Ca clippe encore dans les gros appuis"

Causes probables:

- cible trop haute
- `Dynamic mode` OFF
- `Safety ceiling` trop haute

### "Ca clippe surtout sur les vibreurs"

Causes probables:

- gros spikes transitoires

Essayer:

- `Dynamic mode = ON`
- `Kerb filter = ON`

### "Le FFB est trop faible"

Causes probables:

- cible trop basse
- `Lock percentile` trop prudent
- `Safety ceiling` trop restrictive

## 11. Resume tres court

Si tu ne devais retenir que 4 choses:

1. en DD, ne depasse pas le `max torque` si tu veux eviter le clipping
2. laisse `Mode Auto` actif
3. active `Dynamic mode` si tu as encore des pics
4. `Lock` ou `Hybrid` sont les meilleurs modes de depart
