import os
import time
from dotenv import load_dotenv
from api_calls import get_all_programs, get_all_races, get_participants, get_results

from db_calls import create_connection, create_table, insert_athlete_elo, insert_event_elo_rank, insert_race, insert_table, select_all_where, select_athlete_elo_order_elo, select_elo
from models import AthleteELO, Race

from multielo import MultiElo
import numpy as np

from prediction_model import calculate_loss, create_event_table, predict_event2

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


def generate_elo_from(since_date):
    conn = create_connection('storage.db')
    # Filter races
    races = select_all_where(conn, 'Races', 'Men', 357)
    
    total = len(races)
    ELO_dict: dict[int, AthleteELO] = {}

    # Get resutlts
    races_processed = 0
    for race in races:
        if(time.strptime(race[7], '%Y-%m-%d') < time.strptime(since_date, '%Y-%m-%d')):
            races_processed += 1
            continue
            
        print(race[7])
        results = get_results(api_key, race[1], race[2])
        provisional_elo_scores = {}
        elo_scores = {}
        current_athletes: dict[int, AthleteELO] = {}
        
        # Get each athlete from results
        for athlete in results:
            id = athlete['athlete_id']
            if id in ELO_dict.keys():
                athlete_elo = ELO_dict[id]
            else:
                athlete_elo = get_elo_athlete(conn, id)
                if(athlete_elo == []):
                    athlete_elo = AthleteELO(id, athlete['athlete_title'], 1000, 0, athlete['athlete_country_name'], "", [], [])
                    insert_athlete_elo(conn, athlete_elo)   
                    ELO_dict[id] = athlete_elo
                else:
                    ELO_dict[id] = athlete_elo

            if(ELO_dict[id].races_count >= 10):
                provisional_elo_scores[id] = (ELO_dict[id].elo)
                elo_scores[id] = (ELO_dict[id].elo)
            else:
                provisional_elo_scores[id] = (ELO_dict[id].elo)
            
        # #ELO MATHS to new values
        elo = MultiElo()

        elo_new = []
        provisional_elo_new = []
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

        if(races_processed % 20 == 0):
            for athlete in list(ELO_dict.values()):
                athlete.store_athlete(conn)

def predict_event(eventid, programid):
    conn = create_connection('storage.db')
    participants = get_participants(api_key, eventid, programid)

    create_table(conn, "EVENTe{}p{}".format(eventid, programid), [['name', 'text'], ['startnum', 'real'],['elo', 'real'],['prediction','real']])

    for participant in participants:
        id = participant['athlete_id']
        name = participant['athlete_title']
        startnum = participant['start_num']
        elo = select_elo(conn, id)
        if elo != None: 
            elo = elo[0]
        else:
            elo = 1000
        insert_table(conn, "EVENTe{}p{}".format(eventid, programid), "id, name, startnum, elo", "{},'{}','{}','{}'".format(id, name, startnum, elo))

    scores = select_athlete_elo_order_elo(conn, eventid, programid)
    
    i = 0
    for score in scores:
        insert_event_elo_rank(conn, score[0], (i + 1), eventid, programid)
        i += 1

def func(eventid, programid):
    create_event_table(eventid,programid)
    calculate_loss(eventid,programid)


def main():
    #predict_event(163568, 560518)
    # predict_event(163568, 560516)
    # predict_event(164182, 550795)
    # predict_event(163959, 550779)
    func(163482,547092)
    # pred = predict_event2(163482,547092 )

    func(163478, 546952)

main()