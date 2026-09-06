import streamlit as st
import os

# Configuration de la page
st.set_page_config(page_title="Nos Recettes de Cuisine", page_icon="🍳", layout="wide")

st.title("🍳 Le Carnet de Recettes de la Maison")

# Dossier local ou stockage cloud pour les PDF
STORAGE_DIR = "recettes_pdf"
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

# Menu latéral : Filtres et Recherche
st.sidebar.header("🔍 Recherche & Filtres")
categorie_filtre = st.sidebar.selectbox(
    "Catégorie", 
    ["Toutes", "Entrées", "Plats", "Desserts", "Pains & Pâtisseries", "Boissons & Pesto"]
)
recherche = st.sidebar.text_input("Rechercher une recette...")

# Section d'ajout de recette
st.sidebar.markdown("---")
st.sidebar.header("➕ Ajouter une recette")
nouveau_pdf = st.sidebar.file_uploader("Importer un fichier PDF", type=["pdf"])
titre_recette = st.sidebar.text_input("Nom de la recette")
cat_recette = st.sidebar.selectbox("Catégorie de la recette", ["Entrées", "Plats", "Desserts", "Pains & Pâtisseries", "Autres"])

if st.sidebar.button("Enregistrer la recette"):
    if nouveau_pdf and titre_recette:
        file_path = os.path.join(STORAGE_DIR, f"{cat_recette}_{titre_recette}.pdf")
        with open(file_path, "wb") as f:
            f.write(nouveau_pdf.getbuffer())
        st.sidebar.success(f"Recette '{titre_recette}' ajoutée avec succès !")
    else:
        st.sidebar.error("Veuillez remplir le titre et sélectionner un fichier PDF.")

# Affichage des recettes enregistrées
st.subheader("📚 Vos Recettes")

fichiers = [f for f in os.listdir(STORAGE_DIR) if f.endswith(".pdf")]

if not fichiers:
    st.info("Aucune recette enregistrée pour le moment. Utilisez le menu à gauche pour en ajouter !")
else:
    for fichier in fichiers:
        # Lecture basique des informations
        nom_affichage = fichier.replace(".pdf", "").replace("_", " - ")
        
        with st.expander(f"📖 {nom_affichage}"):
            file_path = os.path.join(STORAGE_DIR, fichier)
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()
            
            # Bouton de téléchargement / Ouverture
            st.download_button(
                label="📥 Télécharger le PDF",
                data=pdf_bytes,
                file_name=fichier,
                mime="application/pdf"
            )
