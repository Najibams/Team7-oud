# %%


# %%
import pandas as pd
import streamlit as st
import requests
import plotly.express as px
from scipy import stats
 
# **Titel van het dashboard**
st.set_page_config(page_title="CBS Demografische Data Analyse", layout="wide")
st.title("📊 CBS Demografische Data Analyse")
st.subheader("Analyseer en vergelijk welzijns- en tevredenheidsstatistieken per groep")
 
# **Pagina navigatie**
st.sidebar.title("📌 Navigatie")
st.sidebar.markdown("<h1 style='color: red;'>TEAM 7</h1>", unsafe_allow_html=True)
page = st.sidebar.radio("Ga naar:", ["KPI's en Inzichten", "Lijnplot", "Histogram", "Boxplot", "Sunburst", "Statistische Analyse"])
 
# **Base URL van de CBS API**
base_url = "https://opendata.cbs.nl/ODataApi/OData/85542ENG/TypedDataSet"
 
# **Functie om data van CBS API op te halen**
@st.cache_data
def get_cbs_data():
    response = requests.get(base_url)
    if response.status_code == 200:
        data = response.json()
        return pd.DataFrame(data.get("value", []))  
    else:
        st.error(f"Fout bij ophalen van data. Statuscode: {response.status_code}")
        return None
 
# **Data ophalen**
df = get_cbs_data()
 
# **Laad de nieuwe CSV-bestand**
new_df = pd.read_csv("bestandextra.csv", sep=';')
 
# Verwerk de nieuwe DataFrame om de "Kenmerken" kolom toe te voegen
new_df["Kenmerken"] = "Team 7"  # Voeg hier de relevante waarde toe
 
# **Mapping van codes naar kenmerken**
mapping = {
    'T009002': 'Total persons',
    '3000': 'Male',
    '4000': 'Female',
    '53105': '18-24 years',
    '53500': '25-34 years',
    '53700': '35-44 years',
    '53800': '45-54 years',
    '53900': '55-64 years',
    '53925': '65+ years',
    '21600': 'No education',
    '2018710': 'Primary education',
    '2018720': 'Secondary education',
    '2018750': 'Higher education',
    '2018800': 'Vocational training',
    '2018810': 'Other education'
}
 
