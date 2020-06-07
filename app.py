from flask import Flask, render_template
from flask_mysqldb import MySQL

from utils import *
from setup import HOST_NAME, USER_NAME, USER_PASS, DB_NAME

app = Flask(__name__)
app.config['MYSQL_HOST'] = HOST_NAME
app.config["MYSQL_USER"] = USER_NAME
app.config['MYSQL_PASSWORD'] = USER_PASS
app.config['MYSQL_DB'] = DB_NAME

mysql = MySQL(app)

@app.route('/')
def index():
    db = mysql.connection.cursor()
    db.execute("""SELECT Grupo.id, Grupo.nombre, count(Estudiante.id) FROM grupo
                    JOIN Estudiante ON Grupo.id = Estudiante.id_grupo
                        GROUP BY Grupo.id""")
    _grupos = db.fetchall()
    db.execute("""SELECT count(id) FROM estudiante""")
    numestud = db.fetchall()[0][0]
    numgrupo = len(_grupos)
    db.execute("""SELECT sum(monto) FROM Transaccion WHERE pagado=TRUE""")
    totganado = "${:,.2f}".format(db.fetchall()[0][0])
    db.execute("""SELECT sum(monto) FROM Transaccion WHERE pagado=FALSE""")
    totadeudos = "${:,.2f}".format(db.fetchall()[0][0])
    _info = {   
        "numestud": numestud,
        "grupos": _grupos,
        "numgrupos": numgrupo,
        "totganado": totganado,
        "totadeudo": totadeudos
    }
    print(_info)
    return render_template('index.html', info = _info)

@app.route('/grupo/<id>', methods = ['POST', 'GET'])
def get_group(id):
    db = mysql.connection.cursor()
    db.execute("""SELECT 
                        Grupo.nombre,
                        Estudiante.id,
                        Estudiante.nombre, 
                        Estudiante.fecha_de_nacimiento, 
                        Estudiante.beca 
                    FROM Estudiante JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                    WHERE id_grupo = \'{}\'""".format(id))
    data = db.fetchall()
    _students = []
    for item in data:
        matricula = "A{:06d}".format(item[1])
        age = gage(item[3])
        _students.append([matricula, item[2], age, item[4]])
    nstud = len(_students)
    _info = {"group": data[0][0], "students": _students, "num": nstud}
    return render_template('group.html', info = _info)
     

if __name__ == '__main__':
    app.run(port = 3000, debug = True)
