"""String representations of templates for in memory loading"""
import os

CSS_PATH = os.path.join(os.path.dirname(__file__), "style.css")

DAILY_TEMPLATE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>HFI Daily</title>
</head>
<body>
            {% for date, planning_areas in daily_pdf_data_by_date.items() %}
            <h1>BC Wildfire Services - HFI Calculator</h1>
            <h2>Fire Centre ID: {{fire_centre_name}} - Date: {{date}}</h2>
            <table>
                <tr>
                    <th colspan="25">{{date}}</th>
                </tr>
                <tr>
                    <th>Planning Area/Station</th>
                    <th>Elev</th>
                    <th>Fuel Type</th>
                    <th>Grass Cure</th>
                    <th>Status</th>
                    <th>Temp</th>
                    <th>RH</th>
                    <th>Wind Dir</th>
                    <th>Wind Spd</th>
                    <th>Precip</th>
                    <th>FFMC</th>
                    <th>DMC</th>
                    <th>DC</th>
                    <th>ISI</th>
                    <th>BUI</th>
                    <th>FWI</th>
                    <th>DGR CL</th>
                    <th>ROS</th>
                    <th>HFI</th>
                    <th>60 min Fire Size</th>
                    <th>Fire Type</th>
                    <th>M/FIG</th>
                    <th>Fire Starts</th>
                    <th>Prep Level</th>
                </tr>
                <tr colspan="22">
                    {% for planning_area_data in planning_areas %}
                        <td colspan="21">{{planning_area_data['planning_area_name']}}</td>
                        <td>{{planning_area_data['highest_daily_intensity_group']}}</td>
                        <td rowspan="{{planning_area_data['dailies']|length + 1}}">{{planning_area_data['fire_starts']}}</td>
                        <td rowspan="{{planning_area_data['dailies']|length + 1}}">{{planning_area_data['mean_prep_level']}}</td>
                            {% for d in planning_area_data['dailies']  %}
                                <tr>
                                    <td>{{d['station_props']['name']}}</td>
                                    <td>{{d['station_props']['elevation']}}</td>
                                    <td>{{d['station_props']['fuel_type']['abbrev']}}</td>  
                                    <td>{{d['grass_cure_percentage']}}</td>
                                    <td>{{d['status']}}</td>
                                    <td>{{d['temperature']}}</td>   
                                    <td>{{d['relative_humidity']| round(1)}}</td>
                                    <td>{{d['wind_direction']}}</td> 
                                    <td>{{d['wind_speed']| round(1)}}</td>   
                                    <td>{{d['precipitation']| round(1)}}</td> 
                                    <td>{{d['ffmc']| round(1)}}</td> 
                                    <td>{{d['dmc']| round(1)}}</td> 
                                    <td>{{d['dc']| round(1)}}</td> 
                                    <td>{{d['isi']| round(1)}}</td> 
                                    <td>{{d['bui']| round(1)}}</td> 
                                    <td>{{d['fwi']| round(1)}}</td> 
                                    <td>{{d['danger_class']}}</td> 
                                    <td>{{d['rate_of_spread'] | round(1)}}</td> 
                                    <td>{{d['hfi']| round(1)}}</td> 
                                    <td>{{d['sixty_minute_fire_size']| round(1)}}</td> 
                                    <td>{{d['fire_type']}}</td> 
                                    <td>{{d['intensity_group']}}</td>
                                </tr>
                            {% endfor %}
                    {% endfor %}
                </tr>
            </table>
        <p></p>
        {% endfor %}
    </body>
</html>
"""


def str_daily_template(template_name: str):    # pylint: disable=unused-argument
    """ Returns the only (currently) template, arg above will be used for switching """
    return DAILY_TEMPLATE_HTML
