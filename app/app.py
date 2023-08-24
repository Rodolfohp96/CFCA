from flask import Flask, render_template, request, session, redirect, url_for, make_response, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
import datetime
from app.utils import *
from app.setup import HOST_NAME, USER_NAME, USER_PASS, DB_NAME
from dotenv import load_dotenv
import pdfkit
import smtplib
import ssl
import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment
from io import BytesIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
#from flask_weasyprint import HTML, render_pdf


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

@app.route('/')
def index():
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    db.execute("""SELECT Grupo.id, Grupo.nombre, count(Estudiante.id) FROM Grupo
                    JOIN Estudiante ON Grupo.id = Estudiante.id_grupo
                        GROUP BY Grupo.id""")
    _grupos = db.fetchall()
    try:
        db.execute("""SELECT count(id) FROM Estudiante""")
        numestud = db.fetchall()[0][0]
    except IndexError:
        numestud = 0

    numgrupo = len(_grupos)

    try:
        db.execute("""SELECT sum(monto) FROM Transaccion WHERE pagado=TRUE""")
        totganado = "${:,.2f}".format(db.fetchall()[0][0])
    except (IndexError, TypeError):
        totganado = "$0.00"

    try:
        db.execute("""SELECT sum(monto) FROM Transaccion WHERE pagado=FALSE""")
        totadeudos = "${:,.2f}".format(db.fetchall()[0][0])
    except (IndexError, TypeError):
        totadeudos = "$0.00"
    _info = {
        "numestud": numestud,
        "grupos": _grupos,
        "numgrupos": numgrupo,
        "totganado": totganado,
        "totadeudo": totadeudos
    }
    fechahoy = date.today()
    db = mysql.connection.cursor()
    db.execute("""SELECT
            E.id AS estudiante_id,
            E.nombre AS estudiante_nombre,
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago,
            E.matricula,
            G.nombre AS nombre_grupo 
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
                    Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE""")
    data = db.fetchall()
    _students = []
    for item in data:
        _students.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    db.execute("""
            SELECT
                E.id AS estudiante_id,
                E.nombre AS estudiante_nombre,
                T.monto,
                T.metodo,
                T.concepto,
                T.fecha_pago,
                E.matricula,
                G.nombre AS nombre_grupo    
            FROM
                Estudiante AS E
            JOIN
                Transaccion AS T ON E.id = T.id_estudiante
            JOIN
                    Grupo AS G ON E.id_grupo = G.id
            WHERE
                T.pagado = TRUE
                AND T.fecha_pago >= CURDATE() - INTERVAL 15 DAY
                """)
    data1 = db.fetchall()
    _studentsquincena = []
    for item in data1:
        _studentsquincena.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    db.execute("""
            SELECT
            E.id AS estudiante_id,
            E.nombre AS estudiante_nombre,
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago,
            E.matricula,
            G.nombre AS nombre_grupo
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
                    Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
            """)
    data2 = db.fetchall()
    _studentsmensual = []
    for item in data2:
        _studentsmensual.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    db.execute("""SELECT
            E.id AS estudiante_id,
            E.nombre AS estudiante_nombre,
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago,
            E.matricula,
            G.nombre AS nombre_grupo
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
                    Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND DATE(T.fecha_pago) = CURDATE()""")
    data3 = db.fetchall()
    _studentsdia = []
    for item in data3:
        _studentsdia.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    db = mysql.connection.cursor()
    db.execute("""
                SELECT
                E.id AS estudiante_id,
                E.nombre AS estudiante_nombre,
                T.monto,
                T.metodo,
                T.concepto,
                T.fecha_pago,
                E.matricula,
                G.nombre AS nombre_grupo
            FROM
                Estudiante AS E
            JOIN
                Transaccion AS T ON E.id = T.id_estudiante
            JOIN
                Grupo AS G ON E.id_grupo = G.id
            WHERE
                T.pagado = TRUE
                AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
                AND T.metodo = 'Efectivo';
            """)
    data4 = db.fetchall()
    _studentsQuincenaefectivo = []
    for item in data4:
        _studentsQuincenaefectivo.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    db.execute("""
                SELECT
                    E.id AS estudiante_id,
                    E.nombre AS estudiante_nombre,
                    E.fecha_de_nacimiento,
                    E.beca,
                    E.matricula,
                    E.password,
                    T.monto,
                    T.metodo,
                    T.concepto,
                    T.fecha_pago,
                    G.nombre AS nombre_grupo
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
                    AND T.metodo = 'Transferencia'; 
            """)
    data5 = db.fetchall()
    _studentsQuincenaTransferencia = []
    for item in data5:
        _studentsQuincenaTransferencia.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    return render_template('index.html', info=_info, fechahoy=fechahoy, diario=_studentsdia, quincena=_studentsquincena, mes=_studentsmensual, efectivo=_studentsQuincenaefectivo, transferencia=_studentsQuincenaTransferencia )




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
def get_nuevorecibol(aid, id):
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
                        Grupo.id,
                        Estudiante.matricula
                        FROM Estudiante JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                        WHERE Estudiante.id={}
                    """.format(aid))
    data1 = db.fetchall()[0]
    name = data1[0]


    # Fetch contact data
    db.execute("SELECT nombre, parentesco, correo, telefono, direccion FROM Contacto WHERE id_estudiante = %s", (aid,))
    cdata = db.fetchall()

    acon = ["", "", "", "", ""]
    bcon = ["", "", "", "", ""]
    for i in range(len(cdata)):
        if i == 0:
            acon = cdata[i]
        if i == 1:
            bcon = cdata[i]

    # String for the first contact

    spc = f"Estimado (a) {acon[0]}, usted ha realizado el pago de la {data[3]} del alumno {data1[0]} con matrícula {data1[5]} el día {data[4]}.\n Adjuntamos su recibo de pago por este medio. \n Si requiere mayor información con gusto podemos antederle vía telefónica en los siguientes números de contacto: 7731003044, 7737325312 y 773 171 62 48. \n En un horario de 8:00 a 14:00 hrs. \n Seguimos a sus órdenes.\n Nuestro cupo es limitado.\n \n Saludos Cordiales. \n Colegio Felipe Carbajal Arcia \n Área de Administración"
    string_primer_contacto = spc
    # String for the second contact
    ssc = f"Estimado (a) {bcon[0]}, usted ha realizado el pago de la {data[3]} del alumno {data1[0]} con matrícula {data1[5]} el día {data[4]}.\n Adjuntamos su recibo de pago por este medio. \n Si requiere mayor información con gusto podemos antederle vía telefónica en los siguientes números de contacto: 7731003044, 7737325312 y 773 171 62 48. \n En un horario de 8:00 a 14:00 hrs. \n Seguimos a sus órdenes.\n Nuestro cupo es limitado.\n \n Saludos Cordiales. \n Colegio Felipe Carbajal Arcia \n Área de Administración"
    string_segundo_contacto = ssc

    pagotxt = data[3]

    correoinfo={"correo": acon[2], "conceptop": data[3], "textocorreo": spc}

    beca = "{} %".format(data1[2])
    group = data1[3]
    student = {"name": name, "beca": beca, "group": group, "group_id": data[4], "matricula": data1[5]}

    _info = {"msg": msg, "student": student, "id": aid, "aid": id, "data": data}

    return render_template('recibo.html', info=_info, noticia=noticia, id=aid, correoinfo=correoinfo)


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
                        Grupo.id,
                        Estudiante.matricula
                        FROM Estudiante JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                        WHERE Estudiante.id={}
                    """.format(aid))
    datac = db.fetchall()[0]
    name = datac[0]

    beca = "{} %".format(datac[2])
    group = datac[3]
    studentsi = {"name": name, "beca": beca, "group": group, "group_id": datac[4], "matricula": datac[5]}
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

    total_con_recargo = calcular_recargo(transaccion_original, data[4])
    _info = {"msg": msg, "id": id, "aid": aid, "data": data, "trans": trans}
    fechahoy = date.today()
    return render_template('factura.html', info=_info, student=studentsi, fechahoy=fechahoy,
                           total_con_recargo=total_con_recargo)


