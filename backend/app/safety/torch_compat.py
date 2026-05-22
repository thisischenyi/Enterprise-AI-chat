"""Torch JIT compatibility patch.

Patches torch.jit.script to a no-op to avoid issues with LLM Guard
on environments where torch.jit compilation is problematic.
Must be imported BEFORE any llm_guard imports.
"""

import torch


def _noop_script(obj, *args, **kwargs):
    """No-op replacement for torch.jit.script."""
    return obj


torch.jit.script = _noop_script
