import streamlit as st
import io
import requests
import unicodedata
import re
import pypdfium2 as pdfium
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import google.auth.transport.requests

st.set_page_config(page_title="Nos Recettes de Cuisine", page_icon="🍳", layout="wide")
st.title("🍳 Le Carnet de Recettes de la Maison")

# Fonction pour normaliser le texte (supprime les accents, gère œ/æ et casse)
def normaliser_texte(texte):
    if not texte:
        return ""
    # Remplace les ligatures courantes
    texte = texte.replace("œ", "oe").replace("Œ", "oe").replace("æ", "ae").replace("Æ", "ae")
    # Décompose les caractères accentués
    texte = unicodedata.normalize('NFD', texte)
    # Supprime tous les diacritiques (accents)
    texte = "".join(c for c in texte if unicodedata.category(c) != 'Mn')
    # Passe en minuscules et ne garde que les lettres et chiffres
    texte = texte.lower()
    texte = re.sub(r'[^a-z0-9]', '', texte)
    return texte

# Client d'authentification
@st.cache_resource
def get_drive_service():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=['https://www.googleapis.com/auth/drive']
    )
    session = requests.Session()
    auth_request = google.auth.transport.requests.Request(session=session)
    creds.refresh(auth_request)
    return build('drive', 'v3', credentials=creds), creds

try:
    drive_service, creds = get_drive_service()
    FOLDER_ID = st.secrets["FOLDER_ID"]
except Exception as e:
    st.error("Erreur de connexion à Google Drive. Vérifiez la configuration des Secrets.")
    st.stop()

# --- BARRE LATÉRALE : AJOUT & FILTRES ---
st.sidebar.header("➕ Ajouter une recette")
nouveau_pdf = st.sidebar.file_uploader("Importer un fichier PDF", type=["pdf"])
titre_recette = st.sidebar.text_input("Nom de la recette")
cat_recette = st.sidebar.selectbox("Catégorie", ["Entrées", "Plats", "Desserts", "Pains & Pâtisseries", "Autres"])

if st.sidebar.button("Sauvegarder sur Google Drive"):
    if nouveau_pdf and titre_recette:
        nom_fichier = f"[{cat_recette}] {titre_recette.strip()}.pdf"
        file_metadata = {
            'name': nom_fichier,
            'parents': [FOLDER_ID]
        }
        media = MediaIoBaseUpload(io.BytesIO(nouveau_pdf.read()), mimetype='application/pdf')
        
        with st.spinner("Envoi vers Google Drive en cours..."):
            drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        
        st.sidebar.success(f"Recette '{titre_recette}' sauvegardée avec succès !")
        st.cache_data.clear()
        st.rerun()
    else:
        st.sidebar.error("Veuillez renseigner le titre et choisir un fichier PDF.")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Options")
categorie_filtre = st.sidebar.selectbox("Filtrer par catégorie", ["Toutes", "Entrées", "Plats", "Desserts", "Pains & Pâtisseries", "Autres"])

if st.sidebar.button("🔄 Rafraîchir la liste"):
    st.cache_data.clear()
    st.rerun()

# --- RECHERCHE EN HAUT DE LA PAGE PRINCIPALE ---
st.markdown("---")
recherche = st.text_input("🔍 **Rechercher une recette par mot-clé**", placeholder="Tapez ici (ex: crepe, gateau, oeuf, poulet...)")
st.markdown("---")

st.subheader("📚 Vos Recettes Sauvegardées")

@st.cache_data(ttl=600)
def get_all_recipes():
    fichiers = []
    page_token = None
    
    # Requête pour ne récupérer que les fichiers PDF non mis à la corbeille
    query = f"'{FOLDER_ID}' in parents and trashed = false and mimeType = 'application/pdf'"
    
    while True:
        response = drive_service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageSize=1000,
            pageToken=page_token
        ).execute()
        
        fichiers.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        
        if page_token is None:
            break
            
    return fichiers

try:
    fichiers = get_all_recipes()
except Exception as err:
    st.error("Petite baisse de réseau avec Google Drive. Cliquez sur 'Rafraîchir la liste' dans le menu de gauche.")
    st.stop()

# Sécurité supplémentaire : filtrer par l'extension .pdf
fichiers_pdf = [f for f in fichiers if f['name'].lower().endswith('.pdf')]

if not fichiers_pdf:
    st.info("Aucune recette au format PDF trouvée sur votre Google Drive. Ajoutez votre première recette depuis le menu à gauche !")
else:
    # Tri alphabétique
    fichiers_pdf = sorted(fichiers_pdf, key=lambda x: x['name'].lower())
    recettes_affichees = 0
    
    # Normalisation de la recherche de l'utilisateur
    terme_recherche_clean = normaliser_texte(recherche)
    
    for f in fichiers_pdf:
        nom = f['name']
        file_id = f['id']
        
        # 1. Filtre par catégorie
        if categorie_filtre != "Toutes" and f"[{categorie_filtre}]" not in nom:
            continue
            
        # Nom propre lisible pour l'affichage (ex: "Tarte aux pommes")
        nom_affiche = nom.replace('.pdf', '').replace('.PDF', '')
        for cat in ["Entrées", "Plats", "Desserts", "Pains & Pâtisseries", "Autres"]:
            nom_affiche = nom_affiche.replace(f"[{cat}] ", "").replace(f"[{cat}]", "")
        
        # Normalisation du nom de la recette
        nom_clean = normaliser_texte(nom_affiche)
        nom_fichier_clean = normaliser_texte(nom)
        
        # 2. Filtre par recherche tolérante (sans accents, sans ligature œ)
        if terme_recherche_clean and (terme_recherche_clean not in nom_clean and terme_recherche_clean not in nom_fichier_clean):
            continue

        recettes_affichees += 1
        
        with st.expander(f"📖 {nom_affiche}"):
            download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
            headers = {"Authorization": f"Bearer {creds.token}"}
            
            if st.button(f"👁️ Afficher la recette", key=f"view_{file_id}"):
                with st.spinner("Chargement et affichage des pages..."):
                    res = requests.get(download_url, headers=headers)
                    if res.status_code == 200:
                        try:
                            # Conversion des pages du PDF en images
                            pdf_file = pdfium.PdfDocument(res.content)
                            for page_index in range(len(pdf_file)):
                                page = pdf_file[page_index]
                                image = page.render(scale=2).to_pil()
                                st.image(image, use_container_width=True)
                        except Exception as e:
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
                        st.error("Erreur lors de la récupération de la recette.")

    if recettes_affichees == 0:
        st.warning("Aucune recette PDF ne correspond à votre recherche.")
