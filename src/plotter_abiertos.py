import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
import matplotlib.ticker as ticker
from scipy.interpolate import make_interp_spline, UnivariateSpline

import numpy as np
import pandas as pd

from .excluir_umbral import no_graficar_umbral
from .obtener_umbrales import obtener_umbrales

def plot_data(df, df_precip, tabla, fecha_inicio, fecha_fin, conexion=None, excel_path=None, sheet_name=None, cell=None):
    
    # Crear una figura y un eje
    fig, ax1 = plt.subplots(figsize=(14, 7))
    plt.style.use('bmh')  # Estilo de Seaborn

    # FILTRAR POR RANGO DE FECHAS
    fecha_inicio_dt = pd.to_datetime(fecha_inicio)
    fecha_fin_dt = pd.to_datetime(fecha_fin)
    df = df[(df['date_time'] >= fecha_inicio_dt) & (df['date_time'] <= fecha_fin_dt)]
    
    # Filtrar datos válidos
    datos_validos = df[['date_time', 'elevacion_piezometrica']].dropna().drop_duplicates(subset='date_time', keep='last')
    if datos_validos.empty:
        print(f"⚠️ No hay datos válidos para graficar en {tabla}")
        return None
    
    # --------------------------------------------------------------------
    # CONFIGURACIÓN DE UMBRALES
    # --------------------------------------------------------------------
    graficar_umbrales = tabla not in no_graficar_umbral
    umbrales_disponibles = None  

    if graficar_umbrales and conexion:  
        try:
            umbrales_disponibles = obtener_umbrales(conexion, tabla)
            if umbrales_disponibles:
                print(f"✓ Umbrales obtenidos de BD para {tabla}")
            else:
                print(f"⚠ No se encontraron umbrales en BD para {tabla}")
        except Exception as e:
            print(f"Error al obtener umbrales de BD para {tabla}: {e}")
            umbrales_disponibles = None
        
    elif graficar_umbrales and not conexion:
        umbrales_disponibles = {}  # Inicializar como diccionario vacío
        for col in ['nivel_umbral_1', 'nivel_umbral_2', 'nivel_umbral_3']:
            if col in df.columns:
                valor_umbral = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if valor_umbral is not None:
                    umbrales_disponibles[col] = valor_umbral
        
        if umbrales_disponibles:
            print(f"✓ Umbrales obtenidos del DataFrame para {tabla}")
        else:
            print(f"⚠️ No hay umbrales disponibles para {tabla}")
    else:
        print(f"ℹ️ Umbrales excluidos para {tabla}")

    # Graficar líneas de umbrales
    if umbrales_disponibles:
        for alerta, valor in umbrales_disponibles.items():
            if valor is not None:
                color = {
                    'nivel_umbral_1': 'yellow',
                    'nivel_umbral_2': 'orange',
                    'nivel_umbral_3': 'red'
                }.get(alerta, 'gray')
                
                ax1.axhline(y=valor, color=color, linestyle='--', linewidth=1.5, zorder=2)

    # ===================================================================================================================
    # CONFIGURACIÓN DEL EJE Y1 (Elevación Piezométrica)
    # ===================================================================================================================

    # Configurar los decimales del eje Y primario
    ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))

    ## Graficar los datos con línea suavizada ##
    x = mdates.date2num(datos_validos['date_time']) # Convertir fechas a números
    y = datos_validos['elevacion_piezometrica'].values 

    # # Suavizar la línea si hay más de 3 puntos
    if len(x) > 3: 
        x_suave = np.linspace(x.min(), x.max(), 200) 
        spl = make_interp_spline(x, y, k=3) # Spline cúbica
        y_suave = spl(x_suave) 
  
        # Graficar línea suavizada
        serie1, = ax1.plot(mdates.num2date(x_suave), y_suave, 
                color="#00008B", 
                linewidth=2, 
                label="Nivel Freático",
                zorder=2)

        # Graficar puntos originales
        ax1.plot(datos_validos['date_time'], 
                y, 'o',   
                markersize=5.2,
                color='#00008B', 
                label='Datos originales',
                zorder=4  # Puntos sobre la línea
                )
    else:
        # Si hay pocos puntos, graficar normal
        serie1, = ax1.plot(
            datos_validos['date_time'],
            y,
            color="#00008B",
            label='Nivel Freático',
            linewidth=2,
            marker='o',
            markersize=5.2,
            zorder=3
        )
        

    # Calcular minimo y máximo valor de fechas
    fecha_min = df['date_time'].min()
    fecha_max = df['date_time'].max()

   
    #---------------------------------------------------------------------------------#
    # Ajustar los límites del eje Y primario si hay datos válidos
    if not datos_validos.empty and (umbrales_disponibles is None or not umbrales_disponibles):
        y_min = datos_validos['elevacion_piezometrica'].min()
        y_max = datos_validos['elevacion_piezometrica'].max()
        if pd.notna(y_min) and pd.notna(y_max):  # verificar que no sean NaN
            ax1.set_ylim(y_min - 1, y_max + 2)

    #---------------------------------------------------------------------------------#


    # ===========================================================================================
    # CONFIGURACIÓN DEL EJE Y2 (SECUNDARIO)
    # ===========================================================================================

    df_precip_procesado = pd.DataFrame()

    if df_precip is None:
        df_precip = pd.DataFrame()

    if not df_precip.empty:
        df_precip = df_precip.copy()

        # Asegurar que existe date_time
        if 'date_time' not in df_precip.columns.tolist():
            print("⚠️ No existe columna 'date_time' en precipitación")
        else:
            df_precip['date_time'] = pd.to_datetime(df_precip['date_time'], errors='coerce')
            df_precip = df_precip.dropna(subset=['date_time'])

            df_precip_indexed = df_precip.set_index('date_time')
            # Agrupar y calcular el máximo diario
            df_precip_diario = df_precip_indexed.resample('D').max().reset_index()
            
            # Calcular rango de días del dataset de piezómetros
            rango_dias = (df['date_time'].max() - df['date_time'].min()).days
            if rango_dias == 0:
                rango_dias = 1  # Evitar división por cero   
            
            # Número de datos de precipitación
            num_datos = len(df_precip)
            if num_datos == 0:
                num_datos = 1  # Evitar división por cero
    
            # Decidir si usar datos originales o agrupados por día
            densidad = num_datos / rango_dias

            if densidad > 5000:
                df_precip_procesado = df_precip_diario
            else:
                df_precip_procesado = df_precip

    # Calcular ancho de barras según rango
    fecha_min = df['date_time'].min()
    fecha_max = df['date_time'].max()
    
    if fecha_min == fecha_max:
        ancho_barra = 0.008
    elif (fecha_max - fecha_min).days <= 10:
        ancho_barra = 0.015
    else:
        rango_dias = (fecha_max - fecha_min).days
        ancho_barra = max(0.035, rango_dias / 100 * 0.2)


    # Dibujar las barras de precipitación
    if not df_precip_procesado.empty and 'rain_mm_tot' in df_precip_procesado.columns:
        ax2 = ax1.twinx()
        ax2.bar(
            df_precip_procesado['date_time'], 
            df_precip_procesado['rain_mm_tot'], 
            label='Precipitación', 
            color='#009ACD', 
            alpha=0.4,          # Transparencia de las barras
            width=ancho_barra,  # Ancho de las barras
            zorder=0            # Dibuja las barras detrás de las líneas
        )
        ax2.set_ylabel('Precipitación (mm/día)', color='black', fontsize=14)
        ax2.tick_params(axis='y', labelcolor='black', labelsize=12)
        ax2.grid(False)  # Desactivar la cuadrícula del eje Y secundario
        ax2.set_ylim(0, df_precip['rain_mm_tot'].max() + 5) # Ajustar el límite superior del eje Y secundario

        # Configurar los decimales del eje Y secundario
        ax2.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))


    # =============================================================================================
    # CONFIGURACIÓN DEL EJE X
    # =============================================================================================

    # Si solo hay un punto, ajusta los límites del eje X para que se centren en ese punto
    if fecha_min == fecha_max:
        fecha_min -= pd.Timedelta(days=1)  # Un día antes
        fecha_max += pd.Timedelta(days=1)  # Un día después
    
    # Definir los límites de fechas en el eje X
    ax1.set_xlim([fecha_min, fecha_max])

    # Calcular el rango de días
    rango_dias = (fecha_max - fecha_min).days
    if rango_dias == 0: # Evitar división por cero
        rango_dias = 1  # Asignar un valor mínimo para evitar errores

    # Ajuste dinámico del intervalo en el eje X
    if rango_dias > 365:
        intervalo = 60  # Cada 2 meses aprox.
    elif rango_dias > 180:
        intervalo = 30  # Cada 1 mes
    elif rango_dias > 90:
        intervalo = 15  # Cada 15 días
    elif rango_dias > 31:
        intervalo = 7  # Cada semana
    elif rango_dias <= 31:
        intervalo = 1  # Cada día
    else:
        intervalo = max(1, rango_dias// 10)  # Dividir en 10 intervalos como máximo

    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=intervalo))  # Intervalo de días
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
    ax1.tick_params(axis='x', labelsize=10, rotation=90)

    # Validar las etiquetas del eje X
    ticks = ax1.get_xticks()
    new_labels = [mdates.num2date(num).strftime('%d-%m-%Y') for num in ticks]
    if len(new_labels) > 0:
        new_labels[-1] = fecha_max.strftime('%d-%m-%Y')  # Cambiar la última etiqueta a la última fecha
    
    # Asegurar que la última fecha esté en las etiquetas del eje X
    # fechas_ticks = list(ax1.get_xticks())  # Obtener los ticks actuales
    # fechas_ticks.append(mdates.date2num(fecha_max))  # Agregar la última fecha como tick
    # ax1.set_xticks(fechas_ticks)  # Actualizar los ticks del eje Xz
   

    # ===============================================================================
    # AJUSTES GENERALES DEL GRÁFICO
    # ===============================================================================

    # Cambiar los guiones bajos (_) por guiones (-) en el nombre de la tabla para el título
    titulo_tabla = tabla.replace('_', '-') # Cambiar los guiones bajos (_) por guiones (-) en el nombre de la tabla para el título
    
    ax1.set_title(f'Nivel Freático {titulo_tabla}', fontsize=18, fontweight='bold') # Título del gráfico
    ax1.set_ylabel('Elevación (msnm)', fontsize=14) # Etiqueta del eje Y primario
    ax1.tick_params(axis='y', labelcolor='black', labelsize=12) # Configuración del eje Y primario
    ax1.tick_params(axis='x', labelsize=12) # Configuración del eje X
    ax1.grid(True, linestyle='--', color='gray', alpha=0.7) # Cuadrícula del gráfico

    # Eliminar el borde superior del gráfico
    ax1.spines['top'].set_visible(False)
    if df_precip is not None and not df_precip.empty and not df_precip_procesado.empty:
        ax2.spines['top'].set_visible(False)

    # Eliminar el fondo gris del gráfico
    ax1.set_facecolor('white')

    # Cambiar el color del borde del gráfico
    for spine in ax1.spines.values():
        spine.set_edgecolor('silver')
        spine.set_linewidth(0.01)



    # ==========================================================================
    #       LEYENDA
    # ==========================================================================
    nombres_umbrales = {
        'nivel_umbral_1': 'Nivel Umbral 1',
        'nivel_umbral_2': 'Nivel Umbral 2',
        'nivel_umbral_3': 'Nivel Umbral 3'
    }
    # Combinar leyendas de ambos ejes
    lines = [serie1]
    labels = [serie1.get_label()]

    if not df_precip_procesado.empty:
        lines.append(Line2D([], [], color='#009ACD', linewidth=4, linestyle='-'))
        labels.append('Precipitación')

    if graficar_umbrales and umbrales_disponibles:
        for umbral_col in ['nivel_umbral_1', 'nivel_umbral_2', 'nivel_umbral_3']:
            if umbral_col in umbrales_disponibles and umbrales_disponibles[umbral_col] is not None:
                color = {
                    'nivel_umbral_1': 'yellow',
                    'nivel_umbral_2': 'orange',
                    'nivel_umbral_3': 'red'
                }[umbral_col]
                lines.append(Line2D([0], [0], color=color, linestyle='--', linewidth=1.5))
                labels.append(nombres_umbrales[umbral_col])

    # Configuración de la leyenda
    ax1.legend(
        lines, labels, loc='lower center', bbox_to_anchor=(0.5, -0.4), ncol=5, 
        frameon=True, fontsize=12, facecolor='white', edgecolor='silver'
    )

    # Ajustar todo el diseño
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    return fig