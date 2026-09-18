import streamlit as st
import io
import requests
import unicodedata
import re
import json
import pypdfium2 as pdfium
from google.oauth2 import service_account
from googleapiclient.discovery import build
import google.auth.transport.requests

st.set_page_config(page_title="Nos Recettes de Cuisine", page_icon="👨‍🍳", layout="wide")
st.title("👨‍🍳 Le Carnet de Recettes de la Maison")

# Normalisation du texte pour la comparaison (sans accent, minuscules)
def normaliser_texte(texte):
    if not texte:
        return ""
    texte = texte.replace("œ", "oe").replace("Œ", "oe").replace("æ", "ae").replace("Æ", "ae")
    texte = unicodedata.normalize('NFD', texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != 'Mn')
    texte = texte.lower()
    return texte

# Nettoyage strict pour la recherche par mot-clé (lettres et chiffres uniquement)
def normaliser_mot_cle(texte):
    texte = normaliser_texte(texte)
    return re.sub(r'[^a-z0-9]', '', texte)

# Dictionnaire de correspondance intelligente (Synonymes, accents, pluriels harmonisés)
MAPPING_CATEGORIES = {
    "Entrées": ["entree", "entrees"],
    "Charcuteries": ["charcuterie", "charcuteries", "salaison", "salaisons"],
    "Sauces": ["sauce", "sauces", "vinaigrette", "vinaigrettes", "marinade", "marinades", "condiment", "condiments"],
    "Plats": ["plat", "plats"],
    "Desserts": ["dessert", "desserts", "douceur", "douceurs"],
    "Pains & Pâtisseries": ["pain", "pains", "patisserie", "patisseries", "boulangerie", "brioche", "brioches"],
    "Vins & Spiritueux": ["vin", "vins", "spiritueux", "boisson", "boissons", "apero", "aperitif", "aperitifs", "cave", "cocktail", "cocktails"]
}

def identifier_categories_balise(balise):
    clean = normaliser_mot_cle(balise)
    cats_trouvees = []
    
    for cat_officielle, mots_cles in MAPPING_CATEGORIES.items():
        for mot in mots_cles:
            if clean == mot or clean == mot + "s" or mot in clean:
                cats_trouvees.append(cat_officielle)
                break
                
    return cats_trouvees

# Connexion Google Drive
@st.cache_resource
def get_drive_service():
    scopes = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    session = requests.Session()
    auth_request = google.auth.transport.requests.Request(session=session)
    creds.refresh(auth_request)
    return build('drive', 'v3', credentials=creds), creds

try:
    drive_service, creds = get_drive_service()
    FOLDER_ID = st.secrets["FOLDER_ID"]
except Exception as e:
    st.error("Erreur de connexion à Google Drive. Vérifiez la configuration dans les Secrets.")
    st.stop()

# --- RECUPERATION DES RECETTES ---
@st.cache_data(ttl=600)
def get_all_recipes():
    fichiers = []
    page_token = None
    query = f"'{FOLDER_ID}' in parents and trashed = false and mimeType = 'application/pdf'"
    
    while True:
        response = drive_service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageSize=1000,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            pageToken=page_token
        ).execute()
        
        fichiers.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        
        if page_token is None:
            break
            
    return fichiers

try:
    fichiers_bruts = get_all_recipes()
except Exception:
    st.error("Petite baisse de réseau avec Google Drive. Cliquez sur 'Rafraîchir la liste'.")
    st.stop()

fichiers_pdf = [f for f in fichiers_bruts if f['name'].lower().endswith('.pdf')]
total_recettes = len(fichiers_pdf)

# Liste officielle affichée dans le menu de sélection (parfaitement alignée avec le mapping)
categories_liste = ["Entrées", "Charcuteries", "Sauces", "Plats", "Desserts", "Pains & Pâtisseries", "Vins & Spiritueux", "Autres"]

# --- BARRE LATÉRALE : OPTIONS ---
st.sidebar.header("⚙️ Options")
categorie_filtre = st.sidebar.selectbox("Filtrer par catégorie", ["Toutes"] + categories_liste)

if st.sidebar.button("🔄 Rafraîchir la liste"):
    st.cache_data.clear()
    st.rerun()

