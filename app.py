import io
import json
import re
import unicodedata
from google.oauth2 import service_account
from googleapiclient.discovery import build
import google.auth.transport.requests
from PIL import Image
import pypdfium2 as pdfium
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
import requests
import streamlit as st

st.set_page_config(
    page_title="Nos Recettes de Cuisine", page_icon="👨‍🍳", layout="wide"
)
st.title("👨‍🍳 Le Carnet de Recettes de la Maison")

# --- NORMALISATION ---


def normaliser_texte(texte):
  if not texte:
    return ""
  texte = (
      texte.replace("œ", "oe")
      .replace("Œ", "oe")
      .replace("æ", "ae")
      .replace("Æ", "ae")
  )
  texte = unicodedata.normalize("NFD", texte)
  texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
  texte = texte.lower()
  return texte


def normaliser_mot_cle(texte):
  texte = normaliser_texte(texte)
  return re.sub(r"[^a-z0-9]", "", texte)


# --- MAPPING ---
MAPPING_CATEGORIES = {
    "Entrées": ["entree", "entrees"],
    "Charcuteries": [
        "charcuterie",
        "charcuteries",
        "salaison",
        "salaisons",
    ],
    "Sauces": [
        "sauce",
        "sauces",
        "vinaigrette",
        "vinaigrettes",
        "marinade",
        "marinades",
        "condiment",
        "condiments",
    ],
    "Plats": ["plat", "plats"],
    "Desserts": ["dessert", "desserts", "douceur", "douceurs"],
    "Pains & Pâtisseries": [
        "pain",
        "pains",
        "patisserie",
        "patisseries",
        "boulangerie",
        "brioche",
        "brioches",
    ],
    "Vins & Spiritueux": [
        "vin",
        "vins",
        "spiritueux",
        "boisson",
        "boissons",
        "apero",
        "aperitif",
        "aperitifs",
        "cave",
        "cocktail",
        "cocktails",
    ],
}


def identifier_categories_balise(balise):
  clean = normaliser_mot_cle(balise)
  cats_trouvees = []
  for cat_officielle, mots_cles in MAPPING_CATEGORIES.items():
    for mot in mots_cles:
      if clean == mot or clean == mot + "s" or mot in clean:
        cats_trouvees.append(cat_officielle)
        break
  return cats_trouvees


# --- CONNEXION GOOGLE DRIVE ---
@st.cache_resource
def get_drive_service():
  scopes = [
      "https://www.googleapis.com/auth/drive.file",
      "https://www.googleapis.com/auth/drive",
  ]
  creds = service_account.Credentials.from_service_account_info(
      st.secrets["gcp_service_account"], scopes=scopes
  )
  session = requests.Session()
  auth_request = google.auth.transport.requests.Request(session=session)
  creds.refresh(auth_request)
  return build("drive", "v3", credentials=creds), creds


try:
  drive_service, creds = get_drive_service()
  FOLDER_ID = st.secrets["FOLDER_ID"]
except Exception as e:
  st.error(
      "Erreur de connexion à Google Drive. Vérifiez la configuration dans les"
      " Secrets."
  )
  st.stop()


@st.cache_data(ttl=600)
def get_all_recipes():
  fichiers = []
  page_token = None
  query = (
      f"'{FOLDER_ID}' in parents and trashed = false and mimeType ="
      " 'application/pdf'"
  )

  while True:
    response = (
        drive_service.files()
        .list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageSize=1000,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            pageToken=page_token,
        )
        .execute()
    )

    fichiers.extend(response.get("files", []))
    page_token = response.get("nextPageToken", None)

    if page_token is None:
      break

  return fichiers


try:
  fichiers_bruts = get_all_recipes()
except Exception:
  st.error(
      "Petite baisse de réseau avec Google Drive. Cliquez sur 'Rafraîchir la"
      " liste'."
  )
  st.stop()

fichiers_pdf = [f for f in fichiers_bruts if f["name"].lower().endswith(".pdf")]
total_recettes = len(fichiers_pdf)
categories_liste = [
    "Entrées",
    "Charcuteries",
    "Sauces",
    "Plats",
    "Desserts",
    "Pains & Pâtisseries",
    "Vins & Spiritueux",
    "Autres",
]


