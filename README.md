# 🎬 VideoTiktok — 104 Vidéos d'Animaux Sauvages Parlants (< 1 min)

Plateforme complète de génération et de visualisation de **vidéos verticales TikTok / Instagram Reels / YouTube Shorts (format 9:16)** où **104 animaux du monde entier parlent à la première personne** pour raconter leur histoire secrète, leurs anecdotes fascinantes et leurs super-pouvoirs biologiques.

Chaque vidéo dure **moins de 1 minute** (entre 25 et 40 secondes), intègre des **sous-titres dynamiques synchronisés**, une **narration vocale en français**, des **effets visuels cinématiques**, un **visualiseur audio animé** et **ne contient aucun logo Arena**.

---

## 🌟 Caractéristiques Principales

- **104 Animaux Répertoriés** : De la savane aux abysses océaniques, des glaces polaires aux jungles d'Amazonie et forêts tempérées.
- **Monologues Immersifs en Français** : Chaque animal s'adresse directement au spectateur (*« Moi, le lion d'Afrique, roi de la savane... »*, *« Je suis le dauphin, danseur des mers turquoises... »*).
- **Format TikTok Vertical Natif (9:16)** : Résolution 720x1280 à 30 images par seconde (H.264 / AAC).
- **Sous-Titres Dynamiques Synchronisés** : Style moderne TikTok avec mise en surbrillance des mots prononcés en temps réel (karaoké).
- **Effets Cinématiques Ken Burns** : Mouvements de caméra lents (zoom & pan), faisceaux lumineux atmosphériques, particules et visualiseur audio dynamique.
- **Export Téléchargeable Immédiat** : Téléchargement direct des fichiers vidéo `.mp4` et des fichiers de sous-titres `.srt` / `.vtt`.
- **Lecteur Web TikTok Interactif** : Défilement vertical fluide au clavier / souris / tactile, synthèse vocale française (Web Speech API + MP3).
- **100% Propre & Sans Logo** : Aucun filigrane ni logo Arena ajouté.

---

## 🗂️ Les 10 Groupes & 104 Animaux

| Catégorie | Nombre | Exemples d'Animaux |
| :--- | :---: | :--- |
| **Savane & Félins** | 12 | Lion, Tigre du Bengale, Guépard, Léopard, Jaguar, Panthère Noire, Puma, Caracal, Serval, Hyène... |
| **Océans & Mers** | 14 | Dauphin, Baleine Bleue, Grand Requin Blanc, Orque, Pieuvre, Tortue Marine, Hippocampe, Raie Manta... |
| **Oiseaux & Ciel** | 12 | Aigle Royal, Hibou Grand-Duc, Faucon Pèlerin, Perroquet Ara, Colibri, Toucan, Flamant Rose... |
| **Forêts & Terres Tempérées** | 14 | Loup Gris, Renard Roux, Ours Grizzly, Cerf Élaphe, Écureuil, Hérisson, Raton Laveur, Castor, Lynx... |
| **Grands Mammifères** | 10 | Éléphant d'Afrique, Rhinocéros Blanc, Hippopotame, Girafe, Zèbre, Bison, Buffle du Cap, Okapi... |
| **Jungle & Primates** | 10 | Chimpanzé, Gorille de Montagne, Orang-outan, Panda Géant, Lémurien, Paresseux, Caméléon, Anaconda... |
| **Arctique & Glaces** | 8 | Ours Polaire, Renard Polaire, Lièvre Arctique, Bœuf Musqué, Renne, Harfang des Neiges, Phoque... |
| **Australie & Terres Exotiques** | 8 | Kangourou Roux, Koala, Ornithorynque, Diable de Tasmanie, Wombat, Émeu, Échidné, Dingo... |
| **Déserts & Terres Arides** | 8 | Chameau de Bactriane, Dromadaire, Fennec, Suricate, Scorpion Empereur, Vipère à Cornes... |
| **Compagnons & Ferme** | 8 | Chien Golden Retriever, Chat Domestique, Cheval Pur-Sang, Mouton Mérinos, Chèvre Alpine, Vache... |

---

## 🚀 Utilisation & Commandes

### 1. Démarrer le Serveur Web Studio & Lecteur TikTok
```bash
python3 server.py
```
Accédez ensuite à l'interface web sur le port `8080` (accessible sur `0.0.0.0:8080`).

### 2. Générer une Vidéo Spécifique en Ligne de Commande
```bash
python3 -c "from video_engine import *; animal = ANIMALS_DATA[0]; render_animal_video(animal, 'videos/lion.mp4')"
```

### 3. Rendu par Lot (Batch)
```bash
# Générer les 15 premiers animaux
python3 video_engine.py --sample

# Générer les 104 animaux
python3 video_engine.py --all
```

---

## 📂 Structure du Répertoire

- `animals_dataset.json` : Base de données complète des 104 animaux (histoires en français, métadonnées, sous-titres timés, super-pouvoirs).
- `artwork_engine.py` : Moteur de génération des portraits d'animaux 9:16 verticaux et ambiances lumineuses.
- `audio_engine.py` : Moteur de synthèse audio multi-pistes (voix narrative + bande sonore d'ambiance naturelle).
- `video_engine.py` : Moteur de rendu vidéo haute performance FFmpeg (animations, sous-titres TikTok, visualiseur de son).
- `server.py` : Serveur HTTP multi-thread avec support du streaming vidéo par tranches (`HTTP 206 Range`).
- `public/` : Interface Web Studio TikTok (Lecteur vertical, Encyclopédie, Studio de génération).
- `images/` : Fichiers d'illustrations et portraits des animaux.
- `audio/` : Pistes audio narrées et ambiances sonores.
- `videos/` : Fichiers vidéo MP4 verticaux générés.
