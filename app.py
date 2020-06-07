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
    return render_template('index.html', info = _info)

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
                        T.deuda
                    FROM Estudiante 
                    JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                    LEFT JOIN (SELECT sum(monto) as deuda, id_estudiante
                            FROM Transaccion WHERE pagado=FALSE
                            GROUP BY id_estudiante) AS T
                    ON Estudiante.id=T.id_estudiante
                    WHERE id_grupo = \'{}\'
                    """.format(id))
    data = db.fetchall()
    _students = []
    for item in data:
        matricula = "mat{:05d}".format(item[1])
        deuda = "PAGADO"
        if item[3] is not None:
            deuda = "${:,.2f}".format(item[3])
        _students.append([item[1], matricula, item[2], deuda])
    nstud = len(_students)
    _info = {"group": data[0][0], "students": _students, "num": nstud}
    return render_template('group.html', info = _info)
     
@app.route('/alumno/<id>', methods = ['POST', 'GET'])
def get_student(id):
    db = mysql.connection.cursor()
    db.execute("""SELECT 
                    Estudiante.nombre, 
                    Estudiante.fecha_de_nacimiento, 
                    Estudiante.beca,  
                    Grupo.nombre
                    FROM Estudiante JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                    WHERE Estudiante.id={}
                """.format(id))
    data = db.fetchall()[0]
    name = data[0]
    age = gage(data[1])
    beca = "{} %".format(data[2])
    group = data[3]
    student = {"name": name, "age": age, "beca": beca, "group": group}
    db.execute("""SELECT
                    nombre, parentesco, correo, telefono, direccion
                    FROM Contacto WHERE id_estudiante={}""".format(id))
    cdata = db.fetchall()
    acon = ["", "", "", "", ""]
    bcon = ["", "", "", "", ""]
    for i in range(len(cdata)):
        if i == 0:
            acon = cdata[i]  
        if i == 1:
            bcon = cdata[i]
    db.execute("SELECT monto, metodo, fecha_limite, pagado FROM Transaccion WHERE id_estudiante={}".format(id))
    tdata = db.fetchall()
    trans = []
    for item in tdata:
        monto = "${:,.2f}".format(item[0])
        metodo = item[1]
        fecha_limite = item[2]
        pagado = item[3]
        noticia = "PAGADO"
        if item[3] == 0:
            noticia = "ADEUDO"
        trans.append({"monto": monto, "metodo": metodo, "limite": fecha_limite, "pagado": pagado, "noticia": noticia})
    _info = { "student_id": id, "student": student, "acon": acon, "bcon": bcon, "trans": trans}
    print(_info)
    return render_template('student.html', info=_info)

if __name__ == '__main__':
    app.run(port = 3000, debug = True)
