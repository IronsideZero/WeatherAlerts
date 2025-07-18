This is a weather checking app that uses the Open-Meteo API to check local weather and give me an hourly alert via text if certain weather factors exceed certain thresholds. Otherwise, it gives me a morning text with the forecast for the day. The python script CAN run independently, however it was written to run inside a docker container. It's triggered hourly by a batch script executed by Windows Task Scheduler. 

Some helpful info:

docker stop weatheralerts-container 
docker rm weatheralerts-container
docker build -t weatheralerts .
docker run -d --name weatheralerts-container -v "${pwd}:/app" weatheralerts 



If developing inside a vs code dev container, the code will go into the workspaces folder. 
If there are multiple python installations, may need to use the command alias python=/usr/local/bin/python in order to force the terminal to use the correct installation
If that doesn't work, just run pip install package1 package2 package3 for whatever is missing. 
