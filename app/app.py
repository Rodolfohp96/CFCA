from flask import Flask, render_template, request, session, redirect, url_for, make_response
from flask_mysqldb import MySQL
import datetime
from datetime import date
from app.utils import *
from app.setup import HOST_NAME, USER_NAME, USER_PASS, DB_NAME
from dotenv import load_dotenv
import pdfkit
import os

load_dotenv()

app = Flask(__name__, static_folder='assets')
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


@app.route('/pago', methods=['GET', 'POST'])
def get_pago():
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    db.execute("""SELECT Grupo.id, Grupo.nombre, count(Estudiante.id) FROM Grupo
                    JOIN Estudiante ON Grupo.id = Estudiante.id_grupo
                        GROUP BY Grupo.id""")
    _grupos = db.fetchall()
    db.execute("""SELECT count(id) FROM Estudiante""")
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
    return render_template('generarPago.html', info=_info)





@app.route('/nuevorecibol/<aid>/<id>', methods=['GET', 'POST'])
def get_nuevorecibol(aid,id):
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    msg = ""
    db.execute("""SELECT id, monto, metodo, concepto, fecha_pago, pagado
                                            FROM Transaccion WHERE id={}""".format(id))
    data = db.fetchone()
    noticia = "PAGADO"
    if data[5] == 0:
        noticia = "ADEUDO"
    db.execute("""SELECT 
                        Estudiante.nombre, 
                        Estudiante.fecha_de_nacimiento, 
                        Estudiante.beca,  
                        Grupo.nombre,
                        Grupo.id
                        FROM Estudiante JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                        WHERE Estudiante.id={}
                    """.format(aid))
    data1 = db.fetchall()[0]
    name = data1[0]
    age = gage(data1[1])
    beca = "{} %".format(data1[2])
    group = data1[3]
    student = {"name": name, "age": age, "beca": beca, "group": group, "group_id": data[4]}

    _info = {"msg": msg, "student": student, "id": aid, "aid": id, "data": data}



    return render_template('recibo.html', info=_info, noticia=noticia, id = aid)

@app.route('/generar_pdf', methods=['POST'])
def generar_pdf():
    data = request.json.get('info')  # Obtener los datos enviados desde el cliente

    # Generar el contenido HTML del PDF utilizando los datos recibidos
    contenido_html = render_template('recibo.html', info=data)

    # Generar el PDF utilizando pdfkit
    pdf = pdfkit.from_string(contenido_html, False)

    # Devolver el PDF como respuesta de la solicitud HTTP
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=recibo.pdf'
    return response

@app.route('/alumno/<aid>/nuevafactura/<id>', methods=['GET', 'POST'])
def get_nuevafactura(aid, id):
    if not check_login():
        return redirect(url_for('login'))
    msg = ""
    if request.method == 'POST':
        try:
            monto = float(request.form['monto'])
            metodo = request.form['metodo']
            if not metodo:
                metodo = " "
            concepto = request.form['concepto']
            limit = request.form['fechalimite']
            pagado = "TRUE" if request.form['pagado'] == '1' else "FALSE"
            inputs = [monto, metodo, concepto, limit, pagado]
            if fempties(inputs):
                raise ValueError("Error solidarity")
            db = mysql.connection.cursor()
            db.execute("""UPDATE Transaccion
                                SET monto={}, 
                                metodo=\"{}\",
                                concepto=\"{}\",
                                fecha_limite=\"{}\",
                                pagado={}
                                WHERE id={}
                            """.format(monto, metodo, concepto, limit, pagado, id))
            db.connection.commit()
            return redirect(url_for('get_student', id=aid))
        except ValueError:
            msg = "Ocurrió un error al agregar la informacón"
    db = mysql.connection.cursor()
    db.execute("""SELECT 
                        Estudiante.nombre, 
                        Estudiante.fecha_de_nacimiento, 
                        Estudiante.beca,  
                        Grupo.nombre,
                        Grupo.id
                        FROM Estudiante JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                        WHERE Estudiante.id={}
                    """.format(aid))
    datac = db.fetchall()[0]
    name = datac[0]
    age = gage(datac[1])
    beca = "{} %".format(datac[2])
    group = datac[3]
    studentsi = {"name": name, "age": age, "beca": beca, "group": group, "group_id": datac[4]}
    db.execute("""SELECT id, monto, metodo, concepto, fecha_limite, pagado
                        FROM Transaccion WHERE id={}""".format(id))
    data = db.fetchone()

    mes_actual = datetime.now().month
    anio_actual = datetime.now().year

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
        trans.append({"id": id_adeudo, "monto": monto, "metodo": metodo, "concepto": concepto, "limite": fecha_limite,
                      "pagado": pagado, "noticia": noticia})

    # Ejemplo de uso
    transaccion_original = data[1]
    print(data[1])
    total_con_recargo = calcular_recargo(transaccion_original, data[4])
    _info = {"msg": msg, "id": id, "aid": aid, "data": data, "trans": trans}
    fechahoy = date.today()
    return render_template('factura.html', info=_info, student=studentsi, fechahoy=fechahoy,
                           total_con_recargo=total_con_recargo)


