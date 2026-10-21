# Liste officielle des catégories
categories_liste = ["Entrées", "Charcuteries", "Sauces", "Plat unique", "Viande", "Poisson", "Desserts", "Pâtes et pains", "Vins & Spiritueux", "Autres"]

# Options complètes incluant "Toutes"
options_categories = ["Toutes"] + categories_liste

# Gestion de l'état pour rendre la répartition cliquable
if "categorie_filtre" not in st.session_state:
    st.session_state.categorie_filtre = "Toutes"

# Recherche sécurisée de l'index actuel
index_actuel = options_categories.index(st.session_state.categorie_filtre) if st.session_state.categorie_filtre in options_categories else 0

# --- BARRE LATÉRALE : OPTIONS ---
st.sidebar.header("⚙️ Options")

categorie_filtre = st.sidebar.selectbox(
    "Filtrer par catégorie", 
    options_categories, 
    index=index_actuel,
    key="select_box_filtre"
)

# Synchronisation manuelle du selectbox si modifié via les boutons de répartition
if st.session_state.select_box_filtre != st.session_state.categorie_filtre:
    st.session_state.categorie_filtre = st.session_state.select_box_filtre

if st.sidebar.button("🔄 Rafraîchir la liste"):
    st.cache_data.clear()
    st.rerun()
