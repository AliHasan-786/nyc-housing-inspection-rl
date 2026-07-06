from nyc_housing_rl.domain import DecisionAction, OutcomeLabel


def test_dispatch_actions_are_stable_integer_codes() -> None:
    assert list(DecisionAction) == [
        DecisionAction.DEFER,
        DecisionAction.ROUTINE,
        DecisionAction.EXPEDITED,
    ]
    assert DecisionAction.EXPEDITED.value == 2


def test_unresolved_outcomes_are_not_negative_labels() -> None:
    assert OutcomeLabel.UNRESOLVED != OutcomeLabel.NO_ACTION
