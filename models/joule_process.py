"""
Core calculation module for the JOULE process.
Contains the JouleProcessCalculator class that performs all thermodynamic calculations.
Extended with intercooling functionality.
"""

import numpy as np
from models import gas_properties  # Anstatt import gas_properties
from models.gas_properties import GAS_PROPERTIES, cp, cp_mean, cv, kappa, kappa_mean, specific_volume
from utils import converters  # Anstatt import converters
from utils.converters import celsius_to_kelvin, kelvin_to_celsius, bar_to_pascal, pascal_to_bar


class JouleProcessCalculator:
    """
    Berechnet einen JOULE-Prozess mit detailliertem Rechenweg
    """
    def __init__(self, gas="air", use_const_cp=True):
        self.gas = gas
        self.use_const_cp = use_const_cp
        self.steps = []  # Speichert alle Berechnungsschritte
        self.states = {}  # Speichert die Zustandsgrößen
        self.step_categories = {}  # Speichert die Schritte nach Kategorien
        
        # Konstanten für das Arbeitsfluid
        self.R = GAS_PROPERTIES[gas]["R"]
        if use_const_cp:
            self.cp_const = GAS_PROPERTIES[gas]["cp_const"]
            self.kappa = GAS_PROPERTIES[gas]["kappa_approx"]
            self.cv_const = self.cp_const - self.R
        
        # Parameter
        self.regeneration = False
        self.reg_eff = 0.0
        self.compressor_efficiency = 1.0
        self.turbine_efficiency = 1.0
        self.mass_flow = None
        
        # Parameter für Zwischenkühlung
        self.intercooling = False
        self.intercooling_temperature = None
        self.intercooling_pressure_ratio = None
    
    def _add_step(self, title, formula=None, calculation=None, result=None, unit=None, category="Allgemein"):
        """
        Fügt einen Berechnungsschritt hinzu
        
        Parameter:
        title : str
            Titel des Schritts
        formula : str
            Mathematische Formel
        calculation : str
            Numerische Berechnung
        result : float
            Ergebnis
        unit : str
            Einheit des Ergebnisses
        category : str
            Kategorie des Schritts für die strukturierte Ausgabe
        """
        step = {
            "title": title,
            "formula": formula,
            "calculation": calculation,
            "result": result,
            "unit": unit
        }
        self.steps.append(step)
        
        # In Kategorie einsortieren
        if category not in self.step_categories:
            self.step_categories[category] = []
        self.step_categories[category].append(step)
    
    def set_parameters(self, regeneration=False, reg_eff=0.0, 
                       compressor_efficiency=1.0, turbine_efficiency=1.0,
                       mass_flow=None, intercooling=False, 
                       intercooling_temperature=None,
                       intercooling_pressure_ratio=None):
        """
        Setzt die Parameter für die Berechnung
        
        Parameter:
        regeneration : bool
            Wenn True, wird Regeneration aktiviert
        reg_eff : float
            Wirkungsgrad der Regeneration (0 bis 1)
        compressor_efficiency : float
            Isentroper Wirkungsgrad des Verdichters (0 bis 1)
        turbine_efficiency : float
            Isentroper Wirkungsgrad der Turbine (0 bis 1)
        mass_flow : float
            Massestrom in kg/s
        intercooling : bool
            Wenn True, wird Zwischenkühlung aktiviert
        intercooling_temperature : float
            Temperatur nach Zwischenkühlung in K (wenn None, wird T1 verwendet)
        intercooling_pressure_ratio : float
            Druckverhältnis der ersten Verdichtungsstufe (wenn None, wird optimales Verhältnis berechnet)
        """
        self.regeneration = regeneration
        self.reg_eff = reg_eff
        self.compressor_efficiency = compressor_efficiency
        self.turbine_efficiency = turbine_efficiency
        self.mass_flow = mass_flow
        self.intercooling = intercooling
        self.intercooling_temperature = intercooling_temperature
        self.intercooling_pressure_ratio = intercooling_pressure_ratio
        
        self._add_step(
            title="Parameter für den JOULE-Prozess",
            calculation=f"Gas: {GAS_PROPERTIES[self.gas]['name']}, " +
                      f"Regeneration: {'Ja' if regeneration else 'Nein'}" +
                      (f" (Wirkungsgrad: {reg_eff:.2f})" if regeneration else "") +
                      f", Verdichterwirkungsgrad: {compressor_efficiency:.2f}" +
                      f", Turbinenwirkungsgrad: {turbine_efficiency:.2f}" +
                      (f", Massestrom: {mass_flow:.4f} kg/s" if mass_flow is not None else "")
        )
        
        if intercooling:
            self._add_step(
                title="Parameter für die Zwischenkühlung",
                calculation=f"Zwischenkühlung: Aktiv" +
                          (f", Temperatur nach Zwischenkühlung: {intercooling_temperature:.2f} K" if intercooling_temperature is not None else ", Kühlung auf Ansaugtemperatur") +
                          (f", Druckverhältnis erste Stufe: {intercooling_pressure_ratio:.4f}" if intercooling_pressure_ratio is not None else ", Optimales Druckverhältnis"),
                category="Zwischenkühlung"
            )
    
    def calculate_state_1(self, p1, T1):
        """
        Berechnet den Zustand 1 (Verdichtereintritt)
        
        Parameter:
        p1 : float
            Druck in Pa
        T1 : float
            Temperatur in K
        """
        # Sicherstellen, dass die Werte float sind
        p1 = float(p1)
        T1 = float(T1)
        
        self._add_step(
            title="Zustand 1 (Verdichtereintritt)",
            calculation=f"p₁ = {pascal_to_bar(p1):.4f} bar = {p1:.2f} Pa, " +
                      f"T₁ = {kelvin_to_celsius(T1):.2f} °C = {T1:.2f} K",
            category="Zustand 1"
        )
        
        # Spezifisches Volumen berechnen
        v1 = specific_volume(p1, T1, self.gas)
        self._add_step(
            title="Spezifisches Volumen v₁",
            formula="v₁ = R·T₁/p₁",
            calculation=f"v₁ = {self.R:.2f} J/(kg·K) · {T1:.2f} K / {p1:.2f} Pa",
            result=v1,
            unit="m³/kg",
            category="Zustand 1"
        )
        
        # Enthalpie als Referenzpunkt setzen
        h1 = 0.0
        self._add_step(
            title="Spezifische Enthalpie h₁",
            calculation="Als Referenzpunkt für die Enthalpie setzen wir h₁ = 0 J/kg",
            result=h1,
            unit="J/kg",
            category="Zustand 1"
        )
        
        # Entropie als Referenzpunkt setzen
        s1 = 0.0
        self._add_step(
            title="Spezifische Entropie s₁",
            calculation="Als Referenzpunkt für die Entropie setzen wir s₁ = 0 J/(kg·K)",
            result=s1,
            unit="J/(kg·K)",
            category="Zustand 1"
        )
        
        self.states[1] = {"p": p1, "T": T1, "v": v1, "h": h1, "s": s1}
    
    def calculate_state_2_isentropic(self, p2):
        """
        Berechnet den Zustand 2s (Verdichteraustritt, isentrop)
        
        Parameter:
        p2 : float
            Druck in Pa
            
        Returns:
        dict:
            Dictionary mit den Zustandsgrößen für den isentropen Zustand 2s
        """
        if 1 not in self.states:
            raise ValueError("Zustand 1 muss zuerst berechnet werden.")
        
        # Sicherstellen, dass p2 ein float ist
        p2 = float(p2)
        
        p1 = float(self.states[1]["p"])
        T1 = float(self.states[1]["T"])
        
        self._add_step(
            title="Zustand 2s (isentroper Verdichteraustritt)",
            calculation=f"p₂ = {pascal_to_bar(p2):.4f} bar = {p2:.2f} Pa"
        )
        
        # Isentroper Exponent für die Verdichtung
        k = self.kappa if self.use_const_cp else kappa_mean(T1, T1 * (p2/p1)**0.2, self.gas)
        self._add_step(
            title="Isentropenexponent κ für die Verdichtung",
            formula="κ = cp/cv" if not self.use_const_cp else "κ = const",
            calculation=f"κ = {k:.4f}" + (" (konstant)" if self.use_const_cp else ""),
            result=k,
            unit=""
        )
        
        # Temperatur berechnen mit der isentropen Zustandsgleichung
        T2s = T1 * (p2/p1)**((k-1)/k)
        self._add_step(
            title="Temperatur T₂ₛ (isentrop)",
            formula="T₂ₛ = T₁ · (p₂/p₁)^((κ-1)/κ)",
            calculation=f"T₂ₛ = {T1:.2f} K · ({p2/p1:.4f})^(({k:.4f}-1)/{k:.4f})",
            result=T2s,
            unit="K"
        )
        self._add_step(
            title="Temperatur T₂ₛ in °C",
            calculation=f"T₂ₛ = {T2s:.2f} K - 273.15",
            result=kelvin_to_celsius(T2s),
            unit="°C"
        )
        
        # Spezifisches Volumen berechnen
        v2s = specific_volume(p2, T2s, self.gas)
        self._add_step(
            title="Spezifisches Volumen v₂ₛ",
            formula="v₂ₛ = R·T₂ₛ/p₂",
            calculation=f"v₂ₛ = {self.R:.2f} J/(kg·K) · {T2s:.2f} K / {p2:.2f} Pa",
            result=v2s,
            unit="m³/kg"
        )
        
        # Enthalpiedifferenz berechnen
        cp_val = self.cp_const if self.use_const_cp else cp_mean(T1, T2s, self.gas)
        dh = cp_val * (T2s - T1)
        self._add_step(
            title="Spezifische Wärmekapazität cₚ",
            formula="cₚ = const" if self.use_const_cp else "cₚ = f(T)",
            calculation=f"cₚ = {cp_val:.2f} J/(kg·K)",
            result=cp_val,
            unit="J/(kg·K)"
        )
        self._add_step(
            title="Enthalpiedifferenz Δh₁₂ₛ",
            formula="Δh₁₂ₛ = cₚ · (T₂ₛ - T₁)",
            calculation=f"Δh₁₂ₛ = {cp_val:.2f} J/(kg·K) · ({T2s:.2f} K - {T1:.2f} K)",
            result=dh,
            unit="J/kg"
        )
        
        # Enthalpie am Zustand 2s
        h2s = self.states[1]["h"] + dh
        self._add_step(
            title="Spezifische Enthalpie h₂ₛ",
            formula="h₂ₛ = h₁ + Δh₁₂ₛ",
            calculation=f"h₂ₛ = {self.states[1]['h']:.2f} J/kg + {dh:.2f} J/kg",
            result=h2s,
            unit="J/kg"
        )
        
        # Entropieänderung ist Null bei isentroper Verdichtung
        s2s = self.states[1]["s"]
        self._add_step(
            title="Spezifische Entropie s₂ₛ",
            formula="s₂ₛ = s₁ (isentrope Verdichtung)",
            calculation=f"s₂ₛ = {s2s:.4f} J/(kg·K)",
            result=s2s,
            unit="J/(kg·K)"
        )
        
        return {"p": p2, "T": T2s, "v": v2s, "h": h2s, "s": s2s}
    
    def calculate_state_2(self, p2):
        """
        Berechnet den Zustand 2 (Verdichteraustritt, real)
        
        Parameter:
        p2 : float
            Druck in Pa
        """
        # Bei aktivierter Zwischenkühlung die erweiterte Berechnung verwenden
        if self.intercooling:
            self.calculate_state_2_with_intercooling(p2)
            return
        
        # Sicherstellen, dass p2 ein float ist
        p2 = float(p2)
        
        state_2s = self.calculate_state_2_isentropic(p2)
        self.states["2s"] = state_2s
        
        # Mit isentropem Wirkungsgrad
        h1 = float(self.states[1]["h"])
        h2s = float(state_2s["h"])
        T1 = float(self.states[1]["T"])
        T2s = float(state_2s["T"])
        
        self._add_step(
            title="Zustand 2 (realer Verdichteraustritt)",
            calculation=f"Isentroper Wirkungsgrad des Verdichters: η_c = {self.compressor_efficiency:.4f}"
        )
        
        if self.compressor_efficiency < 1.0:
            # Bestimme den cp-Wert, der für die isentrope Berechnung verwendet wurde
            if self.use_const_cp:
                cp_val = self.cp_const
            else:
                cp_val = (h2s - h1) / (T2s - T1)
                self._add_step(
                    title="Effektiver cp-Wert für isentrope Verdichtung",
                    formula="cp_eff = (h₂ₛ - h₁) / (T₂ₛ - T₁)",
                    calculation=f"cp_eff = ({h2s:.2f} J/kg - {h1:.2f} J/kg) / ({T2s:.2f} K - {T1:.2f} K)",
                    result=cp_val,
                    unit="J/(kg·K)"
                )
            
            # Reale Temperaturänderung mit Wirkungsgrad
            dT_isentrop = T2s - T1
            dT_real = dT_isentrop / self.compressor_efficiency
            self._add_step(
                title="Reale Temperaturänderung ΔT₁₂",
                formula="ΔT₁₂ = (T₂ₛ - T₁) / η_c",
                calculation=f"ΔT₁₂ = ({T2s:.2f} K - {T1:.2f} K) / {self.compressor_efficiency:.4f}",
                result=dT_real,
                unit="K"
            )
            
            # Reale Temperatur am Zustand 2
            T2 = T1 + dT_real
            self._add_step(
                title="Temperatur T₂",
                formula="T₂ = T₁ + ΔT₁₂",
                calculation=f"T₂ = {T1:.2f} K + {dT_real:.2f} K",
                result=T2,
                unit="K"
            )
            
            # Reale Enthalpieänderung berechnen aus Temperaturänderung
            dh_real = cp_val * dT_real
            self._add_step(
                title="Reale Enthalpieänderung Δh₁₂",
                formula="Δh₁₂ = cp · ΔT₁₂",
                calculation=f"Δh₁₂ = {cp_val:.2f} J/(kg·K) · {dT_real:.2f} K",
                result=dh_real,
                unit="J/kg"
            )
            
            # Reale Enthalpie am Zustand 2
            h2 = h1 + dh_real
            self._add_step(
                title="Spezifische Enthalpie h₂",
                formula="h₂ = h₁ + Δh₁₂",
                calculation=f"h₂ = {h1:.2f} J/kg + {dh_real:.2f} J/kg",
                result=h2,
                unit="J/kg"
            )
        else:
            # Bei idealem Wirkungsgrad ist die reale gleich der isentropen Enthalpie
            T2 = T2s
            h2 = h2s
            self._add_step(
                title="Temperatur und Enthalpie T₂, h₂",
                calculation="Bei idealem Wirkungsgrad (η_c = 1) gilt: T₂ = T₂ₛ, h₂ = h₂ₛ",
                result=T2,
                unit="K"
            )
        
        self._add_step(
            title="Temperatur T₂ in °C",
            calculation=f"T₂ = {T2:.2f} K - 273.15",
            result=kelvin_to_celsius(T2),
            unit="°C"
        )
        
        # Spezifisches Volumen berechnen
        v2 = specific_volume(p2, T2, self.gas)
        self._add_step(
            title="Spezifisches Volumen v₂",
            formula="v₂ = R·T₂/p₂",
            calculation=f"v₂ = {self.R:.2f} J/(kg·K) · {T2:.2f} K / {p2:.2f} Pa",
            result=v2,
            unit="m³/kg"
        )
        
        # Entropieänderung berechnen
        if self.use_const_cp:
            ds = self.cp_const * np.log(T2/self.states[1]["T"]) - self.R * np.log(p2/self.states[1]["p"])
            self._add_step(
                title="Entropieänderung Δs₁₂",
                formula="Δs₁₂ = cₚ · ln(T₂/T₁) - R · ln(p₂/p₁)",
                calculation=f"Δs₁₂ = {self.cp_const:.2f} J/(kg·K) · ln({T2:.2f}/{self.states[1]['T']:.2f}) - " +
                         f"{self.R:.2f} J/(kg·K) · ln({p2:.2f}/{self.states[1]['p']:.2f})",
                result=ds,
                unit="J/(kg·K)"
            )
        else:
            # Bei temperaturabhängigem cp müsste man integrieren
            # Hier: vereinfachte Berechnung mit mittlerem cp
            cp_m = cp_mean(self.states[1]["T"], T2, self.gas)
            ds = cp_m * np.log(T2/self.states[1]["T"]) - self.R * np.log(p2/self.states[1]["p"])
            self._add_step(
                title="Entropieänderung Δs₁₂",
                formula="Δs₁₂ = cₚ_m · ln(T₂/T₁) - R · ln(p₂/p₁)",
                calculation=f"Δs₁₂ = {cp_m:.2f} J/(kg·K) · ln({T2:.2f}/{self.states[1]['T']:.2f}) - " +
                         f"{self.R:.2f} J/(kg·K) · ln({p2:.2f}/{self.states[1]['p']:.2f})",
                result=ds,
                unit="J/(kg·K)"
            )
        
        # Entropie am Zustand 2
        s2 = self.states[1]["s"] + ds
        self._add_step(
            title="Spezifische Entropie s₂",
            formula="s₂ = s₁ + Δs₁₂",
            calculation=f"s₂ = {self.states[1]['s']:.4f} J/(kg·K) + {ds:.4f} J/(kg·K)",
            result=s2,
            unit="J/(kg·K)"
        )
        
        self.states[2] = {"p": p2, "T": T2, "v": v2, "h": h2, "s": s2}
    
    def calculate_state_2_with_intercooling(self, p2):
        """
        Berechnet die Zustände für zweistufige Verdichtung mit Zwischenkühlung
        
        Parameter:
        p2 : float
            Enddruck nach zweiter Verdichtungsstufe in Pa
        """
        if 1 not in self.states:
            raise ValueError("Zustand 1 muss zuerst berechnet werden.")
        
        # Sicherstellen, dass p2 ein float ist
        p2 = float(p2)
        p1 = float(self.states[1]["p"])
        T1 = float(self.states[1]["T"])
        
        # Optimalen Zwischendruck bestimmen
        if self.intercooling_pressure_ratio is None:
            # Bei zweistufiger Verdichtung ist der optimale Zwischendruck das geometrische Mittel
            p_intermediate = np.sqrt(p1 * p2)
            pressure_ratio = p_intermediate / p1
            self._add_step(
                title="Optimaler Zwischendruck",
                formula="p_intermediate = sqrt(p1 · p2)",
                calculation=f"p_intermediate = sqrt({p1:.2f} Pa · {p2:.2f} Pa)",
                result=p_intermediate,
                unit="Pa",
                category="Zwischenkühlung"
            )
        else:
            # Benutzerdefiniertes Druckverhältnis
            pressure_ratio = self.intercooling_pressure_ratio
            p_intermediate = p1 * pressure_ratio
            self._add_step(
                title="Benutzerdefinierter Zwischendruck",
                formula="p_intermediate = p1 · intercooling_pressure_ratio",
                calculation=f"p_intermediate = {p1:.2f} Pa · {pressure_ratio:.4f}",
                result=p_intermediate,
                unit="Pa",
                category="Zwischenkühlung"
            )
        
        # Erste Verdichtungsstufe: 1 → 2a
        self._add_step(
            title="Zustand 2a (nach erster Verdichtungsstufe)",
            calculation=f"Erste Verdichtung von p1 = {p1:.2f} Pa auf p2a = {p_intermediate:.2f} Pa",
            category="Zustand 2a"
        )
        
        # Isentrope Temperatur nach erster Verdichtungsstufe berechnen
        k = self.kappa if self.use_const_cp else kappa_mean(T1, T1 * (p_intermediate/p1)**0.2, self.gas)
        T2a_s = T1 * (p_intermediate/p1)**((k-1)/k)
        self._add_step(
            title="Temperatur T₂ₐₛ (isentrop)",
            formula="T₂ₐₛ = T₁ · (p₂ₐ/p₁)^((κ-1)/κ)",
            calculation=f"T₂ₐₛ = {T1:.2f} K · ({p_intermediate/p1:.4f})^(({k:.4f}-1)/{k:.4f})",
            result=T2a_s,
            unit="K",
            category="Zustand 2a"
        )
        
        # Reale Temperatur mit Verdichterwirkungsgrad
        if self.compressor_efficiency < 1.0:
            dT_isentrop_1 = T2a_s - T1
            dT_real_1 = dT_isentrop_1 / self.compressor_efficiency
            T2a = T1 + dT_real_1
            self._add_step(
                title="Reale Temperaturänderung ΔT₁₂ₐ",
                formula="ΔT₁₂ₐ = (T₂ₐₛ - T₁) / η_c",
                calculation=f"ΔT₁₂ₐ = ({T2a_s:.2f} K - {T1:.2f} K) / {self.compressor_efficiency:.4f}",
                result=dT_real_1,
                unit="K",
                category="Zustand 2a"
            )
            self._add_step(
                title="Temperatur T₂ₐ",
                formula="T₂ₐ = T₁ + ΔT₁₂ₐ",
                calculation=f"T₂ₐ = {T1:.2f} K + {dT_real_1:.2f} K",
                result=T2a,
                unit="K",
                category="Zustand 2a"
            )
        else:
            T2a = T2a_s
            self._add_step(
                title="Temperatur T₂ₐ",
                calculation="Bei idealem Wirkungsgrad (η_c = 1) gilt: T₂ₐ = T₂ₐₛ",
                result=T2a,
                unit="K",
                category="Zustand 2a"
            )
        
        # Weitere Zustandsgrößen für 2a berechnen
        v2a = specific_volume(p_intermediate, T2a, self.gas)
        cp_val = self.cp_const if self.use_const_cp else cp_mean(T1, T2a, self.gas)
        dh_1_2a = cp_val * (T2a - T1)
        h2a = self.states[1]["h"] + dh_1_2a
        
        if self.compressor_efficiency < 1.0:
            # Entropieänderung bei realer Verdichtung
            if self.use_const_cp:
                ds_1_2a = self.cp_const * np.log(T2a/T1) - self.R * np.log(p_intermediate/p1)
            else:
                cp_m = cp_mean(T1, T2a, self.gas)
                ds_1_2a = cp_m * np.log(T2a/T1) - self.R * np.log(p_intermediate/p1)
            s2a = self.states[1]["s"] + ds_1_2a
        else:
            # Bei isentroper Verdichtung bleibt die Entropie konstant
            s2a = self.states[1]["s"]
        
        self.states["2a"] = {"p": p_intermediate, "T": T2a, "v": v2a, "h": h2a, "s": s2a}
        self.states["2a_s"] = {"p": p_intermediate, "T": T2a_s, "v": specific_volume(p_intermediate, T2a_s, self.gas),
                              "h": self.states[1]["h"] + cp_val * (T2a_s - T1), "s": self.states[1]["s"]}
        
        # Zwischenkühlung: 2a → 2b
        self._add_step(
            title="Zustand 2b (nach Zwischenkühlung)",
            calculation=f"Zwischenkühlung bei konstantem Druck p2b = {p_intermediate:.2f} Pa",
            category="Zustand 2b"
        )
        
        # Temperatur nach Zwischenkühlung
        if self.intercooling_temperature is None:
            T2b = T1  # Kühlung zurück auf Ansaugtemperatur
            self._add_step(
                title="Temperatur nach Zwischenkühlung",
                calculation=f"T₂ᵦ = T₁ = {T2b:.2f} K (Kühlung auf Ansaugtemperatur)",
                result=T2b,
                unit="K",
                category="Zustand 2b"
            )
        else:
            T2b = self.intercooling_temperature
            self._add_step(
                title="Temperatur nach Zwischenkühlung",
                calculation=f"T₂ᵦ = {T2b:.2f} K (Benutzerdefinierte Temperatur)",
                result=T2b,
                unit="K",
                category="Zustand 2b"
            )
        
        # Weitere Zustandsgrößen für 2b berechnen
        v2b = specific_volume(p_intermediate, T2b, self.gas)
        cp_val = self.cp_const if self.use_const_cp else cp_mean(T2a, T2b, self.gas)
        dh_2a_2b = cp_val * (T2b - T2a)
        h2b = h2a + dh_2a_2b
        
        # Entropieänderung bei isobarer Kühlung
        if self.use_const_cp:
            ds_2a_2b = self.cp_const * np.log(T2b/T2a)
        else:
            cp_m = cp_mean(T2a, T2b, self.gas)
            ds_2a_2b = cp_m * np.log(T2b/T2a)
        s2b = s2a + ds_2a_2b
        
        self.states["2b"] = {"p": p_intermediate, "T": T2b, "v": v2b, "h": h2b, "s": s2b}
        
        # Zweite Verdichtungsstufe: 2b → 2c
        self._add_step(
            title="Zustand 2c (nach zweiter Verdichtungsstufe)",
            calculation=f"Zweite Verdichtung von p2b = {p_intermediate:.2f} Pa auf p2c = {p2:.2f} Pa",
            category="Zustand 2c"
        )
        
        # Isentrope Temperatur nach zweiter Verdichtungsstufe berechnen
        k = self.kappa if self.use_const_cp else kappa_mean(T2b, T2b * (p2/p_intermediate)**0.2, self.gas)
        T2c_s = T2b * (p2/p_intermediate)**((k-1)/k)
        self._add_step(
            title="Temperatur T₂ₖₛ (isentrop)",
            formula="T₂ₖₛ = T₂ᵦ · (p₂ₖ/p₂ᵦ)^((κ-1)/κ)",
            calculation=f"T₂ₖₛ = {T2b:.2f} K · ({p2/p_intermediate:.4f})^(({k:.4f}-1)/{k:.4f})",
            result=T2c_s,
            unit="K",
            category="Zustand 2c"
        )
        
        # Reale Temperatur mit Verdichterwirkungsgrad
        if self.compressor_efficiency < 1.0:
            dT_isentrop_2 = T2c_s - T2b
            dT_real_2 = dT_isentrop_2 / self.compressor_efficiency
            T2c = T2b + dT_real_2
            self._add_step(
                title="Reale Temperaturänderung ΔT₂ᵦ₂ₖ",
                formula="ΔT₂ᵦ₂ₖ = (T₂ₖₛ - T₂ᵦ) / η_c",
                calculation=f"ΔT₂ᵦ₂ₖ = ({T2c_s:.2f} K - {T2b:.2f} K) / {self.compressor_efficiency:.4f}",
                result=dT_real_2,
                unit="K",
                category="Zustand 2c"
            )
            self._add_step(
                title="Temperatur T₂ₖ",
                formula="T₂ₖ = T₂ᵦ + ΔT₂ᵦ₂ₖ",
                calculation=f"T₂ₖ = {T2b:.2f} K + {dT_real_2:.2f} K",
                result=T2c,
                unit="K",
                category="Zustand 2c"
            )
        else:
            T2c = T2c_s
            self._add_step(
                title="Temperatur T₂ₖ",
                calculation="Bei idealem Wirkungsgrad (η_c = 1) gilt: T₂ₖ = T₂ₖₛ",
                result=T2c,
                unit="K",
                category="Zustand 2c"
            )
        
        # Weitere Zustandsgrößen für 2c berechnen
        v2c = specific_volume(p2, T2c, self.gas)
        cp_val = self.cp_const if self.use_const_cp else cp_mean(T2b, T2c, self.gas)
        dh_2b_2c = cp_val * (T2c - T2b)
        h2c = h2b + dh_2b_2c
        
        if self.compressor_efficiency < 1.0:
            # Entropieänderung bei realer Verdichtung
            if self.use_const_cp:
                ds_2b_2c = self.cp_const * np.log(T2c/T2b) - self.R * np.log(p2/p_intermediate)
            else:
                cp_m = cp_mean(T2b, T2c, self.gas)
                ds_2b_2c = cp_m * np.log(T2c/T2b) - self.R * np.log(p2/p_intermediate)
            s2c = s2b + ds_2b_2c
        else:
            # Bei isentroper Verdichtung bleibt die Entropie konstant
            s2c = s2b
        
        self.states["2c"] = {"p": p2, "T": T2c, "v": v2c, "h": h2c, "s": s2c}
        self.states["2c_s"] = {"p": p2, "T": T2c_s, "v": specific_volume(p2, T2c_s, self.gas),
                              "h": h2b + cp_val * (T2c_s - T2b), "s": s2b}
        
        # Zustand 2c als Zustand 2 speichern für die Kompatibilität mit dem restlichen Code
        self.states[2] = self.states["2c"].copy()
    
    def calculate_state_3(self, p3, T3):
        """
        Berechnet den Zustand 3 (Turbineneintritt)
        
        Parameter:
        p3 : float
            Druck in Pa
        T3 : float
            Temperatur in K
        """
        # Sicherstellen, dass die Werte float sind
        p3 = float(p3)
        T3 = float(T3)
        
        self._add_step(
            title="Zustand 3 (Turbineneintritt)",
            calculation=f"p₃ = {pascal_to_bar(p3):.4f} bar = {p3:.2f} Pa, " +
                      f"T₃ = {kelvin_to_celsius(T3):.2f} °C = {T3:.2f} K",
            category="Zustand 3"
        )
        
        # Spezifisches Volumen berechnen
        v3 = specific_volume(p3, T3, self.gas)
        self._add_step(
            title="Spezifisches Volumen v₃",
            formula="v₃ = R·T₃/p₃",
            calculation=f"v₃ = {self.R:.2f} J/(kg·K) · {T3:.2f} K / {p3:.2f} Pa",
            result=v3,
            unit="m³/kg",
            category="Zustand 3"
        )
        
        # Enthalpieänderung berechnen
        cp_val = self.cp_const if self.use_const_cp else cp_mean(self.states[2]["T"], T3, self.gas)
        dh = cp_val * (T3 - self.states[2]["T"])
        self._add_step(
            title="Spezifische Wärmekapazität cₚ",
            formula="cₚ = const" if self.use_const_cp else "cₚ = f(T)",
            calculation=f"cₚ = {cp_val:.2f} J/(kg·K)",
            result=cp_val,
            unit="J/(kg·K)",
            category="Zustand 3"
        )
        self._add_step(
            title="Enthalpiedifferenz Δh₂₃",
            formula="Δh₂₃ = cₚ · (T₃ - T₂)",
            calculation=f"Δh₂₃ = {cp_val:.2f} J/(kg·K) · ({T3:.2f} K - {self.states[2]['T']:.2f} K)",
            result=dh,
            unit="J/kg",
            category="Zustand 3"
        )
        
        # Enthalpie am Zustand 3
        h3 = self.states[2]["h"] + dh
        self._add_step(
            title="Spezifische Enthalpie h₃",
            formula="h₃ = h₂ + Δh₂₃",
            calculation=f"h₃ = {self.states[2]['h']:.2f} J/kg + {dh:.2f} J/kg",
            result=h3,
            unit="J/kg",
            category="Zustand 3"
        )
        
        # Entropieänderung berechnen
        if self.use_const_cp:
            ds = self.cp_const * np.log(T3/self.states[2]["T"]) - self.R * np.log(p3/self.states[2]["p"])
            self._add_step(
                title="Entropieänderung Δs₂₃",
                formula="Δs₂₃ = cₚ · ln(T₃/T₂) - R · ln(p₃/p₂)",
                calculation=f"Δs₂₃ = {self.cp_const:.2f} J/(kg·K) · ln({T3:.2f}/{self.states[2]['T']:.2f}) - " +
                         f"{self.R:.2f} J/(kg·K) · ln({p3:.2f}/{self.states[2]['p']:.2f})",
                result=ds,
                unit="J/(kg·K)",
                category="Zustand 3"
            )
        else:
            # Bei temperaturabhängigem cp müsste man integrieren
            # Hier: vereinfachte Berechnung mit mittlerem cp
            cp_m = cp_mean(self.states[2]["T"], T3, self.gas)
            ds = cp_m * np.log(T3/self.states[2]["T"]) - self.R * np.log(p3/self.states[2]["p"])
            self._add_step(
                title="Entropieänderung Δs₂₃",
                formula="Δs₂₃ = cₚ_m · ln(T₃/T₂) - R · ln(p₃/p₂)",
                calculation=f"Δs₂₃ = {cp_m:.2f} J/(kg·K) · ln({T3:.2f}/{self.states[2]['T']:.2f}) - " +
                         f"{self.R:.2f} J/(kg·K) · ln({p3:.2f}/{self.states[2]['p']:.2f})",
                result=ds,
                unit="J/(kg·K)",
                category="Zustand 3"
            )
    
        # Entropie am Zustand 3
        s3 = self.states[2]["s"] + ds
        self._add_step(
            title="Spezifische Entropie s₃",
            formula="s₃ = s₂ + Δs₂₃",
            calculation=f"s₃ = {self.states[2]['s']:.4f} J/(kg·K) + {ds:.4f} J/(kg·K)",
            result=s3,
            unit="J/(kg·K)",
            category="Zustand 3"
        )
        
        self.states[3] = {"p": p3, "T": T3, "v": v3, "h": h3, "s": s3}

    def calculate_state_4_isentropic(self, p4):
        """
        Berechnet den Zustand 4s (Turbinenaustritt, isentrop)
        
        Parameter:
        p4 : float
            Druck in Pa
            
        Returns:
        dict:
            Dictionary mit den Zustandsgrößen für den isentropen Zustand 4s
        """
        if 3 not in self.states:
            raise ValueError("Zustand 3 muss zuerst berechnet werden.")
        
        # Sicherstellen, dass p4 ein float ist
        p4 = float(p4)
        
        p3 = float(self.states[3]["p"])
        T3 = float(self.states[3]["T"])
        
        self._add_step(
            title="Zustand 4s (isentroper Turbinenaustritt)",
            calculation=f"p₄ = {pascal_to_bar(p4):.4f} bar = {p4:.2f} Pa"
        )
        
        # Isentroper Exponent für die Expansion
        k = self.kappa if self.use_const_cp else kappa_mean(T3, T3 * (p4/p3)**0.2, self.gas)
        self._add_step(
            title="Isentropenexponent κ für die Expansion",
            formula="κ = cp/cv" if not self.use_const_cp else "κ = const",
            calculation=f"κ = {k:.4f}" + (" (konstant)" if self.use_const_cp else ""),
            result=k,
            unit=""
        )
        
        # Temperatur berechnen mit der isentropen Zustandsgleichung
        T4s = T3 * (p4/p3)**((k-1)/k)
        self._add_step(
            title="Temperatur T₄ₛ (isentrop)",
            formula="T₄ₛ = T₃ · (p₄/p₃)^((κ-1)/κ)",
            calculation=f"T₄ₛ = {T3:.2f} K · ({p4/p3:.4f})^(({k:.4f}-1)/{k:.4f})",
            result=T4s,
            unit="K"
        )
        self._add_step(
            title="Temperatur T₄ₛ in °C",
            calculation=f"T₄ₛ = {T4s:.2f} K - 273.15",
            result=kelvin_to_celsius(T4s),
            unit="°C"
        )
        
        # Spezifisches Volumen berechnen
        v4s = specific_volume(p4, T4s, self.gas)
        self._add_step(
            title="Spezifisches Volumen v₄ₛ",
            formula="v₄ₛ = R·T₄ₛ/p₄",
            calculation=f"v₄ₛ = {self.R:.2f} J/(kg·K) · {T4s:.2f} K / {p4:.2f} Pa",
            result=v4s,
            unit="m³/kg"
        )
        
        # Enthalpiedifferenz berechnen
        cp_val = self.cp_const if self.use_const_cp else cp_mean(T3, T4s, self.gas)
        dh = cp_val * (T4s - T3)
        self._add_step(
            title="Spezifische Wärmekapazität cₚ",
            formula="cₚ = const" if self.use_const_cp else "cₚ = f(T)",
            calculation=f"cₚ = {cp_val:.2f} J/(kg·K)",
            result=cp_val,
            unit="J/(kg·K)"
        )
        self._add_step(
            title="Enthalpiedifferenz Δh₃₄ₛ",
            formula="Δh₃₄ₛ = cₚ · (T₄ₛ - T₃)",
            calculation=f"Δh₃₄ₛ = {cp_val:.2f} J/(kg·K) · ({T4s:.2f} K - {T3:.2f} K)",
            result=dh,
            unit="J/kg"
        )
        
        # Enthalpie am Zustand 4s
        h4s = self.states[3]["h"] + dh
        self._add_step(
            title="Spezifische Enthalpie h₄ₛ",
            formula="h₄ₛ = h₃ + Δh₃₄ₛ",
            calculation=f"h₄ₛ = {self.states[3]['h']:.2f} J/kg + {dh:.2f} J/kg",
            result=h4s,
            unit="J/kg"
        )
        
        # Entropieänderung ist Null bei isentroper Expansion
        s4s = self.states[3]["s"]
        self._add_step(
            title="Spezifische Entropie s₄ₛ",
            formula="s₄ₛ = s₃ (isentrope Expansion)",
            calculation=f"s₄ₛ = {s4s:.4f} J/(kg·K)",
            result=s4s,
            unit="J/(kg·K)"
        )
        
        return {"p": p4, "T": T4s, "v": v4s, "h": h4s, "s": s4s}

    def calculate_state_4(self, p4):
        """
        Berechnet den Zustand 4 (Turbinenaustritt, real)
        
        Parameter:
        p4 : float
            Druck in Pa
        """
        # Sicherstellen, dass p4 ein float ist
        p4 = float(p4)
        
        state_4s = self.calculate_state_4_isentropic(p4)
        self.states["4s"] = state_4s
        
        # Mit isentropem Wirkungsgrad
        h3 = float(self.states[3]["h"])
        h4s = float(state_4s["h"])
        T3 = float(self.states[3]["T"])
        T4s = float(state_4s["T"])
        
        self._add_step(
            title="Zustand 4 (realer Turbinenaustritt)",
            calculation=f"Isentroper Wirkungsgrad der Turbine: η_t = {self.turbine_efficiency:.4f}"
        )
        
        if self.turbine_efficiency < 1.0:
            # Bestimme den cp-Wert, der für die isentrope Berechnung verwendet wurde
            if self.use_const_cp:
                cp_val = self.cp_const
            else:
                cp_val = (h4s - h3) / (T4s - T3)
                self._add_step(
                    title="Effektiver cp-Wert für isentrope Expansion",
                    formula="cp_eff = (h₄ₛ - h₃) / (T₄ₛ - T₃)",
                    calculation=f"cp_eff = ({h4s:.2f} J/kg - {h3:.2f} J/kg) / ({T4s:.2f} K - {T3:.2f} K)",
                    result=cp_val,
                    unit="J/(kg·K)"
                )
            
            # KORRIGIERT: Reale Temperaturänderung mit Wirkungsgrad
            # Bei einer Turbine ist T3 > T4s und die Differenz ist positiv
            dT_isentrop = T3 - T4s  # Diese Differenz ist positiv
            dT_real = dT_isentrop * self.turbine_efficiency
            
            self._add_step(
                title="Reale Temperaturänderung ΔT₃₄",
                formula="ΔT₃₄ = (T₃ - T₄ₛ) · η_t",  # Korrigierte Formel
                calculation=f"ΔT₃₄ = ({T3:.2f} K - {T4s:.2f} K) · {self.turbine_efficiency:.4f}",
                result=dT_real,
                unit="K"
            )
            
            # KORRIGIERT: Reale Temperatur am Zustand 4
            # Die reale Temperatur nach der Expansion ist geringer als die Eintrittstemperatur
            T4 = T3 - dT_real  # Beachte das Minus-Zeichen
            
            self._add_step(
                title="Temperatur T₄",
                formula="T₄ = T₃ - ΔT₃₄",  # Korrigierte Formel
                calculation=f"T₄ = {T3:.2f} K - {dT_real:.2f} K",
                result=T4,
                unit="K"
            )
            
            # Reale Enthalpieänderung berechnen aus Temperaturänderung
            dh_real = cp_val * (T4 - T3)  # Da T4 < T3, ist dies negativ
            
            self._add_step(
                title="Reale Enthalpieänderung Δh₃₄",
                formula="Δh₃₄ = cp · (T₄ - T₃)",
                calculation=f"Δh₃₄ = {cp_val:.2f} J/(kg·K) · ({T4:.2f} K - {T3:.2f} K)",
                result=dh_real,
                unit="J/kg"
            )
            
            # Reale Enthalpie am Zustand 4
            h4 = h3 + dh_real
            self._add_step(
                title="Spezifische Enthalpie h₄",
                formula="h₄ = h₃ + Δh₃₄",
                calculation=f"h₄ = {h3:.2f} J/kg + {dh_real:.2f} J/kg",
                result=h4,
                unit="J/kg"
            )
        else:
            # Bei idealem Wirkungsgrad ist die reale gleich der isentropen Enthalpie
            T4 = T4s
            h4 = h4s
            self._add_step(
                title="Temperatur und Enthalpie T₄, h₄",
                calculation="Bei idealem Wirkungsgrad (η_t = 1) gilt: T₄ = T₄ₛ, h₄ = h₄ₛ",
                result=T4,
                unit="K"
            )
        
        self._add_step(
            title="Temperatur T₄ in °C",
            calculation=f"T₄ = {T4:.2f} K - 273.15",
            result=kelvin_to_celsius(T4),
            unit="°C"
        )
        
        # Spezifisches Volumen berechnen
        v4 = specific_volume(p4, T4, self.gas)
        self._add_step(
            title="Spezifisches Volumen v₄",
            formula="v₄ = R·T₄/p₄",
            calculation=f"v₄ = {self.R:.2f} J/(kg·K) · {T4:.2f} K / {p4:.2f} Pa",
            result=v4,
            unit="m³/kg"
        )
        
        # Entropieänderung berechnen
        if self.use_const_cp:
            ds = self.cp_const * np.log(T4/self.states[3]["T"]) - self.R * np.log(p4/self.states[3]["p"])
            self._add_step(
                title="Entropieänderung Δs₃₄",
                formula="Δs₃₄ = cₚ · ln(T₄/T₃) - R · ln(p₄/p₃)",
                calculation=f"Δs₃₄ = {self.cp_const:.2f} J/(kg·K) · ln({T4:.2f}/{self.states[3]['T']:.2f}) - " +
                         f"{self.R:.2f} J/(kg·K) · ln({p4:.2f}/{self.states[3]['p']:.2f})",
                result=ds,
                unit="J/(kg·K)"
            )
        else:
            # Bei temperaturabhängigem cp müsste man integrieren
            # Hier: vereinfachte Berechnung mit mittlerem cp
            cp_m = cp_mean(self.states[3]["T"], T4, self.gas)
            ds = cp_m * np.log(T4/self.states[3]["T"]) - self.R * np.log(p4/self.states[3]["p"])
            self._add_step(
                title="Entropieänderung Δs₃₄",
                formula="Δs₃₄ = cₚ_m · ln(T₄/T₃) - R · ln(p₄/p₃)",
                calculation=f"Δs₃₄ = {cp_m:.2f} J/(kg·K) · ln({T4:.2f}/{self.states[3]['T']:.2f}) - " +
                         f"{self.R:.2f} J/(kg·K) · ln({p4:.2f}/{self.states[3]['p']:.2f})",
                result=ds,
                unit="J/(kg·K)"
            )
        
        # Entropie am Zustand 4
        s4 = self.states[3]["s"] + ds
        self._add_step(
            title="Spezifische Entropie s₄",
            formula="s₄ = s₃ + Δs₃₄",
            calculation=f"s₄ = {self.states[3]['s']:.4f} J/(kg·K) + {ds:.4f} J/(kg·K)",
            result=s4,
            unit="J/(kg·K)"
        )
        
        self.states[4] = {"p": p4, "T": T4, "v": v4, "h": h4, "s": s4}

    def calculate_optimal_pressure_ratio(self):
        """
        Berechnet das optimale Druckverhältnis für maximalen thermischen Wirkungsgrad
        
        Returns:
        tuple:
            (pi_opt, T2_opt) - Optimales Druckverhältnis und resultierende T2-Temperatur
        """
        # Für konstante Stoffwerte (ideales Gas) gilt: pi_opt = (T3/T1)^(kappa/(2*(kappa-1)))
        T1 = float(self.states[1]["T"])
        T3 = float(self.states[3]["T"]) if 3 in self.states else None
        
        if T3 is None:
            self._add_step(
                title="Optimales Druckverhältnis konnte nicht berechnet werden",
                calculation="Zustand 3 wurde noch nicht berechnet.",
                result=None
            )
            return None, None
        
        if self.use_const_cp:
            # Mit konstantem Kappa
            kappa = self.kappa
            pi_opt = (T3/T1)**(kappa/(2*(kappa-1)))
            self._add_step(
                title="Optimales Druckverhältnis π_opt",
                formula="π_opt = (T₃/T₁)^(κ/(2*(κ-1)))",
                calculation=f"π_opt = ({T3:.2f}/{T1:.2f})^({kappa:.4f}/(2*({kappa:.4f}-1)))",
                result=pi_opt,
                unit=""
            )
        else:
            # Bei temperaturabhängigem kappa müsste man iterativ vorgehen
            # Hier: vereinfachte Berechnung mit mittlerem kappa
            kappa = kappa_mean(T1, T3, self.gas)  # Ändere kappa_m zu kappa
            pi_opt = (T3/T1)**(kappa/(2*(kappa-1)))  # Ändere kappa_m zu kappa
            self._add_step(
                title="Optimales Druckverhältnis π_opt",
                formula="π_opt = (T₃/T₁)^(κ_m/(2*(κ_m-1)))",
                calculation=f"π_opt = ({T3:.2f}/{T1:.2f})^({kappa:.4f}/(2*({kappa:.4f}-1)))",  # Ändere kappa_m zu kappa
                result=pi_opt,
                unit=""
            )
        
        # Berechnung der optimalen T2-Temperatur
        if self.use_const_cp:
            T2_opt = T1 * pi_opt**((self.kappa-1)/self.kappa)
        else:
            # Vereinfachte Berechnung
            kappa_12 = kappa_mean(T1, T1 * pi_opt**0.3, self.gas)  # Schätzung für kappa im Bereich 1-2
            T2_opt = T1 * pi_opt**((kappa_12-1)/kappa_12)
        
        self._add_step(
            title="Optimale Temperatur T₂",
            formula="T₂_opt = T₁ · π_opt^((κ-1)/κ)",
            calculation=f"T₂_opt = {T1:.2f} K · {pi_opt:.4f}^(({kappa:.4f}-1)/{kappa:.4f})",
            result=T2_opt,
            unit="K"
        )
        
        return pi_opt, T2_opt

    def calculate_regeneration(self, pinch_point=0.0):
        """
        Berechnet die Zustände bei Regeneration (Wärmerückgewinnung)
        
        Parameter:
        pinch_point : float
            Minimale Temperaturdifferenz am Wärmeübertrager in K
        """
        if not self.regeneration or self.reg_eff <= 0:
            return
        
        if not all(i in self.states for i in [2, 4]):
            raise ValueError("Zustände 2 und 4 müssen zuerst berechnet werden.")
        
        self._add_step(
            title="Regeneration (Wärmerückgewinnung)",
            calculation=f"Wirkungsgrad der Regeneration: η_reg = {self.reg_eff:.4f}" +
                      (f", Pinch-Point: {pinch_point:.2f} K" if pinch_point > 0 else ""),
            category="Regeneration"
        )
        
        # Temperatur nach Verdichter und vor Wärmeübertrager (2)
        # Explizite Float-Konvertierung
        T2 = float(self.states[2]["T"])
        
        # Temperatur nach Turbine und vor Wärmeübertrager (4)
        # Explizite Float-Konvertierung
        T4 = float(self.states[4]["T"])
        
        # Explizite Float-Konvertierung für pinch_point
        pinch_point = float(pinch_point)
        
        self._add_step(
            title="Temperaturen für Regeneration",
            calculation=f"T₂ = {T2:.2f} K, T₄ = {T4:.2f} K, Pinch-Point = {pinch_point:.2f} K",
            category="Regeneration"
        )
        
        # KORRIGIERT: Überprüfen, ob Regeneration möglich ist
        # Die Temperatur nach der Turbine (T4) muss höher sein als die Temperatur nach dem Verdichter (T2)
        # plus der Pinch-Point-Temperatur, damit Wärme übertragen werden kann
        if T4 <= T2 + pinch_point:
            self._add_step(
                title="Keine Regeneration möglich",
                calculation=f"T₄ = {T4:.2f} K ≤ T₂ + Pinch-Point = {T2:.2f} K + {pinch_point:.2f} K = {T2 + pinch_point:.2f} K",
                category="Regeneration"
            )
            return
        
        # Berechnung der neuen Temperaturen unter Berücksichtigung des Pinch-Points
        if pinch_point > 0:
            # Bei vorgegebenem Pinch-Point
            T2_star_max = T4 - pinch_point  # Maximale T2* unter Berücksichtigung des Pinch-Points
            T2_star_reg = T2 + self.reg_eff * (T4 - T2)  # T2* mit Regenerationseffizienz
            T2_star = min(T2_star_max, T2_star_reg)  # Die niedrigere der beiden Temperaturen
            
            self._add_step(
                title="Maximale Temperatur T₂* (Pinch-Point-Beschränkung)",
                formula="T₂*_max = T₄ - Pinch-Point",
                calculation=f"T₂*_max = {T4:.2f} K - {pinch_point:.2f} K",
                result=T2_star_max,
                unit="K",
                category="Regeneration"
            )
        else:
            # Ohne Pinch-Point, nur mit Regenerationseffizienz
            T2_star = T2 + self.reg_eff * (T4 - T2)
            T2_star = min(T2_star, T4)  # Die Temperatur 2* kann nicht höher sein als T4
        
        self._add_step(
            title="Temperatur T₂* nach Regeneration (Hochdruckseite)",
            formula="T₂* = min(T₂ + η_reg · (T₄ - T₂), T₄ - Pinch-Point)" if pinch_point > 0 else "T₂* = T₂ + η_reg · (T₄ - T₂)",
            calculation=f"T₂* = min({T2:.2f} K + {self.reg_eff:.4f} · ({T4:.2f} K - {T2:.2f} K), {T4:.2f} K - {pinch_point:.2f} K)" if pinch_point > 0 else f"T₂* = {T2:.2f} K + {self.reg_eff:.4f} · ({T4:.2f} K - {T2:.2f} K)",
            result=T2_star,
            unit="K",
            category="Regeneration"
        )
        
        # Temperatur nach Regeneration auf der Niederdruckseite (4*)
        # Wärmebilanz: cp · (T2* - T2) = cp · (T4 - T4*)
        # => T4* = T4 - (T2* - T2)
        T4_star = T4 - (T2_star - T2)
        
        self._add_step(
            title="Temperatur T₄* nach Regeneration (Niederdruckseite)",
            formula="T₄* = T₄ - (T₂* - T₂)",
            calculation=f"T₄* = {T4:.2f} K - ({T2_star:.2f} K - {T2:.2f} K)",
            result=T4_star,
            unit="K",
            category="Regeneration"
        )
        
        # Berechnung der neuen Zustandsgrößen für 2*
        p2_star = self.states[2]["p"]  # Druck bleibt konstant
        v2_star = specific_volume(p2_star, T2_star, self.gas)
        
        # Enthalpieänderung 2 -> 2*
        cp_val = self.cp_const if self.use_const_cp else cp_mean(T2, T2_star, self.gas)
        dh_2_2star = cp_val * (T2_star - T2)
        
        self._add_step(
            title="Enthalpieänderung Δh₂₂*",
            formula="Δh₂₂* = cₚ · (T₂* - T₂)",
            calculation=f"Δh₂₂* = {cp_val:.2f} J/(kg·K) · ({T2_star:.2f} K - {T2:.2f} K)",
            result=dh_2_2star,
            unit="J/kg",
            category="Regeneration"
        )
        
        h2_star = self.states[2]["h"] + dh_2_2star
        
        # Entropieänderung 2 -> 2* (isobar)
        if self.use_const_cp:
            ds_2_2star = self.cp_const * np.log(T2_star/T2)
        else:
            cp_m = cp_mean(T2, T2_star, self.gas)
            ds_2_2star = cp_m * np.log(T2_star/T2)

        self._add_step(
            title="Entropieänderung Δs₂₂* (isobar)",
            formula="Δs₂₂* = cₚ · ln(T₂*/T₂)",
            calculation=f"Δs₂₂* = {cp_val:.2f} J/(kg·K) · ln({T2_star:.2f}/{T2:.2f})",
            result=ds_2_2star,
            unit="J/(kg·K)",
            category="Regeneration"
        )
        
        s2_star = self.states[2]["s"] + ds_2_2star
        
        # Zustand 2* speichern
        self.states["2*"] = {"p": p2_star, "T": T2_star, "v": v2_star, "h": h2_star, "s": s2_star}
        
        # Berechnung der neuen Zustandsgrößen für 4*
        p4_star = self.states[4]["p"]  # Druck bleibt konstant
        v4_star = specific_volume(p4_star, T4_star, self.gas)
        
        # Enthalpieänderung 4 -> 4*
        cp_val = self.cp_const if self.use_const_cp else cp_mean(T4, T4_star, self.gas)
        dh_4_4star = cp_val * (T4_star - T4)
        
        self._add_step(
            title="Enthalpieänderung Δh₄₄*",
            formula="Δh₄₄* = cₚ · (T₄* - T₄)",
            calculation=f"Δh₄₄* = {cp_val:.2f} J/(kg·K) · ({T4_star:.2f} K - {T4:.2f} K)",
            result=dh_4_4star,
            unit="J/kg",
            category="Regeneration"
        )
        
        h4_star = self.states[4]["h"] + dh_4_4star
        
        # Entropieänderung 4 -> 4* (isobar)
        if self.use_const_cp:
            ds_4_4star = self.cp_const * np.log(T4_star/T4)
        else:
            cp_m = cp_mean(T4, T4_star, self.gas)
            ds_4_4star = cp_m * np.log(T4_star/T4)

        self._add_step(
            title="Entropieänderung Δs₄₄* (isobar)",
            formula="Δs₄₄* = cₚ · ln(T₄*/T₄)",
            calculation=f"Δs₄₄* = {cp_val:.2f} J/(kg·K) · ln({T4_star:.2f}/{T4:.2f})",
            result=ds_4_4star,
            unit="J/(kg·K)",
            category="Regeneration"
        )
        
        s4_star = self.states[4]["s"] + ds_4_4star
        
        # Zustand 4* speichern
        self.states["4*"] = {"p": p4_star, "T": T4_star, "v": v4_star, "h": h4_star, "s": s4_star}
    
    def calculate_process_properties(self):
        """
        Berechnet die Prozesseigenschaften wie Arbeit, Wärme und Wirkungsgrad
        
        Returns:
        dict:
            Dictionary mit den Prozesseigenschaften
        """
        # Prüfen, ob Zwischenkühlung verwendet wurde
        has_intercooling = "2a" in self.states and "2b" in self.states and "2c" in self.states
        
        if has_intercooling:
            # Verdichterarbeit erste Stufe (negativ, da zugeführt)
            w_comp1 = self.states[1]["h"] - self.states["2a"]["h"]
            self._add_step(
                title="Spezifische Verdichterarbeit erste Stufe w_c1",
                formula="w_c1 = h₁ - h₂ₐ",
                calculation=f"w_c1 = {self.states[1]['h']:.2f} J/kg - {self.states['2a']['h']:.2f} J/kg",
                result=w_comp1,
                unit="J/kg"
            )
            
            # Verdichterarbeit zweite Stufe (negativ, da zugeführt)
            w_comp2 = self.states["2b"]["h"] - self.states["2c"]["h"]
            self._add_step(
                title="Spezifische Verdichterarbeit zweite Stufe w_c2",
                formula="w_c2 = h₂ᵦ - h₂ₖ",
                calculation=f"w_c2 = {self.states['2b']['h']:.2f} J/kg - {self.states['2c']['h']:.2f} J/kg",
                result=w_comp2,
                unit="J/kg"
            )
            
            # Gesamte Verdichterarbeit
            w_comp = w_comp1 + w_comp2
            self._add_step(
                title="Gesamte spezifische Verdichterarbeit w_c",
                formula="w_c = w_c1 + w_c2",
                calculation=f"w_c = {w_comp1:.2f} J/kg + {w_comp2:.2f} J/kg",
                result=w_comp,
                unit="J/kg"
            )
            
            # Wärmeabfuhr bei Zwischenkühlung (positiv, da abgeführt)
            q_intercool = self.states["2a"]["h"] - self.states["2b"]["h"]
            self._add_step(
                title="Spezifische Wärmeabfuhr bei Zwischenkühlung q_intercool",
                formula="q_intercool = h₂ₐ - h₂ᵦ",
                calculation=f"q_intercool = {self.states['2a']['h']:.2f} J/kg - {self.states['2b']['h']:.2f} J/kg",
                result=q_intercool,
                unit="J/kg"
            )
        else:
            # Standardberechnung für einstufige Verdichtung
            w_comp = self.states[1]["h"] - self.states[2]["h"]
            self._add_step(
                title="Spezifische Verdichterarbeit w_c",
                formula="w_c = h₁ - h₂",
                calculation=f"w_c = {self.states[1]['h']:.2f} J/kg - {self.states[2]['h']:.2f} J/kg",
                result=w_comp,
                unit="J/kg"
            )
        
        # Spezifische Turbinenarbeit (positiv, da abgegeben)
        w_turb = self.states[3]["h"] - self.states[4]["h"]
        self._add_step(
            title="Spezifische Turbinenarbeit w_t",
            formula="w_t = h₃ - h₄",
            calculation=f"w_t = {self.states[3]['h']:.2f} J/kg - {self.states[4]['h']:.2f} J/kg",
            result=w_turb,
            unit="J/kg"
        )
        
        # Spezifische Kreisprozessarbeit
        w_kp = w_comp + w_turb
        self._add_step(
            title="Spezifische Kreisprozessarbeit w_KP",
            formula="w_KP = w_c + w_t",
            calculation=f"w_KP = {w_comp:.2f} J/kg + {w_turb:.2f} J/kg",
            result=w_kp,
            unit="J/kg"
        )
        
        # Spezifische Wärmezufuhr
        if self.regeneration and "2*" in self.states:
            q_in = self.states[3]["h"] - self.states["2*"]["h"]
            self._add_step(
                title="Spezifische Wärmezufuhr q_zu",
                formula="q_zu = h₃ - h₂*",
                calculation=f"q_zu = {self.states[3]['h']:.2f} J/kg - {self.states['2*']['h']:.2f} J/kg",
                result=q_in,
                unit="J/kg"
            )
        else:
            q_in = self.states[3]["h"] - self.states[2]["h"]
            self._add_step(
                title="Spezifische Wärmezufuhr q_zu",
                formula="q_zu = h₃ - h₂",
                calculation=f"q_zu = {self.states[3]['h']:.2f} J/kg - {self.states[2]['h']:.2f} J/kg",
                result=q_in,
                unit="J/kg"
            )
        
        # Spezifische Wärmeabfuhr
        if self.regeneration and "4*" in self.states:
            q_out = self.states["4*"]["h"] - self.states[1]["h"]
            self._add_step(
                title="Spezifische Wärmeabfuhr q_ab",
                formula="q_ab = h₄* - h₁",
                calculation=f"q_ab = {self.states['4*']['h']:.2f} J/kg - {self.states[1]['h']:.2f} J/kg",
                result=q_out,
                unit="J/kg"
            )
        else:
            q_out = self.states[4]["h"] - self.states[1]["h"]
            self._add_step(
                title="Spezifische Wärmeabfuhr q_ab",
                formula="q_ab = h₄ - h₁",
                calculation=f"q_ab = {self.states[4]['h']:.2f} J/kg - {self.states[1]['h']:.2f} J/kg",
                result=q_out,
                unit="J/kg"
            )
        
        # Thermischer Wirkungsgrad
        eta_th = w_kp / q_in
        self._add_step(
            title="Thermischer Wirkungsgrad η_th",
            formula="η_th = w_KP / q_zu",
            calculation=f"η_th = {w_kp:.2f} J/kg / {q_in:.2f} J/kg",
            result=eta_th,
            unit=""
        )
        
        # Thermodynamische Mitteltemperaturen
        # Wärmezufuhr
        if self.regeneration and "2*" in self.states:
            T_m_zu = (self.states[3]["T"] - self.states["2*"]["T"]) / np.log(self.states[3]["T"] / self.states["2*"]["T"])
            self._add_step(
                title="Mittlere Temperatur der Wärmezufuhr",
                formula="T_m_zu = (T₃ - T₂*) / ln(T₃/T₂*)",
                calculation=f"T_m_zu = ({self.states[3]['T']:.2f} - {self.states['2*']['T']:.2f}) / ln({self.states[3]['T']:.2f}/{self.states['2*']['T']:.2f})",
                result=T_m_zu,
                unit="K"
            )
        else:
            T_m_zu = (self.states[3]["T"] - self.states[2]["T"]) / np.log(self.states[3]["T"] / self.states[2]["T"])
            self._add_step(
                title="Mittlere Temperatur der Wärmezufuhr",
                formula="T_m_zu = (T₃ - T₂) / ln(T₃/T₂)",
                calculation=f"T_m_zu = ({self.states[3]['T']:.2f} - {self.states[2]['T']:.2f}) / ln({self.states[3]['T']:.2f}/{self.states[2]['T']:.2f})",
                result=T_m_zu,
                unit="K"
            )
        
        # Wärmeabfuhr
        if self.regeneration and "4*" in self.states:
            T_m_ab = (self.states["4*"]["T"] - self.states[1]["T"]) / np.log(self.states["4*"]["T"] / self.states[1]["T"])
            self._add_step(
                title="Mittlere Temperatur der Wärmeabfuhr",
                formula="T_m_ab = (T₄* - T₁) / ln(T₄*/T₁)",
                calculation=f"T_m_ab = ({self.states['4*']['T']:.2f} - {self.states[1]['T']:.2f}) / ln({self.states['4*']['T']:.2f}/{self.states[1]['T']:.2f})",
                result=T_m_ab,
                unit="K"
            )
        else:
            T_m_ab = (self.states[4]["T"] - self.states[1]["T"]) / np.log(self.states[4]["T"] / self.states[1]["T"])
            self._add_step(
                title="Mittlere Temperatur der Wärmeabfuhr",
                formula="T_m_ab = (T₄ - T₁) / ln(T₄/T₁)",
                calculation=f"T_m_ab = ({self.states[4]['T']:.2f} - {self.states[1]['T']:.2f}) / ln({self.states[4]['T']:.2f}/{self.states[1]['T']:.2f})",
                result=T_m_ab,
                unit="K"
            )
        
        # Wärmerückgewinnung (Regeneration)
        if self.regeneration and "2*" in self.states and "4*" in self.states:
            q_reg = self.states["2*"]["h"] - self.states[2]["h"]
            self._add_step(
                title="Spezifische Wärme im Regenerator q_reg",
                formula="q_reg = h₂* - h₂",
                calculation=f"q_reg = {self.states['2*']['h']:.2f} J/kg - {self.states[2]['h']:.2f} J/kg",
                result=q_reg,
                unit="J/kg"
            )
        else:
            q_reg = 0.0
        
        # Process properties dictionary
        process_properties = {
            "w_comp": w_comp,
            "w_turb": w_turb,
            "w_kp": w_kp,
            "q_in": q_in,
            "q_out": q_out,
            "eta_th": eta_th,
            "T_m_zu": T_m_zu,
            "T_m_ab": T_m_ab
        }
        
        # Eigenschaften bei Zwischenkühlung hinzufügen
        if has_intercooling:
            process_properties["w_comp1"] = w_comp1
            process_properties["w_comp2"] = w_comp2
            process_properties["q_intercool"] = q_intercool
        
        # Eigenschaften bei Regeneration hinzufügen
        if self.regeneration and "2*" in self.states and "4*" in self.states:
            process_properties["q_reg"] = q_reg
        
        # Berechnung der Leistungen, wenn Massestrom gegeben
        if self.mass_flow is not None:
            P_comp = self.mass_flow * w_comp
            P_turb = self.mass_flow * w_turb
            P_kp = self.mass_flow * w_kp
            Q_in = self.mass_flow * q_in
            Q_out = self.mass_flow * q_out
            
            process_properties.update({
                "P_comp": P_comp,
                "P_turb": P_turb,
                "P_kp": P_kp,
                "Q_in": Q_in,
                "Q_out": Q_out
            })
            
            if has_intercooling:
                process_properties["P_comp1"] = self.mass_flow * w_comp1
                process_properties["P_comp2"] = self.mass_flow * w_comp2
                process_properties["Q_intercool"] = self.mass_flow * q_intercool
            
            if self.regeneration and "2*" in self.states and "4*" in self.states:
                process_properties["Q_reg"] = self.mass_flow * q_reg
        
        # Add pressure ratio and temperature ratio
        if 1 in self.states and 2 in self.states:
            pi = self.states[2]["p"] / self.states[1]["p"]
            process_properties["pi"] = pi
        
        if 1 in self.states and 3 in self.states:
            tau = self.states[3]["T"] / self.states[1]["T"]
            process_properties["tau"] = tau
        
        return process_properties