Feature: Grib file processing

    Scenario: Extract origin and pixel information
        Given a grib file: <filename>
        When I extract the geometry
        Then I expect <origin>
        And I expect <pixels>

        Examples:
            | filename                                             | origin             | pixels                       |
            | CMC_glb_RH_TGL_2_latlon.15x.15_2020071300_P000.grib2 | (-180.075, 90.075) | (0.15000000000000002, -0.15) |

    Scenario: Extract the surrounding grid
        Given a grib file: <filename>
        And a <raster_coordinate>
        When I get the surrounding grid
        Then I expect <points>
        And I expect <values>

        Examples:
            | filename                                                        | raster_coordinate | points                                               | values                                                                           |
            | CMC_glb_RH_TGL_2_latlon.15x.15_2020071300_P000.grib2            | (10, 10)          | [[10, 10], [11, 10], [11, 11], [10, 11]]             | [91.99049377441406, 91.99049377441406, 92.24049377441406, 92.24049377441406]     |
            | CMC_hrdps_continental_RH_TGL_2_ps2.5km_2020100700_P007-00.grib2 | (694, 1262)       | [[694, 1262], [695, 1262], [695, 1263], [694, 1263]] | [44.272186279296875, 42.796443939208984, 44.272186279296875, 44.272186279296875] |


    Scenario: Calculate raster coordinates
        Given a GDAL <geotransform> and WKT projection_string <filename>
        And a geographic coordinate <geographic_coordinate>
        When I calculate the raster coordinate
        Then I expect <raster_coordinate>

        Examples:
            | geotransform                                                        | filename                                         | geographic_coordinate      | raster_coordinate |
            | (-2099127.494496938, 2500.0, 0.0, -2099388.521499629, 0.0, -2500.0) | CMC_hrdps_continental_ps2.5km_projection_wkt.txt | (-120.4816667, 50.6733333) | (472, 819)        |
            | (-2099127.494496938, 2500.0, 0.0, -2099388.521499629, 0.0, -2500.0) | CMC_hrdps_continental_ps2.5km_projection_wkt.txt | (-116.7464000, 49.4358000) | (572, 897)        |
            | (-2099127.494496938, 2500.0, 0.0, -2099388.521499629, 0.0, -2500.0) | CMC_hrdps_continental_ps2.5km_projection_wkt.txt | (-123.2732667, 52.0837700) | (409, 736)        |
            | (-180.075, 0.15000000000000002, 0.0, 90.075, 0.0, -0.15)            | CMC_glb_latlon.15x.15_projection_wkt.txt         | (-120.4816667, 50.6733333) | (397, 262)        |
            | (-180.075, 0.15000000000000002, 0.0, 90.075, 0.0, -0.15)            | CMC_glb_latlon.15x.15_projection_wkt.txt         | (-116.7464000, 49.4358000) | (422, 270)        |
            | (-180.075, 0.15000000000000002, 0.0, 90.075, 0.0, -0.15)            | CMC_glb_latlon.15x.15_projection_wkt.txt         | (-123.2732667, 52.0837700) | (378, 253)        |


    Scenario: Calculate geographic coordinates
        Given a GDAL <geotransform> and WKT projection_string <filename>
        And a <raster_coordinate>
        When I calculate the geographic coordinate
        Then I expect <geographic_coordinate>

        Examples:
            | geotransform                                                        | filename                                         | raster_coordinate | geographic_coordinate                     |
            | (-2099127.494496938, 2500.0, 0.0, -2099388.521499629, 0.0, -2500.0) | CMC_hrdps_continental_ps2.5km_projection_wkt.txt | (472, 819)        | (-120.49716122617183, 50.67953463749049)  |
            | (-2099127.494496938, 2500.0, 0.0, -2099388.521499629, 0.0, -2500.0) | CMC_hrdps_continental_ps2.5km_projection_wkt.txt | (572, 897)        | (-116.7609172273627, 49.43970905337442)   |
            | (-2099127.494496938, 2500.0, 0.0, -2099388.521499629, 0.0, -2500.0) | CMC_hrdps_continental_ps2.5km_projection_wkt.txt | (409, 736)        | (-123.28555732697632, 52.084540312301314) |
            | (-180.075, 0.15000000000000002, 0.0, 90.075, 0.0, -0.15)            | CMC_glb_latlon.15x.15_projection_wkt.txt         | (370, 330)        | (-124.57499999999999, 40.575)             |
            | (-180.075, 0.15000000000000002, 0.0, 90.075, 0.0, -0.15)            | CMC_glb_latlon.15x.15_projection_wkt.txt         | (315, 455)        | (-132.825, 21.825000000000003)            |
            | (-180.075, 0.15000000000000002, 0.0, 90.075, 0.0, -0.15)            | CMC_glb_latlon.15x.15_projection_wkt.txt         | (427, 245)        | (-116.02499999999998, 53.325)             |
