# GénéaFan Pro - Visualiseur d'éventail élastique

GénéaFan Pro est une application Python permettant de transformer vos fichiers **GEDCOM** en arbres généalogiques en éventail (fan charts) allant de **2 à 15 générations**.

L'application a été conçue avec une priorité : **la lisibilité**. Elle introduit le concept d'éventail "élastique", permettant de moduler l'espace de chaque branche pour compenser les zones vides de votre généalogie.

## Fonctionnalités clés

*   **Profondeur extrême** : Supporte jusqu'à 15 générations (32 768 individus théoriques).
*   **Éventail Élastique** : Clic droit sur une case pour élargir ou réduire une branche (Paternelle/Maternelle).
*   **Prévisualisation au survol** : Survoler "Élargir Paternelle" ou "Maternelle" dans le menu met en surbrillance la case concernée dans l'arbre.
*   **Orientation fixe** : Le père est toujours à droite, la mère toujours à gauche, à chaque génération.
*   **Amplitude Variable** : Choix du rendu sur 180°, 270°, 345° ou 360°.
*   **Personnalisation Totale** : Double-clic sur n'importe quelle case pour modifier le nom, la couleur de fond et la taille de la police.
*   **Navigation Intuitive** : Zoom à la molette (centré sur le curseur, clampé entre 5 % et 2000 %) et déplacement "Drag & Drop".
*   **Choix de la personne racine** : Une liste de sélection s'affiche à l'ouverture du fichier pour choisir l'individu au centre de l'éventail.
*   **Affichage des prénoms** : Seul le premier prénom est affiché (les prénoms composés par tiret sont conservés entiers — "Jean-Luc" reste "Jean-Luc").
*   **Export Haute Définition** : Génération de fichiers **PDF vectoriels au format A2** (imprimables sans perte de qualité).

## Installation

1. Assurez-vous d'avoir Python 3.10+ installé.
2. Installez les dépendances nécessaires :
   ```bash
   pip install PyQt6 python-gedcom
   ```

## Utilisation

```bash
python fan_chart_maker.py
```

1. Cliquez sur **Charger GEDCOM** et sélectionnez votre fichier `.ged`.
2. Choisissez la **personne racine** dans la liste qui s'affiche.
3. Ajustez l'**amplitude** (180° à 360°) et le nombre de **générations** dans le panneau gauche.
4. Clic droit sur une case pour ajuster l'espace alloué à la branche paternelle ou maternelle.
5. Double-clic sur une case pour personnaliser le nom, la couleur et la taille de police.
6. Cliquez sur **Export PDF A2** pour générer un fichier vectoriel imprimable.
