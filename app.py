import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
import unicodedata
import plotly.graph_objects as go
import plotly.express as px

# 1. CONFIGURACIÓN Y MODO OSCURO FORZADO
st.set_page_config(page_title="AgroIA - NASA Space Apps", layout="wide", initial_sidebar_state="collapsed")

# CSS para oscurecer la interfaz y dar estilo a las tarjetas
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .css-1d391kg { background-color: #262730; }
    .metric-card { background-color: #1E1E1E; padding: 15px; border-radius: 10px; border: 1px solid #333; text-align: center; }
    .metric-value { font-size: 2rem; font-weight: bold; color: #00E5FF; }
    .metric-label { font-size: 0.9rem; color: #A0A0A0; }
    </style>
""", unsafe_allow_html=True)

# --- MEMORIA DEL SISTEMA ---
if 'lat_seleccionada' not in st.session_state:
    st.session_state['lat_seleccionada'] = None
    st.session_state['lon_seleccionada'] = None

# --- BASES DE DATOS ---
bd_dra_peru = {
    'amazonas': {'costa': 'No apto', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Frijol, Maiz', 'selva': 'Cacao nativo, Cafe'},
    'ancash': {'costa': 'Esparrago, Palta', 'sierra_alta': 'Maca, Papa nativa', 'sierra_media': 'Quinua, Maiz amilaceo', 'selva': 'Cafe'},
    'apurimac': {'costa': 'No apto', 'sierra_alta': 'Papa nativa, Canihua', 'sierra_media': 'Quinua, Maiz', 'selva': 'No apto'},
    'arequipa': {'costa': 'Cebolla, Ajo', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Quinua', 'selva': 'No apto'},
    'ayacucho': {'costa': 'No apto', 'sierra_alta': 'Maca, Papa nativa', 'sierra_media': 'Quinua, Tara', 'selva': 'Cacao'},
    'cajamarca': {'costa': 'No apto', 'sierra_alta': 'Papa nativa, Oca', 'sierra_media': 'Maiz morado', 'selva': 'Cafe, Cacao'},
    'cusco': {'costa': 'No apto', 'sierra_alta': 'Papa amarga', 'sierra_media': 'Maiz gigante, Quinua', 'selva': 'Cacao chuncho, Cafe'},
    'huancavelica': {'costa': 'No apto', 'sierra_alta': 'Maca', 'sierra_media': 'Quinua, Maiz', 'selva': 'No apto'},
    'huanuco': {'costa': 'No apto', 'sierra_alta': 'Maca', 'sierra_media': 'Papa amarilla', 'selva': 'Cacao, Cafe'},
    'ica': {'costa': 'Pallar, Algodon nativo, Vid', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'No apto'},
    'junin': {'costa': 'No apto', 'sierra_alta': 'Maca, Canihua', 'sierra_media': 'Papa nativa', 'selva': 'Cafe, Cacao, Kion'},
    'la libertad': {'costa': 'Cana de azucar', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Quinua, Tarwi', 'selva': 'No apto'},
    'lambayeque': {'costa': 'Zapallo loche, Algodon', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'No apto'},
    'lima': {'costa': 'Manzana, Fresa', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Chirimoya', 'selva': 'No apto'},
    'loreto': {'costa': 'No apto', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'Camu camu, Aguaje, Platano'},
    'madre de dios': {'costa': 'No apto', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'Castana, Copoazu'},
    'moquegua': {'costa': 'Palta, Lima', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Oregano nativo', 'selva': 'No apto'},
    'pasco': {'costa': 'No apto', 'sierra_alta': 'Maca, Papa nativa', 'sierra_media': 'Quinua', 'selva': 'Rocoto, Cafe, Cacao'},
    'piura': {'costa': 'Limon sutil, Mango', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Cafe', 'selva': 'No apto'},
    'puno': {'costa': 'No apto', 'sierra_alta': 'Papa amarga', 'sierra_media': 'Quinua, Habas', 'selva': 'Cafe, Frutales'},
    'san martin': {'costa': 'No apto', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'Cacao, Cafe, Sacha inchi'},
    'tacna': {'costa': 'Olivo, Aji amarillo', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Oregano nativo', 'selva': 'No apto'},
    'tumbes': {'costa': 'Limon, Platano, Cacao', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'No apto'},
    'ucayali': {'costa': 'No apto', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'Palma aceitera, Cacao'}
}

bd_senasa = {
    'papa': {'plaga': 'Rancha / Gorgojo', 'tratamiento': 'Beauveria bassiana. Fungicidas sistemicos.'},
    'maca': {'plaga': 'Gorgojo / Gusano cortador', 'tratamiento': 'Control cultural, trampas de luz, extracto de Neem.'},
    'quinua': {'plaga': 'Polilla / Mildiu', 'tratamiento': 'Spinosad (biologico). Rotacion de cultivos.'},
    'maiz': {'plaga': 'Gusano cogollero', 'tratamiento': 'Avispas Trichogramma o Bacillus thuringiensis.'},
    'cacao': {'plaga': 'Moniliasis / Mazorca negra', 'tratamiento': 'Podas fitosanitarias. Aplicacion de cobre.'},
    'cafe': {'plaga': 'Roya / Broca', 'tratamiento': 'Oxicloruro de cobre. Trampas etilicas para Broca.'},
    'platano': {'plaga': 'Mal de Panama / Sigatoka', 'tratamiento': 'Inoculacion de Trichoderma spp. Control de malezas.'},
    'default': {'plaga': 'Insectos masticadores', 'tratamiento': 'Abonos organicos (Biol) y caldo sulfocalcico.'}
}

deps_costa = ['tumbes', 'piura', 'lambayeque', 'la libertad', 'ancash', 'lima', 'callao', 'ica', 'arequipa', 'moquegua', 'tacna']

def normalizar_texto(texto):
    if not texto: return ""
    return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

@st.cache_data
def obtener_datos_geo(lat, lon):
    try:
        res = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1").json()
        dep = res.get('address', {}).get('state', '')
        return res.get('display_name', 'Ubicacion'), dep
    except:
        return "Error", ""

@st.cache_data
def obtener_elevacion(lat, lon):
    try:
        res = requests.get(f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}").json()
        return res.get('elevation', [0])[0]
    except:
        return 0

# --- LAYOUT ESTILO DASHBOARD ---
# Columna del mapa (más grande) y columna de datos
col_mapa, col_datos = st.columns([1.8, 1.2])

with col_mapa:
    st.markdown("<h3 style='color: white;'>🛰️ Geo-Visor AgroIA</h3>", unsafe_allow_html=True)
    centro_mapa = [-9.19, -75.01]
    zoom_mapa = 6
    
    if st.session_state['lat_seleccionada'] is not None:
        centro_mapa = [st.session_state['lat_seleccionada'], st.session_state['lon_seleccionada']]
        zoom_mapa = 10

    m = folium.Map(location=centro_mapa, zoom_start=zoom_mapa)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satellite').add_to(m)
    
    if st.session_state['lat_seleccionada'] is not None:
        folium.Marker([st.session_state['lat_seleccionada'], st.session_state['lon_seleccionada']], icon=folium.Icon(color="red")).add_to(m)
    
    mapa_web = st_folium(m, height=750, width=850, key="mapa")

with col_datos:
    if mapa_web and mapa_web.get("last_clicked"):
        lat = mapa_web["last_clicked"]["lat"]
        lon = mapa_web["last_clicked"]["lng"]
        
        if lat != st.session_state['lat_seleccionada'] or lon != st.session_state['lon_seleccionada']:
            st.session_state['lat_seleccionada'] = lat
            st.session_state['lon_seleccionada'] = lon
            st.rerun()
            
    if st.session_state['lat_seleccionada'] is not None:
        lat = st.session_state['lat_seleccionada']
        lon = st.session_state['lon_seleccionada']
        
        with st.spinner("Sincronizando telemetría..."):
            nombre_ubi, dep_mapa = obtener_datos_geo(lat, lon)
            altitud_msnm = obtener_elevacion(lat, lon)
            dep_norm = normalizar_texto(dep_mapa)
            
            region_dra = next((clave for clave in bd_dra_peru.keys() if clave in dep_norm), 'No identificada')
            
            if region_dra == 'No identificada':
                st.error("Ubicación fuera de la frontera agrícola peruana validada.")
            else:
                url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,PRECTOTCORR,RH2M&community=AG&longitude={lon}&latitude={lat}&start=20230101&end=20231231&format=JSON"
                res = requests.get(url)
                
                if res.status_code == 200:
                    datos = res.json()['properties']['parameter']
                    df = pd.DataFrame({
                        'Fecha': pd.to_datetime(list(datos['T2M'].keys()), format='%Y%m%d'),
                        'Temp': list(datos['T2M'].values()),
                        'Lluvia': list(datos['PRECTOTCORR'].values()),
                        'Humedad': list(datos['RH2M'].values())
                    })
                    df = df[df['Temp'] > -50] # Filtrar errores NASA
                    
                    temp_promedio = df['Temp'].mean()
                    humedad_promedio = df['Humedad'].mean()
                    
                    # 1. SECCIÓN: Detection of Meteorological Hazards
                    st.markdown("<h3 style='color: #00E5FF;'>Detection of Meteorological Hazards</h3>", unsafe_allow_html=True)
                    
                    # Cajas de métricas rápidas
                    col_m1, col_m2 = st.columns(2)
                    col_m1.markdown(f"<div class='metric-card'><div class='metric-label'>Altitud Topográfica</div><div class='metric-value'>{altitud_msnm} m</div></div>", unsafe_allow_html=True)
                    col_m2.markdown(f"<div class='metric-card'><div class='metric-label'>Temp. Promedio</div><div class='metric-value'>{temp_promedio:.1f} °C</div></div>", unsafe_allow_html=True)
                    
                    st.write("") # Espaciador
                    
                    # Gráficos tipo Medidor (Gauges) para Humedad y Lluvia
                    col_g1, col_g2 = st.columns(2)
                    
                    fig_hum = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = humedad_promedio,
                        title = {'text': "Humedad Relativa (%)", 'font': {'color': 'white'}},
                        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#00E5FF"}, 'bgcolor': "black"}
                    ))
                    fig_hum.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="#0E1117", font={'color': "white"})
                    col_g1.plotly_chart(fig_hum, use_container_width=True)

                    riesgo_hidrico = df['Lluvia'].max()
                    fig_lluvia = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = riesgo_hidrico,
                        title = {'text': "Pico Lluvia (mm/día)", 'font': {'color': 'white'}},
                        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#FF4B4B"}, 'bgcolor': "black"}
                    ))
                    fig_lluvia.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="#0E1117", font={'color': "white"})
                    col_g2.plotly_chart(fig_lluvia, use_container_width=True)

                    # Gráfico de líneas (Tendencia anual)
                    fig_line = px.line(df, x='Fecha', y='Temp', title="Fluctuación Térmica (Histórico NASA)", template="plotly_dark")
                    fig_line.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig_line, use_container_width=True)

                    # 2. SECCIÓN: Agronomic Intelligence
                    st.markdown("<h3 style='color: #00FF7F;'>Agronomic Intelligence</h3>", unsafe_allow_html=True)
                    
                    piso = 'arida' if (df['Lluvia'].mean() < 0.5 and region_dra in deps_costa) else ('costa' if altitud_msnm < 2000 and region_dra in deps_costa else ('selva' if altitud_msnm < 2000 else ('sierra_media' if altitud_msnm < 3500 else 'sierra_alta')))
                    recomendacion = 'Tara, Olivo, Pitahaya' if piso == 'arida' else bd_dra_peru[region_dra].get(piso, 'Cultivo estándar')
                    alerta_senasa = next((datos for clave, datos in bd_senasa.items() if clave in normalizar_texto(recomendacion)), bd_senasa['default'])
                    
                    # Pestañas diseñadas como tarjetas
                    tab1, tab2 = st.tabs(["MIDAGRI Directive", "SENASA Protocol"])
                    
                    with tab1:
                        st.info(f"*Optimal Planting Recommendations:*\n\nBasado en el perfil climático {piso.replace('_', ' ').title()}, se sugiere priorizar:\n### {recomendacion.upper()}")
                        
                    with tab2:
                        st.error(f"*Phytosanitary Alerts:\n\nAmenaza:* {alerta_senasa['plaga']}")
                        st.success(f"*Disease Control Protocols:*\n\n{alerta_senasa['tratamiento']}")
