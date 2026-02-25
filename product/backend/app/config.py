from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
DATA_MIGRATION_ROOT = ROOT / "data_migration"
SCHEMAS_DIR = DATA_MIGRATION_ROOT / "schemas"
REPORTS_DIR = DATA_MIGRATION_ROOT / "reports"
MOCK_SOURCE_DIR = DATA_MIGRATION_ROOT / "mock_data" / "source"
MOCK_TARGET_DIR = DATA_MIGRATION_ROOT / "mock_data" / "target"
MOCK_TARGET_CONTRACT_DIR = DATA_MIGRATION_ROOT / "mock_data" / "target_contract"
