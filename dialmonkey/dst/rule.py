from collections import defaultdict

from ..component import Component


class BeliefStateTracker(Component):

    def __call__(self, dial):
        if dial.nlu:
            best_intent = 'inform'  # everything else will not be put into state as it's not something that should be
            # stored persistently

            d = defaultdict(list)
            for dai in dial.nlu:
                if dai.intent == best_intent and dai.slot:
                    d[dai.slot].append(dai)

            for slot, dai_list in d.items():
                if slot not in dial.state:
                    dial.state[slot] = dict()
                null_prob = 1
                for dai in dai_list:
                    null_prob -= dai.confidence
                if null_prob < 0:
                    null_prob = 0

                if len(dial.state[slot].keys()) == 0:
                    dial.state[slot][None] = round(null_prob, 7)
                else:
                    for key in dial.state[slot].keys():
                        dial.state[slot][key] = round(dial.state[slot][key] * null_prob, 7)

                for dai in dai_list:
                    if dai.value not in dial.state[slot]:
                        dial.state[slot][dai.value] = round(dai.confidence, 7)
                    else:
                        dial.state[slot][dai.value] = round(dial.state[slot][dai.value] + dai.confidence, 7)
        else:
            pass
            # dial.state.intent = None
        return dial
