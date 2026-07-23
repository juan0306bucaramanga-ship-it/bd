import streamlit as st
import math
import json
import gspread
from google.oauth2.service_account import Credentials

# Configuración de la página
st.set_page_config(
    page_title="Boda Pro - Plano y Sincronización en Vivo",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ Boda Pro - Plano Interactivo del Salón y Cotizador Sincronizado")
st.markdown("Distribución amplia en patrón intercalado con panel de costos y sincronización en tiempo real vía Google Sheets.")

# --- CONFIGURACIÓN DE CONEXIÓN CON GOOGLE SHEETS ---
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open("Boda_Datos_Salon").sheet1
    return sheet

try:
    sheet = conectar_google_sheets()
except Exception as e:
    st.error(f"Error conectando a Google Sheets. Verifica tus Secrets en Streamlit: {e}")
    sheet = None

# Función con amplio espaciado para evitar solapamientos entre mesas
def calcular_coordenadas(index):
    cols_per_row = 4  
    x_spacing = 520   
    y_spacing = 450   
    row = index // cols_per_row
    col = index % cols_per_row
    
    x_offset = 260 if (row % 2 == 1) else 0
    x = 350 + (col * x_spacing) + x_offset
    y = 250 + (row * y_spacing)
    return x, y

# --- CARGAR / INICIALIZAR ESTADO DESDE LA NUBE ---
if "tables" not in st.session_state:
    if sheet:
        try:
            contenido_celda = sheet.cell(1, 1).value
            if contenido_celda and contenido_celda.startswith("["):
                st.session_state.tables = json.loads(contenido_celda)
            else:
                st.session_state.tables = []
                for i in range(2):
                    x, y = calcular_coordenadas(i)
                    st.session_state.tables.append({
                        "x": x, "y": y,
                        "seats": [{"name": "", "type": "empty"} for _ in range(8)]
                    })
        except Exception:
            st.session_state.tables = []
            for i in range(2):
                x, y = calcular_coordenadas(i)
                st.session_state.tables.append({
                    "x": x, "y": y,
                    "seats": [{"name": "", "type": "empty"} for _ in range(8)]
                })
    else:
        st.session_state.tables = []
        for i in range(2):
            x, y = calcular_coordenadas(i)
            st.session_state.tables.append({
                "x": x, "y": y,
                "seats": [{"name": "", "type": "empty"} for _ in range(8)]
            })

def guardar_en_nube():
    """Función para guardar el estado actual en la celda A1 del Google Sheet"""
    if sheet:
        try:
            sheet.update_cell(1, 1, json.dumps(st.session_state.tables))
        except Exception as e:
            st.warning(f"No se pudo sincronizar con la nube: {e}")

# --- CÁLCULOS FINANCIEROS Y DE COSTOS DETALLADOS ---
num_mesas = len(st.session_state.tables)
UNIT_COSTO_MESA = 55000
costo_mesas = num_mesas * UNIT_COSTO_MESA

total_adultos = sum(1 for t in st.session_state.tables for s in t['seats'] if s['type'] == 'adult')
UNIT_COSTO_ADULTO = 33000
costo_adultos = total_adultos * UNIT_COSTO_ADULTO

total_ninos = sum(1 for t in st.session_state.tables for s in t['seats'] if s['type'] == 'child')
UNIT_COSTO_NINO = 20000
costo_ninos = total_ninos * UNIT_COSTO_NINO

total_invitados = total_adultos + total_ninos
cant_meseros = math.ceil(total_invitados / 20) if total_invitados > 0 else 0
UNIT_COSTO_MESERO = 165000
costo_meseros = cant_meseros * UNIT_COSTO_MESERO

costo_directo = costo_mesas + costo_adultos + costo_ninos + costo_meseros

# --- PANEL PRINCIPAL DE COSTOS EN TIEMPO REAL ---
st.subheader("📊 Resumen Maestro de Costos en Tiempo Real")

col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)
with col_c1:
    st.metric(label=f"Mesas ({num_mesas})", value=f"${costo_mesas:,.0f}", delta=f"${UNIT_COSTO_MESA:,.0f} c/u")
