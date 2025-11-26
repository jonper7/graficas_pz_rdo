import pandas as pd

def process_data(result, columns):
    df = pd.DataFrame(result, columns=columns)
    if not df.empty:

        df.dropna(subset=['fecha_hora'], inplace=True) # Eliminar filas con fechas nulas
        df['date_time'] = pd.to_datetime(df['fecha_hora'], errors='coerce')
        df['elevacion_piezometrica'] = pd.to_numeric(df['elevacion_piezometrica'], errors='coerce')
        df.sort_values('date_time', inplace=True)
    return df


def process_precipitation_data(result, columns):
    df_precip = pd.DataFrame(result, columns=columns)
    if not df_precip.empty:
        # Normalizar nombres a minúsculas
        df_precip.columns = [c.lower() for c in df_precip.columns]
        # Combinar fecha y hora para crear Fecha_Hora
        df_precip['date_time'] = pd.to_datetime(
            df_precip['fecha'].astype(str) + ' ' + df_precip['hora'].astype(str),
            errors='coerce'
        )
        # Eliminar columnas originales si existen
        cols_to_drop = [col for col in ['fecha', 'hora'] if col in df_precip.columns]
        if cols_to_drop:
            df_precip.drop(columns=cols_to_drop, inplace=True)
        df_precip.sort_values('date_time', inplace=True)
    return df_precip
