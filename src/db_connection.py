import psycopg2

def connect_to_db(host, user, password, database, port):
    try:
        conexion = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        conexion.autocommit = True
        return conexion
    except psycopg2.Error as e:
        print(f"Error en la conexión a la base de datos: {e}")
        return None


def execute_query(conexion, query, params=None):
    try:
        cursor = conexion.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        return result, columns
    except psycopg2.Error as e:
        print(f"Error en la ejecución de la consulta: {e}")
        return None, None


def close_connection(conexion):
    if conexion:
        conexion.close()
