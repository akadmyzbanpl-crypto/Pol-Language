"""Local demo launcher. Install requirements first. Not a production server."""
import os,sys,subprocess
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
os.environ['POL_DEBUG']='1'
os.environ['POL_DEMO']='1'
os.environ['POL_ALLOWED_HOSTS']='localhost,127.0.0.1'
Path('data').mkdir(exist_ok=True)
for command in [['migrate','--noinput'],['seed_demo']]:
    subprocess.run([sys.executable,'manage.py',*command],check=True)
print('\nOpen http://127.0.0.1:8000 — Keep this window open.\n',flush=True)
subprocess.run([sys.executable,'manage.py','runserver','127.0.0.1:8000','--noreload'],check=True)
