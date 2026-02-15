import subprocess
from pathlib import Path
from bun.install import get_executable_path


def build_quasar():
    wd = Path().cwd() / "quasar"
    bun = get_executable_path()

    print(subprocess.run([bun, "run","build"], cwd=wd, check=True))
