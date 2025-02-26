import streamlit as st
import pandas as pd
from datetime import datetime
import re

# Configuración de la página
st.set_page_config(
    page_title="HSA Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def format_date(date_str):
    """
    Formatea una fecha en el formato deseado (dd/mm/aa).
    Elimina la parte de tiempo si existe.
    """
    if date_str == 'No disponible':
        return date_str
        
    try:
        # Intentar varios formatos de fecha posibles
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y']:
            try:
                date_obj = datetime.strptime(str(date_str), fmt)
                # Retornar en formato dd/mm/yyyy
                return date_obj.strftime('%d/%m/%Y')
            except ValueError:
                continue
                
        # Si no se pudo convertir con ninguno de los formatos, devolver el original
        return date_str
    except:
        # En caso de cualquier error, devolver el original
        return date_str

def process_trazabilidad(trazabilidad_str):
    """
    Procesa el texto de trazabilidad para extraer fechas y descripciones.
    Maneja correctamente los saltos de línea para separar eventos distintos.
    """
    # Corrección específica para el caso de "14/05/2024 (5 FOLIOS)"
    trazabilidad_str = corregir_caso_especifico(trazabilidad_str)
    
    # Manejar mejor los saltos de línea
    if isinstance(trazabilidad_str, str):
        # Reemplazar múltiples variantes de saltos de línea por un formato estándar
        trazabilidad_str = re.sub(r'\\n', '\n', trazabilidad_str)
        
        # Dividir por líneas y procesar cada línea por separado
        lineas = trazabilidad_str.split('\n')
        trazabilidad_processed = []
        
        fecha_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}/\d{2}/\d{2}'  # Acepta tanto dd/mm/yyyy como dd/mm/yy
        
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue
                
            # Buscar fecha en esta línea
            match = re.search(fecha_pattern, linea)
            if match:
                fecha_original = match.group(0)
                inicio = match.start()
                
                # Normalizar la fecha al formato completo (yyyy)
                partes_fecha = fecha_original.split('/')
                if len(partes_fecha) == 3:
                    dia = partes_fecha[0]
                    mes = partes_fecha[1]
                    anio = partes_fecha[2]
                    # Si el año tiene 2 dígitos, convertirlo a 4 dígitos
                    if len(anio) == 2:
                        anio = '20' + anio  # Asumimos años 2000+
                    fecha = f"{dia}/{mes}/{anio}"
                else:
                    fecha = fecha_original
                
                # Extraer descripción (todo lo que sigue después de la fecha original)
                descripcion = ""
                if inicio + len(fecha_original) < len(linea):
                    descripcion = linea[inicio + len(fecha_original):].strip()
                    descripcion = re.sub(r'^[\s\-–—]+', '', descripcion)
                
                # Convertir la fecha a un objeto datetime para ordenación posterior
                try:
                    fecha_formato = '%d/%m/%Y'
                    fecha_obj = datetime.strptime(fecha, fecha_formato)
                    trazabilidad_processed.append({
                        'fecha': fecha,
                        'fecha_obj': fecha_obj,
                        'descripcion': descripcion
                    })
                except Exception as e:
                    # Si hay un error en el formato de fecha, añadir sin fecha_obj
                    print(f"Error al procesar fecha: {fecha} - {str(e)}")
                    trazabilidad_processed.append({
                        'fecha': fecha,
                        'descripcion': descripcion
                    })
        
        # Ordenar por fecha, de más reciente a más antigua
        trazabilidad_processed = sorted(trazabilidad_processed, 
                                      key=lambda x: x.get('fecha_obj', datetime.min), 
                                      reverse=True)
        return trazabilidad_processed
    return []

def corregir_caso_especifico(texto):
    """
    Corrige manualmente el caso específico de "14/05/2024 (5 FOLIOS)" 
    para asegurar que muestre "14/05/2024 REPARTO (5 FOLIOS)"
    """
    if not isinstance(texto, str):
        return texto
        
    # Buscar específicamente el patrón problemático
    patron = r'(14/05/20?24)\s*\(?5 FOLIOS\)?'
    reemplazo = r'\1 REPARTO (5 FOLIOS)'
    
    # Reemplazar directamente
    texto_corregido = re.sub(patron, reemplazo, texto, flags=re.IGNORECASE)
    
    # También manejar el caso donde el texto completo está, pero separado incorrectamente
    patron2 = r'(14/05/20?24)(\s*)\(?5 FOLIOS\)?'
    if re.search(patron2, texto_corregido, re.IGNORECASE) and not re.search(r'REPARTO', texto_corregido, re.IGNORECASE):
        texto_corregido = re.sub(patron2, r'\1 REPARTO (5 FOLIOS)', texto_corregido, flags=re.IGNORECASE)
    
    return texto_corregido

def render_trazabilidad(trazabilidad_str):
    eventos = process_trazabilidad(trazabilidad_str)
    if not eventos:
        return "No disponible"
    
    # Modificado para mostrar los mosaicos en forma de cuadrícula con colores mejorados para destacar
    html_content = '<div class="trazabilidad-container" style="background: #f0f7ff; padding: 15px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 100%; border: 1px solid #d0e3ff;">'
    html_content += '<h4 style="text-align: center; color: #1f77b4; font-weight: bold;">📑 Historial de Trazabilidad</h4>'
    html_content += '<div class="trazabilidad-grid">'
    
    # Utilizamos un formato de fecha corto para los eventos de trazabilidad
    for evento in eventos:
        html_content += f'<div class="trazabilidad-item">'
        # Convertir la fecha al formato dd/mm/aa para mostrarla
        fecha_formateada = evento["fecha"]
        try:
            fecha_obj = datetime.strptime(evento["fecha"], '%d/%m/%Y')
            fecha_formateada = fecha_obj.strftime('%d/%m/%y')
        except:
            pass
        html_content += f'   <div class="trazabilidad-fecha"><strong>📅 {fecha_formateada}</strong></div>'
        html_content += f'   <div class="trazabilidad-descripcion">{evento["descripcion"]}</div>'
        html_content += f'</div>'
    
    html_content += '</div></div>'
    
    return html_content