with col_c2:
    st.metric(label=f"Adultos ({total_adultos})", value=f"${costo_adultos:,.0f}", delta=f"${UNIT_COSTO_ADULTO:,.0f} c/u")
with col_c3:
    st.metric(label=f"Niños ({total_ninos})", value=f"${costo_ninos:,.0f}", delta=f"${UNIT_COSTO_NINO:,.0f} c/u")
with col_c4:
    st.metric(label=f"Meseros ({cant_meseros})", value=f"${costo_meseros:,.0f}", delta=f"1 c/20 inv.")
with col_c5:
    st.metric(label="TOTAL PROYECTADO", value=f"${costo_directo:,.0f}")

st.divider()

# --- BARRA LATERAL: HERRAMIENTAS ---
st.sidebar.header("🛠️ Herramientas del Salón")

if st.sidebar.button("➕ Añadir Mesa", use_container_width=True):
    if len(st.session_state.tables) < 14:
        nuevo_idx = len(st.session_state.tables)
        x, y = calcular_coordenadas(nuevo_idx)
        st.session_state.tables.append({
            "x": x,
            "y": y,
            "seats": [{"name": "", "type": "empty"} for _ in range(8)]
        })
        guardar_en_nube()
        st.rerun()
    else:
        st.sidebar.warning("Límite máximo de 14 mesas alcanzado.")

if st.sidebar.button("🗑️ Borrar Última Mesa", use_container_width=True):
    if st.session_state.tables:
        st.session_state.tables.pop()
        guardar_en_nube()
        st.rerun()

if st.sidebar.button("🧹 Limpiar Todo el Salón", use_container_width=True):
    st.session_state.tables = []
    guardar_en_nube()
    st.rerun()

# --- RENDERIZADO VISUAL DEL PLANO ---
st.subheader("🗺️ Plano Arquitectónico del Salón")

if st.button("➕ 🪑 Añadir Nueva Mesa al Salón", type="primary", use_container_width=True):
    if len(st.session_state.tables) < 14:
        nuevo_idx = len(st.session_state.tables)
        x, y = calcular_coordenadas(nuevo_idx)
        st.session_state.tables.append({
            "x": x,
            "y": y,
            "seats": [{"name": "", "type": "empty"} for _ in range(8)]
        })
        guardar_en_nube()
        st.rerun()
    else:
        st.warning("Has alcanzado el límite máximo de 14 mesas.")

svg_width = 2200
svg_height = 1400

svg_content = f'''
<svg width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}" style="background-color: #ffffff; border: 2px solid #2f3640; border-radius: 8px;">
    <defs>
        <pattern id="grid" width="80" height="80" patternUnits="userSpaceOnUse">
            <path d="M 80 0 L 0 0 0 80" fill="none" stroke="#e2e8f0" stroke-width="1.5"/>
        </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#grid)" />
'''

for idx, table in enumerate(st.session_state.tables):
    tx, ty = table['x'], table['y']
    radius = 120  
    
    for s_i in range(8):
        angle = s_i * (2 * math.pi / 8)
        sx = tx + radius * math.cos(angle)
        sy = ty + radius * math.sin(angle)
        
        seat = table['seats'][s_i]
        if seat['type'] == 'adult':
            s_color = "#00a8ff"  
            t_color = "#ffffff"
        elif seat['type'] == 'child':
            s_color = "#fbc531"  
            t_color = "#1e293b"
        else:
            s_color = "#cbd5e1"  
            t_color = "#1e293b"
            
        svg_content += f'''
        <circle cx="{sx}" cy="{sy}" r="24" fill="{s_color}" stroke="#475569" stroke-width="2"/>
        <text x="{sx}" y="{sy+6}" font-size="14" font-weight="bold" fill="{t_color}" text-anchor="middle">{s_i+1}</text>
        '''
        if seat['name']:
            nombre_corto = seat['name'] if len(seat['name']) <= 12 else seat['name'][:10] + ".."
            svg_content += f'''
            <text x="{sx}" y="{sy+42}" font-size="13" font-weight="bold" fill="#0f172a" text-anchor="middle">{nombre_corto}</text>
            '''

    svg_content += f'''
    <circle cx="{tx}" cy="{ty}" r="52" fill="#1e293b" stroke="#0f172a" stroke-width="3"/>
    <text x="{tx}" y="{ty+6}" font-size="16" font-weight="bold" fill="#ffffff" text-anchor="middle">Mesa {idx+1}</text>
    '''

