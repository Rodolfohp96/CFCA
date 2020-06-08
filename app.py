from flask import Flask, render_template, request, session, redirect, url_for
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

# Login
def check_login():
    try:
        logged = session['loggedin']
        return True
    except KeyError:
        return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if check_login():
        return redirect(url_for('index'))
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        db = mysql.connection.cursor()
        db.execute("""SELECT id, username FROM Account 
                        WHERE username=\"{}\" AND password =\"{}\" """.format(username, password))
        account = db.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            return redirect(url_for('index'))
        else:
            msg = "Usuario o contraseña incorrecto"
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not check_login():
        return redirect(url_for('login'))
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

@app.route('/AlumnoNuevo', methods = ['POST', 'GET']) 
def alumno_nuevo():
    if not check_login():
        return redirect(url_for('login'))
    return render_template('AlumnoNuevo.html')

@app.route('/AlumnoNuevoAgregado', methods = ['POST']) 
def alumno_nuevo_agregado():
    if not check_login():
        return redirect(url_for('login'))
    if request.method == 'POST':
        NombreCompleto = request.form['NombreCompleto']
        FechadeNacimiento = request.form['FechadeNacimiento']
        Beca = request.form['Beca']
        GrupoId = request.form['GrupoId']
        Tutor1Nombre = request.form['Tutor1Nombre']
        Tutor1Direccion = request.form['Tutor1Direccion']
        Tutor1Correo = request.form['Tutor1Correo']
        Tutor1Parentesco = request.form['Tutor1Parentesco']
        Tutor1Telefono = request.form['Tutor1Telefono']
        Tutor2Nombre = request.form['Tutor2Nombre']
        Tutor2Direccion = request.form['Tutor2Direccion']
        Tutor2Correo = request.form['Tutor2Correo']
        Tutor2Parentesco = request.form['Tutor2Parentesco']
        Tutor2Telefono = request.form['Tutor2Telefono']
        AdeudoTotal = request.form['AdeudoNuevo']
        CantidadTransacciones = request.form['CantidadTransacciones']
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO Estudiante (nombre, fecha_de_nacimiento, beca, id_grupo) VALUES (\'{}\',\'{}\',{},{})'.format(NombreCompleto, FechadeNacimiento, Beca, GrupoId))
        n = cur.lastrowid
        cur.execute('INSERT INTO Contacto (nombre, parentesco, correo, telefono, direccion, id_estudiante) VALUES (\'{}\',\'{}\',\'{}\',{},\'{}\',{})'.format(Tutor1Nombre, Tutor1Parentesco, Tutor1Correo, Tutor1Telefono, Tutor1Direccion, n))
        cur.execute('INSERT INTO Contacto (nombre, parentesco, correo, telefono, direccion, id_estudiante) VALUES (\'{}\',\'{}\',\'{}\',{},\'{}\',{})'.format(Tutor2Nombre, Tutor2Parentesco, Tutor2Correo, Tutor2Telefono, Tutor2Direccion, n))
        cur.execute('INSERT INTO Transaccion (monto, metodo, concepto, fecha_limite, pagado, id_estudiante) VALUES ({},\'{}\', \'{}\', \'{}\', {}, {})'.format(AdeudoTotal, "", "colegiatura", "2020-12-12", "FALSE", n))
        cur.connection.commit()
    return redirect(url_for('get_grupo', id=GrupoId))

@app.route('/grupo/<id>', methods = ['POST', 'GET'])
def get_group(id):
    if not check_login():
        return redirect(url_for('login'))
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
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    db.execute("""SELECT 
                    Estudiante.nombre, 
                    Estudiante.fecha_de_nacimiento, 
                    Estudiante.beca,  
                    Grupo.nombre,
                    Grupo.id
                    FROM Estudiante JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                    WHERE Estudiante.id={}
                """.format(id))
    data = db.fetchall()[0]
    name = data[0]
    age = gage(data[1])
    beca = "{} %".format(data[2])
    group = data[3]
    student = {"name": name, "age": age, "beca": beca, "group": group, "group_id": data[4]}
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
    db.execute("SELECT id, monto, metodo, concepto, fecha_limite, pagado FROM Transaccion WHERE id_estudiante={}".format(id))
    tdata = db.fetchall()
    trans = []
    for item in tdata:
        id_adeudo = item[0]
        monto = "${:,.2f}".format(item[1])
        metodo = item[2]
        concepto = item[3]
        fecha_limite = item[4]
        pagado = item[5]
        noticia = "PAGADO"
        if item[5] == 0:
            noticia = "ADEUDO"
        trans.append({"id": id_adeudo, "monto": monto, "metodo": metodo, "concepto": concepto, "limite": fecha_limite, "pagado": pagado, "noticia": noticia})
    _info = { "student_id": id, "student": student, "acon": acon, "bcon": bcon, "trans": trans}
    print(_info)
    return render_template('student.html', info=_info)

