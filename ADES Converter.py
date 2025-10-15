import os
import sys
import csv
import re
from typing import List, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui

try:
    import qdarkstyle  # type: ignore
    QDARKSTYLE_AVAILABLE = True
except Exception:
    QDARKSTYLE_AVAILABLE = False

from astropy.time import Time


def sniff_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", " "])
        return dialect.delimiter
    except Exception:
        return ","


def read_csv_jd_mag_err(path: str) -> List[Tuple[float, str, str]]:
    rows: List[Tuple[float, str, str]] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    sample_lines = [ln for ln in content.splitlines() if not ln.strip().startswith("#")]
    sample = "\n".join(sample_lines[:10]) if sample_lines else content[:1000]
    delimiter = sniff_delimiter(sample)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter=delimiter)
        header_checked = False
        jd_idx = mag_idx = magerr_idx = None
        for raw in reader:
            if not raw or (len(raw) == 1 and raw[0].strip() == ""):
                continue
            if raw[0].strip().startswith("#"):
                continue
            if not header_checked:
                cols = [c.strip() for c in raw]
                low = [c.lower() for c in cols]
                poss = {"jd": None, "mag": None, "magerr": None}
                for i, name in enumerate(low):
                    if name == "jd":
                        poss["jd"] = i
                    elif name in ("mag", "magnitude"):
                        poss["mag"] = i
                    elif name in ("magerr", "mag_unc", "magunc", "err", "error"):
                        poss["magerr"] = i
                if all(v is not None for v in poss.values()):
                    jd_idx, mag_idx, magerr_idx = poss["jd"], poss["mag"], poss["magerr"]
                    header_checked = True
                    continue
                else:
                    jd_idx, mag_idx, magerr_idx = 0, 1, 2
                    header_checked = True
            if max(jd_idx, mag_idx, magerr_idx) >= len(raw):
                continue
            jd_txt = raw[jd_idx].strip().replace(",", ".")
            mag_txt = raw[mag_idx].strip().replace(",", ".")
            magerr_txt = raw[magerr_idx].strip().replace(",", ".")
            try:
                jd_val = float(jd_txt)
                _ = float(mag_txt)
                _ = float(magerr_txt)
            except ValueError:
                continue
            rows.append((jd_val, mag_txt, magerr_txt))
    return rows


def read_canopus_alcdef(path: str) -> List[Tuple[float, str, str]]:
    rows: List[Tuple[float, str, str]] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or not line.startswith("DATA="):
                continue
            payload = line.split("=", 1)[1]
            parts = [p.strip() for p in payload.split("|")]
            if len(parts) < 3:
                continue
            jd_txt, mag_txt, err_txt = parts[0], parts[1], parts[2]
            try:
                jd_val = float(jd_txt)
                _ = float(mag_txt.replace("+", ""))
                _ = float(err_txt.replace("+", ""))
            except ValueError:
                continue
            rows.append((jd_val, mag_txt.replace("+", ""), err_txt.replace("+", "")))
    return rows


def read_alcdef_generic(path: str) -> List[Tuple[float, str, str]]:
    return read_canopus_alcdef(path)


def read_canopus_observations_table(path: str) -> List[Tuple[float, str, str]]:
    rows: List[Tuple[float, str, str]] = []
    in_table = False
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            ln = raw.strip()
            if not ln:
                continue
            if not in_table:
                if set(ln) == set("-"):
                    in_table = True
                continue
            if ln[0] not in ("Y", "N"):
                continue
            parts = ln.split()
            if len(parts) < 5:
                continue
            if parts[0] != "Y":
                continue
            try:
                jd_val = float(parts[1])
            except ValueError:
                continue
            mag_txt = parts[-2].replace("+", "")
            err_txt = parts[-1].replace("+", "")
            try:
                _ = float(mag_txt)
                _ = float(err_txt)
            except ValueError:
                continue
            rows.append((jd_val, mag_txt, err_txt))
    return rows


def read_tycho_fotometry_whitespace(path: str) -> List[Tuple[float, str, str]]:
    rows: List[Tuple[float, str, str]] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for i, raw in enumerate(f):
            ln = raw.strip()
            if not ln:
                continue
            if i == 0:
                head_parts = ln.split()
                if len(head_parts) >= 3 and head_parts[0].upper() == "JD":
                    continue
            parts = ln.split()
            if len(parts) < 3:
                continue
            jd_txt, mag_txt, err_txt = parts[0], parts[1], parts[2]
            try:
                jd_val = float(jd_txt)
                _ = float(mag_txt.replace("+", ""))
                _ = float(err_txt.replace("+", ""))
            except ValueError:
                continue
            rows.append((jd_val, mag_txt.replace("+", ""), err_txt.replace("+", "")))
    return rows


