"""Keep test imports from mutating the release source tree."""

import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
SRC = Path(__file__).resolve().parents[1] / "src"
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

MISSING_TORCH_REFERENCE_REASON = (
    "Torch reference asset not configured; runtime release tests remain active."
)


@pytest.fixture
def torch_model_state() -> Path:
    from torch_reference_paths import resolve_model_state, validate_model_state

    state = resolve_model_state()
    if state is None:
        pytest.skip(MISSING_TORCH_REFERENCE_REASON)
    try:
        return validate_model_state(state)
    except RuntimeError as error:
        pytest.fail(str(error))


@pytest.fixture
def torch_reference_root(torch_model_state: Path) -> Path:
    from torch_reference_paths import MODEL_STATE_RELATIVE_PATH

    root = torch_model_state
    for _part in MODEL_STATE_RELATIVE_PATH.parts:
        root = root.parent
    return root

# These tests exercise the preserved legacy medical tree and its heavyweight
# environment. The release-default suite is deliberately scoped to the
# lightweight ModelScope canary; the legacy files remain directly runnable.
collect_ignore = [
    "test_jsonl_case_packages.py",
    "test_release_contract.py",
    "test_release_runtime.py",
    "test_tool_execution.py",
]
