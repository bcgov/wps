from datetime import date


def generate_actual(issue_date: date, for_date: date):
    """
        Actuals can be recorded multiple times,
        e.g actual for 24 on 24, but also actual for 23 on 24.

        It is possible that _more_ stations are reporting actuals
        on "follow up" actuals captured days later.
    """

    """
    for_date remains unchanged
    issue_date will have the 5pm time attached to the date

   """


def generate_forecast(issue_date: date, for_date: date):
    """ 
        Forecasts will be generated multiple times for any given date.

        Generally 3 to 4 forecasts will be generated for a single date
        since that's what we've seen SFMS output

        e.g. issue_date: 24
                    - forecast: 25
                    - forecast: 26
                    - forecast: 27
             issue_date: 25
                    - forecast 26
                    - forecast 27
                    - forecast 28
     """
