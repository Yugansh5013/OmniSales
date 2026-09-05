"""OmniSales E2E Test Suite Shim — delegates to tests/e2e/test_e2e.py."""
import runpy
import os
import sys

target = os.path.join(os.path.dirname(__file__), "e2e", "test_e2e.py")
runpy.run_path(target, run_name="__main__")
