"""Reusable CP-SAT helpers for early, compact schedule generation.

Hard scheduling rules must be added to the model before these helpers are used.
The objective only ranks placements that are already legal; it cannot override a
teacher, section, room, availability, duration, or fixed-position constraint.
"""

from dataclasses import dataclass


MAX_SAFE_OBJECTIVE = (1 << 62) - 1


@dataclass(frozen=True)
class PlacementChoice:
    """One legal placement variable and its zero-based chronological ranks."""

    variable: object
    day_rank: int
    start_rank: int


@dataclass(frozen=True)
class CompactObjectiveWeights:
    """Weights used by the strict day -> time -> gap objective."""

    day_thresholds: tuple
    time_thresholds: tuple
    maximum_cost: int

    @staticmethod
    def penalty(rank, thresholds):
        return sum(thresholds[1 : rank + 1])

    def day_penalty(self, day_rank):
        return self.penalty(day_rank, self.day_thresholds)

    def time_penalty(self, start_rank):
        return self.penalty(start_rank, self.time_thresholds)


def _strict_threshold_weights(level_count, assignment_count, lower_tier_bound):
    """Build weights where improving one higher tier beats every lower tier."""

    if level_count < 1:
        raise ValueError("level_count must be positive")
    thresholds = [0] * level_count
    maximum_cost = max(0, int(lower_tier_bound))

    for threshold in range(level_count - 1, 0, -1):
        thresholds[threshold] = maximum_cost + 1
        maximum_cost += assignment_count * thresholds[threshold]

    return tuple(thresholds), maximum_cost


def build_compact_objective_weights(
    assignment_count,
    day_count,
    start_rank_count,
    maximum_gap_penalty,
):
    """Return overflow-safe weights for day, time, then gap minimization.

    Day thresholds make the objective truly chronological: maximizing Day 1
    occupancy is more important than every possible Day 2-4/time/gap change;
    after that, Day 2 is maximized, then Day 3. Within those fixed day counts,
    total start-slot rank is minimized before any vacancy-gap penalty.
    """

    assignment_count = int(assignment_count)
    if assignment_count < 1:
        raise ValueError("assignment_count must be positive")

    time_unit = max(0, int(maximum_gap_penalty)) + 1
    time_thresholds = (0,) + (time_unit,) * max(0, start_rank_count - 1)
    time_and_gap_bound = (
        max(0, int(maximum_gap_penalty))
        + assignment_count * max(0, start_rank_count - 1) * time_unit
    )
    day_thresholds, maximum_cost = _strict_threshold_weights(
        day_count,
        assignment_count,
        time_and_gap_bound,
    )
    if maximum_cost > MAX_SAFE_OBJECTIVE:
        raise OverflowError(
            f"Compact objective can reach {maximum_cost}, exceeding the safe CP-SAT limit"
        )

    return CompactObjectiveWeights(
        day_thresholds=day_thresholds,
        time_thresholds=time_thresholds,
        maximum_cost=maximum_cost,
    )


def add_vacancy_gap_indicators(model, occupancy_by_resource_day, name_prefix):
    """Create penalties for an empty earlier slot followed by an occupied slot.

    ``occupancy_by_resource_day`` maps a resource/day key to a chronological
    list of Boolean occupancy variables. Resources may be sections, teachers,
    or rooms. Forced gaps remain legal; they are merely less desirable than an
    otherwise-equivalent compact placement.
    """

    gap_variables = []
    gap_index = 0
    for occupancies in occupancy_by_resource_day.values():
        for earlier_index, earlier in enumerate(occupancies[:-1]):
            for later in occupancies[earlier_index + 1 :]:
                gap = model.NewBoolVar(f"{name_prefix}_gap_{gap_index}")
                model.Add(gap >= later - earlier)
                gap_variables.append(gap)
                gap_index += 1
    return gap_variables


def minimize_early_compact_schedule(model, placements, assignment_count, gap_variables=()):
    """Apply strict earlier-day, earlier-time, then fewer-gap optimization."""

    placements = list(placements)
    gap_variables = list(gap_variables)
    if not placements:
        raise ValueError("At least one placement choice is required")

    day_count = max(choice.day_rank for choice in placements) + 1
    start_rank_count = max(choice.start_rank for choice in placements) + 1
    weights = build_compact_objective_weights(
        assignment_count=assignment_count,
        day_count=day_count,
        start_rank_count=start_rank_count,
        maximum_gap_penalty=len(gap_variables),
    )

    objective_terms = list(gap_variables)
    for choice in placements:
        cost = weights.day_penalty(choice.day_rank) + weights.time_penalty(choice.start_rank)
        if cost:
            objective_terms.append(choice.variable * cost)

    model.Minimize(sum(objective_terms))
    return weights
