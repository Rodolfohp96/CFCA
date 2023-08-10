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



        # Obtener la lista de estudiantes
    db.execute("SELECT id, id_grupo FROM Estudiante")
    estudiantes = db.fetchall()

    # Recorrer cada estudiante y agregar las transacciones según las condiciones
    for estudiante in estudiantes:
        estudiante_id = estudiante[0]
        id_grupo = estudiante[1]
        monto_colegiatura = 2950 if id_grupo < 6 else 3100

        # Definir las fechas y montos de las transacciones
        transacciones = [
            ("Colegiatura Septiembre", "2023-09-06", "2023-08-28", monto_colegiatura),
            ("Colegiatura Octubre", "2023-10-10", "2023-10-01", monto_colegiatura),
            ("Colegiatura Noviembre", "2023-11-10", "2023-11-01", monto_colegiatura),
            ("Colegiatura Diciembre y Agosto", "2023-12-10", "2023-12-01", monto_colegiatura * 2),
            ("Colegiatura Enero", "2024-01-10", "2024-01-01", monto_colegiatura),
            ("Colegiatura Febrero", "2024-02-10", "2024-02-01", monto_colegiatura),
            ("Colegiatura Marzo", "2024-03-10", "2024-03-01", monto_colegiatura),
            ("Colegiatura Abril", "2024-04-12", "2024-04-01", monto_colegiatura),
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

    # Hacer el commit y cerrar la conexión a la base de datos
    db.connection.commit()

    # Terminar la conexión y retornar
    return 'success'


if __name__ == '__main__':
    setup_app.run(port = 3000, debug = True)
