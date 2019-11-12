'''import requests
import json

api_url_base = ''
headers = {}'''
import pandas as pd
import time
import datetime
import threading
import ast
import WazeRouteCalculator as wrc
import requests
import googlemaps as gmaps
import numpy as np

# after first try:
df = pd.read_csv('traffic_reroute_data_waze.csv', index_col=0)
df.waypoints = df.waypoints.astype(object)
index = df.shape[0]

server = gmaps.Client(key='AIzaSyB4RP41j6fJkO5FPrpKmqeYS3rQVxqEIVc')


#origin goes first, then destination goes second
city_coordinates = {'Morgan Hill': [(37.21324164386, -121.72705650329), (37.1264951034, -121.6306869126)],
                    'Concord': [(37.991371, -122.081389), (38.010636, -122.015226)],
    'Hwy 24': [(37.849014, -122.236295), (37.8977466, -122.0838973)],
 "San Mateo": [(37.586940, -122.343883), (37.566206, -122.270454)],
 'Los Altos': [(37.39187539275, -122.16922875), (37.346108, -122.098488)],
 'US 101 Belmont': [(37.509949, -122.251484), (37.530528, -122.274775)],
    'CA-237': [(37.40186586713, -122.0316463), (37.4218355645, -121.932555371)]}

#unique_route_coordinates = {'Hwy 24': {}, 'San Mateo': {}, 'Los Altos': {}, 'US 101 Belmont': {}}
#unique_route_distances = {'Hwy 24': {}, 'San Mateo': {}, 'Los Altos': {}, 'US 101 Belmont': {}}
file = open('unique_route_distances.txt')
path_content = file.read()
unique_route_distances = ast.literal_eval(path_content)

file = open('convert_waze_to_gmaps_dict2.py')
path_content = file.read()
unique_route_coordinates = ast.literal_eval(path_content)

file = open('tracked_segments.py')
path_content = file.read()
segments = ast.literal_eval(path_content)

def gmaps_directions(params):
    url = 'https://maps.googleapis.com/maps/api/directions/json?'
    response = requests.get(url, params=params)
    if response.status == 200:
        content = response.json()
        return content
    else:
        return 'error'

def waypoints_into_string(waypoints):
    string = ''
    for pair in waypoints:
        string = string + 'via:' + str(pair[0]) + ',' + str(pair[1]) + '|'
    string = string[:-1]
    return string
    

def waypoint_simplifier(coordinates):
    max_waypoints = 21
    orig_coord = coordinates[0]
    dest_coord = coordinates[-1]
    waypoints = coordinates[1:-1]
    if len(waypoints) > max_waypoints:
        step_size = (len(waypoints)//max_waypoints) + 1
        waypoints = waypoints[::step_size]
    coordinates = [orig_coord] + waypoints + [dest_coord]
    '''for n, pair in enumerate(coordinates):
        for k, decimal in enumerate(pair):
            coordinates[n][k] = round(decimal, 5)''' #don't round!
    return coordinates

secs_program_is_running = 10800
sleep_secs = 120

#service is 0 for Waze, 1 for GMaps, 1.5 is GMaps where distance doesn't match Waze, 2.0 is Waze single segment, 3.0 is GMaps original
#4.0 is GMaps segment
for n in range(int(secs_program_is_running/sleep_secs)):
    for city in city_coordinates.keys():
        orig_coord = city_coordinates[city][0]
        dest_coord = city_coordinates[city][1]
        current_time = datetime.datetime.fromtimestamp(time.time())
        try: 
            route = wrc.WazeRouteCalculator(start_address = orig_coord, end_address = dest_coord, region='US')
            info = route.calc_all_routes_info()
            print ('good')
            for unique_route in info.keys(): #returns a gigantic list including alternatives, each entry is a route
                service = 0
                duration = info[unique_route][0]
                summary = unique_route
                km = info[unique_route][1]
                coordinate_list = waypoint_simplifier(info[unique_route][2]) #simplify the route anyway
                

                df.loc[index, :] = [current_time, city, summary, duration, km, service, coordinate_list]

                    
                index += 1
        
        except Exception as e:
            print (e)
            df.loc[index, :] = [current_time, city, 'Error:' + str(e), 0, 0, 0, 0]
            index += 1
        # ----- Start Google Maps ----- #
        try:
            directions = server.directions(origin=orig_coord, destination=dest_coord, alternatives=True, departure_time='now', traffic_model='best_guess')
            print ('good')
            for route in directions: #returns a gigantic list including alternatives, each entry is a route 
                duration = route['legs'][0]['duration_in_traffic']['value'] / 60.0 #we will only have one leg, because no waypoints
                summary = route['summary']
                km = route['legs'][0]['distance']['value']/1000
                coordinate_list = ''
                service = 3.0
                

                current_time = datetime.datetime.fromtimestamp(time.time())
                df.loc[index, :] = [current_time, city, summary, duration, km, service, coordinate_list]
                index += 1
        except Exception as e:
            print (e)
            df.loc[index, :] = [current_time, city, 'Error:' + str(e), 0, 0, 0, 0]
            index += 1
    for city, segment_dict in segments.items():
        current_time = datetime.datetime.fromtimestamp(time.time())
        for segment_name, segment_coord in segment_dict.items():
            try:
                orig_coord = segment_coord[0]
                dest_coord = segment_coord[-1]
                route = wrc.WazeRouteCalculator(start_address = orig_coord, end_address = dest_coord, region='US')
                duration, km = route.calc_route_info()

                service = 2.0

                summary = segment_name
                coordinate_list = '' #nan coordinate list
                

                df.loc[index, :] = [current_time, city, summary, duration, km, service, coordinate_list]
                index += 1
                
            except Exception as e:
                print (e)
                df.loc[index, :] = [current_time, city, 'Error:' + str(e), 0, 0, 0, 0]
                index += 1
            # ___ Start Google Maps ___ #
            try:
                directions = server.directions(origin=orig_coord, destination=dest_coord, departure_time='now', traffic_model='best_guess')
                print ('good')
                
                duration = directions[0]['legs'][0]['duration_in_traffic']['value'] / 60.0 #we will only have one leg, because no waypoints
                summary = directions[0]['summary']
                km = directions[0]['legs'][0]['distance']['value']/1000
                coordinate_list = ''
                service = 4.0
                    

                current_time = datetime.datetime.fromtimestamp(time.time())
                df.loc[index, :] = [current_time, city, summary, duration, km, service, coordinate_list]
                index += 1
            except Exception as e:
                print (e)
                df.loc[index, :] = [current_time, city, 'Error:' + str(e), 0, 0, 0, 0]
                index += 1

                

    for k in range(int((sleep_secs/10))):
        time.sleep(10)

    df.to_csv('traffic_reroute_data_waze.csv')

    '''file = open('convert_waze_to_gmaps_dict3-1.py', 'w')
    file.write(str(unique_route_coordinates))
    file.close()
    file = open('unique_route_distances.txt', 'w')
    file.write(str(unique_route_distances))
    file.close()'''

    
    

