from math import radians, cos, sin, asin, sqrt, ceil
from datetime import datetime

r = 6371


def distance_km_func(lat1: float, long1: float, lat2: float, long2: float):
    lat1, long1, lat2, long2 = map(radians, [lat1, long1, lat2, long2])
    lat_diff = lat2 - lat1
    long_diff = long2 - long1
    a = sin(lat_diff/2)**2 + cos(lat1) * cos(lat2) * sin(long_diff/2)**2
    c = 2 * asin(sqrt(a))
    return c * r


def rough_area(lat, long, km, granularity: float = 25):
    raw_adjustment = ceil(km/granularity)
    deg_adjustment = granularity/100 * raw_adjustment
    out_dict = {"lat_max": lat + deg_adjustment,
                "lat_min": lat - deg_adjustment,
                "long_max": long + deg_adjustment,
                "long_min": long - deg_adjustment}
    return out_dict


def tuple_to_datetime(date_tuple, grain):
    if grain == "day":
        return datetime.strftime(date_tuple[0], "%d-%m-%Y")
    date_tuple = [str(dt) for dt in date_tuple]
    if len(date_tuple[0]) < 2:
        date_tuple[0] = "0"+date_tuple[0]
    if grain == "week":
        date_tuple.append("0")
        date_string = "".join(date_tuple)
        dt_obj = datetime.strptime(date_string, "%W%Y%w")
        return datetime.strftime(dt_obj, "%d-%m-%Y")
    elif grain == "month":
        date_string = "".join(date_tuple)
        dt_obj = datetime.strptime(date_string, "%m%Y")
        return datetime.strftime(dt_obj, "%m-%Y")
    elif grain == "year":
        date_string = "".join(date_tuple)
        dt_obj = datetime.strptime(date_string, "%Y")
        return datetime.strftime(dt_obj, "%Y")


def two_item_mean(num1, num2):
    return (num1+num2)/2
