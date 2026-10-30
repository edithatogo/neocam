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

    activity_basis: str = "contacts"
    contacts_per_episode: float = 1.0

    def __post_init__(self) -> None:
        """Validate the declared activity basis and contact intensity.

        Raises:
            ValueError: If the basis is unknown or the contact count is below one.
        """
        if self.activity_basis not in {"contacts", "episodes"}:
            msg = "Activity basis must be contacts or episodes"
            raise ValueError(msg)
        value = self.contacts_per_episode
        if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value) or value < 1:
            msg = "Contacts per episode must be finite numeric and at least one"
            raise ValueError(msg)

    def exposures(self, forecast: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Return paired episode and contact arrays without modifying the forecast.

        Returns:
            Paired episode and contact exposure arrays.

        Raises:
            ValueError: If the forecast is not finite, nonnegative and one-dimensional.
        """
        values = np.asarray(forecast)
        if (
            values.ndim != 1
            or not len(values)
            or values.dtype.kind not in "iuf"
            or not np.isfinite(values).all()
            or np.any(values < 0)
        ):
            msg = "Forecast requires finite nonnegative one-dimensional numeric values"
            raise ValueError(msg)
        values = values.astype(float, copy=True)
        if self.activity_basis == "contacts":
            return values / self.contacts_per_episode, values
        with np.errstate(over="ignore"):
            contacts = values * self.contacts_per_episode
        if not np.isfinite(contacts).all():
            msg = "Contact exposure overflow"
            raise ValueError(msg)
        return values, contacts
