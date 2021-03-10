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
