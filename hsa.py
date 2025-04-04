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

# Función para buscar en los datos
def search_data(df, search_term, campo_busqueda):
    """
    Busca un término en la columna especificada del DataFrame.
    Si campo_busqueda es 'TODOS', busca en todas las columnas.
    Soporta búsqueda de términos múltiples separados por espacios.
    """
    if not search_term:
        return df
    
    # Convertir todo a string para evitar problemas de tipo
    for col in df.columns:
        df[col] = df[col].astype(str)
    
    # Dividir la búsqueda en términos separados por espacios
    search_terms = search_term.lower().split()
    
    if campo_busqueda == 'TODOS':
        # Buscar todos los términos en todas las columnas
        mask = pd.Series(True, index=df.index)
        for term in search_terms:
            term_mask = False
            for column in df.columns:
                term_mask |= df[column].str.lower().str.contains(term, regex=False, na=False)
            mask &= term_mask
        return df[mask]
    else:
        # Buscar solo en la columna especificada, todos los términos deben estar presentes
        if campo_busqueda in df.columns:
            mask = pd.Series(True, index=df.index)
            for term in search_terms:
                mask &= df[campo_busqueda].str.lower().str.contains(term, regex=False, na=False)
            return df[mask]
        else:
            # Si la columna no existe en esta hoja, devolver DataFrame vacío
            return pd.DataFrame()

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
        /* Estilos para el buscador */
        .search-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            border-left: 5px solid #1f77b4;
        }
        .search-title {
            color: #1f77b4;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .search-icon {
            color: #1f77b4;
            font-size: 24px;
        }
        .search-results {
            margin-top: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            font-size: 14px;
        }
        /* Badge para conteo de resultados */
        .results-badge {
            background: #1f77b4;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 14px;
            margin-left: 10px;
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
    
    # Contenedor para el buscador
    st.markdown("""
        <div class="search-container">
            <h3 class="search-title">🔍 Buscador de Expedientes</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Crear el buscador con Streamlit
    search_col1, search_col2 = st.columns([3, 1])
    
    with search_col1:
        search_term = st.text_input("Ingrese término de búsqueda", 
                                   placeholder="Ej: nombre, número de expediente, tema...")
    
    # Obtener una lista de todas las columnas posibles de todas las hojas
    all_columns = set()
    common_columns = None
    dfs_by_sheet = {}
    
    # Cargar todas las hojas para obtener columnas
    for sheet in sheet_names:
        df = load_sheet_data(file_path, sheet)
        df.columns = df.columns.str.strip()
        dfs_by_sheet[sheet] = df
        
        # Actualizar conjunto de todas las columnas
        sheet_columns = set(df.columns)
        all_columns.update(sheet_columns)
        
        # Mantener un seguimiento de las columnas comunes
        if common_columns is None:
            common_columns = sheet_columns
        else:
            common_columns = common_columns.intersection(sheet_columns)
    
    # Opciones de búsqueda
    search_options_col1, search_options_col2 = st.columns([3, 1])
    
    with search_options_col1:
        # Ordenar y convertir el conjunto a lista para el selectbox
        search_columns = ['TODOS'] + sorted(list(all_columns))
        campo_busqueda = st.selectbox("Campo de búsqueda", options=search_columns)
    
    with search_options_col2:
        search_button = st.button("🔍 Buscar", use_container_width=True)
    
    # Realizar búsqueda si se presiona el botón
    if search_button and search_term:
        # Inicializar DataFrame para almacenar todos los resultados
        all_results = pd.DataFrame()
        total_results = 0
        
        # Buscar en todas las hojas
        for sheet_name, df in dfs_by_sheet.items():
            # Comprobar si el campo de búsqueda existe en esta hoja
            if campo_busqueda == 'TODOS' or campo_busqueda in df.columns:
                # Aplicar búsqueda
                filtered = search_data(df, search_term, campo_busqueda)
                
                # Si hay resultados, añadir columna con nombre de la hoja
                if not filtered.empty:
                    filtered['HOJA_ORIGEN'] = sheet_name
                    all_results = pd.concat([all_results, filtered], ignore_index=True)
                    total_results += len(filtered)
        
        # Mostrar resultados de búsqueda
        st.markdown(f"""
            <div class="search-results">
                <h4>Resultados <span class="results-badge">{total_results}</span> expedientes encontrados en todas las hojas</h4>
            </div>
        """, unsafe_allow_html=True)
        
        # Mostrar los expedientes filtrados
        if not all_results.empty:
            for _, row in all_results.iterrows():
                with st.expander(f"📂 {row['EXPEDIENTE']} - Hoja: {row['HOJA_ORIGEN']}"):
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
                        row.get('EXPEDIENTES RE ASIGNADOS', 'No disponible'),
                        row.get('TEMA', 'No disponible'),
                        row.get('SOLICITANTE', 'No disponible'),
                        row.get('SEGUIMIENTO', 'No disponible'),
                        row.get('ASUNTO', 'No disponible'),
                        render_trazabilidad(row.get('TRAZABILIDAD', 'No disponible'))
                    ), unsafe_allow_html=True)
        else:
            st.info("No se encontraron resultados para la búsqueda en ninguna hoja.")
    
    # Línea divisoria
    st.markdown("---")
    
    # Explorar todas las hojas (como estaba originalmente)
    st.subheader("Explorar por hojas")
    
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
                        row.get('EXPEDIENTES RE ASIGNADOS', 'No disponible'),
                        row.get('TEMA', 'No disponible'),
                        row.get('SOLICITANTE', 'No disponible'),
                        row.get('SEGUIMIENTO', 'No disponible'),
                        row.get('ASUNTO', 'No disponible'),
                        render_trazabilidad(row.get('TRAZABILIDAD', 'No disponible'))
                    ), unsafe_allow_html=True)
except Exception as e:
    st.error(f"❌ Error al cargar el archivo: {str(e)}")
    st.info("ℹ️ Por favor verifica la ruta del archivo y su formato.")