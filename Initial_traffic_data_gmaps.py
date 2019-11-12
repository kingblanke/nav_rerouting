'''import requests
import json

api_url_base = ''
headers = {}'''

##### Honestly I don't plan on using Google Maps to do route choice... instead, calc traffic ###
import pandas as pd
import time
import datetime
import threading
import googlemaps as gmaps

# after first try:
df = pd.read_csv('traffic_reroute_data_gmaps.csv')
index = df.shape[0]
server = gmaps.Client(key='AIzaSyB4RP41j6fJkO5FPrpKmqeYS3rQVxqEIVc')
#result = server.distance_matrix(origins=(37.788829, -122.388450), destinations=(37.768736, -122.405514),
#                       mode='driving', language='English', departure_time='now', traffic_model='best_guess')

#origin goes first, then destination goes second
city_coordinates = {'Hwy 24': [(37.848651, -122.2354605), (37.8977466, -122.0838973)],
 "Emeryville-Pinole": [(37.837513, -122.296113), (37.993544, -122.300030)],
 'Los Altos': [(37.387616, -122.155752), (37.346108, -122.098488)],
 '880 to 680':[(37.440600, -121.91997), (37.5473190, -121.919613)]}
#First one is the rush hour trip from downtown approaching across the Bay Bridge
#Second one is a shortcut on I-680
#Third one is a shortcut onto Dumbarton bridge

#ideas: 3rd street between market and 16th
secs_program_is_running = 10800
sleep_secs = 60

for n in range(int(secs_program_is_running/sleep_secs)):
    for city in city_coordinates.keys():
        orig_coord = city_coordinates[city][0]
        dest_coord = city_coordinates[city][1]
        directions = server.directions(origin=orig_coord, destination=dest_coord, alternatives=True, departure_time='now', traffic_model='best_guess')
        print ('good')
        for route in directions: #returns a gigantic list including alternatives, each entry is a route 
            duration = route['legs'][0]['duration_in_traffic']['value'] / 60.0 #we will only have one leg, because no waypoints
            summary = route['summary']
            steps = len(route['legs'][0]['steps'])
            start_address = route['legs'][0]['start_address']
            end_address = route['legs'][0]['end_address']
            start_location = route['legs'][0]['start_location']
            end_location = route['legs'][0]['end_location']
            current_time = datetime.datetime.fromtimestamp(time.time())
            df.loc[index, :] = current_time, city, summary, duration, steps, start_address, end_address, start_location, end_location
            index += 1
    for k in range(int((sleep_secs/10))):
        time.sleep(10)

df.to_csv('traffic_reroute_data_gmaps.csv')

    
    

