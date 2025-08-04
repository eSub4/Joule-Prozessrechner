# Joule-Prozessrechner
Joule Prozessrechner
🌟 Features

Vollständige thermodynamische Berechnung des JOULE-Prozesses mit detaillierten Rechenschritten
Unterstützung verschiedener Arbeitsfluide: Luft, Helium, Stickstoff, CO₂
Temperaturabhängige Stoffwerte oder konstante Wärmekapazitäten
Erweiterte Prozessmodifikationen:

Regeneration (Wärmerückgewinnung) mit einstellbarem Wirkungsgrad
Zweistufige Verdichtung mit Zwischenkühlung
Berücksichtigung realer Komponentenwirkungsgrade


Interaktive Jupyter-Notebook-Oberfläche mit Widgets
Mehrere Visualisierungsoptionen:

T-s-Diagramm (Temperatur-Entropie)
p-v-Diagramm (Druck-Volumen)
h-s-Diagramm (Enthalpie-Entropie)


Detaillierte Ausgabe aller Zustandsgrößen und Prozessparameter
Export-Funktionen für Berechnungsergebnisse (HTML, PDF, Markdown)

📋 Voraussetzungen

Python 3.8 oder höher
Jupyter Notebook oder JupyterLab

joule-prozess-rechner/
│
├── models/
│   ├── __init__.py
│   ├── gas_properties.py      # Stoffwertdaten und thermodynamische Funktionen
│   └── joule_process.py       # Hauptberechnungsklasse
│
├── utils/
│   ├── __init__.py
│   └── converters.py          # Einheitenumrechnung
│
├── visualization/
│   ├── __init__.py
│   ├── plotting.py            # Diagrammerstellung
│   └── results_formatter.py   # Ergebnisformatierung und Export
│
├── ui/
│   ├── __init__.py
│   └── widgets.py             # Jupyter Widget-Interface
│
├── JOULE-Prozessrechner.ipynb # Hauptnotebook
├── requirements.txt
└── README.md

🎯 Funktionalitäten im Detail
Arbeitsfluide

Luft: Standardarbeitsfluid mit temperaturabhängigen Eigenschaften
Helium: Für Hochtemperaturanwendungen
Stickstoff: Für spezielle Anwendungen
CO₂: Für superkritische Prozesse

Prozessmodifikationen

Regeneration: Wärmerückgewinnung zwischen Turbinenaustritt und Verdichteraustritt
Zwischenkühlung: Zweistufige Verdichtung mit Kühlung zwischen den Stufen
Reale Komponenten: Berücksichtigung von Verdichter- und Turbinenwirkungsgraden

Berechnungsausgaben

Alle Zustandsgrößen (p, T, v, h, s) für jeden Zustandspunkt
Spezifische Arbeiten und Wärmemengen
Thermischer Wirkungsgrad
Optimales Druckverhältnis
Leistungen bei gegebenem Massenstrom

📊 Beispieldiagramme
Das Tool erstellt automatisch thermodynamische Diagramme des Prozesses:

Prozessverlauf mit allen Zustandspunkten
Kennzeichnung von Regeneration und Zwischenkühlung
Logarithmische Skalierung für p-v-Diagramme

🤝 Beitragen
Beiträge sind willkommen! Bitte erstellen Sie einen Fork des Repositories und reichen Sie Pull Requests ein.
Entwicklungsrichtlinien

Code sollte PEP 8 konform sein
Neue Features sollten dokumentiert werden
Tests für neue Funktionalitäten hinzufügen

📚 Theoretische Grundlagen
Der JOULE-Prozess (auch Brayton-Prozess) ist ein thermodynamischer Kreisprozess, der in Gasturbinen Anwendung findet. Der ideale Prozess besteht aus:

Isentroper Verdichtung (1→2)
Isobarer Wärmezufuhr (2→3)
Isentroper Expansion (3→4)
Isobarer Wärmeabfuhr (4→1)

Erweiterte Prozesse

Mit Regeneration: Nutzung der Abgaswärme zur Vorwärmung der verdichteten Luft
Mit Zwischenkühlung: Reduzierung der Verdichterarbeit durch mehrstufige Verdichtung

🐛 Bekannte Probleme

PDF-Export erfordert die Installation von fpdf
Bei sehr hohen Temperaturen können die Stoffwertkorrelationen ungenau werden

📝 Lizenz
Dieses Projekt ist unter der Apache Lizenz lizenziert - siehe LICENSE Datei für Details.

👥 Autor
Till Jonas Wellkamp

Basierend auf thermodynamischen Grundlagen aus der Technischen Thermodynamik
Stoffwertdaten aus VDI-Wärmeatlas und NIST-Datenbanken

📧 Kontakt
Bei Fragen oder Anregungen erstellen Sie bitte ein Issue im GitHub Repository.

Hinweis: Dieses Tool dient Lehrzwecken und zur Prozessanalyse. Für industrielle Anwendungen sollten validierte kommerzielle Software-Pakete verwendet werden.