# --- FONCTION DE GÉNÉRATION DE FICHE RECETTE PDF ---
def generer_pdf_recette(
    titre,
    desc,
    diff,
    bud,
    prep,
    rep,
    img_uploaded,
    ings,
    usts,
    insts,
    asts,
    vars_,
):
  buffer = io.BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=A4,
      rightMargin=25,
      leftMargin=25,
      topMargin=25,
      bottomMargin=25,
  )
  elements = []

  color_primary = colors.HexColor("#7c321a")
  color_accent = colors.HexColor("#c86414")

  style_title = ParagraphStyle(
      "TitleStyle",
      fontName="Helvetica-Bold",
      fontSize=15,
      textColor=colors.white,
      alignment=1,
      spaceAfter=4,
  )
  style_subtitle = ParagraphStyle(
      "SubTitleStyle",
      fontName="Helvetica-Oblique",
      fontSize=9,
      textColor=colors.white,
      alignment=1,
  )
  style_body = ParagraphStyle(
      "BodyStyle",
      fontName="Helvetica",
      fontSize=8.5,
      textColor=colors.HexColor("#333333"),
      leading=11,
  )
  style_meta_val = ParagraphStyle(
      "MetaVal",
      fontName="Helvetica-Bold",
      fontSize=8.5,
      textColor=color_accent,
      alignment=1,
  )
  style_meta_lbl = ParagraphStyle(
      "MetaLbl",
      fontName="Helvetica",
      fontSize=6.5,
      textColor=colors.HexColor("#666666"),
      alignment=1,
  )

  # En-tête bandeau
  header_data = [[Paragraph(titre.upper(), style_title)], [Paragraph(desc, style_subtitle)]]
  header_table = Table(header_data, colWidths=[540])
  header_table.setStyle(
      TableStyle([
          ("BACKGROUND", (0, 0), (-1, -1), color_primary),
          ("TOPPADDING", (0, 0), (-1, -1), 8),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
          ("ALIGN", (0, 0), (-1, -1), "CENTER"),
      ])
  )
  elements.append(header_table)
  elements.append(Spacer(1, 8))

  # Grille Métadonnées & Image
  meta_content = [
      [
          Paragraph("DIFFICULTÉ", style_meta_lbl),
          Paragraph("BUDGET", style_meta_lbl),
      ],
      [
          Paragraph(diff, style_meta_val),
          Paragraph(bud, style_meta_val),
      ],
      [
          Paragraph("PRÉPARATION", style_meta_lbl),
          Paragraph("REPOS / POUSSE", style_meta_lbl),
      ],
      [
          Paragraph(prep, style_meta_val),
          Paragraph(rep, style_meta_val),
      ],
  ]
  meta_table = Table(meta_content, colWidths=[110, 110])
  meta_table.setStyle(
      TableStyle([
          ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fbf5ee")),
          ("BOX", (0, 0), (-1, -1), 1, color_accent),
          ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5dccb")),
          ("TOPPADDING", (0, 0), (-1, -1), 4),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
      ])
  )

  if img_uploaded is not None:
    img_pil = Image.open(img_uploaded)
    img_byte_arr = io.BytesIO()
    img_pil.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)
    recipe_image = RLImage(img_byte_arr, width=300, height=105)
  else:
    recipe_image = Paragraph(
        "<i>Aucune illustration</i>", style_subtitle
    )

  top_grid = Table([[meta_table, recipe_image]], colWidths=[230, 310])
  top_grid.setStyle(
      TableStyle([
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("ALIGN", (1, 0), (1, 0), "CENTER"),
      ])
  )
  elements.append(top_grid)
  elements.append(Spacer(1, 10))

  # Corps 2 colonnes
  col_gauche_text = f"<b>INGRÉDIENTS :</b><br/>{ings.replace('\n', '<br/>')}<br/><br/><b>USTENSILES :</b><br/>{usts.replace('\n', '<br/>')}"
  col_droite_text = f"<b>INSTRUCTIONS DE PRÉPARATION :</b><br/><br/>{insts.replace('\n', '<br/><br/>')}"

  p_gauche = Paragraph(col_gauche_text, style_body)
  p_droite = Paragraph(col_droite_text, style_body)

  body_table = Table([[p_gauche, p_droite]], colWidths=[200, 340])
  body_table.setStyle(
      TableStyle([
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("
