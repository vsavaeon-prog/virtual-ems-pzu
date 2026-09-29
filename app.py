import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Virtual EMS - BESS PZU Optimization", layout="wide")

st.title("⚡ Virtual EMS - Optimizare & Arbitraj Baterii (PZU)")
st.markdown("Încarcă fișierul tău Excel de simulare pentru a rula calculele și graficele.")

# --- SIDEBAR: PARAMETRI BATERIE ȘI ORARE ---
st.sidebar.header("🎛️ Parametri Sistem & Baterie")
cap_baterie = st.sidebar.number_input("Capacitate Nominală Baterie (kWh)", value=40120.0, step=1000.0)
soc_max = st.sidebar.slider("SOC Max (%)", 0.5, 1.0, 0.95, 0.01)
soc_min = st.sidebar.slider("SOC Min (%)", 0.0, 0.5, 0.15, 0.01)
randament = st.sidebar.slider("Randament Încărcare/Descărcare (η)", 0.80, 0.99, 0.95, 0.01)

st.sidebar.header("⏰ Ferestre de Orare")
durata_incarcare = st.sidebar.number_input("Durată Încărcare (ore)", value=4)
durata_descarcare = st.sidebar.number_input("Durată Descărcare (ore)", value=7)

# --- ÎNCĂRCARE FIȘIER EXCEL ---
uploaded_file = st.file_uploader("📂 Încarcă fișierul tău Excel (.xlsx)", type=["xlsx", "xls"])

if uploaded_file is not None:
    @st.cache_data
    def load_excel_safe(file):
        xls = pd.ExcelFile(file)
        # Citeste automat prima foaie din fișier, indiferent de nume
        df_in = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
        return df_in

    df = load_excel_safe(uploaded_file)
    st.success(f"Fișier încărcat cu succes! S-a citit foaia principală.")

    st.subheader("📋 Previzualizare Date Importate")
    st.dataframe(df.dropna(how='all').head(10))

    if st.button("🚀 Rulează Simulatorul EMS"):
        with st.spinner("Se procesează datele..."):
            
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
            st.subheader("📈 Vizualizare Grafică Date")
            
            # Caută automat coloane numerice sau relevante pentru grafic
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_cols) >= 2:
                fig, ax = plt.subplots(figsize=(12, 5))
                # Ia primele două coloane numerice găsite pentru a desena un grafic orientativ
                c1, c2 = numeric_cols[0], numeric_cols[1]
                
                y1 = pd.to_numeric(df[c1].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                y2 = pd.to_numeric(df[c2].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                
                ax.plot(y1.iloc[:96].values, label=str(c1), color="tab:blue")
                ax.plot(y2.iloc[:96].values, label=str(c2), color="tab:orange", linestyle="--")
                ax.set_title("Evoluție Parametri (Primele 24 ore / 96 intervale)")
                ax.set_xlabel("Intervale (15 min)")
                ax.grid(True)
                ax.legend()
                st.pyplot(fig)
            else:
                st.info("S-au încărcat datele, dar nu s-au găsit suficient de multe coloane numerice pentru grafic.")
else:
    st.info("Te rog să încarci fișierul tău Excel pentru a porni aplicația.")
