# SPDX-FileCopyrightText: 2023 Trevor Beaton for Adafruit Industries
#
# SPDX-License-Identifier: MIT
import os
import ssl
import time
import wifi
import board
import displayio
import digitalio
import terminalio
import socketpool
import adafruit_requests
import simpleio
from adafruit_display_text import bitmap_label

#CLOCK,WEATHER,???
mode = 'WEATHER'

button0 = digitalio.DigitalInOut(board.D0)
button0.direction = digitalio.Direction.INPUT
button0.pull = digitalio.Pull.UP
button0_state = False
button1 = digitalio.DigitalInOut(board.D1)
button1.direction = digitalio.Direction.INPUT
button1.pull = digitalio.Pull.DOWN
button1_state = False
button2 = digitalio.DigitalInOut(board.D2)
button2.direction = digitalio.Direction.INPUT
button2.pull = digitalio.Pull.DOWN
button2_state = False

# Initialize Wi-Fi connection
try:
    wifi.radio.connect(
        os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD")
    )
    print("Connected to %s!" % os.getenv("CIRCUITPY_WIFI_SSID"))
except Exception as e:  # pylint: disable=broad-except
    print(
        "Failed to connect to WiFi. Error:", e, "\nBoard will hard reset in 30 seconds."
    )

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

# Set up the URL for fetching time data
DATA_SOURCE = "http://worldtimeapi.org/api/timezone/" + os.getenv("TIMEZONE")

# Set up display 
display = board.DISPLAY
group = displayio.Group()

# minimum expected temperature
min_temp = 0
# maximum expected temperature
max_temp = 100
# first daylight hour
daytime_min = 7
# last daylight hour
daytime_max = 17
# latitude
lat = os.getenv('LATITUDE')
# longitude
long = os.getenv('LONGITUDE')
# temp unit for API request
temperature_unit = "celcius"
# temp unit for display
temp_unit = "C"

# API request to open-meteo
weather_url = "https://api.open-meteo.com/v1/forecast?"
# pass latitude and longitude
weather_url += "latitude=%d&longitude=%d&timezone=auto" % (float(lat), float(long))
# pass temperature_unit
weather_url += "&current=temperature_2m,relative_humidity_2m,wind_speed_10m&wind_speed_unit=mph"

##CLOCK
# Create label for displaying time
time_label = bitmap_label.Label(terminalio.FONT, scale=5)
time_label.anchor_point = (0.6, 0.5)
time_label.anchored_position = (display.width // 2, display.height // 2)

def set_background_image(filename):
    global current_background_image  # pylint: disable=global-statement
    tile_bitmap = displayio.OnDiskBitmap(filename)
    new_tile_grid = displayio.TileGrid(tile_bitmap, pixel_shader=tile_bitmap.pixel_shader)
    group[0] = new_tile_grid
    current_background_image = filename

def parse_time(datetime_str):
    # Extract the time part from the datetime string
    time_str = datetime_str.split("T")[1].split(".")[0]
    hour, minute, _ = map(int, time_str.split(":"))

    # Convert 24-hour format to 12-hour format and determine AM/PM
    period = "AM"
    if hour >= 12:
        period = "PM"
        if hour > 12:
            hour -= 12
    elif hour == 0:
        hour = 12

    return hour, minute, period
##CLOCK

##WEATHER
temperature_label = bitmap_label.Label(terminalio.FONT, scale=3)
temperature_label.anchor_point = (0.5, 0.5)
temperature_label.anchored_position = (display.width // 2, display.height // 4)

wind_label = bitmap_label.Label(terminalio.FONT, scale=3)
wind_label.anchor_point = (0.5, 0.5)
wind_label.anchored_position = (display.width // 2, (display.height // 4)*2)

humidity_label = bitmap_label.Label(terminalio.FONT, scale=3)
humidity_label.anchor_point = (0.5, 0.5)
humidity_label.anchored_position = (display.width // 2, (display.height // 4)*3)



def get_the_weather():
    # make the API request
    response = requests.get(weather_url)
    # packs the response into a JSON
    response_as_json = response.json()
    print()
    # prints the entire JSON
    print(response_as_json)
    print()
    # gets temperature
    t = response_as_json['current']['temperature_2m']
    temp_int = int(t)
    t_c = simpleio.map_range(temp_int, min_temp, max_temp, 255, 0)
    # gets time
    json_time = response_as_json['current']['time']
    n_t = json_time.rsplit("T", 1)[-1]
    n_t = int(n_t[:2])
    ws = response_as_json['current']['wind_speed_10m']
    humid = response_as_json['current']['relative_humidity_2m']
    return t, t_c, n_t, ws, humid
##WEATHER


# Create main group to hold all display groups
main_group = displayio.Group()
main_group.append(group)
main_group.append(time_label)

weather_group = displayio.Group()
weather_group.append(temperature_label)
weather_group.append(humidity_label)
weather_group.append(wind_label)
# Show the main group on the display
display.root_group = main_group

def showClock():
    display.root_group = main_group
    # Fetch time data from WorldTimeAPI
    response = requests.get(DATA_SOURCE)
    data = response.json()

    # Parse the time from the datetime string
    current_hour, current_minute, current_period = parse_time(data["datetime"])

    # Display the time
    time_label.text = "{:2}:{:02} {}".format(current_hour,current_minute, current_period)


def showWeather():
        display.root_group = weather_group
        temp, temp_color, new_time, windSpeed, humidity = get_the_weather()
        temperature_label.text = str(temp) + ' c'
        wind_label.text = str(windSpeed) + ' mph'
        humidity_label.text = str(humidity) + ' %'


while True:
    showClock()
    time.sleep(60)
    showWeather()
    time.sleep(60)