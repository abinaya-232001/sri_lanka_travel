"""Mount the tourism-risk Flask routes under /api/risk on the unified app."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_RISK_ROOT = (
    Path(__file__).resolve().parents[3]
    / "tourism_risk_system (1)"
    / "tourism_risk_system"
)


def mount_risk(flask_app) -> None:
    if not _RISK_ROOT.is_dir():
        flask_app.logger.warning("Risk system folder missing: %s", _RISK_ROOT)
        return

    root_s = str(_RISK_ROOT)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)

    app_py = _RISK_ROOT / "app.py"
    spec = importlib.util.spec_from_file_location("tourism_risk_standalone", app_py)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {app_py}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["tourism_risk_standalone"] = module
    spec.loader.exec_module(module)
    risk_app = module.app

    skip = {"static"}
    mounted = 0
    for rule in list(risk_app.url_map.iter_rules()):
        if rule.endpoint in skip:
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

    site_count = len(getattr(module, "SITES", {}) or {})
    flask_app.logger.info(
        "Risk module mounted at /api/risk (%s routes, %s sites, models_loaded=%s)",
        mounted,
        site_count,
        getattr(module, "MODELS_LOADED", False),
    )