def calcular_recargo(monto, fechalimite):
    fecha_actual = date.today()
    fecha_limite = fechalimite

    dias_atraso = (fecha_actual - fecha_limite).days

    if dias_atraso <= 10:
        return monto, 0
    elif dias_atraso <= 15:
        return monto + 100, 100
    elif dias_atraso <= 30:
        return monto + 50, 50
    else:
        meses_atraso = (dias_atraso + 1) // 30  # Obtener la cantidad de meses completos de atraso a partir del mes cumplido

        if meses_atraso >= 2:
            recargo = 50 + (meses_atraso - 1) * 50  # Restar 1 para no contar el primer mes de atraso (que ya está cubierto por el recargo inicial de 50)
        else:
            recargo = 50

        try:
            monto_float = float(monto)
            total_con_recargo = monto_float + recargo
            return total_con_recargo, recargo
        except ValueError:
            # Si monto no es un número válido, manejar el error o asignar un valor predeterminado
            return 0, 0  # Por ejemplo, asignar 0 como valor predeterminado


@app.route('/')
def index():
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    db.execute("""SELECT Grupo.id, Grupo.nombre, count(Estudiante.id) FROM Grupo
                    JOIN Estudiante ON Grupo.id = Estudiante.id_grupo
                        GROUP BY Grupo.id""")
    _grupos = db.fetchall()
    db.execute("""SELECT count(id) FROM Estudiante""")
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
    fechahoy = date.today()
    return render_template('index.html', info=_info, fechahoy = fechahoy)


@app.route('/busqueda', methods=['POST'])
def search_student():
    if not check_login():
        return redirect(url_for('login'))
    if request.method == 'POST':
        qu = request.form['query']
        db = mysql.connection.cursor()
        db.execute("""SELECT 
                            Estudiante.id,
                            Estudiante.nombre, 
                            T.deuda
                        FROM Estudiante 
                        LEFT JOIN (SELECT sum(monto) as deuda, id_estudiante
                                FROM Transaccion WHERE pagado=FALSE
                                GROUP BY id_estudiante) AS T
                        ON Estudiante.id=T.id_estudiante
                        WHERE Estudiante.nombre LIKE \'%{}%\'
                        """.format(qu))
        data = db.fetchall()
        _students = []
        for item in data:
            matricula = "mat{:05d}".format(item[0])
            deuda = "PAGADO"
            if item[2] is not None:
                deuda = "${:,.2f}".format(item[2])
            _students.append([item[0], matricula, item[1], deuda])
        nstud = len(_students)
        _info = {"query": qu, "students": _students, "num": nstud}
        return render_template('search_student.html', info=_info)


