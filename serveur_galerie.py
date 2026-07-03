from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import os
from PIL import Image

DOSSIER_PHOTOS = "/home/philippe86220/Images/Photos"
PORT = 9000

DOSSIER_MINIATURES = os.path.join(DOSSIER_PHOTOS, "miniatures")
TAILLE_MINIATURE = (240, 240)
EXTENSIONS_IMAGES = (".jpg", ".jpeg", ".png")

ICONES = {
            "cerfs_et_biches": "🦌",
            "chevreuils": "🦌",
            "renards": "🦊",
            "lievres": "🐇",
            "lapins": "🐇",
            "blaireaux": "🦡",
            "sangliers": "🐗",
            "oiseaux": "🦅",
            "rapaces": "🦅",
            "papillons": "🦋",
            "libellules": "🪰",
            "reptiles": "🐍",
            "macro": "🐞",
            "amphibiens": "🐸",
            "paysages": "🌄",
        }


def lister_photos_categorie(categorie):
    dossier = os.path.join(DOSSIER_PHOTOS, categorie)

    return sorted([
        f for f in os.listdir(dossier)
        if os.path.isfile(os.path.join(dossier, f))
        and f.lower().endswith(EXTENSIONS_IMAGES)
    ])


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


class GaleriePhotosHandler(SimpleHTTPRequestHandler):

    def do_GET(self):

        if self.path in (
            "/favicon.ico",
            "/apple-touch-icon.png",
            "/apple-touch-icon-precomposed.png",
        ):
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

    def afficher_categories(self):
        categories = [
            d for d in os.listdir(DOSSIER_PHOTOS)
            if os.path.isdir(os.path.join(DOSSIER_PHOTOS, d))
            and d != "miniatures"
            and d != "Vidéos animalières"
        ]

        categories.sort()

        

        liens = ""

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

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Photothèque Animalière</title>

<style>
body {{
    margin: 0;
    font-family: Arial, sans-serif;
    background: #1b1b1b;
    color: white;
}}

header {{
    text-align: center;
    padding: 40px 20px;
    background: #2d3b2d;
}}

header h1 {{
    margin: 0;
    font-size: 42px;
}}

header p {{
    color: #cfcfcf;
    font-size: 18px;
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 20px;
    padding: 40px;
}}

.categorie {{
    background: #2d2d2d;
    border-radius: 15px;
    padding: 25px;
    text-align: center;
    text-decoration: none;
    color: white;
    transition: 0.2s;
}}

.categorie:hover {{
    background: #4b6b4b;
    transform: translateY(-4px);
}}

.icone {{
    font-size: 48px;
}}

.nom {{
    margin-top: 15px;
    font-size: 22px;
    font-weight: bold;
}}

.nb {{
    margin-top: 8px;
    color: #bbbbbb;
}}

footer {{
    text-align: center;
    padding: 25px;
    color: #888;
    font-size: 14px;
}}
</style>
</head>

<body>

<header>
<h1>📷 Photothèque Animalière</h1>
<p>Bienvenue dans la galerie de Philippe</p>
</header>

<div class="grid">
{liens}
</div>

<footer>
{len(categories)} catégories
</footer>

</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def afficher_galerie_categorie(self):
        categorie = self.path.split("/categorie/")[1]
        categorie = os.path.basename(categorie)

        dossier = os.path.join(DOSSIER_PHOTOS, categorie)

        if not os.path.isdir(dossier):
            self.send_error(404)
            return

        fichiers = lister_photos_categorie(categorie)
        nb = len(fichiers)

        blocs = ""

        for i, f in enumerate(fichiers):
            creer_miniature(categorie, f)

            blocs += f"""
            <a href="/voir/{categorie}/{i}" onclick="sauver_position_scroll()">
                <img src="/miniatures/{categorie}/{f}" loading="lazy" alt="{f}">
            </a>
            """

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{categorie} - {nb} photos</title>

<style>
body {{
    font-family: Arial, sans-serif;
    background: #111;
    color: white;
    padding: 20px;
    margin: 0;
}}

.topbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    background: #1a1a1a;
    border-bottom: 1px solid #333;
    position: sticky;
    top: 0;
    margin: -20px -20px 20px -20px;
}}

.btn-home {{
    text-decoration: none;
    color: #eee;
    background: #333;
    padding: 10px 18px;
    border-radius: 8px;
    font-weight: bold;
}}

.btn-home:hover {{
    background: #555;
}}

.galerie {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
}}

img {{
    width: 220px;
    height: 160px;
    object-fit: cover;
    border-radius: 8px;
}}

img:hover {{
    opacity: 0.8;
}}
</style>
</head>

<body>

<div class="topbar">
    <a href="/" class="btn-home">🏠 Accueil</a>
    <div>{categorie.replace("_", " ").title()} - {nb} photos</div>
    <div style="width: 100px;"></div>
</div>

<div class="galerie">
{blocs}
</div>

<script>
function sauver_position_scroll() {{
    sessionStorage.setItem("scroll_{categorie}", window.scrollY);
}}

window.addEventListener("load", function() {{
    let position = sessionStorage.getItem("scroll_{categorie}");
    if (position !== null) {{
        window.scrollTo(0, parseInt(position));
    }}
}});
</script>

</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def afficher_photo_navigation(self):
        morceaux = self.path.split("/")

        if len(morceaux) != 4:
            self.send_error(404)
            return

        categorie = os.path.basename(morceaux[2])

        try:
            index = int(morceaux[3])
        except ValueError:
            self.send_error(404)
            return

        dossier = os.path.join(DOSSIER_PHOTOS, categorie)

        if not os.path.isdir(dossier):
            self.send_error(404)
            return

        fichiers = lister_photos_categorie(categorie)

        if index < 0 or index >= len(fichiers):
            self.send_error(404)
            return

        fichier = fichiers[index]

        precedent = max(0, index - 1)
        suivant = min(len(fichiers) - 1, index + 1)

        url_original = f"/{categorie}/{fichier}"
        url_categorie = f"/categorie/{categorie}"

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{fichier}</title>

<style>
body {{
    margin: 0;
    background: #111;
    color: white;
    font-family: Arial, sans-serif;
    text-align: center;
}}

.topbar {{
    height: 50px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #1a1a1a;
    padding: 0 20px;
    box-sizing: border-box;
}}

.topbar a {{
    color: white;
    text-decoration: none;
    background: #333;
    padding: 8px 14px;
    border-radius: 8px;
}}

.topbar a:hover {{
    background: #555;
}}

.info {{
    color: #ccc;
    font-size: 14px;
}}

.photo {{
    height: calc(100vh - 50px);
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
}}

.photo a {{
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    width: 100%;
}}

.photo img {{
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
}}

</style>
</head>

<body>

<div class="topbar">
    <a href="{url_categorie}">⬅ Galerie</a>
    <div class="info">{index + 1} / {len(fichiers)} — {fichier}</div>
    <a href="{url_original}" target="_blank" rel="noopener">🔍 Original</a>
</div>

<div class="photo">
    <a href="{url_original}" target="_blank" rel="noopener">
        <img src="{url_original}" alt="{fichier}">
    </a>
</div>

<script>
document.addEventListener("keydown", function(event) {{
    if (event.key === "ArrowLeft") {{
        window.location.href = "/voir/{categorie}/{precedent}";
    }}

    if (event.key === "ArrowRight") {{
        window.location.href = "/voir/{categorie}/{suivant}";
    }}

    if (event.key === "Escape") {{
        window.location.href = "{url_categorie}";
    }}
}});
</script>

</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


os.chdir(DOSSIER_PHOTOS)

serveur = ThreadingHTTPServer(("0.0.0.0", PORT), GaleriePhotosHandler)

print("Serveur photos lance")
print(f"Dossier partage : {DOSSIER_PHOTOS}")
print(f"Adresse locale : http://localhost:{PORT}")
print(f"Depuis un autre appareil : http://IP_DU_NUC:{PORT}")

serveur.serve_forever()

