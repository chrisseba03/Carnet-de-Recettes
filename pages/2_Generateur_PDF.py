import streamlit as st
from weasyprint import HTML
import tempfile
import os
import re

st.set_page_config(page_title="Générateur de Fiches Recettes", page_icon="🍳", layout="centered")

st.title("🍳 Générateur de Fiches Recettes PDF")
st.markdown("Remplissez les champs ci-dessous pour créer votre fiche propre et bien formatée.")

# Liste complète et harmonisée de toutes vos catégories
categories_liste = [
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
    
    # Menu déroulant avec toutes les catégories
    categorie = st.selectbox("Choisissez la catégorie :", categories_liste)
    
    titre_recette = st.text_input("Titre de la recette", placeholder="Ex: Krouchtikis Bugnes Polonaises")
    image_file = st.file_uploader("Photo de la recette (optionnel)", type=["png", "jpg", "jpeg"])
    ingredients = st.text_area("Ingrédients (un par ligne)", placeholder="• 300 g de farine\n• 2 œufs\n• 1 pincée de sel")
    etapes = st.text_area("Préparation & Étapes", placeholder="1. Mélanger tous les ingrédients...\n2. Étaler la pâte...")
    
    submitted = st.form_submit_button("🚀 Générer le PDF de la recette")

if submitted:
    if not titre_recette.strip():
        st.warning("Veuillez indiquer au moins un titre pour votre recette.")
    else:
        try:
            # Gestion de l'image optionnelle
            img_html = ""
            img_path = None
            if image_file is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file.name)[1]) as tmp_img:
                    tmp_img.write(image_file.getvalue())
                    img_path = tmp_img.name
                img_html = f'<div style="text-align: center; margin-bottom: 20px;"><img src="{img_path}" style="max-height: 250px; border-radius: 8px;"></div>'

            # Formatage propre du texte en HTML pour WeasyPrint
            ing_html = "".join([f"<li>{item.strip()}</li>" for item in ingredients.split("\n") if item.strip()])
            etape_html = "".join([f"<p>{item.strip()}</p>" for item in etapes.split("\n") if item.strip()])

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Helvetica, Arial, sans-serif; color: #333; margin: 30px; }}
                h1 {{ text-align: center; color: #2c3e50; font-size: 20px; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                h2 {{ color: #2c3e50; font-size: 16px; margin-top: 20px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
                ul {{ line-height: 1.6; }}
                p {{ line-height: 1.6; }}
                .footer {{ text-align: center; font-size: 10px; color: #777; margin-top: 40px; font-style: italic; }}
            </style>
            </head>
            <body>
                <h1>CARNET DE RECETTES DE LA MAISON</h1>
                <h2 style="font-size: 22px; text-align: center; color: #e67e22;">{titre_recette}</h2>
                {img_html}
                <h2>INGRÉDIENTS</h2>
                <ul>{ing_html}</ul>
                <h2>PRÉPARATION & ÉTAPES</h2>
                {etape_html}
                <div class="footer">Fiche recette individuelle issue du Carnet de Recettes Maison.</div>
            </body>
            </html>
            """

            # Génération du PDF avec WeasyPrint
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                pdf_path = tmp_pdf.name

            HTML(string=html_content).write_pdf(pdf_path)

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            # Nettoyage des fichiers temporaires
            if img_path and os.path.exists(img_path):
                os.remove(img_path)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

            # Nom du fichier propre avec la catégorie entre crochets (ex: [Charcuteries] Saucisson.pdf)
            nom_fichier_clean = re.sub(r'[^a-zA-Z0-9àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ_\- ]', '', titre_recette)
            nom_fichier_clean = nom_fichier_clean.strip().replace(' ', '_')
            nom_pdf = f"[{categorie}] {nom_fichier_clean}.pdf"

            st.success(f"Fiche générée avec succès ! Nom du fichier : **{nom_pdf}**")
            
            st.download_button(
                label="💾 Télécharger le PDF de la recette",
                data=pdf_bytes,
                file_name=nom_pdf,
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"Une erreur est survenue lors de la génération du PDF : {e}")
