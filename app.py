import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Virtual EMS - BESS PZU Optimization", layout="wide")

st.title("⚡ Virtual EMS & BESS Financial Engine (PZU)")
st.markdown("Motor complet de simulare: Încarcă curbele brute, iar aplicația va rula calculele și va genera tabelul complet.")

# Funcție pentru formatare numere (spațiu pentru mii, virgulă pentru zecimale)
def fmt(val, decimals=2):
    if pd.isna(val):
        return ""
    try:
        s = f"{float(val):,.{decimals}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", " ")
    except:
        return str(val)

# --- SIDEBAR: SETĂRI ȘI PARAMETRI (DATE DE INTRARE) ---
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

# --- FORMULE DERIVATE ---
cap_utila_max = cap_nominala * soc_max
cap_utila_min = cap_nominala * soc_min
stare_initiala_baterie = cap_utila_min
limita_energie_15min = putere_invertor * (15 / 60)

# --- ZONA PRINCIPALĂ: ÎNCĂRCARE FIȘIER CU CURBE BRUTE ---
uploaded_file = st.file_uploader("📂 Încarcă fișierul cu curbe brute (.xlsx)", type=["xlsx", "xls"])

if uploaded_file is not None:
    @st.cache_data
    def load_curves_file(file):
        xls = pd.ExcelFile(file)
        # Căutăm foaia 'Curba' sau prima foaie disponibilă
        sheet_name = next((s for s in xls.sheet_names if 'curb' in s.lower()), xls.sheet_names[0])
        df = pd.read_excel(xls, sheet_name=sheet_name)
        return df, sheet_name

    df_curbe, used_sheet = load_curves_file(uploaded_file)
    st.success(f"Fișier încărcat cu succes! S-au preluat curbele din foaia: {used_sheet}")

    # --- MOTORUL DE SIMULARE MATEMATICĂ (GENERARE COLOANE D - Q) ---
    sim_data = []
    soc_curent = stare_initiala_baterie

    # Identificăm coloanele din fișierul de curbe brut
    cols = list(df_curbe.columns)
    
    for idx, row in df_curbe.iterrows():
        # Preluare dată, oră, import existent, export existent și preț PZU din curbe brute
        data_val = row.iloc[3] if len(cols) > 3 else row.iloc[0]
        ora_val = row.iloc[2] if len(cols) > 2 else row.iloc[1]
        imp_ex = float(str(row.iloc[6]).replace(',', '.')) if pd.notnull(row.iloc[6]) else 0.0
        exp_ex = float(str(row.iloc[7]).replace(',', '.')) if pd.notnull(row.iloc[7]) else 0.0
        pzu_val = float(str(row.iloc[12]).replace(',', '.')) if len(cols) > 12 and pd.notnull(row.iloc[12]) else 500.0

        # Algoritm de calcul încărcare / descărcare baterie pe interval
        incarcare = 0.0
        descarcare = 0.0

        # Logica orientativă de arbitraj pe intervale
        if mod_functionare in ["Arbitraj / Interval", "Mixt"]:
            # Încărcare în intervalul orar setat
            if sursa_incarcare != "Doar Panouri":
                incarcare = min(limita_energie_15min, (cap_utila_max - soc_curent) / randament, max(0.0, exp_ex))
            # Descărcare în intervalul de vârf
            descarcare = min(limita_energie_15min, (soc_curent - cap_utila_min) * randament, max(0.0, imp_ex))

        # Actualizare nivel baterie (SOC final)
        soc_curent = max(cap_utila_min, min(cap_utila_max, soc_curent + (incarcare * randament) - (descarcare / randament)))

        # Calcul fluxuri noi
        imp_nou = max(0.0, imp_ex + incarcare - exp_ex - descarcare)
        exp_nou = max(0.0, exp_ex + descarcare - imp_ex - incarcare)

        # Valori financiare în LEI
        imp_ex_lei = imp_ex * (pzu_val + valoare_taxe) / 1000
        exp_ex_lei = exp_ex * pzu_val / 1000
        imp_nou_lei = imp_nou * (pzu_val + valoare_taxe) / 1000
        exp_nou_lei = exp_nou * pzu_val / 1000

        sim_data.append({
            "Data": data_val,
            "Ora": ora_val,
            "Import Existent [kWh]": imp_ex,
            "Export Existent [kWh]": exp_ex,
            "Încărcare Baterie [kWh]": incarcare,
            "Descărcare Baterie [kWh]": descarcare,
            "Nivel Baterie Final / SOC [kWh]": soc_curent,
            "Import NOU [kWh]": imp_nou,
            "Export NOU [kWh]": exp_nou,
            "ISTORIC PZU [lei/MWh]": pzu_val,
            "Import Existent [lei]": imp_ex_lei,
            "Export Existent [lei]": exp_ex_lei,
            "Import NOU [lei]": imp_nou_lei,
            "Export NOU [lei]": exp_nou_lei
        })

    df_simulated = pd.DataFrame(sim_data)

    # Bilanț economic general
     cost_imp_fara = df_simulated["Import Existent [lei]"].sum()
    cost_imp_cu = df_simulated["Import NOU [lei]"].sum()
    economie_totala = max(0.0, cost_imp_fara - cost_imp_cu)
    perioada_amortizare = valoare_investitie / economie_totala if economie_totala > 0 else 0

    st.markdown("---")
    st.subheader("💰 Bilanț Financiar & Rezultate Economice (Simulare Calculată)")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("ECONOMIE TOTALĂ OBȚINUTĂ", f"{fmt(economie_totala, 0)} EURO/an" if economie_totala < 100000 else f"{fmt(economie_totala/5.24, 0)} EURO/an")
    with m2:
        st.metric("Valoare Investiție", f"{fmt(valoare_investitie, 2)} EURO")
    with m3:
        st.metric("Perioada Amortizare", f"{fmt(perioada_amortizare, 2)} ANI")
    with m4:
        st.metric("Capacitate Utilă (Max/Min)", f"{fmt(cap_utila_max, 1)} / {fmt(cap_utila_min, 1)} kWh")

    st.markdown("---")
    st.subheader("📋 Tabel Simulare & Economii PZU (Coloanele D până la Q generate din curbe)")
    st.markdown("Rezultatul simulării rulate automat pe baza curbelor brute încărcate:")

    # Formatare afișare tabel
    df_display = df_simulated.copy()
    df_display["Data"] = pd.to_datetime(df_display["Data"], errors='coerce').dt.strftime('%d.%m.%Y')

    for col in df_display.columns[2:]:
        df_display[col] = pd.to_numeric(df_display[col], errors='coerce').apply(lambda x: fmt(x, 2) if pd.notnull(x) else x)

    st.dataframe(df_display, use_container_width=True, height=500)

else:
    st.info("Te rog să încarci fișierul cu curbe brute pentru a rula simularea și a genera tabelul de rezultate.")