def calcular_recargo(monto, fechalimite):
    fecha_actual = date.today()
    fecha_limite = fechalimite

    if fecha_limite is not None:
        dias_atraso = (fecha_actual - fecha_limite).days
    else:
        # Handle the case where fecha_limite is None
        dias_atraso = 0  # or any other appropriate default value

    if dias_atraso <= 10:
        return monto, 0
    elif dias_atraso <= 15:
        return monto + 100, 100
    elif dias_atraso <= 30:
        return monto + 50, 50
    else:
        meses_atraso = (
                                   dias_atraso + 1) // 30  # Obtener la cantidad de meses completos de atraso a partir del mes cumplido

        if meses_atraso >= 2:
            recargo = 50 + (
                        meses_atraso - 1) * 50  # Restar 1 para no contar el primer mes de atraso (que ya está cubierto por el recargo inicial de 50)
        else:
            recargo = 50

        try:
            monto_float = float(monto)
            total_con_recargo = monto_float + recargo
            return total_con_recargo, recargo
        except ValueError:
            # Si monto no es un número válido, manejar el error o asignar un valor predeterminado
            return 0, 0  # Por ejemplo, asignar 0 como valor predeterminado



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
        # Extraer los datos del formulario
        nombre = request.form['NombreCompleto']
        fecha_nacimiento = request.form['FechadeNacimiento']
        beca = request.form['Beca']
        matricula = request.form['Matricula']
        grupo_id = request.form['GrupoId']

        tutor1nombre = request.form['Tutor1Nombre']
        tutor1Correo = request.form['Tutor1Correo']
        tutor1Parentesco = request.form['Tutor1Parentesco']
        tutor1Direccion = request.form['Tutor1Direccion']
        tutor1Telefono = request.form['Tutor1Telefono']
        tutor1Regimen = request.form['Tutor1Regimen']
        tutor1RS = request.form['Tutor1RS']
        tutor1CFDI = request.form['Tutor1CFDI']
        tutor1RFC = request.form['Tutor1RFC']
        tutor1CP = request.form['Tutor1CP']
        tutor1dirfact = request.form['Tutor1dirfact']
        tutor2Nombre = request.form['Tutor2Nombre']
        tutor2Correo = request.form['Tutor2Correo']
        tutor2Parentesco = request.form['Tutor2Parentesco']
        tutor2Direccion = request.form['Tutor2Direccion']
        tutor2Telefono = request.form['Tutor2Telefono']
        tutor2Regimen = request.form['Tutor2Regimen']
        tutor2RS = request.form['Tutor2RS']
        tutor2CFDI = request.form['Tutor2CFDI']
        tutor2RFC = request.form['Tutor2RFC']
        tutor2CP = request.form['Tutor2CP']
        tutor2dirfact = request.form['Tutor2dirfact']

        # Realizar las inserciones en la base de datos según tus modelos
        db = mysql.connection.cursor()

        insert_estudiante = """
            INSERT INTO Estudiante (nombre, fecha_de_nacimiento, beca, matricula, grado, id_grupo)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
        estudiante_data = (nombre, fecha_nacimiento, beca, matricula, grupo_id, grupo_id)
        db.execute(insert_estudiante, estudiante_data)
        n = db.lastrowid

        insert_contacto1 = """
        INSERT INTO Contacto(nombre, parentesco,correo,telefono,direccion,razonSocial,regimenFiscal,cfdi,rfc,cp,direccionFact,id_estudiante)
        VALUES(%s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s)"""
        contacto1_data = (
        tutor1nombre, tutor1Parentesco, tutor1Correo, tutor1Telefono, tutor1Direccion, tutor1RS, tutor1Regimen,
        tutor1CFDI, tutor1RFC, tutor1CP, tutor1dirfact, n)
        db.execute(insert_contacto1, contacto1_data)
        # Realizar inserciones en tablas relacionadas como Contacto, Estudiante_Contacto, etc.
        # ...
        insert_contacto2 = """
                INSERT INTO Contacto(nombre, parentesco,correo,telefono,direccion,razonSocial,regimenFiscal,cfdi,rfc,cp,direccionFact,id_estudiante)
                VALUES(%s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s)"""
        contacto2_data = (
            tutor2Nombre, tutor2Parentesco, tutor2Correo, tutor2Telefono, tutor2Direccion, tutor2RS, tutor2Regimen,
            tutor2CFDI, tutor2RFC, tutor2CP, tutor2dirfact, n)
        db.execute(insert_contacto2, contacto2_data)

        monto_colegiatura = 2750 if int(gid) < 6 else 2800
        montoreeinscripcion = 2750 if int(gid) < 4 else 2800

        # Definir las fechas y montos de las transacciones
        transacciones = [
            ("Colegiatura Septiembre", "2023-09-06", "2023-08-28", monto_colegiatura),
            ("Colegiatura Octubre", "2023-10-10", "2023-10-01", monto_colegiatura),
            ("Colegiatura Noviembre", "2023-11-10", "2023-11-01", monto_colegiatura),
            ("Colegiatura Agosto", "2023-12-10", "2023-12-01", monto_colegiatura),
            ("Colegiatura Diciembre", "2023-12-10", "2023-12-01", monto_colegiatura),
            ("Colegiatura Enero", "2024-01-10", "2024-01-01", monto_colegiatura),
            ("Reinscripción CICLO ESCOLAR 2024-2025 ", "2024-02-02", "2024-01-22", montoreeinscripcion),
            ("Colegiatura Febrero", "2024-02-10", "2024-02-01", monto_colegiatura),
            ("Colegiatura Marzo", "2024-03-10", "2024-03-01", monto_colegiatura),
            ("Colegiatura Abril", "2024-04-12", "2024-04-01", monto_colegiatura),
            ("Colegiatura Mayo", "2024-05-10", "2024-05-01", monto_colegiatura),
            ("Colegiatura Junio", "2024-06-10", "2024-06-01", monto_colegiatura),
            ("Colegiatura Julio", "2024-06-10", "2024-06-01", monto_colegiatura)
        ]

        # Insertar las transacciones en la tabla Transaccion
        for nombre, fecha_pago, fecha_activacion, monto in transacciones:
            fecha_limite = datetime.strptime(fecha_pago, "%Y-%m-%d").date()
            fecha_activacion = datetime.strptime(fecha_activacion, "%Y-%m-%d").date()
            db.execute(
                "INSERT INTO Transaccion (monto, concepto, fecha_limite, fechaActivacion, activado, pagado, id_estudiante) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (monto, nombre, fecha_limite, fecha_activacion, False, False, n))

        db.connection.commit()
        db.close()
        return redirect(url_for('get_group', id=gid))

    _info = {"student": {"group": int(gid)}, "msg": msg}
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
                        T.deuda,
                        Estudiante.matricula
                    FROM Estudiante 
                    JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                    LEFT JOIN (SELECT sum(monto) as deuda, id_estudiante
                            FROM Transaccion WHERE pagado=FALSE
                            GROUP BY id_estudiante) AS T
                    ON Estudiante.id=T.id_estudiante
                    WHERE id_grupo = '{}'
                    """.format(id))
    data = db.fetchall()
    _students = []
    for item in data:
        matricula = item[4]
        deuda = "PAGADO"
        if item[3] is not None:
            deuda = "${:,.2f}".format(item[3])
        _students.append([item[1], matricula, item[2], deuda])
    nstud = len(_students)
    try:
        db.execute("""
            SELECT
                SUM(T.monto) AS total_monto_pagado
            FROM
                Estudiante AS E
            JOIN
                Transaccion AS T ON E.id = T.id_estudiante
            WHERE
                T.pagado = TRUE
                AND E.id_grupo = '{}';
        """.format(id))

        totganado = "${:,.2f}".format(db.fetchall()[0][0])


    except (IndexError, TypeError):
        totganado = "$0.00"
    _info = {"group_id": id, "group": data[0][0], "students": _students, "num": nstud}
    return render_template('group.html', info=_info, totganado=totganado)


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
    beca = "{} %".format(data[2])
    matricula = data[3]
    password = data[4]
    group = data[5]
    student = {"name": name, "beca": beca, "group": group, "group_id": data[6], "matricula": data[3],
               "password": data[4]}
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
        # Extraer los datos del formulario
        nombre = request.form['nombre']
        fecha_nacimiento = request.form['nacimiento']
        beca = request.form['beca']
        matricula = request.form['matricula']
        grupo_id = request.form['idgrupo']
        acid = request.form['acid']

        tutor1nombre = request.form['acnom']
        tutor1Correo = request.form['acmail']
        tutor1Parentesco = request.form['acparen']
        tutor1Direccion = request.form['acdir']
        tutor1Telefono = request.form['actel']
        tutor1Regimen = request.form['acrf']
        tutor1RS = request.form['acrs']
        tutor1CFDI = request.form['accfdi']
        tutor1RFC = request.form['acrfc']
        tutor1CP = request.form['accp']
        tutor1dirfact = request.form['acdf']
        bcid = request.form['bcid']

        tutor2Nombre = request.form['bcnom']
        tutor2Correo = request.form['bcmail']
        tutor2Parentesco = request.form['bcparen']
        tutor2Direccion = request.form['bcdir']
        tutor2Telefono = request.form['bctel']
        tutor2Regimen = request.form['bcrf']
        tutor2RS = request.form['bcrs']
        tutor2CFDI = request.form['bccfdi']
        tutor2RFC = request.form['bcrfc']
        tutor2CP = request.form['bccp']
        tutor2dirfact = request.form['bcdf']

        # Realizar las inserciones en la base de datos según tus modelos
        db = mysql.connection.cursor()

        insert_estudiante = """
                UPDATE Estudiante
                SET nombre = %s, fecha_de_nacimiento = %s, beca = %s, matricula = %s, id_grupo = %s
                WHERE id = %s
                """
        estudiante_data = (nombre, fecha_nacimiento, beca, matricula, grupo_id, id)
        db.execute(insert_estudiante, estudiante_data)
        n = id

        insert_contacto1 = """
                UPDATE Contacto
                SET nombre = %s, parentesco = %s, correo = %s, telefono = %s, direccion = %s, razonSocial = %s,
                    regimenFiscal = %s, cfdi = %s, rfc = %s, cp = %s, direccionFact = %s
                WHERE id = %s
                """
        contacto1_data = (
            tutor1nombre, tutor1Parentesco, tutor1Correo, tutor1Telefono, tutor1Direccion, tutor1RS, tutor1Regimen,
            tutor1CFDI, tutor1RFC, tutor1CP, tutor1dirfact, acid)
        db.execute(insert_contacto1, contacto1_data)
        # Realizar inserciones en tablas relacionadas como Contacto, Estudiante_Contacto, etc.
        # ...
        insert_contacto2 = """
                UPDATE Contacto
                SET nombre = %s, parentesco = %s, correo = %s, telefono = %s, direccion = %s, razonSocial = %s,
                    regimenFiscal = %s, cfdi = %s, rfc = %s, cp = %s, direccionFact = %s
                WHERE id = %s
                """
        contacto2_data = (
            tutor2Nombre, tutor2Parentesco, tutor2Correo, tutor2Telefono, tutor2Direccion, tutor2RS, tutor2Regimen,
            tutor2CFDI, tutor2RFC, tutor2CP, tutor2dirfact, bcid)
        db.execute(insert_contacto2, contacto2_data)
        db.connection.commit()

        return redirect(url_for('get_student', id=id))
    db = mysql.connection.cursor()
    db.execute("""SELECT 
                    Estudiante.nombre, 
                    Estudiante.fecha_de_nacimiento, 
                    Estudiante.beca,  
                    Grupo.id,
                    Estudiante.matricula
                    FROM Estudiante JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                    WHERE Estudiante.id={}
                """.format(id))
    data = db.fetchall()[0]
    name = data[0]
    nac = data[1]
    beca = data[2]
    group = data[3]
    mat = data[4]
    student = {"name": name, "nac": nac, "beca": beca, "group": group, "mat": mat}
    db.execute("""SELECT
                    nombre, parentesco, correo, telefono, direccion,razonSocial,regimenFiscal,cfdi,rfc,cp,direccionFact, id
                    FROM Contacto WHERE id_estudiante={}""".format(id))
    cdata = db.fetchall()
    acon = ["", "", "", "", "", "", "", "", "", "", "", ""]
    bcon = ["", "", "", "", "", "", "", "", "", "", "", ""]
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

    # Delete associated Estudiante_Contacto records first
    db.execute("DELETE FROM Estudiante_Contacto WHERE id_estudiante = {}".format(id))

    # Now, delete the student record
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
            return redirect(url_for('get_nuevorecibol', aid=aid, id=id))
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

    beca = "{} %".format(data[2])
    matricula = data[3]
    password = data[4]
    group = data[5]
    student = {"name": name, "beca": beca, "group": group, "group_id": data[6], "matricula": data[3],
               "password": data[4]}
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


