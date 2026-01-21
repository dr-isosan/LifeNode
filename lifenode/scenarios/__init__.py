"""
Scenarios Modülü

Afet senaryolarını içerir:
- Earthquake: Deprem senaryosu
- Flood: Sel senaryosu
- Infrastructure: Altyapı çöküşü
"""

from .base import Scenario, ScenarioEvent
from .earthquake import EarthquakeScenario
from .gradual_failure import GradualFailureScenario

__all__ = [
    'Scenario',
    'ScenarioEvent',
    'EarthquakeScenario',
    'GradualFailureScenario',
]