@app.route('/editar_alumno/<id>', methods = ['POST', 'GET'])
def edit_student(id):
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    db.execute("""SELECT 
                    Estudiante.nombre, 
                    Estudiante.fecha_de_nacimiento, 
                    Estudiante.beca,  
                    Grupo.id
                    FROM Estudiante JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                    WHERE Estudiante.id={}
                """.format(id))
    data = db.fetchall()[0]
    name = data[0]
    nac = data[1]
    beca = data[2]
    group = data[3]
    print("Group:",group)
    student = {"name": name, "nac": nac, "beca": beca, "group": group}
    db.execute("""SELECT
                    nombre, parentesco, correo, telefono, direccion, id
                    FROM Contacto WHERE id_estudiante={}""".format(id))
    cdata = db.fetchall()
    acon = ["", "", "", "", "", ""]
    bcon = ["", "", "", "", "", ""]
    for i in range(len(cdata)):
        if i == 0:
            acon = cdata[i]  
        if i == 1:
            bcon = cdata[i]
    acid = acon[-1]
    bcid = bcon[-1]
    _info = { "student_id": id, "student": student, "acon": acon, "bcon": bcon, "acid": acid, "bcid": bcid}
    return render_template('edit_student.html', info=_info)
    
@app.route('/actualizar_alumno/<id>/<acid>/<bcid>', methods =['POST', 'GET'])
def actualizar(id, acid, bcid):
    if not check_login():
        return redirect(url_for('login'))
    if request.method == 'POST':
        nombre = request.form['nombre']
        id_grupo = int(request.form['idgrupo'])
        nac = request.form['nacimiento']
        beca = int(request.form['beca'])
        acnom = request.form['acnom']
        acmail = request.form['acmail']
        acparen = request.form['acparen']
        actel = int(request.form['actel'])
        acdir = request.form['acdir']
        bcnom = request.form['bcnom']
        bcmail = request.form['bcmail']
        bcparen = request.form['bcparen']
        bctel = int(request.form['bctel'])
        bcdir = request.form['bcdir']
        db = mysql.connection.cursor()
        db.execute("""UPDATE Estudiante
                    SET nombre=\"{}\",
                    fecha_de_nacimiento=\"{}\",
                    beca={},
                    id_grupo={} WHERE id={}
                """.format(nombre, nac, beca, id_grupo, id))
        db.execute("""UPDATE Contacto
                    SET nombre=\"{}\",
                    parentesco=\"{}\",
                    correo=\"{}\",
                    telefono={},  
                    direccion=\"{}\"
                    WHERE id={}
                """.format(acnom, acparen, acmail, actel, acdir, acid))
        db.execute("""UPDATE Contacto
                    SET nombre=\"{}\",
                    parentesco=\"{}\",
                    correo=\"{}\",
                    telefono={},  
                    direccion=\"{}\"
                    WHERE id={}
                """.format(bcnom, bcparen, bcmail, bctel, bcdir, bcid))
        db.connection.commit()
        return redirect(url_for('get_student', id=id))

@app.route('/grupo/<gid>/eliminar_alumno/<id>', methods = ['GET', 'POST'])
def delete_student(gid, id):
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    db.execute("DELETE FROM Estudiante WHERE id = {}".format(id))
    db.connection.commit()
    return redirect(url_for('get_group', id=gid))

@app.route('/alumno/<aid>/editar_adeudo/<id>', methods = ['POST', 'GET'])
def edit_pago(aid, id):
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    db.execute("""SELECT id, monto, metodo, concepto, fecha_limite, pagado
                    FROM Transaccion WHERE id={}""".format(id))
    data = db.fetchone()
    _info = {"aid": aid, "data": data}
    return render_template('edit_adeudo.html', info=_info)

@app.route('/actualizar_adeudo/<id>', methods = ['POST'])
def update_contact(id):
    if not check_login():
        return redirect(url_for('login'))
    if request.method == 'POST':
        monto = float(request.form['monto'])
        metodo = request.form['metodo']
        concepto = request.form['concepto']
        limit = request.form['fechalimite']
        print(request.form['pagado'])
        pagado = "TRUE" if request.form['pagado'] == '1' else "FALSE"
        print("Pagado", pagado)
        db = mysql.connection.cursor()
        db.execute("""UPDATE Transaccion
                        SET monto={}, 
                        metodo=\"{}\",
                        concepto=\"{}\",
                        fecha_limite=\"{}\",
                        pagado={}
                        WHERE id={}
                    """.format(monto, metodo, concepto, limit, pagado, id))
        db.execute("SELECT id_estudiante FROM Transaccion WHERE id={}".format(id))
        id_estud = db.fetchone()[0]
        db.connection.commit()
        return redirect(url_for('get_student', id=id_estud))

@app.route('/alumno/<aid>/eliminar_adeudo/<id>', methods = ['GET', 'POST'])
def delete_adeudo(aid, id):
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    db.execute("DELETE FROM Transaccion WHERE id = {}".format(id))
    db.connection.commit()
    return redirect(url_for('get_student', id=aid))

if __name__ == '__main__':
    app.run(port = 3000, debug = True)
