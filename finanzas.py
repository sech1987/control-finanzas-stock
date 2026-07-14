import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Olivia Imagen - Gestión Financiera", page_icon="🛍️", layout="wide")

# --- CONTROL DE SESIÓN (INICIALIZACIÓN ULTRA SEGURA ARRIBA DE TODO) ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "nombre_taller" not in st.session_state:
    st.session_state.nombre_taller = "Olivia Imagen"
if "rol" not in st.session_state:
    st.session_state.rol = "Empleado"
if "usuario_email" not in st.session_state:
    st.session_state.usuario_email = ""

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

# --- CONFIGURACIÓN DE IA (CONEXIÓN DIRECTA POR API) ---
def consultar_gemini_directo(prompt_texto):
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY", "")
        if not api_key:
            return "⚠️ No se detectó la clave de Google en los secretos de Streamlit."
            
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt_texto}]}]}
        
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        data = response.json()
        
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"]
            
        # PLAN B AUTOMÁTICO EN CASO DE ERROR
        url_pro = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-latest:generateContent?key={api_key}"
        response_pro = requests.post(url_pro, headers=headers, json=payload, timeout=20)
        data_pro = response_pro.json()
        
        if "candidates" in data_pro and len(data_pro["candidates"]) > 0:
            return data_pro["candidates"][0]["content"]["parts"][0]["text"]
        elif "error" in data_pro:
            return f"⚠️ Nota del servidor: {data_pro['error'].get('message', 'Sin saldo o cuota excedida')}"
            
        return "⚠️ El servidor no devolvió respuesta. Verificá si tenés saldo disponible en Google Studio."
    except Exception as e:
        return f"⚠️ Error de conexión con el módulo de IA. (Detalle: {e})"

# --- CARGAR DATOS DESDE SUPABASE ---
@st.cache_data(ttl=5)
def cargar_datos():
    try:
        # Traer Historial de operaciones
        res_historial = supabase.table("historial").select("*").order("fecha", desc=True).execute()
        df_historial = pd.DataFrame(res_historial.data) if res_historial.data else pd.DataFrame()
        if not df_historial.empty:
            df_historial["fecha"] = pd.to_datetime(df_historial["fecha"])
            df_historial["monto"] = df_historial["monto"].astype(float)
            
        # Traer Stock
        res_stock = supabase.table("stock").select("*").execute()
        df_stock = pd.DataFrame(res_stock.data) if res_stock.data else pd.DataFrame()
        if not df_stock.empty:
            df_stock["cantidad"] = df_stock["cantidad"].astype(float)
            df_stock["minimo"] = df_stock["minimo"].astype(float)
            df_stock["precio_costo"] = df_stock["precio_costo"].astype(float)
            
        return df_historial, df_stock
    except Exception as e:
        st.error(f"Error cargando tablas base: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_historial, df_stock = cargar_datos()

# --- CÁLCULO DE CAJAS ---
caja_negocio = 0.0
billetera_personal = 0.0

if not df_historial.empty:
    # Ingresos y Gastos del Negocio
    ingresos = df_historial[(df_historial["tipo"] == "Ingreso")]["monto"].sum()
    gastos_negocio = df_historial[(df_historial["tipo"] == "Gasto Negocio")]["monto"].sum()
    
    # Retiros y Gastos Personales
    retiros_personales = df_historial[(df_historial["tipo"] == "Retiro Sueldo")]["monto"].sum()
    gastos_personales = df_historial[(df_historial["tipo"] == "Gasto Personal")]["monto"].sum()
    
    # Saldos
    caja_negocio = ingresos - gastos_negocio - retiros_personales
    billetera_personal = retiros_personales - gastos_personales

# ==========================================
# 🔐 PANTALLA DE INICIO DE SESIÓN (LOGIN)
# ==========================================
if not st.session_state.get("autenticado", False):
    st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>💼 Finanzas & Stock Manager Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Ingresá tus credenciales para acceder al sistema de gestión de Olivia Imagen</p>", unsafe_allow_html=True)
    
    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "✨ Crear Cuenta (Prueba Gratis)"])
    
    with tab_login:
        with st.container(border=True):
            email_input = st.text_input("Correo Electrónico", placeholder="ejemplo@olivia.com", key="login_email")
            password_input = st.text_input("Contraseña", type="password", placeholder="••••••••", key="login_pass")
            
            if st.button("Ingresar al Panel", type="primary", use_container_width=True):
                if email_input and password_input:
                    try:
                        # Buscamos las credenciales del usuario en Supabase
                        res_user = supabase.table("usuarios").select("*").eq("email", email_input).execute()
                        
                        if res_user.data:
                            user_data = res_user.data[0]
                            # Verificación simple de contraseña
                            if user_data["password"] == password_input:
                                st.session_state.autenticado = True
                                st.session_state.usuario_email = user_data["email"]
                                st.session_state.rol = user_data.get("rol", "Empleado")
                                st.session_state.nombre_taller = user_data.get("taller", "Olivia Imagen")
                                st.success(f"¡Bienvenido/a a {st.session_state.nombre_taller}!")
                                st.rerun()
                            else:
                                st.error("Contraseña incorrecta. Por favor, verificá los datos.")
                        else:
                            st.error("El correo ingresado no está registrado.")
                    except Exception as e:
                        st.error(f"Error en el inicio de sesión: {e}")
                else:
                    st.warning("Por favor, completá todos los campos.")
                    
    with tab_registro:
        with st.container(border=True):
            reg_taller = st.text_input("Nombre de tu Emprendimiento", value="Olivia Imagen")
            reg_email = st.text_input("Correo Electrónico de Registro", placeholder="ejemplo@olivia.com")
            reg_pass = st.text_input("Contraseña Nueva", type="password", placeholder="Mínimo 6 caracteres")
            reg_rol = st.selectbox("Rol por Defecto", ["Admin", "Empleado"])
            
            if st.button("Crear Cuenta e Instalar Base", use_container_width=True):
                if reg_taller and reg_email and reg_pass:
                    try:
                        # Guardamos el nuevo usuario en Supabase
                        supabase.table("usuarios").insert({
                            "email": reg_email,
                            "password": reg_pass,
                            "rol": reg_rol,
                            "taller": reg_taller
                        }).execute()
                        st.success("¡Cuenta creada con éxito! Ahora podés iniciar sesión en la pestaña de al lado.")
                    except Exception as e:
                        st.error(f"Error al registrar la cuenta: {e}")
                else:
                    st.warning("Por favor, completa todos los campos del formulario.")

