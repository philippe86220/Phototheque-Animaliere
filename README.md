# 🌿 Photothèque animalière - Serveur Web Léger

Une galerie photographique légère écrite en Python, sans framework, reposant uniquement sur ThreadingHTTPServer, SimpleHTTPRequestHandler et Pillow.

---

### 1. Principe de fonctionnement

L’application fonctionne sur un modèle Client / Serveur classique.

| Acteur | Rôle |
| --- | --- |
| **Le serveur** | Lit les dossiers de photos sur le disque, génère les pages HTML à la volée et sert les images. |
| **Le navigateur client** | Safari, Chrome, Firefox... Il affiche les pages HTML reçues et envoie une requête `GET` au serveur à chaque clic. |

Aucun JavaScript lourd côté client. Chaque changement de page = 1 nouveau `GET`.

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

---

### 3. Navigation : Comment le navigateur communique avec le serveur

Le cœur est la méthode `do_GET` du serveur. Elle analyse l’URL demandée par le navigateur.

#### **Étape 1 : Page d’accueil `/`**
1.  **Client Safari** : Vous tapez `http://IP_DU_SERVEUR:9000/`
2.  **Requête** : Safari envoie `GET /`
3.  **Serveur** : `do_GET` voit `self.path == "/"` -> Il appelle `afficher_categories()`
4.  **Réponse** : Le serveur renvoie du HTML avec une grille de cartes. Chaque carte est un lien : `<a href="/categorie/cerfs_et_biches">`

#### **Étape 2 : Galerie d’une catégorie `/categorie/nom`**
1.  **Client Safari** : Vous cliquez sur une carte "Cerfs et Biches"
2.  **Requête** : Safari fait automatiquement `GET /categorie/cerfs_et_biches`
3.  **Serveur** : `do_GET` voit `self.path.startswith("/categorie/")` -> Il appelle `afficher_galerie_categorie()`
4.  **Réponse** : Le serveur liste les fichiers `.jpg/.png`, crée les miniatures si besoin, et renvoie du HTML avec une grille d’images `<img src="/miniatures/...">`

#### **Étape 3 : Visionneuse `/voir/categorie/index`**
1.  **Client Safari** : vous cliquez sur une miniature
2.  **Requête** : Safari fait `GET /voir/cerfs_et_biches/3`
3.  **Serveur** : `do_GET` -> `afficher_photo_navigation()` 
4.  **Réponse** : HTML plein écran avec l’image originale. 
    Les flèches `←` `→` du clavier et les boutons génèrent un nouveau `GET` vers `/voir/categorie/index-1` ou `index+1`. 
    `ESC` renvoie vers `/categorie/nom`.

#### **Bonus UX : Retour à la position du scroll**
La page galerie utilise `sessionStorage` côté client. 
Au clic sur une photo : `sauver_position_scroll()` mémorise `window.scrollY`. 
Au retour sur la galerie : le JS remet le scroll à la bonne position. Pas de rechargement de la page d’accueil.

---

### 4. Fonctionnalités

- **Catégories avec icônes** : Dictionnaire `ICONES` pour afficher 🦌 🦅 🦊 etc.
- **Compteur de photos** : Le nombre de fichiers par dossier est affiché sur la carte.
- **Miniatures à la demande** : Génération auto via `Pillow` si la miniature n’existe pas.
- **Navigation clavier** : `←` Précédent, `→` Suivant, `ESC` Retour galerie.
- **Ouverture original** : Bouton `🔍 Original` pour voir le fichier en pleine résolution dans un nouvel onglet.
- **Serveur multi-thread** : `ThreadingHTTPServer` pour gérer plusieurs clients en même temps.

---

### 5. Création des miniatures

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
- Le temps de calcul n'est donc payé qu'une seule fois, lors du premier affichage de la photo.

---

### 6. Architecture générale

Le projet repose sur une idée simple : **chaque composant a une responsabilité unique**.

```
          Navigateur Web
                 │
                 ▼
             do_GET()
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
Catégories   Galerie   Visionneuse
        │        │        │
        └────────┼────────┘
                 ▼
      Photos et miniatures
           sur le disque
```
Cette séparation rend le code facile à comprendre, à maintenir et à faire évoluer.

--- 

### 7. Lancement

```bash
pip install Pillow
python3 serveur_galerie.py

---

### Remerciements

Ce projet a été conçu et développé par Philippe86220.
Les réflexions sur l'architecture, les explications techniques, la relecture du code ainsi qu'une partie de la conception ont été réalisées avec l'aide de ChatGPT (OpenAI).
Les choix d'implémentation et le code final restent sous la responsabilité de l'auteur.
