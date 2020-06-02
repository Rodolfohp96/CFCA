from flask import Flask
from flask_mysqldb import MySQL

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

@setup_app.route('/setup')
def setup_db():
    db = mysql.connection.cursor()

    # Drop all tables
    db.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \'{}\''.format(DB_NAME))
    all_tables = db.fetchall()
    print(all_tables)
    for tables in all_tables:
        for table in tables:
            print('Deleting table: {}'.format(table))
            db.execute('DROP TABLE IF EXISTS {}'.format(table));
    
    # Show empty
    db.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \'{}\''.format(DB_NAME))
    data = db.fetchall()
    print(data)

    # Crear las tablas

    # Grupo
    db.execute("""CREATE TABLE Grupo (
        id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
        nombre VARCHAR(50) NOT NULL,
        grado: INT
        )""")

    # Grupo_Materia
    db.execute("""CREATE TABLE Grupo_Materia (
        id_grupo INT NOT NULL,
        id_materia INT NOT NULL,
        FOREIGN KEY (id_grupo) REFERENCES Grupo(id),
        FOREIGN KEY (id_materia) REFERENCES Materia(id)
        )""")

    # Materia
    db.execute("""CREATE TABLE Materia (
        id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
        nombre VARCHAR(50) NOT NULL,
        id_maestro INT,
        hora_entrada TIME,
        hora_salida TIME
        )""")

    # Anadir info a las tablas
    db.execute("""INSERT INTO example (name)
        VALUES
            ("NameA"),
            ("NameB")
        """)

    db.connection.commit()
    # Terminar la conexion
    return 'success'

if __name__ == '__main__':
    setup_app.run(port = 3000, debug = True)
