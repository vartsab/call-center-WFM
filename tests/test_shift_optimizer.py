import unittest

from src.scheduling.shift_optimizer import build_shift_options


class ShiftOptimizerTests(unittest.TestCase):
    def test_shift_options_include_break_outside_coverage(self) -> None:
        options = build_shift_options(
            interval_count=48,
            shift_intervals=16,
            break_after_intervals=8,
            start_step_intervals=2,
        )

        first = options[0]
        self.assertEqual(first.start_index, 0)
        self.assertEqual(first.end_index, 16)
        self.assertEqual(first.break_index, 8)
        self.assertNotIn(first.break_index, first.covered_indexes)
        self.assertIn(first.break_index, first.window_indexes)
        self.assertEqual(len(first.covered_indexes), 15)


if __name__ == "__main__":
    unittest.main()