@app.route('/enviarcorreo/<aid>/<id>', methods=['GET', 'POST'])
def enviar_correo(aid, id):
    if not check_login():
        return redirect(url_for('login'))

    db = mysql.connection.cursor()
    msg = ""

    # Fetch transaction data
    db.execute("SELECT id, monto, metodo, concepto, fecha_pago, pagado FROM Transaccion WHERE id = %s", (id,))
    data = db.fetchone()
    noticia = "PAGADO" if data[5] == 0 else "ADEUDO"

    # Fetch student data
    db.execute(
        "SELECT Estudiante.nombre, Estudiante.fecha_de_nacimiento, Estudiante.beca, Grupo.nombre, Grupo.id, Estudiante.matricula FROM Estudiante JOIN Grupo ON Estudiante.id_grupo = Grupo.id WHERE Estudiante.id = %s",
        (aid,))
    data1 = db.fetchone()

    # Fetch contact data
    db.execute("SELECT nombre, parentesco, correo, telefono, direccion FROM Contacto WHERE id_estudiante = %s", (aid,))
    cdata = db.fetchall()

    acon = ["", "", "", "", ""]
    bcon = ["", "", "", "", ""]
    for i in range(len(cdata)):
        if i == 0:
            acon = cdata[i]
        if i == 1:
            bcon = cdata[i]

    # String for the first contact

    spc = f"Estimado (a) {acon[0]}, usted ha realizado el pago de la {data[3]} del alumno {data1[0]} con matrícula {data1[5]} el día {data[4]}.\n Adjuntamos su recibo de pago por este medio. \n\n\n Si requiere mayor información con gusto podemos antederle vía telefónica en los siguientes números de contacto: 7731003044, 7737325312 y 773 171 62 48. \n \n Saludos Cordiales. \n Colegio Felipe Carbajal Arcia \n Área de Administración"
    string_primer_contacto = spc
    # String for the second contact
    ssc = f"Estimado (a) {bcon[0]}, usted ha realizado el pago de la {data[3]} del alumno {data1[0]} con matrícula {data1[5]} el día {data[4]}.\n Adjuntamos su recibo de pago por este medio. \n\n\n Si requiere mayor información con gusto podemos antederle vía telefónica en los siguientes números de contacto: 7731003044, 7737325312 y 773 171 62 48. \n \n Saludos Cordiales. \n Colegio Felipe Carbajal Arcia \n Área de Administración"
    string_segundo_contacto = ssc

    pagotxt = data[3]


    # Verificar si acon[2] tiene un valor almacenado y llamar send_email si es así
    if acon[2]:
        send_email(pagotxt, string_primer_contacto, acon[2])

    # Verificar si bcon[2] tiene un valor almacenado y llamar send_email si es así
    if bcon[2]:
        send_email(pagotxt, string_primer_contacto, bcon[2])

    return redirect(url_for('get_student', id=aid))





def insertColegiaturas(estudiante_id):
    db = mysql.connection.cursor()

    # Obtener el grupo del estudiante
    db.execute("SELECT id_grupo FROM Estudiante WHERE id = %s", (estudiante_id,))
    id_grupo = db.fetchone()[0]
    monto_colegiatura = 2750 if id_grupo < 6 else 2800

    # Definir las fechas y montos de las transacciones
    transacciones = [
        ("Colegiatura Septiembre", "2023-09-10", "2023-09-01", monto_colegiatura),
        ("Colegiatura Octubre", "2023-10-10", "2023-10-01", monto_colegiatura),
        ("Colegiatura Noviembre", "2023-11-10", "2023-11-01", monto_colegiatura),
        ("Colegiatura Diciembre y Agosto", "2023-12-10", "2023-12-01", monto_colegiatura * 2),
        ("Colegiatura Enero", "2024-01-10", "2024-01-01", monto_colegiatura),
        ("Colegiatura Febrero", "2024-02-10", "2024-02-01", monto_colegiatura),
        ("Colegiatura Marzo", "2024-03-10", "2024-03-01", monto_colegiatura),
        ("Colegiatura Abril", "2024-04-10", "2024-04-01", monto_colegiatura),
        ("Colegiatura Mayo", "2024-05-10", "2024-05-01", monto_colegiatura),
        ("Colegiatura Junio y Julio", "2024-06-10", "2024-06-01", monto_colegiatura * 2)
    ]

    # Insertar las transacciones en la tabla Transaccion
    for nombre, fecha_pago, fecha_activacion, monto in transacciones:
        fecha_limite = datetime.strptime(fecha_pago, "%Y-%m-%d").date()
        fecha_activacion = datetime.strptime(fecha_activacion, "%Y-%m-%d").date()
        db.execute(
            "INSERT INTO Transaccion (monto, concepto, fecha_limite, fechaActivacion, activado, pagado, id_estudiante) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (monto, nombre, fecha_limite, fecha_activacion, False, False, estudiante_id))

    db.connection.commit()


@app.route('/pagoAnual/<id>/<gid>', methods=['POST', 'GET'])
def pagoAnual(id, gid):
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()
    # Obtener el monto de la colegiatura anual
    monto_colegiatura = 30250 if int(gid) < 6 else 30800
    print(monto_colegiatura)

    # Borrar todas las transacciones del estudiante
    db.execute("""DELETE FROM Transaccion 
                                WHERE id_estudiante={}""".format(id))
    db.connection.commit()
    # Agregar la nueva transacción para la colegiatura anual
    nombre_concepto = "Colegiatura Anual"
    fecha_pago = date.today()
    db.execute(
        "INSERT INTO Transaccion (monto, concepto, fecha_pago, activado, pagado, id_estudiante, metodo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (monto_colegiatura, nombre_concepto, fecha_pago, True, True, id, 'Transferencia'))
    db.connection.commit()
    montoreeinscripcion = 2750 if int(gid) < 4 else 2800
    nombre_conceptoIns = "Reinscripción CICLO ESCOLAR 2024-2025 "
    fecha_pagoR = "2024-02-02"
    fecha_activacionR ="2024-01-22"
    db.execute(
        "INSERT INTO Transaccion (monto, concepto, fecha_pago,fechaActivacion, pagado, id_estudiante) VALUES (%s, %s, %s, %s, %s,%s)",
        (montoreeinscripcion, nombre_conceptoIns, fecha_pagoR,fecha_activacionR, False, id ))
    db.connection.commit()
    return redirect(url_for('get_student', id=id))


@app.route('/generate_email/<aid>/<id>', methods=['GET'])
def generate_email(aid, id):
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
                                    Grupo.id,
                                    Estudiante.matricula
                                    FROM Estudiante JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                                    WHERE Estudiante.id={}
                                """.format(aid))
    data1 = db.fetchall()[0]
    name = data1[0]

    # Fetch contact data
    db.execute("SELECT nombre, parentesco, correo, telefono, direccion FROM Contacto WHERE id_estudiante = %s", (aid,))
    cdata = db.fetchall()

    acon = ["", "", "", "", ""]
    bcon = ["", "", "", "", ""]
    for i in range(len(cdata)):
        if i == 0:
            acon = cdata[i]
        if i == 1:
            bcon = cdata[i]

    # String for the first contact

    spc = f"Estimado (a) {acon[0]}, usted ha realizado el pago de la {data[3]} del alumno {data1[0]} con matrícula {data1[5]} el día {data[4]}.\n Adjuntamos su recibo de pago por este medio. \n Si requiere mayor información con gusto podemos antederle vía telefónica en los siguientes números de contacto: 7731003044, 7737325312 y 773 171 62 48. \n En un horario de 8:00 a 14:00 hrs. \n Seguimos a sus órdenes.\n Nuestro cupo es limitado.\n \n Saludos Cordiales. \n Colegio Felipe Carbajal Arcia \n Área de Administración"
    string_primer_contacto = spc
    # String for the second contact
    ssc = f"Estimado (a) {bcon[0]}, usted ha realizado el pago de la {data[3]} del alumno {data1[0]} con matrícula {data1[5]} el día {data[4]}.\n Adjuntamos su recibo de pago por este medio. \n Si requiere mayor información con gusto podemos antederle vía telefónica en los siguientes números de contacto: 7731003044, 7737325312 y 773 171 62 48. \n En un horario de 8:00 a 14:00 hrs. \n Seguimos a sus órdenes.\n Nuestro cupo es limitado.\n \n Saludos Cordiales. \n Colegio Felipe Carbajal Arcia \n Área de Administración"
    string_segundo_contacto = ssc

    pagotxt = data[3]

    correoinfo = {"correo": acon[2], "conceptop": data[3], "textocorreo": spc}

    beca = "{} %".format(data1[2])
    group = data1[3]
    student = {"name": name, "beca": beca, "group": group, "group_id": data[4], "matricula": data1[5]}

    _info = {"msg": msg, "student": student, "id": aid, "aid": id, "data": data}

    html_content = render_template('recibocorreo.html', info=_info, noticia=noticia, id=aid, correoinfo=correoinfo)

    return html_content


@app.route('/send_emaill/<aid>/<id>', methods=['GET'])
def send_email(aid, id):
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
                                    Grupo.id,
                                    Estudiante.matricula
                                    FROM Estudiante JOIN Grupo ON Estudiante.id_grupo=Grupo.id
                                    WHERE Estudiante.id={}
                                """.format(aid))
    data1 = db.fetchall()[0]
    name = data1[0]

    # Fetch contact data
    db.execute("SELECT nombre, parentesco, correo, telefono, direccion FROM Contacto WHERE id_estudiante = %s",
               (aid,))
    cdata = db.fetchall()

    acon = ["", "", "", "", ""]
    bcon = ["", "", "", "", ""]
    for i in range(len(cdata)):
        if i == 0:
            acon = cdata[i]
        if i == 1:
            bcon = cdata[i]

    # String for the first contact

    spc = f"Estimado (a) {acon[0]}, usted ha realizado el pago de la {data[3]} del alumno {data1[0]} con matrícula {data1[5]} el día {data[4]}.\n Adjuntamos su recibo de pago por este medio. \n \n \n Saludos Cordiales. \n Colegio Felipe Carbajal Arcia \n Área de Administración"
    string_primer_contacto = spc
    # String for the second contact
    ssc = f"Estimado (a) {bcon[0]}, usted ha realizado el pago de la {data[3]} del alumno {data1[0]} con matrícula {data1[5]} el día {data[4]}.\n Adjuntamos su recibo de pago por este medio. \n Si requiere mayor información con gusto podemos antederle vía telefónica en los siguientes números de contacto: 7731003044, 7737325312 y 773 171 62 48. \n En un horario de 8:00 a 14:00 hrs. \n Seguimos a sus órdenes.\n Nuestro cupo es limitado.\n \n Saludos Cordiales. \n Colegio Felipe Carbajal Arcia \n Área de Administración"
    string_segundo_contacto = ssc

    pagotxt = data[3]

    correoinfo = {"correo": acon[2], "conceptop": data[3], "textocorreo": spc}

    beca = "{} %".format(data1[2])
    group = data1[3]
    student = {"name": name, "beca": beca, "group": group, "group_id": data[4], "matricula": data1[5]}

    _info = {"msg": msg, "student": student, "id": aid, "aid": id, "data": data}

    css_url = url_for('static', filename='css/estilos.css')
    logo_url = url_for('static', filename='images/logocfca.jpg')

    html_content = render_template('recibocorreo.html', info=_info, noticia=noticia, id=aid, correoinfo=correoinfo,
                                   css_url=css_url, logo_url=logo_url)

    # Configurar los detalles del correo electrónico
    sender_email = 'Colegio Felipe Carbajal Arcia'
    receiver_email = acon[2]
    subject = 'Pago Colegiatura alumno ' + data1[0] +'  matrícula: ' + str(data1[5])

    # Crear el mensaje de correo electrónico
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Agregar el contenido HTML al correo
    msg.attach(MIMEText(html_content, 'html'))



    # Enviar el correo electrónico
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'felipecarbajalarcia@gmail.com'
    smtp_password = 'wqovjkhmaxycrrjx'

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(sender_email, receiver_email, msg.as_string())
    server.quit()

    return redirect(url_for('get_student', id=aid))

@app.route('/efectivoPreescolar')
def efectivoPreescolar():
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()

    db.execute("""
            SELECT
                E.id AS estudiante_id,
                E.matricula,
                E.nombre AS estudiante_nombre,
                G.nombre AS nombre_grupo,   
                T.monto,
                T.metodo,
                T.concepto,
                T.fecha_pago 
            FROM
                Estudiante AS E
            JOIN
                Transaccion AS T ON E.id = T.id_estudiante
            JOIN
                Grupo AS G ON E.id_grupo = G.id
            WHERE
                T.pagado = TRUE
                AND T.fecha_pago >= CURDATE() - INTERVAL 15 DAY
                AND E.id_grupo <= 6
                AND T.metodo = 'Efectivo'
        """)
    data1 = db.fetchall()
    _studentsquincena = []
    for item in data1:
        _studentsquincena.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    db.execute("""
                SELECT
                    E.id AS estudiante_id,
                    E.matricula,
                    E.nombre AS estudiante_nombre,
                    G.nombre AS nombre_grupo,   
                    T.monto,
                    T.metodo,
                    T.concepto,
                    T.fecha_pago 
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
                    AND E.id_grupo <= 6
                    AND T.metodo = 'Efectivo'
            """)
    data2 = db.fetchall()
    _studentsmensual = []
    for item in data2:
        _studentsmensual.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    db.execute("""
                SELECT
                    E.id AS estudiante_id,
                    E.matricula,
                    E.nombre AS estudiante_nombre,
                    G.nombre AS nombre_grupo,   
                    T.monto,
                    T.metodo,
                    T.concepto,
                    T.fecha_pago 
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE()
                    AND E.id_grupo <= 6
                    AND T.metodo = 'Efectivo'
            """)
    data3 = db.fetchall()
    _studentsdia = []
    for item in data3:
        _studentsdia.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])



    return render_template('efectivoPreescolar.html', diario=_studentsdia, quincena=_studentsquincena, mes=_studentsmensual)




