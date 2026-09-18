import streamlit as st
from fpdf import FPDF
import tempfile
import os
import unicodedata
import re

st.set_page_config(page_title="Générateur de Fiches Recettes", page_icon="🍳", layout="centered")

st.title("🍳 Générateur de Fiches Recettes PDF")
st.markdown("Remplissez les champs ci-dessous pour créer votre fiche propre et bien formatée.")

# Liste complète et harmonisée des catégories
CATEGORIES_RECETTES = [
    "Entrées",
    "Charcuteries",
    "Sauces",
    "Plats",
    "Desserts",
    "Pains & Pâtisseries",
    "Vins & Spiritueux",
    "Divers"
]

with st.form("form_recette"):
    st.subheader("1. 📝 Informations de la recette")
    
    # Choix de la catégorie
    categorie = st.selectbox("Choisissez la catégorie :", CATEGORIES_RECETTES)
    
    # Titre de la recette
    titre_recette = st.text_input("Titre de la recette", placeholder="Ex: Krouchtikis Bugnes Polonaises")
    
    # Image optionnelle
    image_file = st.file_uploader("Photo de la recette (optionnel)", type=["png", "jpg", "jpeg"])
    
    # Ingrédients
    ingredients = st.text_area("Ingrédients (un par ligne)", placeholder="• 300 g de farine\n• 2 œufs\n• 1 pincée de sel")
    
    # Étapes de préparation
    etapes = st.text_area("Préparation & Étapes", placeholder="1. Mélanger tous les ingrédients...\n2. Étaler la pâte...")
    
    submitted = st.form_submit_button("🚀 Générer le PDF de la recette")

if submitted:
    if not titre_recette.strip():
        st.warning("Veuillez indiquer au moins un titre pour votre recette.")
    else:
        try:
            # Création du PDF avec FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Titre principal du document
            pdf.set_font("helvetica", "B", 18)
            pdf.cell(0, 10, "CARNET DE RECETTES DE LA MAISON", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(5)
            
            # Titre de la recette
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, titre_recette, new_x="LMARGIN", new_y="NEXT", align="L")
            pdf.ln(3)
            
            # Insertion de l'image si présente
            if image_file is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file.name)[1]) as tmp_img:
                    tmp_img.write(image_file.getvalue())
                    tmp_img_path = tmp_img.name
                try:
                    # Ajout de l'image centrée
                    pdf.image(tmp_img_path, x=60, w=90)
                    pdf.ln(5)
                except Exception:
                    pass
                finally:
                    if os.path.exists(tmp_img_path):
                        os.remove(tmp_img_path)

            # Ingrédients
            pdf.set_font("helvetica", "B", 12)
            pdf.cell(0, 8, "INGRÉDIENTS", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 11)
            pdf.multi_cell(0, 6, ingredients)
            pdf.ln(5)
            
            # Étapes
            pdf.set_font("helvetica", "B", 12)
            pdf.cell(0, 8, "PRÉPARATION & ÉTAPES", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 11)
            pdf.multi_cell(0, 6, etapes)
            pdf.ln(10)
            
            # Pied de page
            pdf.set_font("helvetica", "I", 9)
            pdf.cell(0, 6, "Fiche recette individuelle issue du Carnet de Recettes Maison.", new_x="LMARGIN", new_y="NEXT", align="C")

            # Nom de fichier propre avec la balise entre crochets
            # On nettoie le titre pour éviter les caractères bizarres dans le fichier
            nom_fichier_clean = re.sub(r'[^a-zA-Z0-9àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ_\- ]', '', titre_recette)
            nom_fichier_clean = nom_fichier_clean.strip().replace(' ', '_')
            nom_pdf = f"[{categorie}] {nom_fichier_clean}.pdf"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                pdf.output(tmp_pdf.name)
                tmp_pdf_path = tmp_pdf.name

            with open(tmp_pdf_path, "rb") as f:
                pdf_bytes = f.read()

            if os.path.exists(tmp_pdf_path):
                os.remove(tmp_pdf_path)

            st.success(f"Fiche générée avec succès ! Nom du fichier : **{nom_pdf}**")
            
            st.download_button(
                label="💾 Télécharger le PDF de la recette",
                data=pdf_bytes,
                file_name=nom_pdf,
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"Une erreur est survenue lors de la génération du PDF : {e}")
