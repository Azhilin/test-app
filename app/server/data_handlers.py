"""Jira data preview handler mixin — /api/data-preview."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from atlassian import Jira

from app.core import config, jira_client

logger = logging.getLogger(__name__)


class DataHandlerMixin:
    """Handler for previewing what data will be fetched before generating a report."""

    def _handle_data_preview(self) -> None:  # noqa: ANN001
        """
        GET /api/data-preview?board_id=<id>&sprint_count=<n>&filter=<slug>&project_type=SCRUM|KANBAN

        Returns a preview of what data will be fetched:
        - For SCRUM: sprint list
        - For KANBAN: time period list (weeks)
        """
        query_params = self._query_params()  # type: ignore[attr-defined]
        board_id_param = (query_params.get("board_id") or [""])[0].strip()
        sprint_count_param = (query_params.get("sprint_count") or ["10"])[0].strip()
        filter_slug = (query_params.get("filter") or [""])[0].strip()
        project_type_param = (query_params.get("project_type") or [""])[0].strip().upper()

        # Parse sprint count
        try:
            sprint_count = int(sprint_count_param) if sprint_count_param else 10
        except ValueError:
            sprint_count = 10

        # Parse board ID (optional — will auto-detect if not provided)
        board_id: int | None = None
        if board_id_param.isdigit():
            board_id = int(board_id_param)

        try:
            jira_url, jira_email, jira_token = self._read_env_credentials()  # type: ignore[attr-defined]
            if not (jira_url and jira_email and jira_token):
                self._send_json(400, {"ok": False, "error": "Jira credentials not configured"})  # type: ignore[attr-defined]
                return

            jira = Jira(
                url=jira_url,
                username=jira_email,
                password=jira_token,
                verify_ssl=config.JIRA_SSL_CERT,
                timeout=55,
            )

            # Resolve board ID if not provided
            if board_id is None:
                board_id = jira_client.get_board_id(jira)

            # Get board name
            board_info = jira.get_agile_board(board_id)
            board_name = (board_info or {}).get("name", f"Board {board_id}")

            # Determine project type (from param, or from filter if filter slug provided, or config default)
            if not project_type_param:
                # Try to infer from filter if a filter slug is provided
                if filter_slug:
                    # We could load the filter from config, but for now just use config default
                    project_type_param = config.PROJECT_TYPE
                else:
                    project_type_param = config.PROJECT_TYPE

            if project_type_param not in ("SCRUM", "KANBAN"):
                project_type_param = config.PROJECT_TYPE

            if project_type_param == "KANBAN":
                # Generate synthetic time periods (weeks)
                periods = []
                today = datetime.utcnow().date()
                for week_offset in range(sprint_count):
                    week_end = today - timedelta(days=week_offset * 7)
                    week_start = week_end - timedelta(days=6)
                    week_num = week_start.isocalendar()[1]
                    week_year = week_start.isocalendar()[0]
                    period_label = f"{week_year}-W{week_num:02d}"
                    periods.append(
                        {
                            "id": f"week-{period_label}",
                            "name": period_label,
                            "state": "closed",
                            "startDate": str(week_start),
                            "endDate": str(week_end),
                        }
                    )
                self._send_json(  # type: ignore[attr-defined]
                    200,
                    {
                        "ok": True,
                        "project_type": "KANBAN",
                        "board_name": board_name,
                        "board_id": board_id,
                        "periods": periods,
                        "total_periods": len(periods),
                    },
                )
            else:
                # SCRUM: fetch sprint list
                sprints = jira_client.get_sprints(jira, board_id)
                self._send_json(  # type: ignore[attr-defined]
                    200,
                    {
                        "ok": True,
                        "project_type": "SCRUM",
                        "board_name": board_name,
                        "board_id": board_id,
                        "sprints": sprints,
                        "total_sprints": len(sprints),
                    },
                )

        except Exception as e:  # noqa: BLE001
            logger.exception("Error in _handle_data_preview: %s", str(e))
            self._send_json(  # type: ignore[attr-defined]
                500,
                {
                    "ok": False,
                    "error": f"Failed to fetch data preview: {jira_client._sanitise_error(str(e))}",
                },
            )
