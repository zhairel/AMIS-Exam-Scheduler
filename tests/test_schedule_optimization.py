import unittest
from collections import defaultdict

from ortools.sat.python import cp_model

from schedule_optimization import (
    MAX_SAFE_OBJECTIVE,
    PlacementChoice,
    add_vacancy_gap_indicators,
    build_compact_objective_weights,
    minimize_early_compact_schedule,
)


class CompactScheduleObjectiveTests(unittest.TestCase):
    def solve_single_section(self, item_count, fixed=None, day_count=4, slot_count=3):
        model = cp_model.CpModel()
        choices = {}
        placements = []
        occupancy = defaultdict(list)

        for item in range(item_count):
            item_choices = []
            for day in range(day_count):
                for slot in range(slot_count):
                    variable = model.NewBoolVar(f"item_{item}_{day}_{slot}")
                    choices[item, day, slot] = variable
                    item_choices.append(variable)
                    placements.append(PlacementChoice(variable, day, slot))
            model.AddExactlyOne(item_choices)

        for day in range(day_count):
            for slot in range(slot_count):
                variables = [choices[item, day, slot] for item in range(item_count)]
                model.AddAtMostOne(variables)
                occupied = model.NewBoolVar(f"section_{day}_{slot}_occupied")
                model.Add(occupied == sum(variables))
                occupancy[('section', day)].append(occupied)

        for item, day, slot in fixed or []:
            model.Add(choices[item, day, slot] == 1)

        gaps = add_vacancy_gap_indicators(model, occupancy, "section")
        minimize_early_compact_schedule(model, placements, item_count, gaps)

        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = 0
        status = solver.Solve(model)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))

        result = []
        for item in range(item_count):
            for day in range(day_count):
                for slot in range(slot_count):
                    if solver.Value(choices[item, day, slot]):
                        result.append((item, day, slot))
        return result

    def test_fills_earlier_days_before_later_days(self):
        result = self.solve_single_section(7)
        by_day = [sorted(slot for _, assigned_day, slot in result if assigned_day == day) for day in range(4)]
        self.assertEqual(by_day, [[0, 1, 2], [0, 1, 2], [0], []])

    def test_fixed_assignment_is_never_moved(self):
        result = self.solve_single_section(2, fixed=[(0, 2, 2)])
        self.assertIn((0, 2, 2), result)
        self.assertIn((1, 0, 0), result)

    def test_realistic_weights_fit_cp_sat_integer_range(self):
        weights = build_compact_objective_weights(
            assignment_count=586,
            day_count=4,
            start_rank_count=4,
            maximum_gap_penalty=12000,
        )
        self.assertLess(weights.maximum_cost, MAX_SAFE_OBJECTIVE)
        self.assertGreater(
            weights.day_thresholds[1],
            weights.day_thresholds[2] * 586,
        )
        self.assertGreater(weights.time_thresholds[1], 12000)


if __name__ == '__main__':
    unittest.main()
