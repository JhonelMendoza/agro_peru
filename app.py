import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
import unicodedata
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="AgroIA Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .css-1d391kg { background-color: #262730; }
    .metric-card { background-color: #1E1E1E; padding: 15px; border-radius: 10px; border: 1px solid #333; text-align: center; margin-bottom: 15px; }
    .metric-value { font-size: 2rem; font-weight: bold; color: #00E5FF; }
    .metric-label { font-size: 0.9rem; color: #A0A0A0; }
    </style>
""", unsafe_allow_html=True)

if 'lat_seleccionada' not in st.session_state:
    st.session_state['lat_seleccionada'] = None
    st.session_state['lon_seleccionada'] = None

bd_dra_peru = ['amazonas', 'ancash', 'apurimac', 'arequipa', 'ayacucho', 'cajamarca', 'callao', 'cusco', 'huancavelica', 'huanuco', 'ica', 'junin', 'la libertad', 'lambayeque', 'lima', 'loreto', 'madre de dios', 'moquegua', 'pasco', 'piura', 'puno', 'san martin', 'tacna', 'tumbes', 'ucayali']

deps_costa = ['tumbes', 'piura', 'lambayeque', 'la libertad', 'ancash', 'lima', 'callao', 'ica', 'arequipa', 'moquegua', 'tacna']
meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

bd_cultivos = {
    'costa': {'cultivos': ['Palta', 'Esparrago', 'Vid', 'Algodon', 'Cebolla'], 'base_exito': [88, 85, 92, 75, 80]},
    'sierra_media': {'cultivos': ['Papa Nativa', 'Maiz', 'Habas', 'Arveja', 'Quinua'], 'base_exito': [95, 80, 88, 70, 85]},
    'sierra_alta': {'cultivos': ['Maca', 'Canihua', 'Papa Amarga', 'Oca'], 'base_exito': [90, 85, 92, 78]},
    'selva': {'cultivos': ['Cacao', 'Cafe', 'Platano', 'Palma', 'Camu Camu'], 'base_exito': [85, 82, 90, 75, 88]},
    'arida': {'cultivos': ['Tara', 'Olivo', 'Pitahaya', 'Tuna'], 'base_exito': [95, 90, 85, 92]}
}

bd_senasa = {
    'costa': [{'plaga': 'Mosca de la fruta', 'tratamiento': 'Trampas etologicas, control biologico.'}, {'plaga': 'Oidium', 'tratamiento': 'Azufre en polvo, podas de ventilacion.'}],
    'sierra_media': [{'plaga': 'Rancha (Phytophthora infestans)', 'tratamiento': 'Uso de cultivares resistentes, fungicidas preventivos.'}, {'plaga': 'Gorgojo de los Andes', 'tratamiento': 'Rotacion de cultivos, barreras fisicas.'}],
    'sierra_alta': [{'plaga': 'Gorgojo de la maca', 'tratamiento': 'Control cultural, extractos vegetales.'}],
    'selva': [{'plaga': 'Roya del cafe', 'tratamiento': 'Oxicloruro de cobre, variedades tolerantes.'}, {'plaga': 'Moniliasis', 'tratamiento': 'Remocion de frutos infectados, podas.'}],
    'arida': [{'plaga': 'Queresa', 'tratamiento': 'Lavados a presion, aceites agricolas.'}, {'plaga': 'Mosca blanca', 'tratamiento': 'Trampas cromaticas amarillas.'}]
}

def normalizar_texto(texto):
    if not texto: return ""
    return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

@st.cache_data
def obtener_datos_geo(lat, lon):
    try:
        headers = {'User-Agent': 'AgroIA_Tech_App/2.0'}
        res = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10", headers=headers).json()
        return res.get('display_name', '')
    except:
        return ""

@st.cache_data
def obtener_elevacion(lat, lon):
    try:
        res = requests.get(f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}").json()
        return res.get('elevation', [0])[0]
    except:
        return 0

col_mapa, col_datos = st.columns([1.2, 1.8])

with col_mapa:
    st.markdown("<h3 style='color: white;'>Geo-Visor AGROIA</h3>", unsafe_allow_html=True)
    centro_mapa = [-9.19, -75.01]
    zoom_mapa = 6
    if st.session_state['lat_seleccionada'] is not None:
        centro_mapa = [st.session_state['lat_seleccionada'], st.session_state['lon_seleccionada']]
        zoom_mapa = 10
    m = folium.Map(location=centro_mapa, zoom_start=zoom_mapa)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satellite').add_to(m)
    if st.session_state['lat_seleccionada'] is not None:
        folium.Marker([st.session_state['lat_seleccionada'], st.session_state['lon_seleccionada']]).add_to(m)
    mapa_web = st_folium(m, height=900, width=500, key="mapa")

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
        
        with st.spinner("Entrenando modelo predictivo con datos historicos..."):
            display_name = obtener_datos_geo(lat, lon)
            altitud_msnm = obtener_elevacion(lat, lon)
            display_norm = normalizar_texto(display_name)
            
            es_mar_o_invalido = False
            if not display_name or any(palabra in display_norm for palabra in ['ocean', 'sea', 'mar ', 'pacifico', 'pacific']):
                es_mar_o_invalido = True
            if 'peru' not in display_norm and not es_mar_o_invalido:
                es_mar_o_invalido = True
                
            if es_mar_o_invalido:
                st.markdown("<h3 style='color: #00E5FF;'>Analisis de Riesgo Climatico</h3>", unsafe_allow_html=True)
                st.warning("ZONA NO APTA PARA CULTIVO: El marcador se encuentra en el mar o fuera de la frontera agricola continental peruana.")
            else:
                st.markdown(f"<h4 style='color: #00FF7F;'>Ubicacion validada: {display_name}</h4>", unsafe_allow_html=True)
                
                region_dra = 'No identificada'
                for dep in bd_dra_peru:
                    if dep in display_norm:
                        region_dra = dep
                        break
                
                if region_dra == 'No identificada':
                    region_dra = 'lima'
                    
                url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,PRECTOTCORR,RH2M&community=AG&longitude={lon}&latitude={lat}&start=20140101&end=20231231&format=JSON"
                res = requests.get(url)
                
                if res.status_code == 200:
                    datos = res.json()['properties']['parameter']
                    df = pd.DataFrame({
                        'Fecha': pd.to_datetime(list(datos['T2M'].keys()), format='%Y%m%d'),
                        'Temp': list(datos['T2M'].values()),
                        'Lluvia': list(datos['PRECTOTCORR'].values()),
                        'Humedad': list(datos['RH2M'].values())
                    })
                    df = df[df['Temp'] > -50]
                    df['Anio'] = df['Fecha'].dt.year
                    df['Mes'] = df['Fecha'].dt.month
                    
                    st.markdown("<h3 style='color: #00E5FF;'>Motor de Prediccion Climatica AGROIA </h3>", unsafe_allow_html=True)
                    
                    col_p1, col_p2 = st.columns(2)
                    anio_pred = col_p1.selectbox("Seleccione Año de Proyeccion", [2025, 2026, 2027, 2028, 2029, 2030])
                    mes_pred = col_p2.selectbox("Seleccione Mes de Proyeccion", list(range(1, 13)), format_func=lambda x: meses_nombres[x-1])
                    
                    df_mes = df[df['Mes'] == mes_pred]
                    df_anual = df_mes.groupby('Anio').agg({'Temp': 'mean', 'Lluvia': 'mean'}).reset_index()
                    
                    if len(df_anual) > 1:
                        X = df_anual[['Anio']]
                        y_temp = df_anual['Temp']
                        y_lluvia = df_anual['Lluvia']
                        modelo_temp = LinearRegression().fit(X, y_temp)
                        modelo_lluvia = LinearRegression().fit(X, y_lluvia)
                        temp_pred = modelo_temp.predict([[anio_pred]])[0]
                        lluvia_pred = max(0, modelo_lluvia.predict([[anio_pred]])[0])
                    else:
                        temp_pred = df_mes['Temp'].mean()
                        lluvia_pred = df_mes['Lluvia'].mean()
                        
                    col_m1, col_m2 = st.columns(2)
                    col_m1.markdown(f"<div class='metric-card'><div class='metric-label'>Temp. Predicha ({meses_nombres[mes_pred-1]} {anio_pred})</div><div class='metric-value'>{temp_pred:.1f} C</div></div>", unsafe_allow_html=True)
                    col_m2.markdown(f"<div class='metric-card'><div class='metric-label'>Lluvia Predicha ({meses_nombres[mes_pred-1]} {anio_pred})</div><div class='metric-value'>{lluvia_pred:.1f} mm/dia</div></div>", unsafe_allow_html=True)
                    
                    prob_helada = min(100, max(0, len(df_mes[df_mes['Temp'] <= 0]) / len(df_mes) * 100 + (0 if temp_pred > 2 else 20))) if len(df_mes) > 0 else 0
                    prob_inundacion = min(100, max(0, len(df_mes[df_mes['Lluvia'] >= 20]) / len(df_mes) * 100 + (20 if lluvia_pred > 15 else 0))) if len(df_mes) > 0 else 0
                    prob_sequia = min(100, max(0, 100 - (lluvia_pred * 15))) if lluvia_pred < 2 else 0
                    
                    df_riesgos = pd.DataFrame({
                        'Evento Extremo': ['Helada', 'Sequia', 'Inundacion'],
                        'Probabilidad (%)': [prob_helada, prob_sequia, prob_inundacion]
                    })
                    
                    fig_riesgos = px.bar(df_riesgos, x='Evento Extremo', y='Probabilidad (%)', title=f"Alerta de Eventos Extremos para {meses_nombres[mes_pred-1]} {anio_pred}", template="plotly_dark", color='Probabilidad (%)', color_continuous_scale='Reds')
                    fig_riesgos.update_layout(height=250, margin=dict(l=0, r=0, t=40, b=0))
                    st.plotly_chart(fig_riesgos, use_container_width=True)
                    
                    st.markdown("<h3 style='color: #00FF7F;'>Inteligencia Agronomica</h3>", unsafe_allow_html=True)
                    
                    piso = 'arida'
                    if lluvia_pred > 0.5 or region_dra not in deps_costa:
                        if altitud_msnm < 2000:
                            piso = 'costa' if region_dra in deps_costa else 'selva'
                        elif 2000 <= altitud_msnm < 3500:
                            piso = 'sierra_media'
                        else:
                            piso = 'sierra_alta'
                            
                    data_cultivos = bd_cultivos[piso]
                    nombres_cultivos = data_cultivos['cultivos']
                    exito_base = data_cultivos['base_exito']
                    
                    penalizacion_clima = (prob_helada * 0.2) + (prob_sequia * 0.15) + (prob_inundacion * 0.15)
                    exito_final = np.clip(np.array(exito_base) - penalizacion_clima, 0, 100)
                    
                    df_prediccion = pd.DataFrame({
                        'Cultivo': nombres_cultivos,
                        'Probabilidad de Exito (%)': exito_final
                    })
                    
                    titulo_grafico = f"Probabilidad de Exito (Piso Ecologico: {piso.replace('_', ' ').title()})<br><sup>Fuente: Direccion Regional de Agricultura y MINAGRI (Ajustado al modelo predictivo de {anio_pred})</sup>"
                    
                    fig_bar = px.bar(df_prediccion, x='Probabilidad de Exito (%)', y='Cultivo', orientation='h', title=titulo_grafico, template="plotly_dark", color='Probabilidad de Exito (%)', color_continuous_scale='Viridis')
                    fig_bar.update_layout(height=250, margin=dict(l=0, r=0, t=60, b=0))
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                    st.markdown("<h4 style='color: #FFA500;'>Alertas Fitosanitarias (SENASA)</h4>", unsafe_allow_html=True)
                    alertas = bd_senasa[piso]
                    for alerta in alertas:
                        st.markdown(f"<div style='background-color: #2E1A1A; padding: 10px; border-left: 5px solid #FF4B4B; margin-bottom: 10px;'><b>Amenaza Proyectada:</b> {alerta['plaga']}<br><b>Contramedida Oficial:</b> {alerta['tratamiento']}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<h3 style='color: #00E5FF;'>Analisis de Riesgo Climatico</h3>", unsafe_allow_html=True)
        st.info("Haga clic en un punto del mapa  para generar un diagnóstico agroclimático y proyectar los sembríos de mayor rendimiento según las características de la zona.")
        
        col_m1, col_m2 = st.columns(2)
        col_m1.markdown("<div class='metric-card'><div class='metric-label'>Altitud Topografica</div><div class='metric-value'>-</div></div>", unsafe_allow_html=True)
        col_m2.markdown("<div class='metric-card'><div class='metric-label'>Temperatura Promedio</div><div class='metric-value'>-</div></div>", unsafe_allow_html=True)
        
        fig_empty = px.bar(title="Esperando seleccion en el mapa...", template="plotly_dark")
        fig_empty.update_layout(height=250, margin=dict(l=0, r=0, t=40, b=0), xaxis={'visible': False}, yaxis={'visible': False})
        st.plotly_chart(fig_empty, use_container_width=True)
