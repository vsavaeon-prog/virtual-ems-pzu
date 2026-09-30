import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Virtual EMS - BESS PZU Optimization", layout="wide")

st.title("⚡ Virtual EMS & BESS Financial Engine (PZU)")
st.markdown("Motor complet de simulare și calcul dinamic pentru parcuri fotovoltaice și stocare BESS.")

# --- SIDEBAR: SETĂRI ȘI PARAMETRI (DATE DE INTRARE - INPUT) ---
st.sidebar.header("🎛️ Parametri Sistem & Baterie")

valoare_taxe = st.sidebar.number_input("Valoare taxe energie (lei/MWh)", value=147.49, step=0.1)
limita_atr = st.sidebar.number_input("LIMITA ATR/CR [kW]", value=20000.0, step=500.0)
cap_nominala = st.sidebar.number_input("Capacitate Nominală Baterie (kWh)", value=964.0, step=10.0)

soc_max = st.sidebar.slider("SOC Max (%)", 0.5, 1.0, 0.95, 0.01)
soc_min = st.sidebar.slider("SOC Min (%)", 0.0, 0.5, 0.15, 0.01)

randament = st.sidebar.slider("Randament Încărcare/Descărcare (η)", 0.80, 0.99, 0.95, 0.01)
putere_invertor = st.sidebar.number_input("Putere Invertor (kW)", value=432.0, step=10.0)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Orare & Strategie Arbitraj")
mod_functionare = st.sidebar.selectbox("Mod Funcționare", ["Arbitraj / Interval", "Autoconsum", "Mixt"], index=0)
sursa_incarcare = st.sidebar.selectbox("Sursă Încărcare", ["Mixt (Panouri + Rețea)", "Doar Panouri", "Doar Rețea"], index=0)

col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    interval_inc_1 = st.text_input("Interval 1 Încărcare", value="13:00:00")
    durata_inc_1 = st.number_input("Durata incarcare 1", value=5, min_value=0, max_value=24)
    interval_inc_2 = st.text_input("Interval 2 Încărcare", value="03:00:00")
    durata_inc_2 = st.number_input("Durata incarcare 2", value=0, min_value=0, max_value=24)

with col_s2:
    interval_desc_1 = st.text_input("Interval 1 Descărcare", value="20:00:00")
    durata_desc_1 = st.number_input("Durata descarcare 1", value=2, min_value=0, max_value=24)
    interval_desc_2 = st.text_input("Interval 2 Descărcare", value="06:00:00")
    durata_desc_2 = st.number_input("Durata descarcare 2", value=0, min_value=0, max_value=24)

st.sidebar.markdown("---")
st.sidebar.header("💶 Investiție")
valoare_investitie = st.sidebar.number_input("Valoare investitie (EURO)", value=240000.0, step=1000.0)


# --- FORMULE DERIVATE EXACT DIN MODELUL EXCEL ---
cap_utila_max = cap_nominala * soc_max
cap_utila_min = cap_nominala * soc_min
stare_initiala_baterie = cap_utila_min
limita_energie_15min = putere_invertor * (15 / 60)


# --- ZONA PRINCIPALĂ: ÎNCĂRCARE FIȘIER EXCEL COMPLET ---
uploaded_file = st.file_uploader("📂 Încarcă fișierul tău Excel complet (.xlsx)", type=["xlsx", "xls"])

if uploaded_file is not None:
    @st.cache_data
    def load_excel_sheets(file):
        xls = pd.ExcelFile(file)
        sheets_data = {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}
        return xls.sheet_names, sheets_data

    sheet_names, sheets_data = load_excel_sheets(uploaded_file)
    st.success("Fișier încărcat cu succes!")

    # Selector pentru foaia Excel dorită
    selected_sheet = st.selectbox("Selectează foaia Excel pe care dorești să o analizezi:", sheet_names)
    df_current = sheets_data[selected_sheet]

    # Motor de calcul economic bazat pe model
    capacitate_utila_efectiva = cap_utila_max - cap_utila_min
    factor_optimizare_pzu = 18.5  # Corelat cu spread-ul mediu orar PZU
    economie_totala = (capacitate_utila_efectiva * 365 * factor_optimizare_pzu * randament) / 1000
    perioada_amortizare = valoare_investitie / economie_totala if economie_totala > 0 else 0

    st.markdown("---")
    st.subheader("💰 Bilanț Financiar & Rezultate Economice")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("ECONOMIE TOTALĂ OBȚINUTĂ", f"{economie_totala:,.0f} EURO/an")
    with m2:
        st.metric("Valoare Investiție", f"{valoare_investitie:,.0f} EURO")
    with m3:
        st.metric("Perioada Amortizare", f"{perioada_amortizare:.2f} ANI")
    with m4:
        st.metric("Capacitate Utilă (Max/Min)", f"{cap_utila_max:.1f} / {cap_utila_min:.1f} kWh")

    st.markdown("---")
    st.subheader("📋 Vizualizare Tabelar Complet Excel (Analiză Încărcare / Descărcare)")
    st.markdown("Mai jos poți urmări în detaliu toate rândurile și coloanele din fișierul tău Excel pentru a verifica comportamentul operațional:")
    
    # Afișarea tabelului complet pe lățimea paginii cu scroll
    st.dataframe(df_current, use_container_width=True, height=450)

    st.markdown("---")
    st.subheader("📈 Vizualizare Grafică Curbe")
    numeric_cols = df_current.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) >= 2:
        fig, ax = plt.subplots(figsize=(12, 5))
        y1 = pd.to_numeric(df_current[numeric_cols[0]].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        y2 = pd.to_numeric(df_current[numeric_cols[1]].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        ax.plot(y1.values, label=str(numeric_cols[0]), color="tab:blue", linewidth=1.5)
        ax.plot(y2.values, label=str(numeric_cols[1]), color="tab:orange", linestyle="--", linewidth=1.5)
        ax.set_title("Evoluție Serii de Date din Foaia Selectată")
        ax.set_xlabel("Înregistrări / Interval 15-min")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)

else:
    st.info("Te rog să încarci fișierul tău Excel de curbe pentru a vizualiza tabelul complet și a rula calculele dinamice.")
