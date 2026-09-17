import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_executar_pipeline_help_loads_app_package():
    result = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'executar_pipeline.py'), '--help'],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert 'Pipeline de Nutrição Canina' in result.stdout
