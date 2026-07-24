import streamlit as st
import math
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuración de la página (Debe ser el primer comando)
st.set_page_config(
    page_title="Nuestra Boda",
    page_icon="💍",
    layout="wide"
)

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    # 1. Conectar pestaña del plano (la que ya teníamos)
    sheet_salon = client.open("Boda_Datos_Salon").get_worksheet(0)
    
    # 2. Conectar nueva pestaña de RSVP
    try:
        sheet_rsvp = client.open("Boda_Datos_Salon").worksheet("RSVP_Invitados")
    except:
        sheet_rsvp = None
        
    return sheet_salon, sheet_rsvp

try:
    sheet_salon, sheet_rsvp = conectar_google_sheets()
except Exception as e:
    st.error(f"Error conectando a Google Sheets: {e}")
    sheet_salon, sheet_rsvp = None, None


# --- MENÚ DE NAVEGACIÓN LATERAL ---
st.sidebar.title("Navegación del Proyecto")
vista = st.sidebar.radio("Selecciona la vista:", ["💌 Invitación (Portal Invitados)", "⚙️ Panel Master (Ustedes)"])

st.sidebar.divider()

# ==========================================
# VISTA 1: PORTAL DEL INVITADO (PÚBLICO)
# ==========================================
if vista == "💌 Invitación (Portal Invitados)":
    
    col_centro_1, col_centro_2, col_centro_3 = st.columns([1, 2, 1])
    
    with col_centro_2:
        st.markdown("<h2 style='text-align: center;'>¡Nos Casamos! 💍</h2>", unsafe_allow_html=True)
        
        # --- 1. EMPOTRAR CANVA (Placeholder Animado) ---
        # Este es un diseño por defecto. Luego solo cambiarás el link dentro de 'src'
        canva_embed = '''
        <div style="position: relative; width: 100%; height: 0; padding-top: 177.7778%;
         padding-bottom: 0; box-shadow: 0 2px 8px 0 rgba(63,69,81,0.16); margin-top: 1.6em; margin-bottom: 0.9em; overflow: hidden;
         border-radius: 8px; will-change: transform;">
          <iframe loading="lazy" style="position: absolute; width: 100%; height: 100%; top: 0; left: 0; border: none; padding: 0;margin: 0;"
            src="https://www.canva.com/design/DAF-EjbZ-1c/view?embed" allowfullscreen="allowfullscreen" allow="fullscreen">
          </iframe>
        </div>
        '''
        st.components.v1.html(canva_embed, height=650)
        
        st.divider()
        st.subheader("💌 Confirma tu asistencia")
        st.markdown("Por favor, déjanos saber si nos acompañarás en este día tan especial.")
        
        # --- 2. FORMULARIO RSVP INTEGRADO ---
        if sheet_rsvp is None:
            st.error("⚠️ Falta crear la pestaña 'RSVP_Invitados' en tu archivo de Google Sheets.")
        else:
            with st.form("form_rsvp", clear_on_submit=True):
                nombre = st.text_input("Tu Nombre y Apellido completo *")
                asistencia = st.radio("¿Asistirás al evento? *", ["Sí, confirmo con alegría 🎉", "Lamentablemente no podré asistir 😢"])
                
                col_a, col_b = st.columns(2)
                with col_a:
                    adultos = st.number_input("Cantidad de Adultos", min_value=0, max_value=10, value=1)
                with col_b:
                    ninos = st.number_input("Cantidad de Niños", min_value=0, max_value=10, value=0)
                
                restricciones = st.text_area("¿Alguien tiene alguna alergia o restricción alimenticia? (Opcional)")
                
                submit = st.form_submit_button("Enviar Confirmación 💌", use_container_width=True)
                
                if submit:
                    if nombre.strip() == "":
                        st.error("Por favor ingresa tu nombre para continuar.")
                    else:
                        estado = "Confirmado" if "Sí" in asistencia else "Cancelado"
                        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
                        try:
                            # Se escribe directo en Google Sheets: Fecha, Nombre, Estado, Adultos, Niños, Restricciones
                            sheet_rsvp.append_row([fecha, nombre, estado, adultos, ninos, restricciones])
                            if estado == "Confirmado":
                                st.success(f"¡Gracias {nombre}! Tu confirmación ha sido guardada.")
                                st.balloons()
                            else:
                                st.info(f"Gracias por avisarnos, {nombre}. Te extrañaremos.")
                        except Exception as e:
                            st.error(f"Hubo un error guardando tus datos: {e}")


