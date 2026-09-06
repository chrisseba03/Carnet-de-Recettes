import streamlit as st
import io
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import google.auth.transport.requests

st.set_page_config(page_title="Nos Recettes de Cuisine", page_icon="🍳", layout="wide")
st.title("🍳 Le Carnet de Recettes de la Maison")

# Client d'authentification optimisé avec `requests`
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
        st.cache_data.clear()
        st.rerun()
    else:
        st.sidebar.error("Veuillez renseigner le titre et choisir un fichier PDF.")

# --- AFFICHAGE ET RECHERCHE DES RECETTES ---
st.sidebar.markdown("---")
st.sidebar.header("🔍 Recherche & Filtres")
categorie_filtre = st.sidebar.selectbox("Filtrer par catégorie", ["Toutes", "Entrées", "Plats", "Desserts", "Pains & Pâtisseries", "Autres"])
recherche = st.sidebar.text_input("Rechercher par mot-clé")

if st.sidebar.button("🔄 Rafraîchir la liste"):
    st.cache_data.clear()
    st.rerun()

st.subheader("📚 Vos Recettes Sauvegardées")

# Mise en cache de la liste pour soulager la connexion SSL
@st.cache_data(ttl=600)
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

try:
    fichiers = get_all_recipes()
except Exception as err:
    st.error("Petite baisse de réseau avec Google Drive. Cliquez sur 'Rafraîchir la liste' dans le menu de gauche.")
    st.stop()

if not fichiers:
    st.info("Aucune recette trouvée sur votre Google Drive. Ajoutez votre première recette depuis le menu à gauche !")
else:
    fichiers = sorted(fichiers, key=lambda x: x['name'].lower())
    
    for f in fichiers:
        nom = f['name']
        file_id = f['id']
        
        if categorie_filtre != "Toutes" and f"[{categorie_filtre}]" not in nom:
            continue
        if recherche and recherche.lower() not in nom.lower():
            continue

        with st.expander(f"📖 {nom.replace('.pdf', '')}"):
            # Téléchargement à la demande uniquement lorsque l'utilisateur clique
            download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
            headers = {"Authorization": f"Bearer {creds.token}"}
            
            if st.button(f"📥 Charger / Télécharger le PDF", key=file_id):
                with st.spinner("Téléchargement du fichier..."):
                    res = requests.get(download_url, headers=headers)
                    if res.status_code == 200:
                        st.download_button(
                            label="💾 Enregistrer le fichier PDF",
                            data=res.content,
                            file_name=nom,
                            mime="application/pdf",
                            key=f"dl_{file_id}"
                        )
                    else:
                        st.error("Erreur lors de la récupération du fichier.")
