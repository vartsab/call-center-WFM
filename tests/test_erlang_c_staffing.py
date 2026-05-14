import unittest

from src.workforce.erlang_c_staffing import (
    erlang_c_probability_wait,
    required_agents,
    service_level_probability,
)


class ErlangCStaffingTests(unittest.TestCase):
    def test_erlang_c_probability_wait_zero_load(self) -> None:
        self.assertEqual(erlang_c_probability_wait(0, 1), 0)

    def test_required_agents_meets_service_level_and_occupancy(self) -> None:
        agents, occupancy, service_level = required_agents(
            traffic_intensity=3.2,
            avg_handle_time_sec=520,
            target_answer_time_sec=20,
            target_service_level=0.80,
            max_occupancy=0.85,
        )

        self.assertGreaterEqual(agents, 4)
        self.assertLessEqual(occupancy, 0.85)
        self.assertGreaterEqual(service_level, 0.80)

    def test_service_level_improves_with_more_agents(self) -> None:
        lower = service_level_probability(
            traffic_intensity=2.5,
            agents=4,
            target_answer_time_sec=20,
            avg_handle_time_sec=520,
        )
        higher = service_level_probability(
            traffic_intensity=2.5,
            agents=5,
            target_answer_time_sec=20,
            avg_handle_time_sec=520,
        )

        self.assertGreater(higher, lower)


if __name__ == "__main__":
    unittest.main()
