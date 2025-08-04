"""
Formatting functions for displaying JOULE process calculation results.
Produces tables and structured output of calculation steps.
"""

import pandas as pd
from IPython.display import display, HTML, Markdown
from utils.converters import kelvin_to_celsius, pascal_to_bar
from models.gas_properties import GAS_PROPERTIES, get_material_properties


def print_results_table(joule_calc):
    """
    Gibt eine übersichtliche Tabelle mit den Zustandsgrößen aus
    
    Parameter:
    joule_calc : JouleProcessCalculator
        Instanz des JouleProcessCalculator
    """
    states_df = pd.DataFrame()
    
    # Benutzerdefinierte Sortierfunktion für gemischte Schlüssel
    def custom_sort_key(key):
        if isinstance(key, int):
            return key, ""  # Zahlen zuerst, kein Suffix
        else:
            # String-Schlüssel wie "2*" aufteilen
            try:
                num = int(key.rstrip("*s"))
                suffix = key[len(str(num)):]
                return num, suffix
            except ValueError:
                return float('inf'), key  # Fallback
    
    # Sortierte Schlüssel mit benutzerdefinierter Funktion
    sorted_keys = sorted(joule_calc.states.keys(), key=custom_sort_key)
    
    for i in sorted_keys:
        state = joule_calc.states[i]
        state_series = pd.Series({
            'p [bar]': pascal_to_bar(state['p']),
            'T [K]': state['T'],
            'T [°C]': kelvin_to_celsius(state['T']),
            'v [m³/kg]': state['v'],
            'h [J/kg]': state['h'],
            's [J/(kg·K)]': state['s']
        }, name=f"Zustand {i}")
        states_df = pd.concat([states_df, state_series.to_frame().T])
    
    display(HTML("<h3>Zustandsgrößen</h3>"))
    display(states_df)
    
    # Prozessgrößen
    try:
        props = joule_calc.calculate_process_properties()
        props_df = pd.DataFrame([{
            'η_th [-]': props['eta_th'] if 'eta_th' in props else None,
            'w_KP [J/kg]': props['w_kp'],
            'q_zu [J/kg]': props['q_in'],
            'q_ab [J/kg]': props['q_out'] if 'q_out' in props else None,
            'π [-]': props['pi'] if 'pi' in props else None,
            'τ [-]': props['tau'] if 'tau' in props else None
        }], index=['Wert'])
        
        display(HTML("<h3>Prozessgrößen</h3>"))
        display(props_df.round(4))
        
        # Leistungen, wenn Massestrom gesetzt
        if joule_calc.mass_flow is not None and all(k in props for k in ['P_comp', 'P_turb', 'P_kp', 'Q_in', 'Q_out']):
            power_df = pd.DataFrame([{
                'P_comp [kW]': props['P_comp']/1000,
                'P_turb [kW]': props['P_turb']/1000,
                'P_KP [kW]': props['P_kp']/1000,
                'Q_zu [kW]': props['Q_in']/1000,
                'Q_ab [kW]': props['Q_out']/1000,
                'Q_reg [kW]': props['Q_reg']/1000 if joule_calc.regeneration and 'Q_reg' in props else 0
            }], index=['Wert'])
            
            display(HTML("<h3>Leistungen</h3>"))
            display(power_df.round(2))
    except Exception as e:
        print(f"Fehler bei der Berechnung der Prozessgrößen: {e}")


def material_properties_table(joule_calc, temperatures=None):
    """
    Gibt eine Tabelle mit den Stoffwerten des gewählten Gases bei verschiedenen Temperaturen aus
    
    Parameter:
    joule_calc : JouleProcessCalculator
        Instanz des JouleProcessCalculator
    temperatures : list
        Liste von Temperaturen in K, bei denen die Stoffwerte berechnet werden sollen
    """
    if temperatures is None:
        # Wenn keine Temperaturen angegeben, benutze die Temperaturen aus den berechneten Zuständen
        temperatures = []
        for state in joule_calc.states.values():
            temperatures.append(state["T"])
        temperatures = sorted(list(set(temperatures)))  # Duplikate entfernen und sortieren
    
    props_df = pd.DataFrame()
    
    for T in temperatures:
        props = get_material_properties(joule_calc.gas, T, joule_calc.use_const_cp)
        props_series = pd.Series({
            'T [K]': T,
            'T [°C]': kelvin_to_celsius(T),
            'cp [J/(kg·K)]': props["cp"],
            'cv [J/(kg·K)]': props["cv"],
            'κ [-]': props["kappa"],
            'R [J/(kg·K)]': props["R"]
        }, name=f"{T:.2f} K")
        props_df = pd.concat([props_df, props_series.to_frame().T])
    
    # Formatieren der Tabelle
    props_df = props_df.round({
        'T [K]': 2,
        'T [°C]': 2,
        'cp [J/(kg·K)]': 2,
        'cv [J/(kg·K)]': 2,
        'κ [-]': 4,
        'R [J/(kg·K)]': 2
    })
    
    display(HTML(f"<h3>Stoffwerte für {GAS_PROPERTIES[joule_calc.gas]['name']}</h3>"))
    display(props_df)