def read_any_input(path: str) -> List[Tuple[float, str, str]]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(8000)
    except Exception:
        head = ""
    head_low = head.lower()
    if ("startmetadata" in head_low or "alcdef" in head_low) and "data=" in head_low:
        rows = read_alcdef_generic(path)
        if rows:
            return rows
    if "observation data" in head_low and "o-cavg" in head_low and "err" in head_low:
        rows = read_canopus_observations_table(path)
        if rows:
            return rows
    first_nonempty = ""
    for ln in head.splitlines():
        s = ln.strip()
        if s:
            first_nonempty = s
            break
    if first_nonempty:
        parts = first_nonempty.split()
        if len(parts) >= 3 and parts[0].upper() == "JD" and parts[1].upper().startswith("MAG") and parts[2].upper().startswith("ERR"):
            rows = read_tycho_fotometry_whitespace(path)
            if rows:
                return rows
    return read_csv_jd_mag_err(path)


def jd_to_isot_z(jd_val: float, precision: int = 2) -> str:
    t = Time(jd_val, format="jd", scale="utc")
    old_precision = Time.precision
    try:
        Time.precision = precision
        isot = t.utc.isot
    finally:
        Time.precision = old_precision
    return f"{isot}Z"


def to_n_decimals(s: str, n: int) -> str:
    try:
        d = Decimal(s)
    except Exception:
        d = Decimal(str(float(s)))
    q = Decimal("1").scaleb(-n)
    return str(d.quantize(q, rounding=ROUND_HALF_UP))


def format_columns(obs_times: List[str], mags: List[str], magerrs: List[str], mag_dec: int, err_dec: int) -> List[str]:
    mags_fmt = [to_n_decimals(x, mag_dec) for x in mags]
    errs_fmt = [to_n_decimals(x, err_dec) for x in magerrs]
    w_mag = max(3, *(len(s) for s in mags_fmt))
    w_err = max(3, *(len(s) for s in errs_fmt))
    lines = []
    header = "#obsTime mag magUnc"
    lines.append(header)
    for t, m, e in zip(obs_times, mags_fmt, errs_fmt):
        lines.append(f"{t} {m:>{w_mag}} {e:>{w_err}}")
    return lines


def sanitize_token_keep_underscore(s: str) -> str:
    s = (s or "").strip().upper().replace(" ", "_")
    s = re.sub(r"[^A-Z0-9_]", "", s)
    return s or "NA"


def sanitize_token_no_space(s: str) -> str:
    s = (s or "").strip().upper().replace(" ", "")
    s = re.sub(r"[^A-Z0-9]", "", s)
    return s or "NA"


def create_white_info_label() -> QtWidgets.QLabel:
    text = (
        "Convertitore in formato ADES. Importa i file da Tycho o CANOPUS. "
        "Software scritto da Antonino Brosio (ABObservatory L90)."
    )
    lbl = QtWidgets.QLabel(text)
    lbl.setWordWrap(True)
    lbl.setAlignment(QtCore.Qt.AlignCenter)
    try:
        db = QtGui.QFontDatabase()
        preferred = ["Calibri", "Segoe UI", "Arial", "Helvetica", "DejaVu Sans"]
        family = next((f for f in preferred if f in db.families()), lbl.font().family())
    except Exception:
        family = "Calibri"
    font = QtGui.QFont(family, 11)
    font.setWeight(QtGui.QFont.DemiBold)
    lbl.setFont(font)
    lbl.setStyleSheet("QLabel { color: white; font-weight: 2; font-size: 10pt; }")
    return lbl


class FileDropLineEdit(QtWidgets.QLineEdit):
    fileDropped = QtCore.pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.setReadOnly(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        md = event.mimeData()
        if md.hasUrls():
            for url in md.urls():
                if url.isLocalFile():
                    event.acceptProposedAction()
                    return
        elif md.hasText():
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent):
        md = event.mimeData()
        path = None
        if md.hasUrls():
            for url in md.urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    break
        elif md.hasText():
            txt = md.text().strip()
            if os.path.exists(txt):
                path = txt
        if path and os.path.exists(path):
            self.setText(path)
            try:
                self.fileDropped.emit(path)
            except Exception:
                pass
            event.acceptProposedAction()
        else:
            event.ignore()


