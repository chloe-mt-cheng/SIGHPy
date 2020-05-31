import pandas as pd
from geopy.geocoders import Nominatim
from urllib import parse

geolocator = Nominatim(user_agent="colin_test_app")

raw_frame = pd.read_csv("dc_address.csv")
address_array = raw_frame['address']

site_frame = pd.DataFrame(columns=["address", "latitude", "longitude"])
site_frame_index = 0
for address in address_array[4135:]:
    address = parse.unquote(address)
    location_resp = geolocator.geocode(address)
    if location_resp is None:
        continue
    resp_lat = location_resp.latitude
    resp_long = location_resp.longitude
    site_frame.loc[site_frame_index] = [address, resp_lat, resp_long]
    site_frame_index += 1
    if site_frame_index in [1000, 2000, 3000, 4000, 5000]:
        print("Refreshing geo session.")
        geolocator = Nominatim(user_agent="colin_test_app")

site_frame.to_csv("site_lat_long.csv")
