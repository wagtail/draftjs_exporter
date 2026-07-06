"""Root pytest configuration: Hypothesis profiles for property-based tests.

See docs/CONTRIBUTING.md#property-based-tests for how these are used.
"""

import os

from hypothesis import HealthCheck, settings

settings.register_profile("default", max_examples=100)
settings.register_profile(
    "ci",
    max_examples=500,
    suppress_health_check=[HealthCheck.too_slow],
)

settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))