class ConverterWindow(QtWidgets.QWidget):
    DEFAULT_DATE_DEC = 2
    DEFAULT_MAG_DEC = 1
    DEFAULT_ERR_DEC = 2

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ADES Converter")
        self.setAcceptDrops(True)
        self.resize(800, 480)
        self.lock_current_size()
        self.settings = QtCore.QSettings("ABProject Space", "ADES Converter")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ico = os.path.join(base_dir, "icon.ico")
        if os.path.exists(ico):
            try:
                self.setWindowIcon(QtGui.QIcon(ico))
            except Exception:
                pass
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        path_row = QtWidgets.QHBoxLayout()
        path_row.setSpacing(6)
        self.path_edit = FileDropLineEdit()
        self.path_edit.setPlaceholderText("Apri o trascina il file da convertire")
        self.path_edit.fileDropped.connect(lambda p: self.log_msg(f"File trascinato: {p}"))
        browse_btn = QtWidgets.QPushButton("Apri File")
        browse_btn.clicked.connect(self.on_browse)
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse_btn, 0)
        compact_row = QtWidgets.QHBoxLayout()
        compact_row.setSpacing(12)
        left_col = QtWidgets.QVBoxLayout()
        left_col.setSpacing(6)
        left_form = QtWidgets.QFormLayout()
        left_form.setSpacing(6)
        self.mpc_edit = QtWidgets.QLineEdit()
        self.obj_edit = QtWidgets.QLineEdit()
        self.filt_edit = QtWidgets.QLineEdit()
        self.mpc_edit.setPlaceholderText("es. L90")
        self.obj_edit.setPlaceholderText("es. 2025 FA22")
        self.filt_edit.setPlaceholderText("es. CLEAR")
        left_form.addRow("Codice MPC:", self.mpc_edit)
        left_form.addRow("Oggetto Osservato:", self.obj_edit)
        left_form.addRow("Filtro Utilizzato:", self.filt_edit)
        self.mpc_edit.setText(self.settings.value("mpc_code", "", type=str))
        self.obj_edit.setText(self.settings.value("object_name", "", type=str))
        self.filt_edit.setText(self.settings.value("filter_used", "", type=str))
        self.info_label = create_white_info_label()
        buttons_row = QtWidgets.QHBoxLayout()
        buttons_row.setSpacing(50)
        buttons_row.setAlignment(QtCore.Qt.AlignCenter)
        self.reset_btn = QtWidgets.QPushButton("Ripristina")
        self.convert_btn = QtWidgets.QPushButton("Converti")
        for btn in (self.reset_btn, self.convert_btn):
            btn.setMinimumHeight(34)
            btn.setStyleSheet("QPushButton { padding: 6px 14px; font-weight: 600; }")
        self.reset_btn.clicked.connect(self.on_reset)
        self.convert_btn.clicked.connect(self.on_convert)
        buttons_row.addWidget(self.reset_btn)
        buttons_row.addWidget(self.convert_btn)
        left_col.addLayout(left_form)
        left_col.addWidget(self.info_label)
        left_col.addLayout(buttons_row)
        right_group = QtWidgets.QGroupBox("Decimali")
        rg_layout = QtWidgets.QGridLayout(right_group)
        rg_layout.setHorizontalSpacing(8)
        rg_layout.setVerticalSpacing(6)
        self.dec_date_spin = QtWidgets.QSpinBox()
        self.dec_date_spin.setRange(0, 9)
        self.dec_date_spin.setValue(self.DEFAULT_DATE_DEC)
        self.dec_mag_spin = QtWidgets.QSpinBox()
        self.dec_mag_spin.setRange(0, 6)
        self.dec_mag_spin.setValue(self.DEFAULT_MAG_DEC)
        self.dec_err_spin = QtWidgets.QSpinBox()
        self.dec_err_spin.setRange(0, 6)
        self.dec_err_spin.setValue(self.DEFAULT_ERR_DEC)
        rg_layout.addWidget(QtWidgets.QLabel("Data (s):"), 0, 0)
        rg_layout.addWidget(self.dec_date_spin, 0, 1)
        rg_layout.addWidget(QtWidgets.QLabel("Magnitudine:"), 1, 0)
        rg_layout.addWidget(self.dec_mag_spin, 1, 1)
        rg_layout.addWidget(QtWidgets.QLabel("Errore:"), 2, 0)
        rg_layout.addWidget(self.dec_err_spin, 2, 1)
        compact_row.addLayout(left_col, 2)
        compact_row.addWidget(right_group, 1)
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Log di conversione…")
        self.log.setMaximumHeight(140)
        layout.addLayout(path_row)
        layout.addLayout(compact_row)
        layout.addWidget(self.log)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        md = event.mimeData()
        if md.hasUrls():
            for url in md.urls():
                if url.isLocalFile():
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent):
        md = event.mimeData()
        if not md.hasUrls():
            event.ignore()
            return
        for url in md.urls():
            if url.isLocalFile():
                path = url.toLocalFile()
                if os.path.exists(path):
                    self.path_edit.setText(path)
                    try:
                        self.log_msg(f"File trascinato: {path}")
                    except Exception:
                        pass
                    event.acceptProposedAction()
                    return
        event.ignore()

    def log_msg(self, msg: str):
        self.log.appendPlainText(msg)

    def lock_current_size(self):
        self.repaint()
        size = self.size()
        self.setMinimumSize(size)
        self.setMaximumSize(size)

    def on_browse(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Seleziona file (CSV/TXT/DAT)",
            "",
            "CSV/TXT/DAT (*.csv *.txt *.dat);;Tutti i file (*.*)",
        )
        if path:
            self.path_edit.setText(path)

    def _build_suggested_filename(self, obs_times: List[str], n_obs: int) -> str:
        if not obs_times:
            date_tag = datetime.utcnow().strftime("%Y%m%d") + "UTC"
        else:
            iso0 = obs_times[0]
            yyyy_mm_dd = iso0[:10]
            try:
                date_tag = datetime.strptime(yyyy_mm_dd, "%Y-%m-%d").strftime("%Y%m%d") + "UTC"
            except Exception:
                date_tag = datetime.utcnow().strftime("%Y%m%d") + "UTC"
        mpc = sanitize_token_keep_underscore(self.mpc_edit.text())
        obj = sanitize_token_no_space(self.obj_edit.text())
        filt = sanitize_token_keep_underscore(self.filt_edit.text())
        return f"{date_tag}_{mpc}_{obj}_{n_obs}_{filt}"

    def on_reset(self):
        self.mpc_edit.clear()
        self.obj_edit.clear()
        self.filt_edit.clear()
        self.dec_date_spin.setValue(self.DEFAULT_DATE_DEC)
        self.dec_mag_spin.setValue(self.DEFAULT_MAG_DEC)
        self.dec_err_spin.setValue(self.DEFAULT_ERR_DEC)
        self.settings.setValue("mpc_code", "")
        self.settings.setValue("object_name", "")
        self.settings.setValue("filter_used", "")
        self.log_msg("Valori ripristinati ai predefiniti.")

    def on_convert(self):
        path = self.path_edit.text().strip()
        if not path or not os.path.exists(path):
            QtWidgets.QMessageBox.warning(self, "Attenzione", "Seleziona un file valido (CSV/TXT/DAT).")
            return
        self.settings.setValue("mpc_code", self.mpc_edit.text())
        self.settings.setValue("object_name", self.obj_edit.text())
        self.settings.setValue("filter_used", self.filt_edit.text())
        try:
            self.log.clear()
            self.log_msg(f"File sorgente: {path}")
            rows = read_any_input(path)
            if not rows:
                QtWidgets.QMessageBox.warning(self, "Nessun dato", "Nessuna riga valida trovata (JD, Mag, MagErr).")
                return
            self.log_msg(f"Righe valide: {len(rows)}")
            date_dec = int(self.dec_date_spin.value())
            mag_dec = int(self.dec_mag_spin.value())
            err_dec = int(self.dec_err_spin.value())
            obs_times: List[str] = []
            mags: List[str] = []
            errs: List[str] = []
            for jd_val, mag_txt, err_txt in rows:
                try:
                    t_isot = jd_to_isot_z(jd_val, precision=date_dec)
                except Exception as e:
                    self.log_msg(f"[WARN] JD {jd_val} non convertibile: {e}")
                    continue
                obs_times.append(t_isot)
                mags.append(mag_txt)
                errs.append(err_txt)
            if not obs_times:
                QtWidgets.QMessageBox.warning(self, "Errore", "Tutte le conversioni JD sono fallite.")
                return
            lines = format_columns(obs_times, mags, errs, mag_dec=mag_dec, err_dec=err_dec)
            n_obs = len(lines) - 1
            suggested_name = self._build_suggested_filename(obs_times, n_obs) + ".txt"
            out_path_default = os.path.join(os.path.dirname(path), suggested_name)
            out_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Salva TXT in formato ADES",
                out_path_default,
                "Testo (*.txt);;Tutti i file (*.*)",
            )
            if not out_path:
                self.log_msg("Salvataggio annullato.")
                return
            with open(out_path, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(lines) + "\n")
            self.log_msg(f"Salvato: {out_path}")
            QtWidgets.QMessageBox.information(self, "Fatto", f"Conversione completata.\nFile: {out_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Errore", str(e))
            self.log_msg(f"[ERROR] {e}")


def main():
    app = QtWidgets.QApplication(sys.argv)
    if QDARKSTYLE_AVAILABLE:
        try:
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        except Exception:
            pass
    w = ConverterWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