# Función para cargar los datos
@st.cache_data
def get_sheet_names(file_path):
    xls = pd.ExcelFile(file_path)
    return xls.sheet_names

@st.cache_data
def load_sheet_data(file_path, sheet_name):
    return pd.read_excel(file_path, sheet_name=sheet_name)

# Estilos CSS personalizados para mosaicos mejorados
st.markdown("""
    <style>
        .title-container {
            background-color: #1f77b4;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            color: white;
            text-align: center;
        }
        .data-container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-top: 20px;
        }
        .mosaic-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            padding: 20px;
        }
        .mosaic-item {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            text-align: center;
            font-size: 16px;
            font-weight: bold;
            border-top: 4px solid #1f77b4;
        }
        .trazabilidad-mosaic {
            background: #f0f7ff !important;
            border-top: 4px solid #1f77b4 !important;
            text-align: left;
            padding: 20px;
            grid-column: 1 / span 3; /* Hace que ocupe toda la fila */
            border: 1px solid #d0e3ff;
        }
        .icon {
            font-size: 20px;
            margin-right: 5px;
        }
        /* Nuevos estilos para visualización de trazabilidad en cuadrícula */
        .trazabilidad-container {
            width: 100%;
            margin: 0;
            overflow: hidden;
        }
        .trazabilidad-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
            gap: 15px;
            padding: 10px;
        }
        .trazabilidad-item {
            background: white;
            border-top: 5px solid #1f77b4;
            border-radius: 5px;
            padding: 10px;
            min-height: 120px;
            box-shadow: 0 2px 5px rgba(31, 119, 180, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
        }
        .trazabilidad-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(31, 119, 180, 0.3);
            background-color: #f8fbff;
        }
        .trazabilidad-fecha {
            text-align: center;
            margin-bottom: 8px;
            padding-bottom: 5px;
            border-bottom: 1px solid #1f77b4;
            color: #1f77b4;
            font-weight: bold;
        }
        .trazabilidad-descripcion {
            font-size: 14px;
            overflow-wrap: break-word;
        }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.markdown("""
    <div class="title-container">
        <h1>📊 HSA EXPEDIENTES EN DESPACHO Y PREARCHIVO</h1>
        <p style='font-size: 18px;'>🔍 Sistema de Gestión de Información</p>
    </div>
""", unsafe_allow_html=True)

# Cargar el archivo Excel
file_path = 'PRUEBA HSA 26.xlsx'
try:
    sheet_names = get_sheet_names(file_path)
    
    if 'expanded_sheet' not in st.session_state:
        st.session_state.expanded_sheet = None
    
    for sheet in sheet_names:
        if st.button(f"📁 {sheet}", key=f"btn_{sheet}", use_container_width=True):
            st.session_state.expanded_sheet = sheet if st.session_state.expanded_sheet != sheet else None
        
        if st.session_state.expanded_sheet == sheet:
            df = load_sheet_data(file_path, sheet)
            
            df.columns = df.columns.str.strip()
            
# Mostrar fechas en formato completo dd/mm/yyyy
            if 'Trazabilidad' in df.columns:
                # Asegurarnos de que los saltos de línea se preserven correctamente
                df['Trazabilidad'] = df['Trazabilidad'].astype(str).str.replace(r'\\n', '\n', regex=True)
                
                # Limpiar posibles problemas de formato en el campo Trazabilidad
                def limpiar_trazabilidad(texto):
                    if not isinstance(texto, str):
                        return texto
                    # Asegurar que la fecha y su descripción estén correctamente separadas
                    texto = re.sub(r'(\d{2}/\d{2}/\d{4}|\d{2}/\d{2}/\d{2})(?!\s)', r'\1 ', texto)
                    return texto
                
                df['Trazabilidad'] = df['Trazabilidad'].apply(limpiar_trazabilidad)
            
            df = df.dropna(axis=1, how='all')
            
            for _, row in df.iterrows():
                with st.expander(f"📂 {row['EXPEDIENTE']}"):
                    # Mosaicos regulares (3 columnas)
                    st.markdown("""
                        <div class="mosaic-container">
                            <div class="mosaic-item">📅 <b>Fecha de Reparto</b><br>{}</div>
                            <div class="mosaic-item">🔄 <b>Reasignado</b><br>{}</div>
                            <div class="mosaic-item">🔖 <b>Tema</b><br>{}</div>
                            <div class="mosaic-item">👤 <b>Solicitante</b><br>{}</div>
                            <div class="mosaic-item">🔍 <b>Seguimiento</b><br>{}</div>
                            <div class="mosaic-item">📜 <b>Asunto</b><br>{}</div>
                            <div class="trazabilidad-mosaic">{}</div>
                        </div>
                    """.format(
                        format_date(row.get('FECHA DE REPARTO', 'No disponible')),
                        row.get('REASIGNADO', 'No disponible'),
                        row.get('TEMA', 'No disponible'),
                        row.get('SOLICITANTE', 'No disponible'),
                        row.get('SEGUIMIENTO', 'No disponible'),
                        row.get('ASUNTO', 'No disponible'),
                        render_trazabilidad(row.get('TRAZABILIDAD', 'No disponible'))
                    ), unsafe_allow_html=True)
except Exception as e:
    st.error(f"❌ Error al cargar el archivo: {str(e)}")
    st.info("ℹ️ Por favor verifica la ruta del archivo y su formato.")