# 🌿 Photothèque animalière

Un serveur Web léger écrit en Python permettant de parcourir une photothèque organisée par catégories.

Il repose uniquement sur :

- ThreadingHTTPServer
- SimpleHTTPRequestHandler
- Pillow

**Le développement et les tests ont été réalisés sous Debian 13 (Trixie)**.

---

## Pourquoi ce projet ?

Ce projet est volontairement développé sans framework Web (Flask, Django, FastAPI...).
L'objectif est de comprendre le fonctionnement d'un serveur HTTP en Python en utilisant uniquement les bibliothèques standards (http.server) et Pillow pour la génération des miniatures.

---

### 1. Principe de fonctionnement

L’application fonctionne sur un modèle Client / Serveur classique. 

| Acteur | Rôle |
| --- | --- |
| **Le serveur** | Lit les dossiers de photos sur le disque, génère les pages HTML à la volée et sert les images. |
| **Le navigateur client** | Safari, Chrome, Firefox... Il affiche les pages HTML reçues et envoie une requête `GET` au serveur à chaque clic. |

Aucun JavaScript lourd côté client.   
Chaque action de l'utilisateur (clic, navigation, retour...) provoque une nouvelle requête HTTP GET vers le serveur.

---

### 2. Arborescence attendue

Il faut placer les photos dans des dossiers par catégorie :

```
/home/Photos/
  ├── cerfs_et_biches/
  │   ├── photo1.jpg
  │   └── photo2.jpg
  ├── oiseaux/
  │   └── aigle.png
  └── miniatures/  <- Créé automatiquement par le serveur
```

Dossiers ignorés dans mon arborescence : `miniatures`, `Vidéos animalières`.

Les miniatures `240x240` sont générées une seule fois dans `/miniatures/nom_categorie/` pour accélérer l’affichage.  
Les photos originales ne sont jamais modifiées. Les miniatures sont enregistrées dans un dossier distinct qui constitue un cache permanent.

---

### 3. Navigation : Comment le navigateur communique avec le serveur

Le cœur est la méthode `do_GET` du serveur. Elle analyse l’URL demandée par le navigateur.

#### **Étape 1 : Page d’accueil `/`**
1.  **Client Safari** : Vous tapez `http://IP_DU_SERVEUR:9000/`
2.  **Requête** : Safari envoie `GET /`
3.  **Serveur** : `do_GET` voit `self.path == "/"` -> Il appelle `afficher_categories()`
4.  **Réponse** : Le serveur renvoie du HTML avec une grille de tuiles. Chaque tuile est un lien : `<a href="/categorie/cerfs_et_biches">`

#### **Étape 2 : Galerie d’une catégorie `/categorie/nom`**
1.  **Client Safari** : Vous cliquez sur une tuile "Cerfs et Biches"
2.  **Requête** : Safari fait automatiquement `GET /categorie/cerfs_et_biches`
3.  **Serveur** : `do_GET` voit `self.path.startswith("/categorie/")` -> Il appelle `afficher_galerie_categorie()`
4.  **Réponse** : Le serveur liste les fichiers `.jpg/.png`, crée les miniatures si besoin, et renvoie du HTML avec une grille d’images `<img src="/miniatures/...">`

#### **Étape 3 : Visionneuse `/voir/categorie/index`**
1.  **Client Safari** : vous cliquez sur une miniature
2.  **Requête** : Safari fait `GET /voir/cerfs_et_biches/3`
3.  **Serveur** : `do_GET` -> `afficher_photo_navigation()` 
4. **Réponse** : `afficher_photo_navigation()` génère dynamiquement une page HTML affichant la photo originale adaptée à la taille de la fenêtre.  
   Un clic sur cette photo ouvre le fichier original en pleine résolution dans un nouvel onglet du navigateur.  
   Les flèches `←` et `→` du clavier permettent de parcourir les photos de la catégorie en générant un nouveau `GET` vers `/voir/categorie/index-1` ou `/voir/categorie/index+1`.  
   La touche `ESC` ramène à la galerie de la catégorie.

#### **Bonus UX : Retour à la position du scroll**
La page galerie utilise `sessionStorage` côté client. 
Au clic sur une photo : `sauver_position_scroll()` mémorise `window.scrollY`. 
Au retour sur la galerie : le JS remet le scroll à la bonne position. Pas de rechargement de la page d’accueil.

---

### 4. Le rôle de `SimpleHTTPRequestHandler`

Le serveur hérite de la classe `SimpleHTTPRequestHandler` :

```
class GaleriePhotosHandler(SimpleHTTPRequestHandler):
```

La méthode `do_GET()` intercepte uniquement les URL spécifiques à l'application :
- `/` → `afficher_categories()`
- `/categorie/...` → `afficher_galerie_categorie()`
- `/voir/... `→ `afficher_photo_navigation()`
  
Toutes les autres requêtes sont transmises à la classe parente :

