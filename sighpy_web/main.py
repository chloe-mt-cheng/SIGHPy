from flask import Flask, request, render_template
from sqlalchemy import create_engine
from flask_googlemaps import GoogleMaps, Map
from geopy.geocoders import Nominatim
from datetime import datetime
from calculations import distance_km_func, rough_area, tuple_to_datetime, two_item_mean, marker_maker, marker_chart
from operator import add
import matplotlib.pyplot as plt


app = Flask(__name__)
app.config['GOOGLEMAPS_KEY'] = "GMAPSAPIKEY"

engine = create_engine('mysql+pymysql://USER:PASS@127.0.0.1/sighpy')
GoogleMaps(app)


def engine_txn(dbengine, query):
    with dbengine.begin() as connection:
        cxn_trans = connection.execute(query)
        trans_data = cxn_trans.fetchall()
        return trans_data


@app.route("/")
def home():
    home_query_string = """SELECT address, latitude, longitude
    FROM dc_site_location
    ORDER BY RAND() LIMIT 15"""
    co2_query_form = """SELECT val_average, date_dt FROM
    jaxa_l3_co2_daily_box
    WHERE {lat} BETWEEN down_left_lat AND up_left_lat
    AND {long} BETWEEN up_left_long and up_right_long
    AND date_dt BETWEEN '{date1}' AND '{date2}'"""
    home_data = engine_txn(engine, home_query_string)
    home_markers = [data[1:3] for data in home_data]
    start_date = "2019-04-01"
    end_date = "2020-04-01"
    home_data = engine_txn(engine, home_query_string)
    home_markers = [data[1:3] for data in home_data]
    home_addresses = [data[0] for data in home_data]
    home_info_markers = []
    info_marker_form = "<p style='font-size:22'>CO2 Emissions for Data Center at {dc}:</p>"
    for mark, address in zip(home_markers, home_addresses):
        mark_lat = mark[0]
        mark_long = mark[1]
        print(address, mark)
        address_html_str = info_marker_form.format(dc=address)
        query_string = co2_query_form.format(lat=mark_lat, long=mark_long,
                                             date1=start_date, date2=end_date)
        query_data = engine_txn(engine, query_string)
        plot_html_str = marker_chart(query_data)
        home_info_markers.append(address_html_str+plot_html_str)
    home_marker_param = list(map(marker_maker, home_markers, home_info_markers))
    homemap = Map(
        identifier="homemap",
        varname="homemap",
        lat=40,
        lng=-65,
        zoom=4,
        markers=home_marker_param,
        style="aligh:center;height:650px;width:100%;margin:0;")
    return render_template("home.html", homemap=homemap)


@app.route("/", methods=['POST'])
def home_post():
    home_query_string = """SELECT address, latitude, longitude
    FROM dc_site_location
    ORDER BY RAND() LIMIT 15"""
    co2_query_form = """SELECT val_average, date_dt FROM
    jaxa_l3_co2_daily_box
    WHERE {lat} BETWEEN down_left_lat AND up_left_lat
    AND {long} BETWEEN up_left_long and up_right_long
    AND date_dt BETWEEN '{date1}' AND '{date2}'"""
    # geolocator = Nominatim(user_agent="sighpy_app")
    # user_location = request.form['location']
    # start_date = request.form['date_dt1']
    # end_date = request.form['date_dt2']
    # location_resp = geolocator.geocode(user_location)
    # resp_lat = location_resp.latitude
    # resp_long = location_resp.longitude
    start_date = "2019-09-01"
    end_date = "2020-04-01"
    home_data = engine_txn(engine, home_query_string)
    home_markers = [data[1:3] for data in home_data]
    for mark in home_markers:
        mark_lat = mark[0]
        mark_long = mark[1]
        query_string = co2_query_form.format(lat=mark_lat, long=mark_long,
                                             date1=start_date, date2=end_date)
        query_data = engine_txn(engine, query_string)
        marker_chart(query_data)
    home_info_markers = [data[0] for data in home_data]
    home_marker_param = list(map(marker_maker, home_markers, home_info_markers))
    homemap = Map(
        identifier="homemap",
        varname="homemap",
        lat=40,
        lng=-65,
        zoom=4,
        markers=home_marker_param,
        style="aligh:center;height:650px;width:100%;margin:0;")
    return render_template("home.html", homemap=homemap)


@app.route("/data")
def data():
    return render_template("data.html", data=None)