# ==========================================
# VISTA 2: PANEL DE ADMINISTRACIÓN (PRIVADO)
# ==========================================
elif vista == "⚙️ Panel Master (Ustedes)":
    
    st.sidebar.markdown("### 🔐 Seguridad")
    password = st.sidebar.text_input("Contraseña Master", type="password")
    
    # Contraseña temporal para que solo ustedes vean el plano
    if password != "Boda2026":
        st.warning("⚠️ Esta sección es privada. Ingresa la contraseña en la barra lateral izquierda para acceder al organizador.")
        st.stop()

    # --- A PARTIR DE AQUÍ VA TODO EL CÓDIGO ANTERIOR DEL PLANO ---
    st.title("🏛️ Panel Master - Plano y Cotizador")
    st.markdown("Distribución en patrón intercalado con panel de costos y exportación PNG.")
    
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

    if "tables" not in st.session_state:
        if sheet_salon:
            try:
                contenido_celda = sheet_salon.cell(1, 1).value
                if contenido_celda and contenido_celda.startswith("["):
                    st.session_state.tables = json.loads(contenido_celda)
                else:
                    st.session_state.tables = [{"x": calcular_coordenadas(i)[0], "y": calcular_coordenadas(i)[1], "seats": [{"name": "", "type": "empty"} for _ in range(8)]} for i in range(2)]
            except:
                st.session_state.tables = [{"x": calcular_coordenadas(i)[0], "y": calcular_coordenadas(i)[1], "seats": [{"name": "", "type": "empty"} for _ in range(8)]} for i in range(2)]
        else:
            st.session_state.tables = [{"x": calcular_coordenadas(i)[0], "y": calcular_coordenadas(i)[1], "seats": [{"name": "", "type": "empty"} for _ in range(8)]} for i in range(2)]

    def guardar_en_nube():
        if sheet_salon:
            try:
                sheet_salon.update_cell(1, 1, json.dumps(st.session_state.tables))
            except Exception as e:
                st.warning(f"No se pudo sincronizar: {e}")

    num_mesas = len(st.session_state.tables)
    costo_mesas = num_mesas * 55000
    total_adultos = sum(1 for t in st.session_state.tables for s in t['seats'] if s['type'] == 'adult')
    costo_adultos = total_adultos * 33000
    total_ninos = sum(1 for t in st.session_state.tables for s in t['seats'] if s['type'] == 'child')
    costo_ninos = total_ninos * 20000
    total_invitados = total_adultos + total_ninos
    cant_meseros = math.ceil(total_invitados / 20) if total_invitados > 0 else 0
    costo_meseros = cant_meseros * 165000
    costo_directo = costo_mesas + costo_adultos + costo_ninos + costo_meseros

    st.subheader("📊 Resumen de Costos")
    col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)
    col_c1.metric(f"Mesas ({num_mesas})", f"${costo_mesas:,.0f}")
    col_c2.metric(f"Adultos ({total_adultos})", f"${costo_adultos:,.0f}")
    col_c3.metric(f"Niños ({total_ninos})", f"${costo_ninos:,.0f}")
    col_c4.metric(f"Meseros ({cant_meseros})", f"${costo_meseros:,.0f}")
    col_c5.metric("TOTAL", f"${costo_directo:,.0f}")
    st.divider()

    st.sidebar.header("🛠️ Herramientas")
    if st.sidebar.button("➕ Añadir Mesa", use_container_width=True, key="add1"):
        if len(st.session_state.tables) < 14:
            x, y = calcular_coordenadas(len(st.session_state.tables))
            st.session_state.tables.append({"x": x, "y": y, "seats": [{"name": "", "type": "empty"} for _ in range(8)]})
            guardar_en_nube()
            st.rerun()

    if st.sidebar.button("🗑️ Borrar Mesa", use_container_width=True, key="del1"):
        if st.session_state.tables:
            st.session_state.tables.pop()
            guardar_en_nube()
            st.rerun()

    st.subheader("🗺️ Plano")
    svg_width, svg_height = 2200, 1400
    svg_content = f'<svg id="plano-svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}" style="background-color: #ffffff;"><defs><pattern id="grid" width="80" height="80" patternUnits="userSpaceOnUse"><path d="M 80 0 L 0 0 0 80" fill="none" stroke="#e2e8f0" stroke-width="1.5"/></pattern></defs><rect width="100%" height="100%" fill="url(#grid)" />'
    for idx, table in enumerate(st.session_state.tables):
        tx, ty = table['x'], table['y']
        for s_i in range(8):
            angle = s_i * (2 * math.pi / 8)
            sx, sy = tx + 120 * math.cos(angle), ty + 120 * math.sin(angle)
            seat = table['seats'][s_i]
            s_color, t_color = ("#00a8ff", "#ffffff") if seat['type'] == 'adult' else ("#fbc531", "#1e293b") if seat['type'] == 'child' else ("#cbd5e1", "#1e293b")
            svg_content += f'<circle cx="{sx}" cy="{sy}" r="24" fill="{s_color}" stroke="#475569" stroke-width="2"/><text x="{sx}" y="{sy+6}" font-size="14" font-weight="bold" fill="{t_color}" text-anchor="middle">{s_i+1}</text>'
            if seat['name']:
                svg_content += f'<text x="{sx}" y="{sy+42}" font-size="13" font-weight="bold" fill="#0f172a" text-anchor="middle">{seat["name"][:10]}</text>'
        svg_content += f'<circle cx="{tx}" cy="{ty}" r="52" fill="#1e293b" stroke="#0f172a" stroke-width="3"/><text x="{tx}" y="{ty+6}" font-size="16" font-weight="bold" fill="#ffffff" text-anchor="middle">Mesa {idx+1}</text>'
    svg_content += '</svg>'

    html_code = f'''
    <div style="margin-bottom: 10px;">
        <button id="download-png-btn" style="background-color: #ff4b4b; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer;">📥 Descargar Plano en PNG</button>
    </div>
    <div id="svg-container" style="overflow: auto; width: 100%; height: 600px; border: 2px solid #2f3640;">{svg_content}</div>
    <script>
    document.getElementById('download-png-btn').addEventListener('click', function() {{
        const svgElement = document.getElementById('plano-svg');
        const svgString = new XMLSerializer().serializeToString(svgElement);
        const svgBlob = new Blob([svgString], {{type: 'image/svg+xml;charset=utf-8'}});
        const DOMURL = window.URL || window.webkitURL || window;
        const url = DOMURL.createObjectURL(svgBlob);
        const image = new Image();
        image.onload = function() {{
            const canvas = document.createElement('canvas');
            canvas.width = {svg_width}; canvas.height = {svg_height};
            const context = canvas.getContext('2d');
            context.fillStyle = '#ffffff'; context.fillRect(0, 0, canvas.width, canvas.height);
            context.drawImage(image, 0, 0);
            const downloadLink = document.createElement('a');
            downloadLink.href = canvas.toDataURL('image/png');
            downloadLink.download = 'plano_boda.png';
            document.body.appendChild(downloadLink); downloadLink.click(); document.body.removeChild(downloadLink);
            DOMURL.revokeObjectURL(url);
        }};
        image.src = url;
    }});
    </script>
    '''
    st.components.v1.html(html_code, height=680)
    
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

        st.markdown("#### Asignación de Asientos (Sillas 1 a 8):")
        for s_idx in range(8):
            seat = t_data['seats'][s_idx]
            s_col1, s_col2, s_col3 = st.columns([1, 2, 3])
            
            with s_col1:
                st.markdown(f"**Silla {s_idx+1}**")
            with s_col2:
                tipo_actual_idx = 1 if seat['type'] == 'adult' else 2 if seat['type'] == 'child' else 0
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
