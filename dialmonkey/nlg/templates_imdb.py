import json
import random

from ..da import DA
from ..component import Component


class IMBdNLG(Component):

    def load_templates(self, filename):
        with open(filename) as json_file:
            tmp = json.load(json_file)
        self.templates = []
        for k in [9, 2, 1]:
            for temp, values in tmp.items():
                da = DA.parse_cambridge_da(temp).dais
                length = len(da)
                if da[0].slot == 'success':
                    length = 2
                if length == k:
                    self.templates.append((da, values))

    def check_exact_template(self, dais, templ):
        unused_dais = dais[:]
        res = []
        for t in templ:
            with_same_intents = []
            for dai in unused_dais:
                if dai.intent == t.intent:
                    with_same_intents.append(dai)

            if t.slot is not None and t.slot[0] != '{':
                with_same_slots = []
                for dai in with_same_intents:
                    if dai.slot is not None and dai.slot == t.slot:
                        with_same_slots.append(dai)
                with_same_intents = with_same_slots

            if t.value is not None and t.value[0] != '{':
                with_same_values = []
                for dai in with_same_intents:
                    if dai.value is not None and dai.value == t.value:
                        with_same_values.append(dai)
                with_same_intents = with_same_values

            if len(with_same_intents) > 0:
                it = with_same_intents[0]
                unused_dais.remove(it)
                res.append(it)
            else:
                return []
        return res

    def find_values(self, dais, templ):
        res = {}
        for i in range(len(templ)):
            if templ[i].value is not None and templ[i].value[0] == '{':
                res[templ[i].value] = dais[i].value
        return res

    def check_for_match(self, dais):
        res = []
        i = 0
        while i < len(self.templates):
            template = self.templates[i]
            check = self.check_exact_template(dais, template[0])
            if len(check) > 0:
                d = self.find_values(check, template[0])
                string = str(random.choice(template[1]))
                for key, value in d.items():
                    string = string.replace(key, value)
                res.append(string)
                for c in check:
                    dais.remove(c)
            else:
                i += 1
        return res

    def process(self, dais):
        confirm = []
        ask = []
        other = []
        list_options = []
        for dia in dais:
            if dia.intent == 'confirm':
                confirm.append(dia)
            elif dia.intent == 'ask':
                ask.append(dia)
            elif dia.slot == 'list_options' or dia.slot == 'help':
                list_options.append(dia)
            else:
                other.append(dia)

        if len(confirm) > 0:
            self.current_response += random.choice(["Understood, ", "Ok, so ", "Got it, "])

            strings = self.check_for_match(confirm)
            self.current_response += ', '.join(strings)
            self.current_response += '.\n'

        if len(list_options) > 0:
            strings = self.check_for_match(list_options)
            self.current_response += '\n'.join(strings)

        if len(other) > 0:
            strings = self.check_for_match(other)
            self.current_response += ''.join(strings)

        if len(ask) > 0:
            strings = self.check_for_match(ask)
            self.current_response += ' '.join(strings)

    def __init__(self, config):
        super().__init__(config)
        self.load_templates(config['templates_file'])

    def __call__(self, dial):
        self.current_response = ''
        dais = dial.action.dais
        self.process(dais)

        dial.set_system_response(self.current_response)

        return dial