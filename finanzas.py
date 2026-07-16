import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Olivia Imagen - Gestión Financiera", page_icon="🛍️", layout="wide")

# --- CONTROL DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "nombre_taller" not in st.session_state:
    st.session_state.nombre_taller = "Olivia Imagen"
if "rol" not in st.session_state:
    st.session_state.rol = "Empleado"
if "usuario_email" not in st.session_state:
    st.session_state.usuario_email = ""
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
if "owner_id" not in st.session_state:
    st.session_state.owner_id = None

# --- CONEXIÓN A SUPABASE ---
from supabase import create_client, Client

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Error de conexión con Supabase: {e}")

# --- FUNCIÓN AUXILIAR PARA EXTRAER DATOS ---
def extraer_datos_respuesta(res):
    if isinstance(res, tuple):
        data = res[0]
        if hasattr(data, "data"):
            return data.data
        return data
    elif hasattr(res, "data"):
        return res.data
    return []

# --- CONFIGURACIÓN DE IA (CONEXIÓN DIRECTA) ---
def consultar_gemini_directo(prompt_texto):
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY", "")
        if not api_key:
            return "⚠️ No se detectó la clave de Google en los secretos de Streamlit."
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt_texto}]}]}
        
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        data = response.json()
        
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        elif "error" in data:
            return f"⚠️ Nota del servidor: {data['error'].get('message', 'Error de cuota o clave inválida')}"
            
        return "⚠️ El servidor de IA no devolvió una respuesta válida."
    except Exception as e:
        return f"⚠️ Error de conexión con el módulo de IA: {e}"


# ==========================================
# 🔐 PANTALLA DE ACCESO (LOGIN / REGISTRO SaaS)
# ==========================================
if not st.session_state.get("autenticado", False):
    st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>💼 Finanzas & Stock Manager Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Accedé a tu panel o registrá tu taller para empezar tu prueba de 14 días gratis</p>", unsafe_allow_html=True)
    
    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "🚀 Crear Cuenta (14 días gratis)"])
    
    # --- TAB INICIAR SESIÓN ---
    with tab_login:
        with st.container(border=True):
            email_input = st.text_input("Correo Electrónico", placeholder="ejemplo@olivia.com", key="login_email")
            password_input = st.text_input("Contraseña", type="password", placeholder="••••••••", key="login_pass")
            
            if st.button("Ingresar al Panel", type="primary", use_container_width=True):
                if email_input and password_input:
                    try:
                        res_user = supabase.table("usuarios").select("*").eq("email", email_input).execute()
                        datos_user = extraer_datos_respuesta(res_user)
                        
                        if datos_user:
                            user_data = datos_user[0]
                            
                            # Validar campo contraseña de forma segura
                            clave_usuario = None
                            for k in ["password", "contraseña", "contrasena", "clave", "pass"]:
                                if k in user_data:
                                    clave_usuario = user_data[k]
                                    break
                            
                            if str(clave_usuario) == str(password_input):
                                # --- CONTROL DE VENCIMIENTO DE PRUEBA (SaaS) ---
                                vto_prueba = user_data.get("trial_expires_at")
                                if vto_prueba:
                                    fecha_vto = pd.to_datetime(vto_prueba).tz_localize(None)
                                    if datetime.now() > fecha_vto:
                                        st.error("❌ Tu período de prueba de 14 días ha vencido. Contactanos para activar tu suscripción mensual.")
                                        st.stop()
                                
                                st.session_state.autenticado = True
                                st.session_state.usuario_id = user_data["id"]
                                st.session_state.usuario_email = user_data["email"]
                                st.session_state.rol = user_data.get("rol", "Empleado")
                                st.session_state.nombre_taller = user_data.get("taller", user_data.get("nombre_taller", "Olivia Imagen"))
                                
                                # Definir el owner_id de la sesión para aislar los datos
                                if st.session_state.rol == "Admin":
                                    st.session_state.owner_id = user_data["id"]
                                else:
                                    st.session_state.owner_id = user_data.get("owner_id")
                                    
                                st.success(f"¡Bienvenido/a a {st.session_state.nombre_taller}!")
                                st.rerun()
                            else:
                                st.error("Contraseña incorrecta.")
                        else:
                            st.error("El correo ingresado no está registrado.")
                    except Exception as e:
                        st.error(f"Error en el inicio de sesión: {e}")
                else:
                    st.warning("Por favor, completá todos los campos.")
                    
    # --- TAB REGISTRO DE CUENTA NUEVA ---
    with tab_registro:
        with st.container(border=True):
            st.markdown("### Registrar nuevo taller")
            reg_taller = st.text_input("Nombre de tu Emprendimiento/Taller", placeholder="Ej: Mi Taller Gráfico")
            reg_email = st.text_input("Correo Electrónico del Administrador", placeholder="admin@mitaller.com")
            reg_pass = st.text_input("Crear Contraseña", type="password", placeholder="Mínimo 6 caracteres")
            
            if st.button("Comenzar Prueba Gratis de 14 Días", type="primary", use_container_width=True):
                if reg_taller and reg_email and reg_pass:
                    try:
                        # 1. Verificar si el mail ya está en uso
                        res_check = supabase.table("usuarios").select("id").eq("email", reg_email).execute()
                        datos_check = extraer_datos_respuesta(res_check)
                        
                        if datos_check:
                            st.error("⚠️ Este correo electrónico ya está registrado.")
                        else:
                            # 2. Leer estructura real de la tabla de usuarios en Supabase para evitar PGRST204
                            res_sample = supabase.table("usuarios").select("*").limit(1).execute()
                            datos_sample = extraer_datos_respuesta(res_sample)
                            
                            columnas_existentes = []
                            if datos_sample and len(datos_sample) > 0:
                                columnas_existentes = list(datos_sample[0].keys())
                            
                            # 3. Buscar nombre de columna de contraseña compatible
                            col_pass_detectada = "password"
                            for k in ["password", "contraseña", "contrasena", "clave", "pass"]:
                                if k in columnas_existentes:
                                    col_pass_detectada = k
                                    break
                            
                            # 4. Construir registro agregando SOLO columnas físicamente presentes en la DB
                            nuevo_admin = {
                                "email": reg_email,
                                col_pass_detectada: reg_pass,
                                "rol": "Admin"
                            }
                            
                            # Guardamos la fecha de expiración únicamente si la columna existe en tu Supabase
                            if "trial_expires_at" in columnas_existentes:
                                fecha_expiracion = (datetime.now() + timedelta(days=14)).isoformat()
                                nuevo_admin["trial_expires_at"] = fecha_expiracion
                                mensaje_vto = f" Tu prueba vence el {(datetime.now() + timedelta(days=14)).strftime('%d/%m/%Y')}."
                            else:
                                mensaje_vto = " (Acceso ilimitado activado)."
                            
                            # Guardamos el taller según la columna que tengas disponible
                            if "nombre_taller" in columnas_existentes:
                                nuevo_admin["nombre_taller"] = reg_taller
                            elif "taller" in columnas_existentes:
                                nuevo_admin["taller"] = reg_taller
                            
                            # 5. Guardar en Supabase
                            supabase.table("usuarios").insert(nuevo_admin).execute()
                            st.success(f"🎉 ¡Cuenta de {reg_taller} creada con éxito! Ya podés iniciar sesión en la pestaña izquierda.{mensaje_vto}")
                    except Exception as e:
                        st.error(f"Error al registrar la cuenta: {e}")
                else:
                    st.warning("Por favor, completá todos los campos para el registro.")

