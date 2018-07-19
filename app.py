#!/usr/bin/env python3
"""
Documentation

See also https://www.python-boilerplate.com/flask
"""
import os

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room


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

@socketio.on('joined')
def joined():
    room = request.sid
    print(room + ' connected')
    join_room(room)
    socketio.emit('message', {'type': 'connection', 'usr': room[-4:], 'msg': ' has entered the room'}, room=room)

@socketio.on('disconnect')
def disconnect():
    room = request.sid
    leave_room(room)
    print('Client disconnected')

@socketio.on('send_message')
def send_message(message):
    room = request.sid
    print(message)
    socketio.emit('message', {'type': 'new_message', 'usr': room[-4:],'msg': message['msg']}, room=room)


if __name__ == "__main__":
    socketio.run(app)