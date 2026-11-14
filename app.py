import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
from sklearn.linear_model import LinearRegression
import unicodedata

st.set_page_config(page_title="AgroIA - NASA Space Apps", layout="wide", page_icon="🌱")
st.title("🛰️ AgroIA: Predicción Climática y Agrícola")
st.markdown("Haz clic en cualquier parte del mapa de Perú para analizar el microclima, evaluar riesgos y obtener recomendaciones.")

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
    'papa': {'plaga': 'Rancha / Gorgojo de los Andes', 'tratamiento': 'Control biológico (Beauveria bassiana). Fungicidas.'},
    'maca': {'plaga': 'Gorgojo de la maca / Gusano cortador', 'tratamiento': 'Control cultural, trampas de luz, extracto de Neem.'},
    'quinua': {'plaga': 'Polilla de la quinua / Mildiu', 'tratamiento': 'Spinosad (biológico). Rotación de cultivos.'},
    'maiz': {'plaga': 'Gusano cogollero', 'tratamiento': 'Avispas Trichogramma o Bacillus thuringiensis (Bt).'},
    'cacao': {'plaga': 'Moniliasis / Mazorca negra', 'tratamiento': 'Podas fitosanitarias intensivas. Aplicación de cobre.'},
    'cafe': {'plaga': 'Roya del café / Broca', 'tratamiento': 'Oxicloruro de cobre para Roya. Trampas etílicas para Broca.'},
    'platano': {'plaga': 'Mal de Panamá / Sigatoka Negra', 'tratamiento': 'Trichoderma spp. en suelo. Control de malezas.'},
    'rocoto': {'plaga': 'Mosca de la fruta / Ácaros', 'tratamiento': 'Uso de trampas pegajosas y control etológico.'},
    'default': {'plaga': 'Insectos masticadores / Hongos de suelo', 'tratamiento': 'Abonos orgánicos (Biol) y caldo sulfocálcico preventivo.'}
}

deps_costa = ['tumbes', 'piura', 'lambayeque', 'la libertad', 'ancash', 'lima', 'callao', 'ica', 'arequipa', 'moquegua', 'tacna']
nombres_meses = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'}

def normalizar_texto(texto):
    if not texto: return ""
    return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

@st.cache_data
def obtener_datos_geo(lat, lon):
    try:
        res = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1", headers={'User-Agent': 'HackathonNASA/Web'}).json()
        nombre = res.get('display_name', 'Ubicación desconocida')
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

col1, col2 = st.columns([1, 1])

with col1:
    m = folium.Map(location=[-9.19, -75.01], zoom_start=6)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite Hybrid'
    ).add_to(m)
    
    mapa_web = st_folium(m, height=600, width=700)

with col2:
    if mapa_web and mapa_web.get("last_clicked"):
        lat = mapa_web["last_clicked"]["lat"]
        lon = mapa_web["last_clicked"]["lng"]
        
        with st.spinner("Conectando con servidores de NASA y geolocalizando..."):
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
                st.error("🌊 *Puntero fuera de límite agrícola o en el mar.*")
            else:
                st.success(f"📍 *{nombre_ubi}*")
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
                        piso_ecologico, nombre_piso = ('costa', "Costa") if region_dra in deps_costa else ('selva', "Selva")
                    elif 2000 <= altitud_msnm < 3500:
                        piso_ecologico, nombre_piso = 'sierra_media', "Sierra Media"
                    else:
                        piso_ecologico, nombre_piso = 'sierra_alta', "Sierra Alta"
                    
                    st.write(f"🏢 *Región:* {region_dra.title()} | 🏔️ *Microclima:* {nombre_piso} ({altitud_msnm} msnm)")
                    
                    st.subheader("📡 Sistema de Alerta Temprana")
                    meses_heladas = df[df['Temp_Min'] <= 0]['Mes'].unique()
                    if len(meses_heladas) > 0:
                        st.warning(f"❄️ *Riesgo de Heladas:* Meses críticos: {', '.join([nombres_meses[m] for m in sorted(meses_heladas)])}")
                    else:
                        st.info("✅ Sin riesgo inminente de heladas extremas.")
                        
                    max_lluvia = df['Lluvia'].max()
                    if max_lluvia > 40:
                        meses_lluvia = df[df['Lluvia'] > 40]['Mes'].unique()
                        st.error(f"🌊 *Alerta Huaycos:* Lluvias torrenciales (hasta {max_lluvia:.1f} mm/día). Meses críticos: {', '.join([nombres_meses[m] for m in sorted(meses_lluvia)])}")
                    else:
                        st.info("✅ Precipitaciones estables.")

                    st.subheader("🌱 Recomendación Agrícola y Fitosanitaria")
                    catalogo = bd_dra_peru.get(region_dra, bd_dra_peru['junin'])
                    recomendacion = catalogo.get(piso_ecologico, 'Cultivo estándar')
                    
                    alerta_senasa = bd_senasa['default']
                    for plaga_clave, plaga_datos in bd_senasa.items():
                        if plaga_clave in normalizar_texto(recomendacion):
                            alerta_senasa = plaga_datos
                            break
                            
                    st.success(f"*Cultivo Autóctono Ideal:* {recomendacion.upper()}")
                    st.markdown(f"*🛡️ Protocolo SENASA:*")
                    st.write(f"- 🐛 *Amenaza:* {alerta_senasa['plaga']}")
                    st.write(f"- 🧪 *Tratamiento:* {alerta_senasa['tratamiento']}")
                else:
                    st.error("Error de conexión con la NASA.")
    else:
        st.info("👆 Haz clic en cualquier parte del mapa para comenzar el análisis satelital.")
