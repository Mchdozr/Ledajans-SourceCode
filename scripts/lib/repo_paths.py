"""Repository path constants — tüm betikler buradan import eder."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content"
OPS = ROOT / "ops"
OPS_WORDPRESS = OPS / "wordpress"
OPS_NGINX = OPS / "nginx"
DATA = ROOT / "data"
DATA_BASELINES = DATA / "baselines"
AGENT_HUB = ROOT / "AGENT-HUB"
SCRIPTS = ROOT / "scripts"


def content_path(rel: str) -> Path:
    return CONTENT / rel.replace("/", os.sep)


def data_path(rel: str) -> Path:
    return DATA / rel.replace("/", os.sep)


def ops_wordpress_path(name: str) -> Path:
    return OPS_WORDPRESS / name
