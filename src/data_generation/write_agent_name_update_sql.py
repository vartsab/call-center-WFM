"""Write a SQL Server script that updates synthetic agent display names."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from scheduling.christie_names import christie_agent_name


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="sql/etl/005_update_agent_names.sql")
    parser.add_argument("--agent-count", type=int, default=160)
    args = parser.parse_args()

    rows = [
        f"    ({agent_id}, {sql_literal(christie_agent_name(agent_id))})"
        for agent_id in range(1, args.agent_count + 1)
    ]
    script = (
        "SET NOCOUNT ON;\n\n"
        "UPDATE target\n"
        "SET Agent_Name = source.Agent_Name\n"
        "FROM dbo.Dim_Agent AS target\n"
        "INNER JOIN (\n"
        "VALUES\n"
        + ",\n".join(rows)
        + "\n"
        ") AS source(Agent_ID, Agent_Name)\n"
        "    ON source.Agent_ID = target.Agent_ID;\n\n"
        "SELECT COUNT(*) AS Updated_Agents\n"
        "FROM dbo.Dim_Agent\n"
        "WHERE Agent_ID BETWEEN 1 AND "
        f"{args.agent_count};\n"
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(script, encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
