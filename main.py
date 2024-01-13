import asyncio
import aiohttp
import json
import time

# settings
API_KEY = ""
MAX_REQUESTS_PER_MIN = 400
NUM_PLAYERS_PER_GM = 25
OUTPUT_ERRORS = False


class API:
    def __init__(self):
        self.session = aiohttp.ClientSession()

        self.key = API_KEY
        self.rate_limit = MAX_REQUESTS_PER_MIN
        self.requests = 0

        self.urls = {
            "leaderboard": "https://api.voxyl.net/leaderboard/normal/",
            "guild_leaderboard": "https://api.voxyl.net/guild/top/",
            "guild_members": "https://api.voxyl.net/guild/members/",
            "player_stats": "https://api.voxyl.net/player/stats/game/",
            "ign": "https://api.ashcon.app/mojang/v2/user/",
        }

        with open("gamemodes.json", "r") as file:
            self.gamemodes = json.load(file)

    async def _request(self, url: str, **kwargs) -> dict:
        self.requests += 1
        try:
            async with self.session.get(url, params=kwargs) as resp:
                json = await resp.json(content_type=None)
                if resp.status == 200:
                    return json
                else:
                    # get the reason for the error and output
                    if OUTPUT_ERRORS:
                        if "reason" in json:
                            reason = json["reason"]
                        elif "error" in json:
                            reason = json["error"]
                        else:
                            reason = "Unknown"
                        print(f"ERROR - Code: {resp.status} - Reason: {reason} - URL: {resp.url}")
                    return {}

        except aiohttp.ClientError:
            return {}

    async def close(self):
        await self.session.close()

    async def get_leaderboards(self) -> list[str]:
        level_json = await self._request(self.urls["leaderboard"], api=self.key, num=100, type="level")
        ww_json = await self._request(self.urls["leaderboard"], api=self.key, num=100, type="weightedwins")
        uuids = []
        for player in level_json.get("players", []):
            uuids.append(player["uuid"])
        for player in ww_json.get("players", []):
            uuids.append(player["uuid"])
        return uuids

    async def get_guilds(self) -> list[str]:
        json = await self._request(self.urls["guild_leaderboard"], api=self.key, num=100)
        guilds = []
        for guild in json.get("guilds", []):
            guilds.append(guild["tag"])
        return guilds

    async def get_guild_members(self, guild: str) -> list[str]:
        json = await self._request(self.urls["guild_members"] + guild, api=self.key)
        members = []
        for user in json.get("members", []):
            members.append(user["uuid"])
        return members

    async def get_player_stats(self, uuid: str) -> dict:
        json = await self._request(self.urls["player_stats"] + uuid, api=self.key)
        stats = {}
        for game_name, game_stats in json.get("stats", {}).items():
            if "wins" in game_stats:
                stats[game_name] = game_stats["wins"]
        stats["uuid"] = uuid
        stats["ign"] = await self.get_ign(uuid)
        return stats

    async def get_ign(self, uuid: str) -> str:
        json = await self._request(self.urls["ign"] + uuid)
        return json.get("username", "")


async def main() -> None:
    api = API()
    start = time.time()

    # get the uuids of everything enterd in input_uuids
    with open("input_uuids.txt", "r") as file:
        uuids = [line.strip() for line in file if line.strip()]

    # add uuids of any user on the star on ww leaderboard
    leaderboard_uuids = await api.get_leaderboards()
    uuids.extend(leaderboard_uuids)

    # get a list of all the guild tags on the guild leaderboard
    guilds = await api.get_guilds()

    # split guilds into batches of api.rate_limit, and gather all uuids
    guilds_members = []
    for i in range(0, len(guilds), api.rate_limit):
        guilds_batch = guilds[i : i + api.rate_limit]

        # create a task for each guild to get the uuid of each member
        tasks = [api.get_guild_members(guild) for guild in guilds_batch]
        guilds_members.extend(await asyncio.gather(*tasks))

        await asyncio.sleep(60)

    # add all guild_members list of uuids into overall uuids list
    for guild_members in guilds_members:
        uuids.extend(guild_members)

    # remove all duplicates from uuids
    uuids = list(set(uuids))

    # split uuids into batches of api.rate_limit and gather the stats of each uuid
    players = []
    for i in range(0, len(uuids), api.rate_limit):
        uuids_batch = uuids[i : i + api.rate_limit]

        # create a task for each player to get the player's wins and add it to players
        tasks = [api.get_player_stats(player) for player in uuids_batch]
        players.extend(await asyncio.gather(*tasks))

        # give a progress update in the console
        print(f"Scanned {len(players)}/{len(uuids)} players - {round(len(players)/len(uuids)*100)}%")

        await asyncio.sleep(60)

    # get total time
    total_seconds = round(time.time() - start)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # create title and stats at start of message
    message = "BEDWARS PRACTICE GAMEMODE LEADERBORADS\n\n"
    message += f"Players Scanned: {len(players)} players\n"
    message += f"API Requests: {api.requests} requests\n"
    message += f"Time Elapsed: {hours}h {minutes}m {seconds}s\n"

    # create a message that can be put into an output file
    for gm in api.gamemodes:
        players.sort(key=lambda x: x.get(gm.get("api_name"), 0), reverse=True)

        # add the gm title
        message += f"\n**{gm.get('name', '').upper()}**\n"

        # add the top players by wins
        for i, player in enumerate(players[:NUM_PLAYERS_PER_GM]):
            message += f"{i+1}) {player.get('ign', player.get('uuid'))} - {player.get(gm['api_name'], 0)} wins\n"

    # put message in output.txt
    with open("output.txt", "w+") as file:
        file.write(message)

    await api.close()


if __name__ == "__main__":
    asyncio.run(main())
