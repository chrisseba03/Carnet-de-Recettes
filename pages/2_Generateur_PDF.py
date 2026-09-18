import streamlit as st
import base64
from weasyprint import HTML
import pypdfium2 as pdfium

st.set_page_config(page_title="Générateur de Fiches PDF - Style Terroir", page_icon="✨", layout="wide")

st.markdown("""
    <div style="background-color: #6b2d18; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 24px;">✨ Générateur de Fiches Recettes - Style Authentique</h1>
        <p style="margin: 5px 0 0 0; font-size: 14px; font-style: italic;">Pour votre groupe "La Place du Village - ALLIER (03)"</p>
    </div>
""", unsafe_allow_html=True)

with st.form("recipe_form"):
    st.subheader("1. 📂 Import de fichier source (Optionnel)")
    uploaded_source_file = st.file_uploader(
        "Déposez un fichier PDF ou Texte (.txt) pour pré-remplir les champs", 
        type=["pdf", "txt"]
    )
    
    # Variables de texte par défaut
    def_titre = "RECETTE GOURMANDE DU TERROIR"
    def_soustitre = "Le partage des saveurs authentiques de notre région"
    def_diff = "Facile"
    def_budget = "Abordable"
    def_prep = "20 min"
    def_cuisson = "30 min"
    def_ing = "• Ingrédient 1\n• Ingrédient 2"
    def_ust = "• Bol de préparation\n• Spatule"
    def_inst = "Étape 1 - Préparation\nExpliquez ici la première étape.\n\nÉtape 2 - Cuisson\nExpliquez ici la seconde étape."
    def_astuces = "• Veillez à utiliser des produits frais.\n• Conserver au frais si nécessaire."
    def_alt = "Idéal à partager en famille ou entre amis lors de vos repas conviviaux."

    # Lecture automatique si un fichier est fourni
    if uploaded_source_file is not None:
        if uploaded_source_file.name.endswith('.txt'):
            try:
                raw_text = uploaded_source_file.read().decode("utf-8")
                def_inst = raw_text
            except:
                pass
        elif uploaded_source_file.name.endswith('.pdf'):
            try:
                pdf_doc = pdfium.PdfDocument(uploaded_source_file.read())
                extracted_pages = [page.get_textpage().get_text_range() for page in pdf_doc]
                def_inst = "\n".join(extracted_pages)
            except:
                pass

    st.subheader("2. 📝 Informations de la Recette")
    col1, col2 = st.columns(2)
    with col1:
        titre = st.text_input("Titre de la recette", value=def_titre)
        sous_titre = st.text_input("Sous-titre / Description courte", value=def_soustitre)
    with col2:
        difficulte = st.text_input("Difficulté", value=def_diff)
        budget = st.text_input("Budget", value=def_budget)
    
    col3, col4 = st.columns(2)
    with col3:
        preparation = st.text_input("Temps de préparation", value=def_prep)
    with col4:
        cuisson = st.text_input("Temps de cuisson", value=def_cuisson)

    col5, col6 = st.columns(2)
    with col5:
        ingredients = st.text_area("Ingrédients", value=def_ing, height=120)
        ustensiles = st.text_area("Ustensiles", value=def_ust, height=100)
    with col6:
        instructions = st.text_area("Instructions de préparation", value=def_inst, height=240)

    col7, col8 = st.columns(2)
    with col7:
        astuces = st.text_area("Astuces de l'auteur", value=def_astuces, height=90)
    with col8:
        alternative = st.text_area("Alternative & Dégustation", value=def_alt, height=90)

    st.subheader("3. 📸 Photo de la Recette")
    uploaded_image = st.file_uploader("Choisissez une image (JPG, PNG)", type=["jpg", "jpeg", "png"])
    
    submitted = st.form_submit_button("Générer la Fiche PDF Structurée")

