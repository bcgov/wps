"""Print HFI fire start range to prep level lookup tables from the database."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from wps_shared.db.database import get_read_session_scope
from wps_shared.db.models.hfi_calc import (
    FireCentreFireStartRange,
    FireStartLookup,
    FireStartRange,
)
from wps_shared.db.models.psu import FireCentre


@dataclass
class FireStartRangeReport:
    order: int
    id: int
    label: str
    prep_levels_by_mig: dict[int, int] = field(default_factory=dict)


@dataclass
class FireCentreReport:
    id: int
    name: str
    fire_start_ranges: dict[int, FireStartRangeReport] = field(default_factory=dict)


def get_lookup_rows(session: Session):
    return (
        session.query(
            FireCentre.id.label("fire_centre_id"),
            FireCentre.name.label("fire_centre_name"),
            FireCentreFireStartRange.order.label("range_order"),
            FireStartRange.id.label("fire_start_range_id"),
            FireStartRange.label.label("fire_start_range_label"),
            FireStartLookup.mean_intensity_group,
            FireStartLookup.prep_level,
        )
        .outerjoin(
            FireCentreFireStartRange,
            FireCentreFireStartRange.fire_centre_id == FireCentre.id,
        )
        .outerjoin(
            FireStartRange,
            FireStartRange.id == FireCentreFireStartRange.fire_start_range_id,
        )
        .outerjoin(
            FireStartLookup,
            FireStartLookup.fire_start_range_id == FireStartRange.id,
        )
        .order_by(
            FireCentre.name,
            FireCentreFireStartRange.order,
            FireStartLookup.mean_intensity_group,
        )
        .all()
    )


def build_report(rows) -> list[FireCentreReport]:
    reports_by_fire_centre_id: dict[int, FireCentreReport] = {}
    for row in rows:
        report = reports_by_fire_centre_id.setdefault(
            row.fire_centre_id,
            FireCentreReport(id=row.fire_centre_id, name=row.fire_centre_name),
        )
        if row.fire_start_range_id is None:
            continue
        fire_start_range = report.fire_start_ranges.setdefault(
            row.fire_start_range_id,
            FireStartRangeReport(
                order=row.range_order,
                id=row.fire_start_range_id,
                label=row.fire_start_range_label,
            ),
        )
        if row.mean_intensity_group is not None:
            fire_start_range.prep_levels_by_mig[row.mean_intensity_group] = row.prep_level

    return sorted(reports_by_fire_centre_id.values(), key=lambda report: report.name)


def get_mig_columns(reports: list[FireCentreReport]) -> list[int]:
    mig_columns = {
        mean_intensity_group
        for report in reports
        for fire_start_range in report.fire_start_ranges.values()
        for mean_intensity_group in fire_start_range.prep_levels_by_mig
    }
    return sorted(mig_columns)


def format_table(report: FireCentreReport, mig_columns: list[int]) -> str:
    if not report.fire_start_ranges:
        return "No fire start ranges configured."

    headers = ["Fire starts", "Range ID", *[f"MIG {column}" for column in mig_columns]]
    rows = []
    for fire_start_range in sorted(report.fire_start_ranges.values(), key=lambda item: item.order):
        rows.append(
            [
                fire_start_range.label,
                str(fire_start_range.id),
                *[
                    format_prep_level(fire_start_range.prep_levels_by_mig.get(column))
                    for column in mig_columns
                ],
            ]
        )

    column_widths = [
        max(len(str(row[index])) for row in [headers, *rows]) for index in range(len(headers))
    ]
    lines = [
        " | ".join(value.ljust(column_widths[index]) for index, value in enumerate(headers)),
        "-+-".join("-" * width for width in column_widths),
    ]
    lines.extend(
        " | ".join(value.ljust(column_widths[index]) for index, value in enumerate(row))
        for row in rows
    )
    return "\n".join(lines)


def format_prep_level(prep_level: int | None) -> str:
    if prep_level is None:
        return "--"
    return f"PL {prep_level}"


def print_report(reports: list[FireCentreReport]) -> None:
    if not reports:
        print("No fire centre fire start lookup rows were found.")
        return

    print("HFI fire starts, mean intensity groups, and prep levels")
    print("Source: database read session")
    print()
    mig_columns = get_mig_columns(reports)
    for report in reports:
        print(f"{report.name} (fire centre id {report.id})")
        print(format_table(report, mig_columns))
        print()

    print_summary(reports)


def print_summary(reports: list[FireCentreReport]) -> None:
    ranges_by_signature: dict[tuple[tuple[str, tuple[tuple[int, int], ...]], ...], list[str]] = (
        defaultdict(list)
    )
    for report in reports:
        signature = tuple(
            (
                fire_start_range.label,
                tuple(sorted(fire_start_range.prep_levels_by_mig.items())),
            )
            for fire_start_range in sorted(
                report.fire_start_ranges.values(), key=lambda item: item.order
            )
        )
        ranges_by_signature[signature].append(report.name)

    print("Equivalent configurations")
    for fire_centre_names in ranges_by_signature.values():
        print(f"- {', '.join(fire_centre_names)}")


def main() -> None:
    with get_read_session_scope() as session:
        reports = build_report(get_lookup_rows(session))
    print_report(reports)


if __name__ == "__main__":
    main()
