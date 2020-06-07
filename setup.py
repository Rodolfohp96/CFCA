from flask import Flask
from flask_mysqldb import MySQL

from random import randint

# Global variables
HOST_NAME = 'localhost'
USER_NAME = 'admin'
USER_PASS = 'adminpass'
DB_NAME = 'escueladb'

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

def gdate(_year):
    month = "{:02d}".format(randint(1, 12))
    day = "{:02d}".format(randint(1, 28))
    return "{}-{}-{}".format(_year, month, day)

def grstr():
    return "random str{}".format(randint(0,100))

def gphone():
    return "55 {} {} {}".format(randint(10,55),randint(10,55),randint(10,55))


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
        FOREIGN KEY(id_grupo) REFERENCES Grupo(id)
        )""")

    # Contacto
    db.execute("""CREATE TABLE Contacto (
        id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
        nombre VARCHAR(50) NOT NULL,
        correo VARCHAR(100) NOT NULL,
        telefono INT NOT NULL,
        direccion VARCHAR(100) NOT NULL,
        id_estudiante INT NOT NULL,
        FOREIGN KEY (id_estudiante) REFERENCES Estudiante(id)
        )""")


    # Transaccion
    db.execute(
        """CREATE TABLE Transaccion (
        id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
        monto INT NOT NULL,
        metodo VARCHAR(50),
        fecha_limite DATE,
        pagado Bool,
        id_estudiante INT NOT NULL,
        id_responsable INT NOT NULL,
        FOREIGN KEY (id_estudiante) REFERENCES Estudiante(id),
        FOREIGN KEY (id_responsable) REFERENCES Contacto(id)
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

    # Crea estudiantes y grupos
    for ngrado in range(6):
        mask_grupo = ["A", "B"]
        for ngrupo in range(2):
            numgrado = ngrado + 1
            nomgrupo = "{} {}".format(numgrado, mask_grupo[ngrupo])
            db.execute("""INSERT INTO Grupo (nombre, grado)
                            VALUES (\"{}\",{})""".format(nomgrupo, numgrado))
            size = randint(27, 32)
            for nestud in range(size):
                idgrupo = ngrupo + 2 * ngrado + 1
                idestud = (nestud + 1) + (30 * (idgrupo - 1))
                nacyear = 2013 - ngrado
                nomestud = gname()
                nacestud = gdate(nacyear)
                bestud = randint(1,8) * 10
                db.execute("""INSERT INTO Estudiante (nombre, fecha_de_nacimiento, beca, id_grupo)
                    VALUES
                        (\"{}\", \"{}\", {}, {})
                    """.format(nomestud, nacestud, bestud, idgrupo))



    db.connection.commit()
    # Terminar la conexion
    return 'success'

if __name__ == '__main__':
    setup_app.run(port = 3000, debug = True)
