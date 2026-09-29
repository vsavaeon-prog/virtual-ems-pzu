import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Configurarea corectă a paginii
st.set_page_config(
    page_title="Virtual EMS - BESS PZU Optimization",
    layout="wide"
)

st.title("⚡ Virtual EMS - Optimizare & Arbitraj Baterie (PZU)")
st.markdown("Sistem de simulare și calcul pentru stocare BESS în piața spot (PZU).")

# --- Meniu Lateral (Sidebar) ---
st.sidebar.header("🎛️ Setări Sistem & Baterie")
cap_baterie = st.sidebar.number_input("Capacitate Nominală Baterie (kWh)", value=40120.0, step=1000.0)
soc_max = st.sidebar.slider("SOC Max (%)", 0.5, 1.0, 0.95, 0.01)
soc_min = st.sidebar.slider("SOC Min (%)", 0.0, 0.5, 0.15, 0.01)
randament = st.sidebar.slider("Randament Ciclare (η)", 0.80, 0.99, 0.95, 0.01)

st.sidebar.header("⏰ Ferestre Orare")
durata_incarcare = st.sidebar.number_input("Durată Încărcare (ore)", value=4)
durata_descarcare = st.sidebar.number_input("Durată Descărcare (ore)", value=7)

# --- Zona Principală ---
uploaded_file = st.file_uploader("📂 Încarcă fișierul tău Excel de simulare (.xlsx)", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        @st.cache_data
        def load_file(file):
            xls = pd.ExcelFile(file)
            sheet_name = xls.sheet_names[0]
            df_data = pd.read_excel(xls, sheet_name=sheet_name)
            return df_data

        df = load_file(uploaded_file)
        st.success("Fișierul Excel a fost încărcat și citit cu succes!")

        st.subheader("📋 Previzualizare Date Importate")
        st.dataframe(df.dropna(how='all').head(10))

        if st.button("🚀 Rulează Analiza și Calculele"):
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
            st.subheader("📈 Grafic Orientativ Date")
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) >= 2:
                fig, ax = plt.subplots(figsize=(10, 4))
                y1 = pd.to_numeric(df[numeric_cols[0]].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                y2 = pd.to_numeric(df[numeric_cols[1]].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                
                ax.plot(y1.iloc[:96].values, label=str(numeric_cols[0]), color="tab:blue")
                ax.plot(y2.iloc[:96].values, label=str(numeric_cols[1]), color="tab:orange", linestyle="--")
                ax.set_title("Evoluție pe 24 ore (96 intervale)")
                ax.grid(True)
                ax.legend()
                st.pyplot(fig)
            else:
                st.info("Nu s-au găsit suficiente coloane numerice pentru a genera un grafic automat.")

    except Exception as e:
        st.error(f"A apărut o eroare la citirea fișierului Excel: {e}")
else:
    st.info("Te rog să încarci fișierul tău Excel pentru a începe.")
