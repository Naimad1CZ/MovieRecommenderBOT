#!/usr/bin/env python3

from .dialogue import Dialogue
from .utils import dynload_class
from .component import Component


class ConversationHandler(object):
    """A helper class that calls the individual dialogue system components and thus
    runs the whole dialogue. Its behavior is defined by the config file, the contents
    of which are passed in the constructor."""

    def __init__(self, config):
        self.config = config

        self._load_components()
        self._reset()

    def _init_components(self, dial: Dialogue):
        for component in self.components:
            dial = component.init_dialogue(dial)

    def get_response(self, dial: Dialogue, user_utterance: str):
        is_ok = True
        dial.set_user_input(user_utterance)
        # run the dialogue pipeline (all components from the config)
        for component in self.components:
            dial = component(dial)
        if dial['system'] is None or len(dial['system']) == 0:
            is_ok = False
        system_response = dial['system']
        dial.end_turn()
        eod = dial.eod or\
                ('break_words' in self.config and any([kw in user_utterance for kw in self.config['break_words']]))
        return system_response, not is_ok or eod

    def _reset(self):
        self.iterations = 1
        self.history = []

    def _load_components(self):
        self.components = []
        if 'components' not in self.config:
            return
        for comp in self.config['components']:
            if isinstance(comp, dict):  # component has some configuration options (key=name, value=options)
                comp_name, comp_params = next(iter(comp.items()))
            else:  # component has no configuration options
                comp_name, comp_params = comp, None
            component_cls = dynload_class(comp_name)
            if component_cls is None:
                pass
            else:
                component = component_cls(comp_params)
                assert isinstance(component, Component),\
                    'Provided component has to inherit from the abstract class components.Component'
                self.components.append(component)
