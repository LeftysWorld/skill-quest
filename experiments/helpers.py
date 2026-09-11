from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------- Load json ----------

def load_json(_model, _filename):
    _path = PROJECT_ROOT / "experiments" / "artifacts" / _filename

    if not _path.exists():
        raise FileNotFoundError(
            f"Artifact not found: {_path}"
        )
    return _model.model_validate_json(
        _path.read_text(encoding="utf-8")
    )