@app.route('/grupo/<gid>/AlumnoNuevo', methods=['POST', 'GET'])
def alumno_nuevo(gid):
    if not check_login():
        return redirect(url_for('login'))
    msg = ""
    if request.method == 'POST':
        try:
            NombreCompleto = request.form['NombreCompleto']
            FechadeNacimiento = request.form['FechadeNacimiento']
            Beca = int(request.form['Beca'])
            GrupoId = int(request.form['GrupoId'])
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
            MontoColegiatura = float(request.form['MontoColegiatura'])
            ModalidadColegiatura = int(request.form['ModalidadColegiatura'])
            inputs = [NombreCompleto, FechadeNacimiento, Beca, GrupoId, Tutor1Nombre, Tutor1Direccion, Tutor1Correo,
                      Tutor1Parentesco, Tutor1Telefono, Tutor2Nombre, Tutor2Direccion, Tutor2Correo, Tutor2Parentesco,
                      Tutor2Telefono, MontoColegiatura, ModalidadColegiatura]
            if fempties(inputs):
                raise ValueError("Error solidarity")
            cur = mysql.connection.cursor()
            cur.execute(
                'INSERT INTO Estudiante (nombre, fecha_de_nacimiento, beca, id_grupo) VALUES (\'{}\',\'{}\',{},{})'.format(
                    NombreCompleto, FechadeNacimiento, Beca, GrupoId))
            n = cur.lastrowid
            cur.execute(
                'INSERT INTO Contacto (nombre, parentesco, correo, telefono, direccion, id_estudiante) VALUES (\'{}\',\'{}\',\'{}\',\"{}\",\'{}\',{})'.format(
                    Tutor1Nombre, Tutor1Parentesco, Tutor1Correo, Tutor1Telefono, Tutor1Direccion, n))
            cur.execute(
                'INSERT INTO Contacto (nombre, parentesco, correo, telefono, direccion, id_estudiante) VALUES (\'{}\',\'{}\',\'{}\',\"{}\",\'{}\',{})'.format(
                    Tutor2Nombre, Tutor2Parentesco, Tutor2Correo, Tutor2Telefono, Tutor2Direccion, n))
            desc = 1 - Beca / 100
            if ModalidadColegiatura == 10:
                AdeudoTotal = MontoColegiatura * 10 * desc
                cur.execute(
                    'INSERT INTO Transaccion (monto, metodo, concepto, fecha_limite, pagado, id_estudiante) VALUES ({},\'{}\', \'{}\', \'{}\', {}, {})'.format(
                        AdeudoTotal, "", "Colegiatura completa", "2020-12-12", "FALSE", n))
            elif ModalidadColegiatura == 11:
                AdeudoTotal = MontoColegiatura * desc
                for nummes in range(1, 12):
                    concepto = "Mensualidad {}".format(nummes)
                    cur.execute(
                        'INSERT INTO Transaccion (monto, metodo, concepto, fecha_limite, pagado, id_estudiante) VALUES ({},\'{}\', \'{}\', \'{}\', {}, {})'.format(
                            AdeudoTotal, "", concepto, "2020-12-12", "FALSE", n))
            cur.connection.commit()
            return redirect(url_for('get_group', id=GrupoId))
        except ValueError:
            msg = "Ocurrió un error al agregar la información"
    _info = {"student": {"group": int(gid)}, "msg": msg}
    print(_info)
    return render_template('AlumnoNuevo.html', info=_info)


@app.route('/grupo/<id>', methods=['POST', 'GET'])
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
    _info = {"group_id": id, "group": data[0][0], "students": _students, "num": nstud}
    return render_template('group.html', info=_info)


@app.route('/alumno/<id>', methods=['POST', 'GET'])
def get_student(id):
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    db.execute("""SELECT 
                    Estudiante.nombre, 
                    Estudiante.fecha_de_nacimiento, 
                    Estudiante.beca,
                    Estudiante.matricula,
                    Estudiante.password,  
                    Grupo.nombre,
                    Grupo.id
                    FROM Estudiante JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                    WHERE Estudiante.id={}
                """.format(id))
    data = db.fetchall()[0]
    name = data[0]
    age = gage(data[1])
    beca = "{} %".format(data[2])
    matricula = data[3]
    password = data[4]
    group = data[5]
    student = {"name": name, "age": age, "beca": beca, "group": group, "group_id": data[6], "matricula":data[3],"password":data[4]}
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
    db.execute(
        "SELECT id, monto, metodo, concepto, fecha_limite, pagado FROM Transaccion WHERE id_estudiante={}".format(id))
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
        trans.append({"id": id_adeudo, "monto": monto, "metodo": metodo, "concepto": concepto, "limite": fecha_limite,
                      "pagado": pagado, "noticia": noticia})
    _info = {"student_id": id, "student": student, "acon": acon, "bcon": bcon, "trans": trans}
    return render_template('student.html', info=_info)