@app.route('/transferenciaPreescolar')
def transferenciaPreescolar():
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()

    db.execute("""
            SELECT
                E.id AS estudiante_id,
                E.matricula,
                E.nombre AS estudiante_nombre,
                G.nombre AS nombre_grupo,   
                T.monto,
                T.metodo,
                T.concepto,
                T.fecha_pago 
            FROM
                Estudiante AS E
            JOIN
                Transaccion AS T ON E.id = T.id_estudiante
            JOIN
                Grupo AS G ON E.id_grupo = G.id
            WHERE
                T.pagado = TRUE
                AND T.fecha_pago >= CURDATE() - INTERVAL 15 DAY
                AND E.id_grupo <= 6
                AND T.metodo = 'Transferencia'
        """)
    data1 = db.fetchall()
    _studentsquincena = []
    for item in data1:
        _studentsquincena.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    db.execute("""
                SELECT
                    E.id AS estudiante_id,
                    E.matricula,
                    E.nombre AS estudiante_nombre,
                    G.nombre AS nombre_grupo,   
                    T.monto,
                    T.metodo,
                    T.concepto,
                    T.fecha_pago 
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
                    AND E.id_grupo <= 6
                    AND T.metodo = 'Transferencia'
            """)
    data2 = db.fetchall()
    _studentsmensual = []
    for item in data2:
        _studentsmensual.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    db.execute("""
                SELECT
                    E.id AS estudiante_id,
                    E.matricula,
                    E.nombre AS estudiante_nombre,
                    G.nombre AS nombre_grupo,   
                    T.monto,
                    T.metodo,
                    T.concepto,
                    T.fecha_pago 
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE()
                    AND E.id_grupo <= 6
                    AND T.metodo = 'Transferencia'
            """)
    data3 = db.fetchall()
    _studentsdia = []
    for item in data3:
        _studentsdia.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])



    return render_template('transferenciaPreescolar.html', diario=_studentsdia, quincena=_studentsquincena, mes=_studentsmensual)


@app.route('/efectivoPrimaria')
def efectivoPrimaria():
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()

    db.execute("""
            SELECT
                E.id AS estudiante_id,
                E.matricula,
                E.nombre AS estudiante_nombre,
                G.nombre AS nombre_grupo,   
                T.monto,
                T.metodo,
                T.concepto,
                T.fecha_pago 
            FROM
                Estudiante AS E
            JOIN
                Transaccion AS T ON E.id = T.id_estudiante
            JOIN
                Grupo AS G ON E.id_grupo = G.id
            WHERE
                T.pagado = TRUE
                AND T.fecha_pago >= CURDATE() - INTERVAL 15 DAY
                AND E.id_grupo >= 7
                AND T.metodo = 'Efectivo'
        """)
    data1 = db.fetchall()
    _studentsquincena = []
    for item in data1:
        _studentsquincena.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    db.execute("""
                SELECT
                    E.id AS estudiante_id,
                    E.matricula,
                    E.nombre AS estudiante_nombre,
                    G.nombre AS nombre_grupo,   
                    T.monto,
                    T.metodo,
                    T.concepto,
                    T.fecha_pago 
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
                    AND E.id_grupo >= 7
                    AND T.metodo = 'Efectivo'
            """)
    data2 = db.fetchall()
    _studentsmensual = []
    for item in data2:
        _studentsmensual.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    db.execute("""
                SELECT
                    E.id AS estudiante_id,
                    E.matricula,
                    E.nombre AS estudiante_nombre,
                    G.nombre AS nombre_grupo,   
                    T.monto,
                    T.metodo,
                    T.concepto,
                    T.fecha_pago 
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE()
                    AND E.id_grupo >= 7
                    AND T.metodo = 'Efectivo'
            """)
    data3 = db.fetchall()
    _studentsdia = []
    for item in data3:
        _studentsdia.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])



    return render_template('efectivoPrimaria.html', diario=_studentsdia, quincena=_studentsquincena, mes=_studentsmensual)

@app.route('/transferenciaPrimaria')
def transferenciaPrimaria():
    if not check_login():
        return redirect(url_for('login'))
    db = mysql.connection.cursor()

    db.execute("""
            SELECT
                E.id AS estudiante_id,
                E.matricula,
                E.nombre AS estudiante_nombre,
                G.nombre AS nombre_grupo,   
                T.monto,
                T.metodo,
                T.concepto,
                T.fecha_pago 
            FROM
                Estudiante AS E
            JOIN
                Transaccion AS T ON E.id = T.id_estudiante
            JOIN
                Grupo AS G ON E.id_grupo = G.id
            WHERE
                T.pagado = TRUE
                AND T.fecha_pago >= CURDATE() - INTERVAL 15 DAY
                AND E.id_grupo >= 7
                AND T.metodo = 'Transferencia'
        """)
    data1 = db.fetchall()
    _studentsquincena = []
    for item in data1:
        _studentsquincena.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    db.execute("""
                SELECT
                    E.id AS estudiante_id,
                    E.matricula,
                    E.nombre AS estudiante_nombre,
                    G.nombre AS nombre_grupo,   
                    T.monto,
                    T.metodo,
                    T.concepto,
                    T.fecha_pago 
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
                    AND E.id_grupo >= 7
                    AND T.metodo = 'Transferencia'
            """)
    data2 = db.fetchall()
    _studentsmensual = []
    for item in data2:
        _studentsmensual.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])

    db.execute("""
                SELECT
                    E.id AS estudiante_id,
                    E.matricula,
                    E.nombre AS estudiante_nombre,
                    G.nombre AS nombre_grupo,   
                    T.monto,
                    T.metodo,
                    T.concepto,
                    T.fecha_pago 
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE()
                    AND E.id_grupo >= 7
                    AND T.metodo = 'Transferencia'
            """)
    data3 = db.fetchall()
    _studentsdia = []
    for item in data3:
        _studentsdia.append([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])



    return render_template('transferenciaPrimaria.html', diario=_studentsdia, quincena=_studentsquincena, mes=_studentsmensual)

