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
import numpy as np

# after first try:
df = pd.read_csv('traffic_reroute_data_waze.csv', index_col=0)
df.waypoints = df.waypoints.astype(object)
index = df.shape[0]

#origin goes first, then destination goes second
city_coordinates = {'Hwy 24': [(37.849014, -122.236295), (37.8977466, -122.0838973)],
 "San Mateo": [(37.586940, -122.343883), (37.566206, -122.270454)],
 'Los Altos': [(37.391796, -122.168691), (37.346108, -122.098488)],
 'US 101 Belmont': [(37.509949, -122.251484), (37.530528, -122.274775)]}

#unique_route_coordinates = {'Hwy 24': {}, 'San Mateo': {}, 'Los Altos': {}, 'US 101 Belmont': {}}
#unique_route_distances = {'Hwy 24': {}, 'San Mateo': {}, 'Los Altos': {}, 'US 101 Belmont': {}}
file = open('unique_route_distances.txt')
path_content = file.read()
unique_route_distances = ast.literal_eval(path_content)

file = open('convert_waze_to_gmaps_dict2.py')
path_content = file.read()
unique_route_coordinates = ast.literal_eval(path_content)

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

#service is 0 for Waze, 1 for GMaps, 1.5 is GMaps where distance doesn't match Waze

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

                unique_route_distances[city][summary] = km
                
                if summary not in unique_route_coordinates[city].keys():
                    coordinate_list = info[unique_route][2]
                    simplified_list = waypoint_simplifier(coordinate_list)
                    unique_route_coordinates[city][summary] = simplified_list
                    df.at[index, 'waypoints'] = str(simplified_list)
                    
                index += 1
        
        except Exception as e:
            print (e)
            df.loc[index, :] = [current_time, city, 'Error:' + str(e), 0, 0, 0, 0]
            index += 1
    for city, path in unique_route_coordinates.items():
        for path_name, coordinates in path.items():
            try:
                orig_coord = str(coordinates[0][0]) + ',' + str(coordinates[0][1])
                dest_coord = str(coordinates[-1][0]) + ',' + str(coordinates[-1][1])
                waypoints = coordinates[1:-1]
                waypoints = waypoints_into_string(waypoints)
                
                parameters = {'origin':orig_coord, 'destination':dest_coord, 'waypoints':waypoints, 'departure_time':'now', 'traffic_model':'best_guess', 'key':'AIzaSyB4RP41j6fJkO5FPrpKmqeYS3rQVxqEIVc'}
                directions = gmaps_directions(parameters)
                if directions == 'error':
                    raise Exception('Some problem occurred while requesting from GMaps API.')

                service = 1
                duration = directions['routes'][0]['legs'][0]['duration_in_traffic']['value'] / 60
                km = directions['routes'][0]['legs'][0]['distance']['value']/1000 #behind the scenes GMaps uses km!
                summary = path_name
                current_time = datetime.datetime.fromtimestamp(time.time())

                if abs(km - unique_route_distances[city][path_name]) > 0.1:
                    service = 1.5
                
                df.loc[index, :] = [current_time, city, summary, duration, km, service, str(coordinates)]
                print ('Gmaps good')
                index += 1
 #           directions = server.directions(origin=orig_coord, destination=dest_coord, waypoints = waypoints, departure_time='now', traffic_model='best_guess')
            except Exception as e:
                print (e)

    for k in range(int((sleep_secs/10))):
        time.sleep(10)


            
        
    

df.to_csv('traffic_reroute_data_waze.csv')

coordinates = pd.DataFrame((city, route, pair) for city, routes in unique_route_coordinates.items() for route, coords in routes.items() for pair in coords)
coordinates.to_csv('waze_route_coordinates.csv')

file = open('convert_waze_to_gmaps_dict3-1.py', 'w')
file.write(str(unique_route_coordinates))
file.close()
file = open('unique_route_distances.txt', 'w')
file.write(str(unique_route_distances))
file.close()

    
    

