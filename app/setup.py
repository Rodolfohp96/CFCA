from flask import Flask
from flask_mysqldb import MySQL
import datetime
from datetime import date, timedelta


from random import randint, uniform
from dotenv import load_dotenv


load_dotenv()

# Global variables
HOST_NAME = 'sql9.freemysqlhosting.net'
USER_NAME = 'sql9637135'
USER_PASS = 'ArmH1XNQd7'
DB_NAME = 'sql9637135'

setup_app = Flask(__name__)
setup_app.config['MYSQL_HOST'] = HOST_NAME
setup_app.config['MYSQL_USER'] = USER_NAME
setup_app.config['MYSQL_PASSWORD'] = USER_PASS
setup_app.config['MYSQL_DB'] = DB_NAME

mysql = MySQL(setup_app)

NAMES = ["Juan", "José Luis", "José", "María Guadalupe", "Francisco", "Guadalupe", "María", "Juana", "Antonio", "Jesús", "Miguel Ángel", "Pedro", "Alejandro", "Manuel", "Margarita", "María del CARMEN", "Juan Carlos", "Roberto", "Fernando", "Daniel", "Carlos", "Jorge", "Ricardo", "Miguel", "Eduardo", "Javier", "Rafael", "Martín", "Raúl", "David", "Josefina", "José Antonio", "Arturo", "Marco Antonio", "José Manuel", "Francisco Javier", "Enrique", "Verónica", "Gerardo", "María Elena", "Leticia", "Rosa", "Mario", "Francisca"]
LASTNAMES = ["Martinez", "Lopez", "Gonzalez", "Perez", "Rodriguez", "Sanchez", "Ramirez", "Cruz", "Flores", "Gomez"]

def gname():
    nname = randint(0,9)
    nalast = randint(0,9)
    nblast = randint(0,9)
    while nalast == nblast:
        nblast = randint(0,9)
    return "{} {} {}".format(NAMES[nname], LASTNAMES[nalast], LASTNAMES[nblast])

def gemail(_str, n):
    return "{}{}@email.com".format(_str, n)

def gbdate(_year):
    month = "{:02d}".format(randint(1, 12))
    day = "{:02d}".format(randint(1, 28))
    return "{}-{}-{}".format(_year, month, day)

def grstr():
    return "random str{}".format(randint(0,100))

def gphone():
    return int("55{}{}{}".format(randint(10,55),randint(10,55),randint(10,55)))

def gamount(grado):
    if grado < 3:
        return 2750.00
    elif grado < 6:
        return 2800.00
    return 2800.00

def ginscripcion(grado):
    if grado < 3:
        return 2950.00
    elif grado < 6:
        return 3100.00
    return 3100.00
def gColeg(grado):
    if grado < 3:
        return 2750.00
    elif grado < 6:
        return 2800.00
    return 2800.00
def glibreta(grado):
    if grado < 3:
        return 65.00
    elif grado < 6:
        return 65.00
    return 65.00
def calculate_recargo(mes, dia, pago_normal):
    recargo = 0
    if mes > 10:
        recargo += 200
    elif mes > 5:
        recargo += 100
    if dia > 10:
        recargo += 200
    return recargo
def gmetodo():
    metodos = ["Transferencia", "Tarjeta de Credito", "Efectivo", "Cheque"]
    nmet = randint(0, 3)
    return metodos[nmet]

def gfdate():
    return "2023-12-12"

def gbool(n):
    nrand = randint(0, n)
    eval_ = "FALSE" if nrand > 0 else "TRUE"
    return eval_

def gdir():
    ncalle = randint(0,9)
    calle = LASTNAMES[ncalle]
    num = randint(12, 501)
    ncol = randint(0,9)
    col = LASTNAMES[ncol]
    zip_ = randint(10512, 98950)
    return "Calle {} {}, Col. {}. C.P.{}, HGO".format(calle, num, col, zip_)
    
def gparentesco():
    PAR = ["padre", "tio", "tia", "hermano", "hermana"]
    npar = randint(0,4)
    return PAR[npar]

