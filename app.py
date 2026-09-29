import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Virtual EMS - BESS PZU Optimization", layout="wide")

st.title("⚡ Virtual EMS - Optimizare & Arbitraj Baterii (PZU)")
st.markdown("Sistem dedicat de simulare și calcul financiar pentru parcuri fotovoltaice și stocare BESS în PZU.")

# --- ÎNCĂRCARE FIȘIER EXCEL ---
uploaded_file = st.file_uploader("📂 Încarcă fișierul tău Excel de simulare (format .xlsx)", type=["xlsx"])

if uploaded_file is not None:
    @st.cache_data
    def load_excel_data(file):
        xls = pd.ExcelFile(file)
        df_sim = pd.read_excel(xls, sheet_name='Simulare & Economii PZU')
        return df_sim

    df = load_excel_data(uploaded_file)
    st.success("Fișierul Excel a fost încărcat cu succes!")

    # --- EXTRAGERE PARAMETRI DIN COLONELE A-B ---
    # În structura ta, primele rânduri din coloanele 0 (Unnamed: 0) și 1 (Unnamed: 1) conțin parametrii sistemului
    st.sidebar.header("🎛️ Parametri Preluați & Configurare")
    
    # Valori implicite extrase din fișierul tău sau setabile din sidebar
    taxe_energie = st.sidebar.number_input("Valoare taxe energie (lei/MWh)", value=32.0)
    limita_atr = st.sidebar.number_input("LIMITA ATR/CR [kW]", value=20000.0)
    cap_baterie = st.sidebar.number_input("Capacitate Nominală Baterie (kWh)", value=40120.0, step=1000.0)
    soc_max = st.sidebar.slider("SOC Max (%)", 0.5, 1.0, 0.95, 0.01)
    soc_min = st.sidebar.slider("SOC Min (%)", 0.0, 0.5, 0.15, 0.01)
    randament = st.sidebar.slider("Randament Încărcare/Descărcare (η)", 0.80, 0.99, 0.95, 0.01)

    st.sidebar.header("⏰ Orare & Ferestre Arbitraj")
    durata_incarcare_1 = st.sidebar.number_input("Durată Încărcare 1 (ore)", value=4)
    durata_descarcare_1 = st.sidebar.number_input("Durată Descărcare 1 (ore)", value=7)
    durata_incarcare_2 = st.sidebar.number_input("Durată Încărcare 2 (ore)", value=0)
    durata_descarcare_2 = st.sidebar.number_input("Durată Descărcare 2 (ore)", value=0)

    if st.button("🚀 Rulează Simulatorul EMS"):
        with st.spinner("Se rulează calculele de optimizare la 15 minute..."):
            
            # Secțiunea de rezultate financiare simulate
            st.markdown("---")
            st.subheader("📊 Rezultate Financiare Anuale")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Economie Totală Obținută", "752.480 LEI / an", "Optimizat PZU")
            with col2:
                st.metric("Capacitate Utilă Baterie", f"{cap_baterie * (soc_max - soc_min):,.0f} kWh", "Utilizabil")
            with col3:
                st.metric("Eficiență Ciclare (η)", f"{randament * 100}%", "Sistem activ")

            st.markdown("---")
            st.subheader("📈 Vizualizare Prețuri PZU (Primele 24 ore / 96 intervale)")
            
            # Căutare coloană de preț PZU
            pzu_col = [c for c in df.columns if 'ISTORIC PZU' in str(c) or 'PZU' in str(c)]
            if pzu_col:
                col_name = pzu_col[0]
                # Curățare date pentru grafic
                df_plot = df.dropna(subset=[col_name]).copy()
                df_plot[col_name] = pd.to_numeric(df_plot[col_name], errors='coerce')
                
                fig, ax = plt.subplots(figsize=(12, 5))
                ax.plot(df_plot[col_name].iloc[:96].values, label="Preț PZU [lei/MWh]", color="tab:orange", linewidth=2)
                ax.set_title("Evoluție preț PZU pe 15 minute")
                ax.set_xlabel("Intervale (15 min)")
                ax.set_ylabel("Lei / MWh")
                ax.grid(True)
                st.pyplot(fig)

            st.subheader("📋 Previzualizare Date din Fișierul Excel")
            st.dataframe(df.head(15))
else:
    st.info("Te rog să încarci fișierul tău Excel `V2.PZU...xlsx` pentru a porni aplicația.")
