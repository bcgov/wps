import numpy as np

from cffdrs_vec.fbp import vectorized_elliptical_fire_area_30min
from cffdrs_vec.tests._glc_x_10_data import PAPER, load_rows


def test_glc_x_10_30_minute_cases_match_table_6_fire_area():
    """Compare the 30-minute area calculation with GLC-X-10 Table 6."""
    inputs, _ = PAPER.load()
    input_rows = load_rows(PAPER.input_csv)

    # The area function is fixed at 30 minutes, so select cases by Table 4's elapsed-time
    # column instead of hard-coding case IDs. This keeps the test aligned with the data.
    rows_with_30_minute_elapsed_time = [
        row for row in input_rows if row["t"].strip() and float(row["t"]) == 30.0
    ]
    # Fail clearly if a future data update removes all cases this function is intended to test.
    assert rows_with_30_minute_elapsed_time, "Table 4 should contain cases with t = 30 minutes"
    case_ids = [row["TestCase"] for row in rows_with_30_minute_elapsed_time]
    input_index_by_case = {row["TestCase"]: index for index, row in enumerate(input_rows)}
    indices = np.array([input_index_by_case[case_id] for case_id in case_ids])

    # Key the output tables by test-case ID so each selected Table 4 input is paired with its
    # own published Table 5 FMC/ISI and Table 6 area, independent of row ordering.
    primary_outputs_by_case = {
        row["TestCase"]: row for row in load_rows("glc_x_10_paper_primary_outputs.csv")
    }
    secondary_outputs_by_case = {
        row["TestCase"]: row for row in load_rows("glc_x_10_paper_secondary_outputs.csv")
    }
    expected_area_ha = np.array(
        [float(secondary_outputs_by_case[case_id]["A"]) for case_id in case_ids]
    )
    fmc = np.array([float(primary_outputs_by_case[case_id]["FMC"]) for case_id in case_ids])
    isi = np.array([float(primary_outputs_by_case[case_id]["ISI"]) for case_id in case_ids])

    # Table 4 provides FFMC but not FMC or ISI. Use their published Table 5 values rather than
    # running the full FBP calculation, keeping this test focused on the 30-minute area function.
    area_ha = vectorized_elliptical_fire_area_30min(
        fuel_type_code=inputs.fuel_type_codes[indices],
        ffmc=inputs.ffmc[indices],
        bui=inputs.bui[indices],
        ws=inputs.ws[indices],
        wd_rad=inputs.wd_rad[indices],
        gs=inputs.gs[indices],
        aspect_rad=inputs.aspect_rad[indices],
        pc=inputs.pc[indices],
        pdf=inputs.pdf[indices],
        grass_curing=inputs.cc[indices],
        gfl=inputs.gfl[indices],
        cbh=inputs.cbh[indices],
        cfl=inputs.cfl[indices],
        fmc=fmc,
        isi=isi,
    )

    # Table 6 reports area to three decimal places. The absolute tolerance allows for that
    # rounding when the expected area is near zero; the relative tolerance is 0.5%.
    np.testing.assert_allclose(area_ha, expected_area_ha, rtol=0.005, atol=0.01)
