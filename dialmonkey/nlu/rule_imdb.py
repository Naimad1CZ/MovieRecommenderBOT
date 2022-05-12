from ..component import Component
from ..da import DAI

import re


class IMDbNLU(Component):

    def __init__(self, params):
        self.release_since = re.compile(r"(\d{4}) or newer")
        self.release_until = re.compile(r"(\d{4}) or older")

        self.rating_from1 = re.compile(r"(\d\.?\d?) or more")
        self.rating_from2 = re.compile(r"(\d\.?\d?) or better")
        self.rating_from3 = re.compile(r"better than (\d\.?\d?)")

        self.rating_to1 = re.compile(r"(\d\.?\d?) or less")
        self.rating_to2 = re.compile(r"(\d\.?\d?) or worse")
        self.rating_to3 = re.compile(r"worse than (\d\.?\d?)")

        self.genres = ["action", "adventure", "animation", "biography", "comedy", "crime", "documentary", "drama",
                       "family", "fantasy", "film-noir", "game-show", "history", "horror", "music", "musical",
                       "mystery", "news", "reality-tv", "romance", "sci-fi", "sport", "talk-show", "thriller", "war",
                       "western"]

        self.countries = {"australi": "au", "austri": "at", "belarus": "by", "brazil": "br", "chin": "cn",
                          "czechoslovak": "cshh", "czech": "cz", "france": "fr", "french": "fr", "greece": "gr",
                          "greek": "gr", "hong kong": "hk", "iceland": "is", "india": "in", "ital": "it", "japan": "jp",
                          "new zealand": "nz", "north korea": "kp", "poland": "pl", "polish": "pl", "russia": "ru",
                          "slovak": "sk", "south korea": "kr", "spain": "es", "spanish": "es", "ukrain": "ua",
                          "united kingdom": "gb", "british": "gb", "great britain": "gb", "unites states": "us",
                          "usa": "us"}

        self.keywords = re.compile(r'keyword[s]? "([^"]+)"')

    def __call__(self, dial):
        # put into lowercase
        dial.user = dial.user.lower() + ""

        sentence = dial.user.replace(',', ' ,').replace('.', ' .').replace('?', ' ?').replace('!', ' !')\
            .replace('\t', ' ').split(' ')
        sentence = [x for x in sentence if x != ""]

        if any([w in sentence for w in ['hello', 'hey', 'hi', 'ahoj']]):
            dial.nlu.append(DAI('hello'))
        if any([w in sentence for w in ['bye', 'goodbye', 'good bye', 'see ya', 'see you']]):
            dial.nlu.append(DAI('bye'))

        if "start again" in dial.user:
            dial.nlu.append(DAI('request', 'start_again'))
        if any([w in dial.user for w in ['search']]):
            dial.nlu.append(DAI('request', 'search'))
        if any([w in dial.user for w in ['help']]):
            dial.nlu.append(DAI('request', 'help'))
        if any([w in dial.user for w in ['tooltip', 'possibilities', 'possible', 'options']]):
            count = 0
            if any([w in dial.user for w in ['year', 'release', 'date', 'age']]):
                dial.nlu.append(DAI('request', 'list_options', 'release_date'))
                count += 1
            if any([w in dial.user for w in ['rating', 'score']]):
                dial.nlu.append(DAI('request', 'list_options', 'user_rating'))
                count += 1
            if any([w in dial.user for w in ['popular']]):
                dial.nlu.append(DAI('request', 'list_options', 'num_votes'))
                count += 1
            if any([w in dial.user for w in ['genre']]):
                dial.nlu.append(DAI('request', 'list_options', 'genre'))
                count += 1
            if any([w in dial.user for w in ['award', 'prize', 'reward']]):
                dial.nlu.append(DAI('request', 'list_options', 'group'))
                count += 1
            if any([w in dial.user for w in ['countr']]):
                dial.nlu.append(DAI('request', 'list_options', 'country'))
                count += 1
            if any([w in dial.user for w in ['keyword']]):
                dial.nlu.append(DAI('request', 'list_options', 'keywords'))
                count += 1
            if any([w in dial.user for w in ['directed', 'written', 'starred', 'with', 'actor', 'acting']]):
                dial.nlu.append(DAI('request', 'list_options', 'with_cast_crew'))
                count += 1
            if any([w in dial.user for w in ['runtime', 'time', 'length']]):
                dial.nlu.append(DAI('request', 'list_options', 'runtime'))
                count += 1
            if any([w in dial.user for w in ['everything', 'all']]):
                dial.nlu.append(DAI('request', 'list_options', 'all'))
                count += 1

            if count == 0:
                dial.nlu.append(DAI('request', 'list_options'))
        if any([w in dial.user for w in ['next', 'another']]):
            dial.nlu.append(DAI('request', 'next_movie'))
        if any([w in dial.user for w in ["tell me", "what", "what", "when", "who"]]) and len(dial.nlu.dais) == 0:
            if "detail" in dial.user:
                dial.nlu.append(DAI('request', 'movie_info'))
            if "release" in dial.user or "filmed" in sentence or "year" in sentence:
                dial.nlu.append(DAI('request', 'movie_info', 'Year'))
            if "length" in sentence or "time" in dial.user:
                dial.nlu.append(DAI('request', 'movie_info', 'Runtime'))
            if "genre" in sentence:
                dial.nlu.append(DAI('request', 'movie_info', 'Genre'))
            if "direct" in dial.user:
                dial.nlu.append(DAI('request', 'movie_info', 'Director'))
            if "write" in sentence or "wrote" in sentence or "written" in sentence:
                dial.nlu.append(DAI('request', 'movie_info', 'Writer'))
            if "play" in dial.user or "act" in dial.user or "starr" in dial.user:
                dial.nlu.append(DAI('request', 'movie_info', 'Actors'))
            if ("is" in sentence and "about" in sentence) or "plot" in sentence or "story" in sentence:
                dial.nlu.append(DAI('request', 'movie_info', 'Plot'))
            if "rated" in sentence or "rating" in sentence:
                dial.nlu.append(DAI('request', 'movie_info', 'imdbRating'))

        # affirm, deny, don't care
        if any([w in sentence for w in ['yes', 'yeah']]):
            dial.nlu.append(DAI('affirm'))
        if dial.user == "no" or dial.user == "nope" or dial.user == "not" or dial.user == "nah":
            dial.nlu.append(DAI('deny'))
        if any([w in dial.user for w in ["don't care", "dont care"]]) or dial.user == "none" or dial.user == "-":
            dial.nlu.append(DAI('dont_care'))

        # inform
        # release date
        if self.release_since.search(dial.user):
            dial.nlu.append(DAI('inform', 'release_date_from', self.release_since.search(dial.user).group(1)))
        elif self.release_until.search(dial.user):
            dial.nlu.append(DAI('inform', 'release_date_to', self.release_until.search(dial.user).group(1)))
        elif "pre-war" in sentence:
            dial.nlu.append(DAI('inform', 'release_date_to', '1939'))
        elif "very old" in dial.user:
            dial.nlu.append(DAI('inform', 'release_date_from', '1939'))
            dial.nlu.append(DAI('inform', 'release_date_to', '1990'))
        elif "old" in sentence:
            dial.nlu.append(DAI('inform', 'release_date_from', '1990'))
            dial.nlu.append(DAI('inform', 'release_date_to', '2005'))
        elif "aging" in sentence:
            dial.nlu.append(DAI('inform', 'release_date_from', '2005'))
            dial.nlu.append(DAI('inform', 'release_date_to', '2015'))
        elif "newest" in sentence:
            dial.nlu.append(DAI('inform', 'release_date_from', '2020'))
        elif "new" in sentence:
            dial.nlu.append(DAI('inform', 'release_date_from', '2015'))
            dial.nlu.append(DAI('inform', 'release_date_to', '2020'))

        # user rating
        if "best rating" in dial.user:
            dial.nlu.append(DAI('inform', 'user_rating_from', '9.0'))
        elif "great rating" in dial.user:
            dial.nlu.append(DAI('inform', 'user_rating_from', '8.0'))
        elif "good rating" in dial.user:
            dial.nlu.append(DAI('inform', 'user_rating_from', '6.5'))
            dial.nlu.append(DAI('inform', 'user_rating_to', '8.5'))
        elif "average rating" in dial.user:
            dial.nlu.append(DAI('inform', 'user_rating_from', '5.0'))
            dial.nlu.append(DAI('inform', 'user_rating_to', '7.0'))
        elif "mediocre rating" in dial.user:
            dial.nlu.append(DAI('inform', 'user_rating_from', '3.0'))
            dial.nlu.append(DAI('inform', 'user_rating_to', '5.5'))
        elif "bad rating" in dial.user:
            dial.nlu.append(DAI('inform', 'user_rating_to', '3.5'))
        elif "rating" in dial.user or "rated" in dial.user:
            if self.rating_from1.search(dial.user):
                dial.nlu.append(DAI('inform', 'user_rating_from', self.rating_from1.search(dial.user).group(1)))
            if self.rating_from2.search(dial.user):
                dial.nlu.append(DAI('inform', 'user_rating_from', self.rating_from2.search(dial.user).group(1)))
            if self.rating_from3.search(dial.user):
                dial.nlu.append(DAI('inform', 'user_rating_from', self.rating_from3.search(dial.user).group(1)))

            if self.rating_to1.search(dial.user):
                dial.nlu.append(DAI('inform', 'user_rating_to', self.rating_to1.search(dial.user).group(1)))
            if self.rating_to2.search(dial.user):
                dial.nlu.append(DAI('inform', 'user_rating_to', self.rating_to2.search(dial.user).group(1)))
            if self.rating_to3.search(dial.user):
                dial.nlu.append(DAI('inform', 'user_rating_to', self.rating_to3.search(dial.user).group(1)))

        # popularity - only using words
        if "extremely popular" in dial.user:
            dial.nlu.append(DAI('inform', 'num_votes_from', '100000'))
        elif "very popular" in dial.user:
            dial.nlu.append(DAI('inform', 'num_votes_from', '10000'))
            dial.nlu.append(DAI('inform', 'num_votes_to', '100000'))
        elif "quite popular" in dial.user:
            dial.nlu.append(DAI('inform', 'num_votes_from', '1000'))
            dial.nlu.append(DAI('inform', 'num_votes_to', '10000'))
        elif "average popular" in dial.user:
            dial.nlu.append(DAI('inform', 'num_votes_from', '100'))
            dial.nlu.append(DAI('inform', 'num_votes_to', '1000'))
        elif "not much popular" in dial.user:
            dial.nlu.append(DAI('inform', 'num_votes_from', '10'))
            dial.nlu.append(DAI('inform', 'num_votes_to', '100'))
        elif "unknown" in dial.user:
            dial.nlu.append(DAI('inform', 'num_votes_to', '10'))

        # genres
        for genre in self.genres:
            if genre in sentence:
                idx = sentence.index(genre)
                if idx >= 1 and (sentence[idx-1] == "no" or sentence[idx-1] == "not"):
                    dial.nlu.append(DAI('inform', 'genre', 'not_' + genre))
                else:
                    dial.nlu.append(DAI('inform', 'genre', genre))

        # groups
        if "won" in dial.user or "winner" in dial.user or "awarded" in dial.user or "received" in dial.user:
            if "oscar" in dial.user:
                dial.nlu.append(DAI('inform', 'group', 'oscar_winner'))
            if "emmy" in dial.user:
                dial.nlu.append(DAI('inform', 'group', 'emmy_winner'))
            if "golden globe" in dial.user:
                dial.nlu.append(DAI('inform', 'group', 'golden_globe_winner'))
            if "razzie" in dial.user:
                dial.nlu.append(DAI('inform', 'group', 'razzie_winner'))
        if "nominated" in dial.user or "nominee" in dial.user or "nomination" in dial.user:
            if "oscar" in dial.user:
                dial.nlu.append(DAI('inform', 'group', 'oscar_nominee'))
            if "emmy" in dial.user:
                dial.nlu.append(DAI('inform', 'group', 'emmy_nominee'))
            if "golden globe" in dial.user:
                dial.nlu.append(DAI('inform', 'group', 'golden_globe_nominee'))
            if "razzie" in dial.user:
                dial.nlu.append(DAI('inform', 'group', 'razzie_nominee'))

        # country
        for country, country_code in self.countries.items():
            if country in dial.user:
                dial.nlu.append(DAI('inform', 'country', country_code))
                # we can have only 1 country
                break

        # keywords - have to be in " " and comma separated
        if self.keywords.search(dial.user):
            res = self.keywords.search(dial.user).group(1).replace(' ', '+')
            dial.nlu.append(DAI('inform', 'keywords', res))

        # with (cast/crew)
        if "written by" in dial.user:
            idx = sentence.index("written")
            if idx + 2 < len(sentence):
                name = sentence[idx + 2]
                if idx + 3 < len(sentence) and sentence[idx + 3].isalpha() and len(sentence[idx + 3]) > 2 and not (sentence[idx + 3] == "and"):
                    name += " " + sentence[idx + 3]
                dial.nlu.append(DAI('inform', 'written_by', name))
        if "directed by" in dial.user:
            idx = sentence.index("directed")
            if idx + 2 < len(sentence):
                name = sentence[idx + 2]
                if idx + 3 < len(sentence) and sentence[idx + 3].isalpha() and len(sentence[idx + 3]) > 2 and not (sentence[idx + 3] == "and"):
                    name += " " + sentence[idx + 3]
            dial.nlu.append(DAI('inform', 'directed_by', name))
        if "starring" in sentence and not dial.user.startswith("who"):  # up to two actors with 1 or 2 word names
            idx = sentence.index("starring")

            if idx + 1 < len(sentence):
                idx += 1
                name = sentence[idx]
                idx += 1
                if idx < len(sentence) and sentence[idx].isalpha() and len(sentence[idx]) > 2 \
                        and not (sentence[idx] == "and"):
                    name += " " + sentence[idx]
                    idx += 1
                dial.nlu.append(DAI('inform', 'starring', name))

                if idx + 1 < len(sentence) and sentence[idx] == "and":
                    idx += 1
                    name = sentence[idx]
                    idx += 1
                    if idx < len(sentence) and sentence[idx].isalpha() and len(sentence[idx]) > 2 \
                            and not (sentence[idx] == "and"):
                        name += " " + sentence[idx]
                    dial.nlu.append(DAI('inform', 'starring', name))

        # runtime
        if "very short" in dial.user:
            dial.nlu.append(DAI('inform', 'runtime_to', '20'))
        elif "shorter" in dial.user:
            dial.nlu.append(DAI('inform', 'runtime_from', '50'))
            dial.nlu.append(DAI('inform', 'runtime_to', '80'))
        elif "short" in dial.user:
            dial.nlu.append(DAI('inform', 'runtime_from', '20'))
            dial.nlu.append(DAI('inform', 'runtime_to', '50'))
        elif "medium" in dial.user:
            dial.nlu.append(DAI('inform', 'runtime_from', '80'))
            dial.nlu.append(DAI('inform', 'runtime_to', '120'))
        elif "longer" in dial.user:
            dial.nlu.append(DAI('inform', 'runtime_from', '120'))
            dial.nlu.append(DAI('inform', 'runtime_to', '150'))
        elif "long" in dial.user:
            dial.nlu.append(DAI('inform', 'runtime_from', '150'))

        return dial
