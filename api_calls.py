import requests

def get_all_races(key):
    header = {"apikey":key}

    all_data = []
    fetch = True
    last_page = 100
    page = 1

    while page <= last_page:
        res = requests.get("https://api.triathlon.org/v1/events?page={}&per_page=1000&order=desc".format(page), headers=header)
        last_page = res.json()['last_page']
        data = res.json()['data']

        all_data.extend(data)
        page += 1

    return all_data

def get_all_programs(key, id):
    header = { "apikey": key }
    res = requests.get("https://api.triathlon.org/v1/events/{}/programs".format(id), headers=header)

    return res.json()['data']

def get_results(key, eventid, programid):
    header = { "apikey": key }
    res = requests.get("https://api.triathlon.org/v1/events/{}/programs/{}/results".format(eventid, programid), headers=header)

    return res.json()['data']['results']

def get_participants(key, eventid, programid):
    header = { "apikey": key }
    res = requests.get("https://api.triathlon.org/v1/events/{}/programs/{}/entries".format(eventid, programid), headers=header)

    return res.json()['data']['entries']