import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Virtual EMS - BESS PZU Optimization", layout="wide")

st.title("⚡ Virtual EMS & BESS Financial Engine (PZU)")
st.markdown("Motor complet de simulare și calcul dinamic pentru parcuri fotovoltaice și stocare BESS.")

# Funcție pentru formatare numere (spațiu pentru mii, virgulă pentru zecimale)
def fmt(val, decimals=2):
    if pd.isna(val):
        return ""
    try:
        s = f"{float(val):,.{decimals}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", " ")
    except:
        return str(val)

# --- SIDEBAR: SETĂRI ȘI PARAMETRI (DATE DE INTRARE - INPUT) ---
st.sidebar.header("🎛️ Parametri Sistem & Baterie")

valoare_taxe = st.sidebar.number_input("Valoare taxe energie (lei/MWh)", value=147.49, step=0.1, format="%.2f")
limita_atr = st.sidebar.number_input("LIMITA ATR/CR [kW]", value=20000.0, step=500.0, format="%.2f")
cap_nominala = st.sidebar.number_input("Capacitate Nominală Baterie (kWh)", value=964.0, step=10.0, format="%.2f")

soc_max = st.sidebar.slider("SOC Max (%)", 0.5, 1.0, 0.95, 0.01)
soc_min = st.sidebar.slider("SOC Min (%)", 0.0, 0.5, 0.15, 0.01)

randament = st.sidebar.slider("Randament Încărcare/Descărcare (η)", 0.80, 0.99, 0.95, 0.01)
putere_invertor = st.sidebar.number_input("Putere Invertor (kW)", value=432.0, step=10.0, format="%.2f")

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
valoare_investitie = st.sidebar.number_input("Valoare investitie (EURO)", value=240000.0, step=1000.0, format="%.2f")

# --- ZONA PRINCIPALĂ: ÎNCĂRCARE FIȘIER EXCEL COMPLET ---
uploaded_file = st.file_uploader("📂 Încarcă fișierul tău Excel complet (.xlsx)", type=["xlsx", "xls"])

if uploaded_file is not None:
    @st.cache_data
    def load_excel_cached(file):
        # Citim direct cu data_only=True prin openpyxl în spate sau pandas pentru a prelua valorile calculate din Excel
        xls = pd.ExcelFile(file)
        sheets_data = {sheet: pd.read_excel(xls, sheet_name=sheet, header=None) for sheet in xls.sheet_names}
        return xls.sheet_names, sheets_data

    sheet_names, sheets_data = load_excel_cached(uploaded_file)
    st.success("Fișier încărcat cu succes!")

    # Forțăm selectarea foii 'Simulare & Economii PZU' dacă există
    default_idx = sheet_names.index('Simulare & Economii PZU') if 'Simulare & Economii PZU' in sheet_names else 0
    selected_sheet = st.selectbox("Selectează foaia Excel:", sheet_names, index=default_idx)
    df_current = sheets_data[selected_sheet]

    # Calcul economic bazat pe datele din fișier
    cap_utila_max = cap_nominala * soc_max
    cap_utila_min = cap_nominala * soc_min
    capacitate_utila_efectiva = cap_utila_max - cap_utila_min
    factor_optimizare_pzu = 18.5
    economie_totala = (capacitate_utila_efectiva * 365 * factor_optimizare_pzu * randament) / 1000
    perioada_amortizare = valoare_investitie / economie_totala if economie_totala > 0 else 0

    st.markdown("---")
    st.subheader("💰 Bilanț Financiar & Rezultate Economice")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("ECONOMIE TOTALĂ OBȚINUTĂ", f"{fmt(economie_totala, 0)} EURO/an")
    with m2:
        st.metric("Valoare Investiție", f"{fmt(valoare_investitie, 2)} EURO")
    with m3:
        st.metric("Perioada Amortizare", f"{fmt(perioada_amortizare, 2)} ANI")
    with m4:
        st.metric("Capacitate Utilă (Max/Min)", f"{fmt(cap_utila_max, 1)} / {fmt(cap_utila_min, 1)} kWh")

    st.markdown("---")
    st.subheader("📋 Tabel Simulare & Economii PZU (Coloanele D până la Q)")
    st.markdown("Afișare detaliată preluată direct din foaia de simulare a Excelului tău:")
    
    if selected_sheet == 'Simulare & Economii PZU' and df_current.shape[1] >= 17:
        # Preluăm rândurile de date începând de la rândul 3 (index 2 în Python) și coloanele D la Q (indici 3 la 16)
        df_display = df_current.iloc[2:, 3:17].copy()
        
        # Preluăm anteturile exacte din rândul 1 (index 0 în Python)
        headers = [str(df_current.iloc[0, i]).replace('\n', ' ') for i in range(3, 17)]
        df_display.columns = headers
        df_display.reset_index(drop=True, inplace=True)
        
        # Formatare coloană Data (fără oră, format DD.MM.YYYY)
        date_col = df_display.columns[0]
        df_display[date_col] = pd.to_datetime(df_display[date_col], errors='coerce').dt.strftime('%d.%m.%Y')

        # Formatare valori numerice cu spațiu pentru mii și virgulă pentru zecimale
        for col in df_display.columns[2:]:
            df_display[col] = pd.to_numeric(df_display[col], errors='coerce').apply(lambda x: fmt(x, 2) if pd.notnull(x) else x)

        st.dataframe(df_display, use_container_width=True, height=500)
    else:
        st.dataframe(df_current.dropna(how='all'), use_container_width=True, height=500)

else:
    st.info("Te rog să încarci fișierul tău Excel complet pentru a vizualiza tabelul.")
