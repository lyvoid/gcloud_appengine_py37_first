from flask import Flask
from config import config
from google.cloud import firestore

db = firestore.Client()

doc_ref = db.collection(u'users').document(u'alovelace')
doc_ref.set({
    u'first': u'Ada',
    u'last': u'Lovelace',
    u'born': 1815
})
#
# app = Flask(__name__)
# @app.route('/')
# def hello():
#     """Return a friendly HTTP greeting."""
#     return 'Hello World!'
#
#
# if __name__ == '__main__':
#     app.run(host='127.0.0.1', port=8080, debug=True)