if df is not None and not df.empty:
    # **Data Verkenning - Alleen zichtbaar in Spyder**
    print("Unieke kolomnamen in de dataset:", df.columns.unique())
    # Verwijder rijen met ontbrekende waarden of vul ze in
    df = df.dropna()  # Of gebruik df.fillna(df.mean(), inplace=True) om in te vullen
 
    # Selecteer alleen de relevante kolommen
    relevante_kolommen = ['ID','Kenmerken', 'Perioden', 'ScoreHappiness_1', 'ScoreWorkSatisfaction_13', 
                          'ScoreSatisfactionMentalHealth_29', 'ScoreSatisfactionSocialLife_57', 
                          'ScoreSatisfactionDailyActivities_21']
    df = df[relevante_kolommen]
    df["Kenmerken"] = df["Kenmerken"].astype(str).str.strip()
    df = df[df["Kenmerken"].isin(mapping.keys())]  
    df["Kenmerken"] = df["Kenmerken"].map(mapping)  
    df["Perioden"] = df["Perioden"].astype(str).str[:4].astype(int)
 
    # Voeg de nieuwe DataFrame toe aan de bestaande DataFrame
    combined_df = pd.concat([df, new_df], ignore_index=True)
 
    # **Nieuwe variabelen**
    combined_df["TotaalTevredenheid"] = (combined_df["ScoreHappiness_1"] + 
                                          combined_df["ScoreWorkSatisfaction_13"] + 
                                          combined_df["ScoreSatisfactionMentalHealth_29"] + 
                                          combined_df["ScoreSatisfactionSocialLife_57"] + 
                                          combined_df["ScoreSatisfactionDailyActivities_21"]) / 5
 
    # **Categorieën verdelen voor filters**
    categorieën = {
        "Onderwijsniveau": ["No education", "Primary education", "Secondary education", "Higher education", 
                            "Vocational training", "Other education", "Team 7"]
    }
 
    # **Sidebar met filters**
    st.sidebar.header("📌 Filters")
    selected_education = st.sidebar.multiselect("Kies onderwijsniveau:", categorieën["Onderwijsniveau"], default=categorieën["Onderwijsniveau"])
 
    min_jaar = combined_df["Perioden"].min()
    max_jaar = combined_df["Perioden"].max()
    selected_jaar = st.sidebar.slider("Selecteer een jaar:", min_jaar, max_jaar, (min_jaar, max_jaar))
 
    meting_titels = {
        "ScoreHappiness_1": "Geluksscore",
        "ScoreWorkSatisfaction_13": "Werktevredenheid",
        "ScoreSatisfactionMentalHealth_29": "Mentale Gezondheid",
        "ScoreSatisfactionSocialLife_57": "Tevredenheid Sociaal Leven",
        "ScoreSatisfactionDailyActivities_21": "Tevredenheid Dagelijkse Activiteiten",
        "TotaalTevredenheid": "Totaal Tevredenheid"  # Nieuwe variabele toegevoegd
    }
 
    selected_meting_raw = st.sidebar.selectbox("Kies een meting:", list(meting_titels.values()))
    selected_meting = {v: k for k, v in meting_titels.items()}[selected_meting_raw]
 
    # **Dataset filteren**
    filtered_df = combined_df[
        (combined_df["Perioden"].between(selected_jaar[0], selected_jaar[1])) &
        (combined_df["Kenmerken"].isin(selected_education))
    ]
 
    # **Pagina-weergave**
    if not filtered_df.empty:
        if page == "KPI's en Inzichten":
            st.header("📊 Key Performance Indicators (KPI's) en Statistieken")
            kpi1 = filtered_df[selected_meting].mean()
            kpi2 = filtered_df[selected_meting].max()
            kpi3 = filtered_df[selected_meting].min()
            std_dev = filtered_df[selected_meting].std()
            median = filtered_df[selected_meting].median()
 
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Gemiddelde Score", f"{kpi1:.2f}")
            col2.metric("Maximale Score", f"{kpi2:.2f}")
            col3.metric("Minimale Score", f"{kpi3:.2f}")
            col4.metric("Standaardafwijking", f"{std_dev:.2f}")
            col5.metric("Mediaan", f"{median:.2f}")
 
        elif page == "Lijnplot":
            df_avg = filtered_df.groupby(["Perioden", "Kenmerken"])[selected_meting].mean().reset_index()
            fig = px.line(df_avg, x="Perioden", y=selected_meting, color="Kenmerken", markers=True)
            fig.update_layout(yaxis_title="Score")  # Algemeen label
            st.plotly_chart(fig)
 
        elif page == "Histogram":
            fig = px.histogram(filtered_df, x=selected_meting, color="Kenmerken", nbins=20, marginal="box")
            fig.update_layout(yaxis_title="Aantal")  # Algemeen label
            st.plotly_chart(fig)
 
        elif page == "Boxplot":
            fig = px.box(filtered_df, x="Kenmerken", y=selected_meting, color="Kenmerken")
            fig.update_layout(yaxis_title="Score")  # Algemeen label
            st.plotly_chart(fig)
 
        elif page == "Sunburst":
            fig = px.sunburst(filtered_df, path=["Kenmerken", "Perioden"], values=selected_meting,
                              color=selected_meting, color_continuous_scale="greens")
            st.plotly_chart(fig)
 
        elif page == "Statistische Analyse":
            st.header("📈 Statistische Analyse")
            if len(selected_education) > 1:
                # Verdeel de data op basis van geselecteerde kenmerken
                groups = [filtered_df[filtered_df["Kenmerken"] == edu][selected_meting] for edu in selected_education]
                # Controleer of er genoeg data is voor statistische analyse
                if all(len(group) > 1 for group in groups):
                    # Voer een t-toets uit
                    t_stat, p_value = stats.ttest_ind(groups[0], groups[1], equal_var=False)  # Twee groepen vergelijken
                    st.write(f"T-statistiek: {t_stat:.2f}, P-waarde: {p_value:.4f}")
                    if p_value < 0.05:
                        st.success("Er is een significant verschil tussen de groepen.")
                    else:
                        st.warning("Er is geen significant verschil tussen de groepen.")
                else:
                    st.warning("Niet genoeg gegevens voor statistische analyse.")
            else:
                st.warning("Selecteer minimaal twee groepen voor de statistische analyse.")
    else:
        st.warning("Geen gegevens beschikbaar voor de geselecteerde filters.")
 
else:
    st.error("❌ Kon geen gegevens ophalen. Controleer de API-status.")

# %%



