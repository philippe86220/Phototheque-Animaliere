
# Explication détaillée du serveur de galerie photos

Ce document explique, ligne par ligne et concept par concept, comment fonctionne ce script Python. C'est un **serveur web fait maison** qui affiche des photos animalières sous forme de galerie, sans dépendre de frameworks lourds comme Flask ou Django : tout repose sur la bibliothèque standard `http.server`.

---

## 1. Vue d'ensemble : que fait ce programme ?

Au lancement du script, il :
1. Démarre un **serveur HTTP** qui écoute sur le port `9000`.
2. Quand un navigateur se connecte, il génère du **HTML à la volée** (avec des chaînes de caractères Python) selon l'URL demandée.
3. Affiche trois types de pages :
   - la page d'accueil (liste des catégories) ;
   - la galerie d'une catégorie (miniatures) ;
   - la visionneuse plein écran d'une photo (navigation photo par photo).
4. Génère automatiquement des **miniatures** compressées pour que les galeries se chargent vite.

C'est en fait un mini "framework web" écrit à la main.

---

## 2. Les imports

```python
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import os
from PIL import Image
```

- **`ThreadingHTTPServer`** : une classe de la bibliothèque standard qui crée un serveur HTTP capable de traiter **plusieurs requêtes en même temps**, chacune dans son propre thread (fil d'exécution). Sans ça, si deux personnes chargent une page en même temps, la seconde devrait attendre que la première soit terminée.
- **`SimpleHTTPRequestHandler`** : une classe qui sait déjà servir des fichiers statiques (images, CSS, etc.) depuis un dossier. Ce code **hérite** de cette classe pour ajouter un comportement personnalisé (les pages HTML dynamiques), tout en gardant la capacité de servir les fichiers d'origine et les miniatures.
- **`os`** : pour manipuler les chemins de fichiers et lister les dossiers.
- **`PIL.Image`** (Pillow) : bibliothèque de traitement d'image, utilisée ici pour générer les miniatures.

---

## 3. Les constantes de configuration

```python
DOSSIER_PHOTOS = "/home/philippe86220/Images/Photos"
PORT = 9000

DOSSIER_MINIATURES = os.path.join(DOSSIER_PHOTOS, "miniatures")
TAILLE_MINIATURE = (240, 240)
EXTENSIONS_IMAGES = (".jpg", ".jpeg", ".png")
```

- `DOSSIER_PHOTOS` : le dossier racine contenant les catégories de photos (un sous-dossier par catégorie).
- `PORT` : le port réseau sur lequel le serveur écoute. `http://localhost:9000` correspondra à ce port.
- `DOSSIER_MINIATURES` : sous-dossier `miniatures/` créé à l'intérieur du dossier photos, qui contiendra les versions réduites des images.
- `TAILLE_MINIATURE` : dimension maximale (240×240 px) des miniatures générées.
- `EXTENSIONS_IMAGES` : extensions de fichiers considérées comme des images (le `.lower()` utilisé plus loin permet d'accepter aussi bien `.JPG` que `.jpg`).

Mettre ces valeurs en constantes en haut du fichier permet de tout modifier facilement à un seul endroit (bonne pratique).

---

## 4. Le dictionnaire `ICONES`

```python
ICONES = {
    "cerfs_et_biches": "🦌",
    "chevreuils": "🦌",
    ...
}
```

C'est une simple table de correspondance **nom de dossier → emoji**. Elle est utilisée plus tard pour afficher une icône visuelle sur chaque vignette de catégorie. Si une catégorie n'a pas d'entrée dans ce dictionnaire, une icône par défaut (`📁`) sera utilisée grâce à `ICONES.get(cat.lower(), "📁")`.

---

## 5. `lister_photos_categorie(categorie)`

```python
def lister_photos_categorie(categorie):
    dossier = os.path.join(DOSSIER_PHOTOS, categorie)

    return sorted([
        f for f in os.listdir(dossier)
        if os.path.isfile(os.path.join(dossier, f))
        and f.lower().endswith(EXTENSIONS_IMAGES)
    ])
```

Cette fonction retourne la **liste triée des noms de fichiers images** présents dans un sous-dossier donné.

- `os.listdir(dossier)` : liste tout le contenu du dossier (fichiers ET sous-dossiers).
- La **liste en compréhension** filtre pour ne garder que :
  - les éléments qui sont bien des fichiers (`os.path.isfile`, pour exclure les sous-dossiers) ;
  - dont l'extension correspond à une image (`.jpg`, `.jpeg`, `.png`).
- `sorted(...)` : trie la liste par ordre alphabétique, pour un affichage cohérent d'une exécution à l'autre.

Cette fonction est le "cœur" utilisé à la fois pour compter les photos d'une catégorie (page d'accueil), afficher la galerie, et naviguer photo par photo.

---

## 6. `creer_miniature(categorie, nom_fichier)`

```python
def creer_miniature(categorie, nom_fichier):
    dossier_mini_cat = os.path.join(DOSSIER_MINIATURES, categorie)
    os.makedirs(dossier_mini_cat, exist_ok=True)

    chemin_photo = os.path.join(DOSSIER_PHOTOS, categorie, nom_fichier)
    chemin_miniature = os.path.join(dossier_mini_cat, nom_fichier)

    if os.path.exists(chemin_miniature):
        return

    try:
        img = Image.open(chemin_photo)
        img.thumbnail(TAILLE_MINIATURE)
        img.save(chemin_miniature, "JPEG", quality=80)
    except Exception as e:
        print(f"Erreur miniature {nom_fichier} : {e}")
```

C'est la fonction qui génère les vignettes légères pour accélérer le chargement des galeries.

Étapes :
1. **Créer le dossier de destination** s'il n'existe pas (`os.makedirs(..., exist_ok=True)` ne lève pas d'erreur si le dossier existe déjà).
2. Construire les chemins complets : photo source et miniature de destination.
3. **Cache simple** : si la miniature existe déjà, la fonction s'arrête immédiatement (`return`) — on ne régénère pas ce qui a déjà été fait. C'est ce qui rend le site rapide après le premier chargement.
4. Sinon :
   - `Image.open(...)` ouvre l'image originale ;
   - `img.thumbnail(TAILLE_MINIATURE)` la redimensionne **en conservant les proportions**, sans dépasser 240×240 px ;
   - `img.save(..., "JPEG", quality=80)` sauvegarde en JPEG compressé à 80% de qualité (bon compromis poids/qualité visuelle).
5. Le `try/except` protège le serveur : si une image est corrompue ou illisible, l'erreur est juste affichée dans la console au lieu de faire planter tout le serveur.

---

## 7. La classe `GaleriePhotosHandler`

C'est la partie la plus importante : elle définit **comment le serveur répond à chaque requête HTTP**.

```python
class GaleriePhotosHandler(SimpleHTTPRequestHandler):
```

En héritant de `SimpleHTTPRequestHandler`, la classe récupère tout le comportement "serveur de fichiers statiques" (utile pour servir directement les images originales et les miniatures), et on peut **surcharger** (redéfinir) la méthode `do_GET` pour ajouter son propre routage.

### 7.1 `do_GET` : le routeur

```python
def do_GET(self):
    if self.path in ("/favicon.ico", ...):
        self.send_response(204)
        self.end_headers()
        return

    if self.path == "/":
        self.afficher_categories()
        return

    if self.path.startswith("/categorie/"):
        self.afficher_galerie_categorie()
        return

    if self.path.startswith("/voir/"):
        self.afficher_photo_navigation()
        return

    super().do_GET()
```

`do_GET` est appelée automatiquement chaque fois qu'un navigateur envoie une requête `GET`. C'est un **routeur** : selon la valeur de `self.path` (l'URL demandée), on dirige vers une méthode différente.

- Les requêtes vers `/favicon.ico` etc. (demandées automatiquement par les navigateurs) reçoivent une réponse **204 No Content** — on répond "il n'y a rien" pour éviter des erreurs 404 inutiles dans les logs.
- `/` → page d'accueil (liste des catégories).
- `/categorie/xxx` → galerie de miniatures de la catégorie `xxx`.
- `/voir/xxx/i` → visionneuse plein écran de la photo d'index `i` dans la catégorie `xxx`.
- **Sinon** (`super().do_GET()`) : on délègue au comportement d'origine de `SimpleHTTPRequestHandler`, qui sert simplement le fichier demandé depuis le disque (c'est comme ça que les images originales et les miniatures, ex. `/miniatures/renards/photo.jpg`, sont livrées au navigateur).

> **Point clé** : `os.chdir(DOSSIER_PHOTOS)` (voir plus bas) change le dossier de travail du programme vers `DOSSIER_PHOTOS`. C'est ce qui permet à `SimpleHTTPRequestHandler` de retrouver les fichiers demandés : il sert toujours les fichiers relativement au dossier courant.

### 7.2 `afficher_categories()` — la page d'accueil

Cette méthode construit la page listant toutes les catégories (dossiers) de photos.

```python
categories = [
    d for d in os.listdir(DOSSIER_PHOTOS)
    if os.path.isdir(os.path.join(DOSSIER_PHOTOS, d))
    and d != "miniatures"
    and d != "Vidéos animalières"
]
categories.sort()
```

- Liste tous les sous-**dossiers** de `DOSSIER_PHOTOS` (donc pas les fichiers isolés).
- Exclut le dossier technique `miniatures` et le dossier `Vidéos animalières` (non pertinent ici).
- Trie alphabétiquement.

Ensuite, une boucle construit une chaîne HTML (`liens`) contenant une "carte" cliquable par catégorie :

```python
for cat in categories:
    icone = ICONES.get(cat.lower(), "📁")
    fichiers = lister_photos_categorie(cat)
    nb = len(fichiers)

    liens += f"""
    <a class="categorie" href="/categorie/{cat}">
        <div class="icone">{icone}</div>
        <div class="nom">{cat.replace("_", " ").title()}</div>
        <div class="nb">{nb} photos</div>
    </a>
    """
```

- On récupère l'icône emoji correspondante.
- On compte le nombre de photos via la fonction vue plus haut.
- On formate joliment le nom (`cat.replace("_", " ").title()` remplace les underscores par des espaces et met une majuscule à chaque mot : `cerfs_et_biches` → `Cerfs Et Biches`).
- Chaque carte est un lien `<a>` vers `/categorie/<nom>`.

Le reste de la méthode assemble une page HTML complète (avec CSS intégré dans une balise `<style>`) via un **f-string multi-lignes**, puis l'envoie au navigateur :

```python
self.send_response(200)
self.send_header("Content-type", "text/html; charset=utf-8")
self.end_headers()
self.wfile.write(html.encode("utf-8"))
```

C'est la séquence classique d'une réponse HTTP manuelle :
1. `send_response(200)` : code de statut HTTP "OK".
2. `send_header(...)` : on précise le type de contenu (HTML, encodage UTF-8 pour bien afficher les accents).
3. `end_headers()` : signale la fin des en-têtes HTTP.
4. `self.wfile.write(...)` : écrit le corps de la réponse (le HTML, converti en octets avec `.encode("utf-8")`) directement dans le flux réseau vers le navigateur.

### 7.3 `afficher_galerie_categorie()` — la galerie d'une catégorie

```python
categorie = self.path.split("/categorie/")[1]
categorie = os.path.basename(categorie)
```

- On extrait le nom de la catégorie depuis l'URL, ex. `/categorie/renards` → `renards`.
- `os.path.basename(categorie)` est une **précaution de sécurité** : cela empêche quelqu'un d'injecter un chemin du type `/categorie/../../etc/passwd` pour sortir du dossier photos (on ne garde que le dernier segment du chemin).

```python
if not os.path.isdir(dossier):
    self.send_error(404)
    return
```
Si le dossier n'existe pas, on renvoie une erreur HTTP 404 (page non trouvée).

Ensuite, pour chaque photo de la catégorie :
```python
for i, f in enumerate(fichiers):
    creer_miniature(categorie, f)

    blocs += f"""
    <a href="/voir/{categorie}/{i}" onclick="sauver_position_scroll()">
        <img src="/miniatures/{categorie}/{f}" loading="lazy" alt="{f}">
    </a>
    """
```

- `enumerate(fichiers)` donne à la fois l'**index** `i` (0, 1, 2, ...) et le **nom de fichier** `f`. L'index sert à construire les liens de navigation `/voir/categorie/i`.
- `creer_miniature(...)` est appelée pour s'assurer que la vignette existe (elle ne la régénère pas si elle est déjà là, cf. section 6).
- Chaque photo devient un lien cliquable menant vers la visionneuse (`/voir/...`), affichant la miniature (`loading="lazy"` : le navigateur ne charge l'image que quand elle devient visible à l'écran, ce qui accélère beaucoup les galeries longues).
- `onclick="sauver_position_scroll()"` : avant de quitter la page, un peu de JavaScript sauvegarde la position de défilement (voir plus bas), pour qu'au retour depuis la visionneuse, l'utilisateur retrouve sa place dans la galerie au lieu de remonter en haut.

Un peu de JavaScript est inclus dans la page :
```javascript
function sauver_position_scroll() {
    sessionStorage.setItem("scroll_{categorie}", window.scrollY);
}

window.addEventListener("load", function() {
    let position = sessionStorage.getItem("scroll_{categorie}");
    if (position !== null) {
        window.scrollTo(0, parseInt(position));
    }
});
```
- `sessionStorage` : un espace de stockage propre au navigateur, qui persiste pendant la session de navigation (mais pas entre deux visites différentes).
- Au clic sur une photo, on enregistre la position verticale du scroll (`window.scrollY`).
- Au chargement de la page (`load`), on relit cette position et on y repositionne la page (`window.scrollTo`).

C'est une astuce d'ergonomie très utile : sans elle, revenir à la galerie après avoir vu une photo  ramènerait tout en haut de la page.

### 7.4 `afficher_photo_navigation()` — la visionneuse plein écran

```python
morceaux = self.path.split("/")
if len(morceaux) != 4:
    self.send_error(404)
    return

categorie = os.path.basename(morceaux[2])
index = int(morceaux[3])
```

L'URL `/voir/renards/3` est découpée par `/` en `["", "voir", "renards", "3"]` — 4 morceaux. On récupère la catégorie (`morceaux[2]`) et l'index (`morceaux[3]`, converti en entier). Un `try/except ValueError` protège contre un index non numérique dans l'URL.

```python
if index < 0 or index >= len(fichiers):
    self.send_error(404)
    return
```
Vérifie que l'index demandé existe bel et bien dans la liste des photos (sécurité contre les URL invalides).

```python
precedent = max(0, index - 1)
suivant = min(len(fichiers) - 1, index + 1)
```
Calcule les index de la photo précédente et suivante, **en les bornant** pour ne jamais sortir de la liste (`max`/`min` évitent les index négatifs ou hors limites).

La page générée affiche :
- une barre du haut avec un lien retour vers la galerie, le numéro de la photo (`index+1 / total`), et un lien vers l'image originale en pleine résolution (`target="_blank"` : ouverture dans un nouvel onglet) ;
- la photo elle-même, affichée en grand (CSS `object-fit: contain` pour qu'elle s'adapte à l'écran sans être déformée) ;
- du JavaScript pour la **navigation au clavier** :

```javascript
document.addEventListener("keydown", function(event) {
    if (event.key === "ArrowLeft") {
        window.location.href = "/voir/{categorie}/{precedent}";
    }
    if (event.key === "ArrowRight") {
        window.location.href = "/voir/{categorie}/{suivant}";
    }
    if (event.key === "Escape") {
        window.location.href = "{url_categorie}";
    }
});
```
Flèche gauche/droite pour naviguer entre les photos, `Échap` pour revenir à la galerie — une navigation façon visionneuse d'image classique.

---

## 8. Le démarrage du serveur

```python
os.chdir(DOSSIER_PHOTOS)

serveur = ThreadingHTTPServer(("0.0.0.0", PORT), GaleriePhotosHandler)

print("Serveur photos lance")
...
serveur.serve_forever()
```

- `os.chdir(DOSSIER_PHOTOS)` : change le **dossier de travail courant** du script vers le dossier photos. C'est essentiel car `SimpleHTTPRequestHandler` (utilisé pour servir les fichiers statiques, comme les images et les miniatures) sert toujours des fichiers **relatifs au dossier courant**.
- `ThreadingHTTPServer(("0.0.0.0", PORT), GaleriePhotosHandler)` :
  - `"0.0.0.0"` signifie "écouter sur toutes les interfaces réseau", pas seulement `localhost` — c'est ce qui permet d'accéder au serveur depuis un autre appareil du réseau local (téléphone, autre PC) via l'adresse IP de la machine.
  - `PORT` : le port 9000 défini plus haut.
  - `GaleriePhotosHandler` : la classe qui traitera chaque requête (celle qu'on a détaillée ci-dessus).
- `serveur.serve_forever()` : lance une **boucle infinie** qui écoute et traite les connexions entrantes, jusqu'à ce qu'on arrête le programme (`Ctrl+C`).

---

## 9. Concepts transversaux à retenir

- **Serveur HTTP "from scratch"** : pas de framework, juste `http.server` de la bibliothèque standard. Chaque réponse est construite manuellement (code de statut, en-têtes, corps).
- **Routage manuel** : `do_GET` joue le rôle qu'un framework comme Flask assurerait avec des décorateurs `@app.route(...)`.
- **Génération HTML via f-strings** : le HTML est simplement une grande chaîne de caractères Python, avec des `{...}` remplacés dynamiquement. C'est simple mais peu sécurisé pour de grandes applications (pas d'échappement automatique), acceptable ici pour un usage personnel avec des noms de fichiers maîtrisés.
- **Cache de miniatures** : générer une image redimensionnée est coûteux (CPU) ; on ne le fait qu'une fois par photo, puis on réutilise le fichier existant.
- **Threading** : `ThreadingHTTPServer` permet de gérer plusieurs visiteurs/requêtes simultanément sans blocage.
- **Sécurité basique** : `os.path.basename()` empêche la traversée de répertoires (`path traversal`) via des URL malicieuses.
- **JavaScript côté client** : sert uniquement au confort (mémoriser le scroll, navigation clavier) — le "cœur" de l'application reste côté serveur en Python.

---

