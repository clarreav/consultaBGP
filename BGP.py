from datetime import datetime
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode
import telnetlib


# Metodo de conexion a la DB
def sql_connection():
    try:
        cona = mysql.connector.connect(host='127.0.0.1', user='root', password='Icc3u0qk')

        CurObj = cona.cursor()

        CurObj.execute("SHOW DATABASES")
        record = [item[0] for item in CurObj.fetchall()]
        if 'bgp' in record:
            print("Conexion exitosa con la base de datos")
            return mysql.connector.connect(host='127.0.0.1', database='BGP', user='root',
                                           password='Icc3u0qk')
        else:
            cona = mysql.connector.connect(host='127.0.0.1', user='root', password='Icc3u0qk')

            CurObj = cona.cursor()
            CurObj.execute("CREATE DATABASE BGP")
            cona.commit()

            print("Se creo la db BGP")

            return mysql.connector.connect(host='127.0.0.1', database='BGP', user='root',
                                           password='Icc3u0qk')
    except Error as e:
        print("No se pudo realizar la conexion con la base de datos ", e)


# Metodo para la creacion de tablas en la DB
def sql_table():
    cona = sql_connection()

    CurObj = cona.cursor()
    CurObj.execute("SHOW TABLES;")
    # CurObj.execute("DROP TABLE DatosBGP;")
    record = [item[0] for item in CurObj.fetchall()]
    CurObj.close()
    cona.close()
    if 'datosbgp' in record:
        print("La tabla DatosBGP ya existe en la DB.")
    else:
        # Se crea un diccionario que almacene las estructuras de las tablas
        TABLES = {}
        TABLES['DatosBGP'] = (
            "CREATE TABLE `DatosBGP` ("
            "  `id` double NOT NULL AUTO_INCREMENT,"
            "  `red` varchar(100) NOT NULL,"
            "  `version` varchar(100) NOT NULL,"
            "  `importedpath` varchar(100) NOT NULL,"
            "  `bestroute` varchar(100) NOT NULL,"
            "  `origin` varchar(100) NOT NULL,"
            "  `community` varchar(300) NOT NULL,"
            "  `originator` varchar(100) NOT NULL,"
            "  `clusterlist` varchar(100) NOT NULL,"
            "  `rxpathid` varchar(100) NOT NULL,"
            "  `txpathid` varchar(100) NOT NULL,"
            "  `fecha` varchar(100) NOT NULL,"
            "  PRIMARY KEY (`id`)"
            ") ENGINE=InnoDB")
        con = sql_connection()
        cursor = con.cursor()
        # Se ejecuta la estructura de cada tabla con la finalidad de crearlas
        for table_name in TABLES:
            table_description = TABLES[table_name]
            try:
                print("Creando tabla {}: ".format(table_name), end='')
                cursor.execute(table_description)
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print("ya existe tabla.")
                else:
                    print(err.msg)
            else:
                print("OK")
        cursor.close()
        con.close()

# Metodo de conexion de telnet con router publico
def telnet():
    # Direccion ip del router
    HOST_IP = "route-server.gvt.net.br"
    # Usuario para ingresar al servidor de telnet (gvt_view)
    host_user = input("Enter your telnet username: ")
    # Contrasena para ingresar al servidor de telnet (gvt_view)
    password = input("Enter your telnet password: ")
    # Conexion con telnet
    t = telnetlib.Telnet(HOST_IP)
    t.read_until(b"Username:")
    t.write(host_user.encode("ascii") + b"\n")
    t.read_until(b"Password:")
    t.write(password.encode("ascii") + b"\n")
    # Comando para la lectura de la RIB de la red 1.0.0.0
    t.write(b"sh bgp ipv4 unicast 8.8.8.8\n")
    t.write(b"exit\n")
    # Lectura de la ejecucion de los comandos
    res = t.read_all().decode("ascii")
    return res


def main():
    # sql_connection()
    # Elaboracion de la tabla de datos BGP
    sql_table()
    # Lectura de los comandos de telnet
    lectura = telnet()
    # Separacion por lineas de los comandos
    separado = lectura.split("\n")
    # Conexion a la DB
    conector = sql_connection()
    # Inicializacion de parametros para el cursor
    red = ""
    version = ""
    importedpath = ""
    bestroute = ""
    origin = ""
    community = ""
    originator = ""
    cluster = ""
    rx = ""
    tx = ""
    fecha=datetime.strftime(datetime.now(),"%d/%m/%Y")
    # Lectura de campos de cada linea
    for el in separado:
        print(el)
        separacion2 = el.split(" ")
        for i in range(len(separacion2)):
            if separacion2[i] == "for":
                red = separacion2[i + 1][:-1]
            if separacion2[i] == "version":
                version = separacion2[i + 1][:-2]
            if separacion2[i] == "by":
                importedpath = separacion2[i + 1] + " " + separacion2[i + 2][:-2]
            if separacion2[i] == "from":
                bestroute = separacion2[i + 1] + " " + separacion2[i + 2][:-1]
            if separacion2[i] == "Origin":
                origin = separacion2[i + 1][:-1]
            if separacion2[i] == "Community:":
                community = ' '.join(str(x) for x in separacion2[i + 1:])[:-2]
            if separacion2[i] == "Originator:":
                originator = separacion2[i + 1][:-1]
            if separacion2[i] == "list:":
                cluster = ' '.join(str(x) for x in separacion2[i + 1:])[:-2]
            if separacion2[i] == "rx":
                rx = separacion2[i + 2][:-1]
            if separacion2[i] == "tx":
                tx = separacion2[i + 2][:-2]
    # Creacion del cursor
    cursor = conector.cursor()
    # Instruccion para ejecutar
    query = ("INSERT INTO DatosBGP "
             "(red, version, importedpath, bestroute, origin, community, originator, clusterlist, rxpathid, "
             "txpathid, fecha) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    datos = (red, version, importedpath, bestroute, origin, community, originator, cluster, rx, tx, fecha)
    cursor.execute(query, datos)
    conector.commit()
    cursor.close()
    print("Ingreso exitoso.")
    cursor = conector.cursor()
    # Muestra de los datos almacenados
    cursor.execute("SELECT * FROM DatosBGP")
    record = cursor.fetchall()
    print("Datos de la tabla: \n")
    for el in record:
        print(el)
    cursor.close()
    conector.close()


if __name__ == "__main__":
    main()
