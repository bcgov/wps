Feature: C-Haines calculation

    Scenario: Calculate c-haines
        Then With <t_850> <t_700> and <dp_850>, I expect <c_haines>

        Examples:
            | t_850 | t_700 | dp_850 | c_haines          |
            | 27.5  | 12    | -1     | 4.416666666666667 |
            | 13.4  | 0     | 2.4    | 4.5               |

    Scenario: Calculate severity
        Given <c_haines_data>
        When generating severity
        Then We expect <mask_data>
        And We expect <severity_data>

        Examples:
            | c_haines_data   | mask_data   | severity_data |
            # c-haines below 4 has mask of 0 (i.e. we're going to ignore it), and severity == 0 (low)
            | [[0,1,2,3.9]]   | [[0,0,0,0]] | [[0,0,0,0]]   |
            # c-haines from 4 to 7.99999 has mask of 1 (i.e. we're going to show it), and severity == 1 (moderate)
            | [[4,5,6,7.9]]   | [[1,1,1,1]] | [[1,1,1,1]]   |
            | [[8,9,10,10.9]] | [[1,1,1,1]] | [[2,2,2,2]]   |
            | [[11,12]]       | [[1,1]]     | [[3,3]]       |

    Scenario: Generate c-haines data
        Given <tmp_700>, <tmp_850> and <dew_850>
        When We generate c-haines
        Then We expect <c_haines_data>

        Examples:
            | tmp_700                                                              | tmp_850                                                              | dew_850                                                               | c_haines_data         |
            | CMC_hrdps_continental_TMP_ISBL_0700_ps2.5km_2021012618_P048-00.grib2 | CMC_hrdps_continental_TMP_ISBL_0850_ps2.5km_2021012618_P048-00.grib2 | CMC_hrdps_continental_DEPR_ISBL_0850_ps2.5km_2021012618_P048-00.grib2 | c_haines_data.json.gz |

    Scenario: Make model run base url
        Then make_model_run_base_url(<model>, <model_run_start>, <forecast_hour>) == <result>

        Examples:
            | model | model_run_start | forecast_hour | result                                                               |
            | GDPS  | 00              | 120           | https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/00/120/ |
            | RDPS  | 12              | 010           | https://dd.weather.gc.ca/model_gem_regional/10km/grib2/12/010/       |
            | HRDPS | 00              | 001           | https://dd.weather.gc.ca/model_hrdps/continental/grib2/00/001/       |


    Scenario: Make model run filename
        Then make_model_run_filename(<model>, <level>, <date>, <model_run_start>, <forecast_hour>) == <result>

        Examples:
            | model | level     | date       | model_run_start | forecast_hour | result                                                             |
            | HRDPS | DEPR_ISBL | 2021012618 | 048             | 00            | CMC_hrdps_continental_DEPR_ISBL_ps2.5km_2021012618048_P00-00.grib2 |
            | RDPS  | DEPR_ISBL | 2021012618 | 0               | 12            | CMC_reg_DEPR_ISBL_ps10km_20210126180_P12.grib2                     |
            | GDPS  | DEPR_ISBL | 2021012618 | 0               | 13            | CMC_glb_DEPR_ISBL_latlon.15x.15_20210126180_P13.grib2              |

    Scenario: Make model run download urls
        Given We run make_model_run_download_urls(<model>, <now>, <model_run_hour>, <prediction_hour>)
        Then <urls> are as expected
        And <model_run_timestamp> is as expected
        And <prediction_timestamp> is as expected

        Examples:
            | model | now                        | model_run_hour | prediction_hour | urls                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | model_run_timestamp       | prediction_timestamp      |
            | HRDPS | 2021-03-11T16:46:11.600781 | 12             | 240             | {"TMP_ISBL_0700": "https://dd.weather.gc.ca/model_hrdps/continental/grib2/12/240/CMC_hrdps_continental_TMP_ISBL_0700_ps2.5km_2021031112_P240-00.grib2", "TMP_ISBL_0850": "https://dd.weather.gc.ca/model_hrdps/continental/grib2/12/240/CMC_hrdps_continental_TMP_ISBL_0850_ps2.5km_2021031112_P240-00.grib2", "DEPR_ISBL_0850": "https://dd.weather.gc.ca/model_hrdps/continental/grib2/12/240/CMC_hrdps_continental_DEPR_ISBL_0850_ps2.5km_2021031112_P240-00.grib2"} | 2021-03-11 12:00:00+00:00 | 2021-03-21 12:00:00+00:00 |
            | RDPS  | 2021-04-11T16:46:11.600781 | 12             | 240             | {"TMP_ISBL_700": "https://dd.weather.gc.ca/model_gem_regional/10km/grib2/12/240/CMC_reg_TMP_ISBL_700_ps10km_2021041112_P240.grib2", "TMP_ISBL_850": "https://dd.weather.gc.ca/model_gem_regional/10km/grib2/12/240/CMC_reg_TMP_ISBL_850_ps10km_2021041112_P240.grib2", "DEPR_ISBL_850": "https://dd.weather.gc.ca/model_gem_regional/10km/grib2/12/240/CMC_reg_DEPR_ISBL_850_ps10km_2021041112_P240.grib2"}                                                             | 2021-04-11 12:00:00+00:00 | 2021-04-21 12:00:00+00:00 |
            | GDPS  | 2021-05-11T16:46:11.600781 | 00             | 006             | {"TMP_ISBL_700": "https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/00/006/CMC_glb_TMP_ISBL_700_latlon.15x.15_2021051100_P006.grib2", "TMP_ISBL_850": "https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/00/006/CMC_glb_TMP_ISBL_850_latlon.15x.15_2021051100_P006.grib2", "DEPR_ISBL_850": "https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/00/006/CMC_glb_DEPR_ISBL_850_latlon.15x.15_2021051100_P006.grib2"}                      | 2021-05-11 00:00:00+00:00 | 2021-05-11 06:00:00+00:00 |
