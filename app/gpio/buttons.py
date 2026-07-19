"""Optional GPIO support. GPIO absence must never stop the UI."""
import logging
LOG=logging.getLogger(__name__)
class Buttons:
 def __init__(self, previous, toggle, next_):
  try:
   from gpiozero import Button
   self.buttons=[Button(18, pull_up=True),Button(23,pull_up=True),Button(24,pull_up=True)]
   for button, callback in zip(self.buttons,(previous,toggle,next_)): button.when_pressed=callback
  except Exception as exc: LOG.info("Botões GPIO indisponíveis: %s",exc); self.buttons=[]
 def close(self):
  for b in self.buttons: b.close()
