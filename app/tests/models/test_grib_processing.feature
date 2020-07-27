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
            | filename                                             | raster_coordinate | points                                   | values                                                                       |
            | CMC_glb_RH_TGL_2_latlon.15x.15_2020071300_P000.grib2 | (10, 10)          | [[10, 10], [11, 10], [11, 11], [10, 11]] | [91.99049377441406, 91.99049377441406, 92.24049377441406, 92.24049377441406] |


    Scenario: Calculate raster coordinates
        Given an <origin> and <pixels>
        And a geographic coordinate <geographic_coordinate>
        When I calculate the raster coordinate
        Then I expect <raster_coordinate>

        Examples:
            | origin             | pixels                       | geographic_coordinate      | raster_coordinate |
            | (-180.075, 90.075) | (0.15000000000000002, -0.15) | (-120.4816667, 50.6733333) | (397, 262)        |
            | (-180.075, 90.075) | (0.15000000000000002, -0.15) | (-116.7464000, 49.4358000) | (422, 270)        |
            | (-180.075, 90.075) | (0.15000000000000002, -0.15) | (-123.2732667, 52.0837700) | (378, 253)        |


    Scenario: Calculate geographic coordinates
        Given an <origin> and <pixels>
        And a <raster_coordinate>
        When I calculate the geographic coordinate
        Then I expect <geographic_coordinate>

        Examples:
            | origin             | pixels                       | raster_coordinate | geographic_coordinate         |
            | (-180.075, 90.075) | (0.15000000000000002, -0.15) | (10, 10)          | (-178.575, 88.575)            |
            | (-180.075, 90.075) | (0.15000000000000002, -0.15) | (11, 10)          | (-178.42499999999998, 88.575) |
            | (-180.075, 90.075) | (0.15000000000000002, -0.15) | (11, 11)          | (-178.42499999999998, 88.425) |
