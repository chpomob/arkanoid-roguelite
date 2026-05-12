"""Bot simulation framework for automated gameplay testing.

Provides headless game execution with bot-controlled input for
balance analysis, skill ranking, and regression detection.

Main entry points:
- GameRunner: runs a single bot-driven game headlessly
- run_many(): batch runs with multiple seeds
- BaseBot: abstract bot interface
"""
from simulation.bot import BaseBot, NoisyBot, SimpleBot
from simulation.metrics import RunResult, aggregate
from simulation.runner import GameRunner, run_many

__all__ = ["BaseBot", "SimpleBot", "NoisyBot", "RunResult", "aggregate", "GameRunner", "run_many"]
