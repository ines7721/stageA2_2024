# Stage de deuxième année - Détection de variations de résistivité sur micro-contrôleur nRF52840 

![MicroPython](https://img.shields.io/badge/MicroPython-1.20+-blue?logo=python)
![Systèmes embarqués](https://img.shields.io/badge/Systèmes-embarqués-lightgrey)
![Microcontrôlleur nRF52840](https://img.shields.io/badge/nRF52840-SoC-76B900)
![Traitement du signal](https://img.shields.io/badge/Signal-processing-brightgreen)
![SAADC](https://img.shields.io/badge/ADC-SAADC-orange)
![Random Forest](https://img.shields.io/badge/Machine%20Learning-Random%20Forest-yellow)
 

## Description du projet

Ce projet étudie la faisabilité d’un dispositif embarqué permettant la détection de variations de résistivité à l’aide de ponts diviseurs de tension et d’un micro-contrôleur Seeed Studio XIAO nRF52840.  
Les données de résistivité sont acquises via le SAADC, traitées en temps réel, puis analysées à l’aide d’un algorithme Random Forest implémenté en MicroPython, afin de détecter la présence d’un composé cible : le DMMP.

Les tâches effectuées pour ce faire sont :
- le prototypage et la mise en place de l’architecture matérielle,
- l’acquisition et le traitement du signal,
- l’implémentation de l’algorithme de classification,
- les tests de précision, de fréquence d’échantillonnage, de mémoire et de temps de calcul.

---

## Objectifs

- Mesurer des résistances inconnues via des ponts diviseurs de tension
- Évaluer la précision de mesure en fonction des résistances de référence
- Étudier les limites matérielles (ADC, mémoire, GPIO)
- Implémenter un algorithme de classification Random Forest embarqué
- Analyser les performances et limitations du système

---

## Architecture matérielle

- **Micro-contrôleur** : Seeed Studio XIAO nRF52840  
- **Méthode de mesure** : ponts diviseurs de tension (jusqu’à 3 ponts)
- **ADC** : SAADC (16 bits, approximation successive)
- **Tension d’alimentation** : ~3.3 V (mesurée dynamiquement)

Contraintes principales :
- 6 entrées ADC → maximum 3 résistances mesurées simultanément
- Mémoire RAM limitée (~256 kB)

<img width="1488" height="1100" alt="unnamed (1)" src="https://github.com/user-attachments/assets/3c983f2a-5557-4053-a14f-50070a42e57a" />


---

## Fonctionnement général

1. Acquisition des tensions U et U2 via le SAADC  
2. Calcul de la tension de référence VDD à chaque itération  
3. Calcul des résistances inconnues par la loi d’Ohm  
4. Sur-échantillonnage pour améliorer la robustesse des mesures  
5. Extraction de paramètres (intégrale, dérivée max, delta, somme)  
6. Classification via Random Forest  
7. Arrêt du programme en cas de détection de DMMP  

---

## Paramètres principaux

- Nombre de résistances mesurées
- Fréquence d’échantillonnage
- Nombre d’échantillons consécutifs
- Nombre de sur-échantillons
- Pourcentage de déviation acceptable
- Résolution ADC
- Fréquence d’étalonnage
- Hyper-paramètres Random Forest (arbres, nœuds, seuils)

---

## Résultats

### Précision des mesures
- Résistance de référence optimale : 100 kΩ
- Plage de mesure fiable : 10 kΩ → 1 MΩ
- Erreur moyenne ≈ 2–3 %

### Fréquence d’échantillonnage
- Fréquence maximale mesurée : 246.3 Hz
- Limitation due au temps d’exécution du code

### Mémoire et performances
- La classification Random Forest consomme jusqu’à ~68 % de la RAM disponible
- Exécution continue limitée à quelques minutes
- La mémoire est le facteur limitant principal

---

## Limites identifiées

- Mémoire insuffisante pour un fonctionnement long terme
- Nombre limité de GPIO ADC
- Temps de calcul élevé lors de la classification
- Consommation énergétique non évaluée

---

## Conclusion

Le projet démontre que la mesure de résistivité avec une bonne précision est réalisable sur le nRF52840.  
En revanche, l’exécution embarquée prolongée d’un algorithme de classification de type Random Forest dépasse les capacités mémoire de la carte dans sa configuration actuelle.

Certaines pistes d’amélioration sont :
- Externalisation du traitement
- Simplification de l’algorithme de classification
- Optimisation mémoire plus agressive
- Choix d’un micro-contrôleur plus puissant

---

## Références

- Documentation officielle Seeed Studio XIAO nRF52840  
- Étude de référence sur la détection d’ammoniaque  
- Datasheet Nordic Semiconductor nRF52840  

---
