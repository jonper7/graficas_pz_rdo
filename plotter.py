import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
import matplotlib.ticker as ticker
import pandas as pd


from excluir_umbral import no_graficar_umbral
from obtener_umbrales import obtener_umbrales

def plot_data(df, df_precip, tabla, fecha_inicio, fecha_fin, conexion=None, excel_path=None, sheet_name=None, cell=None):

    fig, ax1 = plt.subplots(figsize=(14, 7))
    plt.style.use('bmh')

    df = df.copy()

    # Validar que existe date_time
    if 'date_time' not in df.columns:
        print(f"✗ Error: No existe columna 'date_time' en el DataFrame")
        return None
    
    # FILTRAR POR RANGO DE FECHAS
    fecha_inicio_dt = pd.to_datetime(fecha_inicio)
    fecha_fin_dt = pd.to_datetime(fecha_fin)
    df = df[(df['date_time'] >= fecha_inicio_dt) & (df['date_time'] <= fecha_fin_dt)]
    
    # Filtrar datos válidos
    datos_validos = df[['date_time', 'elevacion_piezometrica']].dropna()
    
    if datos_validos.empty:
        print(f"⚠️ No hay datos válidos para graficar en {tabla}")
        return None

    # -----------------------------------
    # Configuración de umbrales
    # -----------------------------------
    graficar_umbrales = tabla not in no_graficar_umbral
    umbrales_disponibles = None  

    if graficar_umbrales and conexion:
        # Obtener umbrales desde la base de datos
        try:
            umbrales_disponibles = obtener_umbrales(conexion, tabla)
            if umbrales_disponibles:
                print(f"✓ Umbrales obtenidos de BD para {tabla}")
            else:
                print(f"⚠️ No hay umbrales en BD para {tabla}")
        except Exception as e:
            print(f"⚠️ Error al obtener umbrales para {tabla}: {e}")
            umbrales_disponibles = None
    elif graficar_umbrales and not conexion:
        # Fallback: buscar umbrales en el DataFrame si no hay conexión
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

    # -----------------------------------
    # Serie principal (Elevación Piezométrica)
    # -----------------------------------

    ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))

    serie1, = ax1.plot(
        df['date_time'],
        df['elevacion_piezometrica'],
        color='#00008B',
        label='Elevación Piezométrica (msnm)',
        linewidth=2,
        marker='o' if len(df) == 1 else None,
        markersize=6,
        zorder=3
    )

    # Aplicar solo cuando NO hay umbrales disponibles (diccionario vacío o None)
    if not datos_validos.empty and (umbrales_disponibles is None or not umbrales_disponibles):
        y_min = datos_validos['elevacion_piezometrica'].min()
        y_max = datos_validos['elevacion_piezometrica'].max()
        if pd.notna(y_min) and pd.notna(y_max):
            rango = y_max - y_min
            margen = max(0.5, rango * 0.1)  # 10% del rango o mínimo 0.5
            ax1.set_ylim(y_min - margen, y_max + margen)
            
    # -----------------------------------
    # Eje secundario (Precipitación)
    # -----------------------------------

    df_precip_procesado = pd.DataFrame()

    if df_precip is not None and not df_precip.empty:
        df_precip = df_precip.copy()

        # Asegurar que existe date_time
        if 'date_time' not in df_precip.columns:
            print("⚠️ No existe columna 'date_time' en precipitación")
        else:
            df_precip['date_time'] = pd.to_datetime(df_precip['date_time'], errors='coerce')
            df_precip = df_precip.dropna(subset=['date_time'])

            # Resamplear a diario si hay muchos datos
            rango_dias = max(1, (df['date_time'].max() - df['date_time'].min()).days)
            num_datos = len(df_precip)
            
            if num_datos / rango_dias > 50:
                df_precip_procesado = df_precip.set_index('date_time').resample('D').max().reset_index()
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

    # Graficar barras de precipitación si hay datos
    if not df_precip_procesado.empty and 'rain_mm_tot' in df_precip_procesado.columns:
        ax2 = ax1.twinx()
        ax2.bar(
            df_precip_procesado['date_time'],
            df_precip_procesado['rain_mm_tot'],
            label='Precipitación',
            color='#009ACD',
            alpha=0.4,
            width=ancho_barra,
            zorder=0
        )
        ax2.set_ylabel('Precipitación (mm)', fontsize=14)
        ax2.tick_params(axis='y', labelsize=12)
        ax2.grid(False)
        ax2.set_ylim(0, df_precip['rain_mm_tot'].max() + 5) # Ajustar el límite superior del eje Y secundario

    # -----------------------------------
    # Configuración del eje X
    # -----------------------------------

    if fecha_min == fecha_max:
        fecha_min -= pd.Timedelta(days=1)
        fecha_max += pd.Timedelta(days=1)

    ax1.set_xlim([fecha_min, fecha_max])

    rango_dias = max(1, (fecha_max - fecha_min).days)

    if rango_dias > 365: intervalo = 60
    elif rango_dias > 180: intervalo = 30
    elif rango_dias > 90: intervalo = 15
    elif rango_dias > 31: intervalo = 7
    else: intervalo = 1

    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=intervalo))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
    ax1.tick_params(axis='x', rotation=90, labelsize=10)

    # -----------------------------------
    # Título y formato
    # -----------------------------------

    titulo_tabla = tabla.replace('_', '-')
    ax1.set_title(f'Elevación Piezométrica - {titulo_tabla}',
                   fontsize=18,
                   fontweight='bold',)
    ax1.set_ylabel('Elevación (msnm)', fontsize=14)
    ax1.tick_params(axis='y', 
                    labelsize=12,
                    labelcolor='black')
    ax1.tick_params(axis='x', 
                    labelsize=11, 
                    labelcolor='black')
    ax1.grid(True, linestyle='--', color='gray', alpha=0.7)
    ax1.set_facecolor('white')

    for spine in ax1.spines.values():
        spine.set_edgecolor('silver')
        spine.set_linewidth(0.01)

    # -----------------------------------
    # Leyenda
    # -----------------------------------

    nombres_umbrales = {
        'nivel_umbral_1': 'Nivel Umbral 1',
        'nivel_umbral_2': 'Nivel Umbral 2',
        'nivel_umbral_3': 'Nivel Umbral 3'
    }

    lines = [serie1]
    labels = [serie1.get_label()]

    if not df_precip_procesado.empty:
        lines.append(Line2D([], [], color='#009ACD', linewidth=4, alpha=0.4))
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

    ax1.legend(lines, labels, loc='lower center', bbox_to_anchor=(0.5, -0.38), 
               ncol=min(5, len(lines)), fontsize=12, frameon=True, facecolor='white', 
               edgecolor='silver')
    
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    print(f"✓ Gráfico generado para {tabla}")
    return fig

   