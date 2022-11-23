import sqlite3
from sqlite3 import Error
from models import Race, AthleteELO


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

#WRITES

def insert_race(conn, race: Race):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Races(name, event_num, program_name, eventID, programID, specifications, categories, date) VALUES(?,?,?,?,?,?,?,?)", (race.name, race.event_num, race.program_name, race.eventid, race.programid, race.categories, race.specifications, race.date))
    conn.commit()

def insert_athlete_elo(conn, athlete: AthleteELO):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ELO(name, counted_races, ELO, athlete_id, country, races_sequence, elo_sequence) VALUES(?,?,?,?,?,?,?)", (athlete.name, athlete.races_count, athlete.elo, athlete.id, athlete.country, str(", ".join(map(str,athlete.races))), str(", ".join(map(str,athlete.elo_per_race)))))
    conn.commit()

def update_athlete_elo(conn, athlete: AthleteELO):
    cursor = conn.cursor()
    cursor.execute("UPDATE ELO SET ELO = ?, counted_races = ?, last_race = ?, races_sequence = ?, elo_sequence = ? WHERE athlete_id == ?", (athlete.elo, athlete.races_count, athlete.last_race, str(",".join(map(str,athlete.races))), str(",".join(map(str,athlete.elo_per_race))), athlete.id))
    conn.commit()

def insert_table(conn, name, attributes, values):
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO {}({}) VALUES({})".format(name, attributes, values))
    conn.commit()

def insert_event_elo_rank(conn, id, elo_rank, eventid, programid):
    cursor = conn.cursor()
    cursor.execute("UPDATE EVENTe{}p{} set elo_rank = {} WHERE id == {}".format(eventid, programid, elo_rank, id))
    conn.commit()

def insert_prediction(conn, id, position, eventid, programid):
    cursor = conn.cursor()
    cursor.execute("UPDATE EVENTe{}p{} prediction = {} where id = {}".format(eventid, programid, position, id))
    conn.commit()

#READS

def select_all(conn, table):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM {}".format(table))
    
    return cursor.fetchall()

def select_all_where(conn, table, gender, category):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM {} WHERE ( (program_name == 'Elite {}' OR program_name == 'Overall Male') AND specifications != '' AND categories LIKE \'%{}%\') ORDER BY date ASC".format(table, gender, category))
    
    return cursor.fetchall()

def select_elo(conn, id):
    cursor = conn.cursor()
    cursor.execute("SELECT ELO FROM ELO WHERE (athlete_id =={})".format(id))

    return cursor.fetchone()

def select_elo_athlete(conn, id):
    cursor = conn.cursor()
    cursor.execute("SELECT athlete_id, name, ELO, counted_races, country, last_race, races_sequence, elo_sequence FROM ELO WHERE (athlete_id == {})".format(id))
    res = cursor.fetchall()
    if(res == []):
        return []
    res_athlete = res[0]
    athlete = AthleteELO(res_athlete[0], res_athlete[1], res_athlete[2], res_athlete[3], res_athlete[4], res_athlete[5], str(res_athlete[6]).split(','), str(res_athlete[7]).split(','))
    return athlete

def select_athlete_elo_order_elo(conn, eventid, programid):
    cursor = conn.cursor()
    cursor.execute("SELECT id, elo FROM EVENTe{}p{} ORDER BY elo DESC".format(eventid, programid))
    
    return cursor.fetchall()

#TABLE

def create_table(conn, name, props):
    propstring = ""
    for prop in props:
        propstring += ", " + str(prop[0]) + " " + str(prop[1])

    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS {} (id integer PRIMARY KEY {})".format(name, propstring))
