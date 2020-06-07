from flask import Flask, render_template, request
from flask_mysqldb import MySQL

from utils import *
from setup import HOST_NAME, USER_NAME, USER_PASS, DB_NAME

app = Flask(__name__)
app.config['MYSQL_HOST'] = HOST_NAME
app.config["MYSQL_USER"] = USER_NAME
app.config['MYSQL_PASSWORD'] = USER_PASS
app.config['MYSQL_DB'] = DB_NAME
app.secret_key = 'MYSECRET_KEY'
mysql = MySQL(app)

@app.route('/')
def index():
    db = mysql.connection.cursor()
    db.execute("""SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = \'{}\'""".format(DB_NAME))
    data = db.fetchall() 
    _tables = []
    for tablenames in data:
        for tablename in tablenames:
            _tables.append(tablename)
    return render_template('index.html', tables = _tables)

@app.route('/AlumnoNuevo') 
def alumno_nuevo():
    return render_template('AlumnoNuevo.html')

@app.route('/AlumnoNuevoAgregado', methods = ['POST']) 
def alumno_nuevo_agregado():
    if request.method == 'POST':
        NombreCompleto = request.form['NombreCompleto']
        FechadeNacimiento = request.form['FechadeNacimiento']
        Beca = request.form['Beca']
        Grupo = request.form['Grupo']
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO Estudiante (nombre, fecha_de_nacimiento, beca, id_grupo) VALUES (\'{}\',\'{}\',{},{})'.format(NombreCompleto, FechadeNacimiento, Beca, Grupo))
        cur.connection.commit()
    return 'Enterado'

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