# Diese Änderung sollte in der results_formatter.py-Datei vorgenommen werden
# Ersetze die vorhandene print_calculation_steps-Funktion oder ändere sie wie folgt:

def print_calculation_steps(joule_calc, category=None, format_type="html", output_file=None):
    """
    Gibt die detaillierten Berechnungsschritte aus in verschiedenen Formaten
    
    Parameter:
    joule_calc : JouleProcessCalculator
        Instanz des JouleProcessCalculator
    category : str
        Optional: Nur Schritte einer bestimmten Kategorie anzeigen
    format_type : str
        Format für die Ausgabe ('html', 'markdown', 'text')
    output_file : str
        Optional: Pfad zur Ausgabedatei
    """
    if format_type not in ["html", "markdown", "text"]:
        raise ValueError("format_type must be one of 'html', 'markdown', 'text'")
    
    if category:
        if category in joule_calc.step_categories:
            steps = joule_calc.step_categories[category]
            title = f"Berechnungsschritte: {category}"
            
            if format_type == "html":
                _print_steps_html(title, steps, output_file)
            elif format_type == "markdown":
                _print_steps_markdown(title, steps, output_file)
            else:  # text
                _print_steps_text(title, steps, output_file)
        else:
            print(f"Kategorie '{category}' nicht gefunden.")
    else:
        # Definiere eine logische Reihenfolge der Kategorien für die Ausgabe
        # Diese Reihenfolge entspricht dem typischen Vorgehen in einer Klausur
        category_order = [
            "Allgemein",          # Allgemeine Parameter
            "Zustand 1",          # Zustandsgrößen in Reihenfolge
            "Zustand 2", 
            "Zustand 3", 
            "Zustand 4",
            "Regeneration",       # Falls vorhanden
        ]
        
        # Ergänze fehlende Kategorien am Ende
        for cat in joule_calc.step_categories.keys():
            if cat not in category_order:
                category_order.append(cat)
        
        # Alle Schritte nach Kategorien sortiert anzeigen
        all_output = []
        
        # Header für den Anfang
        if format_type == "html":
            all_output.append("<h1>JOULE-Prozess Berechnungsschritte</h1>")
        elif format_type == "markdown":
            all_output.append("# JOULE-Prozess Berechnungsschritte\n")
        else:  # text
            all_output.append("JOULE-PROZESS BERECHNUNGSSCHRITTE\n")
            all_output.append("=================================\n")
        
        # Zustandsgrößen übersichtlich zusammenfassen
        states_summary = create_states_summary(joule_calc, format_type)
        all_output.append(states_summary)
        
        # Prozessgrößen übersichtlich zusammenfassen
        process_summary = create_process_summary(joule_calc, format_type)
        all_output.append(process_summary)
        
        # Detaillierte Berechnungsschritte in geordneter Reihenfolge
        for category in category_order:
            if category in joule_calc.step_categories:
                steps = joule_calc.step_categories[category]
                title = f"Berechnungsschritte: {category}"
                
                if format_type == "html":
                    html_output = _generate_steps_html(title, steps)
                    all_output.append(html_output)
                elif format_type == "markdown":
                    md_output = _generate_steps_markdown(title, steps)
                    all_output.append(md_output)
                else:  # text
                    text_output = _generate_steps_text(title, steps)
                    all_output.append(text_output)
        
        # Combine all outputs
        if format_type == "html":
            combined_output = "<div style='max-width: 800px; margin: 0 auto;'>"
            combined_output += "".join(all_output)
            combined_output += "</div>"
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"<!DOCTYPE html><html><head><title>JOULE-Prozess</title>"
                           f"<style>{_get_html_css()}</style></head><body>{combined_output}</body></html>")
            else:
                display(HTML(combined_output))
        
        elif format_type == "markdown":
            combined_output = "\n\n".join(all_output)
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(combined_output)
            else:
                display(Markdown(combined_output))
        
        else:  # text
            combined_output = "\n\n".join(all_output)
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(combined_output)
            else:
                print(combined_output)


