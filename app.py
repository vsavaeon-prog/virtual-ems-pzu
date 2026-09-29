import pulp
import pandas as pd

def optimize_bess_arbitrage(prices, capacity_mwh, max_power_mw, eta):
    # Creare problemă de maximizare a profitului
    prob = pulp.LpProblem("BESS_Arbitrage_PZU", pulp.LpMaximize)
    
    T = range(len(prices))
    
    # Variabile de decizie pentru fiecare interval de 15 min / oră
    p_charge = {t: pulp.LpVariable(f"ch_{t}", lowBound=0, upBound=max_power_mw) for t in T}
    p_discharge = {t: pulp.LpVariable(f"dis_{t}", lowBound=0, upBound=max_power_mw) for t in T}
    soc = {t: pulp.LpVariable(f"soc_{t}", lowBound=0.15 * capacity_mwh, upBound=0.95 * capacity_mwh) for t in T}
    
    # Variabilă binară pentru a preveni încărcarea și descărcarea simultană
    u = {t: pulp.LpVariable(f"u_{t}", cat='Binary') for t in T}
    
    # Funcția obiectiv: Maximizarea veniturilor din piață (Vânzare - Cumpărare)
    # Ține cont de prețul PZU și randament (eta)
    prob += pulp.lpSum(
        prices[t] * (p_discharge[t] * eta - p_charge[t] / eta) for t in T
    )
    
    # Restricții de dinamică a stării de încărcare (SOC)
    dt = 0.25 # pentru intervale de 15 minute
    for t in T:
        if t == 0:
            soc_prev = 0.5 * capacity_mwh # SOC inițial
        else:
            soc_prev = soc[t-1]
            
        prob += soc[t] == soc_prev + (p_charge[t] * eta * dt) - (p_discharge[t] / dt / eta) * dt # (simplificat pe interval)
        
        # Oprit încărcarea/descărcarea simultană folosind u[t]
        prob += p_charge[t] <= max_power_mw * u[t]
        prob += p_discharge[t] <= max_power_mw * (1 - u[t])
        
    # Rulare solver CBC integrat în PuLP
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    results = []
    for t in T:
        results.append({
            'Interval': t,
            'Pret_PZU': prices[t],
            'Incarcare_MW': p_charge[t].varValue,
            'Descarcare_MW': p_discharge[t].varValue,
            'SOC_MWh': soc[t].varValue
        })
        
    return pd.DataFrame(results)
