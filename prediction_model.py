import datetime
import math
import time
from db_calls import create_connection, create_table, insert_event_elo_rank, insert_prediction, insert_table, select_athlete_elo_order_elo, select_elo, select_elo_athlete, select_elo_race_date
from api_calls import get_all_programs, get_all_races, get_participants, get_results

from dotenv import load_dotenv
import os

from utils import isDateBefore

load_dotenv()

api_key = os.getenv('API_KEY')

def create_event_table(eventid, programid, race_date):
    conn = create_connection('storage.db')
    participants = get_participants(api_key, eventid, programid)

    create_table(conn, "EVENTe{}p{}".format(eventid, programid), [['name', 'text'], ['startnum', 'real'],['elo', 'real'],['elo_rank','real'], ['prediction','real']])

    for participant in participants:
        id = participant['athlete_id']
        name = participant['athlete_title']
        name = name.replace(r"'", r"")
        startnum = participant['start_num']
        elo = select_elo_race_date(conn, id, race_date)
        if elo != None: 
            elo = elo[0]
        else:
            elo = 1000
        if(id == 130354): print(elo)
        insert_table(conn, "EVENTe{}p{}".format(eventid, programid), "id, name, startnum, elo", "{},'{}','{}','{}'".format(id, name, startnum, elo))

def predict_event2(eventid, programid):
    # conn = create_connection('storage.db')
    # scores = get_race_table_by_ELO(conn, eventid, programid)
    
    predictors = {}

    predictors = elo_rank(predictors, eventid, programid)
    # predictors = elo_delta_since(predictors, '2022-8-22') #Form

    return predictors

def calculate_loss(eventid, programid, race_date):
    f = open("results.txt", "a")
    f.write("w1, w2, d, loss, num_athletes, specification, category")
    f.close()
    results = get_results(api_key, eventid, programid)
    result_by_id = {result['athlete_id'] : result['position'] for result in results}

    bestloss = 1000000000000000000
    bestloss_pair = ['0.0', '0.0']
    bestloss_days = 1
    for days in range(0, 100, 1):
        predictors = {}
        predictors = elo_rank(predictors, eventid, programid)
        predictors = elo_delta_since(predictors, race_date, days) #Form
        for w1 in range(0, 11, 1):
            w1 = 0.1 * w1
            for w2 in range(0, 1001, 1):
                w2 = 0.001 * w2
                prediction_scores = {id : (w1 * predictors[id][0] - w2 * predictors[id][1]) for id in predictors.keys()}
                prediction_order = {k: v for k, v in sorted(prediction_scores.items(), key=lambda item: item[1])}

                i = 1
                loss = 0
                for id in prediction_order.keys():
                    if id not in result_by_id.keys(): continue
                    if(result_by_id[id] == 'DNF' or result_by_id[id] == 'LAP' or result_by_id[id] == 'DSQ' or result_by_id[id] == 'DNS'):
                        result = i
                    else:
                        result = int(result_by_id[id])
                    loss += math.pow((result - i),2)
                    i += 1
                
                if(loss < bestloss):
                    bestloss = loss
                    bestloss_pair = [str(round(w1, 1)), str(round(w2, 4))]
                    bestloss_days = days
                
                # print("w1:{} w2:{} - LOSS: {}".format(str(round(w1, 2)), str(round(w2, 2)), loss))
        
    
    print("[BEST] w1:{} w2:{} d:{} - LOSS: {} TYPE:".format(bestloss_pair[0], bestloss_pair[1], bestloss_days, bestloss))
    f = open("results.txt", "a")
    f.write("{},{},{},{},{}")
    f.close()
    #predict(bestloss_pair[0], bestloss_pair[1], bestloss_days, eventid, programid, race_date)

def predict(w1, w2, days, eventid, programid, race_date):
    conn = create_connection('storage.db')
    predictors = {}
    predictors = elo_rank(predictors, eventid, programid)
    predictors = elo_delta_since(predictors, race_date, days) #Form

    prediction_scores = {id : (float(w1) * float(predictors[id][0]) - float(w2) * float(predictors[id][1])) for id in predictors.keys()}
    prediction_order = {k: v for k, v in sorted(prediction_scores.items(), key=lambda item: item[1])}
    
    i = 1

    for id in prediction_order.keys():
        insert_prediction(conn, id, i, eventid, programid)
        i += 1



#Feature creation
def elo_rank(predictors, eventid, programid):
    conn = create_connection('storage.db')
    scores = select_athlete_elo_order_elo(conn, eventid, programid)
    i = 0
    for score in scores:
        if(score[0] not in predictors.keys()):
            predictors[score[0]] = [(i + 1)]
        else:
            predictors[score[0]] = predictors[score[0]].append(i + 1)
        i += 1

    return predictors

def elo_delta_since(predictors, race_date, days):
    conn = create_connection('storage.db')

    for athlete_id in predictors.keys():
        athlete = select_elo_athlete(conn, athlete_id)
        if (athlete == []): predictors[athlete_id].append(0); continue
        races = list(athlete.races)
        since_date = datetime.datetime.strptime(race_date, '%Y-%m-%d')
        since_date = (since_date - datetime.timedelta(days=days))
        since_date = since_date.strftime('%Y-%m-%d')
        # races.reverse()
        i = 0
        j = 0
        for race in races:
            if (isDateBefore(race, race_date)):
                j += 1
            if (isDateBefore(race, str(since_date))):
                i += 1

        if(i == j and i == 0):
            predictors[athlete_id].append(0)
        else:
            predictors[athlete_id].append( float(athlete.elo_per_race[j]) - float(athlete.elo_per_race[i]) )
    
    return predictors