def create_states_summary(joule_calc, format_type="html"):
    """
    Erstellt eine übersichtliche Zusammenfassung der Zustandsgrößen
    
    Parameter:
    joule_calc : JouleProcessCalculator
        Instanz des JouleProcessCalculator
    format_type : str
        Format für die Ausgabe ('html', 'markdown', 'text')
        
    Returns:
    str:
        Formatierte Zusammenfassung der Zustandsgrößen
    """
    # Hilfsfunktion für benutzerdefinierte Sortierung
    def custom_sort_key(key):
        if isinstance(key, int):
            return key, ""
        else:
            try:
                num = int(key.rstrip("*s"))
                suffix = key[len(str(num)):]
                return num, suffix
            except (ValueError, AttributeError):
                return float('inf'), key
    
    # Sortierte Schlüssel
    sorted_keys = sorted(joule_calc.states.keys(), key=custom_sort_key)
    
    if format_type == "html":
        output = "<h2>Zustandsgrößen Übersicht</h2>"
        output += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        output += "<tr><th>Zustand</th><th>p [bar]</th><th>T [K]</th><th>T [°C]</th><th>v [m³/kg]</th><th>h [J/kg]</th><th>s [J/(kg·K)]</th></tr>"
        
        for i in sorted_keys:
            state = joule_calc.states[i]
            output += f"<tr><td>{i}</td>"
            output += f"<td>{state['p']/1e5:.4f}</td>"
            output += f"<td>{state['T']:.2f}</td>"
            output += f"<td>{state['T']-273.15:.2f}</td>"
            output += f"<td>{state['v']:.6f}</td>"
            output += f"<td>{state['h']:.2f}</td>"
            output += f"<td>{state['s']:.4f}</td></tr>"
        
        output += "</table>"
        
    elif format_type == "markdown":
        output = "## Zustandsgrößen Übersicht\n\n"
        output += "| Zustand | p [bar] | T [K] | T [°C] | v [m³/kg] | h [J/kg] | s [J/(kg·K)] |\n"
        output += "|---------|---------|-------|--------|-----------|----------|--------------|\n"
        
        for i in sorted_keys:
            state = joule_calc.states[i]
            output += f"| {i} | {state['p']/1e5:.4f} | {state['T']:.2f} | {state['T']-273.15:.2f} | "
            output += f"{state['v']:.6f} | {state['h']:.2f} | {state['s']:.4f} |\n"
        
    else:  # text
        output = "Zustandsgrößen Übersicht\n"
        output += "======================\n\n"
        output += f"{'Zustand':<8} {'p [bar]':<10} {'T [K]':<10} {'T [°C]':<10} {'v [m³/kg]':<12} {'h [J/kg]':<12} {'s [J/(kg·K)]':<15}\n"
        output += "-" * 80 + "\n"
        
        for i in sorted_keys:
            state = joule_calc.states[i]
            output += f"{i:<8} {state['p']/1e5:<10.4f} {state['T']:<10.2f} {state['T']-273.15:<10.2f} "
            output += f"{state['v']:<12.6f} {state['h']:<12.2f} {state['s']:<15.4f}\n"
    
    return output


