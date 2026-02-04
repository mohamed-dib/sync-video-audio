import os
import re
import shutil
import subprocess
import tempfile
from pydub import AudioSegment

def sanitize_path(path):
    """
    Copie le fichier dans /tmp en remplaçant
    tout caractère non alphanumérique par "_".
    Si la copie cible == source, on ne copie pas.
    """
    name = os.path.basename(path)
    safe_name = re.sub(r'[^A-Za-z0-9_.-]', '_', name)
    tmp_path = os.path.join(tempfile.gettempdir(), safe_name)
    # Ne pas copier si c'est déjà le même fichier
    if os.path.abspath(path) != os.path.abspath(tmp_path):
        shutil.copy2(path, tmp_path)
    return tmp_path


