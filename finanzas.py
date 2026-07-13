import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime, timezone
from supabase import create_client, Client
import io
import google.generativeai as genai

# --- CONFIGURACIÓN DE IA (CONEXIÓN DIRECTA POR API - CAPA GRATUITA) ---
import requests

def consultar_gemini_directo(prompt_texto):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        # Intento Principal con el último Flash Estable
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
        
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt_texto}]}]}
        
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        data = response.json()
        
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"]
            
        # --- PLAN B AUTOMÁTICO EN CASO DE 404 ---
        # Si da error de modelo no encontrado, intentamos con Gemini 1.5 Pro automáticamente
        url_pro = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-latest:generateContent?key={api_key}"
        response_pro = requests.post(url_pro, headers=headers, json=payload, timeout=20)
        data_pro = response_pro.json()
        
        if "candidates" in data_pro and len(data_pro["candidates"]) > 0:
            return data_pro["candidates"][0]["content"]["parts"][0]["text"]
        elif "error" in data_pro:
            return f"⚠️ Error de la API de Google: {data_pro['error'].get('message', 'Desconocido')}"
            
        return "⚠️ No se recibió una respuesta clara del servidor. Intentá de nuevo."
    except Exception as e:
        return f"⚠️ Error de conexión con el módulo de IA. (Detalle: {e})"
        
# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Error de configuración en secrets.toml: {e}")
        st.stop()

supabase: Client = init_supabase()