@app.route('/editar_alumno/<id>', methods=['POST', 'GET'])
def edit_student(id):
    if not check_login():
        return redirect(url_for('login'))
    msg = ""
    if request.method == 'POST':
        try:
            nombre = request.form['nombre']
            id_grupo = int(request.form['idgrupo'])
            nac = request.form['nacimiento']
            if not nac:
                raise ValueError("Error solidarity")
            beca = int(request.form['beca'])
            acnom = request.form['acnom']
            acid = int(request.form['acid'])
            acmail = request.form['acmail']
            acparen = request.form['acparen']
            actel = request.form['actel']
            acdir = request.form['acdir']
            bcnom = request.form['bcnom']
            bcid = int(request.form['bcid'])
            bcmail = request.form['bcmail']
            bcparen = request.form['bcparen']
            bctel = request.form['bctel']
            bcdir = request.form['bcdir']
            inputs = [nombre, id_grupo, nac, beca, acnom, acid, acmail, acparen, actel, acdir, bcnom, bcid, bcmail,
                      bcparen, bctel, bcdir]
            if fempties(inputs):
                raise ValueError("Error solidarity")
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
                        telefono=\"{}\",  
                        direccion=\"{}\"
                        WHERE id={}
                    """.format(acnom, acparen, acmail, actel, acdir, acid))
            db.execute("""UPDATE Contacto
                        SET nombre=\"{}\",
                        parentesco=\"{}\",
                        correo=\"{}\",
                        telefono=\"{}\",  
                        direccion=\"{}\"
                        WHERE id={}
                    """.format(bcnom, bcparen, bcmail, bctel, bcdir, bcid))
            db.connection.commit()
            return redirect(url_for('get_student', id=id))
        except ValueError:
            msg = "Ocurrió un error al insertar la información"
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
    _info = {"msg": msg, "student_id": id, "student": student, "acon": acon, "bcon": bcon, "acid": acid, "bcid": bcid}
    return render_template('edit_student.html', info=_info)


@app.route('/grupo/<gid>/eliminar_alumno/<id>', methods=['GET', 'POST'])
def delete_student(gid, id):
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    db.execute("DELETE FROM Estudiante WHERE id = {}".format(id))
    db.connection.commit()
    return redirect(url_for('get_group', id=gid))


@app.route('/alumno/<aid>/nuevo_adeudo', methods=['POST', 'GET'])
def add_adeudo(aid):
    if not check_login():
        return redirect(url_for('login'))
    msg = ""
    if request.method == 'POST':
        try:
            monto = float(request.form['monto'])
            metodo = request.form['metodo']
            if not metodo:
                metodo = " "
            concepto = request.form['concepto']
            limit = request.form['fechalimite']
            pagado = "TRUE" if request.form['pagado'] == '1' else "FALSE"
            inputs = [monto, metodo, concepto, limit, pagado]
            if fempties(inputs):
                raise ValueError("Error solidarity")
            db = mysql.connection.cursor()
            db.execute("""INSERT INTO Transaccion (monto, metodo, concepto, fecha_limite, pagado, id_estudiante)
                            VALUES ({}, \"{}\", \"{}\", \"{}\", {}, {})
                        """.format(monto, metodo, concepto, limit, pagado, aid))
            db.connection.commit()
            return redirect(url_for('get_student', id=aid))
        except ValueError:
            msg = "Ocurrió un error al agregar la informacón"
    _info = {"aid": aid, "msg": msg}
    return render_template('nuevo_adeudo.html', info=_info)


@app.route('/alumno/<aid>/editar_adeudo/<id>', methods=['POST', 'GET'])
def edit_pago(aid, id):
    if not check_login():
        return redirect(url_for('login'))
        # Inicializar la variable msg con un valor predeterminado
    msg = ""
    if request.method == 'POST':
        try:
            monto = float(request.form['monto'])
            metodo = request.form['metodo']
            if not metodo:
                metodo = " "
            concepto = request.form['concepto']
            limit = request.form['fechalimite']
            pagado = "TRUE" if request.form['pagado'] == '1' else "FALSE"
            inputs = [monto, metodo, concepto, limit, pagado]
            if fempties(inputs):
                raise ValueError("Error solidarity")
            db = mysql.connection.cursor()
            db.execute("""UPDATE Transaccion
                            SET monto={}, 
                            metodo=\"{}\",
                            concepto=\"{}\",
                            fecha_limite=\"{}\",
                            pagado={}
                            WHERE id={}
                        """.format(monto, metodo, concepto, limit, pagado, id))
            db.connection.commit()
            return redirect(url_for('get_student', id=aid))
        except ValueError:
            msg = "Ocurrió un error al agregar la informacón"
    db = mysql.connection.cursor()
    db.execute("""SELECT id, monto, metodo, concepto, fecha_limite, pagado
                    FROM Transaccion WHERE id={}""".format(id))
    data = db.fetchone()
    _info = {"msg": msg, "id": id, "aid": aid, "data": data}
    return render_template('edit_adeudo.html', info=_info)



@app.route('/alumno/<aid>/pagar/<id>', methods=['POST', 'GET'])
def edit_pagon(aid, id):
    if not check_login():
        return redirect(url_for('login'))
    # Inicializar la variable msg con un valor predeterminado
    msg = ""
    _info = {"msg": msg, "id": id, "aid": aid, "data1": None}

    db = mysql.connection.cursor()
    db.execute("""SELECT id, monto, metodo, concepto, fecha_limite, pagado
                        FROM Transaccion WHERE id={}""".format(id))
    data = db.fetchone()
    # Ejemplo de uso
    transaccion_original = data[1]

    total_con_recargo = calcular_recargo(transaccion_original, data[4])
    fechahoy = date.today()

    if request.method == 'POST':
        try:
            monto = float(total_con_recargo[0])
            metodo = request.form['metodo']
            if not metodo:
                metodo = " "
            concepto = data[3]
            fecha_pago = fechahoy
            pagado = "TRUE"
            inputs = [monto, metodo, concepto, fecha_pago, pagado]
            if fempties(inputs):
                raise ValueError("Error solidarity")
            db = mysql.connection.cursor()
            db.execute("""UPDATE Transaccion
                            SET monto={}, 
                            metodo=\"{}\",
                            concepto=\"{}\",
                            fecha_pago=\"{}\",
                            pagado={}
                            WHERE id={}
                        """.format(monto, metodo, concepto, fecha_pago, pagado, id))
            db.connection.commit()
            return redirect(url_for('get_nuevorecibo', aid=aid, id = id))
        except ValueError:
            msg = "Ocurrió un error al agregar la información"

            db = mysql.connection.cursor()
            db.execute("""SELECT id, monto, metodo, concepto, fecha_pago, pagado
                                    FROM Transaccion WHERE id={}""".format(id))
            data1 = db.fetchone()

            _info = {"msg": msg, "id": id, "aid": aid, "data1": data1}

    return render_template('recibo1.html', info=_info)





@app.route('/alumno/<aid>/eliminar_adeudo/<id>', methods=['GET', 'POST'])
def delete_adeudo(aid, id):
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    db.execute("DELETE FROM Transaccion WHERE id = {}".format(id))
    db.connection.commit()
    return redirect(url_for('get_student', id=aid))



@app.route('/alumnoV/<id>', methods=['POST', 'GET'])
def get_studentV(id):
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    db.execute("""SELECT 
                    Estudiante.nombre, 
                    Estudiante.fecha_de_nacimiento, 
                    Estudiante.beca,
                    Estudiante.matricula,
                    Estudiante.password,  
                    Grupo.nombre,
                    Grupo.id
                    FROM Estudiante JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                    WHERE Estudiante.id={}
                """.format(id))
    data = db.fetchall()[0]
    name = data[0]
    age = gage(data[1])
    beca = "{} %".format(data[2])
    matricula = data[3]
    password = data[4]
    group = data[5]
    student = {"name": name, "age": age, "beca": beca, "group": group, "group_id": data[6], "matricula":data[3],"password":data[4]}
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
    db.execute(
        "SELECT id, monto, metodo, concepto, fecha_limite, pagado FROM Transaccion WHERE id_estudiante={}".format(id))
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
        trans.append({"id": id_adeudo, "monto": monto, "metodo": metodo, "concepto": concepto, "limite": fecha_limite,
                      "pagado": pagado, "noticia": noticia})
    _info = {"student_id": id, "student": student, "acon": acon, "bcon": bcon, "trans": trans}
    fechahoy = date.today()
    return render_template('studentView.html', info=_info, fechahoy=fechahoy)



if __name__ == "__main__":
    app.run()
