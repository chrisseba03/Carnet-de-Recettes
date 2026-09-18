import streamlit as st
import base64
from weasyprint import HTML

# Configuration de la page indépendante
st.set_page_config(page_title="Générateur de Fiches PDF", page_icon="✨", layout="wide")

st.markdown("""
    <div style="background-color: #6b2d18; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 24px;">✨ Générateur de Fiches Recettes PDF</h1>
        <p style="margin: 5px 0 0 0; font-size: 14px; font-style: italic;">Pour votre groupe "La Place du Village - ALLIER (03)"</p>
    </div>
""", unsafe_allow_html=True)

with st.form("recipe_form"):
    st.subheader("1. 📝 Contenu de la Recette")
    recipe_text = st.text_area(
        "Collez ou rédigez votre recette ici (titre, ingrédients, étapes...) :",
        height=220,
        placeholder="Ex: Tarte aux pommes bourbonnaise..."
    )
    
    st.subheader("2. 📸 Photo du Plat (Optionnel)")
    uploaded_image = st.file_uploader("Choisissez une photo (JPG, PNG)", type=["jpg", "jpeg", "png"])
    
    submitted = st.form_submit_button("Générer la Fiche Recette PDF")

if submitted:
    if not recipe_text.strip():
        st.warning("Veuillez saisir ou coller le contenu de la recette.")
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
                @page {{ size: A4; margin: 15mm; }}
                body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #fdfbf7; color: #2c2c2c; margin: 0; padding: 0; font-size: 13pt; line-height: 1.4; }}
                .header-band {{ background-color: #6b2d18; color: white; padding: 18px 20px; border-radius: 8px; text-align: center; margin-bottom: 15px; }}
                .header-band h1 {{ margin: 0; font-size: 22pt; letter-spacing: 1px; }}
                .header-band p {{ margin: 5px 0 0 0; font-size: 11pt; color: #fbf5ee; font-style: italic; }}
                .top-grid {{ width: 100%; margin-bottom: 15px; border-collapse: collapse; }}
                .top-grid td {{ vertical-align: top; padding: 0; }}
                .meta-col {{ width: 48%; }}
                .image-col {{ width: 48%; height: 140px; }}
                .badge-grid {{ display: table; width: 100%; border-spacing: 8px; }}
                .badge-row {{ display: table-row; }}
                .badge {{ display: table-cell; width: 50%; background-color: white; border: 1px solid #e0d6cc; border-radius: 8px; padding: 8px 10px; font-size: 10pt; text-align: center; color: #4a4a4a; }}
                .badge strong {{ color: #c86414; display: block; font-size: 9pt; text-transform: uppercase; margin-bottom: 2px; }}
                .main-grid {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                .main-grid td {{ vertical-align: top; padding: 0; }}
                .left-col {{ width: 42%; padding-right: 12px; }}
                .right-col {{ width: 58%; padding-left: 12px; }}
                .section-title {{ color: #6b2d18; font-size: 12pt; font-weight: bold; border-bottom: 2px solid #d97724; padding-bottom: 4px; margin-top: 0; margin-bottom: 10px; text-transform: uppercase; }}
                .card-block {{ background-color: #fbf5ee; border-left: 4px solid #d97724; padding: 10px 12px; border-radius: 0 8px 8px 0; margin-bottom: 10px; font-size: 10.5pt; }}
                .step-card {{ background-color: #fbf5ee; border: 1px solid #ecdcd0; border-radius: 8px; padding: 10px 12px; margin-bottom: 10px; }}
                .step-title {{ color: #c86414; font-weight: bold; font-size: 11pt; margin-bottom: 4px; }}
                ul {{ margin: 0; padding-left: 18px; }}
                li {{ margin-bottom: 5px; }}
                .footer {{ margin-top: 25px; text-align: center; font-size: 9.5pt; color: #7c321a; font-weight: 500; border-top: 1px dashed #d97724; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="header-band">
                <h1>RECETTE GOURMANDE</h1>
                <p>Le partage des saveurs du terroir bourbonnais</p>
            </div>
            <table class="top-grid">
                <tr>
                    <td class="meta-col">
                        <div class="badge-grid">
                            <div class="badge-row">
                                <div class="badge"><strong>Difficulté</strong>Facile</div>
                                <div class="badge"><strong>Budget</strong>Abordable</div>
                            </div>
                            <div class="badge-row" style="height: 8px;"></div>
                            <div class="badge-grid">
                                <div class="badge"><strong>Préparation</strong>30 min</div>
                                <div class="badge"><strong>Cuisson</strong>45 min</div>
                            </div>
                        </div>
                    </td>
                    <td style="width: 4%;"></td>
                    <td class="image-col">{image_html}</td>
                </tr>
            </table>
            <table class="main-grid">
                <tr>
                    <td class="left-col">
                        <div class="section-title">Ingrédients & Ustensiles</div>
                        <div class="card-block">
                            <p><i>Voir le texte brut ci-dessous</i></p>
                        </div>
                    </td>
                    <td class="right-col">
                        <div class="section-title">Instructions de préparation</div>
                        <div class="step-card">
                            <div class="step-title">Détails de la recette</div>
                            <div>{recipe_text.replace('\n', '<br>')}</div>
                        </div>
                    </td>
                </tr>
            </table>
            <div class="footer">
                Fiche recette générée pour votre groupe "La Place du Village - ALLIER (03)" • Bon appétit !
            </div>
        </body>
        </html>
        """

        pdf_bytes = HTML(string=html_content).write_pdf()
        st.success("Fiche recette PDF générée avec succès !")
        st.download_button(
            label="📥 Télécharger le PDF de la recette",
            data=pdf_bytes,
            file_name="fiche_recette_place_du_village.pdf",
            mime="application/pdf"
        )
