import streamlit as st
import base64
from weasyprint import HTML
import pypdfium2 as pdfium

# Configuration de la page indépendante
st.set_page_config(page_title="Générateur de Fiches PDF", page_icon="✨", layout="wide")

st.markdown("""
    <div style="background-color: #6b2d18; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 24px;">✨ Générateur de Fiches Recettes Pro</h1>
        <p style="margin: 5px 0 0 0; font-size: 14px; font-style: italic;">Pour votre groupe "La Place du Village - ALLIER (03)"</p>
    </div>
""", unsafe_allow_html=True)

with st.form("recipe_form"):
    st.subheader("1. 📂 Source de la recette (Import de fichier ou Saisie)")
    
    uploaded_source_file = st.file_uploader(
        "Importer un fichier source (PDF ou Texte .txt) - Optionnel", 
        type=["pdf", "txt"],
        help="Si vous déposez un fichier ici, son texte sera automatiquement extrait !"
    )
    
    recipe_text = st.text_area(
        "Ou rédigez / collez votre texte de recette ici :",
        height=180,
        placeholder="Ex: Tarte aux pommes bourbonnaise, ingrédients, étapes..."
    )
    
    st.subheader("2. 📸 Photo du Plat (Optionnel)")
    uploaded_image = st.file_uploader("Choisissez une photo (JPG, PNG)", type=["jpg", "jpeg", "png"], key="img_upload")
    
    submitted = st.form_submit_button("Générer la Fiche Recette PDF")

# Récupération automatique du texte selon la source choisie
texte_final = recipe_text
if uploaded_source_file is not None:
    if uploaded_source_file.name.endswith('.txt'):
        try:
            texte_final = uploaded_source_file.read().decode("utf-8")
        except:
            texte_final = uploaded_source_file.read().decode("latin-1")
    elif uploaded_source_file.name.endswith('.pdf'):
        try:
            pdf_doc = pdfium.PdfDocument(uploaded_source_file.read())
            extracted_pages = []
            for i in range(len(pdf_doc)):
                page = pdf_doc[i]
                textpage = page.get_textpage()
                extracted_pages.append(textpage.get_text_range())
            texte_final = "\n".join(extracted_pages)
        except Exception:
            st.error("Erreur lors de la lecture automatique du PDF source.")

if submitted:
    if not texte_final.strip():
        st.warning("Veuillez importer un fichier source ou saisir du texte pour générer la fiche.")
    else:
        image_html = ""
        if uploaded_image is not None:
            bytes_data = uploaded_image.getvalue()
            encoded_img = base64.b64encode(bytes_data).decode("utf-8")
            mime_type = uploaded_image.type
            image_src = f"data:{mime_type};base64,{encoded_img}"
            image_html = f'<img src="{image_src}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px; display: block;" />'
        else:
            image_html = '<div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background-color: #fbf5ee; border-radius: 8px; border: 1px dashed #d97724; color: #7c321a; font-size: 36px;">🍲</div>'

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4; margin: 12mm; }}
                body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #fdfbf7; color: #2c2c2c; margin: 0; padding: 0; font-size: 11pt; line-height: 1.4; }}
                .header-band {{ background: linear-gradient(135deg, #6b2d18 0%, #8c3d20 100%); color: white; padding: 15px 20px; border-radius: 8px; text-align: center; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header-band h1 {{ margin: 0; font-size: 20pt; letter-spacing: 0.5px; text-transform: uppercase; }}
                .header-band p {{ margin: 4px 0 0 0; font-size: 10pt; color: #fbf5ee; font-style: italic; }}
                .top-container {{ display: table; width: 100%; margin-bottom: 12px; }}
                .meta-box {{ display: table-cell; width: 52%; vertical-align: middle; }}
                .image-box {{ display: table-cell; width: 44%; vertical-align: middle; text-align: right; height: 130px; }}
                .badge-grid {{ width: 100%; border-collapse: separate; border-spacing: 6px; }}
                .badge {{ background-color: white; border: 1px solid #e0d6cc; border-radius: 6px; padding: 6px 8px; text-align: center; font-size: 9.5pt; color: #4a4a4a; }}
                .badge strong {{ color: #c86414; display: block; font-size: 8.5pt; text-transform: uppercase; margin-bottom: 1px; }}
                .content-card {{ background-color: #ffffff; border: 1px solid #ecdcd0; border-radius: 8px; padding: 15px; margin-top: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
                .section-title {{ color: #6b2d18; font-size: 11pt; font-weight: bold; border-bottom: 2px solid #d97724; padding-bottom: 3px; margin-bottom: 8px; text-transform: uppercase; }}
                .footer {{ margin-top: 15px; text-align: center; font-size: 9pt; color: #7c321a; font-weight: 500; border-top: 1px dashed #d97724; padding-top: 8px; }}
            </style>
        </head>
        <body>
            <div class="header-band">
                <h1>Fiche Recette Terroir</h1>
                <p>La Place du Village - Allier (03)</p>
            </div>
            
            <div class="top-container">
                <div class="meta-box">
                    <table class="badge-grid">
                        <tr>
                            <td class="badge"><strong>Style</strong>Traditionnel & Fait Maison</td>
                            <td class="badge"><strong>Qualité</strong>Sélection du Terroir</td>
                        </tr>
                        <tr>
                            <td class="badge" colspan="2"><strong>Communauté</strong>La Place du Village - Allier (03)</td>
                        </tr>
                    </table>
                </div>
                <div style="width: 4%;"></div>
                <div class="image-box">
                    {image_html}
                </div>
            </div>

            <div class="content-card">
                <div class="section-title">Détails de la Recette</div>
                <div style="white-space: pre-line; font-size: 10.5pt; color: #333333;">{texte_final}</div>
            </div>

            <div class="footer">
                Partagé avec passion pour le groupe "La Place du Village - Allier (03)" • Bon appétit !
            </div>
        </body>
        </html>
        """

        pdf_bytes = HTML(string=html_content).write_pdf()
        st.success("Fiche recette PDF générée avec brio !")
        st.download_button(
            label="📥 Télécharger la nouvelle fiche PDF",
            data=pdf_bytes,
            file_name="fiche_recette_place_du_village.pdf",
            mime="application/pdf"
        )
