import os
from pathlib import Path


# Resolve project root: prefer DM_DATA_ROOT env var, fallback to parents[3]
# parents[3] from services/backend/app/config.py -> project root
_default_root = Path(__file__).resolve().parents[3]
DATA_MIGRATION_ROOT = Path(os.environ.get("DM_DATA_ROOT", str(_default_root)))
SCHEMAS_DIR = DATA_MIGRATION_ROOT / "schemas"
REPORTS_DIR = DATA_MIGRATION_ROOT / "reports"
MOCK_SOURCE_DIR = DATA_MIGRATION_ROOT / "mock_data" / "source"
MOCK_TARGET_DIR = DATA_MIGRATION_ROOT / "mock_data" / "target"
MOCK_TARGET_CONTRACT_DIR = DATA_MIGRATION_ROOT / "mock_data" / "target_contract"
