"""
Bank Statement Separator

AI-powered tool for separating multi-statement PDF files using LangChain and LangGraph.
"""

try:
    from importlib.metadata import version
except ImportError:
    # Fallback for Python < 3.8
    from importlib_metadata import version

try:
    __version__ = version("bank-statement-separator")
except Exception:
    # Fallback version if package metadata is not available
    __version__ = "unknown"

__author__ = "Bank Statement Separator Team"
