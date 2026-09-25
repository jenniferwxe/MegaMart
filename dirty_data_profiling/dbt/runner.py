# dirty_data_profiling/dbt/runner.py
from __future__ import annotations

import subprocess
from pathlib import Path

DBT_PROJECT = Path("dbt")


class DBTRunner:
    """
    Executes dbt from the profiling pipeline.
    """

    def _execute(self, command: list[str]):

        print()

        print("=" * 70)

        if command[1] == "run":
            print("Running dbt run")
        elif command[1] == "test":
            print("Running dbt test")

        print("=" * 70)

        print("Running command:")
        print(" ".join(command))

        result = subprocess.run(
            command,
            cwd=DBT_PROJECT,
            capture_output=True,
            text=True,
        )

        print(result.stdout)

        if result.returncode != 0:

            print(f"dbt {command[1]} completed with failures.")

            print(result.stderr)

        return result

    def run_test(
        self,
        *,
        target: str,
        select: str | None = None,
        store_failures: bool = True,
    ):

        #
        # dbt run
        #

        run_command = [
            "dbt",
            "run",
            "--target",
            target,
            "--profiles-dir",
            "../dbt_profiles",
        ]

        if select:
            run_command.extend(
                [
                    "--select",
                    select,
                ]
            )

        run_result = self._execute(run_command)

        if run_result.returncode != 0:
            return run_result, None

        #
        # dbt test
        #

        test_command = [
            "dbt",
            "test",
            "--target",
            target,
            "--profiles-dir",
            "../dbt_profiles",
        ]

        if select:
            test_command.extend(
                [
                    "--select",
                    select,
                ]
            )

        if store_failures:
            test_command.append("--store-failures")

        test_result = self._execute(test_command)

        return run_result, test_result
