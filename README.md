# Projet de Synchronisation Vidéo-Musique

## Description

Ce projet permet de synchroniser automatiquement ou manuellement des clips vidéo avec une piste audio, en utilisant des interfaces interactives pour guider l’utilisateur tout au long du processus.

Le programme offre deux fonctionnalités principales :

- **Traitement audio** : détection automatique ou manuelle des battements (beats).
- **Synchronisation vidéo** : création d'une vidéo synchronisée avec les battements détectés (un ou plusieurs clips vidéo).

---

## Structure du projet

```
.
├── Synchro_Video_Musique.py <- Point d'entrée du programme
├── interface_video.py
├── interface_video_multiple.py
├── mongif.gif
├── mouse_click_20ms.wav
├── pres_synchronisation_multiple.py
├── pres_synchronisation_video.py
├── synchonisation_une_video.py
├── synchronisation_multiclip.py
├── util.py
├── index.py
├── detect_beats_automatique.py
└── detect_beats_manuelle.py
```

---

## Lancement de l'application

Lancer le fichier principal :

```console
python Synchro_Video_Musique.py
```

## Navigation du programme

Ce fichier redirige vers `index.py`, qui vous propose deux options principales :

1. **Traitement Audio**
   - Détection **manuelle** des beats : exécute `detect_beats_manuelle.py`
   - Détection **automatique** des beats : exécute `detect_beats_automatique.py`
2. **Synchronisation Vidéo**
   - **Un seul clip** : 
     - `pres_synchronisation_video.py` → `interface_video` & `synchonisation_une_video.py`
   - **Plusieurs clips** : 
     - `pres_synchronisation_multiple.py` → `interface_video_multiple` & `synchronisation_multiclip.py`

## Installation des dépendances

Avant d’exécuter le projet, installez les modules nécessaires avec :

```sh
pip install -r modules.txt
```

- **Contenu du fichier modules.txt**

```
        - PyQt5
        - numpy
        - pyqtgraph
        - pydub
        - opencv-python
        - moviepy
        - tqdm
        - json
        - soundfile
```

## Remarques

```
- Compatible avec Python 3.8+

- Assurez-vous que les fichiers audio/vidéo utilisés soient compatibles avec moviepy et opencv.

- Le fichier `mongif.gif` est utilisé à des fins de démonstration visuelle.

- Le fichir `mouse_click_20ms.wav` est utilisé pour nous permettre de vérifier la déction automatique des beats et doit être  present dans le dossier
```