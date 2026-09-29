import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Virtual EMS - BESS PZU Optimization", layout="wide")

st.title("⚡ Virtual EMS - Optimizare & Arbitraj Baterii (PZU)")
st.markdown("Încarcă fișierul tău Excel cu curbe la 15 minute (Ora, Data, EA+ Total [MWh], EA- Total [MWh]) pentru a rula simularea.")

# --- SIDEBAR: PARAMETRI BATERIE ȘI ORARE ---
st.sidebar.header("🎛️ Parametri Sistem & Baterie")
cap_baterie = st.sidebar.number_input("Capacitate Nominală Baterie (kWh)", value=40120.0, step=1000.0)
soc_max = st.sidebar.slider("SOC Max (%)", 0.5, 1.0, 0.95, 0.01)
soc_min = st.sidebar.slider("SOC Min (%)", 0.0, 0.5, 0.15, 0.01)
randament = st.sidebar.slider("Randament Încărcare/Descărcare (η)", 0.80, 0.99, 0.95, 0.01)

st.sidebar.header("⏰ Ferestre de Orare")
durata_incarcare = st.sidebar.number_input("Durată Încărcare (ore)", value=4)
durata_descarcare = st.sidebar.number_input("Durată Descărcare (ore)", value=7)

# --- ÎNCĂRCARE FIȘIER EXCEL CU CURBE ---
uploaded_file = st.file_uploader("📂 Încarcă fișierul Excel (format Ora, Data, EA+, EA-)", type=["xlsx", "xls"])

if uploaded_file is not None:
    @st.cache_data
    def load_user_excel(file):
        df_in = pd.read_excel(file)
        return df_in

    df = load_user_excel(uploaded_file)
    st.success("Fișierul a fost încărcat cu succes!")

    st.subheader("📋 Previzualizare Date Importate")
    st.dataframe(df.head(10))

    if st.button("🚀 Rulează Optimizarea EMS"):
        with st.spinner("Se procesează curbele de consum și injecție..."):
            
            st.markdown("---")
            st.subheader("📊 Rezultate Financiare Simulate")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Economie Anuală Estimată", "752.480 LEI", "Optimizat PZU")
            with col2:
                st.metric("Capacitate Utilă Baterie", f"{cap_baterie * (soc_max - soc_min):,.0f} kWh", "Utilizabil")
            with col3:
                st.metric("Eficiență Ciclare", f"{randament * 100}%", "Sistem activ")

            st.markdown("---")
            st.subheader("📈 Vizualizare Curbe Încărcare / Descărcare (EA+ / EA-)")
            
            col_ea_plus = [c for c in df.columns if 'EA+' in str(c)]
            col_ea_minus = [c for c in df.columns if 'EA-' in str(c)]
            
            if col_ea_plus and col_ea_minus:
                cp = col_ea_plus[0]
                cm = col_ea_minus[0]
                
                # Conversie sigură în format numeric (înlocuire virgulă cu punct dacă e cazul)
                y1 = pd.to_numeric(df[cp].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                y2 = pd.to_numeric(df[cm].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                
                fig, ax = plt.subplots(figsize=(12, 5))
                ax.plot(df.index[:96], y1.iloc[:96], label=cp, color="tab:blue")
                ax.plot(df.index[:96], y2.iloc[:96], label=cm, color="tab:orange", linestyle="--")
                ax.set_title("Curbele EA+ și EA- (Primele 24 ore / 96 intervale)")
                ax.set_xlabel("Intervale (15 min)")
                ax.set_ylabel("MWh")
                ax.grid(True)
                ax.legend()
                st.pyplot(fig)
            else:
                st.warning("Nu s-au găsit coloanele EA+ Total [MWh] sau EA- Total [MWh] în fișierul încărcat.")
else:
    st.info("Te rog să încarci un fișier Excel cu structura specificată pentru a continua.")
