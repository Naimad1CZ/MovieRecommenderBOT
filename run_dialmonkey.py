#!/usr/bin/env python3

from dialmonkey.conversation_handler import ConversationHandler
from dialmonkey.utils import load_conf
from dialmonkey.conversation_handler import Dialogue
# use this import for testing
from server import *


class MyConversationHandler(object):
    def __init__(self, conf=None, dial=None):
        if conf is None:
            conf = load_conf("text_imdb.yaml")

        self.handler = ConversationHandler(conf)
        if dial is None:
            self.dial = Dialogue()
        else:
            self.dial = dial

    def interact(self, user_utterance):
        self.handler._init_components(self.dial)

        system_response, eod = self.handler.get_response(self.dial, user_utterance)

        return system_response, eod


def test_func():

    h = MyConversationHandler()
    utt = ['Hi', 'tooltip all', 'I would like movie with good rating', 'search', 'What is the plot?', 'Who is starring?', 'Who acted in the movie?', 'What is actor']
    i = 0
    eod = False

    while not eod:
        print('USR:', utt[i])
        (response, eod) = h.interact(utt[i])
        print('SYS:', response)
        i += 1

    print('total end')


def create_empty_storage():
    x = dict()
    #serialize(x)


def trial():
    #x = dict()
    #serialize(x)
    dialogue_storage = load_dialogue_storage_from_file()

    conf = load_conf("text_imdb.yaml")
    dialogue_storage["46543"] = Dialogue()
    conv_handler = MyConversationHandler(conf, dialogue_storage["46543"])
    system_response, eod = conv_handler.interact("czech very popular musical")
    x = 7
    dialogue_storage["46543"] = conv_handler.dial
    #serialize(dialogue_storage)


def main():
    h = MyConversationHandler()
    utt = ['Hi', 'tooltip all', 'I would like movie with good rating', 'search', 'What is the plot?',
           'Who is starring?', 'Who acted in the movie?', 'What is actor']

    eod = False

    while not eod:
        utterance = input('USER INPUT> ')
        (response, eod) = h.interact(utterance)
        print('SYSTEM:', response)

    print('end')


if __name__ == '__main__':
    main()
