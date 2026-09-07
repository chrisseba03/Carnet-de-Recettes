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

# Normalisation avancée du texte (suppression des accents, majuscules et caractères spéciaux)
def normaliser_texte(texte):
    if not texte:
        return ""
    # Remplacement des ligatures
    texte = texte.replace("œ", "oe").replace("Œ", "oe").replace("æ", "ae").replace("Æ", "ae")
    # Décomposition des caractères accentués (NFD)
    texte = unicodedata.normalize('NFD', texte)
    # Suppression des diacritiques (accents)
    texte = "".join(c for c in texte if unicodedata.category(c) != 'Mn')
    texte = texte.lower()
    # Conservation des lettres et chiffres uniquement
    texte = re.sub(r'[^a-z0-9]', '', texte)
    return texte

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

categories_liste = ["Entrées", "Plats", "Desserts", "Pains & Pâtisseries", "Autres"]

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
    nom_norm = normaliser_texte(f['name'])
    trouve = False
    for cat in categories_liste:
        cat_norm = normaliser_texte(cat)
        if f"[{cat_norm}]" in nom_norm or cat_norm in nom_norm[:len(cat_norm)+2]:
            stats_cat[cat] += 1
            trouve = True
            break
    if not trouve:
        stats_cat["Autres"] += 1

for cat, count in stats_cat.items():
    if count > 0:
        st.sidebar.text(f"• {cat} : {count}")

# --- AFFICHAGE PRINCIPAL ---
st.markdown("---")
recherche = st.text_input("🔍 **Rechercher une recette par mot-clé**", placeholder="Tapez ici (ex: pate, crepe, gateau, poulet...)")
st.markdown("---")

if not fichiers_pdf:
    st.info("Aucune recette au format PDF trouvée sur votre Google Drive.")
else:
    terme_recherche_clean = normaliser_texte(recherche)
    fichiers_filtrer = []
    
    for f in fichiers_pdf:
        nom = f['name']
        file_id = f['id']
        nom_norm = normaliser_texte(nom)

        cat_du_fichier = "Autres"
        for cat in categories_liste:
            cat_norm = normaliser_texte(cat)
            if f"[{cat_norm}]" in nom_norm or cat_norm in nom_norm[:len(cat_norm)+2]:
                cat_du_fichier = cat
                break
                
        if categorie_filtre != "Toutes" and cat_du_fichier != categorie_filtre:
            continue
            
        nom_affiche = nom.replace('.pdf', '').replace('.PDF', '')
        for cat in categories_liste:
            pattern = re.compile(re.escape(f"[{cat}]"), re.IGNORECASE)
            nom_affiche = pattern.sub("", nom_affiche)
            pattern_acc = re.compile(re.escape(f"[{unicodedata.normalize('NFD', cat)}]"), re.IGNORECASE)
            nom_affiche = pattern_acc.sub("", nom_affiche)
            
        nom_affiche = nom_affiche.replace("[Entrées]", "").replace("[ENTREES]", "").replace("[entrées]", "").strip()
        nom_affiche = nom_affiche.replace('_', ' ').strip()
        
        # Recherche tolérante : comparaison entre le mot nettoyé et le titre nettoyé
        nom_clean = normaliser_texte(nom_affiche)
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
            
            if st.button("👁️ Afficher la recette", key=f"view_{file_id}"):
                with st.spinner("Chargement..."):
                    res = requests.get(download_url, headers=headers)
                    if res.status_code == 200:
                        try:
                            pdf_file = pdfium.PdfDocument(res.content)
                            for page_index in range(len(pdf_file)):
                                image = pdf_file[page_index].render(scale=2).to_pil()
                                st.image(image, use_container_width=True)
                        except Exception:
                            st.error("Impossible d'afficher l'aperçu du PDF.")

                        st.markdown("---")
                        st.download_button(
                            label="💾 Télécharger le fichier PDF",
                            data=res.content,
                            file_name=nom,
                            mime="application/pdf",
                            key=f"dl_{file_id}"
                        )
                    else:
                        st.error("Erreur de récupération.")

    if nb_resultats == 0:
        st.warning("Aucune recette ne correspond à votre sélection.")
