import os
import time
from dotenv import load_dotenv
import sqlite3
from api_calls import get_all_programs, get_all_races, get_results

from db_calls import create_connection, get_elo_athlete, get_elo_ranking, insert_athlete_elo, insert_race, select_all_races, select_all_races_where
from models import AthleteELO, Race

from multielo import MultiElo
import numpy as np

elo = MultiElo()

load_dotenv()

api_key = os.getenv('API_KEY')


def store_races():
    conn = create_connection('storage.db')

    data_races = get_all_races(api_key)
    total = len(data_races)
    i = 0

    for event in data_races:
        i += 1
        print("Remaining: {} of {}".format(total - i, total))
        specifications = ""
        for specification in event['event_specifications']:
            specifications += (str(specification['cat_id'])) + ", "

        categories = ""
        for category in event['event_categories']:
            categories += (str(category['cat_id'])) + ", "

        eventid = event['event_id']
        event_name = event['event_title']
        data_programs = get_all_programs(api_key, eventid)
        if(data_programs == None):
            programid = None
            program_name = event_name
            program_date = event['event_date']
            
            race = Race(event_name, i, specifications, categories, eventid, programid, program_name, program_date)
            insert_race(conn, race)

        else:
            for program in data_programs:
                programid = program['prog_id']
                program_name = program['prog_name']
                program_date = program['prog_date']
                if(program_date == None): program_date = event['event_date']
            
                race = Race(event_name, i, specifications, categories, eventid, programid, program_name, program_date)
                insert_race(conn, race)

    conn.close()


def main():
    conn = create_connection('storage.db')
    
    # Filter races
    races = select_all_races_where(conn, 'Races', 'Men', 357)
    
    print(len(races))
    total = len(races)
    ELO_dict: dict[int, AthleteELO] = {}

    # Get resutlts
    races_processed = 0
    for race in races:
        results = get_results(api_key, race[1], race[2])
        provisional_elo_scores = {}
        elo_scores = {}
        current_athletes: dict[int, AthleteELO] = {}
        
        # Get each athlete from results
        for athlete in results:
            id = athlete['athlete_id']
            # athlete_elo: AthleteELO = None
            if id in ELO_dict.keys():
                athlete_elo = ELO_dict[id]
            else:
                res = get_elo_athlete(conn, id)
                if(res == []):
                    athlete_elo = AthleteELO(id, athlete['athlete_title'], 1000, 0, athlete['athlete_country_name'])
                    insert_athlete_elo(conn, athlete_elo)   
                    ELO_dict[id] = athlete_elo
                else:
                    ELO_dict[id] = AthleteELO(id, res[0][0], res[0][1], res[0][2], res[0][3])
                    athlete_elo = ELO_dict[id]

            current_athletes[id] = athlete_elo

            if(ELO_dict[id].races_count >= 10):
                provisional_elo_scores[id] = (ELO_dict[id].elo)
                elo_scores[id] = (ELO_dict[id].elo)
            else:
                provisional_elo_scores[id] = (ELO_dict[id].elo)
            
        # #ELO MATHS to new values
        elo = MultiElo()

        if(len(elo_scores.values()) > 1): elo_new = elo.get_new_ratings(list(elo_scores.values()))
        if(len(provisional_elo_scores.values()) > 1): provisional_elo_new = elo.get_new_ratings(list(provisional_elo_scores.values()))

        #Update non provisional values
        i = 0
        if(len(elo_scores) > 1):
            for id in elo_scores.keys():
                athlete = ELO_dict[id]
                ELO_dict[id] = ((ELO_dict[id]).update_elo(elo_new[i], race[7])).add_race()
                i += 1

        i = 0
        if(len(provisional_elo_scores) > 1):
            for id in provisional_elo_scores.keys():
                if id not in elo_scores.keys():
                    ELO_dict[id] = ((ELO_dict[id]).update_elo(provisional_elo_new[i], race[7])).add_race()
                
                i += 1


        races_processed += 1
        print("Remaining {} of {} ".format(total - races_processed, total) )

        if(races_processed % 10 == 0):
            for athlete in list(ELO_dict.values()):
                athlete.store_athlete(conn)

main()