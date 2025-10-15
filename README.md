# 🌌 ADES Converter

**ADES Converter** è un software desktop sviluppato in **Python (PyQt5)** da **Antonino Brosio (ABObservatory L90)**  
per convertire automaticamente i file **fotometrici** provenienti da **CANOPUS** o **Tycho** in formato **ADES**  
(“Astrometry Data Exchange Standard”) o in un formato testo personalizzato coerente con le specifiche.

---

## 🧩 Funzionalità principali

- ✅ Rilevamento automatico del tipo di file:
  - **CANOPUS**
    - Formato **ALCDEF** (`DATA=JD|MAG|ERR|...`)
    - Tabelle “**Observations**” con colonne `O-CAvg  Err`
  - **Tycho**
    - File “**Fotometry**” con header `JD  MAG  ERR`
  - **CSV/TXT** standard con colonne `JD, Mag, MagErr`
- 🕓 Conversione automatica del tempo **JD → UTC ISO-8601**
  - Es. `2025-09-20T21:03:12.34Z`
- 🎯 Impostazione del numero di **decimali** per data, magnitudine e errore
- 💾 Generazione automatica del nome file in formato:
YYYYMMDDUTC_<MPC><OGGETTO><NOSS>_<FILTRO>.txt
Esempio: `20250920UTC_L90_2025FA22_40_CLEAR.txt`
- 🎨 Interfaccia moderna e chiara, con supporto per **tema scuro (qdarkstyle)**
- 🧠 Memorizzazione automatica dei campi MPC, Oggetto, Filtro e preferenze
- 📂 Supporto **drag & drop** del file direttamente nella finestra
- 🔒 Campo percorso non scrivibile, solo selezionabile tramite “Apri File” o drag

---

## 🖥️ Requisiti

- **Python 3.9+**
- Librerie richieste:
```bash
pip install PyQt5 astropy qdarkstyle


## 👨‍💻 Autore
Sviluppato da: Antonino Brosio