if submitted:
    image_html = ""
    if uploaded_image is not None:
        bytes_data = uploaded_image.getvalue()
        encoded_img = base64.b64encode(bytes_data).decode("utf-8")
        image_src = f"data:{uploaded_image.type};base64,{encoded_img}"
        image_html = f'<img src="{image_src}" style="width: 100%; height: 160px; object-fit: cover; border-radius: 6px; display: block;" />'
    else:
        image_html = '<div style="width: 100%; height: 160px; display: flex; align-items: center; justify-content: center; background-color: #fbf5ee; border-radius: 6px; border: 1px dashed #d97724; color: #7c321a; font-size: 28px;">🍲</div>'

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{ size: A4; margin: 10mm; }}
            body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #fdfbf7; color: #2c2c2c; margin: 0; padding: 0; font-size: 9.5pt; line-height: 1.35; }}
            .header {{ background-color: #6b2d18; color: white; text-align: center; padding: 10px 15px; border-radius: 6px; margin-bottom: 8px; }}
            .header h1 {{ margin: 0; font-size: 16pt; text-transform: uppercase; letter-spacing: 0.5px; }}
            .header p {{ margin: 2px 0 0 0; font-size: 9pt; font-style: italic; color: #fbf5ee; }}
            
            .top-section {{ width: 100%; display: table; margin-bottom: 8px; }}
            .meta-col {{ display: table-cell; width: 55%; vertical-align: top; padding-right: 8px; }}
            .image-col {{ display: table-cell; width: 45%; vertical-align: top; text-align: right; }}
            
            .badge-grid {{ width: 100%; border-collapse: separate; border-spacing: 4px; }}
            .badge {{ background: white; border: 1px solid #d9c5b2; border-radius: 4px; padding: 5px 6px; font-size: 8.5pt; text-align: center; color: #4a4a4a; }}
            .badge strong {{ color: #c86414; display: block; font-size: 7.5pt; text-transform: uppercase; margin-bottom: 1px; }}

            .main-grid {{ width: 100%; display: table; margin-bottom: 8px; }}
            .left-col {{ display: table-cell; width: 42%; vertical-align: top; padding-right: 8px; }}
            .right-col {{ display: table-cell; width: 58%; vertical-align: top; }}

            .card {{ background: white; border: 1px solid #ecdcd0; border-radius: 6px; padding: 8px 10px; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); }}
            .section-title {{ color: #6b2d18; font-size: 9.5pt; font-weight: bold; border-bottom: 2px solid #d97724; padding-bottom: 2px; margin-bottom: 6px; text-transform: uppercase; }}
            
            .bottom-grid {{ width: 100%; display: table; margin-bottom: 4px; }}
            .bottom-col {{ display: table-cell; width: 48%; vertical-align: top; }}
            .bottom-col.left {{ padding-right: 4px; }}
            .bottom-col.right {{ padding-left: 4px; }}

            .footer {{ text-align: center; font-size: 8.5pt; color: #7c321a; font-weight: 500; border-top: 1px dashed #d97724; padding-top: 5px; margin-top: 4px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{titre}</h1>
            <p>{sous_titre}</p>
        </div>
        
        <div class="top-section">
            <div class="meta-col">
                <table class="badge-grid">
                    <tr>
                        <td class="badge"><strong>Difficulté</strong>{difficulte}</td>
                        <td class="badge"><strong>Budget</strong>{budget}</td>
                    </tr>
                    <tr>
                        <td class="badge"><strong>Préparation</strong>{preparation}</td>
                        <td class="badge"><strong>Cuisson</strong>{cuisson}</td>
                    </tr>
                </table>
            </div>
            <div class="image-col">
                {image_html}
            </div>
        </div>

        <div class="main-grid">
            <div class="left-col">
                <div class="card">
                    <div class="section-title">Ingrédients</div>
                    <div style="white-space: pre-line;">{ingredients}</div>
                </div>
                <div class="card">
                    <div class="section-title">Ustensiles</div>
                    <div style="white-space: pre-line;">{ustensiles}</div>
                </div>
            </div>
            <div class="right-col">
                <div class="card" style="height: 100%;">
                    <div class="section-title">Instructions de préparation</div>
                    <div style="white-space: pre-line;">{instructions}</div>
                </div>
            </div>
        </div>

        <div class="bottom-grid">
            <div class="bottom-col left">
                <div class="card" style="margin-bottom:0;">
                    <div class="section-title">Astuces de l'auteur</div>
                    <div style="white-space: pre-line; font-size: 9pt;">{astuces}</div>
                </div>
            </div>
            <div class="bottom-col right">
                <div class="card" style="margin-bottom:0;">
                    <div class="section-title">Alternative & Dégustation</div>
                    <div style="white-space: pre-line; font-size: 9pt;">{alternative}</div>
                </div>
            </div>
        </div>

        <div class="footer">
            Fiche recette générée pour votre groupe "La Place du Village - ALLIER (03)" • Bon appétit !
        </div>
    </body>
    </html>
    """

    pdf_bytes = HTML(string=html_content).write_pdf()
    st.success("Fiche recette structurée générée avec succès !")
    st.download_button(
        label="📥 Télécharger la fiche PDF structurée",
        data=pdf_bytes,
        file_name="fiche_recette_structuree.pdf",
        mime="application/pdf"
    )
