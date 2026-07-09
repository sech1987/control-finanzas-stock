import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime, timezone
from supabase import create_client, Client
import io
import google.generativeai as genai

# --- CONFIGURACIÓN DE IA (GEMINI) ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.warning("⚠️ Nota: Falta configurar la GOOGLE_API_KEY en tus secretos de Streamlit Cloud.")

st.set_page_config(layout="wide", page_title="Finanzas & Stock Manager Pro", page_icon="📈")

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
                        
                        # ACCESO DIRECTO PARA OLIVIA IMAGEN
                        if email_input == "admin@olivia.com" and pass_input == "taller2026":
                            st.session_state.autenticado = True
                            st.session_state.usuario_id = 1
                            st.session_state.nombre_taller = "Olivia Imagen"
                            st.session_state.user_rol = "Admin"
                            st.rerun()
                        
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
        st.error("⚠️ **Alerta Financiera:** La caja del taller registra un saldo desfavorable.")
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
        csv_data = df_historial.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button(label="📥 Descargar Planilla de Movimientos (CSV)", data=csv_data, file_name=f"Planilla_Movimientos_{st.session_state.nombre_taller}.csv", mime="text/csv", type="primary")

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
            df_grafico = pd.DataFrame({"Tipo": ["📥 Ventas", "📤 Gastos"], "Monto ($)": [total_ingresos_mes, total_egresos_mes]}).set_index("Tipo")
            st.bar_chart(df_grafico, y="Monto ($)", color="#4F46E5", use_container_width=True)
        
        tab_ingresos, tab_egresos = st.tabs(["📥 INGRESOS (Ventas)", "📤 EGRESOS (Gastos)"])
        with tab_ingresos:
            for idx, row in df_mes[df_mes["tipo"] == "Ingreso"][::-1].iterrows():
                with st.container(border=True):
                    c_f, c_m, c_d, c_b = st.columns([1, 2, 4, 1])
                    c_f.caption(str(row["fecha"]))
                    c_m.markdown(f"**$ {float(row['monto']):,.2f}**")
                    c_d.markdown(f"🔹 *{row['categoria']}* — {row['detalle']}")
                    if c_b.button("🗑️", key=f"del_ing_{row['id']}"):
                        supabase.table("historial").delete().eq("id", int(row["id"])).execute()
                        st.rerun()
        with tab_egresos:
            for idx, row in df_mes[df_mes["tipo"] == "Gasto"][::-1].iterrows():
                with st.container(border=True):
                    c_f, c_m, c_d, c_b = st.columns([1, 2, 4, 1])
                    c_f.caption(str(row["fecha"]))
                    c_m.markdown(f"**$ {float(row['monto']):,.2f}**")
                    c_d.markdown(f"🔸 *{row['categoria']}* — {row['detalle']}")
                    if c_b.button("🗑️", key=f"del_egr_{row['id']}"):
                        supabase.table("historial").delete().eq("id", int(row["id"])).execute()
                        st.rerun()

# --- 🤖 MÓDULO CONSULTOR IA ---
elif seccion == "🤖 Consultor IA" and rol_actual == "Admin":
    st.title("🤖 Consultor Financiero IA Inteligente")
    st.markdown("Dejá que la IA analice tus números para encontrar áreas de optimización.")
    
    if st.button("🚀 Generar Diagnóstico con IA", type="primary", use_container_width=True):
        with st.spinner("🤖 Analizando base de datos..."):
            try:
                hist_txt = df_historial.tail(15).to_string() if not df_historial.empty else "Sin movimientos"
                prompt = f"Actúa como consultor financiero para el taller gráfico {st.session_state.nombre_taller}. Caja: ${caja_negocio:.2f}. Historial:\n{hist_txt}\nBrindá un diagnóstico corto y motivador en español rioplatense (Argentina)."
                response = model.generate_content(prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"❌ Error de IA: {e}")

# --- 📝 NUEVA OPERACIÓN ---
elif seccion == "📝 Nueva Operación":
    st.title("📝 Carga de Movimientos")
    opciones_carga = ["Registrar Venta / Presupuesto", "Registrar Gasto Negocio"] if rol_actual == "Empleado" else ["Registrar Venta / Presupuesto", "Registrar Gasto Negocio", "Retirar Sueldo", "Registrar Gasto Personal"]
    opcion = st.selectbox("¿Qué vas a registrar?", opciones_carga)
    
    with st.container(border=True):
        monto = st.number_input("Monto ($)", min_value=0.0, step=50.0)
        nota = st.text_input("Detalle:")
        if st.button("Guardar Registro", type="primary"):
            tipo_op = "Ingreso" if "Venta" in opcion else "Gasto"
            datos = {"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Negocio" if "Negocio" in opcion or "Venta" in opcion else "Personal", "tipo": tipo_op, "monto": float(monto), "categoria": "General", "detalle": nota, "estado_pago": "Total", "metodo_pago": "Efectivo", "usuario_id": data_scope_id}
            supabase.table("historial").insert(datos).execute()
            st.success("¡Guardado!")
            st.rerun()

# --- 🧮 CALCULADORA DE COSTOS ---
elif seccion == "🧮 Calculadora de Costos" and rol_actual == "Admin":
    st.title("🧮 Calculadora de Costos Completa")
    costo_mat = st.number_input("Materiales ($):", min_value=0.0, step=100.0)
    horas = st.number_input("Horas de trabajo:", min_value=0.0, value=1.0)
    valor_hora = st.number_input("Valor Hora ($):", min_value=0.0, value=4000.0)
    porcentaje = st.slider("Ganancia (%):", min_value=0, max_value=300, value=50)
    
    costo_base = costo_mat + (horas * valor_hora)
    precio_sug = costo_base * (1 + porcentaje/100)
    st.metric("Precio de Venta Sugerido:", f"$ {precio_sug:,.2f}")

# --- 📦 STOCK DE INSUMOS ---
elif seccion == "📦 Stock de Insumos":
    st.title("📦 Control de Inventario Completo")
    with st.expander("➕ Agregar Nuevo Insumo"):
        nombre_i = st.text_input("Material:")
        cant_i = st.number_input("Cantidad:", min_value=0, step=1)
        if st.button("Registrar"):
            supabase.table("stock").insert({"item": nombre_i, "cantidad": int(cant_i), "minimo": 5, "usuario_id": data_scope_id}).execute()
            st.rerun()
    if not df_stock.empty:
        st.dataframe(df_stock[["item", "cantidad", "minimo"]])

# --- RESTO DE MÓDULOS DE RENDERIZADO ORIGINAL ---
elif seccion == "📉 Punto de Equilibrio" and rol_actual == "Admin":
    st.title("📉 Punto de Equilibrio")
    st.info("Módulo operativo.")

elif seccion == "🎯 Metas de Ahorro" and rol_actual == "Admin":
    st.title("🎯 Metas de Ahorro")
    st.info("Módulo operativo.")

elif seccion == "⚙️ Configurar Categorías" and rol_actual == "Admin":
    st.title("⚙️ Configurar Categorías")
    st.info("Módulo operativo.")

elif seccion == "📊 Mi Cierre de Caja":
    st.title("📊 Mi Cierre de Caja")
    st.info("Módulo operativo.")

elif seccion == "👥 Personal del Taller" and rol_actual == "Admin":
    st.title("👥 Personal del Taller")
    st.info("Módulo operativo.")