@app.route("/data", methods=['POST'])
def data_post():
    geolocator = Nominatim(user_agent="sighpy_app")
    location = request.form['location']
    location_resp = geolocator.geocode(location)
    if location_resp is None:
        return render_template("data.html", data=0)
    resp_lat = location_resp.latitude
    resp_long = location_resp.longitude
    date_start = request.form['date_dt1']
    date_end = request.form['date_dt2']
    usage_hours = float(request.form['use_hours'])
    usage_ratio = float(usage_hours/24.0)
    time_series_bool = 'time_series_bool' in request.form
    radius = float(request.form['radius'])
    if date_start == '' or date_end == '' or radius == '':
        return render_template("data.html", data=1)
    c_date_start = datetime.strptime(date_start, "%Y-%m-%d")
    c_date_end = datetime.strptime(date_end, "%Y-%m-%d")
    date_delta = c_date_end - c_date_start
    if date_delta.days < 0:
        return render_template("data.html", data=1)
    big_box = rough_area(resp_lat, resp_long, radius)
    box_query_form = """SELECT *
    FROM dc_site_location
    WHERE latitude BETWEEN {lat_min} AND {lat_max}
    AND longitude BETWEEN {long_min} AND {long_max}"""
    box_query_string = box_query_form.format(lat_min=big_box['lat_min'],
                                             lat_max=big_box['lat_max'],
                                             long_min=big_box['long_min'],
                                             long_max=big_box['long_max'])
    trans_data = engine_txn(engine, box_query_string)
    if len(trans_data) == 0:
        return render_template("data.html", data=2)
    query_form = """SELECT {agg}{time_param}
    FROM {table}
    WHERE {lat} BETWEEN down_left_lat AND up_left_lat
    AND {long} BETWEEN up_left_long and up_right_long
    AND date_dt BETWEEN '{date1}' AND '{date2}'
    {group_by}{order_by};"""
    valid_locations = []
    location_co2_data = []
    location_temp_data = []
    if 'sum_agg' in request.form and 'avg_agg' in request.form:
        return render_template("data.html", data=3)
    elif 'sum_agg' in request.form:
        agg_meth = "SUM(val_average)"
        time_sum = True
    elif 'avg_agg' in request.form:
        agg_meth = 'AVG(NULLIF(val_average,0))'
        time_sum = False
    else:
        agg_meth = 'SUM(val_average)'
        time_sum = True
    if time_series_bool:
        time_axis = None
        time_param_dict = {
            "day": [", date_dt", "GROUP BY date_dt ", "ORDER BY date_dt ASC"],
            "week": [", WEEK(date_dt), YEAR(date_dt)",
                     "GROUP BY YEAR(date_dt), WEEK(date_dt)",
                     "ORDER BY YEAR(date_dt) ASC"],
            "month": [", MONTH(date_dt), YEAR(date_dt)",
                      "GROUP BY YEAR(date_dt), MONTH(date_dt) ",
                      "ORDER BY YEAR(date_dt) ASC"],
            "year": [", YEAR(date_dt)",
                     "GROUP BY YEAR(date_dt) ",
                     "ORDER BY YEAR(date_dt) ASC"]
        }
        search_grain = request.form['date_grain']
        time_param = time_param_dict[search_grain][0]
        group_by = time_param_dict[search_grain][1]
        order_by = time_param_dict[search_grain][2]
        location_temp_data = None
    else:
        time_param = ""
        group_by = ""
        order_by = ""
    for trans_loc in trans_data:
        km_dist = distance_km_func(resp_lat, resp_long,
                                   trans_loc[1], trans_loc[2])
        if km_dist <= radius:
            valid_locations.append(trans_loc[0])
            co2_query_string = query_form.format(agg=agg_meth,
                                                 table="jaxa_l3_co2_daily_box",
                                                 lat=trans_loc[1],
                                                 long=trans_loc[2],
                                                 date1=date_start,
                                                 date2=date_end,
                                                 time_param=time_param,
                                                 group_by=group_by,
                                                 order_by=order_by)
            co2_loc_txn_data = engine_txn(engine, co2_query_string)
            co2_loc_data = [p[0] for p in co2_loc_txn_data]
            co2_loc_data = [0 if d is None else d for d in co2_loc_data]
            if time_series_bool:
                if not time_axis:
                    co2_time_data = [p[1:3] for p in co2_loc_txn_data]
                    search_grain_list = [search_grain] * len(co2_time_data)
                    co2_time_data_converted = list(map(tuple_to_datetime,
                                                       co2_time_data,
                                                       search_grain_list))
                    time_axis = co2_time_data_converted
                    location_co2_data = co2_loc_data
                else:
                    if time_sum:
                        location_co2_data = list(map(add, location_co2_data, co2_loc_data))
                    else:
                        location_co2_data = list(map(two_item_mean, location_co2_data, co2_loc_data))
            else:
                if co2_loc_data[0] == 0:
                    location_co2_data.append("No CO2 data found on this grain.")
                else:
                    co2_val_str = str(round(co2_loc_data[0]*usage_ratio, 2))
                    location_co2_data.append(co2_val_str)
            print(location_co2_data)
            temp_query_string = query_form.format(agg="AVG(val_average)",
                                                  table="skin_temp_daily_box",
                                                  lat=trans_loc[1],
                                                  long=trans_loc[2],
                                                  date1=date_start,
                                                  date2=date_end,
                                                  time_param=time_param,
                                                  group_by=group_by,
                                                  order_by=order_by)
            temp_loc_txn_data = engine_txn(engine, temp_query_string)
            temp_loc_data = [p[0] for p in temp_loc_txn_data]
            temp_loc_data = [0 if d is None else d for d in temp_loc_data]
            if time_series_bool:
                if not time_axis:
                    temp_time_data = [p[1:3] for p in temp_loc_txn_data]
                    search_grain_list = [search_grain] * len(temp_time_data)
                    temp_time_data_converted = list(map(tuple_to_datetime,
                                                        temp_time_data,
                                                        search_grain_list))
                    time_axis = temp_time_data_converted
                    location_temp_data = temp_loc_data
                else:
                    if location_temp_data is None:
                        location_temp_data = temp_loc_data
                    else:
                        if time_sum:
                            location_temp_data = list(map(add, location_temp_data, temp_loc_data))
                        else:
                            location_temp_data = list(map(two_item_mean, location_temp_data, temp_loc_data))
            else:
                if temp_loc_data[0] == 0:
                    location_temp_data.append("No skin temperature data found on this grain.")
                else:
                    temp_val_str = str(round(temp_loc_data[0]*usage_ratio, 2))
                    print(temp_val_str)
                    location_temp_data.append(temp_val_str)
        print(location_co2_data, location_temp_data)
    search_data = [location, radius, usage_hours]
    if time_series_bool:
        data_pkg = zip(time_axis, location_co2_data, location_temp_data)
    else:
        data_pkg = zip(valid_locations, location_co2_data, location_temp_data)
    return render_template("data.html", time_bool=time_series_bool, search_data=search_data, data=data_pkg)


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)
