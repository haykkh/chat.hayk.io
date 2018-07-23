#!/usr/bin/env python3
"""
Flask & SocketIO based webapp that connects with a Slack workspace and carries messages between the two
(hayk (owner) talks from Slack, user talks from webapp)
"""

import os

from flask import Flask, render_template, request, Response
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room
from slackclient import SlackClient


#####################
#                   #
#       slack       #
#       setup       #
#                   #
#####################

# auth token
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
slack_client = SlackClient(SLACK_TOKEN)

# outgoing webhook token
SLACK_WEBHOOK_SECRET = os.environ.get('SLACK_WEBHOOK_SECRET')

# array of channels hayk has messaged in 
hayk_channels = []

def slack_send_message(channel_id, message):
    '''
    Sends a message to the specified channel from "rando"

    Arguments:
        channel_id {str}
        message {str}
    '''
    slack_client.api_call(
        "chat.postMessage",
        channel=channel_id,
        text=message,
        username="rando",
        icon_emoji=':taco:'
    )


def slack_create_channel(channel_id):
    '''
    Creates a channel with name: channel_id

    Arguments:
        channel_id {str} 
    '''
    slack_client.api_call(
        "channels.create",
        name='#' + str(channel_id)
    )

#####################
#                   #
#         end       #
#       slack       #
#       setup       #
#                   #
#####################


# flask app init
app = Flask(__name__)

app.config.update(dict(DEBUG=True))
app.config['SECRET_KEY'] = ';GSp:?4s_n&D'

# Setup cors headers to allow all domains
CORS(app)

# socketio init
socketio = SocketIO(app)


#####################
#                   #
#       flask       #
#       routes      #
#                   #
#####################

@app.route("/")
def index():
    return render_template('index.html')


@app.route('/slack', methods=['POST'])
def inbound():
    if request.form.get('token') == SLACK_WEBHOOK_SECRET:
        username = request.form.get('user_name')

        # prevent bot from sending its own messages over and over
        if username == 'hayk':
            channel = request.form.get('channel_name')
            text = request.form.get('text')[1:]

            print('hayk_channels: ' + str(hayk_channels))
            print('channel: ' + str(channel))

            # if hayk has never responded in this channel
            if channel not in hayk_channels:
                
                hayk_channels.append(channel)
                # emit a conection message
                socketio.emit('message', {'type': 'connection', 'usr': 'hayk', 'msg': ' has entered the room'}, room=channel)
            
            inbound_message = username + " in " + channel + " says: " + text
            print(inbound_message)
            sender = {'usr': username, 'channel': channel, 'msg': text}
            send_message(sender)

    return Response(), 200

#####################
#                   #
#       end         #
#       flask       #
#       routes      #
#                   #
#####################


#####################
#                   #
#     socketio      #
#     handlers      #
#                   #
#####################

@socketio.on('joined')
def joined():
    # cut room name length to 21 chars (slack channel name length limit)
    room = request.sid[:20]
    print(room + ' connected')
    join_room(room)

    # create a channel with 'name': room
    slack_create_channel(room)

    # notify hayk on slack that someone has joined
    slack_send_message(room, "Someone's here!")

    # emit a conection message
    socketio.emit('message', {'type': 'connection', 'usr': room[-4:], 'msg': ' has entered the room'}, room=room)


@socketio.on('disconnect')
def disconnect():
    room = request.sid[:20]
    leave_room(room)
    hayk_channels.remove(room)
    print('Client disconnected')


@socketio.on('send_message')
def send_message(message):

    # if 'usr' not specified (ie message sent by user from web app)
    if 'usr' not in message.keys():
        room = request.sid[:20]
        usr = room[-4:]
        slack_send_message(room, message['msg'])

    # else sent by hayk from slack
    else:
        room = message['channel']
        usr = message['usr']

    sender = {'type': 'new_message', 'usr': usr,
              'msg': message['msg'], 'room': room}

    print('sender: ' + str(sender))

    socketio.emit('message', sender, room=room)

#####################
#                   #
#       end         #
#     socketio      #
#     handlers      #
#                   #
#####################


if __name__ == "__main__":
    socketio.run(app)
