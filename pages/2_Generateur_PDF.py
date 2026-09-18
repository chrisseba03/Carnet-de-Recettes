import streamlit as st
import base64
from weasyprint import HTML
import pypdfium2 as pdfium

st.set_page_config(page_title="Générateur de Fiches PDF - Auto", page_icon="✨", layout="wide")

st.markdown("""
    <div style="background-color: #6b2d18; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 24px;">✨ Générateur Intelligent de Fiches Recettes</h1>
        <p style="margin: 5px 0 0 0; font-size: 14px; font-style: italic;">Pour votre groupe "La Place du Village - ALLIER (03)"</p>
    </div>
""", unsafe_allow_html=True)

with st.form("recipe_form"):
    st.subheader("1. 📂 Source de la recette (Import ou Texte libre)")
    
    uploaded_source_file = st.file_uploader(
        "Déposez un fichier PDF ou Texte (.txt) source (Optionnel)", 
        type=["pdf", "txt"],
        help="L'application va chercher à séparer les ingrédients et les étapes toute seule !"
    )
    
    recipe_text = st.text_area(
        "Ou collez votre texte brut ici :",
        height=200,
        placeholder="Collez votre recette. Astuce : vous pouvez inclure des mots comme 'INGRÉDIENTS :' et 'PRÉPARATION :' pour aider le tri automatique."
    )
    
    st.subheader("2. 📸 Photo de la Recette (Optionnel)")
    uploaded_image = st.file_uploader("Choisissez une image (JPG, PNG)", type=["jpg", "jpeg", "png"])
    
    submitted = st.form_submit_button("Générer la Fiche PDF Structurée")

# Récupération et traitement automatique du texte
texte_brut = recipe_text
if uploaded_source_file is not None:
    if uploaded_source_file.name.endswith('.txt'):
        try:
            texte_brut = uploaded_source_file.read().decode("utf-8")
        except:
            texte_brut = uploaded_source_file.read().decode("latin-1")
    elif uploaded_source_file.name.endswith('.pdf'):
        try:
            pdf_doc = pdfium.PdfDocument(uploaded_source_file.read())
            extracted_pages = [page.get_textpage().get_text_range() for page in pdf_doc]
            texte_brut = "\n".join(extracted_pages)
        except Exception:
            st.error("Erreur lors de la lecture automatique du PDF source.")

# Fonction d'extraction automatique des blocs
def extraire_sections(texte):
    # Valeurs par défaut
    titre = "RECETTE GOURMANDE DU TERROIR"
    ingredients = "• Non spécifié"
    ustensiles = "• Non spécifié"
    instructions = texte

    lignes = texte.split('\n')
    if lignes and len(lignes[0].strip()) > 3:
        titre = lignes[0].strip().upper()

    # Découpage basique par mots-clés si présents dans le texte
    texte_lower = texte.lower()
    
    # Extraction simplifiée des ingrédients si le mot-clé existe
    if "ingrédients" in texte_lower:
        try:
            partie_ing = texte[texte_lower.index("ingrédients"):]
            if "préparation" in partie_ing.lower():
                partie_ing = partie_ing[:partie_ing.lower().index("préparation")]
            ingredients = partie_ing.replace("INGRÉDIENTS", "").replace("Ingrédients", "").strip()
        except:
            pass

    if "instructions" in texte_lower or "préparation" in texte_lower:
        try:
            mot_cle = "instructions" if "instructions" in texte_lower else "préparation"
            partie_inst = texte[texte_lower.index(mot_cle):]
            instructions = partie_inst.replace("INSTRUCTIONS DE PRÉPARATION", "").replace("Instructions de préparation", "").replace("PRÉPARATION", "").strip()
        except:
            pass

    return titre, ingredients, ustensiles, instructions

