from pathlib import Path
from typing import List, Dict, Any, Optional
from ..core.config import RockConfig, WORKSPACE_DIR

class SandboxManager:
    """
    Manages sandboxed file operations strictly within ~/.rock/workspace
    preventing path traversal attacks.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self.root = (workspace_root or WORKSPACE_DIR).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve_safe(self, rel_path: str) -> Path:
        target = (self.root / rel_path).resolve()
        if not str(target).startswith(str(self.root)):
            raise PermissionError(f"Access denied: path '{rel_path}' escapes sandbox boundary.")
        return target

    def write_file(self, rel_path: str, content: str) -> str:
        target = self._resolve_safe(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{rel_path}' written successfully ({len(content)} chars)."

    def read_file(self, rel_path: str) -> str:
        target = self._resolve_safe(rel_path)
        if not target.exists():
            return f"Error: File '{rel_path}' does not exist."
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def list_files(self, sub_dir: str = ".") -> List[str]:
        target = self._resolve_safe(sub_dir)
        if not target.exists():
            return []
        items = []
        for p in target.rglob("*"):
            rel = p.relative_to(self.root)
            items.append(str(rel))
        return items
