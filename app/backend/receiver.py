"""Safe lifecycle wrapper around rtl_fm and aplay; no shell is invoked."""
import glob, logging, shutil, subprocess, time
from .models import TuneRequest
LOG = logging.getLogger(__name__)

class Receiver:
    def __init__(self, audio_device="default", serial=None, demo=False):
        self.audio_device, self.serial, self.demo, self.processes = audio_device, serial, demo, []
        self.active = False
    def command(self, request):
        # rtl_fm uses "fm" for narrow FM; the UI keeps NFM distinct so it can
        # communicate the intended bandwidth without inventing an unsupported
        # rtl_fm mode.
        mode = {"am": "am", "fm": "fm", "nfm": "fm", "wfm": "wbfm"}[request.modulation]
        args = ["rtl_fm", "-M", mode, "-f", str(request.frequency_hz), "-s", str(request.sample_rate), "-l", str(request.squelch)]
        if self.serial: args += ["-d", str(self.serial)]
        if request.gain != "auto": args += ["-g", str(request.gain)]
        return args
    def start(self, request):
        self.stop()
        if self.demo:
            self.active = True
            LOG.info("Demonstração: recepção simulada em %s", request.frequency_hz)
            return
        if not shutil.which("rtl_fm") or not shutil.which("aplay"):
            raise RuntimeError("rtl_fm ou aplay não encontrado. Execute o instalador.")
        try:
            rtl = subprocess.Popen(self.command(request), stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            # Keep ownership immediately: aplay can fail after rtl_fm has started.
            self.processes = [rtl]
            audio = subprocess.Popen(["aplay", "-q", "-D", self.audio_device, "-f", "S16_LE", "-r", str(request.sample_rate), "-c", "1"], stdin=rtl.stdout, stderr=subprocess.PIPE, start_new_session=True)
        except OSError as exc: self.stop(); raise RuntimeError(f"Não foi possível iniciar o receptor: {exc}") from exc
        self.processes = [rtl, audio]
        self.active = True
        time.sleep(.15)
        if rtl.poll() is not None or audio.poll() is not None:
            failed = rtl if rtl.poll() is not None else audio
            error = (failed.stderr.read() or b"").decode(errors="replace").strip()
            self.stop()
            if "usb_claim_interface error -6" in error:
                raise RuntimeError("RTL-SDR ocupado pelo driver DVB. Execute radioctl doctor.")
            if failed is audio:
                raise RuntimeError("Saída de áudio indisponível: " + (error or self.audio_device))
            raise RuntimeError("RTL-SDR indisponível: " + error)
    def stop(self):
        for proc in reversed(self.processes):
            if proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=3)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait()
        self.processes = []
        self.active = False
    @property
    def running(self): return self.active and (self.demo or bool(self.processes) and all(p.poll() is None for p in self.processes))

    def availability(self):
        """Return a truthful lightweight readiness status without claiming USB.

        Probing with ``rtl_test`` would contend with an active tuner.  The
        definitive hardware check is performed by :meth:`start`, while this
        method safely exposes missing local dependencies to the touchscreen.
        """
        if self.demo:
            return "SIMULADO"
        if not all(shutil.which(name) for name in ("rtl_fm", "aplay")):
            return "INDISPONÍVEL"
        # This sysfs check is non-invasive: unlike rtl_test it does not claim
        # the receiver or briefly interrupt an active audio session.
        known_ids = {("0bda", "2832"), ("0bda", "2838"), ("1d19", "1101"),
                     ("1b80", "d393"), ("1b80", "d395"), ("0ccd", "00a9")}
        for vendor_path in glob.glob("/sys/bus/usb/devices/*/idVendor"):
            try:
                vendor = open(vendor_path, encoding="ascii").read().strip().lower()
                product = open(vendor_path.replace("idVendor", "idProduct"), encoding="ascii").read().strip().lower()
            except OSError:
                continue
            if (vendor, product) in known_ids:
                return "PRONTO"
        return "INDISPONÍVEL"
