# Centro Escolar Del Valle Del Mezquital - instalacion del codigo


## Pasos para empezar

- Installar MAMP
- pip3 install flask flask-mysqldb
- resolver problemas con la insalacion de flask-mysql
    - Problemas dependientes de la insalacion local de mysql.
    - Problemas en mac. MAMP necesita un system link de archivos .sock a /usr/
    - En linux instalar con apt libmysqlclient-dev
    - En Windows revisar que la instalacion de cpp sea correcta
    - En windows revisar las versiones de pip3 o python


## Para empezar la base de datos

- Con MAMP (que usamos en clase), acceder a myPHP admin
- Crear una database escueladb y un usuario: admin con password: adminpass 
- O impotar el dump

## Setup de la base de datos
- Iniciar servers con MAMP.
- python setup.py
    - Es una app de flask separada que corre en localhost:3000/setup
    - **Borra todas las tablas en la db**
    - Crea nuevas tablas
    - Inserta datos en las tablas
- ***Es necesario abrir y correr localhost:3000/setup o haber importado el dump a mysql***
## Para correr

- python app.py
- en el navegador localhost:3000
- Asegurarse que MAMP este corriendo
- Hay un login para devs (usr, pass): devadmin, dev$admin

