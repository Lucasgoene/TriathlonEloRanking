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
    cursor.execute("INSERT INTO ELO(name, counted_races, ELO, athlete_id, country) VALUES(?,?,?,?,?)", (athlete.name, athlete.races_count, athlete.elo, athlete.id, athlete.country))
    conn.commit()

def update_athlete_elo(conn, athlete: AthleteELO):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ELO(name, athlete_id, counted_races, ELO) VALUES(?,?,?,?)", (athlete.name, athlete.id, athlete.races, athlete.elo))
    conn.commit()

#READS

def select_all_races(conn, table):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM {}".format(table))
    
    return cursor.fetchall()

def select_all_races_where(conn, table, gender, category):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Races WHERE ( (program_name == 'Elite {}' OR program_name == 'Overall Male') AND specifications != '' AND categories LIKE \'%{}%\') ORDER BY date ASC".format(gender, category))
    
    return cursor.fetchall()

def get_elo_ranking(conn, id):
    cursor = conn.cursor()
    cursor.execute("SELECT ELO, FROM ELO WHERE (athlete_id =={}".format(id))

    return cursor.fetchall()

def get_elo_athlete(conn, id):
    cursor = conn.cursor()
    cursor.execute("SELECT name, ELO, counted_races, country FROM ELO WHERE (athlete_id == {})".format(id))

    return cursor.fetchall()