# ==========================================
# 📊 PÁGINA PRINCIPAL (SISTEMA AUTENTICADO)
# ==========================================
else:
    rol_actual = st.session_state.get("rol", "Empleado")

    # --- MENÚ LATERAL ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3061/3061341.png", width=80)
        st.title(st.session_state.nombre_taller)
        st.caption(f"Sesión: **{st.session_state.usuario_email}** ({rol_actual})")
        
        st.markdown("---")
        
        # Secciones dinámicas según el Rol del usuario autenticado
        if rol_actual == "Admin":
            secciones = [
                "📊 Dashboard General",
                "🤖 Consultor IA",
                "📝 Nueva Operación",
                "🧮 Calculadora de Costos",
                "📦 Stock de Insumos",
                "🎯 Metas de Ahorro"
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
            st.rerun()

    # ==========================================
    # 📊 DASHBOARD GENERAL (SÓLO ADMIN)
    # ==========================================
    if seccion == "📊 Dashboard General" and rol_actual == "Admin":
        st.title("📊 Control de Mando - Olivia Imagen")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.metric(label="💼 Caja del Negocio", value=f"$ {caja_negocio:,.2f}")
        with col_c2:
            st.metric(label="👤 Billetera Personal (Tus Retiros)", value=f"$ {billetera_personal:,.2f}")
            
        st.markdown("---")
        st.subheader("📈 Últimos Movimientos Generales")
        if df_historial.empty:
            st.info("No hay transacciones registradas.")
        else:
            st.dataframe(
                df_historial[["fecha", "tipo", "descripcion", "monto"]].head(10),
                use_container_width=True
            )

    # ==========================================
    # 🤖 CONSULTOR IA (SÓLO ADMIN)
    # ==========================================
    elif seccion == "🤖 Consultor IA" and rol_actual == "Admin":
        st.title("🤖 Consultor Financiero IA Inteligente")
        st.markdown("Dejá que la Inteligencia Artificial analice tus números para encontrar áreas de optimización y fugas de dinero.")
        
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
                
                respuesta_ia = consultar_gemini_directo(prompt_expert)
                st.markdown("<br><hr>", unsafe_allow_html=True)
                st.markdown(respuesta_ia)

    # ==========================================
    # 📝 NUEVA OPERACIÓN (FILTRADO POR ROL)
    # ==========================================
    elif seccion == "📝 Nueva Operación":
        st.title("📝 Registrar Nueva Operación")
        
        # FILTRO SEGURO DE OPCIONES POR ROL
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
        
        with st.form("form_nueva_operacion", clear_on_submit=True):
            col_o1, col_o2 = st.columns(2)
            monto_op = col_o1.number_input("Monto ($)", min_value=1.0, step=100.0)
            desc_op = col_o2.text_input("Detalle / Concepto (Ej: Venta de Vinilos, Compra de hojas)")
            
            if st.form_submit_button("💾 Guardar Operación", use_container_width=True):
                if desc_op:
                    # Mapeamos la selección de interfaz al formato de base de datos
                    tipo_db = "Ingreso"
                    if "Gasto Negocio" in tipo_op:
                        tipo_db = "Gasto Negocio"
                    elif "Retirar Sueldo" in tipo_op:
                        tipo_db = "Retiro Sueldo"
                    elif "Gasto Personal" in tipo_op:
                        tipo_db = "Gasto Personal"
                    
                    try:
                        supabase.table("historial").insert({
                            "fecha": datetime.now().isoformat(),
                            "tipo": tipo_db,
                            "descripcion": desc_op,
                            "monto": monto_op
                        }).execute()
                        st.success("¡Operación registrada con éxito!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar en base de datos: {e}")
                else:
                    st.warning("Por favor, poné un concepto o descripción para el registro.")

    # ==========================================
    # 🧮 CALCULADORA DE COSTOS (SÓLO ADMIN)
    # ==========================================
    elif seccion == "🧮 Calculadora de Costos" and rol_actual == "Admin":
        st.title("🧮 Calculadora de Costos Gráficos")
        
        with st.container(border=True):
            col_e1, col_e2 = st.columns(2)
            producto = col_e1.text_input("Nombre del Trabajo (Ej: Remera estampada)", value="Trabajo Personalizado")
            costo_fijo = col_e2.number_input("Costos de Insumos ($)", min_value=0.0, step=100.0)
            
            col_e3, col_e4 = st.columns(2)
            horas_diseno = col_e3.number_input("Horas de Trabajo Estimadas", min_value=0.0, step=0.5)
            valor_hora = col_e4.number_input("Valor de tu Hora de Trabajo ($)", min_value=0.0, value=2500.0, step=500.0)
            
            porcentaje_ganancia = st.slider("Margen de Ganancia Deseado (%)", min_value=10, max_value=200, value=50, step=5)
            
            # Cálculos de la cotización
            mano_obra = horas_diseno * valor_hora
            costo_total = costo_fijo + mano_obra
            precio_sugerido = costo_total * (1 + (porcentaje_ganancia / 100))
            ganancia_neta = precio_sugerido - costo_total
            
            st.markdown("---")
            col_r1, col_r2 = st.columns(2)
            col_r1.metric("💰 PRECIO RECOMENDADO", f"$ {precio_sugerido:,.2f}")
            col_r2.metric("📈 GANANCIA ESTIMADA", f"$ {ganancia_neta:,.2f}")
            
            # --- 📝 PLANTILLA DE PRESUPUESTO PARA EL CLIENTE (BLINDADA) ---
            st.markdown("---")
            st.subheader("📝 Presupuesto Listo para Enviar")
            st.markdown("Copiá este texto y mandaselo directo a tu cliente por WhatsApp o mensaje:")
            
            # Armamos el texto de forma limpia y profesional
            texto_presupuesto = (
                f"¡Hola! Te paso el presupuesto detallado para tu trabajo: *{producto}*\n\n"
                f"📌 *Detalle:* Servicio de diseño y producción personalizada.\n"
                f"💰 *Valor Total:* $ {precio_sugerido:,.2f}\n\n"
                f"⚠️ *Condiciones:* Válido por 5 días debido a la reposición de insumos. "
                f"Se inicia el trabajo con una seña del 50%.\n\n"
                f"¡Cualquier duda me avisás y lo coordinamos! Muchas gracias por confiar en *{st.session_state.nombre_taller}* 🚀"
            )
            
            # Lo mostramos en un cuadro de texto especial que permite copiar con un solo clic
            st.text_area("Presupuesto para copiar:", value=texto_presupuesto, height=180, key="txt_presupuesto_cliente")

    # ==========================================
    # 📦 STOCK DE INSUMOS
    # ==========================================
    elif seccion == "📦 Stock de Insumos":
        st.title("📦 Inventario de Insumos Críticos")
        
        if df_stock.empty:
            st.info("No hay insumos cargados en stock.")
        else:
            # Semáforo de alerta
            df_stock["Alerta"] = df_stock.apply(
                lambda r: "🔴 Reponer Ya" if r["cantidad"] <= r["minimo"] else "🟢 OK", axis=1
            )
            st.dataframe(
                df_stock[["item", "cantidad", "minimo", "precio_costo", "Alerta"]],
                use_container_width=True
            )
            
            # Formulario de modificación rápida (Solo administradores)
            if rol_actual == "Admin":
                st.markdown("---")
                st.subheader("✏️ Ajustar Stock")
                with st.form("form_ajuste_stock"):
                    col_s1, col_s2 = st.columns(2)
                    item_seleccionado = col_s1.selectbox("Insumo a modificar", df_stock["item"].tolist())
                    nueva_cantidad = col_s2.number_input("Nueva Cantidad en Stock", min_value=0.0, step=1.0)
                    
                    if st.form_submit_button("⚙️ Actualizar Stock"):
                        try:
                            supabase.table("stock").update({"cantidad": nueva_cantidad}).eq("item", item_seleccionado).execute()
                            st.success(f"¡Stock de {item_seleccionado} actualizado a {nueva_cantidad}!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al modificar el stock: {e}")

    # ==========================================
    # 🎯 METAS DE AHORRO (SÓLO ADMIN)
    # ==========================================
    elif seccion == "🎯 Metas de Ahorro" and rol_actual == "Admin":
        st.title("🎯 Metas de Ahorro y Alcancías")
        st.markdown("Definí objetivos claros para equipamiento, insumos grandes o fondos de emergencia.")
        
        # 🔍 LEEMOS LAS METAS DIRECTAMENTE DE SUPABASE EN TIEMPO REAL
        try:
            respuesta_metas = supabase.table("metas").select("*").execute()
            df_metas = pd.DataFrame(respuesta_metas.data) if respuesta_metas.data else pd.DataFrame()
        except Exception as e:
            st.error(f"Error al conectar con la base de datos de metas: {e}")
            df_metas = pd.DataFrame()
        
        # --- FORMULARIO PARA CREAR NUEVA META (CORREGIDO Y SEGURO) ---
        with st.container(border=True):
            st.subheader("🆕 Crear Nueva Alcancía")
            with st.form("form_nueva_meta", clear_on_submit=True):
                col_f1, col_f2 = st.columns(2)
                nueva_meta_nombre = col_f1.text_input("¿Para qué estás ahorrando? (Ej: Guillotina nueva)", placeholder="Nombre de la meta")
                objetivo_monto = col_f2.number_input("Monto Objetivo ($)", min_value=1.0, step=1000.0)
                
                if st.form_submit_button("🚀 Crear Alcancía", use_container_width=True):
                    if nueva_meta_nombre:
                        try:
                            # Insertamos sin el campo 'taller' que no existe en tu base de datos
                            supabase.table("metas").insert({
                                "meta": nueva_meta_nombre,
                                "objetivo": objetivo_monto,
                                "acumulado": 0.0
                            }).execute()
                            st.success(f"¡Alcancía '{nueva_meta_nombre}' creada con éxito!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar la meta: {e}")
                    else:
                        st.warning("Por favor, ingresá un nombre para tu meta de ahorro.")

        st.markdown("---")
        
        # --- LISTA DE ALCANCÍAS EXISTENTES ---
        if df_metas.empty:
            st.info("No tenés metas de ahorro creadas todavía.")
        else:
            st.subheader("📌 Tus Alcancías")
            for idx, row in df_metas.iterrows():
                with st.container(border=True):
                    obj = float(row['objetivo'])
                    acum = float(row.get('acumulado', 0.0))
                    
                    # Calculamos el porcentaje real de ahorro
                    porcentaje = (acum / obj) * 100 if obj > 0 else 0.0
                    
                    # Diseño en columnas ordenadas
                    col_m1, col_m2, col_m3 = st.columns([4, 3, 2])
                    
                    col_m1.markdown(f"🎯 **{row['meta']}**")
                    col_m1.progress(min(1.0, acum / obj) if obj > 0 else 0.0)
                    col_m1.caption(f"📈 Progreso: **{porcentaje:.1f}%** completado")
                    
                    col_m2.markdown(f"💰 **$ {acum:,.2f}** / $ {obj:,.2f}")
                    
                    # Formulario para meter o sacar plata en la alcancía
                    with col_m3:
                        monto_ahorrar = st.number_input(
                            "Sumar/Restar ($):", 
                            value=0.0, 
                            step=500.0, 
                            key=f"add_m_{row['id']}"
                        )
                        
                        if st.button("💾", key=f"btn_save_m_{row['id']}", help="Guardar movimiento"):
                            if monto_ahorrar != 0:
                                nuevo_acumulado = acum + monto_ahorrar
                                
                                # Evitamos saldo negativo por seguridad
                                if nuevo_acumulado < 0:
                                    st.error("⚠️ No podés retirar más plata de la que tenés ahorrada.")
                                else:
                                    supabase.table("metas").update({"acumulado": nuevo_acumulado}).eq("id", int(row["id"])).execute()
                                    if monto_ahorrar > 0:
                                        st.success(f"¡Sumaste $ {monto_ahorrar:,.2f}!")
                                    else:
                                        st.warning(f"¡Retiraste $ {abs(monto_ahorrar):,.2f} por urgencia!")
                                    st.cache_data.clear()
                                    st.rerun()
                        
                        # Botón de eliminar
                        if st.button("🗑️", key=f"del_meta_{row['id']}"):
                            supabase.table("metas").delete().eq("id", int(row["id"])).execute()
                            st.cache_data.clear()
                            st.rerun()
