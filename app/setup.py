import csv

from flask import Flask
from flask_mysqldb import MySQL
import datetime
from datetime import datetime
from datetime import date, timedelta


from random import randint, uniform
from dotenv import load_dotenv


load_dotenv()

# Global variables
HOST_NAME = 'sql5.freemysqlhosting.net'
USER_NAME = 'sql5521421'
USER_PASS = '2DQeK4zHLZ'
DB_NAME = 'sql5521421'

setup_app = Flask(__name__)
setup_app.config['MYSQL_HOST'] = HOST_NAME
setup_app.config['MYSQL_USER'] = USER_NAME
setup_app.config['MYSQL_PASSWORD'] = USER_PASS
setup_app.config['MYSQL_DB'] = DB_NAME

mysql = MySQL(setup_app)




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



def gbool(n):
    nrand = randint(0, n)
    eval_ = "FALSE" if nrand > 0 else "TRUE"
    return eval_



@setup_app.route('/setup')
def setup_db():
    db = mysql.connection.cursor()

    # Drop all tables
    db.execute('SET FOREIGN_KEY_CHECKS = 0')
    db.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \'{}\''.format(DB_NAME))
    all_tables = db.fetchall()

    for tables in all_tables:
        for table in tables:
            print('Deleting table: {}'.format(table))
            db.execute('DROP TABLE IF EXISTS {}'.format(table));
    db.execute('SET FOREIGN_KEY_CHECKS = 0')
    # Show empty
    db.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \'{}\''.format(DB_NAME))
    data = db.fetchall()


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
        fecha_de_nacimiento DATE,
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
        nombre VARCHAR(50) ,
        parentesco VARCHAR(50) ,
        correo VARCHAR(100) ,
        telefono VARCHAR(20) ,
        direccion VARCHAR(200) ,
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
            # Lista de estudiantes a ingresar

    db = mysql.connection.cursor()

    def convert_to_none(value):
        if value and value != 'None':
            if value.isdigit():
                return int(value)
            return value
        return None



    # ...

    with open('BaseCentralizadaCFCA.csv', 'r', newline='', encoding='utf-8') as csvfile:

        csvreader = csv.DictReader(csvfile, delimiter=',')
        print(csvfile)

        for row in csvreader:
            print(row)
            fecha_de_nacimiento = None
            if row['fecha_de_nacimiento'] and row['fecha_de_nacimiento'] != 'None':
                fecha_de_nacimiento = datetime.strptime(row['fecha_de_nacimiento'], '%Y-%m-%d').date()

            beca = convert_to_none(row['beca'])
            grado = convert_to_none(row['grado'])
            id_grupo = convert_to_none(row['id_grupo'])

            estudiante_data = (
                row['\ufeffnombre_alumno'], fecha_de_nacimiento, beca,
                grado, id_grupo, row['matricula'], row['password']
            )

            # Insertar datos en la tabla Estudiante
            insert_estudiante = """INSERT INTO Estudiante (nombre, fecha_de_nacimiento, beca, grado, id_grupo, matricula, password) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            db.execute(insert_estudiante, estudiante_data)
            estudiante_id = db.lastrowid  # Obtener el ID del estudiante insertado

            # Insertar datos en la tabla Contacto (si es necesario)
            if row['nombre_contacto']:
                # Resto de la inserción de datos en Contacto
                # ...
                insert_contacto = (
                    "INSERT INTO Contacto (nombre, parentesco, correo, telefono, direccion, id_estudiante) "
                    "VALUES (%s, %s, %s, %s, %s, %s)"
                )
                contacto_data = (
                    row['nombre_contacto'], row['parentesco_contacto'], row['correo_contacto'],
                    row['telefono_contacto'], row['direccionFact'], estudiante_id
                )
                db.execute(insert_contacto, contacto_data)
                contacto_id = db.lastrowid  # Obtén el ID del contacto insertado

                # Inserta datos en la tabla Estudiante_Contacto
                insert_estudiante_contacto = (
                    "INSERT INTO Estudiante_Contacto (id_estudiante, id_contacto, parentesco, es_responsable) "
                    "VALUES (%s, %s, %s, %s)"
                )
                estudiante_contacto_data = (
                    estudiante_id, contacto_id, row['parentesco_contacto'], True
                )  # Aquí asumo que el primer contacto es responsable
                db.execute(insert_estudiante_contacto, estudiante_contacto_data)

                # Inserta el segundo contacto si está presente
                if row['nombre_contacto2']:
                    insert_contacto2 = (
                        "INSERT INTO Contacto (nombre, parentesco, correo, telefono, direccion, id_estudiante) "
                        "VALUES (%s, %s, %s, %s, %s, %s)"
                    )
                    contacto_data2 = (
                        row['nombre_contacto2'], row['parentesco_contacto2'], row['correo_contacto2'],
                        row['telefono_contacto2'], row['direccion_contacto2'], estudiante_id
                    )
                    db.execute(insert_contacto2, contacto_data2)
                    contacto_id2 = db.lastrowid  # Obtén el ID del segundo contacto insertado

                    # Inserta datos en la tabla Estudiante_Contacto para el segundo contacto
                    insert_estudiante_contacto2 = (
                        "INSERT INTO Estudiante_Contacto (id_estudiante, id_contacto, parentesco, es_responsable) "
                        "VALUES (%s, %s, %s, %s)"
                    )
                    estudiante_contacto_data2 = (
                        estudiante_id, contacto_id2, row['parentesco_contacto2'], False
                    )  # Aquí asumo que el segundo contacto no es responsable
                    db.execute(insert_estudiante_contacto2, estudiante_contacto_data2)

            # Truncate the "Transaccion" table
            db.execute('TRUNCATE TABLE Transaccion')

            # Obtener la lista de estudiantes
            db.execute("SELECT id, id_grupo FROM Estudiante")
            estudiantes = db.fetchall()

            # Recorrer cada estudiante y agregar las transacciones según las condiciones
            for estudiante in estudiantes:
                estudiante_id = estudiante[0]
                id_grupo = estudiante[1]
                monto_colegiatura = 2750 if id_grupo < 6 else 2800
                montoreeinscripcion = 2750 if id_grupo < 4 else 2800

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
                        (monto, nombre, fecha_limite, fecha_activacion, False, False, estudiante_id))

            db.connection.commit()

    # Hacer el commit y cerrar la conexión a la base de datos
    db.connection.commit()

    # Terminar la conexión y retornar
    return 'success'


if __name__ == '__main__':
    setup_app.run(port = 3000, debug = True)
