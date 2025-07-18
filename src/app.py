import requests
import smtplib 
import sys 
import time
import os
import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry
import json
from email.message import EmailMessage
from datetime import datetime, time, timedelta 
from zoneinfo import ZoneInfo


print("Entering application")

def ParseWithOpenMeteo(URL, PARAMS):
    responses = openmeteo.weather_api(URL, PARAMS)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # Current values. The order of variables needs to be the same as requested.
    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()
    current_apparent_temperature = current.Variables(1).Value()
    current_precipitation = current.Variables(2).Value()
    current_rain = current.Variables(3).Value()
    current_showers = current.Variables(4).Value()
    current_snowfall = current.Variables(5).Value()
    current_wind_speed_10m = current.Variables(6).Value()
    current_wind_gusts_10m = current.Variables(7).Value()

    # print(f"Current time {current.Time()}")
    # print(f"Current temperature_2m {current_temperature_2m}")
    # print(f"Current apparent_temperature {current_apparent_temperature}")
    # print(f"Current precipitation {current_precipitation}")
    # print(f"Current rain {current_rain}")
    # print(f"Current showers {current_showers}")
    # print(f"Current snowfall {current_snowfall}")
    # print(f"Current wind_speed_10m {current_wind_speed_10m}")
    # print(f"Current wind_gusts_10m {current_wind_gusts_10m}")

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
    daily_apparent_temperature_max = daily.Variables(2).ValuesAsNumpy()
    daily_apparent_temperature_min = daily.Variables(3).ValuesAsNumpy()
    daily_rain_sum = daily.Variables(4).ValuesAsNumpy()
    daily_showers_sum = daily.Variables(5).ValuesAsNumpy()
    daily_snowfall_sum = daily.Variables(6).ValuesAsNumpy()
    daily_precipitation_sum = daily.Variables(7).ValuesAsNumpy()
    daily_precipitation_hours = daily.Variables(8).ValuesAsNumpy()
    daily_precipitation_probability_max = daily.Variables(9).ValuesAsNumpy()
    daily_wind_speed_10m_max = daily.Variables(10).ValuesAsNumpy()
    daily_wind_gusts_10m_max = daily.Variables(11).ValuesAsNumpy()

    #use pandas to create chart
    daily_data = {"date": pd.date_range(
        start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
        end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = daily.Interval()),
        inclusive = "left"
    )}

    #set up columns
    daily_data["temperature_2m_max"] = daily_temperature_2m_max
    daily_data["temperature_2m_min"] = daily_temperature_2m_min
    daily_data["apparent_temperature_max"] = daily_apparent_temperature_max
    daily_data["apparent_temperature_min"] = daily_apparent_temperature_min
    daily_data["rain_sum"] = daily_rain_sum
    daily_data["showers_sum"] = daily_showers_sum
    daily_data["snowfall_sum"] = daily_snowfall_sum
    daily_data["precipitation_sum"] = daily_precipitation_sum
    daily_data["precipitation_hours"] = daily_precipitation_hours
    daily_data["precipitation_probability_max"] = daily_precipitation_probability_max
    daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max
    daily_data["wind_gusts_10m_max"] = daily_wind_gusts_10m_max

    daily_dataframe = pd.DataFrame(data = daily_data)
    #print(daily_dataframe)

    #end direct from open-meteo.com

def ParseFromRaw(URL, PARAMS):
    # Convert list-type params to comma-separated strings
    params = {
        key: ",".join(value) if isinstance(value, list) else value
        for key, value in PARAMS.items()
    }
    responseRaw = requests.get(URL, params)
    responseJson = responseRaw.json()

    with open(output_path, "w") as f:
        f.write(str(responseRaw.json()))

    #print("Raw data parsed: ")
    return responseJson

def AssembleMessage(parametersToSend):
    alertMessage = "\n\nOne or more weather factors has exceeded a preset threshold: \n\n"
    for parameter in parametersToSend:
        alertMessage = alertMessage + f"{parameter[0]}{parameter[1]}{parameter[2]}\n\n"
    
    #print(alertMessage)
    return alertMessage

def AssembleForecastMessage(parametersToSend):    
    forecastMessage = "\n\n"
    for parameter in parametersToSend:
        forecastMessage = forecastMessage + f"{parameter[0]}{parameter[1]}{parameter[2]}\n\n"
    
    #print(forecastMessage)
    return forecastMessage

def CheckTime():
    time_zone = rawParamsFromConfig["timezone"]
    #print("Timezone: " + time_zone)
    now = datetime.now(ZoneInfo(time_zone))
    target = now.replace(hour = 8, minute = 0, second = 0, microsecond = 0)
    delta = abs(now - target)
    #print(now)
    #print(target)
    #print(delta)
    return delta <= timedelta(minutes = 5)

def SendMessage(message):
    carriers = config["carriers"]["telus"]
    #print("Carriers: " + carriers)    
    phone = config["phone"]
    #print("Phone: " + str(phone))
    recipient = str(phone) + carriers
    #print("Recipient: " + recipient)
    auth = (config["email"],config["password"])
    #print("Auth: " + auth[0] + " " + auth[1])

    msg = EmailMessage()
    msg.set_content(message)
    msg["From"] = auth[0]
    msg["To"] = recipient
    msg["Subject"] = ""

    server = smtplib.SMTP(config["server"], config["port"])
    server.starttls()
    server.login(auth[0], auth[1])
    server.send_message(msg)
    server.quit()

    #server.sendmail(auth[0], recipient, message)


#generate a path for the output file
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct output file path relative to the script
output_path = os.path.join(script_dir, "output.json")

