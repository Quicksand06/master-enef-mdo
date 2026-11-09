#!/usr/bin/env python3
"""
AMDO – Hausarbeit 1, Team A, Aufgabe 1.

Physikalisches Modell: einseitig eingespannter Kragbalken mit rechteckigem
Querschnitt. Am freien Ende wirkt eine Querkraft F.
WICHTIG: Die Einspannung ist eine Modellannahme, da die Aufgabenstellung
keine eindeutige Lagerung vorgibt.

Das Programm liest Eingangsparameter aus einer Textdatei, berechnet
Masse, maximale Durchbiegung und maximale Biegespannung unter
Berücksichtigung des Eigengewichts und schreibt
die Ergebnisse in eine Ausgabedatei zur späteren Einbindung in HEEDS.

Aufruf:
    python beam_calculation.py input.txt output.txt

Ohne Argumente werden input.txt und output.txt im Arbeitsverzeichnis genutzt.
Es werden keine zusätzlichen Python-Pakete benötigt.

Einheiten:
    b, h, L         – mm
    F               – N
    E, sigma_allow  – MPa = N/mm²
    rho             – kg/m³
    g (optional)    – m/s²; Standardwert 9.81
"""

import sys
from pathlib import Path


def read_input(path):
    """Eingangsparameter im Format „Name Wert“ einlesen."""
    data = {}

    # Zeilennummerierung beginnt bei 1, damit Fehlermeldungen eindeutig sind.
    for line_number, raw in enumerate(
        Path(path).read_text(encoding='utf-8').splitlines(), 1
    ):
        # Alles nach „#“ ist ein Kommentar; Leerzeilen werden übersprungen.
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue

        # Beide Schreibweisen sind erlaubt: 'b 40' und 'b = 40'.
        parts = line.replace('=', ' ').split()
        if len(parts) != 2:
            raise ValueError(f'Line {line_number}: expected "key value"')

        key, value = parts
        if key in data:
            raise ValueError(f'Duplicate input parameter: {key}')

        # Alle Eingabewerte werden als Gleitkommazahlen eingelesen.
        data[key] = float(value)

    # Prüfen, ob alle für die Berechnung erforderlichen Parameter vorhanden sind.
    required = ('b', 'h', 'L', 'F', 'E', 'rho', 'sigma_allow')
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError('Missing parameters: ' + ', '.join(missing))

    # Optionale Erdbeschleunigung prüfen.
    if 'g' in data and not 0 < data['g'] < float('inf'):
        raise ValueError('g must be positive and finite')

    # Alle Parameter müssen positiv und endlich sein; dies entspricht
    # den Annahmen des hier verwendeten Berechnungsmodells.
    for key in required:
        if not 0 < data[key] < float('inf'):
            raise ValueError(f'{key} must be positive and finite')

    return data


def calculate(p):
    """Masse, Durchbiegung, Länge und maximale Biegespannung berechnen."""

    # Geometrie: Querschnittsbreite b, Querschnittshöhe h und Balkenlänge L [mm].
    b, h, L = p['b'], p['h'], p['L']

    # Querkraft F [N], Elastizitätsmodul E [MPa], Werkstoffdichte rho [kg/m³].
    F, E, rho = p['F'], p['E'], p['rho']

    # 1. Flächenträgheitsmoment des Rechteckquerschnitts [mm^4].
    #    Die Höhe h liegt in Richtung der Querkraft und geht kubisch ein.
    #    Nicht mit dem Massenträgheitsmoment verwechseln.
    I = b * h**3 / 12.0

    # 2. Balkenmasse [kg] = Dichte * Volumen.
    #    Das Volumen b*h*L liegt in mm³ vor; 1 mm³ = 10^-9 m³.
    mass = rho * (b * h * L) * 1e-9

    # 3. Gleichmäßig verteilte Streckenlast durch Eigengewicht [N/mm].
    #    Querschnitt A = b*h [mm²]; Umrechnung in m² mit 10^-6.
    #    rho*A_m² ergibt kg/m; Multiplikation mit g ergibt N/m.
    #    Umrechnung von N/m in N/mm mit 10^-3.
    #    Das Eigengewicht wirkt in derselben Richtung wie die Endkraft F.
    g = p.get('g', 9.81)  # Erdbeschleunigung [m/s²]
    q = rho * (b * h * 1e-6) * g * 1e-3

    # 4. Maximale Durchbiegung am freien Ende [mm].
    #    Superposition aus Endkraft und gleichmäßiger Streckenlast:
    #        w_F = F*L³/(3*E*I)
    #        w_G = q*L⁴/(8*E*I)
    deflection_force = F * L**3 / (3.0 * E * I)
    deflection_self_weight = q * L**4 / (8.0 * E * I)
    deflection = deflection_force + deflection_self_weight

    # 5. Maximale Biegespannung an der Einspannung [MPa].
    #    Biegemoment durch Endkraft: M_F = F*L [N*mm].
    #    Biegemoment durch Eigengewicht: M_G = q*L²/2 [N*mm].
    #    Spannung an der Randfaser: sigma = (M_F + M_G)*(h/2)/I.
    moment_force = F * L
    moment_self_weight = q * L**2 / 2.0
    sigma = (moment_force + moment_self_weight) * (h / 2.0) / I

    # 6. Prüfung der Spannungsnebenbedingung.
    #    stress_ok = 1 bei sigma <= sigma_allow, sonst 0.
    #    235 MPa ist hier ein nomineller Richtwert für S235JR, kein
    #    automatisch mit Sicherheitsbeiwert festgelegter zulässiger Wert.
    stress_ok = int(sigma <= p['sigma_allow'])

    # Die Länge wird nicht berechnet, sondern als Entwurfsvariable eingelesen
    # und für das dritte Optimierungsziel in die Ausgabedatei übernommen.
    return {
        'mass_kg': mass,              # in HEEDS minimieren
        'deflection_mm': deflection,   # in HEEDS minimieren
        'length_mm': L,               # in HEEDS maximieren
        'sigma_max_MPa': sigma,       # Nebenbedingung: <= sigma_allow
        'stress_ok': stress_ok,       # zusätzliche Prüfung (1/0)
        'self_weight_N': q * L,      # Eigengewichtskraft [N]
        'deflection_force_mm': deflection_force,  # Anteil der Endkraft
        'deflection_self_weight_mm': deflection_self_weight,  # Eigengewichtsanteil
    }


def main():
    # Kommandozeilenargumente: zuerst Eingabedatei, dann Ausgabedatei.
    # Ohne Argumente werden die Standarddateinamen verwendet.
    input_path = sys.argv[1] if len(sys.argv) > 1 else 'input.txt'
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'output.txt'

    # Zuerst Eingabewerte einlesen, anschließend Ergebnisse berechnen.
    p = read_input(input_path)
    result = calculate(p)

    # Ergebnisse zeilenweise im Format 'Name Wert' speichern.
    # Dieses Format lässt sich in HEEDS einfach auslesen.
    # .10g schreibt bis zu zehn signifikante Stellen ohne unnötige Nullen.
    Path(output_path).write_text(
        ''.join(
            f'{key} {value:.10g}\n' if isinstance(value, float)
            else f'{key} {value}\n'
            for key, value in result.items()
        ),
        encoding='utf-8'
    )

    # Ergebnisse zusätzlich zur schnellen Kontrolle in der Konsole ausgeben.
    for key, value in result.items():
        print(f'{key}: {value}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, OverflowError) as exc:
        # Bei einem Fehler eine Meldung und den Rückgabecode 1 ausgeben.
        # So kann HEEDS einen fehlgeschlagenen Berechnungslauf erkennen.
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
