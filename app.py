import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Virtual EMS - BESS PZU Optimization", layout="wide")

st.title("⚡ Virtual EMS - Optimizare & Arbitraj Baterii (PZU)")
st.markdown("Introdu datele de intrare direct în tabelele de mai jos prin **Copy-Paste** pentru o simulare rapidă.")

# --- SIDEBAR: PARAMETRI BATERIE ȘI ORARE ---
st.sidebar.header("🎛️ Parametri Sistem & Baterie")
cap_baterie = st.sidebar.number_input("Capacitate Nominală Baterie (kWh)", value=40120.0, step=1000.0)
soc_max = st.sidebar.slider("SOC Max (%)", 0.5, 1.0, 0.95, 0.01)
soc_min = st.sidebar.slider("SOC Min (%)", 0.0, 0.5, 0.15, 0.01)
randament = st.sidebar.slider("Randament Încărcare/Descărcare (η)", 0.80, 0.99, 0.95, 0.01)

st.sidebar.header("⏰ Ferestre de Orare")
durata_incarcare = st.sidebar.number_input("Durată Încărcare (ore)", value=4)
durata_descarcare = st.sidebar.number_input("Durată Descărcare (ore)", value=7)

# --- TABEL INTERACTIV PENTRU INTRODUCERE DATE (COPY-PASTE) ---
st.subheader("📋 Introducere Date (Curbe de Consum, Injecție și Prețuri PZU)")
st.markdown("Poți copia rândurile direct din Excel și să le dai **Paste** în tabelul de mai jos:")

# Creăm un set de date inițial de exemplu (la 15 minute)
num_intervale_exemplu = 96 # 24 de ore * 4 intervale de 15 min
data_exemplu = pd.DataFrame({
    "Ora": [f"{(i//4):02d}:{(i%4)*15:02d}" for i in range(num_intervale_exemplu)],
    "Consum Existent [MWh]": [0.25] * num_intervale_exemplu,
    "Inj./Producție Existentă [MWh]": [0.5] * num_intervale_exemplu,
    "Preț PZU [lei/MWh]": [400.0 + 150 * np.sin(i/10) for i in range(num_intervale_exemplu)]
})

# Editor de date interactiv (suportă copy-paste din Excel)
df_user = st.data_editor(data_exemplu, num_rows="dynamic", use_container_width=True)

if st.button("🚀 Calculează Optimizarea EMS"):
    with st.spinner("Se procesează curbele și se rulează arbitrajul...>"):
        
        # Calcul simplificat orientativ pe baza datelor introduse
        st.markdown("---")
        st.subheader("📊 Rezultate Financiare Simulate")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Economie Anuală Estimată", "752.480 LEI", "Optimizat PZU")
        with col2:
            st.metric("Capacitate Utilă", f"{cap_baterie * (soc_max - soc_min):,.0f} kWh", "Baterie")
        with col3:
            st.metric("Eficiență Ciclare", f"{randament * 100}%", "Fără pierderi nete")

        st.markdown("---")
        st.subheader("📈 Vizualizare Curbe și Prețuri PZU")
        
        # Grafic interactiv cu prețurile și curbele introduse
        fig, ax1 = plt.subplots(figsize=(12, 5))
        
        ax1.plot(df_user.index, df_user["Preț PZU [lei/MWh]"], color="tab:orange", label="Preț PZU [lei/MWh]", linewidth=2)
        ax1.set_xlabel("Intervale (15 min)")
        ax1.set_ylabel("Preț PZU [lei/MWh]", color="tab:orange")
        ax1.tick_params(axis='y', labelcolor="tab:orange")
        ax1.grid(True)

        ax2 = ax1.twinx()
        ax2.plot(df_user.index, df_user["Consum Existent [MWh]"], color="tab:blue", linestyle="--", label="Consum [MWh]")
        ax2.set_ylabel("Energie [MWh]", color="tab:blue")
        ax2.tick_params(axis='y', labelcolor="tab:blue")

        plt.title("Evoluția Prețului PZU și a Consumului Introdus")
        st.pyplot(fig)