# --- FUNCIÓN AUXILIAR DE ENCRIPTACIÓN ---
def encriptar_contrasena(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# --- SISTEMA DE LOGIN Y REGISTRO MULTI-CLIENTE ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
if "nombre_taller" not in st.session_state:
    st.session_state.nombre_taller = ""
if "user_rol" not in st.session_state:
    st.session_state.user_rol = "Admin"

if not st.session_state.autenticado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #4F46E5;'>💼 Finanzas & Stock Manager Pro</h1>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        tab_login, tab_registro = st.tabs(["🔒 Iniciar Sesión", "✨ Crear Cuenta (Prueba Gratis)"])
        
        with tab_login:
            with st.container(border=True):
                email_input = st.text_input("Correo Electrónico", key="login_email").strip().lower()
                pass_input = st.text_input("Contraseña", type="password", key="login_pass") 
                
                if st.button("Ingresar al Panel", use_container_width=True, type="primary"):
                    if email_input and pass_input:
                        
                        # ==========================================
                        # 🔥 ACCESO DIRECTO BLINDADO PARA OLIVIA IMAGEN
                        # ==========================================
                        if email_input == "admin@olivia.com" and pass_input == "taller2026":
                            st.session_state.autenticado = True
                            st.session_state.usuario_id = 1
                            st.session_state.nombre_taller = "Olivia Imagen"
                            st.session_state.user_rol = "Admin"
                            st.rerun()
                        # ==========================================
                        
                        else:
                            pass_encriptada = encriptar_contrasena(pass_input)
                            try:
                                res_user = supabase.table("usuarios").select("*").eq("email", email_input).eq("contrasena", pass_encriptada).execute()
                                if res_user.data:
                                    user_data = res_user.data[0]
                                    
                                    # CONTROL DE FECHA DE VENCIMIENTO (14 DÍAS DE PRUEBA)
                                    fecha_creacion_str = user_data["created_at"]
                                    fecha_creacion = datetime.fromisoformat(fecha_creacion_str.replace("Z", "+00:00"))
                                    fecha_actual = datetime.now(timezone.utc)
                                    dias_transcurridos = (fecha_actual - fecha_creacion).days
                                    
                                    if dias_transcurridos > 14:
                                        st.error("❌ Tu período de prueba de 14 días ha vencido.")
                                        st.info("ℹ️ Para activar tu licencia comercial comunícate con el administrador.")
                                    else:
                                        st.session_state.autenticado = True
                                        st.session_state.usuario_id = user_data["id"]
                                        st.session_state.nombre_taller = user_data["nombre_taller"]
                                        st.session_state.user_rol = user_data.get("rol", "Admin")
                                        st.rerun()
                                else:
                                    st.error("Correo o contraseña incorrectos.")
                            except Exception as db_err:
                                st.error("Error al conectar con la base de datos de usuarios.")
                    else:
                        st.warning("Por favor, completa todos los campos.")
                        
        with tab_registro:
            with st.container(border=True):
                reg_taller = st.text_input("Nombre de tu Emprendimiento / Taller", key="reg_taller").strip()
                reg_email = st.text_input("Correo Electrónico de Registro", key="reg_email").strip().lower()
                reg_pass = st.text_input("Crea tu Contraseña", type="password", key="reg_pass")
                
                if st.button("Registrarme y Comenzar", use_container_width=True):
                    if reg_taller and reg_email and reg_pass:
                        try:
                            check_user = supabase.table("usuarios").select("id").eq("email", reg_email).execute()
                            if check_user.data:
                                st.error("❌ Este correo ya se encuentra registrado.")
                            else:
                                hash_seguro = encriptar_contrasena(reg_pass)
                                nuevo_usuario = {"nombre_taller": reg_taller, "email": reg_email, "contrasena": hash_seguro, "rol": "Admin"}
                                supabase.table("usuarios").insert(nuevo_usuario).execute()
                                st.success("🎉 ¡Cuenta creada con éxito! Ya podés iniciar sesión.")
                        except Exception as e:
                            st.error(f"Error al registrar: {e}")
                    else:
                        st.warning("Por favor, completa todos los campos para el registro.")
    st.stop()

# --- COMIENZO DE LA SESIÓN FILTRADA ---
u_id = st.session_state.usuario_id
rol_actual = st.session_state.user_rol

try:
    user_actual_data = supabase.table("usuarios").select("*").eq("id", u_id).execute().data[0]
    owner_id = user_actual_data.get("owner_id")
    data_scope_id = owner_id if owner_id else u_id
except Exception:
    data_scope_id = u_id

# --- FUNCIONES DE CARGA ---
def cargar_datos_cloud(tabla):
    try:
        res = supabase.table(tabla).select("*").eq("usuario_id", data_scope_id).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

df_historial = cargar_datos_cloud("historial")
df_stock = cargar_datos_cloud("stock")
df_metas = cargar_datos_cloud("metas")
df_cat_local = cargar_datos_cloud("categories")

if not df_historial.empty:
    df_historial["monto"] = pd.to_numeric(df_historial["monto"], errors='coerce').fillna(0.0)
else:
    df_historial = pd.DataFrame(columns=["id", "fecha", "cuenta", "tipo", "monto", "categoria", "detalle", "estado_pago", "metodo_pago", "usuario_id"])

if df_stock.empty:
    df_stock = pd.DataFrame(columns=["id", "item", "cantidad", "minimo", "usuario_id"])
else:
    df_stock["cantidad"] = pd.to_numeric(df_stock["cantidad"], errors='coerce').fillna(0)
    df_stock["minimo"] = pd.to_numeric(df_stock["minimo"], errors='coerce').fillna(0)

if df_metas.empty:
    df_metas = pd.DataFrame(columns=["id", "meta", "objetivo", "acumulado", "usuario_id"])

# --- PROCESAMIENTO DE CATEGORÍAS ---
if df_cat_local.empty:
    categorias_ingreso = ["Venta Producto", "Servicio", "Diseño", "Otros"]
    categorias_gasto_negocio = ["Insumos", "Publicidad", "Herramientas", "Otros"]
    categorias_gasto_personal = ["Alimentos", "Servicios", "Ocio", "Otros"]
else:
    categorias_ingreso = df_cat_local[df_cat_local["tipo_categoria"] == "Ingreso"]["nombre_categoria"].tolist()
    categorias_gasto_negocio = df_cat_local[df_cat_local["tipo_categoria"] == "Gasto Negocio"]["nombre_categoria"].tolist()
    categorias_gasto_personal = df_cat_local[df_cat_local["tipo_categoria"] == "Gasto Personal"]["nombre_categoria"].tolist()

# --- CÁLCULO DE SALDOS ---
caja_negocio = 0.0
billetera_personal = 0.0

if not df_historial.empty:
    ingresos_n = df_historial[(df_historial["cuenta"] == "Negocio") & (df_historial["tipo"] == "Ingreso") & (df_historial["estado_pago"] != "Presupuesto")]["monto"].sum()
    gastos_n = df_historial[(df_historial["cuenta"] == "Negocio") & (df_historial["tipo"] == "Gasto")]["monto"].sum()
    caja_negocio = ingresos_n - gastos_n

    ingresos_p = df_historial[(df_historial["cuenta"] == "Personal") & (df_historial["tipo"] == "Ingreso")]["monto"].sum()
    gastos_p = df_historial[(df_historial["cuenta"] == "Personal") & (df_historial["tipo"] == "Gasto")]["monto"].sum()
    billetera_personal = ingresos_p - gastos_p
   # --- NAVEGACIÓN ---
with st.sidebar:
    st.markdown(f"<h2 style='color: #4F46E5; margin-top: 0px;'>⚡ {st.session_state.nombre_taller}</h2>", unsafe_allow_html=True)
    st.caption(f"Rol Activo: **{rol_actual}**")
    if st.button("Cerrar Sesión 🔓", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_id = None
        st.session_state.nombre_taller = ""
        st.session_state.user_rol = "Admin"
        st.rerun()
    st.markdown("---")
    
    if rol_actual == "Admin":
        opciones_menu = ["🏠 Dashboard General", "🤖 Consultor IA", "📝 Nueva Operación", "🧮 Calculadora de Costos", "📦 Stock de Insumos", "📉 Punto de Equilibrio", "🎯 Metas de Ahorro", "⚙️ Configurar Categorías", "📊 Mi Cierre de Caja", "👥 Personal del Taller"]
    else:
        opciones_menu = ["📝 Nueva Operación", "📦 Stock de Insumos", "📊 Mi Cierre de Caja"]
        
    seccion = st.radio("Navegación:", opciones_menu)
    st.markdown("---")
    
    if not df_stock.empty:
        criticos = df_stock[df_stock["cantidad"] <= df_stock["minimo"]]
        if not criticos.empty:
            st.error(f"⚠️ ¡Falta reponer {len(criticos)} insumos!")

# --- 🏠 DASHBOARD GENERAL ---
if seccion == "🏠 Dashboard General" and rol_actual == "Admin":
    st.title("💼 Panel de Control General")
    
    if caja_negocio < 0:
        st.error("⚠️ **Alerta Financiera:** La caja del taller registra un saldo desfavorable (en rojo).")
    if billetera_personal < 0:
        st.warning("⚠️ **Alerta Personal:** Tus finanzas individuales están en rojo.")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown(f"<div style='padding: 10px;'><p style='color: #94A3B8; font-size: 13px; font-weight: bold; margin-bottom: 5px; letter-spacing: 0.5px;'>🛠️ FONDOS DISPONIBLES EMPRENDIMIENTO</p><h2 style='color: #38BDF8; font-size: 46px; font-weight: 800; margin: 0px;'>$ {caja_negocio:,.2f}</h2><p style='color: #64748B; font-size: 12px; margin-top: 5px; margin-bottom: 0px;'>Capital total activo en la caja operativa de tu taller.</p></div>", unsafe_allow_html=True)
            
    with col2:
        with st.container(border=True):
            st.markdown(f"<div style='padding: 10px;'><p style='color: #94A3B8; font-size: 13px; font-weight: bold; margin-bottom: 5px; letter-spacing: 0.5px;'>👤 FINANZAS PERSONALES (RETIRADO LIBRE)</p><h2 style='color: #34D399; font-size: 46px; font-weight: 800; margin: 0px;'>$ {billetera_personal:,.2f}</h2><p style='color: #64748B; font-size: 12px; margin-top: 5px; margin-bottom: 0px;'>Dinero extraído neto disponible para tus gastos personales cotidianos.</p></div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("💡 Distribución Interna Recomendada")
    monto_negocio_total = max(0.0, caja_negocio)
    
    sub_col1, sub_col2, sub_col3 = st.columns(3)
    with sub_col1:
        with st.container(border=True): st.markdown(f"<div style='text-align: center; padding: 5px;'><p style='color: #38BDF8; font-size: 12px; font-weight: bold; margin-bottom: 2px;'>🛠️ CAJA INSUMOS (40%)</p><h3 style='margin: 0px; font-size: 24px; color: #E2E8F0;'>$ {monto_negocio_total * 0.40:,.2f}</h3></div>", unsafe_allow_html=True)
    with sub_col2:
        with st.container(border=True): st.markdown(f"<div style='text-align: center; padding: 5px;'><p style='color: #A78BFA; font-size: 12px; font-weight: bold; margin-bottom: 2px;'>💰 CAJA SUELDOS (40%)</p><h3 style='margin: 0px; font-size: 24px; color: #E2E8F0;'>$ {monto_negocio_total * 0.40:,.2f}</h3></div>", unsafe_allow_html=True)
    with sub_col3:
        with st.container(border=True): st.markdown(f"<div style='text-align: center; padding: 5px;'><p style='color: #FBBF24; font-size: 12px; font-weight: bold; margin-bottom: 2px;'>🔧 MANTENIMIENTO (20%)</p><h3 style='margin: 0px; font-size: 24px; color: #E2E8F0;'>$ {monto_negocio_total * 0.20:,.2f}</h3></div>", unsafe_allow_html=True)

    st.markdown("<br><hr style='border-color: #334155;'><br>", unsafe_allow_html=True)
    
    if df_historial.empty:
        st.info("No hay movimientos registrados todavía.")
    else:
        st.subheader("📊 Exportar Historial Completo")
        try:
            df_csv = df_historial.copy()
            if "fecha" in df_csv.columns:
                df_csv["fecha"] = pd.to_datetime(df_csv["fecha"], errors='coerce').dt.strftime("%Y-%m-%d")
            columnas_a_sacar = ["id", "usuario_id", "Mes", "fecha_txt"]
            df_csv = df_csv.drop(columns=[c for c in columnas_a_sacar if c in df_csv.columns], errors='ignore')
            df_csv.columns = [c.replace("_", " ").capitalize() for c in df_csv.columns]
            csv_data = df_csv.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button(label="📥 Descargar Planilla de Movimientos (Excel/CSV)", data=csv_data, file_name=f"Planilla_Movimientos_{st.session_state.nombre_taller}.csv", mime="text/csv", type="primary")
        except Exception:
            csv_simple = df_historial.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button(label="📥 Descargar Planilla Directa (CSV)", data=csv_simple, file_name=f"Planilla_Movimientos_{st.session_state.nombre_taller}.csv", mime="text/csv")

        st.markdown("<br>", unsafe_allow_html=True)
        df_historial_visual = df_historial.copy()
        df_historial_visual["fecha_dt"] = pd.to_datetime(df_historial_visual["fecha"], errors='coerce')
        df_historial_visual["Mes"] = df_historial_visual["fecha_dt"].dt.strftime("%Y-%m").fillna("Sin Fecha")
        
        mes_sel = st.selectbox("📆 Seleccionar Período:", sorted(df_historial_visual["Mes"].unique(), reverse=True))
        df_mes = df_historial_visual[df_historial_visual["Mes"] == mes_sel]
        
        st.subheader("📈 Balance Financiero Mensual")
        with st.container(border=True):
            total_ingresos_mes = df_mes[(df_mes["tipo"] == "Ingreso") & (df_mes["estado_pago"] != "Presupuesto")]["monto"].sum()
            total_egresos_mes = df_mes[df_mes["tipo"] == "Gasto"]["monto"].sum()
            df_grafico = pd.DataFrame({"Tipo": ["📥 Ventas / Ingresos", "📤 Gastos / Egresos"], "Monto ($)": [total_ingresos_mes, total_egresos_mes]}).set_index("Tipo")
            st.bar_chart(df_grafico, y="Monto ($)", color="#4F46E5", use_container_width=True)
        
        tab_ingresos, tab_egresos = st.tabs(["📥 Historial de INGRESOS (Ventas)", "📤 Historial de EGRESOS (Gastos)"])
        with tab_ingresos:
            for idx, row in df_mes[df_mes["tipo"] == "Ingreso"][::-1].iterrows():
                with st.container(border=True):
                    col_h1, col_h2, col_h3, col_h4 = st.columns([1, 2, 4, 1])
                    fecha_str = row["fecha_dt"].strftime("%Y-%m-%d") if pd.notnull(row["fecha_dt"]) else str(row["fecha"])
                    col_h1.caption(fecha_str)
                    col_h2.markdown(f"**$ {float(row['monto']):,.2f}**")
                    col_h3.markdown(f"🔹 *{row['categoria']}* — {row['detalle']}\n\nCondición: **{row['estado_pago']}** | Medio: **{row['metodo_pago']}**")
                    if col_h4.button("🗑️", key=f"del_ing_{row['id']}"):
                        supabase.table("historial").delete().eq("id", int(row["id"])).execute()
                        st.rerun()
        with tab_egresos:
            for idx, row in df_mes[df_mes["tipo"] == "Gasto"][::-1].iterrows():
                with st.container(border=True):
                    col_e1, col_e2, col_e3, col_e4 = st.columns([1, 2, 4, 1])
                    fecha_str = row["fecha_dt"].strftime("%Y-%m-%d") if pd.notnull(row["fecha_dt"]) else str(row["fecha"])
                    col_e1.caption(fecha_str)
                    col_e2.markdown(f"**$ {float(row['monto']):,.2f}**")
                    lbl = "⚙️ GASTO TALLER" if row["cuenta"] == "Negocio" else "👤 PERSONAL"
                    col_e3.markdown(f"**{lbl}** | *{row['categoria']}*\n\n{row['detalle']}")
                    if col_e4.button("🗑️", key=f"del_egr_{row['id']}"):
                        supabase.table("historial").delete().eq("id", int(row["id"])).execute()
                        st.rerun()

# --- 🤖 MÓDULO CONSULTOR IA ---
elif seccion == "🤖 Consultor IA" and rol_actual == "Admin":
    st.title("🤖 Consultor Financiero IA Inteligente")
    st.markdown("Dejá que la Inteligencia Artificial analice tus números para encontrar áreas de optimización, fugas de dinero y estrategias de precios.")
    
    items_criticos_lista = []
    if not df_stock.empty:
        criticos_df = df_stock[df_stock["cantidad"] <= df_stock["minimo"]]
        if not criticos_df.empty:
            items_criticos_lista = criticos_df["item"].tolist()
            
    items_criticos_txt = ", ".join(items_criticos_lista) if items_criticos_lista else "Ninguno (Stock Ok)"

    with st.container(border=True):
        st.subheader("📊 Resumen Enviado al Consultor")
        st.write(f"🏢 **Taller Activo:** {st.session_state.nombre_taller}")
        st.write(f"🛠️ **Fondos en Caja:** $ {caja_negocio:,.2f}")
        st.write(f"👤 **Caja Personal:** $ {billetera_personal:,.2f}")
        st.write(f"📦 **Insumos Críticos a Reponer:** {items_criticos_txt}")

    if st.button("🚀 Generar Diagnóstico con IA", type="primary", use_container_width=True):
        with st.spinner("🤖 Analizando base de datos en tiempo real..."):
            historial_texto = df_historial.tail(15).to_string() if not df_historial.empty else "Sin movimientos registrados"
            resumen_data = f"Nombre: {st.session_state.nombre_taller}\nCaja Negocio: ${caja_negocio:.2f}\nCaja Personal: ${billetera_personal:.2f}\nCriticos: {items_criticos_txt}\nHistorial:\n{historial_texto}"
            
            prompt_expert = f"Actúa como consultor financiero estratégico para un taller gráfico y de personalización en Argentina. Analizá los siguientes datos:\n{resumen_data}\nDevolvé un reporte estructurado con diagnóstico operativo, fugas de dinero o riesgos, y 3 consejos de rentabilidad clave. Hablá en español rioplatense (Argentina), de forma directa, corporativa pero cercana."
            
            # Llamada directa pasando por encima de la librería rota
            respuesta_ia = consultar_gemini_directo(prompt_expert)
            st.markdown("<br><hr>", unsafe_allow_html=True)
            st.markdown(respuesta_ia)
            
# --- 📝 NUEVA OPERACIÓN ---
elif seccion == "📝 Nueva Operación":
    st.title("📝 Carga de Movimientos")
    opciones_carga = ["Registrar Venta / Presupuesto", "Registrar Gasto Negocio"] if rol_actual == "Empleado" else ["Registrar Venta / Presupuesto", "Registrar Gasto Negocio", "Retirar Sueldo", "Registrar Gasto Personal"]
    opcion = st.selectbox("¿Qué vas a registrar hoy?", opciones_carga)
    
    with st.container(border=True):
        if opcion == "Registrar Venta / Presupuesto":
            if "ultimo_comprobante" not in st.session_state:
                st.session_state.ultimo_comprobante = None
                st.session_state.tipo_comprobante = None

            monto = st.number_input("Monto total ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", categorias_ingreso)
            descuenta_stock = False
            insumo_seleccionado = None
            amount_to_deduct = 0
            
            if not df_stock.empty and categoria == "Venta Producto":
                descuenta_stock = st.checkbox("🔄 ¿Esta venta descuenta materiales del Stock?")
                if descuenta_stock:
                    col_st1, col_st2 = st.columns(2)
                    insumo_seleccionado = col_st1.selectbox("Seleccionar Insumo:", df_stock["item"].tolist())
                    amount_to_deduct = col_st2.number_input("Cantidad utilizada:", min_value=1, value=1, step=1)

            col_v1, col_v2 = st.columns(2)
            est_pago = col_v1.selectbox("Condición:", ["Total Pagado", "Seña", "Fiado", "Presupuesto"])
            estado_guardar = "Total" if est_pago == "Total Pagado" else est_pago
            met_pago = col_v2.selectbox("Medio de Cobro:", ["Efectivo", "Mercado Pago", "Transferencia", "Tarjeta", "Ninguno (Presupuesto)"])
            cliente_nombre = st.text_input("Nombre del Cliente (Opcional):")
            nota = st.text_input("Detalle del trabajo / Producto:")

            if st.button("Guardar e Imprimir Comprobante", type="primary"):
                detalle_final = nota
                if descuenta_stock and insumo_seleccionado:
                    detalle_final = f"{detalle_final} [Descontado {amount_to_deduct} un. de {insumo_seleccionado}]"
                detalle_final = f"Cliente: {cliente_nombre} | {detalle_final}" if cliente_nombre else detalle_final
                
                datos_insertar = {"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Negocio", "tipo": "Ingreso", "monto": float(monto), "categoria": categoria, "detalle": detalle_final, "estado_pago": estado_guardar, "metodo_pago": met_pago, "usuario_id": data_scope_id}
                supabase.table("historial").insert(datos_insertar).execute()
                
                if descuenta_stock and insumo_seleccionado:
                    fila_insumo = df_stock[df_stock["item"] == insumo_seleccionado].iloc[0]
                    nueva_cantidad = max(0, int(fila_insumo["cantidad"]) - amount_to_deduct)
                    supabase.table("stock").update({"cantidad": nueva_cantidad}).eq("id", int(fila_insumo["id"])).execute()
                
                fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                nom_c = cliente_nombre.strip() if cliente_nombre else "Cliente"
                if estado_guardar == "Total":
                    st.session_state.ultimo_comprobante = f"🧾 *COMPROBANTE DE PAGO*\n\n📅 *Fecha:* {fecha_hoy}\n👤 *Cliente:* {nom_c}\n💼 *Detalle:* {nota}\n💰 *Total Abonado:* $ {monto:,.2f}\n💳 *Medio:* {met_pago}"
                    st.session_state.tipo_comprobante = "¡Recibo guardado!"
                st.rerun()

            if st.session_state.ultimo_comprobante:
                st.success(st.session_state.tipo_comprobante)
                st.text_area("Texto listo para WhatsApp:", value=st.session_state.ultimo_comprobante, height=150)
                if st.button("Limpiar Pantalla"):
                    st.session_state.ultimo_comprobante = None
                    st.rerun()

        elif opcion == "Registrar Gasto Negocio":
            monto = st.number_input("Monto ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", categorias_gasto_negocio)
            met_pago = st.selectbox("Pagado desde:", ["Efectivo", "Mercado Pago", "Transferencia", "Tarjeta"])
            nota = st.text_input("Detalle:")
            if st.button("Guardar Gasto", type="primary"):
                # REEMPLAZADO MEXPORT_PAGO POR MET_PAGO (CORRECCIÓN CRÍTICA)
                supabase.table("historial").insert({"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Negocio", "tipo": "Gasto", "monto": float(monto), "categoria": categoria, "detalle": nota, "estado_pago": "Total", "metodo_pago": met_pago, "usuario_id": data_scope_id}).execute()
                st.rerun()

        elif opcion == "Retirar Sueldo" and rol_actual == "Admin":
            monto = st.number_input("Monto a extraer ($)", min_value=0.0, max_value=max(0.0, caja_negocio), step=50.0)
            if st.button("Confirmar Retiro", type="primary"):
                f = datetime.now().strftime("%Y-%m-%d")
                supabase.table("historial").insert([
                    {"fecha": f, "cuenta": "Negocio", "tipo": "Gasto", "monto": float(monto), "categoria": "Retiro de Socio", "detalle": "Retiro ganancias", "estado_pago": "Total", "metodo_pago": "Efectivo", "usuario_id": data_scope_id},
                    {"fecha": f, "cuenta": "Personal", "tipo": "Ingreso", "monto": float(monto), "categoria": "Sueldo", "detalle": "Ingreso desde Negocio", "estado_pago": "Total", "metodo_pago": "Efectivo", "usuario_id": data_scope_id}
                ]).execute()
                st.rerun()

        elif opcion == "Registrar Gasto Personal" and rol_actual == "Admin":
            monto = st.number_input("Monto ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", categorias_gasto_personal)
            nota = st.text_input("Detalle:")
            if st.button("Guardar Gasto Personal", type="primary"):
                supabase.table("historial").insert({"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Personal", "tipo": "Gasto", "monto": float(monto), "categoria": "Gasto Personal", "detalle": nota, "estado_pago": "Total", "metodo_pago": "Efectivo", "usuario_id": data_scope_id}).execute()
                st.rerun()

# --- 🧮 CALCULADORA DE COSTOS ---
elif seccion == "🧮 Calculadora de Costos" and rol_actual == "Admin":
    st.title("🧮 Calculadora de Costos y Precio de Venta")
    modo_cliente = st.toggle("👁️ Modo Vista Cliente (Ocultar Costos y Ganancias)", value=False)
    
    col_calc1, col_calc2 = st.columns([4, 3])
    with col_calc1:
        with st.container(border=True):
            nombre_prod = st.text_input("Nombre del producto / trabajo:", placeholder="Ej: Remera Estampada DTF")
            costo_materiales = st.number_input("Suma total de materiales usados ($):", min_value=0.0, value=0.0, step=100.0)
            tiempo_horas = st.number_input("Tiempo estimado de trabajo (Horas):", min_value=0.0, value=0.5, step=0.25)
            precio_hora_trabajo = st.number_input("Valor de tu hora de trabajo ($):", min_value=0.0, value=4000.0, step=500.0)
            costo_mano_obra = tiempo_horas * precio_hora_trabajo
            costo_fijos_prod = st.number_input("Costo de estructura fijo por producto ($):", min_value=0.0, value=500.0, step=100.0)
            porcentaje_ganancia = st.slider("Porcentaje de ganancia deseado (%):", min_value=0, max_value=300, value=50, step=5)

    costo_total_fabricacion = costo_materiales + costo_mano_obra + costo_fijos_prod
    monto_ganancia_comercial = costo_total_fabricacion * (porcentaje_ganancia / 100.0)
    precio_venta_sugerido = costo_total_fabricacion + monto_ganancia_comercial

    with col_calc2:
        with st.container(border=True):
            st.markdown(f"<h1 style='text-align: center; color: #34D399; font-size: 50px;'>$ {precio_venta_sugerido:,.2f}</h1>", unsafe_allow_html=True)
            if not modo_cliente:
                st.write(f"📦 Materiales: $ {costo_materiales:,.2f} | 👤 Mano de Obra: $ {costo_mano_obra:,.2f}")
                st.write(f"⚡ Costos Fijos: $ {costo_fijos_prod:,.2f} | 💰 Ganancia: $ {monto_ganancia_comercial:,.2f}")
                
# --- 📝 PLANTILLA DE PRESUPUESTO PARA EL CLIENTE (BLINDADA) ---
        st.markdown("---")
        st.subheader("📝 Presupuesto Listo para Enviar")
        st.markdown("Copiá este texto y mandaselo directo a tu cliente por WhatsApp o mensaje:")
        
        # 1. Buscamos el nombre del trabajo de forma segura
        nombre_trabajo = "Trabajo Personalizado"
        for var_name in ['producto', 'descripcion', 'nombre_trabajo', 'item_name']:
            if var_name in locals():
                nombre_trabajo = locals()[var_name]
                break
        
        # 2. Buscamos el precio calculado de forma segura entre las variables comunes
        precio_final = 0.0
        for var_name in ['precio_sugerido', 'precio_final', 'precio_venta', 'total_sugerido', 'precio_sug', 'precio']:
            if var_name in locals():
                try:
                    precio_final = float(locals()[var_name])
                    break
                except:
                    continue
        
        # Armamos el texto de forma limpia y profesional
        texto_presupuesto = (
            f"¡Hola! Te paso el presupuesto detallado para tu trabajo: *{nombre_trabajo}*\n\n"
            f"📌 *Detalle:* Servicio de diseño y producción personalizada.\n"
            f"💰 *Valor Total:* $ {precio_final:,.2f}\n\n"
            f"⚠️ *Condiciones:* Válido por 5 días debido a la reposición de insumos. "
            f"Se inicia el trabajo con el pago del 100%.\n\n"
            f"¡Cualquier duda me avisás y lo coordinamos! Muchas gracias por confiar en *{st.session_state.nombre_taller}* 🚀"
        )
        
        # Lo mostramos en un cuadro de texto especial que permite copiar con un solo clic
        st.text_area("Presupuesto para copiar:", value=texto_presupuesto, height=180, key="txt_presupuesto_cliente")

# --- 📦 STOCK DE INSUMOS ---
elif seccion == "📦 Stock de Insumos":
    st.title("📦 Control de Inventario Personalizado")
    with st.expander("➕ Agregar Nuevo Insumo al Stock"):
        col_i1, col_i2, col_i3 = st.columns(3)
        nombre_i = col_i1.text_input("Nombre del material:")
        cant_i = col_i2.number_input("Cantidad Inicial:", min_value=0, step=1)
        minimo_i = col_i3.number_input("Stock Mínimo Alerta:", min_value=0, step=1)
        if st.button("Registrar Insumo", type="primary"):
            if nombre_i.strip():
                supabase.table("stock").insert({"item": nombre_i.strip(), "cantidad": int(cant_i), "minimo": int(minimo_i), "usuario_id": data_scope_id}).execute()
                st.rerun()

    st.markdown("---")
    if df_stock.empty:
        st.info("No tienes insumos cargados todavía.")
    else:
        for idx, row in df_stock.iterrows():
            es_critico = int(row["cantidad"]) <= int(row["minimo"])
            color_cartel = "🔴 Stock Crítico" if es_critico else "🟢 Stock Ok"
            with st.container(border=True):
                c_name, c_status, c_cant, c_actions, c_del = st.columns([3, 2, 2, 3, 1])
                c_name.markdown(f"**{row['item']}**")
                if es_critico: c_status.error(color_cartel)
                else: c_status.success(color_cartel)
                c_cant.markdown(f"Unidades: `{row['cantidad']}` (Mín: {row['minimo']})")
                
                btn_menos, btn_mas = c_actions.columns(2)
                if btn_menos.button("➖ Usar 1", key=f"min_{row['id']}"):
                    supabase.table("stock").update({"cantidad": max(0, int(row["cantidad"]) - 1)}).eq("id", int(row["id"])).execute()
                    st.rerun()
                if btn_mas.button("➕ Sumar 1", key=f"add_{row['id']}"):
                    supabase.table("stock").update({"cantidad": int(row["cantidad"]) + 1}).eq("id", int(row["id"])).execute()
                    st.rerun()
                if c_del.button("🗑️", key=f"del_insumo_{row['id']}"):
                    supabase.table("stock").delete().eq("id", int(row["id"])).execute()
                    st.rerun()

# --- 📉 PUNTO DE EQUILIBRIO ---
elif seccion == "📉 Punto de Equilibrio" and rol_actual == "Admin":
    st.title("📉 Análisis de Punto de Equilibrio")
    with st.container(border=True):
        costos_fijos = st.number_input("Costos fijos mensuales ($):", min_value=0.0, value=50000.0, step=1000.0)
        precio_promedio = st.number_input("Precio de venta promedio ($):", min_value=1.0, value=2000.0)
        costo_promedio = st.number_input("Costo de insumos promedio ($):", min_value=0.0, value=800.0)
    margen = precio_promedio - costo_promedio
    if margen > 0:
        unidades = costos_fijos / margen
        st.markdown("---")
        res1, res2 = st.columns(2)
        res1.metric("Unidades mensuales necesarias:", f"{int(unidades)} un.")
        res2.metric("Facturación mínima requerida:", f"${unidades * precio_promedio:,.2f}")

# --- 🎯 METAS DE AHORRO ---
elif seccion == "🎯 Metas de Ahorro": # O el nombre exacto de tu sección
    st.title("🎯 Metas de Ahorro y Alcancías")
    
    # ... acá va la lógica que carga el df_metas ...

    st.markdown("---") # <-- ESTA LÍNEA (578) TIENE QUE TENER LA MISMA INDENTACIÓN QUE EL ST.TITLE
    if df_metas.empty:
        st.info("No tenés metas de ahorro creadas todavía.")
    else:
        st.subheader("📌 Tus Alcancías")
        for idx, row in df_metas.iterrows():
            with st.container(border=True):
                obj = float(row['objetivo'])
                acum = float(row.get('acumulado', 0.0))
                
                porcentaje = (acum / obj) * 100 if obj > 0 else 0.0
                
                col_m1, col_m2, col_m3 = st.columns([4, 3, 2])
                
                col_m1.markdown(f"🎯 **{row['meta']}**")
                col_m1.progress(min(1.0, acum / obj) if obj > 0 else 0.0)
                col_m1.caption(f"📈 Progreso: **{porcentaje:.1f}%** completado")
                
                col_m2.markdown(f"💰 **$ {acum:,.2f}** / $ {obj:,.2f}")
                
                with col_m3:
                    monto_ahorrar = st.number_input("Sumar ($):", min_value=0.0, step=500.0, key=f"add_m_{row['id']}")
                    if st.button("💾", key=f"btn_save_m_{row['id']}", help="Guardar ahorro"):
                        if monto_ahorrar > 0:
                            nuevo_acumulado = acum + monto_ahorrar
                            supabase.table("metas").update({"acumulado": nuevo_acumulado}).eq("id", int(row["id"])).execute()
                            st.success("¡Ahorro guardado!")
                            st.rerun()
                    
                    if st.button("🗑️", key=f"del_meta_{row['id']}"):
                        supabase.table("metas").delete().eq("id", int(row["id"])).execute()
                        st.rerun()
                        
# --- ⚙️ CONFIGURACIÓN DE CATEGORÍAS ---
elif seccion == "⚙️ Configurar Categorías" and rol_actual == "Admin":
    st.title("⚙️ Gestión Personalizada de Categorías")
    with st.container(border=True):
        tipo_nueva = st.selectbox("¿A qué módulo pertenece?", ["Ingreso", "Gasto Negocio", "Gasto Personal"])
        nombre_nueva = st.text_input("Nombre de la categoría:")
        if st.button("Guardar Nueva Categoría", type="primary"):
            if nombre_nueva.strip():
                supabase.table("categorias").insert({"tipo_categoria": tipo_nueva, "nombre_categoria": nombre_nueva.strip(), "usuario_id": data_scope_id}).execute()
                st.rerun()

# --- 📊 MI CIERRE DE CAJA ---
elif seccion == "📊 Mi Cierre de Caja":
    st.title("📊 Resumen del Día (Cierre de Caja)")
    fecha_hoy_db = datetime.now().strftime("%Y-%m-%d")
    st.markdown(f"### 📆 Movimientos del día de hoy")
    
    if df_historial.empty:
        st.info("No se registran movimientos cargados hoy.")
    else:
        df_historial_hoy = df_historial.copy()
        df_historial_hoy["fecha_txt"] = pd.to_datetime(df_historial_hoy["fecha"], errors='coerce').dt.strftime("%Y-%m-%d")
        df_hoy = df_historial_hoy[df_historial_hoy["fecha_txt"] == fecha_hoy_db]
        
        if df_hoy.empty:
            st.info("Todavía no se cargaron operaciones hoy.")
        else:
            hoy_efectivo = df_hoy[(df_hoy["tipo"] == "Ingreso") & (df_hoy["metodo_pago"] == "Efectivo")]["monto"].sum()
            st.metric("Total Recaudado Hoy Efectivo:", f"$ {hoy_efectivo:,.2f}")

# --- 👥 GESTIÓN DE PERSONAL ---
elif seccion == "👥 Personal del Taller" and rol_actual == "Admin":
    st.title("👥 Panel de Control de Colaboradores")
    with st.container(border=True):
        nombre_emp = st.text_input("Nombre del Empleado:").strip()
        email_emp = st.text_input("Correo de Trabajo:").strip().lower()
        pass_emp = st.text_input("Contraseña:", type="password")
        if st.button("Registrar Colaborador", type="primary"):
            if nombre_emp and email_emp and pass_emp:
                hash_seguro_emp = encriptar_contrasena(pass_emp)
                supabase.table("usuarios").insert({"nombre_taller": st.session_state.nombre_taller, "email": email_emp, "contrasena": hash_seguro_emp, "rol": "Empleado", "owner_id": u_id}).execute()
                st.success("🎉 ¡Colaborador registrado!")
                st.rerun()