```
super().do_GET()
```
C'est cette méthode qui se charge automatiquement de servir les fichiers présents dans le répertoire partagé.  

Par exemple :

```
| Requête                                  | Traitement                   |
| ---------------------------------------- | ---------------------------- |
| `/cerfs_et_biches/photo1.jpg`            | Envoi de la photo originale  |
| `/miniatures/cerfs_et_biches/photo1.jpg` | Envoi de la miniature        |
| `/document.pdf`                          | Envoi du document PDF        |
| `/archive.zip`                           | Envoi de l'archive           |
| fichier inexistant                       | Réponse HTTP `404 Not Found` |
```
Le projet repose donc sur une répartition simple des responsabilités :  

- les pages HTML dynamiques (catégories, galeries, visionneuse) sont générées par la classe
  `GaleriePhotosHandler` ;
- le transfert des fichiers (images, miniatures, PDF, vidéos, etc.) est assuré automatiquement par
  `SimpleHTTPRequestHandler`.
  
Cette séparation permet de bénéficier des fonctionnalités de la bibliothèque standard Python sans avoir à réécrire un serveur de fichiers complet.

### 5. Fonctionnalités

- **Catégories avec icônes** : Dictionnaire `ICONES` pour afficher 🦌 🦅 🦊 etc.
- **Compteur de photos** : Le nombre de fichiers par dossier est affiché sur la carte.
- **Miniatures à la demande** : Génération auto via `Pillow` si la miniature n’existe pas.
- **Navigation clavier** : `←` Précédent, `→` Suivant, `ESC` Retour galerie.
- **Ouverture original** : Bouton `🔍 Original` pour voir le fichier en pleine résolution dans un nouvel onglet.  
  Egalement un clic sur la photo ouvre le fichier original en pleine résolution dans un nouvel onglet, sans perte de qualité.
- **Serveur multi-thread** : `ThreadingHTTPServer` pour gérer plusieurs clients en même temps.

---

### 6. Création des miniatures

L'affichage direct de plusieurs centaines ou milliers de photos haute résolution serait très lent.  
Le serveur utilise donc un mécanisme de cache.  
Lorsqu'une galerie est affichée, le serveur vérifie pour chaque photo si une miniature existe déjà.   
Schématiquement :  

```
Photo originale
      │
      ▼
La miniature existe ?
      │
  ┌───┴────┐
  │        │
 Oui      Non
  │        │
  ▼        ▼
Utilisation  Création avec Pillow
immédiate        │
                 ▼
         Enregistrement sur le disque
                 │
                 ▼
        Affichage de la miniature
```

La fonction responsable est :

```
creer_miniature(categorie, nom_fichier)
```
1. Son fonctionnement est le suivant :
2. Création du dossier `miniatures/nom_categorie` si nécessaire.
3. Vérification de l'existence de la miniature.
4. Si elle existe déjà, aucune opération n'est effectuée.
5. Sinon, la photo originale est ouverte avec **Pillow**.
6. Une miniature de **240 × 240 pixels maximum** est créée.
7. La miniature est enregistrée sur le disque puis sera réutilisée lors des prochains affichages.
   
Une miniature n'est donc créée **qu'une seule fois**.  

Les affichages suivants sont beaucoup plus rapides car le serveur lit directement les miniatures déjà présentes.

---

### Pourquoi utiliser thumbnail() ?

La méthode :
```
img.thumbnail((240, 240))
```
ne force jamais l'image à mesurer exactement **240 × 240**.  

Elle réduit simplement la photo pour que :  

- la largeur soit inférieure ou égale à 240 pixels ;
- la hauteur soit inférieure ou égale à 240 pixels ;
  
tout en conservant les proportions de l'image.  

Ainsi, aucune photo n'est déformée.  

---

### Un véritable cache disque

- Le dossier `miniatures` constitue un **cache**.
- Le serveur ne recalcule jamais une miniature déjà présente.
- Il se contente de la relire directement sur le disque.
- La création d'une miniature n'a donc lieu qu'une seule fois, lors du premier affichage de la photo.

---

### 7. Architecture générale

Le projet repose sur une idée simple : **chaque composant a une responsabilité unique**.

```
                Navigateur Web
                       │
                  Requête GET
                       │
                       ▼
                  do_GET()
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
Catégories       Galerie        Visionneuse
        │              │              │
        └──────────────┼──────────────┘
                       ▼
             Système de fichiers
             Photos + Miniatures
```
Cette séparation rend le code facile à comprendre, à maintenir et à faire évoluer.

--- 

### 8. Lancement

```
pip install Pillow
python3 serveur_galerie.py
```
---

### Remerciements

Ce projet a été conçu et développé par Philippe86220.
Les échanges techniques, les explications sur le fonctionnement du serveur, les réflexions sur l'architecture ainsi que la relecture du code ont été réalisés avec l'aide de ChatGPT (OpenAI).
