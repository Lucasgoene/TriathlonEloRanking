

import sqlite3
import sys
import traceback


class Race:
    def __init__(self, name, num, specifications, categories, eventid, programid, program_name, date):
        self.name = name
        self.eventid = eventid
        self.specifications = specifications
        self.categories = categories
        self.programid = programid
        self.program_name = program_name
        self.date = date
        self.event_num = num

    def __str__(self):
        return f'EVENT:({self.eventid}) - {self.name} PROGRAM:({self.programid})'


class AthleteELO:
    def __init__(self, id, name, elo, races_count, country, last_race="", races=[], elo_per_race=[]):
        self.id = id
        self.name = name
        self.elo = elo
        self.races_count = races_count
        self.country = country
        self.last_race = last_race
        self.races = races
        self.elo_per_race = elo_per_race

    def __empty__(self):
        self.id = 0
        self.name = ""
        self.elo = 0
        self.races_count = 0

    def __str__(self):
        return f'ID:({self.id}) - {self.name} (ELO:{self.elo}) in {self.races_count} races (last: {self.last_race}) - [seq] {self.elo_per_race} [seq-dates] {self.races}'

    def update_elo(self, new_elo, date):
        self.elo = new_elo
        self.races.append(date)
        self.elo_per_race.append(new_elo)
        self.last_race = date
        if(len(list(self.races)) != self.races_count + 1): print("error") #print(str(len(self.races)) + "  " + str(self.races_count))
        return self

    def add_race(self):
        self.races_count = self.races_count + 1
        return self

    def store_athlete(self, conn):
        conn.cursor()
        sql = "UPDATE ELO SET ELO = ?, counted_races = ?, last_race = ?, races_sequence = ?, elo_sequence = ? WHERE athlete_id == ? "
        try:
            conn.execute(sql, (self.elo, self.races_count, self.last_race, str(", ".join(map(str,self.races))), str(", ".join(map(str,self.elo_per_race))), self.id))
            conn.commit()
        except sqlite3.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Input values " + print(self))
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))