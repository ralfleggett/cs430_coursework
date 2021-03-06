import ast
import collections
import csv
import json

from datetime import date
from re import match
from tqdm import tqdm

from HLTV import HLTV

MAJOR_EVENT_ID = 4866
MAJOR_END_DATE = date(2021, 11, 7)

def write_dict(dict_to_write, filename):
    """
    Writes a dictionary to the filename
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({str(k): v for k, v in dict_to_write.items()}, f, ensure_ascii=False, indent=4)
        # json.dump(dict_to_write, f, ensure_ascii=False, indent=4)

def read_json(filename, is_tuple_key=False):
    """
    Reads a json file into a dictionary
    """
    with open(filename) as handle:
        dictdump = json.loads(handle.read())
    return dictdump if not is_tuple_key else {ast.literal_eval(k): v for k, v in dictdump.items()}

def get_major_teams(hltv):
    """
    Queries HLTV for teams that played in final 16 of the 2021 PGL major
    """
    return hltv.get_event_teams(MAJOR_EVENT_ID, "pgl-major-stockholm-2021")

def get_major_players(hltv, team_dict):
    """ 
    Queries HLTV for players in teams in team_dict 
    """
    players = {}
    for team_id, team_name in tqdm(team_dict.items(), unit="team"):
        player_dict = hltv.get_event_team_players(team_id, team_name, MAJOR_EVENT_ID)
        team_dict[team_id].update({
            "major_roster": [id for id in player_dict],
            "players": [id for id in player_dict]
        })
        players.update(player_dict)
    return players

def get_map_ids(hltv, team_dict, latest_date=None, min_players=5):
    """
    Gets all map ids between teams in team_dict where the players in the 
    map were exactly the players specified in team_dict. Ignores maps
    after latest_date if not None
    Returns:
        dictionary {map_id: [team1_id, team2_id]}
    """
    team_ids = list(team_dict.keys())
    map_ids = {}            # IDs that have appeared at least once
    confirmed_map_ids = {}  # IDs which have appeared for both teams

    for team in tqdm(team_dict, unit="teams"):
        ids = hltv.get_map_ids(
            team_dict[team]["players"], 
            team, 
            team_ids,
            latest_date=latest_date,
            min_players=min_players)
        for id in ids:
            if id not in map_ids:
                map_ids.update({id: ids[id]})
            else:
                confirmed_map_ids.update({id: ids[id]})

    return confirmed_map_ids

def remove_invalid_maps(map_ids, match_dict, event_dict):
    """
    Params:
        map_ids:    [map_id]. map_ids to remove
        match_dict: dictionary. Remove maps, empty matches from it
        event_dict: dictionary. Remove empty events from it
    Returns:
        match_dict: updated match_dict
        event_dict: updated event_dict
    """
    matches_to_delete = []
    for match in match_dict:
        if any(x in map_ids for x in match_dict[match]["map_ids"]):
            # [map_ids] contains an invalid map
            match_dict[match]["map_ids"] = [x for x in match_dict[match]["map_ids"] if x not in map_ids]
            if len(match_dict[match]["map_ids"]) == 0:
                matches_to_delete.append(match)

    for match in matches_to_delete:
        # match contains no maps
        del match_dict[match]
        # delete from event_dict
        for event in event_dict:
            if match in event_dict[event]["match_ids"]:
                event_dict[event]["match_ids"].remove(match)
                if len(event_dict[event]["match_ids"]) == 0:
                    # event contains no matches
                    del event_dict[event]
                break

    return match_dict, event_dict

def map_player_dict_to_csv(map_player_dict, player_dict):
    keylist = list(map_player_dict.keys())
    with open('map_player.csv', 'w', newline='') as csvfile:
        fieldnames = ['map_id', 'player_id', 'player_name']
        fieldnames.extend(list(map_player_dict[keylist[0]].keys()))

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for (map_id, player_id) in keylist:
            player_name = player_dict[player_id]["name"]
            dict_to_write = {
                "map_id": map_id,
                "player_id": player_id,
                "player_name": player_name
            }
            dict_to_write.update(map_player_dict[(map_id, player_id)])
            writer.writerow(dict_to_write)

def main():
    hltv = HLTV("hltv.org")

    team_dict = read_json("team.json")
    player_dict = read_json("player.json")
    event_dict = read_json("event.json")
    match_dict = read_json("match.json")
    # map_dict = read_json("map.json")
    map_player_dict = read_json("map_player.json", is_tuple_key=True)
    map_pick_dict = read_json("./other_jsons/map_picks.json")
    # map_ids = read_json("map_ids.json")

    # team_dict = get_major_teams(hltv)
    # player_dict = get_major_players(hltv, team_dict)
    # map_ids = get_map_ids(hltv, team_dict, latest_date=MAJOR_END_DATE, min_players=4)
    # match_dict, map_pick_dict, events_dict = hltv.get_match_ids(map_dict, team_dict)
    map_info_dict, invalid_map_ids = hltv.get_map_info(team_dict, match_dict, map_pick_dict)
    # print(f"{len(invalid_map_ids)} invalid maps found")
    # match_dict, event_dict = remove_invalid_maps(invalid_map_ids, match_dict, event_dict)
    # map_player_dict, player_dict, team_dict = hltv.get_map_player_info(map_dict, player_dict, team_dict)

    # write_dict(team_dict, "teams_new.json")
    # write_dict(player_dict, "players_new.json")
    # write_dict(map_ids, "map_ids.json")
    # write_dict(match_dict, "matches.json")
    # write_dict(map_pick_dict, "map_picks.json")
    # write_dict(event_dict, "events.json")
    write_dict(map_info_dict, "map.json")
    # write_dict(map_player_dict, "map_player.json")

    # map_player_dict_to_csv(map_player_dict, player_dict)
  
if __name__ == "__main__":
    main()