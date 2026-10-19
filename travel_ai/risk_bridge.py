"""Mount the crowd/risk Flask routes on the travel app under /api/risk.

The trained pipelines stay in the risk-management folder. This module only
attaches their existing views. It does not load or modify the itinerary models.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import warnings
from pathlib import Path

_DEFAULT_ROOT = (
    Path(__file__).resolve().parents[1]
    / "risk-management1_final_20261018_153823"
    / "components"
    / "risk-management"
    / "backend"
)


def mount_risk(flask_app) -> None:
    root = Path(os.environ.get("RISK_BACKEND") or _DEFAULT_ROOT)
    if not root.is_dir():
        flask_app.logger.warning("Risk backend folder missing: %s", root)
        return

    root_s = str(root)
    if root_s not in sys.path:
        sys.path.append(root_s)

    # Pipelines were saved with scikit-learn 1.7.1. Loading them on the
    # itinerary app's scikit-learn warns, but predict() still runs. Do not
    # upgrade scikit-learn here: the itinerary joblib file depends on it.
    warnings.filterwarnings("ignore", message="Trying to unpickle estimator")

    app_py = root / "app.py"
    spec = importlib.util.spec_from_file_location("tourism_risk_standalone", app_py)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {app_py}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["tourism_risk_standalone"] = module
    spec.loader.exec_module(module)
    risk_app = module.app

    mounted = 0
    for rule in list(risk_app.url_map.iter_rules()):
        if rule.endpoint == "static":
            continue
        view = risk_app.view_functions.get(rule.endpoint)
        if view is None:
            continue
        methods = sorted((rule.methods or set()) - {"HEAD", "OPTIONS"})
        flask_app.add_url_rule(
            "/api/risk" + rule.rule,
            endpoint=f"risk_{rule.endpoint}",
            view_func=view,
            methods=methods or ["GET"],
        )
        mounted += 1

    print(
        f"Risk module mounted at /api/risk ({mounted} routes, "
        f"{len(getattr(module, 'SITES', {}) or {})} sites, "
        f"models_loaded={getattr(module, 'MODELS_LOADED', False)})"
    )
