import os
import sys
import pickle
import json

import requests
from flask import Flask, request
from run_dialmonkey import MyConversationHandler
from dialmonkey.conversation_handler import Dialogue
from dialmonkey.utils import load_conf

app = Flask(__name__)
conf = load_conf("text_imdb.yaml")


def serialize(dialogue_storage):
    res = dict()
    for key, value in dialogue_storage.items():
        res[key] = value.get_serializable_obj()
    with open('storage.obj', 'wb') as f:
        pickle.dump(res, f)


def load_dialogue_storage_from_file():
    with open('storage.obj', 'rb') as f:
        loaded_dict = pickle.load(f)
    res = dict()
    for key, value in loaded_dict.items():
        d = Dialogue()
        d.load_from_serializable(value)
        res[key] = d
    return res


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            log('didnt verified :(')
            return "Verification token mismatch", 403
        log('verified')
        return request.args["hub.challenge"], 200

    log('Hello worlds was displayed')
    return "Hello world 2", 200


@app.route('/', methods=['POST'])
def webhook():
    # endpoint for processing incoming messaging events
    try:
        dialogue_storage = load_dialogue_storage_from_file()

        data = request.get_json()

        if data["object"] == "page":
            for entry in data["entry"]:
                for messaging_event in entry["messaging"]:
                    if messaging_event.get("message"):  # someone sent us a message
                        try:
                            sender_id = messaging_event["sender"]["id"]  # the facebook ID of the person sending you the message

                            if sender_id not in dialogue_storage.keys():
                                log('completely new customer')
                                log(sender_id)
                                for k, v in dialogue_storage.items():
                                    log(k)

                                    log(v.current_movie)
                                    log(v.history)
                                    log(v.state)

                                    log('-')
                                dialogue_storage[sender_id] = None
                            if dialogue_storage[sender_id] is None:
                                dialogue_storage[sender_id] = Dialogue()
                                log('creating new dialogue for sender ' + sender_id)

                            conv_handler = MyConversationHandler(conf, dialogue_storage[sender_id])
                            message_text = messaging_event["message"]["text"]  # the message's text
                            system_response, eod = conv_handler.interact(message_text)

                            if eod:
                                # removing unnecessary resources
                                log('removing unnecessary resources from sender ' + sender_id)
                                del dialogue_storage[sender_id]
                            else:
                                dialogue_storage[sender_id] = conv_handler.dial

                            reply = system_response
                            send_message(sender_id, str(reply))
                        except Exception as e:
                            log(messaging_event.get("message"))
                            log(e)
                            send_message(sender_id, str("Sorry! I didn't get that."))
        serialize(dialogue_storage)
        return "ok", 200
    except:
        log('oh f...')


def send_message(recipient_id, message_text):
    #log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    if len(message_text) >= 2000:
        first = message_text[:1696]
        last = message_text[1696:]
        send_message(recipient_id, first)
        send_message(recipient_id, last)
        return

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print(str(message))
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