#ExcelPreescolar
@app.route('/export_excelDiarioEfectivoPreescolar')
def export_excelDiarioEP():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            E.id AS estudiante_id,
            E.matricula,
            E.nombre AS estudiante_nombre,
            G.nombre AS nombre_grupo,   
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago 
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
            Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND T.fecha_pago >= CURDATE() 
            AND E.id_grupo <= 6
            AND T.metodo = 'Efectivo'
    """)

    data3 = cur.fetchall()

    # Crea un DataFrame de pandas con los datos
    df = pd.DataFrame(data3,
                      columns=['ID alumno App', 'Matricula ', 'Nombre ', 'Grado y Grupo', 'Monto', 'Forma de pago',
                               'Mes', 'Fecha de Pago'])

    # Crea un objeto ExcelWriter utilizando XlsxWriter como motor de escritura
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Escribe el DataFrame en una hoja de cálculo Excel
    df.to_excel(writer, sheet_name='ExcelDiarioEfectivoPreescolar', index=False)

    # Obtener la hoja de trabajo actual
    workbook = writer.book
    worksheet = writer.sheets['ExcelDiarioEfectivoPreescolar']

    try:

        cur.execute("""SELECT
                    SUM(monto) AS Total
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE() 
                    AND E.id_grupo <= 6
                    AND T.metodo = 'Efectivo'""")
        totganado = "${:,.2f}".format(cur.fetchall()[0][0])
    except (IndexError, TypeError):
        totganado = "$0.00"

    # Agregar el título, subtítulo y fecha
    worksheet.merge_range('A1:H1', 'Colegio Felipe Carbajal Arcia', workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
    worksheet.merge_range('A2:H2', 'Reporte Quincenal Preescolar en efectivo', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
    worksheet.merge_range('A3:H3', f'Fecha: {datetime.now().strftime("%Y-%m-%d")}', workbook.add_format({'font_size': 12, 'align': 'center'}))
    worksheet.merge_range('A4:H4', f'Total: {totganado}', workbook.add_format({'bold': True,'font_size': 15, 'align': 'center'}))
    worksheet.write('A5', 'ID alumno App', workbook.add_format({'bold': True}))
    worksheet.write('B5', 'Matricula', workbook.add_format({'bold': True}))
    worksheet.write('C5', 'Nombre', workbook.add_format({'bold': True}))
    worksheet.write('D5', 'Grado y Grupo', workbook.add_format({'bold': True}))
    worksheet.write('E5', 'Monto', workbook.add_format({'bold': True}))
    worksheet.write('F5', 'Forma de pago', workbook.add_format({'bold': True}))
    worksheet.write('G5', 'Mes', workbook.add_format({'bold': True}))
    worksheet.write('H5', 'Fecha de Pago', workbook.add_format({'bold': True}))

    # Ajusta el ancho de las columnas
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(str(col)))
        worksheet.set_column(i, i, column_width)

    # Cierra el objeto writer para guardar el archivo correctamente
    writer.close()

    # Lleva la posición del cursor al inicio del BytesIO
    output.seek(0)

    # Guarda el contenido del archivo de Excel en una variable
    excel_data = output.read()

    # Crea una respuesta HTTP con el archivo de Excel adjunto
    response = make_response(excel_data)
    response.headers['Content-Disposition'] = 'attachment; filename=ExcelDiarioEfectivoPreescolar.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return response
@app.route('/export_excelDiarioTransferenciaPreescolar')
def export_excelDiarioTP():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            E.id AS estudiante_id,
            E.matricula,
            E.nombre AS estudiante_nombre,
            G.nombre AS nombre_grupo,   
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago 
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
            Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND T.fecha_pago >= CURDATE()
            AND E.id_grupo <= 6
            AND T.metodo = 'Transferencia'
    """)

    data3 = cur.fetchall()

    # Crea un DataFrame de pandas con los datos
    df = pd.DataFrame(data3,
                      columns=['ID alumno App', 'Matricula ', 'Nombre ', 'Grado y Grupo', 'Monto', 'Forma de pago',
                               'Mes', 'Fecha de Pago'])

    # Crea un objeto ExcelWriter utilizando XlsxWriter como motor de escritura
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Escribe el DataFrame en una hoja de cálculo Excel
    df.to_excel(writer, sheet_name='DiarioTransferenciaPreescolar', index=False)

    # Obtener la hoja de trabajo actual
    workbook = writer.book
    worksheet = writer.sheets['DiarioTransferenciaPreescolar']

    try:

        cur.execute("""SELECT
                    SUM(monto) AS Total
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE()
                    AND E.id_grupo <= 6
                    AND T.metodo = 'Efectivo'""")
        totganado = "${:,.2f}".format(cur.fetchall()[0][0])
    except (IndexError, TypeError):
        totganado = "$0.00"

    # Agregar el título, subtítulo y fecha
    worksheet.merge_range('A1:H1', 'Colegio Felipe Carbajal Arcia', workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
    worksheet.merge_range('A2:H2', 'Reporte Quincenal Preescolar en efectivo', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
    worksheet.merge_range('A3:H3', f'Fecha: {datetime.now().strftime("%Y-%m-%d")}', workbook.add_format({'font_size': 12, 'align': 'center'}))
    worksheet.merge_range('A4:H4', f'Total: {totganado}', workbook.add_format({'bold': True,'font_size': 15, 'align': 'center'}))
    worksheet.write('A5', 'ID alumno App', workbook.add_format({'bold': True}))
    worksheet.write('B5', 'Matricula', workbook.add_format({'bold': True}))
    worksheet.write('C5', 'Nombre', workbook.add_format({'bold': True}))
    worksheet.write('D5', 'Grado y Grupo', workbook.add_format({'bold': True}))
    worksheet.write('E5', 'Monto', workbook.add_format({'bold': True}))
    worksheet.write('F5', 'Forma de pago', workbook.add_format({'bold': True}))
    worksheet.write('G5', 'Mes', workbook.add_format({'bold': True}))
    worksheet.write('H5', 'Fecha de Pago', workbook.add_format({'bold': True}))

    # Ajusta el ancho de las columnas
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(str(col)))
        worksheet.set_column(i, i, column_width)

    # Cierra el objeto writer para guardar el archivo correctamente
    writer.close()

    # Lleva la posición del cursor al inicio del BytesIO
    output.seek(0)

    # Guarda el contenido del archivo de Excel en una variable
    excel_data = output.read()

    # Crea una respuesta HTTP con el archivo de Excel adjunto
    response = make_response(excel_data)
    response.headers['Content-Disposition'] = 'attachment; filename=DiarioTransferenciaPreescolar.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return response
@app.route('/export_excelQuincenalefectivoPreescolar')
def export_excelQuincenalEP():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            E.id AS estudiante_id,
            E.matricula,
            E.nombre AS estudiante_nombre,
            G.nombre AS nombre_grupo,   
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago 
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
            Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND T.fecha_pago >= CURDATE() - INTERVAL 15 DAY
            AND E.id_grupo <= 6
            AND T.metodo = 'Efectivo'
    """)

    data3 = cur.fetchall()

    # Crea un DataFrame de pandas con los datos
    df = pd.DataFrame(data3,
                      columns=['ID alumno App', 'Matricula ', 'Nombre ', 'Grado y Grupo', 'Monto', 'Forma de pago',
                               'Mes', 'Fecha de Pago'])

    # Crea un objeto ExcelWriter utilizando XlsxWriter como motor de escritura
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Escribe el DataFrame en una hoja de cálculo Excel
    df.to_excel(writer, sheet_name='ExcelQuincenal', index=False)

    # Obtener la hoja de trabajo actual
    workbook = writer.book
    worksheet = writer.sheets['ExcelQuincenal']

    try:
        cur.execute("""SELECT
                        SUM(T.monto) AS Total
                    FROM
                        Estudiante AS E
                    JOIN
                        Transaccion AS T ON E.id = T.id_estudiante
                    JOIN
                        Grupo AS G ON E.id_grupo = G.id
                    WHERE
                        T.pagado = TRUE
                        AND T.fecha_pago >= CURDATE() - INTERVAL 15 DAY
                        AND E.id_grupo <= 6
                        AND T.metodo = 'Efectivo'""")
        totganado = "${:,.2f}".format(cur.fetchall()[0][0])
    except (IndexError, TypeError):
        totganado = "$0.00"

    # Agregar el título, subtítulo y fecha
    worksheet.merge_range('A1:H1', 'Colegio Felipe Carbajal Arcia', workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
    worksheet.merge_range('A2:H2', 'Reporte Quincenal Preescolar en efectivo', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
    worksheet.merge_range('A3:H3', f'Fecha: {datetime.now().strftime("%Y-%m-%d")}', workbook.add_format({'font_size': 12, 'align': 'center'}))
    worksheet.merge_range('A4:H4', f'Total: {totganado}', workbook.add_format({'bold': True,'font_size': 15, 'align': 'center'}))
    worksheet.write('A5', 'ID alumno App', workbook.add_format({'bold': True}))
    worksheet.write('B5', 'Matricula', workbook.add_format({'bold': True}))
    worksheet.write('C5', 'Nombre', workbook.add_format({'bold': True}))
    worksheet.write('D5', 'Grado y Grupo', workbook.add_format({'bold': True}))
    worksheet.write('E5', 'Monto', workbook.add_format({'bold': True}))
    worksheet.write('F5', 'Forma de pago', workbook.add_format({'bold': True}))
    worksheet.write('G5', 'Mes', workbook.add_format({'bold': True}))
    worksheet.write('H5', 'Fecha de Pago', workbook.add_format({'bold': True}))

    # Ajusta el ancho de las columnas
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(str(col)))
        worksheet.set_column(i, i, column_width)

    # Cierra el objeto writer para guardar el archivo correctamente
    writer.close()

    # Lleva la posición del cursor al inicio del BytesIO
    output.seek(0)

    # Guarda el contenido del archivo de Excel en una variable
    excel_data = output.read()

    # Crea una respuesta HTTP con el archivo de Excel adjunto
    response = make_response(excel_data)
    response.headers['Content-Disposition'] = 'attachment; filename=ExcelQuincenal.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return response
@app.route('/export_excelQuincenalTransferenciaPreescolar')
def export_excelQuincenalTP():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            E.id AS estudiante_id,
            E.matricula,
            E.nombre AS estudiante_nombre,
            G.nombre AS nombre_grupo,   
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago 
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
            Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND T.fecha_pago >= CURDATE() - INTERVAL 15 DAY
            AND E.id_grupo <= 6
            AND T.metodo = 'Transferencia'
    """)

    data3 = cur.fetchall()

    # Crea un DataFrame de pandas con los datos
    df = pd.DataFrame(data3,
                      columns=['ID alumno App', 'Matricula ', 'Nombre ', 'Grado y Grupo', 'Monto', 'Forma de pago',
                               'Mes', 'Fecha de Pago'])

    # Crea un objeto ExcelWriter utilizando XlsxWriter como motor de escritura
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Escribe el DataFrame en una hoja de cálculo Excel
    df.to_excel(writer, sheet_name='ExcelQuincenal', index=False)

    # Obtener la hoja de trabajo actual
    workbook = writer.book
    worksheet = writer.sheets['ExcelQuincenal']

    try:

        cur.execute("""SELECT
                    SUM(monto) AS Total
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE() - INTERVAL 15 DAY
                    AND E.id_grupo <= 6
                    AND T.metodo = 'Efectivo'""")
        totganado = "${:,.2f}".format(cur.fetchall()[0][0])
    except (IndexError, TypeError):
        totganado = "$0.00"

    # Agregar el título, subtítulo y fecha
    worksheet.merge_range('A1:H1', 'Colegio Felipe Carbajal Arcia', workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
    worksheet.merge_range('A2:H2', 'Reporte Quincenal Preescolar en efectivo', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
    worksheet.merge_range('A3:H3', f'Fecha: {datetime.now().strftime("%Y-%m-%d")}', workbook.add_format({'font_size': 12, 'align': 'center'}))
    worksheet.merge_range('A4:H4', f'Total: {totganado}', workbook.add_format({'bold': True,'font_size': 15, 'align': 'center'}))
    worksheet.write('A5', 'ID alumno App', workbook.add_format({'bold': True}))
    worksheet.write('B5', 'Matricula', workbook.add_format({'bold': True}))
    worksheet.write('C5', 'Nombre', workbook.add_format({'bold': True}))
    worksheet.write('D5', 'Grado y Grupo', workbook.add_format({'bold': True}))
    worksheet.write('E5', 'Monto', workbook.add_format({'bold': True}))
    worksheet.write('F5', 'Forma de pago', workbook.add_format({'bold': True}))
    worksheet.write('G5', 'Mes', workbook.add_format({'bold': True}))
    worksheet.write('H5', 'Fecha de Pago', workbook.add_format({'bold': True}))

    # Ajusta el ancho de las columnas
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(str(col)))
        worksheet.set_column(i, i, column_width)

    # Cierra el objeto writer para guardar el archivo correctamente
    writer.close()

    # Lleva la posición del cursor al inicio del BytesIO
    output.seek(0)

    # Guarda el contenido del archivo de Excel en una variable
    excel_data = output.read()

    # Crea una respuesta HTTP con el archivo de Excel adjunto
    response = make_response(excel_data)
    response.headers['Content-Disposition'] = 'attachment; filename=ExcelQuincenal.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return response

@app.route('/export_excelMensualEfectivoPreescolar')
def export_excelMensualEP():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            E.id AS estudiante_id,
            E.matricula,
            E.nombre AS estudiante_nombre,
            G.nombre AS nombre_grupo,   
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago 
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
            Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
            AND E.id_grupo <= 6
            AND T.metodo = 'Efectivo'
    """)

    data3 = cur.fetchall()

    # Crea un DataFrame de pandas con los datos
    df = pd.DataFrame(data3,
                      columns=['ID alumno App', 'Matricula ', 'Nombre ', 'Grado y Grupo', 'Monto', 'Forma de pago',
                               'Mes', 'Fecha de Pago'])

    # Crea un objeto ExcelWriter utilizando XlsxWriter como motor de escritura
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Escribe el DataFrame en una hoja de cálculo Excel
    df.to_excel(writer, sheet_name='ExcelMensualEfectivoPreescolar', index=False)

    # Obtener la hoja de trabajo actual
    workbook = writer.book
    worksheet = writer.sheets['ExcelMensualEfectivoPreescolar']

    try:
        cur.execute("""SELECT
                        SUM(T.monto) AS Total
                    FROM
                        Estudiante AS E
                    JOIN
                        Transaccion AS T ON E.id = T.id_estudiante
                    JOIN
                        Grupo AS G ON E.id_grupo = G.id
                    WHERE
                        T.pagado = TRUE
                        AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
                        AND E.id_grupo <= 6
                        AND T.metodo = 'Efectivo'""")
        totganado = "${:,.2f}".format(cur.fetchall()[0][0])
    except (IndexError, TypeError):
        totganado = "$0.00"

    # Agregar el título, subtítulo y fecha
    worksheet.merge_range('A1:H1', 'Colegio Felipe Carbajal Arcia', workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
    worksheet.merge_range('A2:H2', 'Reporte Quincenal Preescolar en efectivo', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
    worksheet.merge_range('A3:H3', f'Fecha: {datetime.now().strftime("%Y-%m-%d")}', workbook.add_format({'font_size': 12, 'align': 'center'}))
    worksheet.merge_range('A4:H4', f'Total: {totganado}', workbook.add_format({'bold': True,'font_size': 15, 'align': 'center'}))
    worksheet.write('A5', 'ID alumno App', workbook.add_format({'bold': True}))
    worksheet.write('B5', 'Matricula', workbook.add_format({'bold': True}))
    worksheet.write('C5', 'Nombre', workbook.add_format({'bold': True}))
    worksheet.write('D5', 'Grado y Grupo', workbook.add_format({'bold': True}))
    worksheet.write('E5', 'Monto', workbook.add_format({'bold': True}))
    worksheet.write('F5', 'Forma de pago', workbook.add_format({'bold': True}))
    worksheet.write('G5', 'Mes', workbook.add_format({'bold': True}))
    worksheet.write('H5', 'Fecha de Pago', workbook.add_format({'bold': True}))

    # Ajusta el ancho de las columnas
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(str(col)))
        worksheet.set_column(i, i, column_width)

    # Cierra el objeto writer para guardar el archivo correctamente
    writer.close()

    # Lleva la posición del cursor al inicio del BytesIO
    output.seek(0)

    # Guarda el contenido del archivo de Excel en una variable
    excel_data = output.read()

    # Crea una respuesta HTTP con el archivo de Excel adjunto
    response = make_response(excel_data)
    response.headers['Content-Disposition'] = 'attachment; filename=ExcelMensualEfectivoPreescolar.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return response
@app.route('/export_excelMensualTransferenciaPreescolar')
def export_excelMensualTP():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            E.id AS estudiante_id,
            E.matricula,
            E.nombre AS estudiante_nombre,
            G.nombre AS nombre_grupo,   
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago 
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
            Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
            AND E.id_grupo <= 6
            AND T.metodo = 'Transferencia'
    """)

    data3 = cur.fetchall()

    # Crea un DataFrame de pandas con los datos
    df = pd.DataFrame(data3,
                      columns=['ID alumno App', 'Matricula ', 'Nombre ', 'Grado y Grupo', 'Monto', 'Forma de pago',
                               'Mes', 'Fecha de Pago'])

    # Crea un objeto ExcelWriter utilizando XlsxWriter como motor de escritura
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Escribe el DataFrame en una hoja de cálculo Excel
    df.to_excel(writer, sheet_name='MensualTransferenciaPreescolar', index=False)

    # Obtener la hoja de trabajo actual
    workbook = writer.book
    worksheet = writer.sheets['MensualTransferenciaPreescolar']

    try:

        cur.execute("""SELECT
                    SUM(monto) AS Total
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
                    AND E.id_grupo <= 6
                    AND T.metodo = 'Efectivo'""")
        totganado = "${:,.2f}".format(cur.fetchall()[0][0])
    except (IndexError, TypeError):
        totganado = "$0.00"

    # Agregar el título, subtítulo y fecha
    worksheet.merge_range('A1:H1', 'Colegio Felipe Carbajal Arcia', workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
    worksheet.merge_range('A2:H2', 'Reporte Quincenal Preescolar en efectivo', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
    worksheet.merge_range('A3:H3', f'Fecha: {datetime.now().strftime("%Y-%m-%d")}', workbook.add_format({'font_size': 12, 'align': 'center'}))
    worksheet.merge_range('A4:H4', f'Total: {totganado}', workbook.add_format({'bold': True,'font_size': 15, 'align': 'center'}))
    worksheet.write('A5', 'ID alumno App', workbook.add_format({'bold': True}))
    worksheet.write('B5', 'Matricula', workbook.add_format({'bold': True}))
    worksheet.write('C5', 'Nombre', workbook.add_format({'bold': True}))
    worksheet.write('D5', 'Grado y Grupo', workbook.add_format({'bold': True}))
    worksheet.write('E5', 'Monto', workbook.add_format({'bold': True}))
    worksheet.write('F5', 'Forma de pago', workbook.add_format({'bold': True}))
    worksheet.write('G5', 'Mes', workbook.add_format({'bold': True}))
    worksheet.write('H5', 'Fecha de Pago', workbook.add_format({'bold': True}))

    # Ajusta el ancho de las columnas
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(str(col)))
        worksheet.set_column(i, i, column_width)

    # Cierra el objeto writer para guardar el archivo correctamente
    writer.close()

    # Lleva la posición del cursor al inicio del BytesIO
    output.seek(0)

    # Guarda el contenido del archivo de Excel en una variable
    excel_data = output.read()

    # Crea una respuesta HTTP con el archivo de Excel adjunto
    response = make_response(excel_data)
    response.headers['Content-Disposition'] = 'attachment; filename=MensualTransferenciaPreescolar.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return response


#Excel PRimaria
@app.route('/export_excelDiarioEfectivoPrimaria')
def export_excelDiarioEPrimaria():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            E.id AS estudiante_id,
            E.matricula,
            E.nombre AS estudiante_nombre,
            G.nombre AS nombre_grupo,   
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago 
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
            Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND T.fecha_pago >= CURDATE() 
            AND E.id_grupo >= 7
            AND T.metodo = 'Efectivo'
    """)

    data3 = cur.fetchall()

    # Crea un DataFrame de pandas con los datos
    df = pd.DataFrame(data3,
                      columns=['ID alumno App', 'Matricula ', 'Nombre ', 'Grado y Grupo', 'Monto', 'Forma de pago',
                               'Mes', 'Fecha de Pago'])

    # Crea un objeto ExcelWriter utilizando XlsxWriter como motor de escritura
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Escribe el DataFrame en una hoja de cálculo Excel
    df.to_excel(writer, sheet_name='ExcelDiarioEfectivoPrimaria', index=False)

    # Obtener la hoja de trabajo actual
    workbook = writer.book
    worksheet = writer.sheets['ExcelDiarioEfectivoPrimaria']

    try:

        cur.execute("""SELECT
                    SUM(monto) AS Total
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE() 
                    AND E.id_grupo >= 7
                    AND T.metodo = 'Efectivo'""")
        totganado = "${:,.2f}".format(cur.fetchall()[0][0])
    except (IndexError, TypeError):
        totganado = "$0.00"

    # Agregar el título, subtítulo y fecha
    worksheet.merge_range('A1:H1', 'Colegio Felipe Carbajal Arcia', workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
    worksheet.merge_range('A2:H2', 'Reporte Quincenal Preescolar en efectivo', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
    worksheet.merge_range('A3:H3', f'Fecha: {datetime.now().strftime("%Y-%m-%d")}', workbook.add_format({'font_size': 12, 'align': 'center'}))
    worksheet.merge_range('A4:H4', f'Total: {totganado}', workbook.add_format({'bold': True,'font_size': 15, 'align': 'center'}))
    worksheet.write('A5', 'ID alumno App', workbook.add_format({'bold': True}))
    worksheet.write('B5', 'Matricula', workbook.add_format({'bold': True}))
    worksheet.write('C5', 'Nombre', workbook.add_format({'bold': True}))
    worksheet.write('D5', 'Grado y Grupo', workbook.add_format({'bold': True}))
    worksheet.write('E5', 'Monto', workbook.add_format({'bold': True}))
    worksheet.write('F5', 'Forma de pago', workbook.add_format({'bold': True}))
    worksheet.write('G5', 'Mes', workbook.add_format({'bold': True}))
    worksheet.write('H5', 'Fecha de Pago', workbook.add_format({'bold': True}))

    # Ajusta el ancho de las columnas
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(str(col)))
        worksheet.set_column(i, i, column_width)

    # Cierra el objeto writer para guardar el archivo correctamente
    writer.close()

    # Lleva la posición del cursor al inicio del BytesIO
    output.seek(0)

    # Guarda el contenido del archivo de Excel en una variable
    excel_data = output.read()

    # Crea una respuesta HTTP con el archivo de Excel adjunto
    response = make_response(excel_data)
    response.headers['Content-Disposition'] = 'attachment; filename=ExcelDiarioEfectivoPrimaria.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return response
@app.route('/export_excelDiarioTransferenciaPrimaria')
def export_excelDiarioTPrimaria():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            E.id AS estudiante_id,
            E.matricula,
            E.nombre AS estudiante_nombre,
            G.nombre AS nombre_grupo,   
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago 
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
            Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND T.fecha_pago >= CURDATE()
            AND E.id_grupo >= 7
            AND T.metodo = 'Transferencia'
    """)

    data3 = cur.fetchall()

    # Crea un DataFrame de pandas con los datos
    df = pd.DataFrame(data3,
                      columns=['ID alumno App', 'Matricula ', 'Nombre ', 'Grado y Grupo', 'Monto', 'Forma de pago',
                               'Mes', 'Fecha de Pago'])

    # Crea un objeto ExcelWriter utilizando XlsxWriter como motor de escritura
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Escribe el DataFrame en una hoja de cálculo Excel
    df.to_excel(writer, sheet_name='ExcelDiarioTransferenciaPrimaria', index=False)

    # Obtener la hoja de trabajo actual
    workbook = writer.book
    worksheet = writer.sheets['ExcelDiarioTransferenciaPrimaria']

    try:

        cur.execute("""SELECT
                    SUM(monto) AS Total
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE()
                    AND E.id_grupo >= 7
                    AND T.metodo = 'Efectivo'""")
        totganado = "${:,.2f}".format(cur.fetchall()[0][0])
    except (IndexError, TypeError):
        totganado = "$0.00"

    # Agregar el título, subtítulo y fecha
    worksheet.merge_range('A1:H1', 'Colegio Felipe Carbajal Arcia', workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
    worksheet.merge_range('A2:H2', 'Reporte Quincenal Preescolar en efectivo', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
    worksheet.merge_range('A3:H3', f'Fecha: {datetime.now().strftime("%Y-%m-%d")}', workbook.add_format({'font_size': 12, 'align': 'center'}))
    worksheet.merge_range('A4:H4', f'Total: {totganado}', workbook.add_format({'bold': True,'font_size': 15, 'align': 'center'}))
    worksheet.write('A5', 'ID alumno App', workbook.add_format({'bold': True}))
    worksheet.write('B5', 'Matricula', workbook.add_format({'bold': True}))
    worksheet.write('C5', 'Nombre', workbook.add_format({'bold': True}))
    worksheet.write('D5', 'Grado y Grupo', workbook.add_format({'bold': True}))
    worksheet.write('E5', 'Monto', workbook.add_format({'bold': True}))
    worksheet.write('F5', 'Forma de pago', workbook.add_format({'bold': True}))
    worksheet.write('G5', 'Mes', workbook.add_format({'bold': True}))
    worksheet.write('H5', 'Fecha de Pago', workbook.add_format({'bold': True}))

    # Ajusta el ancho de las columnas
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(str(col)))
        worksheet.set_column(i, i, column_width)

    # Cierra el objeto writer para guardar el archivo correctamente
    writer.close()

    # Lleva la posición del cursor al inicio del BytesIO
    output.seek(0)

    # Guarda el contenido del archivo de Excel en una variable
    excel_data = output.read()

    # Crea una respuesta HTTP con el archivo de Excel adjunto
    response = make_response(excel_data)
    response.headers['Content-Disposition'] = 'attachment; filename=ExcelDiarioTransferenciaPrimaria.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return response
@app.route('/export_excelQuincenalefectivoPrimaria')
def export_excelQuincenalEPrimaria():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            E.id AS estudiante_id,
            E.matricula,
            E.nombre AS estudiante_nombre,
            G.nombre AS nombre_grupo,   
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago 
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
            Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND T.fecha_pago >= CURDATE() - INTERVAL 15 DAY
            AND E.id_grupo >= 7
            AND T.metodo = 'Efectivo'
    """)

    data3 = cur.fetchall()

    # Crea un DataFrame de pandas con los datos
    df = pd.DataFrame(data3,
                      columns=['ID alumno App', 'Matricula ', 'Nombre ', 'Grado y Grupo', 'Monto', 'Forma de pago',
                               'Mes', 'Fecha de Pago'])

    # Crea un objeto ExcelWriter utilizando XlsxWriter como motor de escritura
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Escribe el DataFrame en una hoja de cálculo Excel
    df.to_excel(writer, sheet_name='ExcelQuincenalEfectivoPrimaria', index=False)

    # Obtener la hoja de trabajo actual
    workbook = writer.book
    worksheet = writer.sheets['ExcelQuincenalEfectivoPrimaria']

    try:

        cur.execute("""SELECT
                    SUM(monto) AS Total
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE() - INTERVAL 15 DAY
                    AND E.id_grupo >= 7
                    AND T.metodo = 'Efectivo'""")
        totganado = "${:,.2f}".format(cur.fetchall()[0][0])
    except (IndexError, TypeError):
        totganado = "$0.00"

    # Agregar el título, subtítulo y fecha
    worksheet.merge_range('A1:H1', 'Colegio Felipe Carbajal Arcia', workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
    worksheet.merge_range('A2:H2', 'Reporte Quincenal Preescolar en efectivo', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
    worksheet.merge_range('A3:H3', f'Fecha: {datetime.now().strftime("%Y-%m-%d")}', workbook.add_format({'font_size': 12, 'align': 'center'}))
    worksheet.merge_range('A4:H4', f'Total: {totganado}', workbook.add_format({'bold': True,'font_size': 15, 'align': 'center'}))
    worksheet.write('A5', 'ID alumno App', workbook.add_format({'bold': True}))
    worksheet.write('B5', 'Matricula', workbook.add_format({'bold': True}))
    worksheet.write('C5', 'Nombre', workbook.add_format({'bold': True}))
    worksheet.write('D5', 'Grado y Grupo', workbook.add_format({'bold': True}))
    worksheet.write('E5', 'Monto', workbook.add_format({'bold': True}))
    worksheet.write('F5', 'Forma de pago', workbook.add_format({'bold': True}))
    worksheet.write('G5', 'Mes', workbook.add_format({'bold': True}))
    worksheet.write('H5', 'Fecha de Pago', workbook.add_format({'bold': True}))

    # Ajusta el ancho de las columnas
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(str(col)))
        worksheet.set_column(i, i, column_width)

    # Cierra el objeto writer para guardar el archivo correctamente
    writer.close()

    # Lleva la posición del cursor al inicio del BytesIO
    output.seek(0)

    # Guarda el contenido del archivo de Excel en una variable
    excel_data = output.read()

    # Crea una respuesta HTTP con el archivo de Excel adjunto
    response = make_response(excel_data)
    response.headers['Content-Disposition'] = 'attachment; filename=ExcelQuincenalEfectivoPrimaria.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return response
@app.route('/export_excelQuincenalTransferenciaPrimaria')
def export_excelQuincenalTPrimaria():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            E.id AS estudiante_id,
            E.matricula,
            E.nombre AS estudiante_nombre,
            G.nombre AS nombre_grupo,   
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago 
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
            Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND T.fecha_pago >= CURDATE() - INTERVAL 15 DAY
            AND E.id_grupo >= 7
            AND T.metodo = 'Transferencia'
    """)

    data3 = cur.fetchall()

    # Crea un DataFrame de pandas con los datos
    df = pd.DataFrame(data3,
                      columns=['ID alumno App', 'Matricula ', 'Nombre ', 'Grado y Grupo', 'Monto', 'Forma de pago',
                               'Mes', 'Fecha de Pago'])

    # Crea un objeto ExcelWriter utilizando XlsxWriter como motor de escritura
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Escribe el DataFrame en una hoja de cálculo Excel
    df.to_excel(writer, sheet_name='ExcelQuincenalTransferenciaPrimaria', index=False)

    # Obtener la hoja de trabajo actual
    workbook = writer.book
    worksheet = writer.sheets['ExcelQuincenalTransferenciaPrimaria']

    try:

        cur.execute("""SELECT
                    SUM(monto) AS Total
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE() - INTERVAL 15 DAY
                    AND E.id_grupo >= 7
                    AND T.metodo = 'Transferencia'""")
        totganado = "${:,.2f}".format(cur.fetchall()[0][0])
    except (IndexError, TypeError):
        totganado = "$0.00"

    # Agregar el título, subtítulo y fecha
    worksheet.merge_range('A1:H1', 'Colegio Felipe Carbajal Arcia', workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
    worksheet.merge_range('A2:H2', 'Reporte Quincenal Preescolar en efectivo', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
    worksheet.merge_range('A3:H3', f'Fecha: {datetime.now().strftime("%Y-%m-%d")}', workbook.add_format({'font_size': 12, 'align': 'center'}))
    worksheet.merge_range('A4:H4', f'Total: {totganado}', workbook.add_format({'bold': True,'font_size': 15, 'align': 'center'}))
    worksheet.write('A5', 'ID alumno App', workbook.add_format({'bold': True}))
    worksheet.write('B5', 'Matricula', workbook.add_format({'bold': True}))
    worksheet.write('C5', 'Nombre', workbook.add_format({'bold': True}))
    worksheet.write('D5', 'Grado y Grupo', workbook.add_format({'bold': True}))
    worksheet.write('E5', 'Monto', workbook.add_format({'bold': True}))
    worksheet.write('F5', 'Forma de pago', workbook.add_format({'bold': True}))
    worksheet.write('G5', 'Mes', workbook.add_format({'bold': True}))
    worksheet.write('H5', 'Fecha de Pago', workbook.add_format({'bold': True}))

    # Ajusta el ancho de las columnas
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(str(col)))
        worksheet.set_column(i, i, column_width)

    # Cierra el objeto writer para guardar el archivo correctamente
    writer.close()

    # Lleva la posición del cursor al inicio del BytesIO
    output.seek(0)

    # Guarda el contenido del archivo de Excel en una variable
    excel_data = output.read()

    # Crea una respuesta HTTP con el archivo de Excel adjunto
    response = make_response(excel_data)
    response.headers['Content-Disposition'] = 'attachment; filename=ExcelQuincenalEfectivoPrimaria.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return response

@app.route('/export_excelMensualEfectivoPrimaria')
def export_excelMensualEPrimaria():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            E.id AS estudiante_id,
            E.matricula,
            E.nombre AS estudiante_nombre,
            G.nombre AS nombre_grupo,   
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago 
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
            Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
            AND E.id_grupo >= 7
            AND T.metodo = 'Efectivo'
    """)

    data3 = cur.fetchall()

    # Crea un DataFrame de pandas con los datos
    df = pd.DataFrame(data3,
                      columns=['ID alumno App', 'Matricula ', 'Nombre ', 'Grado y Grupo', 'Monto', 'Forma de pago',
                               'Mes', 'Fecha de Pago'])

    # Crea un objeto ExcelWriter utilizando XlsxWriter como motor de escritura
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Escribe el DataFrame en una hoja de cálculo Excel
    df.to_excel(writer, sheet_name='ExcelMensualEfectivoPrimaria', index=False)

    # Obtener la hoja de trabajo actual
    workbook = writer.book
    worksheet = writer.sheets['ExcelMensualEfectivoPrimaria']

    try:

        cur.execute("""SELECT
                    SUM(monto) AS Total
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
                    AND E.id_grupo >= 7
                    AND T.metodo = 'Efectivo'""")
        totganado = "${:,.2f}".format(cur.fetchall()[0][0])
    except (IndexError, TypeError):
        totganado = "$0.00"

    # Agregar el título, subtítulo y fecha
    worksheet.merge_range('A1:H1', 'Colegio Felipe Carbajal Arcia', workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
    worksheet.merge_range('A2:H2', 'Reporte Quincenal Preescolar en efectivo', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
    worksheet.merge_range('A3:H3', f'Fecha: {datetime.now().strftime("%Y-%m-%d")}', workbook.add_format({'font_size': 12, 'align': 'center'}))
    worksheet.merge_range('A4:H4', f'Total: {totganado}', workbook.add_format({'bold': True,'font_size': 15, 'align': 'center'}))
    worksheet.write('A5', 'ID alumno App', workbook.add_format({'bold': True}))
    worksheet.write('B5', 'Matricula', workbook.add_format({'bold': True}))
    worksheet.write('C5', 'Nombre', workbook.add_format({'bold': True}))
    worksheet.write('D5', 'Grado y Grupo', workbook.add_format({'bold': True}))
    worksheet.write('E5', 'Monto', workbook.add_format({'bold': True}))
    worksheet.write('F5', 'Forma de pago', workbook.add_format({'bold': True}))
    worksheet.write('G5', 'Mes', workbook.add_format({'bold': True}))
    worksheet.write('H5', 'Fecha de Pago', workbook.add_format({'bold': True}))

    # Ajusta el ancho de las columnas
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(str(col)))
        worksheet.set_column(i, i, column_width)

    # Cierra el objeto writer para guardar el archivo correctamente
    writer.close()

    # Lleva la posición del cursor al inicio del BytesIO
    output.seek(0)

    # Guarda el contenido del archivo de Excel en una variable
    excel_data = output.read()

    # Crea una respuesta HTTP con el archivo de Excel adjunto
    response = make_response(excel_data)
    response.headers['Content-Disposition'] = 'attachment; filename=ExcelMensualEfectivoPrimaria.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return response
@app.route('/export_excelMensualTransferenciaPrimaria')
def export_excelMensualTPrimaria():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            E.id AS estudiante_id,
            E.matricula,
            E.nombre AS estudiante_nombre,
            G.nombre AS nombre_grupo,   
            T.monto,
            T.metodo,
            T.concepto,
            T.fecha_pago 
        FROM
            Estudiante AS E
        JOIN
            Transaccion AS T ON E.id = T.id_estudiante
        JOIN
            Grupo AS G ON E.id_grupo = G.id
        WHERE
            T.pagado = TRUE
            AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
            AND E.id_grupo >= 7
            AND T.metodo = 'Transferencia'
    """)

    data3 = cur.fetchall()

    # Crea un DataFrame de pandas con los datos
    df = pd.DataFrame(data3,
                      columns=['ID alumno App', 'Matricula ', 'Nombre ', 'Grado y Grupo', 'Monto', 'Forma de pago',
                               'Mes', 'Fecha de Pago'])

    # Crea un objeto ExcelWriter utilizando XlsxWriter como motor de escritura
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Escribe el DataFrame en una hoja de cálculo Excel
    df.to_excel(writer, sheet_name='ExcelMensualTransferenciaPrimaria', index=False)

    # Obtener la hoja de trabajo actual
    workbook = writer.book
    worksheet = writer.sheets['ExcelMensualTransferenciaPrimaria']

    try:

        cur.execute("""SELECT
                    SUM(monto) AS Total
                FROM
                    Estudiante AS E
                JOIN
                    Transaccion AS T ON E.id = T.id_estudiante
                JOIN
                    Grupo AS G ON E.id_grupo = G.id
                WHERE
                    T.pagado = TRUE
                    AND T.fecha_pago >= CURDATE() - INTERVAL 1 MONTH
                    AND E.id_grupo >= 7
                    AND T.metodo = 'Efectivo'""")
        totganado = "${:,.2f}".format(cur.fetchall()[0][0])
    except (IndexError, TypeError):
        totganado = "$0.00"

    # Agregar el título, subtítulo y fecha
    worksheet.merge_range('A1:H1', 'Colegio Felipe Carbajal Arcia', workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
    worksheet.merge_range('A2:H2', 'Reporte Quincenal Preescolar en efectivo', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
    worksheet.merge_range('A3:H3', f'Fecha: {datetime.now().strftime("%Y-%m-%d")}', workbook.add_format({'font_size': 12, 'align': 'center'}))
    worksheet.merge_range('A4:H4', f'Total: {totganado}', workbook.add_format({'bold': True,'font_size': 15, 'align': 'center'}))
    worksheet.write('A5', 'ID alumno App', workbook.add_format({'bold': True}))
    worksheet.write('B5', 'Matricula', workbook.add_format({'bold': True}))
    worksheet.write('C5', 'Nombre', workbook.add_format({'bold': True}))
    worksheet.write('D5', 'Grado y Grupo', workbook.add_format({'bold': True}))
    worksheet.write('E5', 'Monto', workbook.add_format({'bold': True}))
    worksheet.write('F5', 'Forma de pago', workbook.add_format({'bold': True}))
    worksheet.write('G5', 'Mes', workbook.add_format({'bold': True}))
    worksheet.write('H5', 'Fecha de Pago', workbook.add_format({'bold': True}))

    # Ajusta el ancho de las columnas
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(str(col)))
        worksheet.set_column(i, i, column_width)

    # Cierra el objeto writer para guardar el archivo correctamente
    writer.close()

    # Lleva la posición del cursor al inicio del BytesIO
    output.seek(0)

    # Guarda el contenido del archivo de Excel en una variable
    excel_data = output.read()

    # Crea una respuesta HTTP con el archivo de Excel adjunto
    response = make_response(excel_data)
    response.headers['Content-Disposition'] = 'attachment; filename=ExcelMensualTransferenciaPrimaria.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return response

if __name__ == "__main__":
    app.run()
