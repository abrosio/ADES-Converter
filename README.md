# 🌌 ADES Converter

**ADES Converter** è un software desktop sviluppato in **Python (PyQt5)** da **Antonino Brosio (ABObservatory L90)** per convertire automaticamente i file **fotometrici** provenienti da **CANOPUS** o **Tycho** in formato **ADES** (“Astrometry Data Exchange Standard”) o in un formato testo personalizzato coerente con le specifiche.

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
  - Esempio: `2025-09-20T21:03:12.34Z`
- 🎯 Impostazione del numero di **decimali** per data, magnitudine e errore
- 💾 Generazione automatica del nome file in formato:
  ```
  YYYYMMDDUTC_<MPC>_<OGGETTO>_<NOSS>_<FILTRO>.txt
  ```
  Esempio: `20250920UTC_L90_2025FA22_40_CLEAR.txt`
- 🎨 Interfaccia moderna e chiara, con supporto per **tema scuro (qdarkstyle)**
- 🧠 Memorizzazione automatica dei campi MPC, Oggetto, Filtro e preferenze
- 📂 Supporto **drag & drop** del file direttamente nella finestra
- 🔒 Campo percorso non scrivibile, solo selezionabile tramite “Apri File” o trascinamento

---

## 🖥️ Requisiti

- **Python 3.9+**
- Librerie richieste:
  ```bash
  pip install PyQt5 astropy qdarkstyle
  ```
  > `qdarkstyle` è opzionale (solo per il tema scuro)

---

## 🚀 Avvio del programma

```bash
python main.py
```

1. Clicca su **“Apri File”** oppure **trascina** un file nel campo in alto  
2. Inserisci:
   - Codice MPC (es. `L90`)
   - Oggetto osservato (es. `2025 FA22`)
   - Filtro (es. `CLEAR`)
3. Imposta i decimali per tempo, magnitudine ed errore  
4. Premi **“Converti”** per creare il file in formato ADES  
5. Premi **“Ripristina”** per azzerare i campi e tornare ai valori predefiniti  

---

## 📄 Esempio di output

```
#obsTime mag magUnc
2025-09-20T21:03:12.34Z  15.2  0.03
2025-09-20T21:03:32.34Z  15.1  0.02
2025-09-20T21:03:52.34Z  15.1  0.03
```

---

## 🧠 Note

- Supporta formati multipli (CANOPUS, Tycho, CSV) **senza dover specificare nulla manualmente**.  
- L’output è compatibile con la struttura **ADES** per l’invio dati a ricercatori o per uso personale.

---

## 👨‍💻 Autore

**Sviluppato da:** Antonino Brosio  
**Affiliazione:** ABObservatory L90  

---