def create_process_summary(joule_calc, format_type="html"):
    """
    Erstellt eine übersichtliche Zusammenfassung der Prozessgrößen
    
    Parameter:
    joule_calc : JouleProcessCalculator
        Instanz des JouleProcessCalculator
    format_type : str
        Format für die Ausgabe ('html', 'markdown', 'text')
        
    Returns:
    str:
        Formatierte Zusammenfassung der Prozessgrößen
    """
    try:
        props = joule_calc.calculate_process_properties()
        
        if format_type == "html":
            output = "<h2>Prozessgrößen Übersicht</h2>"
            output += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
            output += "<tr><th>Größe</th><th>Wert</th><th>Einheit</th></tr>"
            
            # Wichtige Prozessgrößen für Klausuren
            output += f"<tr><td>Druckverhältnis π</td><td>{props.get('pi', '-'):.4f}</td><td>-</td></tr>"
            output += f"<tr><td>Temperaturverhältnis τ</td><td>{props.get('tau', '-'):.4f}</td><td>-</td></tr>"
            output += f"<tr><td>Verdichterarbeit w_c</td><td>{props.get('w_comp', '-'):.2f}</td><td>J/kg</td></tr>"
            output += f"<tr><td>Turbinenarbeit w_t</td><td>{props.get('w_turb', '-'):.2f}</td><td>J/kg</td></tr>"
            output += f"<tr><td>Kreisprozessarbeit w_KP</td><td>{props.get('w_kp', '-'):.2f}</td><td>J/kg</td></tr>"
            output += f"<tr><td>Wärmezufuhr q_zu</td><td>{props.get('q_in', '-'):.2f}</td><td>J/kg</td></tr>"
            output += f"<tr><td>Wärmeabfuhr q_ab</td><td>{props.get('q_out', '-'):.2f}</td><td>J/kg</td></tr>"
            output += f"<tr><td>Thermischer Wirkungsgrad η_th</td><td>{props.get('eta_th', '-'):.4f}</td><td>-</td></tr>"
            
            # Leistungen anzeigen, wenn Massestrom gesetzt
            if joule_calc.mass_flow is not None and all(k in props for k in ['P_comp', 'P_turb', 'P_kp']):
                output += f"<tr><td colspan='3'><b>Leistungen (Massestrom: {joule_calc.mass_flow:.4f} kg/s)</b></td></tr>"
                output += f"<tr><td>Verdichterleistung P_c</td><td>{props.get('P_comp', '-')/1000:.2f}</td><td>kW</td></tr>"
                output += f"<tr><td>Turbinenleistung P_t</td><td>{props.get('P_turb', '-')/1000:.2f}</td><td>kW</td></tr>"
                output += f"<tr><td>Nettoleistung P_KP</td><td>{props.get('P_kp', '-')/1000:.2f}</td><td>kW</td></tr>"
                output += f"<tr><td>Wärmeleistung zu Q_zu</td><td>{props.get('Q_in', '-')/1000:.2f}</td><td>kW</td></tr>"
                output += f"<tr><td>Wärmeleistung ab Q_ab</td><td>{props.get('Q_out', '-')/1000:.2f}</td><td>kW</td></tr>"
            
            output += "</table>"
            
        elif format_type == "markdown":
            output = "## Prozessgrößen Übersicht\n\n"
            output += "| Größe | Wert | Einheit |\n"
            output += "|-------|------|--------|\n"
            
            # Wichtige Prozessgrößen für Klausuren
            output += f"| Druckverhältnis π | {props.get('pi', '-'):.4f} | - |\n"
            output += f"| Temperaturverhältnis τ | {props.get('tau', '-'):.4f} | - |\n"
            output += f"| Verdichterarbeit w_c | {props.get('w_comp', '-'):.2f} | J/kg |\n"
            output += f"| Turbinenarbeit w_t | {props.get('w_turb', '-'):.2f} | J/kg |\n"
            output += f"| Kreisprozessarbeit w_KP | {props.get('w_kp', '-'):.2f} | J/kg |\n"
            output += f"| Wärmezufuhr q_zu | {props.get('q_in', '-'):.2f} | J/kg |\n"
            output += f"| Wärmeabfuhr q_ab | {props.get('q_out', '-'):.2f} | J/kg |\n"
            output += f"| Thermischer Wirkungsgrad η_th | {props.get('eta_th', '-'):.4f} | - |\n"
            
            # Leistungen anzeigen, wenn Massestrom gesetzt
            if joule_calc.mass_flow is not None and all(k in props for k in ['P_comp', 'P_turb', 'P_kp']):
                output += f"\n**Leistungen (Massestrom: {joule_calc.mass_flow:.4f} kg/s)**\n\n"
                output += f"| Verdichterleistung P_c | {props.get('P_comp', '-')/1000:.2f} | kW |\n"
                output += f"| Turbinenleistung P_t | {props.get('P_turb', '-')/1000:.2f} | kW |\n"
                output += f"| Nettoleistung P_KP | {props.get('P_kp', '-')/1000:.2f} | kW |\n"
                output += f"| Wärmeleistung zu Q_zu | {props.get('Q_in', '-')/1000:.2f} | kW |\n"
                output += f"| Wärmeleistung ab Q_ab | {props.get('Q_out', '-')/1000:.2f} | kW |\n"
            
        else:  # text
            output = "Prozessgrößen Übersicht\n"
            output += "======================\n\n"
            output += f"{'Größe':<30} {'Wert':<10} {'Einheit':<10}\n"
            output += "-" * 50 + "\n"
            
            # Wichtige Prozessgrößen für Klausuren
            output += f"{'Druckverhältnis π':<30} {props.get('pi', '-'):<10.4f} {'-':<10}\n"
            output += f"{'Temperaturverhältnis τ':<30} {props.get('tau', '-'):<10.4f} {'-':<10}\n"
            output += f"{'Verdichterarbeit w_c':<30} {props.get('w_comp', '-'):<10.2f} {'J/kg':<10}\n"
            output += f"{'Turbinenarbeit w_t':<30} {props.get('w_turb', '-'):<10.2f} {'J/kg':<10}\n"
            output += f"{'Kreisprozessarbeit w_KP':<30} {props.get('w_kp', '-'):<10.2f} {'J/kg':<10}\n"
            output += f"{'Wärmezufuhr q_zu':<30} {props.get('q_in', '-'):<10.2f} {'J/kg':<10}\n"
            output += f"{'Wärmeabfuhr q_ab':<30} {props.get('q_out', '-'):<10.2f} {'J/kg':<10}\n"
            output += f"{'Thermischer Wirkungsgrad η_th':<30} {props.get('eta_th', '-'):<10.4f} {'-':<10}\n"
            
            # Leistungen anzeigen, wenn Massestrom gesetzt
            if joule_calc.mass_flow is not None and all(k in props for k in ['P_comp', 'P_turb', 'P_kp']):
                output += f"\nLeistungen (Massestrom: {joule_calc.mass_flow:.4f} kg/s)\n"
                output += "-" * 50 + "\n"
                output += f"{'Verdichterleistung P_c':<30} {props.get('P_comp', '-')/1000:<10.2f} {'kW':<10}\n"
                output += f"{'Turbinenleistung P_t':<30} {props.get('P_turb', '-')/1000:<10.2f} {'kW':<10}\n"
                output += f"{'Nettoleistung P_KP':<30} {props.get('P_kp', '-')/1000:<10.2f} {'kW':<10}\n"
                output += f"{'Wärmeleistung zu Q_zu':<30} {props.get('Q_in', '-')/1000:<10.2f} {'kW':<10}\n"
                output += f"{'Wärmeleistung ab Q_ab':<30} {props.get('Q_out', '-')/1000:<10.2f} {'kW':<10}\n"
        
        return output
    
    except Exception as e:
        return f"Fehler bei der Berechnung der Prozessgrößen: {e}"


