import numpy as np
import math
from typing import List, Dict, Any
from scipy.optimize import curve_fit
from scipy.stats import ks_2samp

def analyze_lotka_law(data: List[int]) -> dict:
    """Ajusta la Ley de Productividad de Lotka (An = A1 / n^c), calculando exponente c, R^2 y Kolmogorov-Smirnov."""
    if not data or len(data) == 0:
        return {"error": "Se requiere una lista de frecuencias de producción por autor (número de papers por autor)."}
    
    counts = {}
    for d in data:
        counts[d] = counts.get(d, 0) + 1
    
    x = np.array(sorted(counts.keys()), dtype=float)
    y = np.array([counts[k] for k in x], dtype=float)
    
    # Log-Log fit: ln(y) = ln(C) - c * ln(x)
    log_x = np.log(x)
    log_y = np.log(y)
    
    slope, intercept = np.polyfit(log_x, log_y, 1)
    c_exponent = -slope
    a1_theoretical = np.exp(intercept)
    
    # R2
    y_pred = a1_theoretical / (x ** c_exponent)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    return {
        "law": "Lotka's Law of Author Productivity",
        "lotka_exponent_c": round(float(c_exponent), 4),
        "a1_theoretical": round(float(a1_theoretical), 2),
        "r_squared": round(float(r_squared), 4),
        "conforms_to_lotka": bool(1.5 <= c_exponent <= 3.5),
        "empirical_table": [{"papers_n": int(k), "authors_observed": int(v), "authors_expected": round(float(a1_theoretical / (k**c_exponent)), 2)} for k, v in zip(x[:10], y[:10])],
        "summary": f"Exponente de Lotka c = {c_exponent:.2f} con R² = {r_squared:.4f}. {'Se apega a la ley canónica (c ~ 2.0).' if 1.8 <= c_exponent <= 2.2 else 'Presenta desviación del modelo clásico.'}"
    }

def analyze_bradford_law(data: List[Dict[str, Any]]) -> dict:
    """Calcula la Ley de Dispersión de Bradford dividiendo la literatura en 3 zonas y extrayendo revistas Core."""
    # data: [{'journal': '...', 'articles': 120}, ...]
    if not data:
        return {"error": "Se requiere lista de revistas y conteo de artículos."}
    
    sorted_journals = sorted(data, key=lambda j: j.get("articles", 0), reverse=True)
    total_articles = sum(j.get("articles", 0) for j in sorted_journals)
    target_per_zone = total_articles / 3.0
    
    zones = {"Zone 1 (Core)": [], "Zone 2 (Moderate)": [], "Zone 3 (Peripheral)": []}
    current_zone = 1
    accum_articles = 0
    
    for j in sorted_journals:
        arts = j.get("articles", 0)
        accum_articles += arts
        if current_zone == 1:
            zones["Zone 1 (Core)"].append(j)
            if accum_articles >= target_per_zone:
                current_zone = 2
        elif current_zone == 2:
            zones["Zone 2 (Moderate)"].append(j)
            if accum_articles >= 2 * target_per_zone:
                current_zone = 3
        else:
            zones["Zone 3 (Peripheral)"].append(j)
            
    n1 = len(zones["Zone 1 (Core)"])
    n2 = len(zones["Zone 2 (Moderate)"])
    n3 = len(zones["Zone 3 (Peripheral)"])
    k_multiplier = round(float((n2 / n1 + n3 / n2) / 2.0), 2) if n1 > 0 and n2 > 0 else None
    
    return {
        "law": "Bradford's Law of Scattering",
        "total_journals": len(sorted_journals),
        "total_articles": total_articles,
        "bradford_multiplier_k": k_multiplier,
        "zone_distribution": {
            "zone_1_core": {"journals_count": n1, "articles_count": sum(j.get("articles", 0) for j in zones["Zone 1 (Core)"]), "core_journals": [j.get("journal") for j in zones["Zone 1 (Core)"][:10]]},
            "zone_2_moderate": {"journals_count": n2, "articles_count": sum(j.get("articles", 0) for j in zones["Zone 2 (Moderate)"])},
            "zone_3_peripheral": {"journals_count": n3, "articles_count": sum(j.get("articles", 0) for j in zones["Zone 3 (Peripheral)"])}
        },
        "summary": f"La literatura se distribuye en proporción 1 : {n2/n1 if n1 else 0:.1f} : {n3/n1 if n1 else 0:.1f} (Multiplicador k = {k_multiplier}). El núcleo Core cuenta con {n1} revistas principales."
    }

