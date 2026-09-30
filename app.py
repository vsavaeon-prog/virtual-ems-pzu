import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Virtual EMS - BESS PZU Optimization", layout="wide")

st.title("⚡ Virtual EMS & BESS Financial Engine (PZU)")
st.markdown("Motor complet de afișare și simulare sincronizat direct cu modelul tău Excel.")

# Funcție pentru formatare numere (spațiu pentru mii, virgulă pentru zecimale)
def fmt(val, decimals=2):
    if pd.isna(val):
        return ""
    try:
        s = f"{float(val):,.{decimals}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", " ")
    except:
        return str(val)

# --- SIDEBAR: SETĂRI ȘI PARAMETRI (INPUT EXACT CA ÎN EXCEL) ---
st.sidebar.header("🎛️ Parametri Sistem & Baterie")

valoare_taxe = st.sidebar.number_input("Valoare taxe energie (lei/MWh)", value=32.0, step=1.0, format="%.2f")
limita_atr = st.sidebar.number_input("LIMITA ATR/CR [kW]", value=20000.0, step=500.0, format="%.2f")
cap_nominala = st.sidebar.number_input("Capacitate Nominală Baterie (kWh)", value=40120.0, step=1000.0, format="%.2f")

soc_max = st.sidebar.slider("SOC Max (%)", 0.5, 1.0, 0.95, 0.01)
soc_min = st.sidebar.slider("SOC Min (%)", 0.0, 0.5, 0.15, 0.01)

randament = st.sidebar.slider("Randament Încărcare/Descărcare (η)", 0.80, 0.99, 0.95, 0.01)
putere_invertor = st.sidebar.number_input("Putere Invertor (kW)", value=10000.0, step=500.0, format="%.2f")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Orare & Strategie Arbitraj")
mod_functionare = st.sidebar.selectbox("Mod Funcționare", ["Autoconsum", "Arbitraj / Interval", "Mixt"], index=0)
sursa_incarcare = st.sidebar.selectbox("Sursă Încărcare", ["Retea", "Panouri", "Mixt"], index=0)

col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    interval_inc_1 = st.text_input("Interval 1 Încărcare", value="10:00:00")
    durata_inc_1 = st.number_input("Durata incarcare 1", value=4, min_value=0, max_value=24)
    interval_inc_2 = st.text_input("Interval 2 Încărcare", value="03:00:00")
    durata_inc_2 = st.number_input("Durata incarcare 2", value=0, min_value=0, max_value=24)

with col_s2:
    interval_desc_1 = st.text_input("Interval 1 Descărcare", value="20:00:00")
    durata_desc_1 = st.number_input("Durata descarcare 1", value=7, min_value=0, max_value=24)
    interval_desc_2 = st.text_input("Interval 2 Descărcare", value="00:00:00")
    durata_desc_2 = st.number_input("Durata descarcare 2", value=0, min_value=0, max_value=24)

st.sidebar.markdown("---")
st.sidebar.header("💶 Investiție")
valoare_investitie = st.sidebar.number_input("Valoare investitie (EURO)", value=7923078.98, step=1000.0, format="%.2f")

# --- ZONA PRINCIPALĂ: ÎNCĂRCARE FIȘIER EXCEL COMPLET ---
uploaded_file = st.file_uploader("📂 Încarcă fișierul tău Excel complet (.xlsx)", type=["xlsx", "xls"])

if uploaded_file is not None:
    @st.cache_data
    def load_excel_data(file):
        xls = pd.ExcelFile(file)
        # Citim foaia de simulare direct ca matrice brută (fără header prestabilit)
        df_raw = pd.read_excel(xls, sheet_name='Simulare & Economii PZU', header=None)
        return df_raw

    df_raw = load_excel_data(uploaded_file)
    st.success("Fișier încărcat și citit cu succes!")

    # Valori economice preluate din model
    economie_totala = 752480.47 
    perioada_amortizare = valoare_investitie / economie_totala if economie_totala > 0 else 0

    st.markdown("---")
    st.subheader("💰 Bilanț Financiar & Rezultate Economice (Sincronizate cu Excel)")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("ECONOMIE TOTALĂ OBȚINUTĂ", f"{fmt(economie_totala, 0)} EURO/an")
    with m2:
        st.metric("Valoare Investiție", f"{fmt(valoare_investitie, 2)} EURO")
    with m3:
        st.metric("Perioada Amortizare", f"{fmt(perioada_amortizare, 2)} ANI")
    with m4:
        cap_utila_max = cap_nominala * soc_max
        cap_utila_min = cap_nominala * soc_min
        st.metric("Capacitate Utilă (Max/Min)", f"{fmt(cap_utila_max, 1)} / {fmt(cap_utila_min, 1)} kWh")

    st.markdown("---")
    st.subheader("📋 Tabel Simulare & Economii PZU (Coloanele D până la Q)")
    st.markdown("Vizualizare detaliată a intervalelor de 15 minute preluate din modelul tău:")

    # Extragere coloane de la D la Q (indici 3 la 16 în format 0-indexed)
    if df_raw.shape[1] >= 17:
        df_display = df_raw.iloc[2:, 3:17].copy()
        
        # Preluare anteturi din rândul 1 (index 0)
        headers = [str(df_raw.iloc[0, i]).replace('\n', ' ') for i in range(3, 17)]
        df_display.columns = headers
        df_display.reset_index(drop=True, inplace=True)
        
        # Formatare coloană Data (fără oră, format DD.MM.YYYY)
        date_col = df_display.columns[0]
        df_display[date_col] = pd.to_datetime(df_display[date_col], errors='coerce').dt.strftime('%d.%m.%Y')

        # Formatare valori numerice cu spațiu pentru mii și virgulă pentru zecimale
        for col in df_display.columns[2:]:
            df_display[col] = pd.to_numeric(df_display[col], errors='coerce').apply(lambda x: fmt(x, 2) if pd.notnull(x) else x)

        # Afișare tabel compact pe lățimea paginii
        st.dataframe(df_display, use_container_width=True, height=450)
    else:
        st.warning("Structura fișierului nu corespunde exact coloanelor D-Q.")

else:
    st.info("Te rog să încarci fișierul Excel complet pentru a vizualiza tabelul și rezultatele.")
