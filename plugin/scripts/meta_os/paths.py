"""Where the plugin's own files are, and what the plugin calls itself."""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_ROOT = PLUGIN_ROOT / "instance-template" / "root"
CONFIG = "meta-os.config.json"
LAUNCHER_DIR = ".meta-os"

PLUGIN_NAME = "meta-os"
# Until the preview listing the plugin is installed from the marketplace file inside its build
# repository. These two values change when it is listed in the organisation's marketplace.
MARKETPLACE = "meta-os-preview"
MARKETPLACE_SOURCE = {"source": "github", "repo": "meta-agentic/meta-os-plugin"}
# Packs are Claude Code plugins from the organisation's marketplace.
PACK_MARKETPLACE = "meta-agentic"
PACK_MARKETPLACE_SOURCE = {"source": "github", "repo": "meta-agentic/meta-disciplines"}

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def plugin_version() -> str:
    manifest = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    return manifest["version"]


def version_tuple(text: object) -> tuple[int, int, int] | None:
    """(major, minor, patch) of an `X.Y.Z` string, or None."""
    match = VERSION_RE.match(text) if isinstance(text, str) else None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3))) if match else None


def load_resolver():
    """The resolver the instance template carries: one implementation, used on both sides."""
    path = TEMPLATE_ROOT / LAUNCHER_DIR / "resolver.py"
    spec = importlib.util.spec_from_file_location("meta_os_resolver", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
