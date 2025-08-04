"""
Plotting functions for the JOULE process calculator.
Creates diagrams of the thermodynamic cycle.
"""

import matplotlib.pyplot as plt
from utils.converters import pascal_to_bar

def custom_sort_key(key):
    """
    Custom sorting function for mixed key types (int and str)
    
    Parameters:
    key : object
        The key to sort
        
    Returns:
    tuple:
        Sorting criteria tuple
    """
    if isinstance(key, int):
        return key, ""  # Numbers first, no suffix
    else:
        # String keys like "2*" or "4s"
        try:
            # Extract the numeric part
            if key.rstrip("*s").isdigit():
                num = int(key.rstrip("*s"))
                suffix = key[len(str(num)):]
                return num, suffix
            else:
                return float('inf'), key  # Fallback
        except (ValueError, AttributeError):
            return float('inf'), key  # Fallback for non-string, non-int keys

def plot_process(joule_calc, diagram_type="Ts", save_fig=False, filename=None, show_points=True):
    """
    Zeichnet den Prozess in einem Diagramm
    
    Parameter:
    joule_calc : JouleProcessCalculator
        Instanz des JouleProcessCalculator
    diagram_type : str
        Art des Diagramms ('Ts', 'pv', 'hs')
    save_fig : bool
        Wenn True, wird die Figur gespeichert
    filename : str
        Dateiname für die gespeicherte Figur
    show_points : bool
        Wenn True, werden die Zustandspunkte im Diagramm angezeigt
    """
    if not all(i in joule_calc.states for i in [1, 2, 3, 4]):
        raise ValueError("Alle Zustände (1, 2, 3, 4) müssen berechnet sein.")
    
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
    
    # Punktkoordinaten vorbereiten
    x_vals = []
    y_vals = []
    labels = []
    for label, point in points.items():
        x_val = point[x_key]
        y_val = point[y_key]
        if y_key == "p":
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
    if joule_calc.regeneration and "2*" in joule_calc.states and "4*" in joule_calc.states:
        # Mit Regeneration
        # 1 -> 2
        ax.plot([points[1][x_key], points[2][x_key]], 
                [points[1][y_key] if y_key != "p" else pascal_to_bar(points[1][y_key]), 
                 points[2][y_key] if y_key != "p" else pascal_to_bar(points[2][y_key])], 
                'k-', linewidth=2)
        # 2 -> 2*
        ax.plot([points[2][x_key], points["2*"][x_key]], 
                [points[2][y_key] if y_key != "p" else pascal_to_bar(points[2][y_key]), 
                 points["2*"][y_key] if y_key != "p" else pascal_to_bar(points["2*"][y_key])], 
                'k--', linewidth=2)
        # 2* -> 3
        ax.plot([points["2*"][x_key], points[3][x_key]], 
                [points["2*"][y_key] if y_key != "p" else pascal_to_bar(points["2*"][y_key]), 
                 points[3][y_key] if y_key != "p" else pascal_to_bar(points[3][y_key])], 
                'k-', linewidth=2)
        # 3 -> 4
        ax.plot([points[3][x_key], points[4][x_key]], 
                [points[3][y_key] if y_key != "p" else pascal_to_bar(points[3][y_key]), 
                 points[4][y_key] if y_key != "p" else pascal_to_bar(points[4][y_key])], 
                'k-', linewidth=2)
        # 4 -> 4*
        ax.plot([points[4][x_key], points["4*"][x_key]], 
                [points[4][y_key] if y_key != "p" else pascal_to_bar(points[4][y_key]), 
                 points["4*"][y_key] if y_key != "p" else pascal_to_bar(points["4*"][y_key])], 
                'k--', linewidth=2)
        # 4* -> 1
        ax.plot([points["4*"][x_key], points[1][x_key]], 
                [points["4*"][y_key] if y_key != "p" else pascal_to_bar(points["4*"][y_key]), 
                 points[1][y_key] if y_key != "p" else pascal_to_bar(points[1][y_key])], 
                'k-', linewidth=2)
        # Regeneration: 4 -> 2*
        ax.plot([points[4][x_key], points["2*"][x_key]], 
                [points[4][y_key] if y_key != "p" else pascal_to_bar(points[4][y_key]), 
                 points["2*"][y_key] if y_key != "p" else pascal_to_bar(points["2*"][y_key])], 
                'r--', linewidth=1)
    else:
        # Ohne Regeneration
        # Alle Punkte der Reihe nach verbinden und am Ende zum Anfang zurück
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
    if joule_calc.regeneration:
        ax.plot([], [], 'k-', label='Hauptprozess')
        ax.plot([], [], 'k--', label='Regeneration')
        ax.plot([], [], 'r--', label='Wärmeübertragung')
        ax.legend()
    
    plt.tight_layout()
    
    if save_fig and filename:
        plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    return fig, ax