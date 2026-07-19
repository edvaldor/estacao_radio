"""Consultas de diagnóstico que não dependem de um número fixo de eventN."""

import glob
import grp
import os
from pathlib import Path
import pwd
import stat
import subprocess


def touchscreen_devices(sysfs_pattern='/sys/class/input/event*/device/name'):
    """Retorna os touchscreens encontrados com o respectivo ``/dev/input/eventN``."""
    found = []
    for name_path in glob.glob(sysfs_pattern):
        try:
            name = Path(name_path).read_text().strip()
        except OSError:
            continue
        if 'ads7846' in name.lower() or 'touchscreen' in name.lower():
            event_name = Path(name_path).parent.parent.name
            found.append((f'/dev/input/{event_name}', name, name_path))
    return found


def user_can_read(path, user):
    """Verifica as permissões Unix de leitura de *path* para *user*.

    Não usa ``os.access`` porque ele verifica o usuário efetivo do processo (que
    normalmente é root quando ``radioctl doctor`` é executado com sudo).
    """
    try:
        account = pwd.getpwnam(user)
        file_stat = os.stat(path)
    except (KeyError, OSError):
        return False
    groups = {account.pw_gid}
    groups.update(group.gr_gid for group in grp.getgrall() if user in group.gr_mem)
    mode = file_stat.st_mode
    if file_stat.st_uid == account.pw_uid:
        return bool(mode & stat.S_IRUSR)
    if file_stat.st_gid in groups:
        return bool(mode & stat.S_IRGRP)
    return bool(mode & stat.S_IROTH)


def pyqt5_xcb_support():
    """Informa se o PyQt5 instalado possui o plugin de plataforma X11 (xcb)."""
    try:
        from PyQt5.QtCore import QLibraryInfo
    except ImportError as exc:
        return False, f'PyQt5 indisponível: {exc}'
    plugins_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
    plugin = Path(plugins_path) / 'platforms' / 'libqxcb.so'
    if plugin.is_file():
        return True, f'plugin xcb encontrado em {plugin}'
    return False, f'plugin xcb ausente em {plugin}'


def rtl_test():
    try:
        result = subprocess.run(['rtl_test', '-t'], text=True, capture_output=True, timeout=15)
        return result.stdout + result.stderr
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f'Falha ao testar RTL-SDR: {exc}'