@setup_app.route('/setup')
def setup_db():
    db = mysql.connection.cursor()

    # Drop all tables
    db.execute('SET FOREIGN_KEY_CHECKS = 0')
    db.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \'{}\''.format(DB_NAME))
    all_tables = db.fetchall()
    print(all_tables)
    for tables in all_tables:
        for table in tables:
            print('Deleting table: {}'.format(table))
            db.execute('DROP TABLE IF EXISTS {}'.format(table));
    db.execute('SET FOREIGN_KEY_CHECKS = 0')
    # Show empty
    db.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \'{}\''.format(DB_NAME))
    data = db.fetchall()
    print(data)

    # Crear las tablas

    # Account
    db.execute(
        """CREATE TABLE Account (
        id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
        username VARCHAR(50) NOT NULL,
        password VARCHAR(50) NOT NULL
        )"""
    )

    # Maestro
    db.execute(
        """CREATE TABLE Maestro (
        id_maestro INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
        nombre VARCHAR(50) NOT NULL,
        correo VARCHAR(50) NOT NULL,
        fecha_de_nacimiento DATE
        )"""
    )

    # Grupo
    db.execute("""CREATE TABLE Grupo (
        id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
        nombre VARCHAR(50) NOT NULL,
        grado INT
        )""")

    # Estudiante
    db.execute("""CREATE TABLE Estudiante (
        id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
        nombre VARCHAR(50) NOT NULL, 
        fecha_de_nacimiento DATE NOT NULL,
        beca INT,
        grado INT,
        id_grupo INT NOT NULL,
        matricula INT,
        password VARCHAR(50),
        FOREIGN KEY(id_grupo) REFERENCES Grupo(id)
        )""")

    # Contacto
    db.execute("""CREATE TABLE Contacto (
        id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
        nombre VARCHAR(50) NOT NULL,
        parentesco VARCHAR(50) NOT NULL,
        correo VARCHAR(100) NOT NULL,
        telefono VARCHAR(20) NOT NULL,
        direccion VARCHAR(200) NOT NULL,
        razonSocial VARCHAR(200),
        regimenFiscal VARCHAR(200),
        cfdi VARCHAR(200),
        rfc VARCHAR(200),
        cp VARCHAR(200),
        direccionFact VARCHAR(200),
        id_estudiante INT NOT NULL,
        FOREIGN KEY (id_estudiante) REFERENCES Estudiante(id) ON DELETE CASCADE
        )""")


    # Transaccion
    db.execute(
        """CREATE TABLE Transaccion (
        id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
        monto FLOAT NOT NULL,
        metodo VARCHAR(50),
        concepto VARCHAR(200),
        fecha_limite DATE,
        fecha_pago DATE,
        fechaActivacion DATE,
        activado Bool,
        pagado Bool,
        id_estudiante INT NOT NULL,
        FOREIGN KEY (id_estudiante) REFERENCES Estudiante(id) ON DELETE CASCADE
        )"""
    )

    # Materia
    db.execute("""CREATE TABLE Materia (
        id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
        nombre VARCHAR(50) NOT NULL,
        id_maestro INT NOT NULL,
        hora_entrada TIME,
        hora_salida TIME
        )""")

    # Grupo_Materia
    db.execute("""CREATE TABLE Grupo_Materia (
        id_grupo INT NOT NULL,
        id_materia INT NOT NULL,
        FOREIGN KEY (id_grupo) REFERENCES Grupo(id),
        FOREIGN KEY (id_materia) REFERENCES Materia(id)
        )""")

    # Estudiante_Contacto
    db.execute("""CREATE TABLE Estudiante_Contacto (
        id_estudiante INT NOT NULL,
        id_contacto INT NOT NULL,
        parentesco VARCHAR(50) NOT NULL,
        es_responsable BOOLEAN  NOT NULL,
        FOREIGN KEY(id_estudiante) REFERENCES Estudiante(id),
        FOREIGN KEY(id_contacto) REFERENCES Contacto(id)
        )""")

    # Inserta accounts
    db.execute("""INSERT INTO Account (username, password)
                    VALUES ("direccion2023", "dir$$2023"),
                            ("devadmin", "dev$admin")""")

    # Inserta estudiantes y grupos
    for ngrado in range(9):
        mask_grupo = ["A", "B"]
        for ngrupo in range(2):
            numgrado = ngrado + 1
            namgrado = ""
            if numgrado < 4:
                namgrado = "Preescolar {}".format(numgrado)
            else:
                namgrado = "{}".format(numgrado - 3)
            nomgrupo = "{} {}".format(namgrado, mask_grupo[ngrupo])
            db.execute("""INSERT INTO Grupo (nombre, grado)
                            VALUES (\"{}\",{})""".format(nomgrupo, numgrado))
            for nestud in range(20):
                idgrupo = ngrupo + 2 * ngrado + 1
                idestud = (nestud + 1) + (20 * (idgrupo - 1))
                nacyear = 2013 - ngrado
                nomestud = gname()
                nacestud = gbdate(nacyear)
                bestud = randint(0,4) * 10
                mat  = numgrado + 15
                passw = str(numgrado) + '$$2023'
                db.execute("""INSERT INTO Estudiante (nombre, fecha_de_nacimiento, beca,matricula, password, id_grupo)
                    VALUES
                        (\"{}\", \"{}\", {},{},"\{}\", {})
                    """.format(nomestud, nacestud, bestud,mat, passw , idgrupo))

                apagado = gbool(4)
                ametodo = gmetodo() if apagado == "TRUE" else ""
                desc = 1 - bestud / 100
                amount = gamount(ngrado) * desc
                amountins = ginscripcion(ngrado)
                amountlib = glibreta(ngrado)

                fecha_activacion = date(2023, 9, 1)
                # Monto inicial
                monto_colegiatura = amount
                # Crear 10 colegiaturas
                for mes in range(1, 11):
                    # Obtener la fecha de pago (10 de cada mes)
                    fecha_pago = date(2023, mes, 10).strftime('%Y-%m-%d')
                    # Obtener la fecha de activación (1 de cada mes)
                    fecha_activacion = date(2023, mes, 1).strftime('%Y-%m-%d')

                    # Multiplicar el monto por 2 para las colegiaturas 4 y 10 y ajustar las fechas a 2024
                    if mes in [4, 10]:
                        monto_colegiatura *= 2
                        fecha_activacion = date(2024, mes, 1).strftime('%Y-%m-%d')
                        fecha_pago = date(2024, mes, 10).strftime('%Y-%m-%d')

                    # Insertar la colegiatura en la base de datos
                    db.execute("""INSERT INTO Transaccion 
                                        (monto, metodo, concepto, fecha_limite, fecha_pago, fechaActivacion,activado, pagado, id_estudiante)
                                        VALUES (%(monto)s, "", %(concepto)s, %(fecha_limite)s, %(fecha_pago)s, %(fecha_activacion)s, %(activado)s, %(pagado)s, %(id_estudiante)s)
                                    """, {
                        'monto': monto_colegiatura,
                        'concepto': "Colegiatura {}".format(mes),
                        'fecha_limite': fecha_pago,
                        'fecha_pago': fecha_pago,
                        'fecha_activacion': fecha_activacion,
                        'activado': 0,  # Valor entero 0 para False,
                        'pagado': 0,  # Valor entero 0 para False
                        'id_estudiante': idestud,
                    })



                # db.execute("""INSERT INTO Transaccion
                #                                 (monto, metodo, concepto, fecha_limite, pagado, id_estudiante)
                #                                 VALUES ({}, \"{}\", \"{}\", \"{}\", {}, {})
                #                             """.format(amountins, ametodo, "Inscripción", gfdate(), apagado,
                #                                        idestud))
                # db.execute("""INSERT INTO Transaccion
                #                                                 (monto, metodo, concepto, fecha_limite, pagado, id_estudiante)
                #                                                 VALUES ({}, \"{}\", \"{}\", \"{}\", {}, {})
                #                                             """.format(amountlib, ametodo, "Libreta", gfdate(),
                #                                                        apagado,
                #                                                        idestud))
                nomacon = gname()
                mailacon = "{}@mail.com".format(gname().split(" ")[0].lower())
                nombcon = gname()
                mailbcon = "{}@mail.com".format(gname().split(" ")[0].lower())
                db.execute("""INSERT INTO Contacto
                                    (nombre, parentesco, correo, telefono, direccion, id_estudiante)
                                    VALUES 
                                    (\"{}\",\"{}\",\"{}\", \"{}\", \"{}\", {}),
                                    (\"{}\",\"{}\",\"{}\", \"{}\", \"{}\", {}) 
                            """.format(nomacon, gparentesco(), mailacon, gphone(), gdir(), idestud, nombcon, gparentesco(), mailbcon, gphone(), gdir(), idestud))
    db.connection.commit()
    # Terminar la conexion
    return 'success'

if __name__ == '__main__':
    setup_app.run(port = 3000, debug = True)
