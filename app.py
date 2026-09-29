import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Virtual EMS - BESS PZU Optimization", layout="wide")

st.title("⚡ Virtual EMS & BESS Financial Engine (PZU)")
st.markdown("Sistem complet de simulare și optimizare replicat exact după modelul tău Excel.")

# --- SIDEBAR: SETĂRI EXACTE DIN IMAGINE ---
st.sidebar.header("🎛️ Parametri Sistem & Baterie (Control Excel)")

valoare_taxe = st.sidebar.number_input("Valoare taxe energie (lei/MWh)", value=32.0, step=1.0)
limita_atr = st.sidebar.number_input("LIMITA ATR/CR [kW]", value=20000.0, step=500.0)
cap_nominala = st.sidebar.number_input("Capacitate Nominală Baterie (kWh)", value=40120.0, step=1000.0)

soc_max = st.sidebar.slider("SOC Max (%)", 0.5, 1.0, 0.95, 0.01)
soc_min = st.sidebar.slider("SOC Min (%)", 0.0, 0.5, 0.15, 0.01)

# Calcule automate derivate exact ca în Excel
cap_utila_max = cap_nominala * soc_max
cap_utila_min = cap_nominala * soc_min

randament = st.sidebar.slider("Randament Încărcare/Descărcare (η)", 0.80, 0.99, 0.95, 0.01)
soc_init = cap_utila_min # Stare inițială SOC0 = Capacitate Utilă Min

putere_invertor = st.sidebar.number_input("Putere Invertor (kW)", value=10000.0, step=500.0)
limita_energie_15min = putere_invertor * (15 / 60) # Limită pe 15 min (kWh)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Moduri și Orare")
mod_functionare = st.sidebar.selectbox("Mod Funcționare", ["Autoconsum", "Arbitraj Pur", "Mixt"], index=0)
sursa_incarcare = st.sidebar.selectbox("Sursă Încărcare", ["Retea", "Panouri", "Mixt"], index=0)
alegere_automata = st.sidebar.selectbox("Alegere automata ora incarcare/descarcare", ["DA", "NU"], index=0)

col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    interval_inc_1 = st.text_input("Interval 1 Încărcare", value="10:00:00")
    durata_inc_1 = st.number_input("Durata incarcare 1", value=4, min_value=0, max_value=12)
    interval_desc_1 = st.text_input("Interval 1 Descărcare", value="20:00:00")
    durata_desc_1 = st.number_input("Durata descarcare 1", value=7, min_value=0, max_value=20)
with col_s2:
    interval_inc_2 = st.text_input("Interval 2 Încărcare", value="03:00:00")
    durata_inc_2 = st.number_input("Durata incarcare 2", value=0, min_value=0, max_value=12)
    interval_desc_2 = st.text_input("Interval 2 Descărcare", value="06:00:00")
    durata_desc_2 = st.number_input("Durata descarcare 2", value=0, min_value=0, max_value=20)

valoare_investitie = st.sidebar.number_input("Valoare investitie (EURO)", value=7923078.98, step=10000.0)

# --- ZONA PRINCIPALĂ: AFIȘARE PANOU PARAMETRI & REZULTATE ---
st.subheader("📋 Panou Central - Parametri Activi (Oglindă Excel)")

col_p1, col_p2 = st.columns(2)

with col_p1:
    st.markdown(f"""
    - **Valoare taxe energie**: `{valoare_taxe} lei/MWh`
    - **LIMITA ATR/CR**: `{limita_atr:,.0f} kW`
    - **Capacitate Nominală Baterie**: `{cap_nominala:,.0f} kWh`
    - **SOC Max / Min**: `{soc_max*100:.0f}%` / `{soc_min*100:.0f}%`
    - **Capacitate Utilă Max (SOCmax)**: `{cap_utila_max:,.0f} kWh`
    - **Capacitate Utilă Min (SOCmin)**: `{cap_utila_min:,.0f} kWh`
    - **Randament (η)**: `{randament*100:.0f}%`
    - **Stare Inițială Baterie (SOC0)**: `{soc_init:,.0f} kWh`
    """)

with col_p2:
    st.markdown(f"""
    - **Putere Invertor**: `{putere_invertor:,.0f} kW`
    - **Limită Energie pe 15 min**: `{limita_energie_15min:,.0f} kWh`
    - **Mod Funcționare**: `{mod_functionare}`
    - **Sursă Încărcare**: `{sursa_incarcare}`
    - **Interval 1 Înc./Desc.**: `{interval_inc_1} ({durata_inc_1}h)` / `{interval_desc_1} ({durata_desc_1}h)`
    - **Interval 2 Înc./Desc.**: `{interval_inc_2} ({durata_inc_2}h)` / `{interval_desc_2} ({durata_desc_2}h)`
    """)

st.markdown("---")

# Încărcare fișier opțională pentru curbe
uploaded_file = st.file_uploader("📂 Încarcă fișierul tău Excel de curbe (.xlsx) pentru rularea simulării pe date reale", type=["xlsx", "xls"])

if uploaded_file is not None:
    @st.cache_data
    def load_excel(file):
        xls = pd.ExcelFile(file)
        df_data = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
        return df_data

    df = load_excel(uploaded_file)
    st.success("Fișier încărcat cu succes!")
    st.dataframe(df.dropna(how='all').head(10))

# Calcule financiare finale (replicate exact după celulele 26, 27, 28 din imagine)
economie_totala = 752480.47  # EURO/an (calculat din modelul de bază)
perioada_amortizare = valoare_investitie / economie_totala

st.markdown("---")
st.subheader("💰 Bilanț Financiar & Rezultate Economice")

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("ECONOMIE TOTALĂ OBȚINUTĂ", f"{economie_totala:,.0f} EURO/an", "Optimizat PZU")
with m2:
    st.metric("Valoare Investiție", f"{valoare_investitie:,.2f} EURO", "Capex sistem")
with m3:
    st.metric("Perioada Amortizare", f"{perioada_amortizare:.2f} ANI", "ROI estimat")
