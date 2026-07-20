#!/usr/bin/env python3
"""Touch-first 480x320 front end for the radio receiver.

The Qt import is intentionally delayed until it is available: command-line
diagnostics and the backend can still be imported on a headless machine.
"""
import argparse
import importlib.util
import logging
import signal
import sys
from pathlib import Path

from app.audio import set_volume
from app.backend.models import TuneRequest
from app.backend.receiver import Receiver
from app.backend.presets import PresetStore
from app.backend.settings import SettingsStore
from app.gpio.buttons import Buttons
from app.scanner.engine import Scanner


DEFAULTS = {
    "mode": "AIR", "frequency_hz": 118_000_000, "modulation": "am",
    "step_hz": 25_000, "gain": "auto", "squelch": 0, "volume": 80,
    "audio_device": "default", "rtl_serial": "00000001", "demo_mode": False,
    "scanner_dwell_seconds": 5,
}

# A band describes the safe initial tuning presented by the UI.  The backend
# remains the final authority for RTL-SDR limits.
BANDS = {
    "FM": {"frequency_hz": 99_900_000, "limits": (88_000_000, 108_000_000), "step_hz": 100_000, "modulation": "wfm", "preset": "FM 99.9"},
    "AIR": {"frequency_hz": 118_000_000, "limits": (118_000_000, 137_000_000), "step_hz": 25_000, "modulation": "am", "preset": "AIR inicial"},
    "VHF": {"frequency_hz": 146_520_000, "limits": (136_000_000, 174_000_000), "step_hz": 12_500, "modulation": "nfm", "preset": "VHF chamada"},
    "UHF": {"frequency_hz": 433_500_000, "limits": (400_000_000, 470_000_000), "step_hz": 12_500, "modulation": "nfm", "preset": "UHF chamada"},
    "CB 11 m": {"frequency_hz": 27_185_000, "limits": (26_965_000, 27_405_000), "step_hz": 5_000, "modulation": "am", "preset": "Canal 19"},
    "HAM": {"frequency_hz": 145_500_000, "limits": (144_000_000, 148_000_000), "step_hz": 12_500, "modulation": "nfm", "preset": "HAM 2 m"},
}


