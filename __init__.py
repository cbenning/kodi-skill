
from adapt.intent import IntentBuilder
from os.path import dirname, join

from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger
import requests
import json
from fuzzywuzzy import fuzz
# pip install fuzzywuzzy
from functools import reduce

__author__ = 'cbenning'

LOGGER = getLogger(__name__)

class KodiSkill(MycroftSkill):

    URL_PATTERN = "{0}://{1}:{2}/{3}"
    KODI_PATH = "jsonrpc"
    DEFAULT_PAYLOAD = {"jsonrpc": "2.0", "id": 1}
    DEFAULT_HEADERS = {'Content-Type': 'application/json'}

    def __init__(self):
        super(KodiSkill, self).__init__(name="KodiSkill")
        self.protocol = self.config['protocol']
        self.host = self.config['host']
        self.port = self.config['port']
        self.url = self.URL_PATTERN.format(self.protocol, self.host, self.port, self.KODI_PATH)
        self.similarity = self.config['similarity_threshold_percentage']

    def initialize(self):
        self.load_vocab_files(join(dirname(__file__), 'vocab', self.lang))
        self.load_regex_files(join(dirname(__file__), 'regex', self.lang))
        intent = IntentBuilder("WatchMovieIntent").require(
            "WatchKeyword").require("MovieTitle").build()
        self.register_intent(intent, self.handle_intent)

    def handle_intent(self, message):
        try:
            movie = message.metadata.get("MovieTitle").lower()

            movie = self.get_movie(movie)
            if movie is None:
                self.speak("I cannot find that movie")
            else:
                self.speak(self.play(movie['movieid'],'movieid'))

        except Exception as e:
            LOGGER.error("Error: {0}".format(e))

    def get_movies(self):
        payload = self.DEFAULT_PAYLOAD
        payload["method"] = "VideoLibrary.GetMovies"
        payload["params"] = {'properties': ['resume']}
        r = requests.post(self.url,
                          data=json.dumps(payload),
                          headers=self.DEFAULT_HEADERS)
        ## TODO error handling
        return r.json()['result']['movies']

    def get_movie(self, movie_title):
        movies = self.get_movies()
        matches = [
            {
                'match':fuzz.partial_ratio(movie_title, movie['label']),
                'movie':movie
            }
            for movie in movies ]
        movie = reduce(lambda a, b: a if a['match'] > b['match'] else b, matches)
        #TODO parameterize match
        if(movie['match'] < 75): return None
        return movie['movie']

    def play(self, contentid, type):
        payload = self.DEFAULT_PAYLOAD
        payload["method"] = "Player.Open"
        payload["params"] = {'item': {type:contentid}}
        r = requests.post(self.url,
                          data=json.dumps(payload),
                          headers=self.DEFAULT_HEADERS)
        ## TODO error handling
        return r.json()['result']

    def get_shows(self):
        payload = self.DEFAULT_PAYLOAD
        payload["method"] = "VideoLibrary.GetTVShows"
        r = requests.post(self.url,
                          data=json.dumps(payload),
                          headers=self.headers)
        ## TODO error handling
        return r.json()['result']['tvshows']

    def get_show(self, show_title):
        shows = self.get_shows()
        matches = [
            {
                'match':fuzz.partial_ratio(show_title, show['label']),
                'show':show
            }
            for show in shows ]
        show = reduce(lambda a, b: a if a['match'] > b['match'] else b, matches)
        #TODO parameterize match
        if(show['match'] < 75): return None
        return show['show']

    def get_show_episodes(self, tvshowid):
        payload = self.DEFAULT_PAYLOAD
        payload["method"] = "VideoLibrary.GetEpisodes"
        payload["params"] = {'tvshowid': tvshowid,
                             'properties': ['lastplayed', 'resume', 'episode']}
        r = requests.post(self.url,
                          data=json.dumps(payload),
                          headers=self.DEFAULT_HEADERS)
        ## TODO error handling
        return r.json()['result']['episodes']

    def get_episode_details(self, episodeid):
        payload = self.DEFAULT_PAYLOAD
        payload["method"] = "VideoLibrary.GetEpisodeDetails"
        payload["params"] = {'episodeid': episodeid,
                             'properties': ['lastplayed', 'resume' ]}
        r = requests.post(self.url,
                          data=json.dumps(payload),
                          headers=self.headers)
        #TODO error handling

        # return r.json()['result']['episodes']
        return r.json()


    def stop(self):
        pass

    def __api_error(self, e):
        LOGGER.error("Error: {0}".format(e))
        if e._triggering_error.code == 401:
            self.speak_dialog('not.paired')


def create_skill():
    return KodiSkill()