svg_content += '</svg>'

st.components.v1.html(f'<div style="overflow: auto; width: 100%; height: 650px;">{svg_content}</div>', height=670)

# --- GESTIÓN DETALLADA DE POSICIONES E INVITADOS ---
st.divider()
st.subheader("👥 Configuración y Ubicación de Mesas")

if st.session_state.tables:
    selected_table = st.selectbox(
        "Selecciona una mesa para ajustar su posición exacta o gestionar sus puestos:",
        options=list(range(len(st.session_state.tables))),
        format_func=lambda x: f"Mesa {x+1} (Posición X: {st.session_state.tables[x]['x']}, Y: {st.session_state.tables[x]['y']})"
    )
    
    t_data = st.session_state.tables[selected_table]
    
    col_pos1, col_pos2 = st.columns(2)
    with col_pos1:
        new_x = st.slider(f"Ajustar X (Mesa {selected_table+1})", min_value=100, max_value=2000, value=int(t_data['x']), step=10, key=f"x_{selected_table}")
        if new_x != t_data['x']:
            t_data['x'] = new_x
            guardar_en_nube()
            st.rerun()
    with col_pos2:
        new_y = st.slider(f"Ajustar Y (Mesa {selected_table+1})", min_value=100, max_value=1200, value=int(t_data['y']), step=10, key=f"y_{selected_table}")
        if new_y != t_data['y']:
            t_data['y'] = new_y
            guardar_en_nube()
            st.rerun()

    st.markdown("#### Asignación de Asientos (Sillas 1 a Rellenar):")
    for s_idx in range(8):
        seat = t_data['seats'][s_idx]
        s_col1, s_col2, s_col3 = st.columns([1, 2, 3])
        
        with s_col1:
            st.markdown(f"**Silla {s_idx+1}**")
        with s_col2:
            tipo_actual_idx = 0
            if seat['type'] == 'adult':
                tipo_actual_idx = 1
            elif seat['type'] == 'child':
                tipo_actual_idx = 2
                
            nuevo_tipo_sel = st.selectbox(
                f"Tipo S{s_idx+1}",
                options=["Libre", "Adulto ($33.000)", "Niño ($20.000)"],
                index=tipo_actual_idx,
                key=f"stype_{selected_table}_{s_idx}",
                label_visibility="collapsed"
            )
            
            mapping = {"Libre": "empty", "Adulto ($33.000)": "adult", "Niño ($20.000)": "child"}
            val_mapeado = mapping[nuevo_tipo_sel]
            if val_mapeado != seat['type']:
                seat['type'] = val_mapeado
                if val_mapeado == 'empty':
                    seat['name'] = ""
                elif not seat['name']:
                    seat['name'] = f"Invitado {s_idx+1}"
                guardar_en_nube()
                st.rerun()
                
        with s_col3:
            nuevo_nombre = st.text_input(
                f"Nombre S{s_idx+1}",
                value=seat['name'],
                placeholder="Nombre del invitado",
                key=f"sname_{selected_table}_{s_idx}",
                label_visibility="collapsed"
            )
            if nuevo_nombre != seat['name']:
                seat['name'] = nuevo_nombre
                guardar_en_nube()
                st.rerun()