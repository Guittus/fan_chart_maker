# 🧬 GénéaFan Pro - Visualiseur d'éventail élastique

GénéaFan Pro est une application Python permettant de transformer vos fichiers **GEDCOM** en arbres généalogiques en éventail (fan charts) allant de **2 à 15 générations**. 

L'application a été conçue avec une priorité : **la lisibilité**. Elle introduit le concept d'éventail "élastique", permettant de moduler l'espace de chaque branche pour compenser les zones vides de votre généalogie.

## ✨ Fonctionnalités clés

*   **Profondeur extrême** : Supporte jusqu'à 15 générations (32 768 individus théoriques).
*   **Éventail Élastique** : Clic droit sur une case pour élargir ou réduire une branche (Paternelle/Maternelle).
*   **Amplitude Variable** : Choix du rendu sur 180°, 270°, 345° ou 360°.
*   **Personnalisation Totale** : Double-clic sur n'importe quelle case pour modifier le nom, la couleur de fond et la taille de la police.
*   **Navigation Intuitive** : Zoom à la molette (centré sur le curseur) et déplacement "Drag & Drop".
*   **Export Haute Définition** : Génération de fichiers **PDF vectoriels au format A2** (imprimables sans perte de qualité).

## 🛠️ Installation

1. Assurez-vous d'avoir Python 3.10+ installé.
2. Installez les dépendances nécessaires :
   ```bash
   pip install PyQt6 python-gedcom