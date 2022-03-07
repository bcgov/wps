"""String representations of templates for in memory loading"""


DAILY_TEMPLATE_HTML = """
<!DOCTYPE html>
<html lang="en">
<style type="text/css" media="screen">
        .first-cell{
            width: 80px;
            padding: 5px;
            border:1px solid #000000;
        }
        .planning-area-header {
            max-width: 80px;
        }
        .table {
            border-collapse:collapse;
            border:1px solid #000000;
        }
        
        .table-data {
            padding: 5px;
            border:1px solid #000000;
            width: 80px;
        }

        .table-header {
            width: 80px;
            padding: 5px;
            border:1px solid #000000;
        }
        .new-page {
            page-break-before: always;
        }
</style>
<head>
    <title>HFI Daily</title>
</head>
<body>
            {% for date, planning_areas in daily_pdf_data_by_date.items() %}
            <h1>BC Wildfire Services - HFI Calculator</h1>
            <h2>Fire Centre ID: {{fire_centre_name}} - Date: {{date}}</h2>
            <table class="table">
                <tr>
                    <th class="table-header" colspan="25">{{date}}</th>
                </tr>
                <tr>
                    <th class="planning-area-header">Planning Area/Station</th>
                    <th class="table-header">Elev</th>
                    <th class="table-header">Fuel Type</th>
                    <th class="table-header">Grass Cure</th>
                    <th class="table-header">Status</th>
                    <th class="table-header">Temp</th>
                    <th class="table-header">RH</th>
                    <th class="table-header">Wind Dir</th>
                    <th class="table-header">Wind Spd</th>
                    <th class="table-header">Precip</th>
                    <th class="table-header">FFMC</th>
                    <th class="table-header">DMC</th>
                    <th class="table-header">DC</th>
                    <th class="table-header">ISI</th>
                    <th class="table-header">BUI</th>
                    <th class="table-header">FWI</th>
                    <th class="table-header">DGR CL</th>
                    <th class="table-header">ROS</th>
                    <th class="table-header">HFI</th>
                    <th class="table-header">60 min Fire Size</th>
                    <th class="table-header">Fire Type</th>
                    <th class="table-header">M/FIG</th>
                    <th class="table-header">Fire Starts</th>
                    <th class="table-header">Prep Level</th>
                </tr>
                <tr colspan="22">
                    {% for planning_area_data in planning_areas %}
                        <td class="table-data" colspan="21">{{planning_area_data['planning_area_name']}}</td>
                        <td class="table-data" rowspan="{{planning_area_data['dailies']|length + 1}}">TODO</td>
                        <td class="table-data" rowspan="{{planning_area_data['dailies']|length + 1}}">{{planning_area_data['fire_starts']}}</td>
                        <td class="table-data" rowspan="{{planning_area_data['dailies']|length + 1}}">{{planning_area_data['mean_prep_level']}}</td>
                            {% for d in planning_area_data['dailies']  %}
                                <tr>
                                    <td class="first-cell">{{d['station_props']['name']}}</td>
                                    <td class="table-data">{{d['station_props']['elevation']}}</td>
                                    <td class="table-data">{{d['station_props']['fuel_type']['abbrev']}}</td>  
                                    <td class="table-data">{{d['grass_cure_percentage']}}</td>
                                    <td class="table-data">{{d['status']}}</td>
                                    <td class="table-data">{{d['temperature']}}</td>   
                                    <td class="table-data">{{d['relative_humidity']| round(1)}}</td>
                                    <td class="table-data">{{d['wind_direction']}}</td> 
                                    <td class="table-data">{{d['wind_speed']| round(1)}}</td>   
                                    <td class="table-data">{{d['precipitation']| round(1)}}</td> 
                                    <td class="table-data">{{d['ffmc']| round(1)}}</td> 
                                    <td class="table-data">{{d['dmc']| round(1)}}</td> 
                                    <td class="table-data">{{d['dc']| round(1)}}</td> 
                                    <td class="table-data">{{d['isi']| round(1)}}</td> 
                                    <td class="table-data">{{d['bui']| round(1)}}</td> 
                                    <td class="table-data">{{d['fwi']| round(1)}}</td> 
                                    <td class="table-data">{{d['danger_class']}}</td> 
                                    <td class="table-data">{{d['rate_of_spread'] | round(1)}}</td> 
                                    <td class="table-data">{{d['hfi']| round(1)}}</td> 
                                    <td class="table-data">{{d['sixty_minute_fire_size']| round(1)}}</td> 
                                    <td class="table-data">{{d['fire_type']}}</td> 
                                </tr>
                            {% endfor %}
                    {% endfor %}
                </tr>
            </table>
        <p class="new-page"></p>
        {% endfor %}
    </body>
</html>
"""


def str_daily_template(template_name: str):    # pylint: disable=unused-argument
    """ Returns the only (currently) template, arg above will be used for switching """
    return DAILY_TEMPLATE_HTML
