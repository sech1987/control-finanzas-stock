import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import io
from PIL import Image

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Olivia Imagen - Gestión Financiera", page_icon="🛍️", layout="wide")

# --- CONTROL DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "nombre_taller" not in st.session_state:
    st.session_state.nombre_taller = "Olivia Imagen"
if "rol" not in st.session_state:
    st.session_state.rol = "Admin"
if "usuario_email" not in st.session_state:
    st.session_state.usuario_email = ""
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
if "owner_id" not in st.session_state:
    st.session_state.owner_id = None
if "logo_taller" not in st.session_state:
    st.session_state.logo_taller = None

# Inicializar lista dinámica de insumos para el presupuesto actual
if "insumos_presupuesto" not in st.session_state:
    st.session_state.insumos_presupuesto = []

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

# --- CONFIGURACIÓN DE IA ---
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
                            
                            clave_usuario = None
                            for k in ["password", "contraseña", "contrasena", "clave", "pass"]:
                                if k in user_data:
                                    clave_usuario = user_data[k]
                                    break
                            
                            if str(clave_usuario) == str(password_input):
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
                    
    with tab_registro:
        with st.container(border=True):
            st.markdown("### Registrar nuevo taller")
            reg_taller = st.text_input("Nombre de tu Emprendimiento/Taller", placeholder="Ej: Mi Taller Gráfico")
            reg_email = st.text_input("Correo Electrónico del Administrador", placeholder="admin@mitaller.com")
            reg_pass = st.text_input("Crear Contraseña", type="password", placeholder="Mínimo 6 caracteres")
            
            if st.button("Comenzar Prueba Gratis de 14 Días", type="primary", use_container_width=True):
                if reg_taller and reg_email and reg_pass:
                    try:
                        res_check = supabase.table("usuarios").select("id").eq("email", reg_email).execute()
                        datos_check = extraer_datos_respuesta(res_check)
                        
                        if datos_check:
                            st.error("⚠️ Este correo electrónico ya está registrado.")
                        else:
                            res_sample = supabase.table("usuarios").select("*").limit(1).execute()
                            datos_sample = extraer_datos_respuesta(res_sample)
                            
                            columnas_existentes = list(datos_sample[0].keys()) if datos_sample else []
                            
                            col_pass_detectada = "password"
                            for k in ["password", "contraseña", "contrasena", "clave", "pass"]:
                                if k in columnas_existentes:
                                    col_pass_detectada = k
                                    break
                            
                            nuevo_admin = {
                                "email": reg_email,
                                col_pass_detectada: reg_pass,
                                "rol": "Admin"
                            }
                            
                            if "trial_expires_at" in columnas_existentes:
                                nuevo_admin["trial_expires_at"] = (datetime.now() + timedelta(days=14)).isoformat()
                                mensaje_vto = f" Tu prueba vence el {(datetime.now() + timedelta(days=14)).strftime('%d/%m/%Y')}."
                            else:
                                mensaje_vto = " (Acceso ilimitado activado)."
                            
                            if "nombre_taller" in columnas_existentes:
                                nuevo_admin["nombre_taller"] = reg_taller
                            elif "taller" in columnas_existentes:
                                nuevo_admin["taller"] = reg_taller
                            
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
    id_propietario_datos = st.session_state.get("owner_id")

    @st.cache_data(ttl=3)
    def cargar_datos_seguro(owner_id_filtro):
        try:
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

            if col_owner_historial_existe and owner_id_filtro is not None:
                res_historial = supabase.table("historial").select("*").eq("owner_id", owner_id_filtro).order("fecha", desc=True).execute()
            else:
                res_historial = supabase.table("historial").select("*").order("fecha", desc=True).execute()
                
            datos_historial = extraer_datos_respuesta(res_historial)
            df_hist_tmp = pd.DataFrame(datos_historial) if datos_historial else pd.DataFrame()
            
            if not df_hist_tmp.empty:
                df_hist_tmp["fecha"] = pd.to_datetime(df_hist_tmp["fecha"])
                df_hist_tmp["monto"] = df_hist_tmp["monto"].astype(float)
                
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

    col_desc_detectada = "descripcion"
    if not df_historial.empty:
        for c in ["descripción", "descripcion", "detalle", "concepto"]:
            if c in df_historial.columns:
                col_desc_detectada = c
                break

    # Balance de cajas
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
        # --- LOGO DINÁMICO ---
        if st.session_state.logo_taller is not None:
            st.image(st.session_state.logo_taller, width=100)
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
            
        st.title(st.session_state.nombre_taller)
        st.caption(f"Sesión: **{st.session_state.usuario_email}** ({rol_actual})")
        
        # --- CONFIGURACIÓN DE LOGO OCULTA EN EXPANDER ---
        with st.expander("⚙️ Configurar Logo"):
            archivo_logo = st.file_uploader("Subir imagen (PNG/JPG)", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
            if archivo_logo is not None:
                try:
                    img_logo = Image.open(archivo_logo)
                    img_logo = img_logo.resize((300, 300))
                    st.session_state.logo_taller = img_logo
                    st.rerun()
                except Exception:
                    pass

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
            secciones = ["📝 Nueva Operación", "📦 Stock de Insumos"]
            
        seccion = st.radio("Ir a:", secciones)
        
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.usuario_email = ""
            st.session_state.usuario_id = None
            st.session_state.owner_id = None
            st.session_state.logo_taller = None
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
            
        st.markdown("---")
        st.markdown("### 💡 Distribución Interna Recomendada")
        caja_insumos_calc = caja_negocio * 0.35
        caja_sueldos_calc = caja_negocio * 0.55
        caja_mantenimiento_calc = caja_negocio * 0.10
        
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1: st.metric(label="📦 CAJA INSUMOS (35%)", value=f"$ {caja_insumos_calc:,.2f}")
        with col_p2: st.metric(label="💸 CAJA SUELDOS (55%)", value=f"$ {caja_sueldos_calc:,.2f}")
        with col_p3: st.metric(label="🔧 MANTENIMIENTO (10%)", value=f"$ {caja_mantenimiento_calc:,.2f}")
            
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
            
            df_chart = pd.DataFrame({"Categoría": ["Gastos / Egresos", "Ventas / Ingresos"], "Monto ($)": [egresos_mes, ingresos_mes]})
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
                            except Exception as e: st.error(f"Error al borrar: {e}")
        else: st.info("No hay transacciones registradas.")

    # ==========================================
    # 🤖 CONSULTOR IA
    # ==========================================
    elif seccion == "🤖 Consultor IA" and rol_actual == "Admin":
        st.title("🤖 Consultor Financiero IA Inteligente")
        with st.container(border=True):
            st.subheader("📊 Resumen de Datos Enviados")
            st.write(f"🏢 **Taller Activo:** {st.session_state.nombre_taller}")
            st.write(f"🛠️ **Fondos en Caja:** $ {caja_negocio:,.2f}")
            st.write(f"👤 **Caja Personal:** $ {billetera_personal:,.2f}")
        if st.button("🚀 Generar Diagnóstico con IA", type="primary", use_container_width=True):
            with st.spinner("🤖 Analizando..."):
                historial_texto = df_historial.tail(15).to_string() if not df_historial.empty else "Sin movimientos"
                resumen_data = f"Taller: {st.session_state.nombre_taller}\nCaja Negocio: ${caja_negocio:.2f}\nCaja Personal: ${billetera_personal:.2f}\nHistorial:\n{historial_texto}"
                prompt_expert = f"Actuá como asesor financiero para un taller gráfico en Argentina. Analizá: {resumen_data}. Brindá un diagnóstico corto, directo, en español rioplatense, con 3 tips de rentabilidad clave."
                st.markdown("<br><hr>", unsafe_allow_html=True)
                st.markdown(consultar_gemini_directo(prompt_expert))

    # ==========================================
    # 📝 NUEVA OPERACIÓN
    # ==========================================
    elif seccion == "📝 Nueva Operación":
        st.title("📝 Registrar Nueva Operación")
        opciones = ["Registrar Venta / Presupuesto", "Registrar Gasto Negocio", "Retirar Sueldo", "Registrar Gasto Personal"] if rol_actual == "Admin" else ["Registrar Venta / Presupuesto", "Registrar Gasto Negocio"]
        tipo_op = st.selectbox("Tipo de Movimiento", opciones)
        
        if "datos_ultimo_envio" not in st.session_state: st.session_state.datos_ultimo_envio = None

        with st.form("form_nueva_operacion"):
            col_o1, col_o2 = st.columns(2)
            monto_op = col_o1.number_input("Monto ($)", min_value=1.0, step=100.0)
            desc_op = col_o2.text_input("Detalle / Concepto")
            if st.form_submit_button("💾 Guardar Operación", use_container_width=True):
                if desc_op:
                    tipo_db = "Ingreso" if "Venta" in tipo_op else ("Gasto Negocio" if "Gasto Negocio" in tipo_op else ("Retiro Sueldo" if "Retirar" in tipo_op else "Gasto Personal"))
                    try:
                        res_sample_hist = supabase.table("historial").select("*").limit(1).execute()
                        columnas_existentes_hist = list(extraer_datos_respuesta(res_sample_hist)[0].keys()) if extraer_datos_respuesta(res_sample_hist) else []
                        col_destino_desc = "descripcion"
                        for c in ["descripcion", "detalle", "concepto"]:
                            if c in columnas_existentes_hist: col_destino_desc = c; break
                        
                        fila_insertar = {"fecha": datetime.now().isoformat(), "tipo": tipo_db, "monto": monto_op, col_destino_desc: desc_op}
                        if "owner_id" in columnas_existentes_hist and id_propietario_datos is not None: fila_insertar["owner_id"] = int(id_propietario_datos)
                        
                        supabase.table("historial").insert(fila_insertar).execute()
                        st.success("¡Operación registrada!")
                        st.session_state.datos_ultimo_envio = {"detalle": desc_op, "monto": monto_op} if tipo_db == "Ingreso" else None
                        st.cache_data.clear()
                    except Exception as e: st.error(f"Error: {e}")
                else: st.warning("Ingresá una descripción.")

        if st.session_state.datos_ultimo_envio:
            st.markdown("---")
            with st.container(border=True):
                tel_cliente = st.text_input("WhatsApp del Cliente", placeholder="549...")
                texto_whatsapp = f"¡Hola! Te pasamos el comprobante de tu compra en *{st.session_state.nombre_taller}* 🛍️\n\n📌 *Detalle:* {st.session_state.datos_ultimo_envio['detalle']}\n💰 *Monto:* $ {st.session_state.datos_ultimo_envio['monto']:,.2f}\n\n¡Gracias por elegirnos! 🚀"
                st.text_area("Texto:", value=texto_whatsapp, height=120)
                if tel_cliente:
                    st.markdown(f'<a href="https://wa.me/{tel_cliente}?text={requests.utils.quote(texto_whatsapp)}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 10px; border-radius: 5px; width: 100%; font-weight: bold;">🟢 Enviar por WhatsApp</button></a>', unsafe_allow_html=True)

    # ==========================================
    # 🧮 CALCULADORA DE COSTOS (CONECTADA AL STOCK)
    # ==========================================
    elif seccion == "🧮 Calculadora de Costos" and rol_actual == "Admin":
        st.title("🧮 Calculadora de Costos Inteligente")
        vista_cliente = st.toggle("Modo Vista Cliente (Ocultar Costos y Ganancias)", value=False)
        col_calc_izq, col_calc_der = st.columns([1, 1])
        
        with col_calc_izq:
            st.subheader("📦 Insumos del Trabajo")
            if df_stock.empty: st.info("No hay materiales en stock.")
            else:
                lista_items = df_stock["item"].tolist()
                col_sel_ins, col_sel_cant = st.columns([3, 1])
                item_a_presupuestar = col_sel_ins.selectbox("Insumo:", lista_items)
                cant_a_presupuestar = col_sel_cant.number_input("Cant:", min_value=0.01, value=1.0)
                
                if st.button("➕ Agregar Insumo", use_container_width=True):
                    datos_material = df_stock[df_stock["item"] == item_a_presupuestar].iloc[0]
                    costo_unitario = float(datos_material.get("precio_costo", 0.0))
                    st.session_state.insumos_presupuesto.append({"item": item_a_presupuestar, "cantidad": cant_a_presupuestar, "costo_unit": costo_unitario, "subtotal": cant_a_presupuestar * costo_unitario})
                    st.rerun()
            
            if st.session_state.insumos_presupuesto:
                df_insumos_calc = pd.DataFrame(st.session_state.insumos_presupuesto)
                for idx_ins, item_row in df_insumos_calc.iterrows():
                    with st.container(border=True):
                        col_rname, col_rsub, col_rbtn = st.columns([5, 3, 1])
                        col_rname.markdown(f"**{item_row['item']}** (x{item_row['cantidad']:.2f})")
                        col_rsub.markdown(f"$ {item_row['subtotal']:,.2f}")
                        if col_rbtn.button("🗑️", key=f"del_ins_calc_{idx_ins}"): st.session_state.insumos_presupuesto.pop(idx_ins); st.rerun()
                total_acumulado_insumos = df_insumos_calc["subtotal"].sum()
                st.metric("Total Materiales", f"$ {total_acumulado_insumos:,.2f}")
                if st.button("🧹 Limpiar todo", use_container_width=True): st.session_state.insumos_presupuesto = []; st.rerun()
            else: total_acumulado_insumos = 0.0
                
        with col_calc_der:
            st.subheader("💰 Cálculo de Precio Final")
            with st.container(border=True):
                producto = st.text_input("Trabajo", value="Trabajo Personalizado")
                costo_fijo = st.number_input("Costos Insumos ($)", min_value=0.0, value=total_acumulado_insumos)
                col_e3, col_e4 = st.columns(2)
                horas_diseno = col_e3.number_input("Horas", min_value=0.0)
                valor_hora = col_e4.number_input("Valor Hora ($)", value=2500.0)
                porcentaje_ganancia = st.slider("Ganancia (%)", 10, 200, 50)
                
                costo_total = costo_fijo + (horas_diseno * valor_hora)
                precio_sugerido = costo_total * (1 + (porcentaje_ganancia / 100))
                
                if vista_cliente: st.metric("💰 PRECIO SUGERIDO", f"$ {precio_sugerido:,.2f}")
                else:
                    col_r1, col_r2 = st.columns(2)
                    col_r1.metric("💰 PRECIO RECOMENDADO", f"$ {precio_sugerido:,.2f}")
                    col_r2.metric("📈 GANANCIA ESTIMADA", f"$ {(precio_sugerido - costo_total):,.2f}")
                
                texto_presupuesto = f"¡Hola! Presupuesto para: *{producto}*\n💰 *Valor Total:* $ {precio_sugerido:,.2f}\n¡Gracias por confiar en *{st.session_state.nombre_taller}*! 🚀"
                st.text_area("Copia rápida:", value=texto_presupuesto, height=100)

    # ==========================================
    # 📉 PUNTO DE EQUILIBRIO
    # ==========================================
    elif seccion == "📉 Punto de Equilibrio" and rol_actual == "Admin":
        st.title("📉 Punto de Equilibrio")
        with st.container(border=True):
            col_eq1, col_eq2 = st.columns(2)
            costos_fijos_fijos = col_eq1.number_input("Costos Fijos Mensuales ($)", value=150000.0)
            margen_contribucion = col_eq2.slider("Margen Ganancia Promedio (%)", 10, 200, 50)
            porcentaje_margen = (margen_contribucion / (100 + margen_contribucion))
            pe_pesos = costos_fijos_fijos / porcentaje_margen if porcentaje_margen > 0 else 0.0
            st.columns(2)[0].metric("🏁 FACTURACIÓN MÍNIMA REQUERIDA", f"$ {pe_pesos:,.2f}")

    # ==========================================
    # 📦 STOCK DE INSUMOS (CON FUNCIÓN DE BORRADO)
    # ==========================================
    elif seccion == "📦 Stock de Insumos":
        st.title("📦 Inventario de Insumos Críticos")
        if df_stock.empty: st.info("💡 Aún no tenés ningún insumo registrado.")
        else:
            df_stock["Alerta"] = df_stock.apply(lambda r: "🔴 Reponer Ya" if r["cantidad"] <= r["minimo"] else "🟢 OK", axis=1)
            columnas_mostrar = ["item", "cantidad", "minimo"]
            if "precio_costo" in df_stock.columns: columnas_mostrar.append("precio_costo")
            columnas_mostrar.append("Alerta")
            st.dataframe(df_stock[columnas_mostrar], use_container_width=True)
            
        if rol_actual == "Admin":
            st.markdown("---")
            if not df_stock.empty: tab_ajustar, tab_crear_categoria = st.tabs(["✏️ Ajustar Cantidades / Costos", "🆕 Crear Nuevo Insumo"])
            else: tab_crear_categoria, = st.tabs(["🆕 Crear Nuevo Insumo"]); tab_ajustar = None
            
            if tab_ajustar is not None:
                with tab_ajustar:
                    with st.form("form_ajuste_stock"):
                        st.subheader("Modificar / Eliminar Existencias")
                        col_s1, col_s2 = st.columns(2)
                        item_seleccionado = col_s1.selectbox("Insumo a modificar", df_stock["item"].tolist())
                        datos_item_actual = df_stock[df_stock["item"] == item_seleccionado].iloc[0]
                        
                        nueva_cantidad = col_s2.number_input("Nueva Cantidad", value=int(datos_item_actual.get("cantidad", 0)))
                        col_s3, col_s4 = st.columns(2)
                        nuevo_costo_item = col_s3.number_input("Precio Costo ($)", value=float(datos_item_actual.get("precio_costo", 0.0)))
                        punto_minimo_editar = col_s4.number_input("Mínimo Alerta", value=int(datos_item_actual.get("minimo", 5)))
                        
                        btn_col1, btn_col2 = st.columns([4, 1])
                        guardar_cambios = btn_col1.form_submit_button("💾 Guardar Cambios en Insumo", use_container_width=True, type="primary")
                        eliminar_item = btn_col2.form_submit_button("🗑️ Eliminar", use_container_width=True)
                        
                        # Lógica unificada de acciones
                        if guardar_cambios:
                            try:
                                res_st = supabase.table("stock").select("*").limit(1).execute()
                                col_p_db = "precio_costo"
                                for c in ["precio_costo", "precio", "costo"]:
                                    if c in list(extraer_datos_respuesta(res_st)[0].keys()): col_p_db = c; break
                                supabase.table("stock").update({"cantidad": int(nueva_cantidad), "minimo": int(punto_minimo_editar), col_p_db: float(nuevo_costo_item)}).eq("item", item_seleccionado).execute()
                                st.success("¡Insumo actualizado!")
                                st.cache_data.clear(); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")
                            
                        if eliminar_item:
                            try:
                                supabase.table("stock").delete().eq("item", item_seleccionado).execute()
                                st.success(f"¡Insumo '{item_seleccionado}' eliminado definitivamente!")
                                st.cache_data.clear(); st.rerun()
                            except Exception as e: st.error(f"Error al eliminar: {e}")
                                
            with tab_crear_categoria:
                with st.form("form_crear_insumo", clear_on_submit=True):
                    st.subheader("Registrar Insumo Nuevo")
                    col_crea1, col_crea2 = st.columns(2)
                    nuevo_nombre_item = col_crea1.text_input("Nombre (Ej: Vinilo Holográfico)")
                    precio_costo_nuevo = col_crea2.number_input("Costo Inicial ($)")
                    col_crea3, col_crea4 = st.columns(2)
                    cantidad_inicial_nueva = col_crea3.number_input("Stock Inicial", step=1)
                    minimo_alerta_nuevo = col_crea4.number_input("Mínimo Reorden", value=5, step=1)
                    
                    if st.form_submit_button("💾 Guardar Insumo Nuevo", use_container_width=True, type="primary"):
                        if nuevo_nombre_item:
                            try:
                                res_dup = supabase.table("stock").select("*").eq("item", nuevo_nombre_item).execute()
                                datos_dup = extraer_datos_respuesta(res_dup)
                                duplicado = any(str(d.get("owner_id")) == str(id_propietario_datos) for d in datos_dup)
                                
                                if duplicado: st.warning("⚠️ Este insumo ya existe en tu catálogo.")
                                else:
                                    res_st = supabase.table("stock").select("*").limit(1).execute()
                                    cols_st = list(extraer_datos_respuesta(res_st)[0].keys()) if extraer_datos_respuesta(res_st) else []
                                    col_p_db = "precio_costo"
                                    for c in ["precio_costo", "precio", "costo"]:
                                        if c in cols_st: col_p_db = c; break
                                    
                                    nuevo_reg = {"item": nuevo_nombre_item, "cantidad": int(cantidad_inicial_nueva), "minimo": int(minimo_alerta_nuevo), col_p_db: float(precio_costo_nuevo)}
                                    if "owner_id" in cols_st and id_propietario_datos is not None: nuevo_reg["owner_id"] = int(id_propietario_datos)
                                    
                                    supabase.table("stock").insert(nuevo_reg).execute()
                                    st.success("¡Insumo cargado!")
                                    st.cache_data.clear(); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")

  # ==========================================
    # 🎯 METAS DE AHORRO (BLINDADO Y CORREGIDO)
    # ==========================================
    elif seccion == "🎯 Metas de Ahorro" and rol_actual == "Admin":
        st.title("🎯 Metas de Ahorro")
        
        # Cargar metas de forma segura filtrando por el dueño de casa
        try:
            res_metas = supabase.table("metas").select("*").execute()
            datos_metas_totales = extraer_datos_respuesta(res_metas)
            df_metas_tmp = pd.DataFrame(datos_metas_totales) if datos_metas_totales else pd.DataFrame()
            
            # Si la tabla tiene la columna owner_id, filtramos para este usuario para mantener el SaaS aislado
            if not df_metas_tmp.empty and "owner_id" in df_metas_tmp.columns and id_propietario_datos is not None:
                df_metas = df_metas_tmp[df_metas_tmp["owner_id"].astype(str) == str(id_propietario_datos)]
            else:
                df_metas = df_metas_tmp
        except Exception:
            df_metas = pd.DataFrame()
        
        with st.container(border=True):
            st.subheader("🆕 Crear Nueva Alcancía")
            with st.form("form_nueva_meta", clear_on_submit=True):
                col_f1, col_f2 = st.columns(2)
                nueva_meta_nombre = col_f1.text_input("¿Para qué estás ahorrando?")
                objetivo_monto = col_f2.number_input("Monto Objetivo ($):", min_value=1.0, step=1000.0)
                
                if st.form_submit_button("🚀 Crear Alcancía", use_container_width=True, type="primary"):
                    if nueva_meta_nombre:
                        try:
                            # 1. Analizar la estructura real de la tabla metas
                            res_sample_m = supabase.table("metas").select("*").limit(1).execute()
                            datos_sample_m = extraer_datos_respuesta(res_sample_m)
                            columnas_metas = list(datos_sample_m[0].keys()) if datos_sample_m else []
                            
                            # Detectar dinámicamente si se llama objetivo u objective
                            obj_col = "objetivo"
                            for c in ["objetivo", "objective", "monto_objetivo"]:
                                if c in columnas_metas:
                                    obj_col = c
                                    break
                            
                            # 2. Construir el registro básico
                            nueva_fila_meta = {
                                "meta": nueva_meta_nombre,
                                "acumulado": 0.0,
                                obj_col: float(objetivo_monto)
                            }
                            
                            # 3. Forzar el owner_id solo si la columna físicamente existe en tu base
                            if "owner_id" in columnas_metas and id_propietario_datos is not None:
                                nueva_fila_meta["owner_id"] = int(id_propietario_datos)
                            
                            # 4. Grabar en Supabase
                            supabase.table("metas").insert(nueva_fila_meta).execute()
                            st.success(f"¡Alcancía '{nueva_meta_nombre}' creada con éxito!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            # 5. Plan B de emergencia por si la tabla estaba 100% vacía y no pudo leer columnas
                            try:
                                fallback_meta = {"meta": nueva_meta_nombre, "acumulado": 0.0, "objetivo": float(objetivo_monto)}
                                if id_propietario_datos is not None: fallback_meta["owner_id"] = int(id_propietario_datos)
                                supabase.table("metas").insert(fallback_meta).execute()
                                st.success(f"¡Alcancía '{nueva_meta_nombre}' creada con éxito!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e2:
                                st.error(f"Error al guardar la alcancía: {e2}")
                    else:
                        st.warning("Por favor, escribí un nombre para tu meta.")

        st.markdown("---")
        
        # --- DIBUJAR LAS ALCANCÍAS EN PANTALLA ---
        if df_metas.empty:
            st.info("📌 Todavía no tenés ninguna alcancía creada. ¡Armá la primera arriba!")
        else:
            st.subheader("📌 Tus Alcancías Activas")
            for idx, row in df_metas.iterrows():
                with st.container(border=True):
                    # Detectar qué columna de objetivo usar para mostrarla bien
                    col_obj_ver = 'objective' if 'objective' in row else ('objetivo' if 'objetivo' in row else None)
                    obj = float(row[col_obj_ver]) if col_obj_ver and row[col_obj_ver] is not None else 1.0
                    acum = float(row.get('acumulado', 0.0))
                    
                    porcentaje = (acum / obj) * 100 if obj > 0 else 0.0
                    col_m1, col_m2, col_m3 = st.columns([4, 3, 2])
                    
                    col_m1.markdown(f"🎯 **{row['meta']}**")
                    col_m1.progress(min(1.0, max(0.0, acum / obj)))
                    col_m1.caption(f"📈 Progreso de ahorro: **{porcentaje:.1f}%**")
                    
                    col_m2.markdown(f"**Ahorrado:** $ {acum:,.2f} / $ {obj:,.2f}")
                    
                    with col_m3:
                        monto_ahorrar = st.number_input(
                            "Sumar/Restar fondos ($):", 
                            value=0.0, 
                            step=500.0, 
                            key=f"add_m_input_{row['id']}"
                        )
                        
                        col_btns = st.columns(2)
                        with col_btns[0]:
                            if st.button("💾", key=f"btn_save_m_meta_{row['id']}", help="Guardar monto"):
                                nuevo_acumulado = acum + monto_ahorrar
                                if nuevo_acumulado < 0:
                                    st.error("No podés retirar más de lo que tenés acumulado.")
                                else:
                                    supabase.table("metas").update({"acumulado": nuevo_acumulado}).eq("id", int(row["id"])).execute()
                                    st.cache_data.clear()
                                    st.rerun()
                        with col_btns[1]:
                            if st.button("🗑️", key=f"btn_del_m_meta_{row['id']}", help="Eliminar alcancía"):
                                supabase.table("metas").delete().eq("id", int(row["id"])).execute()
                                st.cache_data.clear()
                                st.rerun()
    # ==========================================
    # 👥 PERSONAL DEL TALLER
    # ==========================================
    elif seccion == "👥 Personal del Taller" and rol_actual == "Admin":
        st.title("👥 Personal del Taller")
        try:
            res_u = supabase.table("usuarios").select("*").eq("owner_id", st.session_state.get("usuario_id")).execute()
            df_usuarios_db = pd.DataFrame(extraer_datos_respuesta(res_u)) if extraer_datos_respuesta(res_u) else pd.DataFrame()
        except Exception: df_usuarios_db = pd.DataFrame()
            
        with st.container(border=True):
            with st.form("form_crear_usuario", clear_on_submit=True):
                col_u1, col_u2 = st.columns(2)
                n_email = col_u1.text_input("Email Empleado:")
                n_pass = col_u2.text_input("Contraseña:", type="password")
                if st.form_submit_button("👥 Guardar Nuevo Miembro"):
                    if n_email and n_pass:
                        try:
                            # Forzar lectura limpia de columnas existentes
                            res_s = supabase.table("usuarios").select("*").limit(1).execute()
                            datos_s = extraer_datos_respuesta(res_s)
                            cols_u = list(datos_s[0].keys()) if datos_s else []
                            
                            col_p_det = "contraseña"
                            for k in ["contraseña", "contrasena", "password", "clave", "pass"]:
                                if k in cols_u: 
                                    col_p_det = k
                                    break
                                    
                            emp = {"email": n_email, col_p_det: n_pass, "rol": "Empleado", "owner_id": int(st.session_state.usuario_id)}
                            if "nombre_taller" in cols_u: emp["nombre_taller"] = st.session_state.nombre_taller
                            elif "taller" in cols_u: emp["taller"] = st.session_state.nombre_taller
                            
                            supabase.table("usuarios").insert(emp).execute()
                            st.success("¡Miembro del equipo registrado!")
                            st.rerun()
                        except Exception as e: st.error(f"Error al registrar usuario: {e}")