def _get_html_css():
    """Return CSS styles for HTML output"""
    return """
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    h2 { color: #3498db; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 30px; }
    h3 { color: #2980b9; margin-top: 20px; }
    .step { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9; }
    .step:hover { box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    .formula { font-style: italic; color: #2c3e50; background-color: #f5f5f5; padding: 5px; border-left: 3px solid #3498db; }
    .calculation { margin: 10px 0; padding: 5px; background-color: #f8f9fa; border-left: 3px solid #27ae60; }
    .result { font-weight: bold; color: #e74c3c; }
    .category { margin-top: 40px; }
    """


def _print_steps_html(title, steps, output_file=None):
    """Print steps in HTML format"""
    html_output = _generate_steps_html(title, steps)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"<!DOCTYPE html><html><head><title>{title}</title>"
                   f"<style>{_get_html_css()}</style></head><body>{html_output}</body></html>")
    else:
        display(HTML(html_output))


def _generate_steps_html(title, steps):
    """Generate HTML output for steps"""
    html_output = f"<div class='category'><h2>{title}</h2>"
    
    for i, step in enumerate(steps):
        html_output += f"<div class='step' id='step-{i+1}'>"
        html_output += f"<h3>{step['title']}</h3>"
        
        if step['formula']:
            html_output += f"<p class='formula'><strong>Formel:</strong> {step['formula']}</p>"
        
        if step['calculation']:
            html_output += f"<p class='calculation'><strong>Berechnung:</strong> {step['calculation']}</p>"
        
        if step['result'] is not None:
            result_str = f"{step['result']:.6g}" if isinstance(step['result'], float) else str(step['result'])
            unit_str = f" {step['unit']}" if step['unit'] else ""
            html_output += f"<p class='result'><strong>Ergebnis:</strong> {result_str}{unit_str}</p>"
        
        html_output += "</div>"
    
    html_output += "</div>"
    return html_output


def _print_steps_markdown(title, steps, output_file=None):
    """Print steps in Markdown format"""
    md_output = _generate_steps_markdown(title, steps)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_output)
    else:
        display(Markdown(md_output))