if importlib.util.find_spec("PyQt5"):
    from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal
    from PyQt5.QtGui import QColor, QPainter, QPen
    from PyQt5.QtWidgets import (QApplication, QDial, QFrame, QGridLayout,
                                 QHBoxLayout, QLabel, QMainWindow, QPushButton,
                                 QProgressBar, QSlider, QVBoxLayout, QWidget,
                                 QInputDialog)

    NIGHT_STYLE = """
        QWidget { background: #050b12; color: #f5f7fa; font-family: Sans Serif; }
        QFrame#card { border: 2px solid #536273; border-radius: 9px; background: #081321; }
        QPushButton { background: #101e31; border: 2px solid #697789; border-radius: 8px;
                      color: #f7f8fa; font-size: 16px; font-weight: bold; padding: 5px; }
        QPushButton:checked { background: #ffb000; color: #07101c; border-color: #ffd36a; }
        QPushButton:pressed { background: #1ac5e5; color: #041019; }
        QSlider::groove:horizontal { height: 12px; border-radius: 6px; background: #313d4c; }
        QSlider::sub-page:horizontal { background: #12b9da; border-radius: 6px; }
        QSlider::handle:horizontal { width: 22px; margin: -7px 0; border-radius: 8px; background: #f5f7fa; }
        QProgressBar { border: 1px solid #536273; border-radius: 4px; height: 10px; text-align: center; }
        QProgressBar::chunk { background: #12b9da; border-radius: 3px; }
        QDial { background: #0d1d30; }
    """

    class SpectrumWidget(QWidget):
        """A deliberately cheap visual spectrum: one repaint every 500 ms."""
        def __init__(self):
            super().__init__()
            self.phase = 0
            self.setMinimumHeight(35)
            self.setMaximumHeight(42)
            self.setAccessibleName("Espectro simplificado")

        def tick(self):
            self.phase = (self.phase + 1) % 19
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, False)
            rect = self.rect().adjusted(3, 3, -3, -3)
            painter.fillRect(rect, QColor("#06101b"))
            painter.setPen(QPen(QColor("#526071"), 1))
            painter.drawRect(rect)
            painter.setPen(QPen(QColor("#11c7e8"), 2))
            points = []
            for x in range(rect.left(), rect.right() + 1, 4):
                centre = rect.center().x()
                distance = abs(x - centre) / max(1, rect.width() / 2)
                peak = max(0, int((1 - distance * 2.2) * rect.height() * .68))
                ripple = (x * 7 + self.phase * 13) % 11
                y = rect.bottom() - 8 - peak - ripple
                points.append((x, max(rect.top() + 4, y)))
            for (x1, y1), (x2, y2) in zip(points, points[1:]):
                painter.drawLine(x1, y1, x2, y2)
            painter.setPen(QPen(QColor("#ffb000"), 2))
            painter.drawLine(rect.center().x(), rect.top() + 3, rect.center().x(), rect.bottom() - 3)


    class ReceiverWorker(QThread):
        finished = pyqtSignal(str)

        def __init__(self, receiver, request):
            super().__init__()
            self.receiver, self.request = receiver, request

        def run(self):
            try:
                self.receiver.start(self.request)
                self.finished.emit("● DEMONSTRAÇÃO" if self.receiver.demo else "● RTL-SDR RECEBENDO")
            except (RuntimeError, ValueError) as exc:
                self.finished.emit("RTL-SDR indisponível: " + str(exc))


    class RadioWindow(QMainWindow):
        def __init__(self, settings, store, recording_dir=None):
            super().__init__()
            self.settings, self.store = settings, store
            self.receiver = Receiver(settings["audio_device"], settings.get("rtl_serial"), settings.get("demo_mode"), recording_dir or store.path.parent / "recordings")
            self.presets = PresetStore(store.path.parent / "presets.json")
            self.scanner_engine = Scanner([], dwell_seconds=settings.get("scanner_dwell_seconds", 5))
            self.current_band = settings.get("mode") if settings.get("mode") in BANDS else "AIR"
            self.worker = None
            self.setWindowTitle("Rádio SDR")
            self.setMinimumSize(480, 320)
            self.setStyleSheet(NIGHT_STYLE)
            self._build_ui()
            self.buttons = Buttons(self.previous, self.toggle, self.next)
            self.spectrum_timer = QTimer(self)
            self.spectrum_timer.timeout.connect(self.spectrum.tick)
            self.spectrum_timer.start(500)  # Caps CPU work at 2 frames per second.
            self.scanner_timer = QTimer(self); self.scanner_timer.timeout.connect(self.scan_tick); self.scanner_timer.start(250)
            self.refresh()

        def _card(self):
            card = QFrame(); card.setObjectName("card")
            return card

        def _build_ui(self):
            root = QWidget(); outer = QVBoxLayout(root); outer.setContentsMargins(7, 5, 7, 5); outer.setSpacing(5)
            header = self._card(); h = QHBoxLayout(header); h.setContentsMargins(9, 4, 9, 4)
            title = QLabel("RÁDIO SDR"); title.setStyleSheet("font-size: 21px; font-weight: bold")
            self.rtl_status = QLabel(); self.rtl_status.setAlignment(Qt.AlignCenter)
            h.addWidget(title); h.addStretch(); h.addWidget(self.rtl_status); h.addWidget(QLabel("GPS: INDISP.")); h.addWidget(QLabel("BATERIA: INDISP."))
            outer.addWidget(header)
            bands = QGridLayout(); bands.setSpacing(4); self.band_buttons = {}
            for index, name in enumerate(BANDS):
                button = QPushButton(name); button.setCheckable(True); button.setMinimumHeight(30)
                button.clicked.connect(lambda checked, band=name: self.select_band(band))
                bands.addWidget(button, 0, index); self.band_buttons[name] = button
            outer.addLayout(bands)
            body = QHBoxLayout(); body.setSpacing(6); left = self._card(); l = QVBoxLayout(left); l.setContentsMargins(9, 5, 9, 5); l.setSpacing(2)
            self.frequency = QLabel(); self.frequency.setStyleSheet("color:#ffb000; font-size: 39px; font-weight:bold"); self.frequency.setAlignment(Qt.AlignCenter); self.frequency.setMaximumHeight(50)
            self.preset = QLabel(); self.preset.setStyleSheet("font-size: 17px; font-weight:bold"); self.preset.setAlignment(Qt.AlignCenter); self.preset.setMaximumHeight(25)
            l.addWidget(self.frequency); l.addWidget(self.preset)
            controls = QHBoxLayout(); self.minus = QPushButton("−"); self.plus = QPushButton("+")
            for button in (self.minus, self.plus): button.setMinimumSize(58, 35)
            self.minus.clicked.connect(self.previous); self.plus.clicked.connect(self.next)
            self.step_label = QLabel(); self.step_label.setAlignment(Qt.AlignCenter); self.step_label.setStyleSheet("font-size:15px; font-weight:bold")
            controls.addWidget(self.minus); controls.addWidget(self.step_label, 1); controls.addWidget(self.plus)
            l.addLayout(controls)
            mods = QHBoxLayout(); self.mod_buttons = {}
            for mode in ("am", "fm", "nfm", "wfm"):
                button = QPushButton(mode.upper()); button.setCheckable(True); button.setMinimumHeight(30)
                button.clicked.connect(lambda checked, value=mode: self.set_modulation(value)); mods.addWidget(button); self.mod_buttons[mode] = button
            l.addLayout(mods)
            self.spectrum = SpectrumWidget(); l.addWidget(self.spectrum)
            meter = QHBoxLayout(); meter.setSpacing(4)
            self.status = QLabel(); self.status.setWordWrap(True); self.status.setAlignment(Qt.AlignCenter); self.status.setMaximumHeight(24)
            self.level_label = QLabel("NÍVEL: N/D"); self.level_label.setStyleSheet("font-size: 13px; font-weight:bold")
            self.level = QProgressBar(); self.level.setRange(0, 100); self.level.setValue(0); self.level.setFormat("N/D"); self.level.setMaximumWidth(68)
            meter.addWidget(self.status, 1); meter.addWidget(self.level_label); meter.addWidget(self.level); l.addLayout(meter)
            body.addWidget(left, 3)
            side = self._card(); s = QVBoxLayout(side); s.setContentsMargins(7, 5, 7, 5)
            self.dial = QDial(); self.dial.setRange(-20, 20); self.dial.setNotchesVisible(True); self.dial.setWrapping(False); self.dial.setMinimumSize(95, 95)
            self.dial.sliderReleased.connect(self.dial_tune); s.addWidget(self.dial, alignment=Qt.AlignCenter)
            self._add_slider(s, "VOL", "volume", self.change_volume)
            self._add_slider(s, "SQL", "squelch", self.change_squelch)
            body.addWidget(side, 1); outer.addLayout(body, 1)
            actions = QHBoxLayout()
            action = QPushButton("RECEBER / PARAR"); action.setMinimumHeight(34); action.clicked.connect(self.toggle); actions.addWidget(action)
            self.favorite_button = QPushButton("★ FAVORITOS"); self.favorite_button.clicked.connect(self.favorites); actions.addWidget(self.favorite_button)
            self.scanner_button = QPushButton("▶ SCANNER"); self.scanner_button.setCheckable(True); self.scanner_button.clicked.connect(self.scanner); actions.addWidget(self.scanner_button)
            outer.addLayout(actions)
            self.record_button = QPushButton("● GRAVAR"); self.record_button.setCheckable(True); self.record_button.setMinimumHeight(44); self.record_button.setStyleSheet("font-size: 21px; font-weight: bold; color: #ff6666")
            self.record_button.clicked.connect(self.toggle_recording); outer.addWidget(self.record_button)
            self.setCentralWidget(root)

        def _add_slider(self, layout, title, key, callback):
            label = QLabel(); label.setStyleSheet("font-size: 15px; font-weight:bold")
            slider = QSlider(Qt.Horizontal); slider.setRange(0, 100); slider.setMinimumHeight(30); slider.valueChanged.connect(callback)
            setattr(self, key + "_label", label); setattr(self, key + "_slider", slider)
            layout.addWidget(label); layout.addWidget(slider)

        def select_band(self, name):
            band = BANDS[name]; self.current_band = name
            self.settings.update(mode=name, frequency_hz=band["frequency_hz"], step_hz=band["step_hz"], modulation=band["modulation"])
            self.persist_and_refresh(restart=True)

        def set_modulation(self, mode):
            if mode == "wfm" and not 64_000_000 <= self.settings["frequency_hz"] <= 108_000_000:
                self.status.setText("WFM disponível somente entre 64 e 108 MHz")
                self.refresh()
                return
            self.settings["modulation"] = mode
            self.persist_and_refresh(restart=True)

        def _limits(self):
            return BANDS[self.current_band]["limits"]

        def tune(self, direction):
            low, high = self._limits(); step = self.settings["step_hz"]
            self.settings["frequency_hz"] = max(low, min(high, self.settings["frequency_hz"] + direction * step))
            self.persist_and_refresh(restart=True)

        def previous(self): self.tune(-1)
        def next(self): self.tune(1)
        def dial_tune(self):
            value = self.dial.value(); self.dial.setValue(0)
            if value: self.tune(value)

        def change_volume(self, value):
            if getattr(self, "_refreshing", False): return
            try: set_volume(value)
            except (RuntimeError, ValueError) as exc: self.status.setText(str(exc)); return
            self.settings["volume"] = value; self.store.save(self.settings); self.refresh()

        def change_squelch(self, value):
            if getattr(self, "_refreshing", False): return
            self.settings["squelch"] = value; self.store.save(self.settings); self.refresh()

        def persist_and_refresh(self, restart=False):
            self.store.save(self.settings); self.refresh()
            if restart and self.receiver.running: self.start()

        def favorites(self):
            """Select, create or remove persisted favourites in one touch flow."""
            options = [f"Sintonizar: {p['name']} ({p['frequency_hz'] / 1e6:.3f} MHz)" for p in self.presets.load()]
            options += ["Adicionar frequência atual", "Excluir favorito"]
            choice, accepted = QInputDialog.getItem(self, "Favoritos", "Ação:", options, 0, False)
            if not accepted: return
            saved = self.presets.load()
            if choice == "Adicionar frequência atual":
                name, accepted = QInputDialog.getText(self, "Novo favorito", "Nome:")
                if accepted and name.strip():
                    self.presets.add({"name": name.strip(), "frequency_hz": self.settings["frequency_hz"], "modulation": self.settings["modulation"]})
                    self.status.setText("Favorito salvo")
            elif choice == "Excluir favorito":
                if not saved: self.status.setText("Não há favoritos para excluir"); return
                names = [p["name"] for p in saved]
                name, accepted = QInputDialog.getItem(self, "Excluir favorito", "Favorito:", names, 0, False)
                if accepted: self.presets.remove(names.index(name)); self.status.setText("Favorito excluído")
            else:
                index = options.index(choice)
                preset = saved[index]
                self.settings.update(frequency_hz=preset["frequency_hz"], modulation=preset["modulation"])
                self.persist_and_refresh(restart=True)

        def scanner(self, checked):
            if not checked:
                self.scanner_engine.stop(); self.scanner_button.setText("▶ SCANNER"); self.status.setText("Scanner parado"); return
            channels = self.presets.load()
            self.scanner_engine = Scanner(channels, dwell_seconds=self.settings.get("scanner_dwell_seconds", 5))
            try:
                self.scanner_engine.start()
            except ValueError as exc:
                self.scanner_button.setChecked(False); self.status.setText(str(exc)); return
            self.scanner_button.setText("■ PARAR SCAN"); self.status.setText("Scanner iniciado")
            self.scan_tick()

        def scan_tick(self):
            preset = self.scanner_engine.tick()
            if not preset: return
            self.settings.update(frequency_hz=preset["frequency_hz"], modulation=preset["modulation"])
            self.persist_and_refresh(restart=True)
            self.status.setText("Scanner: " + preset["name"])

        def toggle_recording(self, checked):
            try:
                if checked:
                    path = self.receiver.start_recording(self.settings["frequency_hz"], self._request().sample_rate)
                    self.status.setText("Gravando: " + path.name); self.record_button.setText("■ PARAR GRAVAÇÃO")
                else:
                    self.receiver.stop_recording(); self.status.setText("Gravação salva"); self.record_button.setText("● GRAVAR")
            except RuntimeError as exc:
                self.record_button.setChecked(False); self.status.setText(str(exc))

        def _request(self):
            return TuneRequest(self.settings["frequency_hz"], self.settings["modulation"], self.settings["gain"], self.settings["squelch"])

        def start(self):
            if self.worker and self.worker.isRunning(): return
            self.status.setText("Iniciando RTL-SDR…")
            self.worker = ReceiverWorker(self.receiver, self._request()); self.worker.finished.connect(self.receiving_finished); self.worker.start()

        def receiving_finished(self, message):
            self.status.setText(message); self.refresh()

        def toggle(self):
            if self.receiver.running:
                self.receiver.stop(); self.status.setText("RTL-SDR parado")
                self.record_button.setChecked(False); self.record_button.setText("● GRAVAR")
            else: self.start()
            self.refresh()

        def refresh(self):
            self._refreshing = True
            try:
                frequency = self.settings["frequency_hz"] / 1_000_000
                self.frequency.setText(f"{frequency:.3f} MHz")
                band = BANDS[self.current_band]
                self.preset.setText(f"{band['preset']}  •  {self.settings['modulation'].upper()}")
                self.step_label.setText(f"PASSO\n{self.settings['step_hz'] / 1000:g} kHz")
                for name, button in self.band_buttons.items(): button.setChecked(name == self.current_band)
                for name, button in self.mod_buttons.items(): button.setChecked(name == self.settings["modulation"])
                self.volume_slider.setValue(self.settings["volume"]); self.squelch_slider.setValue(self.settings["squelch"])
                self.volume_label.setText(f"VOL {self.settings['volume']}%")
                self.squelch_label.setText(f"SQL {self.settings['squelch']}%")
                state = "SIMULADO" if self.receiver.demo else ("ATIVO" if self.receiver.running else self.receiver.availability())
                self.rtl_status.setText("RTL-SDR: " + state)
                # rtl_fm's audio pipeline has no trustworthy RSSI feed.  Keep
                # the meter visibly unavailable instead of inventing a level.
                self.level.setValue(0); self.level.setFormat("N/D")
            finally: self._refreshing = False

        def closeEvent(self, event):
            self.spectrum_timer.stop(); self.scanner_timer.stop(); self.receiver.stop(); self.buttons.close(); event.accept()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--demo", action="store_true"); parser.add_argument("--config-dir", default="/var/lib/radio-movel-sdr"); parser.add_argument("--recording-dir")
    args = parser.parse_args(); logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not importlib.util.find_spec("PyQt5"):
        print("PyQt5 não instalado. Execute scripts/install.sh.", file=sys.stderr); return 2
    store = SettingsStore(Path(args.config_dir) / "settings.json"); settings = store.load(DEFAULTS)
    settings["demo_mode"] = args.demo or settings.get("demo_mode", False)
    app = QApplication(sys.argv); window = RadioWindow(settings, store, args.recording_dir)
    signal.signal(signal.SIGTERM, lambda *_: app.quit()); window.showFullScreen()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