# --- BARRE LATÉRALE : RÉPARTITION ---
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Répartition")
stats_cat = {cat: 0 for cat in categories_liste}

for f in fichiers_pdf:
    nom_f = f['name']
    balises = re.findall(r'\[(.*?)\]', nom_f)
    cats_du_fichier = set()
    
    for b in balises:
        for c in identifier_categories_balise(b):
            cats_du_fichier.add(c)
            
    if not cats_du_fichier:
        stats_cat["Autres"] += 1
    else:
        for c in cats_du_fichier:
            stats_cat[c] += 1

for cat, count in stats_cat.items():
    if count > 0:
        st.sidebar.text(f"• {cat} : {count}")

# --- AFFICHAGE PRINCIPAL ---
st.markdown("---")
recherche = st.text_input("🔍 **Rechercher une recette par mot-clé**", placeholder="Tapez ici (ex: pate, crepe, gateau, vin, sauce, merguez...)")
st.markdown("---")

if not fichiers_pdf:
    st.info("Aucune recette au format PDF trouvée sur votre Google Drive.")
else:
    terme_recherche_clean = normaliser_mot_cle(recherche)
    fichiers_filtrer = []
    
    for f in fichiers_pdf:
        nom = f['name']
        file_id = f['id']

        # Identification de toutes les catégories associées au fichier
        balises = re.findall(r'\[(.*?)\]', nom)
        categories_du_fichier = set()
        
        for b in balises:
            for c in identifier_categories_balise(b):
                categories_du_fichier.add(c)
                
        if not categories_du_fichier:
            categories_du_fichier.add("Autres")
                
        # Filtre sur la catégorie sélectionnée
        if categorie_filtre != "Toutes" and categorie_filtre not in categories_du_fichier:
            continue
            
        # Nettoyage propre du titre pour l'affichage principal
        nom_affiche = nom.replace('.pdf', '').replace('.PDF', '')
        nom_affiche = re.sub(r'\[.*?\]', '', nom_affiche).strip()
        nom_affiche = nom_affiche.replace('_', ' ').strip()
        
        # Filtre de recherche tolérante par mot-clé
        nom_clean = normaliser_mot_cle(nom_affiche)
        if terme_recherche_clean and (terme_recherche_clean not in nom_clean):
            continue
            
        fichiers_filtrer.append((f, nom_affiche))

    fichiers_filtrer = sorted(fichiers_filtrer, key=lambda x: x[1].lower())
    nb_resultats = len(fichiers_filtrer)

    if categorie_filtre != "Toutes" or terme_recherche_clean:
        st.subheader(f"📚 Recettes correspondantes ({nb_resultats} / {total_recettes})")
    else:
        st.subheader(f"📚 Toutes vos recettes ({total_recettes})")

    for f, nom_affiche in fichiers_filtrer:
        nom = f['name']
        file_id = f['id']

        with st.expander(f"📖 {nom_affiche}"):
            download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
            headers = {"Authorization": f"Bearer {creds.token}"}

            col_btn1, col_btn2 = st.columns([1, 1])

            with col_btn1:
                voir_recette = st.button("👁️ Afficher la recette", key=f"view_{file_id}")

            with col_btn2:
                def telecharger_fichier(url, h):
                    r = requests.get(url, headers=h)
                    return r.content if r.status_code == 200 else None

                st.download_button(
                    label="💾 Télécharger le PDF",
                    data=telecharger_fichier(download_url, headers),
                    file_name=nom,
                    mime="application/pdf",
                    key=f"dl_{file_id}"
                )

            if voir_recette:
                with st.spinner("Chargement de l'aperçu..."):
                    res = requests.get(download_url, headers=headers)
                    if res.status_code == 200:
                        try:
                            pdf_file = pdfium.PdfDocument(res.content)
                            for page_index in range(len(pdf_file)):
                                image = pdf_file[page_index].render(scale=2).to_pil()
                                st.image(image, use_container_width=True)
                        except Exception:
                            st.error("Impossible d'afficher l'aperçu du PDF.")
                    else:
                        st.error("Erreur de récupération.")

    if nb_resultats == 0:
        st.warning("Aucune recette ne correspond à votre sélection.")
