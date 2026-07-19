#!/usr/bin/env python3
import argparse, json, logging, signal, sys
from pathlib import Path
from app.backend.models import TuneRequest
from app.backend.receiver import Receiver
from app.backend.settings import SettingsStore
from app.gpio.buttons import Buttons
DEFAULTS={"mode":"Aviacao","frequency_hz":118000000,"modulation":"am","step_hz":25000,"gain":"auto","squelch":0,"volume":80,"audio_device":"default","rtl_serial":"00000001","demo_mode":False}

class RadioWindow:
 def __init__(self, settings, store):
  from PyQt5.QtCore import Qt
  from PyQt5.QtWidgets import QApplication,QGridLayout,QHBoxLayout,QLabel,QMainWindow,QPushButton,QVBoxLayout,QWidget
  self.Qt=Qt; self.settings=settings; self.store=store; self.receiver=Receiver(settings['audio_device'],settings.get('rtl_serial'),settings.get('demo_mode'))
  self.window=QMainWindow(); self.window.setWindowTitle('Rádio Móvel SDR'); self.window.setWindowState(Qt.WindowFullScreen)
  root=QWidget(); layout=QVBoxLayout(root); self.mode=QLabel(); self.mode.setAlignment(Qt.AlignCenter); self.freq=QLabel(); self.freq.setAlignment(Qt.AlignCenter)
  self.status=QLabel('Parado'); self.status.setAlignment(Qt.AlignCenter); layout.addWidget(self.mode);layout.addWidget(self.freq);layout.addWidget(self.status)
  grid=QGridLayout(); buttons=[('◀ Anterior',self.previous),('▶ Próximo',self.next),('▶ Receber',self.toggle),('Favoritos',self.favorites),('Scanner',self.scanner),('Volume −',lambda:self.volume(-5)),('Volume +',lambda:self.volume(5)),('Configurações',self.configure),('Desligar',self.shutdown)]
  for n,(name,fn) in enumerate(buttons):
   b=QPushButton(name);b.setMinimumHeight(52);b.clicked.connect(fn);grid.addWidget(b,n//3,n%3)
  layout.addLayout(grid); self.window.setCentralWidget(root); self.refresh(); self.buttons=Buttons(self.previous,self.toggle,self.next)
 def refresh(self):
  self.mode.setText(f"{self.settings['mode']}  •  {self.settings['modulation'].upper()}  •  passo {self.settings['step_hz']/1000:g} kHz")
  self.freq.setText(f"{self.settings['frequency_hz']/1e6:.3f} MHz")
  self.freq.setStyleSheet('font-size: 42px; font-weight: bold'); self.mode.setStyleSheet('font-size: 20px')
 def tune(self, direction):
  self.settings['frequency_hz']+=direction*self.settings['step_hz']; self.store.save(self.settings); self.refresh()
  if self.receiver.running: self.start()
 def previous(self): self.tune(-1)
 def next(self): self.tune(1)
 def start(self):
  try: self.receiver.start(TuneRequest(self.settings['frequency_hz'],self.settings['modulation'],self.settings['gain'],self.settings['squelch']));self.status.setText('● RECEBENDO' if not self.settings['demo_mode'] else '● DEMONSTRAÇÃO')
  except (ValueError,RuntimeError) as exc:self.status.setText(str(exc))
 def toggle(self):
  if self.receiver.running:self.receiver.stop();self.status.setText('Parado')
  else:self.start()
 def favorites(self): self.status.setText('Edite favoritos em /var/lib/radio-movel-sdr/presets.json')
 def scanner(self): self.status.setText('Scanner: configure canais em presets.json')
 def volume(self, delta): self.settings['volume']=max(0,min(100,self.settings['volume']+delta));self.store.save(self.settings);self.status.setText(f"Volume: {self.settings['volume']}%")
 def configure(self): self.status.setText('Configurações persistidas em /var/lib/radio-movel-sdr/settings.json')
 def shutdown(self): self.receiver.stop(); self.status.setText('Desligamento seguro solicitado'); __import__('subprocess').Popen(['systemctl','poweroff'])
 def show(self):self.window.show()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--demo',action='store_true');parser.add_argument('--config-dir',default='/var/lib/radio-movel-sdr');args=parser.parse_args()
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
 store=SettingsStore(Path(args.config_dir)/'settings.json'); settings=store.load(DEFAULTS);settings['demo_mode']=args.demo or settings.get('demo_mode',False)
 try:
  from PyQt5.QtWidgets import QApplication
 except ImportError: print('PyQt5 não instalado. Execute scripts/install.sh.',file=sys.stderr);return 2
 app=QApplication(sys.argv); window=RadioWindow(settings,store);signal.signal(signal.SIGTERM,lambda *_:app.quit());window.show();return app.exec_()
if __name__=='__main__':raise SystemExit(main())