if submitted:
    if not texte_brut.strip():
        st.warning("Veuillez importer un fichier ou coller du texte pour générer la fiche.")
    else:
        titre_recette, ingredients_recette, ustensiles_recette, instructions_recette = extraire_sections(texte_brut)

        image_html = ""
        if uploaded_image is not None:
            bytes_data = uploaded_image.getvalue()
            encoded_img = base64.b64encode(bytes_data).decode("utf-8")
            image_src = f"data:{uploaded_image.type};base64,{encoded_img}"
            image_html = f'<img src="{image_src}" style="width: 100%; height: 150px; object-fit: cover; border-radius: 6px; display: block;" />'
        else:
            image_html = '<div style="width: 100%; height: 150px; display: flex; align-items: center; justify-content: center; background-color: #fbf5ee; border-radius: 6px; border: 1px dashed #d97724; color: #7c321a; font-size: 28px;">🍲</div>'

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4; margin: 10mm; }}
                body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #fdfbf7; color: #2c2c2c; margin: 0; padding: 0; font-size: 9pt; line-height: 1.3; }}
                .header {{ background-color: #6b2d18; color: white; text-align: center; padding: 10px 15px; border-radius: 6px; margin-bottom: 8px; }}
                .header h1 {{ margin: 0; font-size: 15pt; text-transform: uppercase; letter-spacing: 0.5px; }}
                .header p {{ margin: 2px 0 0 0; font-size: 8.5pt; font-style: italic; color: #fbf5ee; }}
                
                .top-section {{ width: 100%; display: table; margin-bottom: 8px; }}
                .meta-col {{ display: table-cell; width: 55%; vertical-align: top; padding-right: 8px; }}
                .image-col {{ display: table-cell; width: 45%; vertical-align: top; text-align: right; }}
                
                .badge-grid {{ width: 100%; border-collapse: separate; border-spacing: 4px; }}
                .badge {{ background: white; border: 1px solid #d9c5b2; border-radius: 4px; padding: 5px 6px; font-size: 8pt; text-align: center; color: #4a4a4a; }}
                .badge strong {{ color: #c86414; display: block; font-size: 7pt; text-transform: uppercase; margin-bottom: 1px; }}

                .main-grid {{ width: 100%; display: table; margin-bottom: 8px; }}
                .left-col {{ display: table-cell; width: 40%; vertical-align: top; padding-right: 6px; }}
                .right-col {{ display: table-cell; width: 60%; vertical-align: top; }}

                .card {{ background: white; border: 1px solid #ecdcd0; border-radius: 6px; padding: 8px 10px; margin-bottom: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); }}
                .section-title {{ color: #6b2d18; font-size: 9pt; font-weight: bold; border-bottom: 2px solid #d97724; padding-bottom: 2px; margin-bottom: 5px; text-transform: uppercase; }}
                
                .footer {{ text-align: center; font-size: 8pt; color: #7c321a; font-weight: 500; border-top: 1px dashed #d97724; padding-top: 4px; margin-top: 4px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{titre_recette}</h1>
                <p>Le partage des saveurs du terroir bourbonnais</p>
            </div>
            
            <div class="top-section">
                <div class="meta-col">
                    <table class="badge-grid">
                        <tr>
                            <td class="badge"><strong>Style</strong>Traditionnel</td>
                            <td class="badge"><strong>Qualité</strong>Fait Maison</td>
                        </tr>
                        <tr>
                            <td class="badge" colspan="2"><strong>Communauté</strong>La Place du Village - Allier (03)</td>
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
                        <div style="white-space: pre-line; font-size: 8.5pt;">{ingredients_recette}</div>
                    </div>
                </div>
                <div class="right-col">
                    <div class="card">
                        <div class="section-title">Instructions de préparation</div>
                        <div style="white-space: pre-line; font-size: 8.5pt;">{instructions_recette}</div>
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
        st.success("Fiche structurée automatiquement avec succès !")
        st.download_button(
            label="📥 Télécharger la fiche PDF triée",
            data=pdf_bytes,
            file_name="fiche_recette_triee.pdf",
            mime="application/pdf"
        )
