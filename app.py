from flask import Flask
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config["MYSQL_USER"] = 'admin'
app.config['MYSQL_PASSWORD'] = 'adminpass'
app.config['MYSQL_DB'] = 'escueladb'

mysql = MySQL(app)

@app.route('/')
def index():
    return 'Hello world!'

if __name__ == '__main__':
    app.run(port = 3000, debug = True)