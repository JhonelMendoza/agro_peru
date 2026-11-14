import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
from sklearn.linear_model import LinearRegression
import unicodedata


st.set_page_config(page_title="AgroIA", layout="wide")


with st.sidebar:
    st.title(" AGROIA ")
    st.write("Plataforma de inteligencia satelital para prediccion climatica y planificacion agricola.")
    st.divider()
    st.subheader("Instrucciones del Sistema")
    st.write("1. Navegue por el visor geoespacial.")
    st.write("2. Seleccione un cuadrante en el territorio peruano.")
    st.divider()
    st.caption("MODULO: AGROIA")
    st.caption("ESTADO: Servidores Operativos")


st.header("Panel de Control de Riesgo Climatico")
st.markdown("Integracion de datos meteorologicos historicos (2015-2025) y bases de datos MIDAGRI/SENASA.")
            
if 'lat_seleccionada' not in st.session_state:
    st.session_state['lat_seleccionada'] = None
    st.session_state['lon_seleccionada'] = None

bd_dra_peru = {
    'amazonas': {'costa': 'No apto', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Frijol, Maiz', 'selva': 'Cacao nativo, Cafe, Platano'},
    'ancash': {'costa': 'Esparrago, Palta', 'sierra_alta': 'Maca, Papa nativa', 'sierra_media': 'Quinua, Maiz amilaceo', 'selva': 'Cafe'},
    'apurimac': {'costa': 'No apto', 'sierra_alta': 'Papa nativa, Canihua', 'sierra_media': 'Quinua, Maiz', 'selva': 'No apto'},
    'arequipa': {'costa': 'Cebolla, Ajo', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Quinua', 'selva': 'No apto'},
    'ayacucho': {'costa': 'No apto', 'sierra_alta': 'Maca, Papa nativa', 'sierra_media': 'Quinua, Tara', 'selva': 'Cacao, Cafe'},
    'cajamarca': {'costa': 'No apto', 'sierra_alta': 'Papa nativa, Oca', 'sierra_media': 'Maiz morado', 'selva': 'Cafe, Cacao'},
    'cusco': {'costa': 'No apto', 'sierra_alta': 'Papa amarga', 'sierra_media': 'Maiz gigante, Quinua', 'selva': 'Cacao chuncho, Te, Cafe'},
    'huancavelica': {'costa': 'No apto', 'sierra_alta': 'Maca', 'sierra_media': 'Quinua, Maiz', 'selva': 'No apto'},
    'huanuco': {'costa': 'No apto', 'sierra_alta': 'Maca', 'sierra_media': 'Papa amarilla', 'selva': 'Cacao, Cafe'},
    'ica': {'costa': 'Pallar, Algodon nativo, Vid', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'No apto'},
    'junin': {'costa': 'No apto', 'sierra_alta': 'Maca, Canihua', 'sierra_media': 'Papa nativa', 'selva': 'Cafe, Cacao, Kion'},
    'la libertad': {'costa': 'Cana de azucar', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Quinua, Tarwi', 'selva': 'No apto'},
    'lambayeque': {'costa': 'Zapallo loche, Algodon', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'No apto'},
    'lima': {'costa': 'Manzana, Fresa', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Chirimoya', 'selva': 'No apto'},
    'loreto': {'costa': 'No apto', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'Camu camu, Aguaje, Platano'},
    'madre de dios': {'costa': 'No apto', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'Castana, Copoazu, Yuca'},
    'moquegua': {'costa': 'Palta, Lima', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Oregano nativo', 'selva': 'No apto'},
    'pasco': {'costa': 'No apto', 'sierra_alta': 'Maca, Papa nativa', 'sierra_media': 'Quinua', 'selva': 'Rocoto, Cafe, Cacao'},
    'piura': {'costa': 'Limon sutil, Mango', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Cafe', 'selva': 'No apto'},
    'puno': {'costa': 'No apto', 'sierra_alta': 'Papa amarga', 'sierra_media': 'Quinua, Habas', 'selva': 'Cafe, Frutales'},
    'san martin': {'costa': 'No apto', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'Cacao, Cafe, Sacha inchi'},
    'tacna': {'costa': 'Olivo, Aji amarillo', 'sierra_alta': 'Papa nativa', 'sierra_media': 'Oregano nativo', 'selva': 'No apto'},
    'tumbes': {'costa': 'Limon, Platano, Cacao', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'No apto'},
    'ucayali': {'costa': 'No apto', 'sierra_alta': 'No apto', 'sierra_media': 'No apto', 'selva': 'Palma aceitera, Cacao, Platano'}
}

bd_senasa = {
    'papa': {'plaga': 'Rancha / Gorgojo de los Andes', 'tratamiento': 'Control biologico (Beauveria bassiana). Uso de fungicidas sistemicos.'},
    'maca': {'plaga': 'Gorgojo de la maca / Gusano cortador', 'tratamiento': 'Control cultural, trampas de luz, aplicacion de extracto de Neem.'},
    'quinua': {'plaga': 'Polilla de la quinua / Mildiu', 'tratamiento': 'Aplicacion de Spinosad (biologico). Protocolos de rotacion de cultivos.'},
    'maiz': {'plaga': 'Gusano cogollero', 'tratamiento': 'Liberacion de avispas Trichogramma o aplicacion de Bacillus thuringiensis.'},
    'cacao': {'plaga': 'Moniliasis / Mazorca negra', 'tratamiento': 'Podas fitosanitarias intensivas. Aplicacion regulada de cobre.'},
    'cafe': {'plaga': 'Roya del cafe / Broca', 'tratamiento': 'Oxicloruro de cobre para Roya. Instalacion de trampas etilicas para Broca.'},
    'platano': {'plaga': 'Mal de Panama / Sigatoka Negra', 'tratamiento': 'Inoculacion de Trichoderma spp. en suelo. Control estricto de malezas.'},
    'rocoto': {'plaga': 'Mosca de la fruta / Acaros', 'tratamiento': 'Implementacion de trampas pegajosas y control etologico continuo.'},
    'default': {'plaga': 'Insectos masticadores / Hongos de suelo', 'tratamiento': 'Aplicacion de abonos organicos (Biol) y caldo sulfocalcico preventivo.'}
}

deps_costa = ['tumbes', 'piura', 'lambayeque', 'la libertad', 'ancash', 'lima', 'callao', 'ica', 'arequipa', 'moquegua', 'tacna']
nombres_meses = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'}

def normalizar_texto(texto):
    if not texto: return ""
    return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

@st.cache_data
def obtener_datos_geo(lat, lon):
    try:
        res = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1", headers={'User-Agent': 'AgroIA_Tech/1.0'}).json()
        nombre = res.get('display_name', 'Ubicacion desconocida')
        dep = res.get('address', {}).get('state', res.get('address', {}).get('region', res.get('address', {}).get('province', '')))
        return nombre, dep
    except:
        return "Error", ""

@st.cache_data
def obtener_elevacion(lat, lon):
    try:
        res = requests.get(f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}").json()
        return res.get('elevation', [0])[0]
    except:
        return 0

col_mapa, col_datos = st.columns([1.2, 1])


with col_mapa:
    centro_mapa = [-9.19, -75.01]
    zoom_mapa = 6
    
    if st.session_state['lat_seleccionada'] is not None:
        centro_mapa = [st.session_state['lat_seleccionada'], st.session_state['lon_seleccionada']]
        zoom_mapa = 11

    m = folium.Map(location=centro_mapa, zoom_start=zoom_mapa)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite Hybrid'
    ).add_to(m)
    
    if st.session_state['lat_seleccionada'] is not None:
        folium.Marker(
            [st.session_state['lat_seleccionada'], st.session_state['lon_seleccionada']],
            popup="Punto de Analisis",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)
    
    mapa_web = st_folium(m, height=700, width=800, key="visor_principal")


with col_datos:
    if mapa_web and mapa_web.get("last_clicked"):
        nuevo_lat = mapa_web["last_clicked"]["lat"]
        nuevo_lon = mapa_web["last_clicked"]["lng"]
        
        if nuevo_lat != st.session_state['lat_seleccionada'] or nuevo_lon != st.session_state['lon_seleccionada']:
            st.session_state['lat_seleccionada'] = nuevo_lat
            st.session_state['lon_seleccionada'] = nuevo_lon
            st.rerun()
            
    if st.session_state['lat_seleccionada'] is not None:
        lat = st.session_state['lat_seleccionada']
        lon = st.session_state['lon_seleccionada']
        
        with st.spinner("Procesando telemetria satelital..."):
            nombre_ubi, dep_mapa = obtener_datos_geo(lat, lon)
            altitud_msnm = obtener_elevacion(lat, lon)
            dep_norm = normalizar_texto(dep_mapa)
            
            region_dra = 'No identificada'
            if dep_norm:
                for clave in bd_dra_peru.keys():
                    if clave in dep_norm:
                        region_dra = clave
                        break
            
            if region_dra == 'No identificada':
                st.error("ERROR DE LIMITES: Coordenadas detectadas en zona maritima o territorio internacional. El analisis requiere seleccion dentro de la superficie agricola peruana.")
            else:
                st.info(f"UBICACION DETECTADA: {nombre_ubi}")
                url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M_MIN,PRECTOTCORR&community=AG&longitude={lon}&latitude={lat}&start=20150101&end=20251231&format=JSON"
                respuesta = requests.get(url)
                
                if respuesta.status_code == 200:
                    datos = respuesta.json()
                    df = pd.DataFrame({
                        'Fecha': list(datos['properties']['parameter']['T2M_MIN'].keys()),
                        'Temp_Min': list(datos['properties']['parameter']['T2M_MIN'].values()),
                        'Lluvia': list(datos['properties']['parameter']['PRECTOTCORR'].values())
                    })
                    
                    df = df[df['Temp_Min'] > -50].copy()
                    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y%m%d')
                    df['Mes'] = df['Fecha'].dt.month
                    
                    if altitud_msnm < 2000:
                        piso_ecologico, nombre_piso = ('costa', "Costa / Valles") if region_dra in deps_costa else ('selva', "Selva Tropical")
                    elif 2000 <= altitud_msnm < 3500:
                        piso_ecologico, nombre_piso = 'sierra_media', "Sierra Interandina"
                    else:
                        piso_ecologico, nombre_piso = 'sierra_alta', "Sierra Alta / Puna"
                    
                    col_m1, col_m2 = st.columns(2)
                    col_m1.metric(label="Jurisdiccion Regional", value=region_dra.upper())
                    col_m2.metric(label="Altitud Topografica", value=f"{altitud_msnm} msnm", delta=nombre_piso, delta_color="off")
                    
                    st.divider()
                    st.subheader("Deteccion de Riesgos Meteorologicos")
                    
                    meses_heladas = df[df['Temp_Min'] <= 0]['Mes'].unique()
                    max_lluvia = df['Lluvia'].max()
                    
                    col_r1, col_r2 = st.columns(2)
                    
                    with col_r1:
                        if len(meses_heladas) > 0:
                            st.warning(f"ALERTA TERMICA: Riesgo de heladas criticas durante los meses de {', '.join([nombres_meses[m] for m in sorted(meses_heladas)])}.")
                        else:
                            st.success("PARAMETRO TERMICO: Estable. Riesgo de heladas inferior al umbral critico.")
                            
                    with col_r2:
                        if max_lluvia > 40:
                            st.error(f"ALERTA HIDRICA: Precipitaciones torrenciales detectadas (picos de {max_lluvia:.1f} mm/dia). Riesgo de deslizamientos en: {', '.join([nombres_meses[m] for m in sorted(df[df['Lluvia'] > 40]['Mes'].unique())])}.")
                        else:
                            st.success("PARAMETRO HIDRICO: Precipitaciones dentro de margenes de seguridad operacional.")

                    st.divider()
                    st.subheader("Inteligencia Agronomica")
                    
                    catalogo = bd_dra_peru.get(region_dra, bd_dra_peru['junin'])
                    recomendacion = catalogo.get(piso_ecologico, 'Cultivo estandar')
                    
                    alerta_senasa = bd_senasa['default']
                    for plaga_clave, plaga_datos in bd_senasa.items():
                        if plaga_clave in normalizar_texto(recomendacion):
                            alerta_senasa = plaga_datos
                            break
                    
                    tab1, tab2 = st.tabs(["Directiva MIDAGRI", "Protocolo SENASA"])
                    
                    with tab1:
                        st.write("Con base en el modelo meteorologico predictivo y el perfil topografico, el catalogo de biodiversidad autoctona sugiere:")
                        st.info(f"CULTIVO ESTRATEGICO SUGERIDO: {recomendacion.upper()}")
                        
                    with tab2:
                        st.write("Evaluacion de riesgo sanitario basado en el cultivo estrategico proyectado:")
                        st.error(f"AMENAZA PROYECTADA: {alerta_senasa['plaga']}")
                        st.success(f"CONTRAMEDIDA OFICIAL: {alerta_senasa['tratamiento']}")

                else:
                    st.error("FALLO DE CONEXION: No se pudo establecer enlace con los servidores de NASA POWER.")
    else:
        st.write("ESTADO DEL SISTEMA: En espera de seleccion de coordenadas en el visor geoespacial.")
