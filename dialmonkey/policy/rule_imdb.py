import collections

from ..component import Component
from ..da import DAI

from bs4 import BeautifulSoup
import requests
import json
import random
import asyncio


class IMBdPolicy(Component):

    def __init__(self, config=None):
        self.countries = {'au': 'Australia', 'at': 'Austria', 'by': 'Belarus', 'br': 'Brazil', 'cn': 'China',
                          'cz': 'Czech Republic', 'cshh': 'Czechoslovakia', 'fr': 'France', 'gr': 'Greece', 'hk': 'Hong Kong',
                          'is': 'Iceland', 'in': 'India', 'it': 'Italy', 'jp': 'Japan', 'nz': 'New Zealand',
                          'kp': 'North Korea', 'pl': 'Poland', 'ru': 'Russia', 'sk': 'Slovakia', 'kr': 'South Korea',
                          'es': 'Spain', 'ua': 'Ukraine', 'gb': 'United Kingdom', 'us': 'United States'}

    def __call__(self, dial):
        # the logic goes like: State contains just the things that user informed us about, i.e. his preferences.
        # things like hello(), deny() and request(something) are thing that we should react to immediately, so there is
        # no need to store them for later.

        if len(dial.nlu.dais) == 0:
            dial.action.append(DAI('dont_understand'))
            for prev_act in dial.previous_actions:
                if prev_act.intent == 'ask':
                    dial.action.append(DAI('inform', 'list_options', prev_act.slot))
                    dial.previous_actions = dial.action.dais[:]
                    return dial


        if len(dial.nlu.dais) == 1 and dial.nlu.dais[0].intent == 'hello':
            dial.action.append(DAI('hello'))  # otherwise just ignore it because user just gave some other info/request

        for dai in dial.nlu.dais:
            if dai.intent == 'bye':
                dial.action.append(DAI('bye'))
                dial.end_dialogue()
                return dial

        # confirm all the time what the user said
        for dai in dial.nlu.dais:
            if dai.intent == 'inform':
                if dai.slot == 'country':
                    dial.action.append(DAI('confirm', dai.slot, self.countries[dai.value]))
                elif dai.slot == 'keywords':
                    dial.action.append(DAI('confirm', dai.slot, dai.value.replace('+', ' ')))
                else:
                    dial.action.append(DAI('confirm', dai.slot, dai.value))

        # handling next_movie and start_again, which have very high priority
        for dai in dial.nlu.dais:
            if dai.intent == 'request':
                if dai.slot == 'next_movie':
                    succ = self.choose_next_movie(dial)
                    if not succ:
                        dial.action.append(DAI('inform', 'failure', 'next_movie'))
                        dial.previous_actions = dial.action.dais[:]
                        return dial
                    else:
                        dial.action.append(DAI('inform', 'success', 'next_movie'))
                        dial.action.append(DAI('inform', 'Title', dial.current_movie['Title']))
                        dial.action.append(DAI('inform', 'Url', dial.current_movie['Url']))
                        dial.previous_actions = dial.action.dais[:]
                        return dial
                elif dai.slot == 'start_again':
                    self.reset(dial.state, dial)
                    dial.action.append(DAI('inform', 'start_again'))
                    return dial

        for dai in dial.nlu.dais:
            if dai.intent == 'request':
                if dai.slot == 'movie_info':
                    if dial.current_movie is not None:
                        if dai.value is None:
                            dial.action.append(DAI('inform', 'Title', dial.current_movie["Title"]))
                            dial.action.append(DAI('inform', 'Year', dial.current_movie["Year"]))
                            dial.action.append(DAI('inform', 'Runtime', dial.current_movie["Runtime"]))
                            dial.action.append(DAI('inform', 'Genre', dial.current_movie["Genre"]))
                            dial.action.append(DAI('inform', 'Writer', dial.current_movie["Writer"]))
                            dial.action.append(DAI('inform', 'Director', dial.current_movie["Director"]))
                            dial.action.append(DAI('inform', 'Actors', dial.current_movie["Actors"]))
                            dial.action.append(DAI('inform', 'imdbRating', dial.current_movie["imdbRating"]))
                            dial.action.append(DAI('inform', 'Plot', dial.current_movie["Plot"]))
                        else:
                            dial.action.append(DAI('inform', dai.value, dial.current_movie[dai.value]))
                    else:
                        dial.action.append(DAI('inform', 'failure', 'cant_tell_movie_info'))
                elif dai.slot == 'help':
                    dial.action.append(DAI('inform', 'help'))
                elif dai.slot == 'list_options':
                    val = dai.value
                    if val is None:
                        did_ask = False
                        for prev_act in dial.previous_actions:
                            if prev_act.intent == 'ask':
                                did_ask = True
                                slot = prev_act.slot
                        if did_ask:
                            dial.action.append(DAI('inform', 'list_options', slot))
                        else:
                            val = 'all'

                    if val == 'all':
                        dial.action.append(DAI('inform', 'list_options', 'release_date'))
                        dial.action.append(DAI('inform', 'list_options', 'user_rating'))
                        dial.action.append(DAI('inform', 'list_options', 'num_votes'))
                        dial.action.append(DAI('inform', 'list_options', 'genre'))
                        dial.action.append(DAI('inform', 'list_options', 'runtime'))
                        dial.action.append(DAI('inform', 'list_options', 'group'))
                        dial.action.append(DAI('inform', 'list_options', 'country'))
                        dial.action.append(DAI('inform', 'list_options', 'with_cast_crew'))
                        dial.action.append(DAI('inform', 'list_options', 'keywords'))
                    elif val is not None:
                        dial.action.append(DAI('inform', 'list_options', val))

        # handling search, which have low priority
        for dai in dial.nlu.dais:
            if dai.intent == 'request':
                if dai.slot == 'search':
                    # check if there is no other request - if there is, do nothing as other request was probably meant
                    # and search was just unintentionally used keyword
                    cont = True
                    for action in dial.action.dais:
                        if action.intent == 'request':
                            cont = False
                            break
                    if not cont:
                        break

                    if len(dial.state) == 0:
                        dial.action.append(DAI('inform', 'failure', 'not_enough_info'))
                        break

                    succ = self.api_call_search_and_choose(dial)
                    if not succ:
                        self.reset(dial.state, dial)
                        dial.action.append(DAI('inform', 'failure', 'search'))
                        return dial
                    else:
                        dial.state.clear()
                        dial.action.append(DAI('inform', 'success', 'search'))
                        dial.action.append(DAI('inform', 'Title', dial.current_movie['Title']))
                        dial.action.append(DAI('inform', 'Url', dial.current_movie['Url']))

        for prev_act in dial.previous_actions:
            if prev_act.intent == 'ask':
                for dai in dial.nlu.dais:
                    if dai.intent == 'deny' or dai.intent == 'dont_care':
                        slot = prev_act.slot
                        if slot in ['release_date', 'user_rating', 'num_votes', 'runtime']:
                            if slot + '_from' not in dial.state:
                                dial.state[slot + '_from'] = dict()
                            dial.state[slot + '_from'][None] = 1
                            if slot + '_to' not in dial.state:
                                dial.state[slot + '_to'] = dict()
                            dial.state[slot + '_to'][None] = 1
                        elif slot == 'with_cast_crew':
                            if 'written_by' not in dial.state:
                                dial.state['written_by'] = dict()
                            dial.state['written_by'][None] = 1
                            if 'directed_by' not in dial.state:
                                dial.state['directed_by'] = dict()
                            dial.state['directed_by'][None] = 1
                            if 'starring' not in dial.state:
                                dial.state['starring'] = dict()
                            dial.state['starring'][None] = 1
                        else:
                            if slot not in dial.state:
                                dial.state[slot] = dict()
                            dial.state[slot][None] = 1

        requests_etc = False
        if dial.current_movie is not None:
            requests_etc = True
        for dai in dial.nlu.dais:
            if dai.intent == 'request' or dai.intent == 'hello':
                requests_etc = True
                break

        if not requests_etc:
            order = ['genre', 'release_date', 'user_rating', 'num_votes', 'runtime', 'country', 'with_cast_crew',
                     'group', 'keywords']
            asked = False
            for potential_slot in order:
                if potential_slot in ['release_date', 'user_rating', 'num_votes', 'runtime']:
                    do_ask = True
                    if potential_slot + '_from' in dial.state:
                        if any(w > 0.0 for w in dial.state[potential_slot + '_from'].values()):
                            do_ask = False
                    if potential_slot + '_to' in dial.state:
                        if any(w > 0.0 for w in dial.state[potential_slot + '_to'].values()):
                            do_ask = False
                    if do_ask:
                        dial.action.append(DAI('ask', potential_slot))
                        asked = True
                        break
                elif potential_slot == 'with_cast_crew':
                    do_ask = True
                    if 'written_by' in dial.state:
                        if any(w > 0.0 for w in dial.state['written_by'].values()):
                            do_ask = False
                    if 'directed_by' in dial.state:
                        if any(w > 0.0 for w in dial.state['directed_by'].values()):
                            do_ask = False
                    if 'starring' in dial.state:
                        if any(w > 0.0 for w in dial.state['starring'].values()):
                            do_ask = False
                    if do_ask:
                        dial.action.append(DAI('ask', potential_slot))
                        asked = True
                        break
                else:
                    do_ask = True
                    if potential_slot in dial.state:
                        if any(w > 0.0 for w in dial.state[potential_slot].values()):
                            do_ask = False
                    if do_ask:
                        dial.action.append(DAI('ask', potential_slot))
                        asked = True
                        break
            if not asked:
                # perform search
                succ = self.api_call_search_and_choose(dial)
                if not succ:
                    self.reset(dial.state, dial)
                    dial.action.append(DAI('inform', 'failure', 'search'))
                    return dial
                else:
                    dial.state.clear()
                    dial.action.append(DAI('inform', 'success', 'search'))
                    dial.action.append(DAI('inform', 'Title', dial.current_movie['Title']))
                    dial.action.append(DAI('inform', 'Url', dial.current_movie['Url']))

        dial.previous_actions = dial.action.dais[:]
        return dial

    def api_call_search_and_choose(self, dial):
        dial_state = dial.state
        first_dict = {}
        for slot, values in dial_state.items():
            if any(w > 0.1 for w in values.values()):
                first_dict[slot] = []
                for k, v in values.items():
                    if v > 0.1 and k is not None:
                        first_dict[slot].append(k)

        temp_dict = {}
        for slot, values in first_dict.items():
            if len(values) > 0:
                temp_dict[slot] = values

        better_list = []

        for slot in ['release_date']:
            if slot + '_from' in temp_dict.keys() and slot + '_to' in temp_dict.keys():
                tmp = slot + '=' + temp_dict[slot + '_from'][0] + '-01-01,' + temp_dict[slot + '_to'][0] + '-01-01'
                better_list.append(tmp)
            elif slot + '_from' in temp_dict.keys():
                tmp = slot + '=' + temp_dict[slot + '_from'][0] + '-01-01,'
                better_list.append(tmp)
            elif slot + '_to' in temp_dict.keys():
                tmp = slot + '=' + ',' + temp_dict[slot + '_to'][0] + '-01-01'
                better_list.append(tmp)

        for slot in ['user_rating', 'num_votes', 'runtime']:
            if slot + '_from' in temp_dict.keys() and slot + '_to' in temp_dict.keys():
                tmp = slot + '=' + temp_dict[slot + '_from'][0] + ',' + temp_dict[slot + '_to'][0]
                better_list.append(tmp)
            elif slot + '_from' in temp_dict.keys():
                tmp = slot + '=' + temp_dict[slot + '_from'][0] + ','
                better_list.append(tmp)
            elif slot + '_to' in temp_dict.keys():
                tmp = slot + '=' + ',' + temp_dict[slot + '_to'][0] + ''
                better_list.append(tmp)

        if 'genre' in temp_dict.keys():
            tmp = 'genres='
            for g in temp_dict['genre']:
                if len(tmp) > 7:
                    tmp += ','
                if g.startswith('not'):
                    tmp += '!' + g[4:]
                else:
                    tmp += g
            better_list.append(tmp)

        if 'group' in temp_dict.keys():
            tmp = 'groups='
            for g in temp_dict['group']:
                if len(tmp) > 7:
                    tmp += ','
                tmp += g
            better_list.append(tmp)

        if 'country' in temp_dict.keys():
            tmp = 'countries=' + temp_dict['country'][0]
            better_list.append(tmp)

        if 'keywords' in temp_dict.keys():
            tmp = 'keywords=' + temp_dict['keywords'][0]
            better_list.append(tmp)

        cast_crew = []
        for slot in ['written_by', 'directed_by', 'starring']:
            if slot in temp_dict.keys():
                for pers in temp_dict[slot]:
                    cast_crew.append(pers)

        if len(cast_crew) > 0:
            tmp = 'role='
            for person in cast_crew:
                try:
                    person_id, person_name = self.api_call_get_persons_id(person)
                    if len(tmp) > 5:
                        tmp += ','
                    tmp += person_id

                    for slot in ['written_by', 'directed_by', 'starring']:
                        if slot in temp_dict.keys():
                            if person in temp_dict[slot]:
                                idx = temp_dict[slot].index(person)
                                temp_dict[slot][idx] = person_name
                except:
                    pass
            better_list.append(tmp)

        url_mid = ''
        for item in better_list:
            if len(url_mid) > 0:
                url_mid += '&'
            url_mid += item

        try:
            movies, found_amount = self.api_call_get_search_results(url_mid, True)
        except Exception as e:
            return False

        # now filter them out
        filtered_movies = self.filter_result_movies(movies, temp_dict)

        res = filtered_movies
        # commenting this second try because I need to fullfill some timeout quota
        '''
        if len(filtered_movies) < 5 and found_amount == 30:
            try:
                another_movies, found_amount = self.api_call_get_search_results(url_mid, False)
            except:
                return False

            filtered_another_movies = self.filter_result_movies(another_movies, temp_dict)

            res = filtered_movies + filtered_another_movies
        else:
            res = filtered_movies
        '''

        if len(res) == 0:
            return False
        random_movie = random.choice(res)
        res.remove(random_movie)
        dial.searched_movies = res
        dial.current_movie = random_movie
        return True

    def api_call_get_persons_id(self, name):
        name = name.replace(' ', '+')
        url = "https://www.imdb.com/search/name/?name=" + name
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        scraped_persons = soup.find('h3', class_='lister-item-header')
        children = scraped_persons.findChildren("a", recursive=False)
        href = children[0]['href']
        person_id = href.split('/')[-1]
        person_name = children[0].string.strip()
        return person_id, person_name

    def api_call_get_search_results(self, url_mid, small_amount=True):
        if small_amount:
            url_end = '&view=simple&count=30'
        else:
            url_end = '&view=simple&count=100'
        url = "https://www.imdb.com/search/title/?" + url_mid + url_end
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        scraped_person_movies = soup.find_all('div', class_='col-title')
        ids = []
        for movie in scraped_person_movies:
            children = movie.findChildren("a", recursive=True)
            href = children[0]['href']
            id = href.split('/')[-2]
            ids.append(id)


        start = 0 if small_amount else 30
        end = 30 if small_amount else 100
        if len(ids) < end:
            end = len(ids)

        used_ids = []
        for i in range(start, end):
            used_ids.append(ids[i])

        movies = self.api_call_get_all_movies(used_ids)
        return movies, len(used_ids)

    async def api_call_get_movie_info(self, movie_id, i):
        try:
            url = "https://movie-database-alternative.p.rapidapi.com/"
            querystring = {"r": "json", "i": movie_id}

            headers = {
                "X-RapidAPI-Host": "movie-database-alternative.p.rapidapi.com",
                "X-RapidAPI-Key": "c81e8fe130msh2c89d4523a2dc5ap1f1c20jsn75f5629ba65c"
            }

            response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
            obj = json.loads(response.text)
            obj['Url'] = 'https://www.imdb.com/title/' + movie_id + '/'
            return obj
        except:
            return None

    def api_call_get_all_movies(self, movie_ids):
        loop = asyncio.get_event_loop()

        tasks = []

        for i in range(len(movie_ids)):
            task = asyncio.ensure_future(self.api_call_get_movie_info(movie_ids[i], i))
            tasks.append(task)

        group = asyncio.gather(*tasks)
        movies = loop.run_until_complete(group)

        movies = [m for m in movies if m is not None]
        return movies

    def filter_result_movies(self, movies, temp_dict):
        better_movies = []
        for m in movies:
            better_movies.append(collections.defaultdict(str, m))
        movies = better_movies

        real_movies = []
        for m in movies:
            if 'Type' in m.keys() and m['Type'] == 'movie':
                real_movies.append(m)

        correct_country_movies = []
        if 'country' in temp_dict.keys():
            country_code = temp_dict['country'][0]
            country_name = self.countries[country_code]
            for m in real_movies:
                movie_country = m['Country'].split(',')[0]
                if country_name == movie_country:
                    correct_country_movies.append(m)
        else:
            correct_country_movies = real_movies

        correct_written_by_movies = []
        if 'written_by' in temp_dict.keys():
            writers = temp_dict['written_by']
            for m in correct_country_movies:
                movie_writers = m['Writer'].split(', ')
                accept = True
                for w in writers:
                    if w not in movie_writers:
                        accept = False
                if accept:
                    correct_written_by_movies.append(m)
        else:
            correct_written_by_movies = correct_country_movies

        correct_directed_by_movies = []
        if 'directed_by' in temp_dict.keys():
            directors = temp_dict['directed_by']
            for m in correct_written_by_movies:
                movie_directors = m['Director'].split(', ')
                accept = True
                for w in directors:
                    if w not in movie_directors:
                        accept = False
                if accept:
                    correct_directed_by_movies.append(m)
        else:
            correct_directed_by_movies = correct_written_by_movies

        return correct_directed_by_movies

    def choose_next_movie(self, dial):
        if dial.current_movie is None or dial.searched_movies is None or len(dial.searched_movies) == 0:
            return False

        random_movie = random.choice(dial.searched_movies)
        dial.searched_movies.remove(random_movie)
        dial.current_movie = random_movie
        return True

    def reset(self, state, dial):
        # clear the state
        state.clear()
        dial.searched_movies = None
        dial.current_movie = None
        dial.previous_actions = []
