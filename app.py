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
    texte = texte.replace("œ", "oe").replace("Œ", "oe").replace("æ", "ae").replace("Æ", "ae")
    texte = unicodedata.normalize('NFD', texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != 'Mn')
    texte = texte.lower()
    texte = re.sub(r'[^a-z0-9]', '', texte)
    return texte

# Client d'authentification Google Drive
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

# --- RECUPERATION DE TOUTES LES RECETTES ---
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
            pageToken=page_token
        ).execute()
        
        fichiers.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        
        if page_token is None:
            break
            
    return fichiers

try:
    fichiers_bruts = get_all_recipes()
except Exception as err:
    st.error("Petite baisse de réseau avec Google Drive. Cliquez sur 'Rafraîchir la liste' dans le menu de gauche.")
    st.stop()

# Filtre strict sur l'extension PDF
fichiers_pdf = [f for f in fichiers_bruts if f['name'].lower().endswith('.pdf')]
total_recettes = len(fichiers_pdf)

categories_liste = ["Entrées", "Plats", "Desserts", "Pains & Pâtisseries", "Autres"]

# --- BARRE LATÉRALE : AJOUT & FILTRES ---
st.sidebar.header("➕ Ajouter une recette")
nouveau_pdf = st.sidebar.file_uploader("Importer un fichier PDF", type=["pdf"])
titre_recette = st.sidebar.text_input("Nom de la recette")
cat_recette = st.sidebar.selectbox("Catégorie", categories_liste)

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
categorie_filtre = st.sidebar.selectbox("Filtrer par catégorie", ["Toutes"] + categories_liste)

if st.sidebar.button("🔄 Rafraîchir la liste"):
    st.cache_data.clear()
    st.rerun()

# --- RECAPITULATIF PAR CATEGORIE DANS LA BARRE LATERALE ---
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

# --- RECHERCHE ET AFFICHAGE PRINCIPAL ---
st.markdown("---")
recherche = st.text_input("🔍 **Rechercher une recette par mot-clé**", placeholder="Tapez ici (ex: crepe, gateau, oeuf, poulet...)")
st.markdown("---")

if not fichiers_pdf:
    st.info("Aucune recette au format PDF trouvée sur votre Google Drive. Ajoutez votre première recette depuis le menu à gauche !")
else:
    terme_recherche_clean = normaliser_texte(recherche)
    
    # Pré-filtrage des recettes
    fichiers_filtrer = []
    for f in fichiers_pdf:
        nom = f['name']
        file_id = f['id']
        nom_norm = normaliser_texte(nom)

        # Détermination de la catégorie du fichier
        cat_du_fichier = "Autres"
        for cat in categories_liste:
            cat_norm = normaliser_texte(cat)
            if f"[{cat_norm}]" in nom_norm or cat_norm in nom_norm[:len(cat_norm)+2]:
                cat_du_fichier = cat
                break
                
        # Filtre de catégorie
        if categorie_filtre != "Toutes" and cat_du_fichier != categorie_filtre:
            continue
            
        # Nettoyage du titre affiché
        nom_affiche = nom.replace('.pdf', '').replace('.PDF', '')
        for cat in categories_liste:
            pattern = re.compile(re.escape(f"[{cat}]"), re.IGNORECASE)
            nom_affiche = pattern.sub("", nom_affiche)
            pattern_acc = re.compile(re.escape(f"[{unicodedata.normalize('NFD', cat)}]"), re.IGNORECASE)
            nom_affiche = pattern_acc.sub("", nom_affiche)
            
        nom_affiche = nom_affiche.replace("[Entrées]", "").replace("[ENTREES]", "").replace("[entrées]", "").strip()
        nom_affiche = nom_affiche.replace('_', ' ').strip()
        
        nom_clean = normaliser_texte(nom_affiche)
        
        if terme_recherche_clean and (terme_recherche_clean not in nom_clean and terme_recherche_clean not in nom_norm):
            continue
            
        fichiers_filtrer.append((f, nom_affiche))

    # Tri par ordre alphabétique
    fichiers_filtrer = sorted(fichiers_filtrer, key=lambda x: x[1].lower())

    # Affichage du titre et des sous-titres
    nb_resultats = len(fichiers_filtrer)
    if categorie_filtre != "Toutes" or terme_recherche_clean:
        st.subheader(f"📚 Recettes correspondantes ({nb_resultats} / {total_recettes})")
    else:
        st.subheader(f"📚 Toutes vos recettes ({total_recettes})")

    # Affichage de chaque recette
    for f, nom_affiche in fichiers_filtrer:
        nom = f['name']
        file_id = f['id']

        titre_accordéon = f"📖 {nom_affiche}"

        with st.expander(titre_accordéon):
            download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
            headers = {"Authorization": f"Bearer {creds.token}"}
            
            if st.button(f"👁️ Afficher la recette", key=f"view_{file_id}"):
                with st.spinner("Chargement et affichage des pages..."):
                    res = requests.get(download_url, headers=headers)
                    if res.status_code == 200:
                        try:
                            pdf_file = pdfium.PdfDocument(res.content)
                            for page_index in range(len(pdf_file)):
                                image = pdf_file[page_index].render(scale=2).to_pil()
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

    if nb_resultats == 0:
        st.warning("Aucune recette ne correspond à votre sélection.")
