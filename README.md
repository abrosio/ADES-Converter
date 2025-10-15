ADES Converter
Piccolo tool desktop (PyQt5) per convertire file fotometrici in un file testo formattato in ADES (o in formato personalizzato coerente alle specifiche usate nel programma).
Semplifica il flusso da software di riduzione come CANOPUS e Tycho al formato pronto per l’uso.
Autore: Antonino Brosio (ABObservatory L90)

Cosa fa
Legge automaticamente diversi formati di input:
CSV/TXT con colonne JD, Mag, MagErr

CANOPUS:
ALCDEF (DATA=JD|MAG|ERR|…)
Tabelle “Observations …” con colonne … O-CAvg Err

Tycho:
“Fotometry” con header JD MAG ERR (spazi/tab)
Converte il tempo JD in UTC ISO-8601 (YYYY-MM-DDThh:mm:ss[.xx]Z) con numero di decimali configurabile.
Formatta magnitudine ed errore con decimali configurabili (ROUND_HALF_UP).

Allinea le colonne in output:
#obsTime mag magUnc

Autocompone il nome del file di output come:
YYYYMMDDUTC_<MPC>_<OGGETTO_SENZA_SPAZI>_<NOSS>_<FILTRO>.txt
(es.: 20250920UTC_L90_2025FA22_40_CLEAR.txt)

Drag & Drop: trascina un file sul campo in alto per caricarlo.
Campi memorizzati: MPC, Oggetto osservato, Filtro e preferenze sui decimali restano salvati per i successivi avvii.
Tema scuro opzionale (qdarkstyle, se presente).

Requisiti
Python 3.9+ (consigliato)

Librerie:
pip install PyQt5 astropy qdarkstyle

Crediti
Sviluppato da Antonino Brosio (ABObservatory L90).
