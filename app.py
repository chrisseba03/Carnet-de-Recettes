import streamlit as st
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

st.set_page_config(page_title="Nos Recettes de Cuisine", page_icon="🍳", layout="wide")
st.title("🍳 Le Carnet de Recettes de la Maison")

# Authentification Google Drive via Streamlit Secrets
@st.cache_resource
def get_drive_service():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)

try:
    drive_service = get_drive_service()
    FOLDER_ID = st.secrets["FOLDER_ID"]
except Exception as e:
    st.error("Erreur de connexion à Google Drive. Vérifiez la configuration des Secrets.")
    st.stop()

# --- BARRE LATÉRALE : AJOUT DE RECETTE ---
st.sidebar.header("➕ Ajouter une recette")
nouveau_pdf = st.sidebar.file_uploader("Importer un fichier PDF", type=["pdf"])
titre_recette = st.sidebar.text_input("Nom de la recette")
cat_recette = st.sidebar.selectbox("Catégorie", ["Entrées", "Plats", "Desserts", "Pains & Pâtisseries", "Autres"])

if st.sidebar.button("Sauvegarder sur Google Drive"):
    if nouveau_pdf and titre_recette:
        nom_fichier = f"[{cat_recette}] {titre_recette}.pdf"
        file_metadata = {
            'name': nom_fichier,
            'parents': [FOLDER_ID]
        }
        media = MediaIoBaseUpload(io.BytesIO(nouveau_pdf.read()), mimetype='application/pdf')
        
        with st.spinner("Envoi vers Google Drive en cours..."):
            drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        
        st.sidebar.success(f"Recette '{titre_recette}' sauvegardée avec succès !")
        st.rerun()
    else:
        st.sidebar.error("Veuillez renseigner le titre et choisir un fichier PDF.")

# --- AFFICHAGE ET RECHERCHE DES RECETTES ---
st.sidebar.markdown("---")
st.sidebar.header("🔍 Recherche & Filtres")
categorie_filtre = st.sidebar.selectbox("Filtrer par catégorie", ["Toutes", "Entrées", "Plats", "Desserts", "Pains & Pâtisseries", "Autres"])
recherche = st.sidebar.text_input("Rechercher par mot-clé")

st.subheader("📚 Vos Recettes Sauvegardées")

# Fonction pour récupérer l'intégralité des fichiers (gestion de la pagination)
def get_all_recipes():
    fichiers = []
    page_token = None
    query = f"'{FOLDER_ID}' in parents and trashed = false and mimeType = 'application/pdf'"
    
    while True:
        response = drive_service.files().list(
            q=query,
            fields="nextPageToken, files(id, name)",
            pageSize=100,
            pageToken=page_token
        ).execute()
        
        fichiers.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        
        if page_token is None:
            break
            
    return fichiers

fichiers = get_all_recipes()

if not fichiers:
    st.info("Aucune recette trouvée sur votre Google Drive. Ajoutez votre première recette depuis le menu à gauche !")
else:
    # Tri par ordre alphabétique
    fichiers = sorted(fichiers, key=lambda x: x['name'].lower())
    
    for f in fichiers:
        nom = f['name']
        file_id = f['id']
        
        # Filtrage par catégorie et recherche
        if categorie_filtre != "Toutes" and f"[{categorie_filtre}]" not in nom:
            continue
        if recherche and recherche.lower() not in nom.lower():
            continue

        with st.expander(f"📖 {nom.replace('.pdf', '')}"):
            request = drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            pdf_bytes = fh.getvalue()
            
            st.download_button(
                label="📥 Ouvrir / Télécharger le PDF",
                data=pdf_bytes,
                file_name=nom,
                mime="application/pdf"
            )
