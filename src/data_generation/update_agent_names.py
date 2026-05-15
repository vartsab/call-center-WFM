"""Apply synthetic agent display names to the SQL Server agent dimension."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pyodbc

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from scheduling.christie_names import christie_agent_name


def connection_string(server: str, database: str) -> str:
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="localhost")
    parser.add_argument("--database", default="CallCenterWFM")
    parser.add_argument("--agent-count", type=int, default=160)
    args = parser.parse_args()

    connection = pyodbc.connect(connection_string(args.server, args.database))
    cursor = connection.cursor()
    updates = [
        (christie_agent_name(agent_id), agent_id)
        for agent_id in range(1, args.agent_count + 1)
    ]
    cursor.executemany(
        "UPDATE dbo.Dim_Agent SET Agent_Name = ? WHERE Agent_ID = ?;",
        updates,
    )
    connection.commit()
    cursor.close()
    connection.close()
    print(json.dumps({"updated_agents": len(updates)}, indent=2))


if __name__ == "__main__":
    main()
