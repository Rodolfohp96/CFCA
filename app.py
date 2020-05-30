from flask import Flask, render_template
from flask_mysqldb import MySQL

from setup import HOST_NAME, USER_NAME, USER_PASS, DB_NAME

app = Flask(__name__)
app.config['MYSQL_HOST'] = HOST_NAME
app.config["MYSQL_USER"] = USER_NAME
app.config['MYSQL_PASSWORD'] = USER_PASS
app.config['MYSQL_DB'] = DB_NAME

mysql = MySQL(app)

@app.route('/')
def index():
    db =mysql.connection.cursor()
    db.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \'{}\''.format(DB_NAME))
    data = db.fetchall() 
    _tables = []
    for tablenames in data:
        for tablename in tablenames:
            _tables.append(tablename)
    return render_template('index.html', tables = _tables)


if __name__ == '__main__':
    app.run(port = 3000, debug = True)
