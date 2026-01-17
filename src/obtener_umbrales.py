from .db_connection import execute_query

def obtener_umbrales(conexion, id_instrumento):
    """
    Obtiene los umbrales para un instrumento específico de la tabla de umbrales.
    
    Args:
        conexion: Conexión a la base de datos PostgreSQL
        id_instrumento: ID del instrumento (string)
    
    Returns:
        dict: Diccionario con claves 'nivel_umbral_1', 'nivel_umbral_2', 'nivel_umbral_3'
              y sus valores correspondientes. Si no hay datos o todos son NULL, retorna None.
    """
    try:
        query = f'''
            SELECT 
                nivel_umbral_1, 
                nivel_umbral_2, 
                nivel_umbral_3
            FROM "MV_PIEZOMETROS"."02_umbrales_pz"
            WHERE id_instrumento = '{id_instrumento}'
            ORDER BY fecha_actualizacion DESC
            LIMIT 1
        '''
        
        result, columns = execute_query(conexion, query)
        
        if not result:
            print(f"⚠️ No hay umbrales registrados para {id_instrumento}")
            return None
        
        nivel_umbral_1, nivel_umbral_2, nivel_umbral_3 = result[0]
        
        # Validar si TODOS los umbrales son None
        if nivel_umbral_1 is None and nivel_umbral_2 is None and nivel_umbral_3 is None:
            print(f"⚠️ Todos los umbrales son NULL para {id_instrumento}")
            return None
        
        umbrales = {
            "nivel_umbral_1": nivel_umbral_1,
            "nivel_umbral_2": nivel_umbral_2,
            "nivel_umbral_3": nivel_umbral_3
        }
        
        return umbrales
        
    except Exception as e:
        print(f"Error al obtener umbrales para {id_instrumento}: {e}")
        return None