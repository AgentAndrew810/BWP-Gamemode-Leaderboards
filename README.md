
# BWP-Gamemode-Leaderboards

BWP Gamemode Leaderboards is a Python utility for gettings the players with the most wins in each BWP gamemode. It uses asynchronous HTTP requests to the Voxyl API for efficient data collection.

If you don't want to run the project, you can just open output.txt in the github for the results.
## Usage
Clone Project
```
  git clone https://github.com/AgentAndrew810/BWP-Gamemode-Leaderboards
```
Install dependencies
```
pip install aiohttp
```
Get api key on bwp
```
/api get
```

Adjust settings in main.py, make sure to add api key from bwp
```
API_KEY = ""
MAX_REQUESTS_PER_MIN = 400
NUM_PLAYERS_PER_GM = 25
OUTPUT_ERRORS = False
```
Start the program
```
python main.py
```
## Adding Custom UUIDS

Open input_uuids.txt, add one uuid per line. 
```
00462df2-aabf-4f9e-8673-604970dc8195
88542690-737a-47e3-87f4-4af32dd5a6e4
e995b082-baa3-46fa-bfbb-51f40f3c7a47
```

## Output
Open the output.txt file after main.py has finished.
