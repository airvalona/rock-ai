import pytest
from pathlib import Path
from rock.tools.sandbox import SandboxManager

def test_sandbox_write_and_read(tmp_path: Path):
    sandbox = SandboxManager(workspace_root=tmp_path)
    res = sandbox.write_file("hello.txt", "Hello rock.ai!")
    assert "written successfully" in res

    content = sandbox.read_file("hello.txt")
    assert content == "Hello rock.ai!"

def test_sandbox_path_traversal_prevention(tmp_path: Path):
    sandbox = SandboxManager(workspace_root=tmp_path)
    with pytest.raises(PermissionError):
        sandbox.write_file("../escape.txt", "Should fail")
