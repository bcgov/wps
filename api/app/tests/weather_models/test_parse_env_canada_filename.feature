Feature: Parse Grib Filename

    Scenario: Parse a grib filename
        Given I have a grib file <filename>
        Then The projection is <projection>
        Then The variable_name is <variable_name>

        Examples:
            | filename                                                                                     | projection    | variable_name |
            | CMC_glb_TMP_TGL_2_latlon.24x.24_2020070212_P240.grib2                                        | latlon.24x.24 | TMP_TGL_2     |
            | CMC_glb_ABSV_ISBL_200_latlon.24x.24_2020070600_P000.grib2                                    | latlon.24x.24 | ABSV_ISBL_200 |
            | CMC_glb_ABSV_ISBL_200_latlon.15x.15_2020070600_P000.grib2                                    | latlon.15x.15 | ABSV_ISBL_200 |
            | CMC_glb_RH_TGL_2_latlon.15x.15_2020070712_P000.grib2                                         | latlon.15x.15 | RH_TGL_2      |
            | /somewhere_on/the_drive/CMC_glb_RH_TGL_2_latlon.15x.15_2020070712_P000.grib2                 | latlon.15x.15 | RH_TGL_2      |
            | api/app/tests/weather_models/CMC_hrdps_continental_RH_TGL_2_ps2.5km_2020100700_P007-00.grib2 | ps2.5km       | RH_TGL_2      |

