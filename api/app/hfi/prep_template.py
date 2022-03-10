"""Prep cycle pdf template"""
PREP_TEMPLATE_HTML = """
'<!DOCTYPE html>
<html lang="en">
<head>
    <title>Prep Cycle Template</title>
</head>

<style>
    td {
        border-top: 2px solid black;
        border-bottom: black 2px solid;
        padding: 0;
        border-collapse: collapse;
        min-width: 35px;
        max-width: 200px;
        text-align: center;
    }
    th{
        min-width: 35px;
        max-width: 200px;
        text-align: center; 
    }

    table {
            border-collapse:collapse;
            border:2px solid #000000;
        }

    .leftBorder{
        border-left: 1px solid black;
        border-collapse: collapse;
    }

    .rightBorder{
        border-right: 1px solid black;
        border-collapse: collapse;
    }

    .boldRightBorder{
        border-right: 2px solid black;
        border-collapse: collapse;
    }

    .boldLeftBorder{
        border-left: 2px solid black;
        border-collapse: collapse;
    }

    .planningArea {
        background-color: cornflowerblue;
        border-bottom: black 2px solid;
        border-collapse: collapse;
        height: 20px;
        padding: 0;
    }
    .station{
        border-bottom: black 2px solid;
        border-collapse: collapse;
        padding: 0;
    }
</style>

<body>
    <table>
        <tr class="leftBorder">
            <td></td>
            <td></td>
            {% for day in prepDays %}
                <td></td>
                <td class="boldRightBorder"></td>
                <td></td>
                <td></td>
                <th>{{ day }}</th>
            {% endfor %}
            <td></td>
            <td></td>
            <td class="boldLeftBorder"></td>
            <th>Prep</th>
        </tr>
        <tr>
            <td></td>
            <td>Elev</td>
            <td>Fuel Type</td>
            <td>Grass Cure</td>
            {% for day in prepDays %}
                <td class="boldLeftBorder">ROS</td>
                <td>HFI</td>
                <td>M/FIG</td>
                <td>Fire Starts</td>
                <td class="boldRightBorder">Prep</td>
            {% endfor %}
            <td>Highest FIG</td>
            <td>Prep Level</td>
        </tr>
        {% for area in planningAreas %}
            <tr class="planningArea leftBorder rightBorder">
                <td>{{area['planningAreaName']}}</td>
                <td></td>
                <td></td>
                <td class="boldRightBorder"></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td class="boldRightBorder"></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td class="boldRightBorder"></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td class="boldRightBorder"></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td class="boldRightBorder"></td>
                <td class="boldRightBorder"></td>
                <td></td>
            </tr>
            {% for code, dailies in area['dailies'].items() %}
            <tr class="station">
                <td class="rightBorder">{{code}}</td>
                <td class="rightBorder">X</td>
                <td class="rightBorder">X</td>
                <td class="rightBorder">X</td>
                {% for daily in dailies %}
                    <td class="boldLeftBorder rightBorder">{{daily['rate_of_spread'] | round(1)}}</td>
                    <td class="leftBorder rightBorder">{{daily['hfi'] | round(1)}}</td>
                    <td class="leftBorder rightBorder">{{daily['intensity_group']}}</td>
                    <td class="leftBorder rightBorder">X</td>
                    <td class="leftBorder boldRightBorder">X</td>
                {% endfor %}
                <td class="boldRightBorder">X</td>
                <td>:D</td>
            </tr>
            {% endfor %}
        {% endfor %}

    </table>
    </body>
</html>
"""


def str_prep_template(template_name: str):    # pylint: disable=unused-argument
    """ Returns the only (currently) template, arg above will be used for switching """
    return PREP_TEMPLATE_HTML
