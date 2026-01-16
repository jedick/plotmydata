from pathlib import Path
import warnings
import os
from . import agent

# Ensure upload directory exists
upload_dir = "/tmp/uploads"
Path(upload_dir).mkdir(parents=True, exist_ok=True)
# Read, write, execute for owner; read and execute for others
os.chmod(upload_dir, 0o755)

# Suppress Pydantic serialization warnings
warnings.filterwarnings("ignore", message="Pydantic serializer warnings")