#get values from config file
# Go up one level to reach the project root, then add "config.json"
config_path = os.path.join(script_dir, "..", "config.json")
# Normalize the path
config_path = os.path.normpath(config_path)
testVal = "Pre-load."
config = "holder"
with open(config_path) as json_data:
    config = json.load(json_data)
    json_data.close()
    #print(str(data))
    testVal = config["testParam"]

#direct from open-meteo.com
# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)


meteoParamsFromConfig = config["openMeteoParams"]
rawParamsFromConfig = config["rawParams"]
#ParseWithOpenMeteo(config["url"], meteoParamsFromConfig)
weatherData = ParseFromRaw(config["url"], rawParamsFromConfig)
#print("Raw data after return: ")

currentTime = weatherData["daily"]["time"][0]
currentActualTemp = weatherData["current"]["temperature_2m"]
currentApparentTemp = weatherData["current"]["apparent_temperature"]
currentWindSpeed = weatherData["current"]["apparent_temperature"]
currentWindGusts = weatherData["current"]["apparent_temperature"]
currentSnowfall = weatherData["current"]["apparent_temperature"]

todayTime = weatherData["daily"]["time"][0]
todayMaxTemp = weatherData["daily"]["temperature_2m_max"][0]
todayMinTemp = weatherData["daily"]["temperature_2m_min"][0]
todayApparentMaxTemp = weatherData["daily"]["apparent_temperature_max"][0]
todayApparentMinTemp = weatherData["daily"]["apparent_temperature_min"][0]
todayRain = weatherData["daily"]["rain_sum"][0]
todaySnow = weatherData["daily"]["snowfall_sum"][0]
todayChanceOfRain = weatherData["daily"]["precipitation_probability_max"][0]
todayWindMax = weatherData["daily"]["wind_speed_10m_max"][0]
todayWindGustsMax = weatherData["daily"]["wind_gusts_10m_max"][0]

tomorrowTime = weatherData["daily"]["time"][1]
tomorrowMaxTemp = weatherData["daily"]["temperature_2m_max"][1]
tomorrowMinTemp = weatherData["daily"]["temperature_2m_min"][1]
tomorrowApparentMaxTemp = weatherData["daily"]["apparent_temperature_max"][1]
tomorrowApparentMinTemp = weatherData["daily"]["apparent_temperature_min"][1]
tomorrowRain = weatherData["daily"]["rain_sum"][1]
tomorrowSnow = weatherData["daily"]["snowfall_sum"][1]
tomorrowChanceOfRain = weatherData["daily"]["precipitation_probability_max"][1]
tomorrowWindMax = weatherData["daily"]["wind_speed_10m_max"][1]
tomorrowWindGustsMax = weatherData["daily"]["wind_gusts_10m_max"][1]

# print(currentTime)
# print(currentActualTemp)
# print(currentApparentTemp)
# print(currentWindSpeed)
# print(currentWindGusts)
# print(currentSnowfall)
# print(tomorrowTime)
# print(tomorrowMaxTemp)
# print(tomorrowMinTemp)
# print(tomorrowApparentMaxTemp)
# print(tomorrowApparentMinTemp)
# print(tomorrowRain)
# print(tomorrowSnow)
# print(tomorrowChanceOfRain)
# print(tomorrowWindMax)
# print(tomorrowWindGustsMax)

#test changes for hot day
#currentActualTemp = 35
#currentApparentTemp = 36
#currentWindSpeed = 35
#currentWindGusts = 45
#test changes for cold day
#currentActualTemp = 3
#currentApparentTemp = -15
#currentWindSpeed = 35
#currentWindGusts = 45

#generate alert message for hourly check-ins and send if needed
#make sure not to run these overnight (?)
parametersToAlert = []
if(currentActualTemp > 30):
    parametersToAlert.append(("Current temperature is ", currentActualTemp, "C. Consider sheltering plants."))
if(currentActualTemp < 5):
    parametersToAlert.append(("Current temperature is ", currentActualTemp, "C. Consider bringing plants in."))
if(currentApparentTemp > 30):
    parametersToAlert.append(("Current temperature feels like ", currentApparentTemp, "C. Consider sheltering plants."))
if(currentApparentTemp < 5):
    parametersToAlert.append(("Current temperature feels like ", currentApparentTemp, "C. Consider bringing plants in."))
if(currentWindSpeed > 30):
    parametersToAlert.append(("Current average wind speed is ", currentWindSpeed, "kph. Consider sheltering plants."))
if(currentWindGusts > 40):
    parametersToAlert.append(("Wind is gusting up to ", currentWindGusts, "kph. Consider sheltering plants."))

if(len(parametersToAlert) > 0):
    SendMessage(AssembleMessage(parametersToAlert))

#check the time, and if it's first thing in the morning, assembled and send a morning forecast message
isMorning = CheckTime()
#isMorning = True
if(isMorning):
    messageToAssemble = []
    messageToAssemble.append(("Good morning!", "\n\nToday is ", currentTime))
    messageToAssemble.append(("Today's high will be ", todayMaxTemp, "C."))
    messageToAssemble.append(("Today's low will be ", todayMinTemp, "C."))
    messageToAssemble.append(("Windspeed today will be ", todayWindMax, "kph"))
    messageToAssemble.append(("with gusts up to ", todayWindGustsMax, "kph."))
    messageToAssemble.append(("There is a ", todayChanceOfRain, "% chance of precipitation today, consisting of "))
    if(todayMaxTemp > 0):
        messageToAssemble.append(("up to ", todayRain, "mm of rain."))
    else:
        messageToAssemble.append(("up to ", todaySnow, "cm of snow."))

    SendMessage(AssembleForecastMessage(messageToAssemble))

