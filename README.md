# Praxisnachbereitung SS25

## Projektbeschreibung

Dieses Projekt ist Teil der Übung "Tag 1: ETL mit Excel · Git-Einstieg" im Rahmen der Lehrveranstaltung "Praxisnachbereitung" an der Hochschule Karlsruhe. 

Ziel ist es, reale CSV-Daten zu importieren, zu bereinigen, zusammenzuführen und visuell auszuwerten. Der gesamte Prozess wird mit Git versioniert und dokumentiert.


## Datensätze

- **Geraete.csv**: Geräteinformationen (Gerätenummer, Typ, Modell, Kaufdatum, Preis, Standort)
- **Mitarbeiter.csv**: Mitarbeiterinformationen (Mitarbeiter-ID, Name, Abteilung, Standort)
- **Ausleihen.csv**: Ausleihvorgänge (Gerätenummer, Mitarbeiter-ID, Ausgabedatum, Rückgabedatum)

## Arbeitsablauf

### Augabe 1

- GitHub-Repository erstellt: `praxisnachbereitung-ss25`
- README.md und .gitignore hinzugefügt
- Repository lokal geklont
- Ordner `excel/` erstellt
- CSV-Dateien hinzugefügt
- Erster Commit durchgeführt: "Startdateien hinzugefügt"

### Augabe 2

**Import:**
- Alle drei CSV-Dateien mit Power Query importiert
- Trennzeichen: Semikolon (;)
- Codierung: UTF-8
- Datumsformat: TT.MM.JJJJ

**Bereinigung:**
- **Geraete.csv**: 36 Zeilen → 35 Zeilen (1 leere Zeile entfernt)
- **Mitarbeiter.csv**: 12 Zeilen (keine Bereinigung erforderlich)
- **Ausleihen.csv**: 46 Zeilen → 45 Zeilen (1 leere Zeile entfernt)

**Durchgeführte Bereinigungsschritte:**
1. Komplett leere Zeilen entfernt
2. Datensätze mit leerer Gerätenummer gelöscht
3. Datumsformatierung: TT.MM.JJJJ → Excel-Datumstyp
4. Preisfelder in numerische Werte konvertiert (Netto-Kaufpreis)

### Augabe 3

**Merge-Prozess:**
1. **Erste Zusammenführung**: Ausleihen + Geräte (über Gerätenummer)
2. **Zweite Zusammenführung**: Ergebnis + Mitarbeiter (über Mitarbeiter-ID)
3. **Ergebnis**: Gesamttabelle mit 45 Zeilen und 12 Spalten

**Spaltenbenennung:**
- `Standort` (aus Geräte) → `Geräte_Standort`
- `Standort` (aus Mitarbeiter) → `Mitarbeiter_Standort`

Alle 45 Ausleihvorgänge wurden erfolgreich mit Geräte- und Mitarbeiterinformationen verknüpft.

### Augabe 4
#### 4a

**Methodik:**
- Filtern zuerst mit Null-Wert von "Rückgabe am"  
- Mit Spalte G zeigt Gesamtwert nicht im Einsatz, in G2 diese Titel einschreiben.
- Schreiben Funktion =SUMIFS(H2:H46, D2:D46, "") in G2 ein und entfern alle andere Werte von diese Spalte
- **Gesamtwert nicht verwendeter Geräte: 14460.65 €**


#### 4b

**Filter:** Gerätetyp = "Laptop"
**Ergebnis:** 10 Ausleihvorgänge

**Ergebnis-Arbeitsblatt:** `Laptop`

#### 4c

| Gerätetyp | Anzahl Ausleihen |
|-----------|------------------|
| Beamer | 12 |
| Drucker | 12 |
| Laptop | 10 |
| Monitor | 4 |
| Smartphone | 4 |
| Tablet | 3 |

**Visualisierung:** Säulendiagramm erstellt

#### 4d

|           | Berlin | Hamburg | München |
|-----------|--------|---------|---------|
| Beamer    | 7      | 3       | 2       |
| Drucker   | 9      | 2       | 1       |
| Laptop    | 0      | 4       | 6       |
| Monitor   | 2      | 0       | 2       |
| Smartphone| 0      | 0       | 4       |
| Tablet    | 0      | 2       | 1       |

**Visualisierung:** Gestapeltes Säulendiagramm erstellt

**Ergebnis-Arbeitsblatt:** `PivotTable`

### Aufgabe 5


**CSV-Export:**
1. **Manueller Export**: Gesamttabelle als CSV UTF-8 exportiert
2. **Python-Export**: Skript `export_csv.py` erstellt, das die Gesamttabelle aus Excel extrahiert

**Dateien:**
- `exports/Gesamttabelle.csv` (mit Zeitstempel)
- `/export_csv.py`

## Entdeckte Probleme und Lösungen

### Problem 1: Leere Zeilen in CSV-Dateien
**Symptom:** Am Ende von `Geraete.csv` und `Ausleihen.csv` befanden sich komplett leere Zeilen.

**Lösung:** 
- In Power Query: Zeilen entfernen → Leere Zeilen entfernen
- Alternativ: Filter auf Gerätenummer anwenden (nur nicht-leere Werte)

### Problem 2: Datumsformat-Inkonsistenz
**Symptom:** Datum als Text im Format TT.MM.JJJJ in CSV-Dateien.

**Lösung:**
- In Power Query: Spaltentyp auf "Datum" setzen

### Problem 3: Spaltennamenskonflikte
**Symptom:** Beide Tabellen (Geräte und Mitarbeiter) enthalten eine "Standort"-Spalte.

**Lösung:**
- Eindeutige Umbenennung:
  - `Standort` (Geräte) → `Geräte_Standort`
  - `Standort` (Mitarbeiter) → `Mitarbeiter_Standort`

## Wichtige Erkenntnisse aus der Analyse

## Technischer Stack

- **Microsoft Excel**: Datenanalyse und Visualisierung
- **Power Query**: ETL-Prozesse (Import, Transformation, Laden)
- **Python**: Automatisierung und Export
  - `pandas`: Datenverarbeitung
  - `openpyxl`: Excel-Dateien lesen/schreiben
- **Git**: Versionskontrolle
- **GitHub**: Remote-Repository

## Autor

**Name:** Tiancheng Wang und Atay Özcan
**Matrikelnummer:** 95290 und 95270