def _generate_steps_markdown(title, steps):
    """Generate Markdown output for steps"""
    md_output = f"## {title}\n\n"
    
    for i, step in enumerate(steps):
        md_output += f"### {step['title']}\n\n"
        
        if step['formula']:
            md_output += f"**Formel:** {step['formula']}\n\n"
        
        if step['calculation']:
            md_output += f"**Berechnung:** {step['calculation']}\n\n"
        
        if step['result'] is not None:
            result_str = f"{step['result']:.6g}" if isinstance(step['result'], float) else str(step['result'])
            unit_str = f" {step['unit']}" if step['unit'] else ""
            md_output += f"**Ergebnis:** {result_str}{unit_str}\n\n"
        
        md_output += "---\n\n"
    
    return md_output


def _print_steps_text(title, steps, output_file=None):
    """Print steps in plain text format"""
    text_output = _generate_steps_text(title, steps)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text_output)
    else:
        print(text_output)


def _generate_steps_text(title, steps):
    """Generate plain text output for steps"""
    text_output = f"{title}\n"
    text_output += "=" * len(title) + "\n\n"
    
    for i, step in enumerate(steps):
        text_output += f"{step['title']}\n"
        text_output += "-" * len(step['title']) + "\n"
        
        if step['formula']:
            text_output += f"Formel: {step['formula']}\n"
        
        if step['calculation']:
            text_output += f"Berechnung: {step['calculation']}\n"
        
        if step['result'] is not None:
            result_str = f"{step['result']:.6g}" if isinstance(step['result'], float) else str(step['result'])
            unit_str = f" {step['unit']}" if step['unit'] else ""
            text_output += f"Ergebnis: {result_str}{unit_str}\n"
        
        text_output += "\n"
    
    return text_output


