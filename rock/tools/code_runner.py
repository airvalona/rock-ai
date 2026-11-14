import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from .sandbox import SandboxManager

FORBIDDEN_PATTERNS = [
    "format c:", "rm -rf /", "rmdir /s /q c:",
    ":(){ :|:& };:", "drop database", "mkfs"
]

class CodeRunner:
    """
    Executes Python scripts or shell commands securely within the sandbox boundary.
    """

    def __init__(self, sandbox: Optional[SandboxManager] = None):
        self.sandbox = sandbox or SandboxManager()

    def run_python(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Executes Python code in an isolated subprocess with current workspace as CWD.
        """
        # Quick safety check
        lower = code.lower()
        for p in FORBIDDEN_PATTERNS:
            if p in lower:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Security Error: Command blocked by safety policy ('{p}')"
                }

        temp_script = self.sandbox.root / "__temp_exec__.py"
        try:
            with open(temp_script, "w", encoding="utf-8") as f:
                f.write(code)

            res = subprocess.run(
                [sys.executable, str(temp_script)],
                cwd=str(self.sandbox.root),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout,
                "stderr": res.stderr
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": f"Execution timed out ({timeout}s)"}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e)}
        finally:
            if temp_script.exists():
                try:
                    temp_script.unlink()
                except Exception:
                    pass