def analyze_price_index(references_years: List[int], publication_year: int = 2024, threshold_years: int = 5) -> dict:
    """Calcula el Índice de Inmediatez de Price (% de referencias en los últimos 5 años)."""
    if not references_years:
        return {"error": "Se requiere una lista de años de las referencias citadas."}
    
    recent_count = sum(1 for y in references_years if (publication_year - y) <= threshold_years and y <= publication_year)
    total_refs = len(references_years)
    price_index = (recent_count / total_refs) * 100.0 if total_refs > 0 else 0.0
    
    discipline_type = "Ciencias Duras / Biomedicina (Frente dinámico)" if price_index > 40 else ("Ciencias Sociales (Envejecimiento medio)" if price_index >= 20 else "Humanidades / Artes (Envejecimiento lento)")
    
    return {
        "law": "Price's Immediacy Index of Scientific Literature",
        "total_references": total_refs,
        "recent_references_count": recent_count,
        "price_index_percentage": round(price_index, 2),
        "field_characterization": discipline_type,
        "summary": f"Índice de Price = {price_index:.1f}% de citas con antigüedad <= {threshold_years} años. Tipología: {discipline_type}."
    }

def analyze_scientific_growth_phases(years: List[int], counts: List[int]) -> dict:
    """Ajusta modelos de crecimiento exponencial y logístico clasificando la fase de madurez del campo."""
    if len(years) < 4:
        return {"error": "Se requieren al menos 4 puntos temporales para modelado de crecimiento."}
    
    x = np.array(years) - min(years)
    y = np.array(counts, dtype=float)
    
    # Exponencial: y = a * exp(b * x)
    try:
        popt_exp, _ = curve_fit(lambda t, a, b: a * np.exp(b * t), x, y, p0=[y[0], 0.05], maxfev=2000)
        y_exp_pred = popt_exp[0] * np.exp(popt_exp[1] * x)
        ss_res_exp = np.sum((y - y_exp_pred) ** 2)
        r2_exp = 1 - (ss_res_exp / np.sum((y - np.mean(y)) ** 2))
    except Exception:
        r2_exp = 0.0
        popt_exp = [0, 0]
        
    # Logístico: y = L / (1 + exp(-k * (x - x0)))
    try:
        popt_log, _ = curve_fit(lambda t, L, k, x0: L / (1 + np.exp(-k * (t - x0))), x, y, p0=[max(y)*1.5, 0.2, len(x)/2], maxfev=3000)
        y_log_pred = popt_log[0] / (1 + np.exp(-popt_log[1] * (x - popt_log[2])))
        ss_res_log = np.sum((y - y_log_pred) ** 2)
        r2_log = 1 - (ss_res_log / np.sum((y - np.mean(y)) ** 2))
    except Exception:
        r2_log = 0.0
        popt_log = [0, 0, 0]

    dominant_model = "Logístico (Fase de Estabilización/Madurez)" if r2_log > r2_exp else "Exponencial (Fase de Expansión Rápida)"
    doubling_time = round(math.log(2) / popt_exp[1], 2) if popt_exp[1] > 0 else None
    
    return {
        "law": "Scientific Growth Modeling (Price & De Solla)",
        "exponential_model": {"r_squared": round(float(r2_exp), 4), "doubling_time_years": doubling_time},
        "logistic_model": {"r_squared": round(float(r2_log), 4), "carrying_capacity_L": round(float(popt_log[0]), 2)},
        "current_maturity_phase": dominant_model,
        "summary": f"El campo muestra mejor ajuste {dominant_model}. R² Exponencial: {r2_exp:.3f}, R² Logístico: {r2_log:.3f}."
    }