def print_calculation_summary(joule_calc, output_file=None):
    """
    Gibt eine kompakte Zusammenfassung aller Berechnungsschritte aus
    
    Parameter:
    joule_calc : JouleProcessCalculator
        Instanz des JouleProcessCalculator
    output_file : str
        Optional: Pfad zur Ausgabedatei
    """
    # Create a summary dataframe
    summary_data = []
    
    for i, step in enumerate(joule_calc.steps):
        category = ""
        for cat, steps in joule_calc.step_categories.items():
            if step in steps:
                category = cat
                break
        
        result_str = f"{step['result']:.6g}" if isinstance(step['result'], float) and step['result'] is not None else ""
        unit_str = step['unit'] if step['unit'] else ""
        
        summary_data.append({
            "Nr.": i+1,
            "Kategorie": category,
            "Schritt": step['title'],
            "Ergebnis": result_str,
            "Einheit": unit_str
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    if output_file:
        # Export to Excel or CSV
        if output_file.endswith(".xlsx"):
            summary_df.to_excel(output_file, index=False)
        else:
            summary_df.to_csv(output_file, index=False)
        print(f"Zusammenfassung gespeichert in {output_file}")
    else:
        # Display in notebook
        display(HTML("<h2>Berechnungszusammenfassung</h2>"))
        display(summary_df)


def export_calculation_to_pdf(joule_calc, output_file, include_plots=True):
    """
    Exportiert die Berechnung als PDF-Datei mit robuster Unicode-Behandlung
    
    Parameter:
    joule_calc : JouleProcessCalculator
        Instanz des JouleProcessCalculator
    output_file : str
        Pfad zur Ausgabedatei
    include_plots : bool
        Wenn True, werden Diagramme im PDF inkludiert
    """
    try:
        from fpdf import FPDF
        import matplotlib.pyplot as plt
        from visualization.plotting import plot_process
        import tempfile
        import os
        import sys
    except ImportError:
        print("Für den PDF-Export wird fpdf benötigt. Installieren mit: pip install fpdf")
        return
    
    class CustomPDF(FPDF):
        """Custom PDF class with Unicode-safe methods"""
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'JOULE-Prozess Berechnungsdokumentation', 0, 1, 'C')
            self.ln(10)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Seite {self.page_no()}', 0, 0, 'C')
        
        def add_cell(self, text, new_line=True, style=''):
            """Add a cell with Unicode-safe text conversion"""
            safe_text = self._make_text_safe(text)
            self.set_font('Arial', style, 10)
            self.cell(0, 6, safe_text, 0, 1 if new_line else 0, 'L')
        
        def add_multi_cell(self, text, height=6, style=''):
            """Add a multi-line cell with Unicode-safe text conversion"""
            safe_text = self._make_text_safe(text)
            self.set_font('Arial', style, 10)
            self.multi_cell(0, height, safe_text)
        
        def add_heading(self, text, level=1):
            """Add a heading with Unicode-safe text conversion"""
            safe_text = self._make_text_safe(text)
            if level == 1:
                self.set_font('Arial', 'B', 16)
                self.cell(0, 10, safe_text, 0, 1, 'L')
            elif level == 2:
                self.set_font('Arial', 'B', 14)
                self.cell(0, 10, safe_text, 0, 1, 'L')
            else:
                self.set_font('Arial', 'B', 12)
                self.cell(0, 8, safe_text, 0, 1, 'L')
        
        def _make_text_safe(self, text):
            """Convert any Unicode text to Latin-1 safe equivalent"""
            if not isinstance(text, str):
                return str(text)
                
            # Ersetze Zeichen durch sichere Alternativen
            replacements = {
                # Griechische Buchstaben (kleine)
                'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon',
                'ζ': 'zeta', 'η': 'eta', 'θ': 'theta', 'ι': 'iota', 'κ': 'kappa',
                'λ': 'lambda', 'μ': 'mu', 'ν': 'nu', 'ξ': 'xi', 'ο': 'omicron',
                'π': 'pi', 'ρ': 'rho', 'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon',
                'φ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega',
                
                # Griechische Buchstaben (große)
                'Α': 'Alpha', 'Β': 'Beta', 'Γ': 'Gamma', 'Δ': 'Delta', 'Ε': 'Epsilon',
                'Ζ': 'Zeta', 'Η': 'Eta', 'Θ': 'Theta', 'Ι': 'Iota', 'Κ': 'Kappa',
                'Λ': 'Lambda', 'Μ': 'Mu', 'Ν': 'Nu', 'Ξ': 'Xi', 'Ο': 'Omicron',
                'Π': 'Pi', 'Ρ': 'Rho', 'Σ': 'Sigma', 'Τ': 'Tau', 'Υ': 'Upsilon',
                'Φ': 'Phi', 'Χ': 'Chi', 'Ψ': 'Psi', 'Ω': 'Omega',
                
                # Tiefgestellte Zahlen
                '₀': '_0', '₁': '_1', '₂': '_2', '₃': '_3', '₄': '_4',
                '₅': '_5', '₆': '_6', '₇': '_7', '₈': '_8', '₉': '_9',
                
                # Hochgestellte Zahlen
                '⁰': '^0', '¹': '^1', '²': '^2', '³': '^3', '⁴': '^4',
                '⁵': '^5', '⁶': '^6', '⁷': '^7', '⁸': '^8', '⁹': '^9',
                
                # Thermodynamische Symbole
                '°': 'deg', '·': '*', '→': '->', '←': '<-', '−': '-',
                '×': 'x', '≈': '~=', '≠': '!=', '≤': '<=', '≥': '>=',
                '±': '+/-', '∂': 'd', '∫': 'int', '√': 'sqrt', '∞': 'inf',
                
                # Deutsche Umlaute
                'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss'
            }
            
            for char, replacement in replacements.items():
                text = text.replace(char, replacement)
                
            # Entferne alle verbleibenden nicht-Latin1-Zeichen
            text = ''.join(c for c in text if ord(c) < 256)
            return text
    
    # PDF-Dokument erstellen
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Titel
    pdf.add_heading('Berechnungsdokumentation')
    pdf.ln(5)
    
    # Gas und Modell-Informationen
    pdf.add_heading('Arbeitsfluid und Modell', 3)
    pdf.add_cell(f"Gas: {GAS_PROPERTIES[joule_calc.gas]['name']}")
    pdf.add_cell(f"cp Modell: {'Konstant' if joule_calc.use_const_cp else 'Temperaturabhängig'}")
    pdf.add_cell(f"Regeneration: {'Ja' if joule_calc.regeneration else 'Nein'}")
    if joule_calc.regeneration:
        pdf.add_cell(f"Regenerationswirkungsgrad: {joule_calc.reg_eff:.2f}")
    pdf.ln(5)
    
    # Zustandsgrößen
    pdf.add_heading('Zustandsgrößen', 3)
    
    # Hilfsfunktion für benutzerdefinierte Sortierung
    def custom_sort_key(key):
        if isinstance(key, int):
            return key, ""
        else:
            try:
                num = int(key.rstrip("*s"))
                suffix = key[len(str(num)):]
                return num, suffix
            except (ValueError, AttributeError):
                return float('inf'), key
    
    # Zustände ausgeben
    for i in sorted(joule_calc.states.keys(), key=custom_sort_key):
        state = joule_calc.states[i]
        pdf.add_cell(f"Zustand {i}", style='B')
        pdf.add_cell(f"p [bar]: {pascal_to_bar(state['p']):.6g}")
        pdf.add_cell(f"T [K]: {state['T']:.6g}")
        pdf.add_cell(f"T [°C]: {kelvin_to_celsius(state['T']):.6g}")
        pdf.add_cell(f"v [m³/kg]: {state['v']:.6g}")
        pdf.add_cell(f"h [J/kg]: {state['h']:.6g}")
        pdf.add_cell(f"s [J/(kg·K)]: {state['s']:.6g}")
        pdf.ln(2)
    
    pdf.ln(5)
    
    # Prozessgrößen
    try:
        props = joule_calc.calculate_process_properties()
        pdf.add_heading('Prozessgrößen', 3)
        
        if 'eta_th' in props:
            pdf.add_cell(f"eta_th [-]: {props['eta_th']:.4f}")
        pdf.add_cell(f"w_KP [J/kg]: {props['w_kp']:.2f}")
        pdf.add_cell(f"q_zu [J/kg]: {props['q_in']:.2f}")
        if 'q_out' in props:
            pdf.add_cell(f"q_ab [J/kg]: {props['q_out']:.2f}")
        if 'pi' in props:
            pdf.add_cell(f"pi [-]: {props['pi']:.4f}")
        if 'tau' in props:
            pdf.add_cell(f"tau [-]: {props['tau']:.4f}")
        
        pdf.ln(5)
    except Exception as e:
        pdf.add_cell(f"Fehler bei der Berechnung der Prozessgrößen: {e}")
    
    # Diagramme einfügen
    if include_plots:
        for diagram_type in ['Ts', 'pv', 'hs']:
            pdf.add_page()
            
            if diagram_type == 'Ts':
                pdf.add_heading('T-s-Diagramm', 3)
            elif diagram_type == 'pv':
                pdf.add_heading('p-v-Diagramm', 3)
            else:  # hs
                pdf.add_heading('h-s-Diagramm', 3)
            
            # Temporäre Datei für das Diagramm
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
                temp_name = temp.name
            
            # Diagramm erzeugen und speichern
            fig, ax = plot_process(joule_calc, diagram_type=diagram_type, save_fig=True, filename=temp_name)
            plt.close(fig)
            
            # Diagramm in PDF einfügen
            pdf.image(temp_name, x=10, y=30, w=190)
            
            # Temporäre Datei löschen
            os.unlink(temp_name)
    
    # Berechnungsschritte
    pdf.add_page()
    pdf.add_heading('Detaillierte Berechnungsschritte', 2)
    
    for category, steps in joule_calc.step_categories.items():
        pdf.add_page()
        pdf.add_heading(f"Kategorie: {category}", 3)
        
        for step in steps:
            pdf.add_cell(step['title'], style='B')
            
            if step['formula']:
                pdf.add_cell(f"Formel: {step['formula']}", style='I')
            
            if step['calculation']:
                # Lange Berechnungstexte aufteilen
                calc_text = step['calculation']
                chunks = [calc_text[i:i+80] for i in range(0, len(calc_text), 80)]
                
                pdf.add_cell(f"Berechnung: {chunks[0]}")
                for chunk in chunks[1:]:
                    pdf.add_cell(chunk)
            
            if step['result'] is not None:
                result_str = f"{step['result']:.6g}" if isinstance(step['result'], float) else str(step['result'])
                unit_str = f" {step['unit']}" if step['unit'] else ""
                pdf.add_cell(f"Ergebnis: {result_str}{unit_str}", style='B')
            
            pdf.ln(2)
    
    # PDF speichern
    try:
        pdf.output(output_file)
        print(f"Berechnung gespeichert in {output_file}")
    except Exception as e:
        print(f"Fehler beim Speichern der PDF: {e}")
        
        # Detaillierte Fehlerinformationen für Debugging
        import traceback
        traceback.print_exc()
        
        # Versuche alternativen Speicheransatz
        try:
            print("Versuche alternativen Speicheransatz...")
            # Bei älteren FPDF-Versionen kann es helfen, erst in Bytes zu konvertieren
            with open(output_file, 'wb') as f:
                f.write(pdf.output(dest='S').encode('latin1'))
            print(f"PDF wurde mit alternativem Ansatz gespeichert in {output_file}")
        except Exception as e2:
            print(f"Auch alternativer Ansatz fehlgeschlagen: {e2}")
            print("Bitte aktualisieren Sie Ihre FPDF-Installation: pip install --upgrade fpdf")
            print("Oder versuchen Sie FPDF2: pip install fpdf2")