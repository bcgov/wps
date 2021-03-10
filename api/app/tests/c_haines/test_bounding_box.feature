Feature: Bounding Box Checker

    Scenario: Check bounding box
        Given a <grib_file>
        Then We expect the coordinate <x_coordinate> <y_coordinate> to be <is_inside>

        Examples:
            | grib_file                                                             | x_coordinate | y_coordinate | is_inside |
            | CMC_hrdps_continental_DEPR_ISBL_0850_ps2.5km_2021012618_P048-00.grib2 | 1            | 1            | False     |
            | CMC_hrdps_continental_DEPR_ISBL_0850_ps2.5km_2021012618_P048-00.grib2 | 2            | 2            | False     |
            | CMC_hrdps_continental_DEPR_ISBL_0850_ps2.5km_2021012618_P048-00.grib2 | 315          | 0            | True      |
