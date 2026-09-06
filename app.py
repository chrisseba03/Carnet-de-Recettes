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

# Configuration de la page
st.set_page_config(
    page_title="Le Carnet de Recettes de la Maison",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="collapsed"  # Masque le menu par défaut pour gagner de la place sur mobile
)

# Style CSS personnalisé pour l'optimisation mobile et les cartes
st.markdown("""
<style>
    /* Amélioration du style global */
    .stApp {
        background-color: #faf8f5;
    }
    
    /* Titre principal chaleureux */
    .main-title {
        color: #2c3e50;
        font-size: 2rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    /* Cartes de recettes */
    div[data-testid="stVerticalBlock"] > div.recipe-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eef0f2;
        margin-bottom: 10px;
    }
    
    /* Boutons adaptés au tactile sur mobile */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
        padding-top: 8px;
        padding-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🍳 Le Carnet de Recettes de la Maison</h1>', unsafe_allow_html=True)

# Initialisation des favoris
if "favoris" not in st.session_state:
    st.session_state.favoris = set()

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
    st.error("Petite baisse de réseau avec Google Drive. Utilisez le bouton 'Rafraîchir' dans le menu latéral.")
    st.stop()

# Filtre strict sur l'extension PDF
fichiers_pdf = [f for f in fichiers_bruts if f['name'].lower().endswith('.pdf')]
total_recettes = len(fichiers_pdf)

categories_liste = ["Entrées", "Plats", "Desserts", "Pains & Pâtisseries", "Autres"]

# --- BARRE LATÉRALE : AJOUT ET RECAP ---
st.sidebar.header("➕ Ajouter une recette")
nouveau_pdf = st.sidebar.file_uploader("Importer un fichier PDF", type=["pdf"])
titre_recette = st.sidebar.text_input("Nom de la recette")
cat_recette = st.sidebar.selectbox("Catégorie", categories_liste)

if st.sidebar.button("💾 Sauvegarder sur Google Drive"):
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

if st.sidebar.button("🔄 Rafraîchir la liste"):
    st.cache_data.clear()
    st.rerun()

# Récapitulatif par catégorie dans le menu latéral
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Répartition")
stats_cat = {cat: 0 for cat in categories_liste}

for f in fichiers_pdf:
    trouve = False
    for cat in categories_liste:
        if f"[{cat}]" in f['name']:
            stats_cat[cat] += 1
            trouve = True
            break
    if not trouve:
        stats_cat["Autres"] += 1

for cat, count in stats_cat.items():
    if count > 0:
        st.sidebar.text(f"• {cat} : {count}")

st.sidebar.text(f"• ⭐ Coups de cœur : {len(st.session_state.favoris)}")

# --- BARRE DE RECHERCHE PRINCIPALE ---
recherche = st.text_input("🔍 **Rechercher une recette par mot-clé**", placeholder="Tapez ici (ex: crepe, gateau, poulet...)", label_visibility="collapsed")

# --- NAVIGATION PAR ONGLETS (TABS) POUR MOBILES ---
onglets = st.tabs([
    f"📚 Toutes ({total_recettes})",
    f"⭐ Favoris ({len(st.session_state.favoris)})",
    f"🥗 Entrées ({stats_cat['Entrées']})",
    f"🍲 Plats ({stats_cat['Plats']})",
    f"🍰 Desserts ({stats_cat['Desserts']})",
    f"🥖 Pains ({stats_cat['Pains & Pâtisseries']})",
    f"📦 Autres ({stats_cat['Autres']})"
])

# Fonction d'affichage des cartes de recettes
def afficher_grille_recettes(liste_fichiers, filtre_categorie=None, uniquement_favoris=False):
    terme_recherche_clean = normaliser_texte(recherche)
    
    # Pre-filtrage
    fichiers_filtrer = []
    for f in liste_fichiers:
        nom = f['name']
        file_id = f['id']
        
        est_favori = file_id in st.session_state.favoris
        if uniquement_favoris and not est_favori:
            continue

        cat_du_fichier = "Autres"
        for cat in categories_liste:
            if f"[{cat}]" in nom:
                cat_du_fichier = cat
                break
                
        if filtre_categorie and cat_du_fichier != filtre_categorie:
            continue
            
        nom_affiche = nom.replace('.pdf', '').replace('.PDF', '')
        for cat in categories_liste:
            nom_affiche = nom_affiche.replace(f"[{cat}] ", "").replace(f"[{cat}]", "")
        
        nom_clean = normaliser_texte(nom_affiche)
        nom_fichier_clean = normaliser_texte(nom)
        
        if terme_recherche_clean and (terme_recherche_clean not in nom_clean and terme_recherche_clean not in nom_fichier_clean):
            continue
            
        fichiers_filtrer.append((f, nom_affiche, est_favori, cat_du_fichier))

    # Tri : Les favoris en premier, puis alphabétique
    fichiers_filtrer = sorted(fichiers_filtrer, key=lambda x: (not x[2], x[1].lower()))

    if not fichiers_filtrer:
        st.info("Aucune recette ne correspond à votre sélection.")
        return

    # Grille responsive : 2 colonnes sur tablette/PC, s'adapte très bien au smartphone
    cols = st.columns(2)
    
    for idx, (f, nom_affiche, est_favori, cat_du_fichier) in enumerate(fichiers_filtrer):
        col = cols[idx % 2]
        
        with col:
            # Carte de la recette
            st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
            
            # Badge de catégorie & titre
            icone_fav = "⭐ " if est_favori else ""
            st.markdown(f"### {icone_fav}{nom_affiche}")
            st.caption(f"📁 **Catégorie :** {cat_du_fichier}")
            
            # Boutons d'action rapides
            col_b1, col_b2 = st.columns([1, 1])
            
            with col_b1:
                # Bouton Favori toggle
                if est_favori:
                    if st.button("❌ Retirer", key=f"fav_del_{f['id']}"):
                        st.session_state.favoris.remove(f['id'])
                        st.rerun()
                else:
                    if st.button("⭐ Favori", key=f"fav_add_{f['id']}"):
                        st.session_state.favoris.add(f['id'])
                        st.rerun()
                        
            with col_b2:
                # Bouton/Accordéon d'ouverture du PDF
                bouton_voir = st.checkbox("👁️ Aperçu", key=f"check_view_{f['id']}")

            if bouton_voir:
                download_url = f"https://www.googleapis.com/drive/v3/files/{f['id']}?alt=media"
                headers = {"Authorization": f"Bearer {creds.token}"}
                
                with st.spinner("Chargement de la recette..."):
                    res = requests.get(download_url, headers=headers)
                    if res.status_code == 200:
                        try:
                            pdf_file = pdfium.PdfDocument(res.content)
                            for page_index in range(len(pdf_file)):
                                page = pdf_file[page_index]
                                image = page.render(scale=2).to_pil()
                                st.image(image, use_container_width=True)
                        except Exception as e:
                            st.error("Impossible d'afficher l'aperçu du PDF.")

                        st.download_button(
                            label="💾 Télécharger PDF",
                            data=res.content,
                            file_name=f['name'],
                            mime="application/pdf",
                            key=f"dl_{f['id']}"
                        )
                    else:
                        st.error("Erreur lors de la récupération de la recette.")
                        
            st.markdown('</div>', unsafe_allow_html=True)

# REMPLISSAGE DE CHAQUE ONGLET
with onglets[0]:
    afficher_grille_recettes(fichiers_pdf)

with onglets[1]:
    afficher_grille_recettes(fichiers_pdf, uniquement_favoris=True)

with onglets[2]:
    afficher_grille_recettes(fichiers_pdf, filtre_categorie="Entrées")

with onglets[3]:
    afficher_grille_recettes(fichiers_pdf, filtre_categorie="Plats")

with onglets[4]:
    afficher_grille_recettes(fichiers_pdf, filtre_categorie="Desserts")

with onglets[5]:
    afficher_grille_recettes(fichiers_pdf, filtre_categorie="Pains & Pâtisseries")

with onglets[6]:
    afficher_grille_recettes(fichiers_pdf, filtre_categorie="Autres")
