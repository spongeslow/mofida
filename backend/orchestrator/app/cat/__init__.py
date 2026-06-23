"""Computerized Adaptive Testing (CAT) engine for the Moufida adaptive intake.

Item Response Theory (2PL) + Bayesian EAP ability estimation drive a genuinely
adaptive questionnaire: each next question is the one that maximises Fisher
information about the founder's latent maturity, instead of a fixed/branching
script. See ``docs/research/computerized-adaptive-testing.md``.
"""
from . import irt, session

__all__ = ["irt", "session"]
