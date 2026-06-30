"""
J.A.R.V.I.S Proactive Engine Interface.

Background service that periodically checks triggers and sends
notifications to keep the user informed and on track.
"""

from interfaces.proactive.proactive_engine import ProactiveEngine

__all__ = ["ProactiveEngine"]
