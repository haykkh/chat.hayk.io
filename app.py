#!/usr/bin/env python3
"""
Documentation

See also https://www.python-boilerplate.com/flask
"""
import os

from flask import Flask, jsonify, render_template, request, Response
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room
from slackclient import SlackClient

#####################
#					#
#		slack 		#
#					#
#####################
					
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
slack_client = SlackClient(SLACK_TOKEN)
SLACK_WEBHOOK_SECRET = os.environ.get('SLACK_WEBHOOK_SECRET')

def slack_send_message(channel_id, message):
	slack_client.api_call(
		"chat.postMessage",
		channel=channel_id,
		text=message,
		username="rando",
		icon_emoji=':taco:'
		)

def slack_create_channel(channel_id):
	slack_client.api_call(
		"channels.create",
		name=channel_id
		)


app = Flask(__name__)

# See http://flask.pocoo.org/docs/latest/config/
app.config.update(dict(DEBUG=True))
app.config['SECRET_KEY'] = ';GSp:?4s_n&D'

# Setup cors headers to allow all domains
# https://flask-cors.readthedocs.io/en/latest/
CORS(app)

#socketio
socketio = SocketIO(app)

# Definition of the routes. Put them into their own file. See also
# Flask Blueprints: http://flask.pocoo.org/docs/latest/blueprints
@app.route("/")
def index():
    return render_template('index.html')

@app.route('/slack', methods=['POST'])
def inbound():
    if request.form.get('token') == SLACK_WEBHOOK_SECRET:
        username = request.form.get('user_name')
        if username == 'hayk':
            channel = request.form.get('channel_name')
            text = request.form.get('text')[1:]
            inbound_message = username + " in " + channel + " says: " + text
            print(inbound_message)
            sender = {'usr': username, 'channel': channel, 'msg': text}
            send_message(sender)
    return Response(), 200

@socketio.on('joined')
def joined():
    room = request.sid[:20]
    print(room + ' connected')
    join_room(room)
    slack_create_channel(room)
    socketio.emit('message', {'type': 'connection', 'usr': room[-4:], 'msg': ' has entered the room'}, room=room)

@socketio.on('disconnect')
def disconnect():
    room = request.sid[:20]
    leave_room(room)
    print('Client disconnected')

@socketio.on('send_message')
def send_message(message):
    if 'usr' not in message.keys():
        room = request.sid[:20]
        usr = room[-4:]
        slack_send_message(room, message['msg'])
    else:
        room = message['channel']
        usr = message['usr']
    print('message: ' + str(message))
    sender = {'type': 'new_message', 'usr': usr,'msg': message['msg'], 'room' : room}
    print('sender: ' + str(sender))
    socketio.emit('message', sender, room=room)


if __name__ == "__main__":
    socketio.run(app)