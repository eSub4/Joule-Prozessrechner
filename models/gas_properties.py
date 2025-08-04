"""
Gas properties and thermodynamic functions for the JOULE process calculator.
Contains data and functions to calculate thermodynamic properties of various gases.
"""

import numpy as np

# Stoffwerte für ideale Gase
GAS_PROPERTIES = {
    "air": {
        "name": "Luft",
        "M": 28.9647,  # Molare Masse in g/mol
        "R": 287.058,  # Spezifische Gaskonstante in J/(kg·K)
        "kappa_approx": 1.4,  # Näherungswert für den Isentropenexponenten
        # Koeffizienten für cp(T) = a + b*T + c*T^2 + d*T^3 in J/(kg·K), T in K
        "cp_coeffs": [1047.63, -0.372589, 9.45304e-4, -6.02409e-7],
        "cp_const": 1005.0,  # Konstanter Wert für cp in J/(kg·K)
        "T_range": [200, 1600]  # Gültigkeitsbereich für die cp-Formel in K
    },
    "helium": {
        "name": "Helium",
        "M": 4.0026,  # Molare Masse in g/mol
        "R": 2077.1,  # Spezifische Gaskonstante in J/(kg·K)
        "kappa_approx": 1.667,  # Näherungswert für den Isentropenexponenten
        "cp_coeffs": [5193.0, 0, 0, 0],  # cp ist annähernd konstant für Helium
        "cp_const": 5193.0,  # Konstanter Wert für cp in J/(kg·K)
        "T_range": [200, 2000]  # Gültigkeitsbereich für die cp-Formel in K
    },
    "nitrogen": {
        "name": "Stickstoff",
        "M": 28.0134,  # Molare Masse in g/mol
        "R": 296.8,  # Spezifische Gaskonstante in J/(kg·K)
        "kappa_approx": 1.4,  # Näherungswert für den Isentropenexponenten
        "cp_coeffs": [1041.0, -0.29, 0.0007, -5e-7],  # Näherungswerte
        "cp_const": 1040.0,  # Konstanter Wert für cp in J/(kg·K)
        "T_range": [200, 1600]  # Gültigkeitsbereich für die cp-Formel in K
    },
    "carbon_dioxide": {
        "name": "Kohlendioxid",
        "M": 44.01,  # Molare Masse in g/mol
        "R": 188.9,  # Spezifische Gaskonstante in J/(kg·K)
        "kappa_approx": 1.3,  # Näherungswert für den Isentropenexponenten
        "cp_coeffs": [820.0, 1.2, -0.0005, 7e-8],  # Näherungswerte
        "cp_const": 846.0,  # Konstanter Wert für cp in J/(kg·K)
        "T_range": [200, 1600]  # Gültigkeitsbereich für die cp-Formel in K
    }
}


def cp(T, gas="air", use_const=False):
    """
    Berechnet die spezifische Wärmekapazität bei konstantem Druck (cp)
    
    Parameter:
    T : float
        Temperatur in K
    gas : str
        Gas ('air', 'helium', etc.)
    use_const : bool
        Wenn True, wird der konstante Wert für cp verwendet
        
    Returns:
    float
        Spezifische Wärmekapazität in J/(kg·K)
    """
    if use_const:
        return GAS_PROPERTIES[gas]["cp_const"]
    
    a, b, c, d = GAS_PROPERTIES[gas]["cp_coeffs"]
    return a + b*T + c*T**2 + d*T**3


def cp_mean(T1, T2, gas="air", use_const=False):
    """
    Berechnet den Mittelwert der spezifischen Wärmekapazität cp zwischen T1 und T2
    
    Parameter:
    T1, T2 : float
        Temperaturen in K
    gas : str
        Gas ('air', 'helium', etc.)
    use_const : bool
        Wenn True, wird der konstante Wert für cp verwendet
        
    Returns:
    float
        Mittlere spezifische Wärmekapazität in J/(kg·K)
    """
    if use_const:
        return GAS_PROPERTIES[gas]["cp_const"]
    
    # Bei genauerer Berechnung: Integration von cp(T) über T
    return (cp(T1, gas) + cp(T2, gas)) / 2


def cv(T, gas="air", use_const=False):
    """
    Berechnet die spezifische Wärmekapazität bei konstantem Volumen (cv)
    
    Parameter:
    T : float
        Temperatur in K
    gas : str
        Gas ('air', 'helium', etc.)
    use_const : bool
        Wenn True, wird der konstante Wert für cv verwendet
        
    Returns:
    float
        Spezifische Wärmekapazität in J/(kg·K)
    """
    R = GAS_PROPERTIES[gas]["R"]
    return cp(T, gas, use_const) - R


def kappa(T, gas="air", use_const=False):
    """
    Berechnet den Isentropenexponenten (κ = cp/cv)
    
    Parameter:
    T : float
        Temperatur in K
    gas : str
        Gas ('air', 'helium', etc.)
    use_const : bool
        Wenn True, wird der konstante Wert für κ verwendet
        
    Returns:
    float
        Isentropenexponent (dimensionslos)
    """
    if use_const:
        return GAS_PROPERTIES[gas]["kappa_approx"]
    
    return cp(T, gas) / cv(T, gas)


def kappa_mean(T1, T2, gas="air", use_const=False):
    """
    Berechnet den mittleren Isentropenexponenten zwischen T1 und T2
    
    Parameter:
    T1, T2 : float
        Temperaturen in K
    gas : str
        Gas ('air', 'helium', etc.)
    use_const : bool
        Wenn True, wird der konstante Wert für κ verwendet
        
    Returns:
    float
        Mittlerer Isentropenexponent (dimensionslos)
    """
    if use_const:
        return GAS_PROPERTIES[gas]["kappa_approx"]
    
    return (kappa(T1, gas) + kappa(T2, gas)) / 2


def specific_volume(p, T, gas="air"):
    """
    Berechnet das spezifische Volumen eines idealen Gases
    
    Parameter:
    p : float
        Druck in Pa
    T : float
        Temperatur in K
    gas : str
        Gas ('air', 'helium', etc.)
        
    Returns:
    float
        Spezifisches Volumen in m³/kg
    """
    R = GAS_PROPERTIES[gas]["R"]
    return R * T / p


def get_material_properties(gas, T, use_const=False):
    """
    Gibt die Stoffwerte eines Gases bei einer bestimmten Temperatur zurück
    
    Parameter:
    gas : str
        Gas ('air', 'helium', etc.)
    T : float
        Temperatur in K
    use_const : bool
        Wenn True, werden konstante Werte verwendet
        
    Returns:
    dict
        Dictionary mit den Stoffwerten
    """
    properties = {}
    properties["cp"] = cp(T, gas, use_const)
    properties["cv"] = cv(T, gas, use_const)
    properties["kappa"] = kappa(T, gas, use_const)
    properties["R"] = GAS_PROPERTIES[gas]["R"]
    properties["name"] = GAS_PROPERTIES[gas]["name"]
    
    return properties