# ==========================================
# 📊 PÁGINA PRINCIPAL (SISTEMA AUTENTICADO)
# ==========================================
else:
    # ID del dueño de los datos actuales (para aislar por completo cada cuenta)
    id_propietario_datos = st.session_state.get("owner_id")

    # --- CARGAR DATOS DESDE SUPABASE AISLADOS DESDE LA CONSULTA DE FORMA SEGURA ---
    @st.cache_data(ttl=3)
    def cargar_datos_seguro(owner_id_filtro):
        try:
            # 1. Analizar si las columnas de aislamiento existen en la base de datos de Supabase de forma dinámica
            col_owner_historial_existe = False
            try:
                res_check_hist = supabase.table("historial").select("*").limit(1).execute()
                datos_check_hist = extraer_datos_respuesta(res_check_hist)
                if datos_check_hist and len(datos_check_hist) > 0:
                    col_owner_historial_existe = "owner_id" in datos_check_hist[0].keys()
            except Exception:
                col_owner_historial_existe = False

            col_owner_stock_existe = False
            try:
                res_check_stock = supabase.table("stock").select("*").limit(1).execute()
                datos_check_stock = extraer_datos_respuesta(res_check_stock)
                if datos_check_stock and len(datos_check_stock) > 0:
                    col_owner_stock_existe = "owner_id" in datos_check_stock[0].keys()
            except Exception:
                col_owner_stock_existe = False

            # 2. Cargar historial con control de errores si no existe la columna
            if col_owner_historial_existe and owner_id_filtro is not None:
                res_historial = supabase.table("historial").select("*").eq("owner_id", owner_id_filtro).order("fecha", desc=True).execute()
            else:
                res_historial = supabase.table("historial").select("*").order("fecha", desc=True).execute()
                
                datos_historial = extraer_datos_respuesta(res_historial)
            df_hist_tmp = pd.DataFrame(datos_historial) if datos_historial else pd.DataFrame()
            
            if not df_hist_tmp.empty:
                df_hist_tmp["fecha"] = pd.to_datetime(df_hist_tmp["fecha"])
                df_hist_tmp["monto"] = df_hist_tmp["monto"].astype(float)
                
            # 3. Cargar stock con control de errores
            if col_owner_stock_existe and owner_id_filtro is not None:
                res_stock = supabase.table("stock").select("*").eq("owner_id", owner_id_filtro).execute()
            else:
                res_stock = supabase.table("stock").select("*").execute()
                
            datos_stock = extraer_datos_respuesta(res_stock)
            df_stock_tmp = pd.DataFrame(datos_stock) if datos_stock else pd.DataFrame()
            
            if not df_stock_tmp.empty:
                df_stock_tmp["cantidad"] = df_stock_tmp["cantidad"].astype(float) if "cantidad" in df_stock_tmp.columns else 0.0
                df_stock_tmp["minimo"] = df_stock_tmp["minimo"].astype(float) if "minimo" in df_stock_tmp.columns else 0.0
                
                col_precio = None
                for c in ["precio_costo", "precio", "costo", "valor_costo"]:
                    if c in df_stock_tmp.columns:
                        col_precio = c
                        break
                if col_precio:
                    df_stock_tmp["precio_costo"] = df_stock_tmp[col_precio].astype(float)
                else:
                    df_stock_tmp["precio_costo"] = 0.0
                
            return df_hist_tmp, df_stock_tmp
        except Exception as e:
            st.error(f"Error cargando base de datos: {e}")
            return pd.DataFrame(), pd.DataFrame()

    df_historial, df_stock = cargar_datos_seguro(id_propietario_datos)

    # --- DETECCIÓN DINÁMICA DE LA COLUMNA DETALLE/DESCRIPCIÓN ---
    col_desc_detectada = "descripcion"
    if not df_historial.empty:
        for c in ["descripción", "descripcion", "detalle", "concepto"]:
            if c in df_historial.columns:
                col_desc_detectada = c
                break

    # --- CÁLCULO DE CAJAS ---
    caja_negocio = 0.0
    billetera_personal = 0.0

    if not df_historial.empty:
        ingresos = df_historial[(df_historial["tipo"] == "Ingreso")]["monto"].sum()
        gastos_negocio = df_historial[(df_historial["tipo"] == "Gasto Negocio")]["monto"].sum()
        retiros_personales = df_historial[(df_historial["tipo"] == "Retiro Sueldo")]["monto"].sum()
        gastos_personales = df_historial[(df_historial["tipo"] == "Gasto Personal")]["monto"].sum()
        
        caja_negocio = ingresos - gastos_negocio - retiros_personales
        billetera_personal = retiros_personales - gastos_personales

    rol_actual = st.session_state.get("rol", "Empleado")

    # --- MENÚ LATERAL ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3061/3061341.png", width=80)
        st.title(st.session_state.nombre_taller)
        st.caption(f"Sesión: **{st.session_state.usuario_email}** ({rol_actual})")
        
        st.markdown("---")
        
        if rol_actual == "Admin":
            secciones = [
                "📊 Dashboard General",
                "🤖 Consultor IA",
                "📝 Nueva Operación",
                "🧮 Calculadora de Costos",
                "📉 Punto de Equilibrio",
                "📦 Stock de Insumos",
                "🎯 Metas de Ahorro",
                "👥 Personal del Taller"
            ]
        else:
            secciones = [
                "📝 Nueva Operación",
                "📦 Stock de Insumos"
            ]
            
        seccion = st.radio("Ir a:", secciones)
        
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.usuario_email = ""
            st.session_state.usuario_id = None
            st.session_state.owner_id = None
            st.rerun()

    # ==========================================
    # 📊 DASHBOARD GENERAL
    # ==========================================
    if seccion == "📊 Dashboard General" and rol_actual == "Admin":
        st.title(f"📊 Control de Mando - {st.session_state.nombre_taller}")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.metric(label="💼 FONDOS DISPONIBLES EMPRENDIMIENTO", value=f"$ {caja_negocio:,.2f}")
            st.caption("Capital total activo en la caja operativa de tu taller.")
        with col_c2:
            st.metric(label="👤 FINANZAS PERSONALES (RETIRO LIBRE)", value=f"$ {billetera_personal:,.2f}")
            st.caption("Dinero extraído neto disponible para tus gastos personales cotidianos.")
            
        # --- DISTRIBUCIÓN INTERNA RECOMENDADA ---
        st.markdown("---")
        st.markdown("### 💡 Distribución Interna Recomendada")
        
        caja_insumos_calc = caja_negocio * 0.35
        caja_sueldos_calc = caja_negocio * 0.55
        caja_mantenimiento_calc = caja_negocio * 0.10
        
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.metric(label="📦 CAJA INSUMOS (35%)", value=f"$ {caja_insumos_calc:,.2f}")
        with col_p2:
            st.metric(label="💸 CAJA SUELDOS (55%)", value=f"$ {caja_sueldos_calc:,.2f}")
        with col_p3:
            st.metric(label="🔧 MANTENIMIENTO (10%)", value=f"$ {caja_mantenimiento_calc:,.2f}")
            
        st.markdown("---")
        
        if not df_historial.empty:
            col_exp1, col_exp2 = st.columns([1, 1])
            with col_exp1:
                st.markdown("### 📥 Exportar Historial Completo")
                df_exportar = df_historial.copy()
                df_exportar["fecha"] = df_exportar["fecha"].dt.strftime('%Y-%m-%d %H:%M:%S')
                csv_data = df_exportar.to_csv(index=False, encoding="utf-8-sig")
                
                st.download_button(
                    label="📥 Descargar Planilla de Movimientos (Excel/CSV)",
                    data=csv_data,
                    file_name=f"movimientos_{st.session_state.nombre_taller}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
            with col_exp2:
                st.markdown("### 📅 Seleccionar Período")
                df_historial["periodo"] = df_historial["fecha"].dt.strftime('%Y-%m')
                periodos_disponibles = sorted(df_historial["periodo"].unique(), reverse=True)
                periodo_seleccionado = st.selectbox("Mes de Análisis:", periodos_disponibles)
                
                df_filtrado_mes = df_historial[df_historial["periodo"] == periodo_seleccionado]
            
            st.markdown("---")
            st.subheader(f"📊 Balance Financiero Mensual ({periodo_seleccionado})")
            
            ingresos_mes = df_filtrado_mes[df_filtrado_mes["tipo"] == "Ingreso"]["monto"].sum()
            egresos_mes = df_filtrado_mes[df_filtrado_mes["tipo"].isin(["Gasto Negocio", "Retiro Sueldo", "Gasto Personal"])]["monto"].sum()
            
            df_chart = pd.DataFrame({
                "Categoría": ["Gastos / Egresos", "Ventas / Ingresos"],
                "Monto ($)": [egresos_mes, ingresos_mes]
            })
            st.bar_chart(data=df_chart, x="Categoría", y="Monto ($)", color="#ff4b4b", use_container_width=True)
            
            st.markdown("---")
            st.subheader("📋 Lista Detallada de Movimientos")
            
            for idx, row in df_filtrado_mes.iterrows():
                color_card = "#2ecc71" if row["tipo"] == "Ingreso" else "#e74c3c"
                simbolo = "➕" if row["tipo"] == "Ingreso" else "➖"
                
                with st.container(border=True):
                    col_t1, col_t2, col_t3 = st.columns([5, 3, 1])
                    
                    with col_t1:
                        st.markdown(f"**{simbolo} {row['tipo']}** - {row[col_desc_detectada]}")
                        st.caption(f"📅 Fecha: {row['fecha'].strftime('%Y-%m-%d %H:%M:%S')}")
                    with col_t2:
                        st.markdown(f"<h3 style='margin:0; color:{color_card};'>$ {row['monto']:,.2f}</h3>", unsafe_allow_html=True)
                    with col_t3:
                        if st.button("🗑️", key=f"del_h_{row['id']}"):
                            try:
                                supabase.table("historial").delete().eq("id", int(row["id"])).execute()
                                st.success("¡Movimiento eliminado!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al borrar: {e}")
        else:
            st.info("No hay transacciones registradas.")

    # ==========================================
    # 🤖 CONSULTOR IA
    # ==========================================
    elif seccion == "🤖 Consultor IA" and rol_actual == "Admin":
        st.title("🤖 Consultor Financiero IA Inteligente")
        st.markdown("Análisis automático de tus números para optimizar tu taller gráfico.")
        
        items_criticos_lista = []
        if not df_stock.empty:
            criticos_df = df_stock[df_stock["cantidad"] <= df_stock["minimo"]]
            if not criticos_df.empty:
                items_criticos_lista = criticos_df["item"].tolist()
                
        items_criticos_txt = ", ".join(items_criticos_lista) if items_criticos_lista else "Ninguno (Stock Ok)"

        with st.container(border=True):
            st.subheader("📊 Resumen de Datos Enviados")
            st.write(f"🏢 **Taller Activo:** {st.session_state.nombre_taller}")
            st.write(f"🛠️ **Fondos en Caja:** $ {caja_negocio:,.2f}")
            st.write(f"👤 **Caja Personal:** $ {billetera_personal:,.2f}")

        if st.button("🚀 Generar Diagnóstico con IA", type="primary", use_container_width=True):
            with st.spinner("🤖 Analizando base de datos..."):
                historial_texto = df_historial.tail(15).to_string() if not df_historial.empty else "Sin movimientos"
                resumen_data = f"Taller: {st.session_state.nombre_taller}\nCaja Negocio: ${caja_negocio:.2f}\nCaja Personal: ${billetera_personal:.2f}\nHistorial:\n{historial_texto}"
                
                prompt_expert = f"Actuá como asesor financiero para un taller gráfico en Argentina. Analizá: {resumen_data}. Brindá un diagnóstico corto, directo, en español rioplatense, con 3 tips de rentabilidad clave."
                
                respuesta_ia = consultar_gemini_directo(prompt_expert)
                st.markdown("<br><hr>", unsafe_allow_html=True)
                st.markdown(respuesta_ia)

    # ==========================================
    # 📝 NUEVA OPERACIÓN
    # ==========================================
    elif seccion == "📝 Nueva Operación":
        st.title("📝 Registrar Nueva Operación")
        
        if rol_actual == "Admin":
            opciones = [
                "Registrar Venta / Presupuesto", 
                "Registrar Gasto Negocio", 
                "Retirar Sueldo", 
                "Registrar Gasto Personal"
            ]
        else:
            opciones = [
                "Registrar Venta / Presupuesto", 
                "Registrar Gasto Negocio"
            ]
            
        tipo_op = st.selectbox("Tipo de Movimiento", opciones)
        
        if "datos_ultimo_envio" not in st.session_state:
            st.session_state.datos_ultimo_envio = None

        with st.form("form_nueva_operacion", clear_on_submit=False):
            col_o1, col_o2 = st.columns(2)
            monto_op = col_o1.number_input("Monto ($)", min_value=1.0, step=100.0)
            desc_op = col_o2.text_input("Detalle / Concepto (Ej: Venta de Remera, Vinilos)")
            
            if st.form_submit_button("💾 Guardar Operación", use_container_width=True):
                if desc_op:
                    tipo_db = "Ingreso"
                    if "Gasto Negocio" in tipo_op:
                        tipo_db = "Gasto Negocio"
                    elif "Retirar Sueldo" in tipo_op:
                        tipo_db = "Retiro Sueldo"
                    elif "Gasto Personal" in tipo_op:
                        tipo_db = "Gasto Personal"
                    
                    try:
                        res_sample_hist = supabase.table("historial").select("*").limit(1).execute()
                        datos_sample_hist = extraer_datos_respuesta(res_sample_hist)
                        
                        columnas_existentes_hist = []
                        if datos_sample_hist and len(datos_sample_hist) > 0:
                            columnas_existentes_hist = list(datos_sample_hist[0].keys())
                        
                        col_destino_desc = "descripcion"
                        for c in ["descripción", "descripcion", "detalle", "concepto"]:
                            if c in columnas_existentes_hist:
                                col_destino_desc = c
                                break
                        
                        fila_insertar = {
                            "fecha": datetime.now().isoformat(),
                            "tipo": tipo_db,
                            "monto": monto_op
                        }
                        fila_insertar[col_destino_desc] = desc_op
                        
                        if "owner_id" in columnas_existentes_hist and id_propietario_datos is not None:
                            fila_insertar["owner_id"] = int(id_propietario_datos)
                        
                        supabase.table("historial").insert(fila_insertar).execute()
                        st.success("¡Operación registrada con éxito!")
                        
                        if tipo_db == "Ingreso":
                            st.session_state.datos_ultimo_envio = {
                                "detalle": desc_op,
                                "monto": monto_op
                            }
                        else:
                            st.session_state.datos_ultimo_envio = None

                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                else:
                    st.warning("Por favor, ingresá una descripción.")

        if st.session_state.datos_ultimo_envio:
            st.markdown("---")
            st.subheader("📲 ¡Venta registrada! Generar ticket para enviar por WhatsApp")
            
            with st.container(border=True):
                tel_cliente = st.text_input("Número de WhatsApp del Cliente", placeholder="Ej: 5493412345678")
                
                t_detalle = st.session_state.datos_ultimo_envio["detalle"]
                t_monto = st.session_state.datos_ultimo_envio["monto"]
                
                texto_whatsapp = (
                    f"¡Hola! Te pasamos el comprobante de tu compra en *{st.session_state.nombre_taller}* 🛍️\n\n"
                    f"📌 *Detalle:* {t_detalle}\n"
                    f"💰 *Monto Abonado:* $ {t_monto:,.2f}\n\n"
                    f"¡Muchas gracias por elegirnos! Cualquier duda estamos a disposición. 🚀"
                )
                
                st.text_area("Texto a enviar:", value=texto_whatsapp, height=140)
                
                if tel_cliente:
                    texto_url = requests.utils.quote(texto_whatsapp)
                    enlace_wp = f"https://wa.me/{tel_cliente}?text={texto_url}"
                    
                    st.markdown(
                        f'<a href="{enlace_wp}" target="_blank">'
                        f'<button style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold;">'
                        f'🟢 Enviar Comprobante por WhatsApp'
                        f'</button></a>',
                        unsafe_allow_html=True
                    )

    # ==========================================
    # 🧮 CALCULADORA DE COSTOS
    # ==========================================
    elif seccion == "🧮 Calculadora de Costos" and rol_actual == "Admin":
        st.title("🧮 Calculadora de Costos Gráficos")
        
        vista_cliente = st.toggle("Modo Vista Cliente (Ocultar Costos y Ganancias)", value=False)
        
        with st.container(border=True):
            col_e1, col_e2 = st.columns(2)
            producto = col_e1.text_input("Nombre del Trabajo", value="Trabajo Personalizado")
            costo_fijo = col_e2.number_input("Costos de Insumos ($)", min_value=0.0, step=100.0)
            
            col_e3, col_e4 = st.columns(2)
            horas_diseno = col_e3.number_input("Horas de Trabajo", min_value=0.0, step=0.1)
            valor_hora = col_e4.number_input("Valor Hora ($)", min_value=0.0, value=2500.0, step=100.0)
            
            porcentaje_ganancia = st.slider("Margen de Ganancia (%)", min_value=10, max_value=200, value=50, step=5)
            
            mano_obra = horas_diseno * valor_hora
            costo_total = costo_fijo + mano_obra
            precio_sugerido = costo_total * (1 + (porcentaje_ganancia / 100))
            ganancia_neta = precio_sugerido - costo_total
            
            st.markdown("---")
            if vista_cliente:
                st.metric("💰 PRECIO PRESUPUESTADO sugerido", f"$ {precio_sugerido:,.2f}")
            else:
                col_r1, col_r2 = st.columns(2)
                col_r1.metric("💰 PRECIO RECOMENDADO", f"$ {precio_sugerido:,.2f}")
                col_r2.metric("📈 GANANCIA ESTIMADA", f"$ {ganancia_neta:,.2f}")
            
            st.markdown("---")
            texto_presupuesto = (
                f"¡Hola! Te paso el presupuesto detallado para tu trabajo: *{producto}*\n\n"
                f"📌 *Detalle:* Servicio de diseño y producción personalizada.\n"
                f"💰 *Valor Total:* $ {precio_sugerido:,.2f}\n\n"
                f"¡Cualquier duda me avisás y lo coordinamos! Muchas gracias por confiar en *{st.session_state.nombre_taller}* 🚀"
            )
            st.text_area("Presupuesto para copiar:", value=texto_presupuesto, height=150)

    # ==========================================
    # 📉 PUNTO DE EQUILIBRIO
    # ==========================================
    elif seccion == "📉 Punto de Equilibrio" and rol_actual == "Admin":
        st.title("📉 Punto de Equilibrio - Olivia Imagen")
        st.markdown("Conocé con precisión cuánto tenés que facturar para cubrir tus costos fijos y variables mensuales.")
        
        with st.container(border=True):
            st.subheader("⚙️ Parámetros de Simulación Financiera")
            col_eq1, col_eq2 = st.columns(2)
            costos_fijos_fijos = col_eq1.number_input("Costos Fijos del Mes ($)", min_value=0.0, value=150000.0, step=5000.0)
            margen_contribucion = col_eq2.slider("Margen de Ganancia Promedio sobre Insumos (%)", min_value=10, max_value=200, value=50, step=5)
            
            porcentaje_margen = (margen_contribucion / (100 + margen_contribucion))
            punto_equilibrio_pesos = costos_fijos_fijos / porcentaje_margen if porcentaje_margen > 0 else 0.0
            
            st.markdown("---")
            col_eqr1, col_eqr2 = st.columns(2)
            col_eqr1.metric("🏁 FACTURACIÓN MÍNIMA REQUERIDA", f"$ {punto_equilibrio_pesos:,.2f}")
            col_eqr2.metric("📊 Margen de Contribución Real", f"{porcentaje_margen * 100:.1f} %")

    # ==========================================
    # 📦 STOCK DE INSUMOS (FORMULARIO RESTAURADO)
    # ==========================================
    elif seccion == "📦 Stock de Insumos":
        st.title("📦 Inventario de Insumos Críticos")
        
        if df_stock.empty:
            st.info("No hay insumos en el inventario.")
        else:
            df_stock["Alerta"] = df_stock.apply(
                lambda r: "🔴 Reponer Ya" if r["cantidad"] <= r["minimo"] else "🟢 OK", axis=1
            )
            
            columnas_mostrar = ["item", "cantidad", "minimo"]
            if "precio_costo" in df_stock.columns:
                columnas_mostrar.append("precio_costo")
            columnas_mostrar.append("Alerta")
            
            st.dataframe(df_stock[columnas_mostrar], use_container_width=True)
            
            if rol_actual == "Admin":
                st.markdown("---")
                tab_ajustar, tab_crear_categoria = st.tabs(["✏️ Ajustar Cantidades", "🆕 Crear Nuevo Insumo / Categoría"])
                
                with tab_ajustar:
                    with st.form("form_ajuste_stock"):
                        col_s1, col_s2 = st.columns(2)
                        item_seleccionado = col_s1.selectbox("Insumo a modificar", df_stock["item"].tolist())
                        nueva_cantidad = col_s2.number_input("Nueva Cantidad en Stock (Entero)", min_value=0, step=1, value=0)
                        
                        if st.form_submit_button("⚙️ Actualizar Stock"):
                            try:
                                supabase.table("stock").update({"cantidad": int(nueva_cantidad)}).eq("item", item_seleccionado).execute()
                                st.success(f"¡Stock de {item_seleccionado} actualizado a {int(nueva_cantidad)}!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al modificar el stock: {e}")
                                
                with tab_crear_categoria:
                    with st.form("form_crear_insumo"):
                        st.subheader("Registrar Insumo Nuevo en la Base")
                        col_crea1, col_crea2 = st.columns(2)
                        nuevo_nombre_item = col_crea1.text_input("Nombre del Insumo / Categoría (Ej: Vinilo Holográfico)")
                        precio_costo_nuevo = col_crea2.number_input("Precio de Costo Inicial ($)", min_value=0.0, step=100.0)
                        
                        col_crea3, col_crea4 = st.columns(2)
                        cantidad_inicial_nueva = col_crea3.number_input("Stock Inicial", min_value=0, step=1)
                        minimo_alerta_nuevo = col_crea4.number_input("Punto de Reorden Mínimo", min_value=0, step=1, value=5)
                        
                        # Botón de envío que procesa el formulario restaurado
                        if st.form_submit_button("💾 Guardar Insumo Nuevo", use_container_width=True):
                            if nuevo_nombre_item:
                                try:
                                    res_sample_st = supabase.table("stock").select("*").limit(1).execute()
                                    datos_sample_st = extraer_datos_respuesta(res_sample_st)
                                    
                                    columnas_existentes_st = []
                                    if datos_sample_st and len(datos_sample_st) > 0:
                                        columnas_existentes_st = list(datos_sample_st[0].keys())
                                        
                                    col_precio_db = "precio_costo"
                                    for c in ["precio_costo", "precio", "costo", "valor_costo"]:
                                        if c in columnas_existentes_st:
                                            col_precio_db = c
                                            break
                                    
                                    nuevo_registro = {
                                        "item": nuevo_nombre_item,
                                        "cantidad": int(cantidad_inicial_nueva),
                                        "minimo": int(minimo_alerta_nuevo),
                                        col_precio_db: float(precio_costo_nuevo)
                                    }
                                    
                                    if "owner_id" in columnas_existentes_st and id_propietario_datos is not None:
                                        nuevo_registro["owner_id"] = int(id_propietario_datos)
                                    
                                    supabase.table("stock").insert(nuevo_registro).execute()
                                    st.success(f"¡Insumo '{nuevo_nombre_item}' cargado con éxito en Supabase!")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al registrar insumo: {e}")
                            else:
                                st.warning("Por favor, ingresá un nombre para el nuevo insumo.")

    # ==========================================
    # 🎯 METAS DE AHORRO
    # ==========================================
    elif seccion == "🎯 Metas de Ahorro" and rol_actual == "Admin":
        st.title("🎯 Metas de Ahorro y Alcancías")
        
        try:
            col_owner_metas_existe = False
            try:
                res_check_metas = supabase.table("metas").select("*").limit(1).execute()
                datos_check_metas = extraer_datos_respuesta(res_check_metas)
                if datos_check_metas and len(datos_check_metas) > 0:
                    col_owner_metas_existe = "owner_id" in datos_check_metas[0].keys()
            except Exception:
                col_owner_metas_existe = False

            if col_owner_metas_existe and id_propietario_datos is not None:
                respuesta_metas = supabase.table("metas").select("*").eq("owner_id", id_propietario_datos).execute()
            else:
                respuesta_metas = supabase.table("metas").select("*").execute()
                
            datos_metas = extraer_datos_respuesta(respuesta_metas)
            df_metas = pd.DataFrame(datos_metas) if datos_metas else pd.DataFrame()
        except Exception as e:
            st.error(f"Error con la tabla metas: {e}")
            df_metas = pd.DataFrame()
        
        with st.container(border=True):
            st.subheader("🆕 Crear Nueva Alcancía")
            with st.form("form_nueva_meta", clear_on_submit=True):
                col_f1, col_f2 = st.columns(2)
                nueva_meta_nombre = col_f1.text_input("¿Para qué estás ahorrando?")
                objetivo_monto = col_f2.number_input("Monto Objetivo ($)", min_value=1.0, step=1000.0)
                
                if st.form_submit_button("🚀 Crear Alcancía", use_container_width=True):
                    if nueva_meta_nombre:
                        try:
                            res_sample_metas = supabase.table("metas").select("*").limit(1).execute()
                            datos_sample_metas = extraer_datos_respuesta(res_sample_metas)
                            
                            columnas_existentes_metas = []
                            if datos_sample_metas and len(datos_sample_metas) > 0:
                                columnas_existentes_metas = list(datos_sample_metas[0].keys())
                                
                            nueva_fila_meta = {
                                "meta": nueva_meta_nombre,
                                "acumulado": 0.0
                            }
                            
                            if "objetivo" in columnas_existentes_metas:
                                nueva_fila_meta["objetivo"] = objetivo_monto
                            elif "objective" in columnas_existentes_metas:
                                nueva_fila_meta["objective"] = objetivo_monto
                                
                            if "owner_id" in columnas_existentes_metas and id_propietario_datos is not None:
                                nueva_fila_meta["owner_id"] = int(id_propietario_datos)
                                
                            supabase.table("metas").insert(nueva_fila_meta).execute()
                            st.success(f"¡Alcancía '{nueva_meta_nombre}' creada!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar meta: {e}")
                    else:
                        st.warning("Escribí un nombre para tu meta.")

        st.markdown("---")
        
        if df_metas.empty:
            st.info("No hay alcancías creadas.")
        else:
            st.subheader("📌 Tus Alcancías")
            for idx, row in df_metas.iterrows():
                with st.container(border=True):
                    obj_col = 'objective' if 'objective' in row else 'objetivo'
                    obj = float(row[obj_col])
                    acum = float(row.get('acumulado', 0.0))
                    
                    porcentaje = (acum / obj) * 100 if obj > 0 else 0.0
                    col_m1, col_m2, col_m3 = st.columns([4, 3, 2])
                    
                    col_m1.markdown(f"🎯 **{row['meta']}**")
                    col_m1.progress(min(1.0, acum / obj) if obj > 0 else 0.0)
                    col_m1.caption(f"📈 Progreso: **{porcentaje:.1f}%**")
                    
                    col_m2.markdown(f"**Acumulado:** $ {acum:,.2f} / $ {obj:,.2f}")
                    
                    with col_m3:
                        monto_ahorrar = st.number_input(
                            "Sumar/Restar ($):", 
                            value=0.0, 
                            step=500.0, 
                            key=f"add_m_{row['id']}"
                        )
                        
                        col_btns = st.columns(2)
                        with col_btns[0]:
                            if st.button("💾", key=f"btn_save_m_{row['id']}"):
                                if monto_ahorrar != 0:
                                    nuevo_acumulado = acum + monto_ahorrar
                                    if nuevo_acumulado < 0:
                                        st.error("No podés retirar más de lo que tenés.")
                                    else:
                                        supabase.table("metas").update({"acumulado": nuevo_acumulado}).eq("id", int(row["id"])).execute()
                                        st.cache_data.clear()
                                        st.rerun()
                        with col_btns[1]:
                            if st.button("🗑️", key=f"del_meta_{row['id']}"):
                                supabase.table("metas").delete().eq("id", int(row["id"])).execute()
                                st.cache_data.clear()
                                st.rerun()

    # ==========================================
    # 👥 PERSONAL DEL TALLER
    # ==========================================
    elif seccion == "👥 Personal del Taller" and rol_actual == "Admin":
        st.title("👥 Panel de Control de Usuarios y Empleados")
        st.markdown("Crea, gestiona y da de baja a los miembros del equipo de tu taller.")
        
        try:
            admin_id_actual = st.session_state.get("usuario_id")
            res_usuarios_db = supabase.table("usuarios").select("*").eq("owner_id", admin_id_actual).execute()
            datos_usuarios_db = extraer_datos_respuesta(res_usuarios_db)
            df_usuarios_db = pd.DataFrame(datos_usuarios_db) if datos_usuarios_db else pd.DataFrame()
        except Exception as e:
            st.error(f"Error al leer la base de usuarios: {e}")
            df_usuarios_db = pd.DataFrame()
            
        with st.container(border=True):
            st.subheader("🆕 Crear Nuevo Empleado")
            with st.form("form_crear_usuario", clear_on_submit=True):
                col_u1, col_u2 = st.columns(2)
                nuevo_email_user = col_u1.text_input("Correo Electrónico (Login)", placeholder="empleado@olivia.com")
                nuevo_pass_user = col_u2.text_input("Contraseña de Acceso", type="password", placeholder="Contraseña")
                
                if st.form_submit_button("👥 Guardar Nuevo Miembro"):
                    if nuevo_email_user and nuevo_pass_user:
                        try:
                            res_sample = supabase.table("usuarios").select("*").limit(1).execute()
                            datos_sample = extraer_datos_respuesta(res_sample)
                            
                            columnas_existentes = []
                            if datos_sample and len(datos_sample) > 0:
                                columnas_existentes = list(datos_sample[0].keys())
                            
                            col_pass_detectada = "password"
                            for k in ["password", "contraseña", "contrasena", "clave", "pass"]:
                                if k in columnas_existentes:
                                    col_pass_detectada = k
                                    break
                            
                            nuevo_empleado = {
                                "email": nuevo_email_user,
                                col_pass_detectada: nuevo_pass_user,
                                "rol": "Empleado",
                                "owner_id": int(st.session_state.usuario_id)
                            }
                            
                            if "nombre_taller" in columnas_existentes:
                                nuevo_empleado["nombre_taller"] = st.session_state.nombre_taller
                            elif "taller" in columnas_existentes:
                                nuevo_empleado["taller"] = st.session_state.nombre_taller
                                        
                            supabase.table("usuarios").insert(nuevo_empleado).execute()
                            
                            st.success(f"¡Empleado '{nuevo_email_user}' registrado exitosamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al registrar: {e}")
                    else:
                        st.warning("Completá todos los campos.")
                        
        st.markdown("---")
        st.subheader("👥 Equipo Activo Registrado")
        
        if df_usuarios_db.empty:
            st.info("No tenés empleados registrados todavía en tu taller.")
        else:
            for idx, row in df_usuarios_db.iterrows():
                with st.container(border=True):
                    col_emp1, col_emp2, col_emp3 = st.columns([5, 3, 1])
                    with col_emp1:
                        st.markdown(f"📧 **{row['email']}**")
                        st.caption(f"Rol: {row.get('rol', 'Empleado')} | Registrado el: {pd.to_datetime(row.get('created_at')).strftime('%d/%m/%Y')}")
                    with col_emp2:
                        st.markdown(f"🏢 Taller: **{st.session_state.nombre_taller}**")
                    with col_emp3:
                        if st.button("🗑️", key=f"del_user_{row['id']}", help="Eliminar permanentemente a este empleado"):
                            try:
                                supabase.table("usuarios").delete().eq("id", int(row["id"])).execute()
                                st.success("¡Empleado eliminado de tu taller!")
                                st.rerun()
                            except Exception as e:
                                r_err = str(e)
                                st.error(f"No se pudo eliminar al empleado: {r_err}")
