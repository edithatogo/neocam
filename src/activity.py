"""Separate clinical episodes from specialist contacts without inventing incidence."""
from __future__ import annotations

from dataclasses import dataclass
from numbers import Real

import numpy as np


@dataclass(frozen=True)
class ActivitySpec:
    """Interpret the forecast denominator; contact intensity is a scenario input.

    Contacts are workload events, not independent transfer opportunities. A clinical
    episode is not asserted to be a unique infant over multiple admissions. The same
    intensity applies in both arms; no extra clinical success is inferred per call.
    """

    activity_basis: str = 'contacts'
    contacts_per_episode: float = 1.0

    def __post_init__(self) -> None:
        if self.activity_basis not in ('contacts', 'episodes'):
            raise ValueError('Activity basis must be contacts or episodes')
        value = self.contacts_per_episode
        if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value) or value < 1:
            raise ValueError('Contacts per episode must be finite numeric and at least one')

    def exposures(self, forecast: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Return paired episode and contact arrays without modifying the forecast."""
        values = np.asarray(forecast)
        if (values.ndim != 1 or not len(values) or values.dtype.kind not in 'iuf'
                or not np.isfinite(values).all() or np.any(values < 0)):
            raise ValueError('Forecast requires finite nonnegative one-dimensional numeric values')
        values = values.astype(float, copy=True)
        if self.activity_basis == 'contacts':
            return values / self.contacts_per_episode, values
        with np.errstate(over='ignore'):
            contacts = values * self.contacts_per_episode
        if not np.isfinite(contacts).all():
            raise ValueError('Contact exposure overflow')
        return values, contacts
