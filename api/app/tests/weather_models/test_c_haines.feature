Feature: C-Haines calculation

    Scenario: Calculate c-haines
        # Given <t_850> <t_700> and <dp_850>
        # When I calculate c_haines
        Then With <t_850> <t_700> and <dp_850>, I expect <c_haines>

        Examples:
            | t_850 | t_700 | dp_850 | c_haines          |
            | 27.5  | 12    | -1     | 12.5              |
            | 13.4  | 0     | 2.4    | 7.366666666666667 |
