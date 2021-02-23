'''
This module creates a web map. The web map displays information
about the locations of films that were shot in a given year.
'''

from flask import Flask, render_template, request
import tweepy, folium, certifi, ssl
import geopy.distance
from geopy.distance import geodesic
from geopy.exc import GeocoderUnavailable
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


def twitter(username, consumer_key, consumer_secret, access_token, access_token_secret):
    '''
    This function returns a list of followers and their location
    '''

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    flag = True
    api = tweepy.API(auth)
    counter = 0
    lst = []
    try:
        user = api.get_user(username)
    except:
        flag = False
    if flag:
        for friend in user.friends():
            coordinates = friend.location
            geolocator = Nominatim(user_agent="location", scheme='http')
            geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
            ctx = ssl.create_default_context(cafile=certifi.where())
            geopy.geocoders.options.default_ssl_context = ctx
            location = geolocator.geocode(coordinates)
            if location == None:
                continue
            else:
                lst.append((location.latitude, location.longitude, friend.screen_name))
                counter += 1
                if counter > 8:
                    break
    return lst, flag


def create_map(values: list()):
    '''
    This function creates a map with 3 layers. The map shows 10 labels
    of the nearest filming locations.
    '''

    map = folium.Map(tiles="Stamen Terrain",location = [values[0][0], values[0][1]], zoom_start=4)
    fg = folium.FeatureGroup(name='Users')
    for user_info in values:
        loc_x = user_info[0]
        loc_y = user_info[1]
        name = user_info[2]
        fg.add_child(folium.Marker(location=[loc_x,loc_y], popup=name, icon=folium.Icon()))
    map.add_child(fg)
    map.add_child(folium.LayerControl())
    return map


app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/map", methods=["POST"])
def register():
    consumer_key = request.form.get("consumer_key")
    consumer_secret = request.form.get("consumer_secret")
    access_token = request.form.get("access_token")
    access_token_secret = request.form.get("access_token_secret")
    username = request.form.get("username")
    if not consumer_key or not consumer_secret or not access_token or not access_token_secret or not username:
        return render_template("failure.html")
    lst = twitter(username, consumer_key, consumer_secret, access_token, access_token_secret)
    if lst[1]:
        users_on_map = create_map(lst[0])
        return users_on_map.get_root().render()
    else:
        return render_template("failure.html")

app.run(debug = True)
