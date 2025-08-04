"""
User interface components for the JOULE process calculator.
Contains widget-based UI elements for interactive calculations.
Extended with intercooling functionality.
"""

import ipywidgets as widgets
from IPython.display import display, HTML
import matplotlib.pyplot as plt
import numpy as np

from models.gas_properties import GAS_PROPERTIES
from models.joule_process import JouleProcessCalculator
from utils.converters import bar_to_pascal
from visualization.results_formatter import print_results_table, material_properties_table
from visualization.plotting import plot_process, custom_sort_key


def create_joule_calculator_ui():
    """
    Creates a user interface for the JOULE process calculator
    
    Returns:
    widgets.VBox
        Widget container with UI elements
    """
    # Gasauswahl
    gas_dropdown = widgets.Dropdown(
        options=[('Luft', 'air'), ('Helium', 'helium'), ('Stickstoff', 'nitrogen'), ('Kohlendioxid', 'carbon_dioxide')],
        value='air',
        description='Gas:',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Cp Modell
    cp_model_dropdown = widgets.Dropdown(
        options=[('Konstant', True), ('Temperaturabhängig', False)],
        value=True,
        description='cp Modell:',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Regeneration
    regeneration_checkbox = widgets.Checkbox(
        value=False,
        description='Regeneration',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Regenerations-Wirkungsgrad
    reg_eff_slider = widgets.FloatSlider(
        value=0.8,
        min=0.0,
        max=1.0,
        step=0.01,
        description='Reg. Wirkungsgrad:',
        disabled=True,
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Pinch-Point für Regeneration
    pinch_point_slider = widgets.FloatSlider(
        value=0.0,
        min=0.0,
        max=100.0,
        step=1.0,
        description='Pinch-Point [K]:',
        disabled=True,
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Verdichter-Wirkungsgrad
    comp_eff_slider = widgets.FloatSlider(
        value=0.85,
        min=0.5,
        max=1.0,
        step=0.01,
        description='Verdichter η:',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Turbinen-Wirkungsgrad
    turb_eff_slider = widgets.FloatSlider(
        value=0.9,
        min=0.5,
        max=1.0,
        step=0.01,
        description='Turbine η:',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # NEUER ABSCHNITT: Zwischenkühlung
    # Checkbox für Zwischenkühlung
    intercooling_checkbox = widgets.Checkbox(
        value=False,
        description='Zwischenkühlung',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Dropdown für Zwischenkühlungstemperatur
    intercooling_temp_dropdown = widgets.Dropdown(
        options=[('Zurück zu T₁', 'T1'), ('Benutzerdefiniert', 'custom')],
        value='T1',
        description='Kühlung auf:',
        disabled=True,
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Eingabefeld für benutzerdefinierte Zwischenkühlungstemperatur
    intercooling_temp_text = widgets.FloatText(
        value=293.15,
        description='T_Kühlung [K]:',
        disabled=True,
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Dropdown für Zwischendruck-Berechnung
    intercooling_pressure_dropdown = widgets.Dropdown(
        options=[('Optimal (Geometrisches Mittel)', 'geo_mean'), 
                 ('Arithmetisches Mittel', 'arith_mean'), 
                 ('Benutzerdefiniertes Verhältnis', 'custom')],
        value='geo_mean',
        description='Zwischendruck:',
        disabled=True,
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Eingabefeld für benutzerdefiniertes Druckverhältnis
    intercooling_pressure_ratio_text = widgets.FloatText(
        value=1.5,
        description='p₂ₐ/p₁:',
        disabled=True,
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Massenstrom-Bereich
    mass_flow_options = widgets.RadioButtons(
        options=['Direkte Eingabe', 'Berechnung aus Leistung', 'Ohne Massestrom'],
        value='Ohne Massestrom',
        description='Massestrom:',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Massenstrom direkte Eingabe
    mass_flow_text = widgets.FloatText(
        value=1.0,
        description='Massestrom [kg/s]:',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px'),
        disabled=True
    )
    
    # Massestrom aus Leistung berechnen
    power_type = widgets.Dropdown(
        options=[('Turbinenleistung', 'turb'), ('Verdichterleistung', 'comp'), ('Nettoleistung', 'net')],
        value='net',
        description='Leistungstyp:',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px'),
        disabled=True
    )
    
    power_value = widgets.FloatText(
        value=100.0,
        description='Leistung [kW]:',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px'),
        disabled=True
    )
    
    # Zustand 1
    p1_text = widgets.FloatText(
        value=1.0,
        description='p₁ [bar]:',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Geändert: Eingabe direkt in Kelvin statt Celsius
    T1_text = widgets.FloatText(
        value=293.15,  # Default jetzt in Kelvin (entspricht 20°C)
        description='T₁ [K]:',  # Beschriftung geändert zu [K]
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Zustand 2
    p2_text = widgets.FloatText(
        value=8.0,
        description='p₂ [bar]:',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Zustand 3
    # Geändert: Eingabe direkt in Kelvin statt Celsius
    T3_text = widgets.FloatText(
        value=1273.15,  # Default jetzt in Kelvin (entspricht 1000°C)
        description='T₃ [K]:',  # Beschriftung geändert zu [K]
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Zustand 4
    p4_text = widgets.FloatText(
        value=1.0,
        description='p₄ [bar]:',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Diagramm-Auswahl
    diagram_dropdown = widgets.Dropdown(
        options=[('T-s-Diagramm', 'Ts'), ('p-v-Diagramm', 'pv'), ('h-s-Diagramm', 'hs')],
        value='Ts',
        description='Diagramm:',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Anzeige von Stoffwerten
    show_material_props_checkbox = widgets.Checkbox(
        value=True,
        description='Stoffwerte anzeigen',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px')
    )
    
    # Ausgabebereich
    output = widgets.Output()
    
    # Additional output area specifically for calculation steps
    calculation_output = widgets.Output()
    
    # Store the current calculator instance
    current_calc = {'instance': None}
    
    # Dropdown to select calculation step categories
    step_category_dropdown = widgets.Dropdown(
        options=[('All Steps', None)],
        value=None,
        description='Step Category:',
        style={'description_width': '120px'},
        layout=widgets.Layout(width='350px'),
        disabled=True
    )
    
    # Button for showing detailed calculation
    show_calculation_button = widgets.Button(
        description='Show Detailed Calculation',
        button_style='info',
        tooltip='Show detailed calculation steps',
        icon='list-ol',
        disabled=True
    )
    
    # Export format selection
    export_format = widgets.RadioButtons(
        options=['HTML', 'PDF', 'Markdown'],
        value='HTML',
        description='Export Format:',
        disabled=True,
        layout=widgets.Layout(width='200px')
    )
    
    # Export button
    export_button = widgets.Button(
        description='Export Calculation',
        button_style='success',
        tooltip='Export detailed calculation steps',
        icon='file-download',
        disabled=True
    )
    
    # Export filename
    export_filename = widgets.Text(
        value='joule_calculation',
        description='Filename:',
        disabled=True,
        style={'description_width': '80px'},
        layout=widgets.Layout(width='250px')
    )
    
    # Funktion zur Aktualisierung der Massenstrom-Felder
    def update_mass_flow_fields(*args):
        option = mass_flow_options.value
        if option == 'Direkte Eingabe':
            mass_flow_text.disabled = False
            power_type.disabled = True
            power_value.disabled = True
        elif option == 'Berechnung aus Leistung':
            mass_flow_text.disabled = True
            power_type.disabled = False
            power_value.disabled = False
        else:  # 'Ohne Massestrom'
            mass_flow_text.disabled = True
            power_type.disabled = True
            power_value.disabled = True
    
    mass_flow_options.observe(update_mass_flow_fields, 'value')
    
    # Funktion zur Aktualisierung der Regenerations-Felder
    def update_reg_fields(*args):
        reg_eff_slider.disabled = not regeneration_checkbox.value
        pinch_point_slider.disabled = not regeneration_checkbox.value
    
    regeneration_checkbox.observe(update_reg_fields, 'value')
    
    # NEUE FUNKTION: Aktualisierung der Zwischenkühlungs-Felder
    def update_intercooling_fields(*args):
        is_enabled = intercooling_checkbox.value
        intercooling_temp_dropdown.disabled = not is_enabled
        intercooling_pressure_dropdown.disabled = not is_enabled
        
        # Benutzerdefinierte Temperatur nur aktivieren, wenn Zwischenkühlung an UND 'Benutzerdefiniert' ausgewählt ist
        intercooling_temp_text.disabled = not is_enabled or intercooling_temp_dropdown.value != 'custom'
        
        # Benutzerdefiniertes Druckverhältnis nur aktivieren, wenn Zwischenkühlung an UND 'Benutzerdefiniert' ausgewählt ist
        intercooling_pressure_ratio_text.disabled = not is_enabled or intercooling_pressure_dropdown.value != 'custom'
    
    intercooling_checkbox.observe(update_intercooling_fields, 'value')
    intercooling_temp_dropdown.observe(update_intercooling_fields, 'value')
    intercooling_pressure_dropdown.observe(update_intercooling_fields, 'value')
    
    # Funktion zur Berechnung des Massestroms aus der Leistung
    def calculate_mass_flow(props, power_type, power_value):
        """
        Berechnet den Massestrom aus der gegebenen Leistung
        
        Parameter:
        props : dict
            Berechnete Prozessgrößen
        power_type : str
            Art der Leistung ('turb', 'comp', 'net')
        power_value : float
            Leistungswert in kW
            
        Returns:
        float
            Berechneter Massestrom in kg/s
        """
        power_value_w = power_value * 1000  # Umrechnung von kW in W
        
        if power_type == 'turb':
            # Turbinenleistung: P_turb = w_turb * m_dot
            # Korrigiert: Minus-Zeichen entfernt, da w_turb bereits das richtige Vorzeichen hat
            return power_value_w / props['w_turb']
        elif power_type == 'comp':
            # Verdichterleistung: P_comp = w_comp * m_dot
            return power_value_w / props['w_comp']
        else:  # 'net'
            # Nettoleistung: P_net = w_kp * m_dot
            return power_value_w / props['w_kp']
    
    # Berechnen-Button
    calculate_button = widgets.Button(
        description='Berechnen',
        button_style='success',
        tooltip='JOULE-Prozess berechnen',
        icon='calculator'
    )
    
    # Functions for showing and exporting calculation steps
    def show_calculation(b):
        with calculation_output:
            calculation_output.clear_output()
            if current_calc['instance'] is not None:
                from visualization.results_formatter import print_calculation_steps
                print_calculation_steps(current_calc['instance'], category=step_category_dropdown.value)
            else:
                print("Bitte zuerst eine Berechnung durchführen.")

    def update_calculation_display(change):
        if current_calc['instance'] is not None:
            show_calculation(None)

    def export_calculation(b):
        with calculation_output:
            calculation_output.clear_output()
            if current_calc['instance'] is not None:
                format_type = export_format.value.lower()
                filename = export_filename.value
                
                if format_type == 'pdf':
                    from visualization.results_formatter import export_calculation_to_pdf
                    try:
                        export_calculation_to_pdf(current_calc['instance'], f"{filename}.pdf", include_plots=True)
                    except ImportError:
                        print("Für den PDF-Export wird fpdf benötigt.")
                        print("Installiere mit: pip install fpdf")
                        print("Alternativ wähle ein anderes Format.")
                else:
                    from visualization.results_formatter import print_calculation_steps
                    print_calculation_steps(
                        current_calc['instance'], 
                        format_type=format_type.lower(), 
                        output_file=f"{filename}.{format_type.lower()}"
                    )
            else:
                print("Bitte zuerst eine Berechnung durchführen.")
    
    # Connect the buttons to the functions
    show_calculation_button.on_click(show_calculation)
    step_category_dropdown.observe(update_calculation_display, names='value')
    export_button.on_click(export_calculation)
    
    # NEUE FUNKTION: Plot des Prozesses mit Zwischenkühlung
    def plot_process_with_intercooling(joule_calc, diagram_type="Ts", save_fig=False, filename=None, show_points=True):
        """
        Zeichnet einen JOULE-Prozess mit Zwischenkühlung
        
        Parameter:
        joule_calc : JouleProcessCalculator
            Instanz des JouleProcessCalculators
        diagram_type : str
            Art des Diagramms ('Ts', 'pv', 'hs')
        save_fig : bool
            Wenn True, wird die Figur gespeichert
        filename : str
            Dateiname für die gespeicherte Figur
        show_points : bool
            Wenn True, werden die Zustandspunkte im Diagramm angezeigt
        """
        # Überprüfen, ob alle grundlegenden Zustände berechnet wurden
        if not all(i in joule_calc.states for i in [1, 2, 3, 4]):
            raise ValueError("Alle grundlegenden Zustände (1, 2, 3, 4) müssen berechnet sein.")
        
        fig, ax = plt.subplots(figsize=(10, 6), dpi=120)
        
        # Zustandspunkte extrahieren mit benutzerdefinierter Sortierfunktion
        points = {}
        for i in sorted(joule_calc.states.keys(), key=custom_sort_key):
            points[i] = joule_calc.states[i]
        
        # Diagramm-Typ
        if diagram_type == "Ts":
            x_key, y_key = "s", "T"
            xlabel, ylabel = "Entropie s [J/(kg·K)]", "Temperatur T [K]"
            title = "T-s-Diagramm des JOULE-Prozesses"
        elif diagram_type == "pv":
            x_key, y_key = "v", "p"
            xlabel, ylabel = "Spezifisches Volumen v [m³/kg]", "Druck p [bar]"
            title = "p-v-Diagramm des JOULE-Prozesses"
        elif diagram_type == "hs":
            x_key, y_key = "h", "s"
            xlabel, ylabel = "Spezifische Enthalpie h [J/kg]", "Entropie s [J/(kg·K)]"
            title = "h-s-Diagramm des JOULE-Prozesses"
        else:
            raise ValueError(f"Unbekannter Diagramm-Typ: {diagram_type}")
        
        # Prüfen, ob Zwischenkühlung aktiv ist
        has_intercooling = "2a" in joule_calc.states and "2b" in joule_calc.states and "2c" in joule_calc.states
        
        if has_intercooling:
            title += " mit Zwischenkühlung"
        
        # Punktkoordinaten vorbereiten
        x_vals = []
        y_vals = []
        labels = []
        for label, point in points.items():
            x_val = point[x_key]
            y_val = point[y_key]
            if y_key == "p":
                from utils.converters import pascal_to_bar
                y_val = pascal_to_bar(y_val)  # Pa zu bar
            x_vals.append(x_val)
            y_vals.append(y_val)
            labels.append(str(label))
        
        # Punkte zeichnen
        if show_points:
            ax.scatter(x_vals, y_vals, s=80, c='blue', zorder=3)
            
            # Beschriftungen hinzufügen
            for i, label in enumerate(labels):
                ax.annotate(label, (x_vals[i], y_vals[i]), fontsize=12, 
                        xytext=(10, 10), textcoords='offset points')
        
        # Linien zwischen den Zuständen zeichnen
        if has_intercooling:
            # Mit Zwischenkühlung
            if joule_calc.regeneration and "2*" in joule_calc.states and "4*" in joule_calc.states:
                # Mit Regeneration und Zwischenkühlung
                # 1 -> 2a (erste Verdichtung)
                ax.plot([points[1][x_key], points["2a"][x_key]], 
                        [points[1][y_key] if y_key != "p" else pascal_to_bar(points[1][y_key]), 
                        points["2a"][y_key] if y_key != "p" else pascal_to_bar(points["2a"][y_key])], 
                        'k-', linewidth=2)
                # 2a -> 2b (Zwischenkühlung)
                ax.plot([points["2a"][x_key], points["2b"][x_key]], 
                        [points["2a"][y_key] if y_key != "p" else pascal_to_bar(points["2a"][y_key]), 
                        points["2b"][y_key] if y_key != "p" else pascal_to_bar(points["2b"][y_key])], 
                        'b-', linewidth=2)
                # 2b -> 2c (zweite Verdichtung)
                ax.plot([points["2b"][x_key], points["2c"][x_key]], 
                        [points["2b"][y_key] if y_key != "p" else pascal_to_bar(points["2b"][y_key]), 
                        points["2c"][y_key] if y_key != "p" else pascal_to_bar(points["2c"][y_key])], 
                        'k-', linewidth=2)
                # 2c -> 2* (Regeneration)
                ax.plot([points["2c"][x_key], points["2*"][x_key]], 
                        [points["2c"][y_key] if y_key != "p" else pascal_to_bar(points["2c"][y_key]), 
                        points["2*"][y_key] if y_key != "p" else pascal_to_bar(points["2*"][y_key])], 
                        'k--', linewidth=2)
                # 2* -> 3 (Erhitzung)
                ax.plot([points["2*"][x_key], points[3][x_key]], 
                        [points["2*"][y_key] if y_key != "p" else pascal_to_bar(points["2*"][y_key]), 
                        points[3][y_key] if y_key != "p" else pascal_to_bar(points[3][y_key])], 
                        'r-', linewidth=2)
                # 3 -> 4 (Expansion)
                ax.plot([points[3][x_key], points[4][x_key]], 
                        [points[3][y_key] if y_key != "p" else pascal_to_bar(points[3][y_key]), 
                        points[4][y_key] if y_key != "p" else pascal_to_bar(points[4][y_key])], 
                        'k-', linewidth=2)
                # 4 -> 4* (Regeneration)
                ax.plot([points[4][x_key], points["4*"][x_key]], 
                        [points[4][y_key] if y_key != "p" else pascal_to_bar(points[4][y_key]), 
                        points["4*"][y_key] if y_key != "p" else pascal_to_bar(points["4*"][y_key])], 
                        'k--', linewidth=2)
                # 4* -> 1 (Kühlung)
                ax.plot([points["4*"][x_key], points[1][x_key]], 
                        [points["4*"][y_key] if y_key != "p" else pascal_to_bar(points["4*"][y_key]), 
                        points[1][y_key] if y_key != "p" else pascal_to_bar(points[1][y_key])], 
                        'b-', linewidth=2)
                # Regeneration: 4 -> 2*
                ax.plot([points[4][x_key], points["2*"][x_key]], 
                        [points[4][y_key] if y_key != "p" else pascal_to_bar(points[4][y_key]), 
                        points["2*"][y_key] if y_key != "p" else pascal_to_bar(points["2*"][y_key])], 
                        'r--', linewidth=1)
            else:
                # Mit Zwischenkühlung aber ohne Regeneration
                # 1 -> 2a -> 2b -> 2c -> 3 -> 4 -> 1
                states_order = [1, "2a", "2b", "2c", 3, 4, 1]
                x_cycle = [points[state][x_key] for state in states_order]
                y_cycle = [points[state][y_key] if y_key != "p" else pascal_to_bar(points[state][y_key]) 
                          for state in states_order]
                ax.plot(x_cycle, y_cycle, 'k-', linewidth=2)
        else:
            # Ohne Zwischenkühlung
            if joule_calc.regeneration and "2*" in joule_calc.states and "4*" in joule_calc.states:
                # Standardmäßige Regeneration ohne Zwischenkühlung
                # Alle relevanten Punkte verbinden
                cycle_points = [1, 2, "2*", 3, 4, "4*", 1]
                x_cycle = [points[state][x_key] for state in cycle_points]
                y_cycle = [points[state][y_key] if y_key != "p" else pascal_to_bar(points[state][y_key]) 
                         for state in cycle_points]
                ax.plot(x_cycle, y_cycle, 'k-', linewidth=2)
                
                # Regeneration: 4 -> 2*
                ax.plot([points[4][x_key], points["2*"][x_key]], 
                        [points[4][y_key] if y_key != "p" else pascal_to_bar(points[4][y_key]), 
                         points["2*"][y_key] if y_key != "p" else pascal_to_bar(points["2*"][y_key])], 
                        'r--', linewidth=1)
            else:
                # Basiszyklus ohne Regeneration oder Zwischenkühlung
                x_cycle = [points[1][x_key], points[2][x_key], points[3][x_key], points[4][x_key], points[1][x_key]]
                y_cycle = [points[1][y_key] if y_key != "p" else pascal_to_bar(points[1][y_key]),
                          points[2][y_key] if y_key != "p" else pascal_to_bar(points[2][y_key]),
                          points[3][y_key] if y_key != "p" else pascal_to_bar(points[3][y_key]),
                          points[4][y_key] if y_key != "p" else pascal_to_bar(points[4][y_key]),
                          points[1][y_key] if y_key != "p" else pascal_to_bar(points[1][y_key])]
                ax.plot(x_cycle, y_cycle, 'k-', linewidth=2)
        
        # Diagramm-Eigenschaften
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_title(title, fontsize=14)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Achsen anpassen
        if diagram_type == "pv":
            ax.set_xscale('log')  # Logarithmische x-Achse für p-v-Diagramm
            ax.set_yscale('log')  # Logarithmische y-Achse für p-v-Diagramm
        
        # Legende
        legend_elements = []
        if has_intercooling:
            legend_elements.append(plt.Line2D([0], [0], color='k', lw=2, label='Verdichtung/Expansion'))
            legend_elements.append(plt.Line2D([0], [0], color='b', lw=2, label='Kühlung'))
            legend_elements.append(plt.Line2D([0], [0], color='r', lw=2, label='Erwärmung'))
        if joule_calc.regeneration:
            legend_elements.append(plt.Line2D([0], [0], color='k', ls='--', lw=2, label='Regeneration'))
            legend_elements.append(plt.Line2D([0], [0], color='r', ls='--', lw=1, label='Wärmeübertragung'))
        
        if legend_elements:
            ax.legend(handles=legend_elements)
        
        plt.tight_layout()
        
        if save_fig and filename:
            plt.savefig(filename, dpi=300, bbox_inches='tight')
        
        return fig, ax
    
    # Berechnung durchführen
    def calculate(b):
        with output:
            output.clear_output()
            try:
                # Instanz der Klasse erstellen
                calc = JouleProcessCalculator(gas=gas_dropdown.value, use_const_cp=cp_model_dropdown.value)
                
                # Store the instance for later access
                current_calc['instance'] = calc
                
                # Ensure all inputs are properly converted to float
                p1_value = float(p1_text.value)
                T1_value = float(T1_text.value)
                p2_value = float(p2_text.value)
                T3_value = float(T3_text.value)
                p4_value = float(p4_text.value)
                compressor_eff = float(comp_eff_slider.value)
                turbine_eff = float(turb_eff_slider.value)
                reg_eff = float(reg_eff_slider.value) if regeneration_checkbox.value else 0.0
                pinch_point = float(pinch_point_slider.value) if regeneration_checkbox.value else 0.0
                
                # Parameter für Zwischenkühlung
                intercooling = intercooling_checkbox.value
                intercooling_temperature = None
                intercooling_pressure_ratio = None
                
                # Wenn Zwischenkühlung aktiviert ist, Parameter extrahieren
                if intercooling:
                    # Temperatur nach Zwischenkühlung
                    if intercooling_temp_dropdown.value == 'custom':
                        intercooling_temperature = float(intercooling_temp_text.value)
                    # Wenn 'T1' ausgewählt, bleibt temperature=None (dann wird in der Berechnung T1 verwendet)
                    
                    # Zwischendruck-Verhältnis
                    if intercooling_pressure_dropdown.value == 'custom':
                        intercooling_pressure_ratio = float(intercooling_pressure_ratio_text.value)
                    elif intercooling_pressure_dropdown.value == 'arith_mean':
                        # Arithmetisches Mittel als Verhältnis
                        # p_intermediate = (p1 + p2) / 2
                        # p_ratio = p_intermediate / p1
                        # Dies wird in der Rechnung durchgeführt
                        intercooling_pressure_ratio = 0.5 * (1 + p2_value / p1_value)
                    # Wenn 'geo_mean' ausgewählt, bleibt pressure_ratio=None (dann wird in der Berechnung optimaler Wert verwendet)
                
                # Vorläufiger Massestrom (wird später ggf. aktualisiert)
                initial_mass_flow = None
                if mass_flow_options.value == 'Direkte Eingabe':
                    initial_mass_flow = float(mass_flow_text.value)
                
                # Parameter setzen
                calc.set_parameters(
                    regeneration=regeneration_checkbox.value,
                    reg_eff=reg_eff,
                    compressor_efficiency=compressor_eff,
                    turbine_efficiency=turbine_eff,
                    mass_flow=initial_mass_flow,
                    intercooling=intercooling,
                    intercooling_temperature=intercooling_temperature,
                    intercooling_pressure_ratio=intercooling_pressure_ratio
                )
                
                # Zustände berechnen
                # Zustand 1 berechnen
                p1 = bar_to_pascal(p1_value)
                T1 = T1_value  # Keine Umrechnung mehr nötig, direkt Kelvin
                calc.calculate_state_1(p1, T1)
                
                # Zustand 2 berechnen (mit oder ohne Zwischenkühlung)
                p2 = bar_to_pascal(p2_value)
                calc.calculate_state_2(p2)
                
                # Zustand 3 berechnen
                p3 = p2  # Isobar
                T3 = T3_value  # Keine Umrechnung mehr nötig, direkt Kelvin
                calc.calculate_state_3(p3, T3)
                
                # Zustand 4 berechnen
                p4 = bar_to_pascal(p4_value)
                calc.calculate_state_4(p4)
                
                # Regeneration berechnen (wenn aktiviert)
                if regeneration_checkbox.value:
                    try:
                        calc.calculate_regeneration(pinch_point=pinch_point)
                    except Exception as e:
                        print(f"Fehler bei der Berechnung der Regeneration: {e}")
                        import traceback
                        traceback.print_exc()
                        print("Berechnung wird ohne Regeneration fortgesetzt.")
                
                # Prozessgrößen berechnen
                props = calc.calculate_process_properties()
                
                # Massestrom aktualisieren, falls er aus der Leistung berechnet wird
                mass_flow = initial_mass_flow
                if mass_flow_options.value == 'Berechnung aus Leistung':
                    mass_flow = calculate_mass_flow(props, power_type.value, power_value.value)
                    display(HTML(f"<h3>Berechneter Massestrom: {mass_flow:.4f} kg/s</h3>"))
                    
                    # Parameter mit dem berechneten Massestrom aktualisieren
                    calc.mass_flow = mass_flow
                
                # Optimales Druckverhältnis berechnen
                pi_opt, T2_opt = calc.calculate_optimal_pressure_ratio()
                
                # Übersichtliche Ausgabe
                display(HTML(f"<h2>JOULE-Prozess Rechner</h2>"))
                if intercooling:
                    display(HTML(f"<h3>Prozess mit Zwischenkühlung</h3>"))
                display(HTML(f"<h3>Optimales Druckverhältnis: π_opt = {pi_opt:.4f}</h3>"))
                
                # Zustandsgrößen-Tabelle
                print_results_table(calc)
                
                # Stoffwerte anzeigen
                if show_material_props_checkbox.value:
                    material_properties_table(calc)
                
                # Diagramm zeichnen (mit angepasster Funktion für Zwischenkühlung)
                if intercooling:
                    fig, ax = plot_process_with_intercooling(calc, diagram_type=diagram_dropdown.value)
                else:
                    fig, ax = plot_process(calc, diagram_type=diagram_dropdown.value)
                plt.show()
                
                # Enable calculation step controls
                step_category_dropdown.disabled = False
                show_calculation_button.disabled = False
                export_format.disabled = False
                export_button.disabled = False
                export_filename.disabled = False
                
                # Update the step categories dropdown
                step_categories = list(calc.step_categories.keys())
                step_category_dropdown.options = [('All Steps', None)] + [(cat, cat) for cat in step_categories]
                
            except Exception as e:
                print(f"Fehler bei der Berechnung: {e}")
                import traceback
                traceback.print_exc()
    
    calculate_button.on_click(calculate)
    
    # Layout erstellen
    gas_params = widgets.VBox([
        widgets.HTML("<h3>Arbeitsfluid und Modell</h3>"),
        gas_dropdown,
        cp_model_dropdown,
        show_material_props_checkbox
    ])
    
    efficiency_params = widgets.VBox([
        widgets.HTML("<h3>Wirkungsgrade</h3>"),
        regeneration_checkbox,
        reg_eff_slider,
        pinch_point_slider,
        comp_eff_slider,
        turb_eff_slider
    ])
    
    # NEUER ABSCHNITT: Zwischenkühlungs-Parameter
    intercooling_params = widgets.VBox([
        widgets.HTML("<h3>Zwischenkühlung</h3>"),
        intercooling_checkbox,
        intercooling_temp_dropdown,
        intercooling_temp_text,
        intercooling_pressure_dropdown,
        intercooling_pressure_ratio_text
    ])
    
    mass_flow_params = widgets.VBox([
        widgets.HTML("<h3>Massestrom</h3>"),
        mass_flow_options,
        mass_flow_text,
        power_type,
        power_value
    ])
    
    state_params = widgets.VBox([
        widgets.HTML("<h3>Zustandsgrößen</h3>"),
        p1_text, T1_text,
        p2_text,
        T3_text,
        p4_text,
        diagram_dropdown
    ])
    
    # Angepasstes Layout mit Zwischenkühlung
    params_box_row1 = widgets.HBox([gas_params, efficiency_params, intercooling_params])
    params_box_row2 = widgets.HBox([mass_flow_params, state_params])
    params_box = widgets.VBox([params_box_row1, params_box_row2])
    
    calculate_box = widgets.HBox([calculate_button])
    
    # Create the calculation controls
    calculation_controls = widgets.HBox([show_calculation_button, step_category_dropdown])
    export_controls = widgets.HBox([export_format, export_filename, export_button])
    
    ui = widgets.VBox([
        params_box,
        calculate_box,
        output,
        widgets.HTML("<h3>Detailed Calculation</h3>"),
        calculation_controls,
        export_controls,
        calculation_output
    ])
    
    return ui


def run_joule_calculator():
    """
    Startet den JOULE-Prozess Rechner
    """
    ui = create_joule_calculator_ui()
    display(ui)