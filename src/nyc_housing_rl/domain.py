"""Stable domain vocabulary shared by data, simulation, policies, and APIs."""

from enum import IntEnum, StrEnum


class DecisionAction(IntEnum):
    """Actions available to an inspection dispatcher.

    Enforcement outcomes are deliberately excluded: a dispatcher can prioritize or
    defer an inspection, but cannot choose whether an inspector issues a summons.
    """

    DEFER = 0
    ROUTINE = 1
    EXPEDITED = 2


class OutcomeLabel(StrEnum):
    """Research labels derived after a complaint reaches a terminal disposition."""

    ACTIONABLE = "actionable"
    NO_ACTION = "no_action"
    INACCESSIBLE = "inaccessible"
    REFERRED_OR_DUPLICATE = "referred_or_duplicate"
    UNRESOLVED = "unresolved"
