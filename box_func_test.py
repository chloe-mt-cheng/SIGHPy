from datetime import datetime
import pandas as pd
import os

dir_path = "C:\\Users\\Colin Yip\\Documents\\SpaceApps\\2019_csv\\SurfSkinTemp"
file_list = os.listdir(dir_path)

in_dfs = []

for file in file_list:
    file_path = dir_path+"\\"+file
    tmp_df = pd.read_csv(file_path)
    tmp_df['date'] = tmp_df['date'].apply(lambda x: datetime.strptime(x, "%Y_%m_%d"))
    in_dfs.append(tmp_df)

col_names = ["up_left_lat", "up_left_long", "up_right_lat", "up_right_long",
             "down_left_lat", "down_left_long", "down_right_lat", "down_right_long"]


def lat_switch_func(lat_list):
    lat_list_len = len(lat_list)
    prev_val = None
    out_list = []
    for j in range(lat_list_len):
        curr_val = lat_list[j]
        if j == 0:
            prev_val = curr_val
            continue
        if curr_val == prev_val:
            continue
        else:
            out_list.append(j)
            prev_val = curr_val
    return out_list


def comparison(item1, item2):
    item1_bool = item1 != -9999
    item2_bool = item2 != -9999
    if item1_bool and item2_bool:
        return (item1+item2)/2
    elif item1_bool and not item2_bool:
        return item1
    elif not item1_bool and item2_bool:
        return item2
    else:
        return -9999


def box_create(df, lat_col_name, long_col_name, value_col_names, col_names):
    output_boxes = {}
    prev_lat = None
    prev_long = None
    df_len = df.shape[0]
    lats = df[lat_col_name]
    lat_switch = lat_switch_func(lats)
    lat_switch_i = 0
    for i in range(df_len):
        slice = df.iloc[i]
        curr_lat = slice[lat_col_name]
        curr_long = slice[long_col_name]
        try:
            next_slice = df.iloc[i+1]
            next_long = next_slice[long_col_name]
        except IndexError:
            next_long = None
        if i == lat_switch[lat_switch_i]:
            prev_long = None
            if lat_switch_i < len(lat_switch)-1:
                lat_switch_i += 1
        lat_row_push = lat_switch[lat_switch_i]
        if (i+1) == lat_row_push:
            next_long = None
        if lat_row_push != lat_switch[-1]:
            next_lat = df.iloc[lat_row_push][lat_col_name]
        else:
            next_lat = None
        if prev_lat is None:
            up_left_lat = up_right_lat = curr_lat
            down_left_lat = down_right_lat = (curr_lat+next_lat)/2
        elif next_lat is None:
            up_left_lat = up_right_lat = (prev_lat+curr_lat)/2
            down_left_lat = down_right_lat = curr_lat
        else:
            up_left_lat = up_right_lat = (prev_lat+curr_lat)/2
            down_left_lat = down_right_lat = (curr_lat+next_lat)/2
        if prev_long is None:
            up_left_long = down_left_long = curr_long
            up_right_long = down_right_long = (curr_long+next_long)/2
        elif next_long is None:
            up_left_long = down_left_long = (prev_long+curr_long)/2
            up_right_long = down_right_long = curr_long
        else:
            up_left_long = down_left_long = (prev_long+curr_long)/2
            up_right_long = down_right_long = (curr_long+next_long)/2
        prev_long = curr_long
        if (i+1) == lat_row_push:
            prev_lat = curr_lat
        append_list = [up_left_lat, up_left_long, up_right_lat, up_right_long,
                       down_left_lat, down_left_long, down_right_lat, down_right_long]
        output_boxes[i] = append_list
    box_frame = pd.DataFrame.from_dict(output_boxes, orient='index')
    box_frame.columns = col_names
    box_frame['val_average'] = [-9999] * df.shape[0]
    for value_col_name in value_col_names:
        box_frame_val = list(box_frame['val_average'])
        df_val = list(df[value_col_name])
        box_frame['val_average'] = list(map(comparison, box_frame_val, df_val))
    box_frame['val_average'] = box_frame['val_average'].apply(lambda x: None if x < 0 else x)
    box_frame['date'] = df['date']
    return box_frame


box_dfs = []
index = 0

for df in in_dfs:
    lat_param = "location/Data Fields/Latitude"
    long_param = "location/Data Fields/Longitude"
    temp_params = ["ascending/Data Fields/SurfSkinTemp_A","descending/Data Fields/SurfSkinTemp_D"]
    box_dfs.append(box_create(df, lat_col_name=lat_param,
                              long_col_name=long_param,
                              value_col_names=temp_params,
                              col_names=col_names))
    # except KeyError:
    #     lat_param = "Data/geolocation/latitude"
    #     long_param = "Data/geolocation/longitude"
    #     box_dfs.append(box_create(df, lat_col_name=lat_param,
    #                           long_col_name=long_param,
    #                           value_col_names=["Data/latticeInformation/XCO2Average"],
    #                           col_names=col_names))
    print(index)
    index += 1

final_temp_box = pd.concat(box_dfs).reset_index().drop('index', axis=1)
