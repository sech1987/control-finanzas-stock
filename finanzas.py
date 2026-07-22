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
                            st.success(f"🎉 ¡Cuenta de {reg_taller} creada con éxito! Ya podés iniciar sesión.{mensaje_vto}")
                    except Exception as e:
                        st.error(f"Error al registrar la cuenta: {e}")
                else:
                    st.warning("Por favor, completá todos los campos para el registro.")

# ==========================================
# 📊 PÁGINA PRINCIPAL (SISTEMA AUTENTICADO)
# ==========================================
else:
    id_propietario_datos = st.session_state.get("owner_id")
    usuario_id_actual = st.session_state.get("usuario_id")
    usuario_email_actual = st.session_state.get("usuario_email")
    rol_actual = st.session_state.get("rol", "Empleado")

    @st.cache_data(ttl=3)
    def cargar_datos_seguro(owner_id_filtro):
        try:
            res_historial = supabase.table("historial").select("*").order("fecha", desc=True).execute()
            datos_historial = extraer_datos_respuesta(res_historial)
            df_hist_tmp = pd.DataFrame(datos_historial) if datos_historial else pd.DataFrame()
            
            if not df_hist_tmp.empty:
                df_hist_tmp["fecha"] = pd.to_datetime(df_hist_tmp["fecha"])
                df_hist_tmp["monto"] = df_hist_tmp["monto"].astype(float)
                
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
                df_stock_tmp["precio_costo"] = df_stock_tmp[col_precio].astype(float) if col_precio else 0.0
                
            return df_hist_tmp, df_stock_tmp
        except Exception as e:
            st.error(f"Error cargando base de datos: {e}")
            return pd.DataFrame(), pd.DataFrame()

    df_historial_total, df_stock_total = cargar_datos_seguro(id_propietario_datos)

    # FILTRO ESTRICTO DE HISTORIAL POR DUEÑO DE TALLER
    if not df_historial_total.empty and "owner_id" in df_historial_total.columns and id_propietario_datos is not None:
        df_historial = df_historial_total[df_historial_total["owner_id"].astype(str) == str(id_propietario_datos)]
    else:
        df_historial = df_historial_total if id_propietario_datos is None else pd.DataFrame()

    # FILTRO ESTRICTO DE STOCK POR DUEÑO DE TALLER
    if not df_stock_total.empty and "owner_id" in df_stock_total.columns and id_propietario_datos is not None:
        df_stock = df_stock_total[df_stock_total["owner_id"].astype(str) == str(id_propietario_datos)]
    else:
        df_stock = df_stock_total if id_propietario_datos is None else pd.DataFrame()

    col_desc_detectada = "descripcion"
    if not df_historial.empty:
        for c in ["descripción", "descripcion", "detalle", "concepto"]:
            if c in df_historial.columns:
                col_desc_detectada = c
                break

    caja_negocio = 0.0
    billetera_personal = 0.0
    if not df_historial.empty:
        ingresos = df_historial[(df_historial["tipo"] == "Ingreso")]["monto"].sum()
        gastos_negocio = df_historial[(df_historial["tipo"] == "Gasto Negocio")]["monto"].sum()
        retiros_personales = df_historial[(df_historial["tipo"] == "Retiro Sueldo")]["monto"].sum()
        gastos_personales = df_historial[(df_historial["tipo"] == "Gasto Personal")]["monto"].sum()
        
        caja_negocio = ingresos - gastos_negocio - retiros_personales
        billetera_personal = retiros_personales - gastos_personales

    # --- MENÚ LATERAL ESTILIZADO POR BOTONES ---
    with st.sidebar:
        if st.session_state.logo_taller is not None:
            st.image(st.session_state.logo_taller, width=100)
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
            
        st.title(st.session_state.nombre_taller)
        st.caption(f"Sesión: **{usuario_email_actual}** ({rol_actual})")
        
        with st.expander("⚙️ Configurar Logo"):
            archivo_logo = st.file_uploader("Subir imagen (PNG/JPG)", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
            if archivo_logo is not None:
                try:
                    img_logo = Image.open(archivo_logo)
                    st.session_state.logo_taller = img_logo.resize((300, 300))
                    st.rerun()
                except Exception:
                    pass

        st.markdown("---")
        st.markdown("### 📌 Navegación")
        
        if "seccion_activa" not in st.session_state:
            st.session_state.seccion_activa = "📊 Dashboard General" if rol_actual == "Admin" else "💵 Mi Caja Diaria"

        if rol_actual == "Admin":
            secciones_botones = [
                ("📊 Dashboard General", "📊 Dashboard General"),
                ("🧾 Cajas & Cierres Empleados", "🧾 Cajas & Cierres Empleados"),
                ("🤖 Consultor IA", "🤖 Consultor IA"),
                ("📝 Nueva Operación", "📝 Nueva Operación"),
                ("🧮 Calculadora de Costos", "🧮 Calculadora de Costos"),
                ("📉 Punto de Equilibrio", "📉 Punto de Equilibrio"),
                ("📦 Stock de Insumos", "📦 Stock de Insumos"),
                ("🎯 Metas de Ahorro", "🎯 Metas de Ahorro"),
                ("👥 Personal del Taller", "👥 Personal del Taller")
            ]
        else:
            secciones_botones = [
                ("💵 Mi Caja Diaria", "💵 Mi Caja Diaria"),
                ("📝 Nueva Operación", "📝 Nueva Operación"),
                ("📦 Stock de Insumos", "📦 Stock de Insumos")
            ]

        for label, nombre_seccion in secciones_botones:
            es_activa = (st.session_state.seccion_activa == nombre_seccion)
            tipo_btn = "primary" if es_activa else "secondary"
            if st.button(label, key=f"nav_btn_{nombre_seccion}", use_container_width=True, type=tipo_btn):
                st.session_state.seccion_activa = nombre_seccion
                st.rerun()

        seccion = st.session_state.seccion_activa

        st.markdown("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.usuario_email = ""
            st.session_state.usuario_id = None
            st.session_state.owner_id = None
            st.session_state.logo_taller = None
            st.rerun()

    # ==========================================
    # 📊 DASHBOARD GENERAL (ADMIN)
    # ==========================================
    if seccion == "📊 Dashboard General" and rol_actual == "Admin":
        st.title(f"📊 Control de Mando - {st.session_state.nombre_taller}")
        
        if not df_stock.empty:
            criticos = df_stock[df_stock["cantidad"] <= df_stock["minimo"]]
            if not criticos.empty:
                st.warning(f"⚠️ **Alerta de Stock:** Tenés {len(criticos)} insumo(s) en punto de reorden mínimo ({', '.join(criticos['item'].tolist())}). Revisá la sección de Stock.")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.metric(label="💼 FONDOS DISPONIBLES EMPRENDIMIENTO", value=f"$ {caja_negocio:,.2f}")
            st.caption("Capital total activo en la caja operativa del taller.")
        with col_c2:
            st.metric(label="👤 FINANZAS PERSONALES (RETIRO LIBRE)", value=f"$ {billetera_personal:,.2f}")
            st.caption("Dinero extraído neto disponible para tus gastos personales cotidianos.")
            
        st.markdown("---")
        st.markdown("### 💡 Distribución Interna Recomendada")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1: st.metric(label="📦 CAJA INSUMOS (35%)", value=f"$ {caja_negocio * 0.35:,.2f}")
        with col_p2: st.metric(label="💸 CAJA SUELDOS (55%)", value=f"$ {caja_negocio * 0.55:,.2f}")
        with col_p3: st.metric(label="🔧 MANTENIMIENTO (10%)", value=f"$ {caja_negocio * 0.10:,.2f}")
            
        st.markdown("---")
        if not df_historial.empty:
            col_exp1, col_exp2 = st.columns([1, 1])
            with col_exp1:
                st.markdown("### 📥 Exportar Historial Completo")
                df_exportar = df_historial.copy()
                df_exportar["fecha"] = df_exportar["fecha"].dt.strftime('%Y-%m-%d %H:%M:%S')
                csv_data = df_exportar.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("📥 Descargar Movimientos (Excel/CSV)", data=csv_data, file_name=f"movimientos_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
            with col_exp2:
                st.markdown("### 📅 Seleccionar Período")
                df_historial["periodo"] = df_historial["fecha"].dt.strftime('%Y-%m')
                periodos = sorted(df_historial["periodo"].unique(), reverse=True)
                periodo_sel = st.selectbox("Mes de Análisis:", periodos)
                df_filtrado_mes = df_historial[df_historial["periodo"] == periodo_sel]
            
            st.markdown("---")
            st.subheader(f"📊 Balance Financiero Mensual ({periodo_sel})")
            ingresos_m = df_filtrado_mes[df_filtrado_mes["tipo"] == "Ingreso"]["monto"].sum()
            egresos_m = df_filtrado_mes[df_filtrado_mes["tipo"].isin(["Gasto Negocio", "Retiro Sueldo", "Gasto Personal"])]["monto"].sum()
            st.bar_chart(pd.DataFrame({"Categoría": ["Gastos", "Ingresos"], "Monto ($)": [egresos_m, ingresos_m]}), x="Categoría", y="Monto ($)", color="#ff4b4b", use_container_width=True)
            
            st.markdown("---")
            st.subheader("📋 Lista Detallada de Movimientos")
            for idx, row in df_filtrado_mes.iterrows():
                color_card = "#2ecc71" if row["tipo"] == "Ingreso" else "#e74c3c"
                simbolo = "➕" if row["tipo"] == "Ingreso" else "➖"
                with st.container(border=True):
                    col_t1, col_t2, col_t3 = st.columns([5, 3, 1])
                    with col_t1:
                        st.markdown(f"**{simbolo} {row['tipo']}** - {row[col_desc_detectada]}")
                        f_str = row['fecha'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['fecha'], 'strftime') else str(row['fecha'])
                        st.caption(f"📅 Fecha: {f_str} | Usuario: {row.get('usuario_email', 'Admin')}")
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
    # 💵 MI CAJA DIARIA (VISTA EMPLEADO / MI CAJA)
    # ==========================================
    elif seccion == "💵 Mi Caja Diaria":
        st.title(f"💵 Mi Caja del Día - {usuario_email_actual}")
        st.markdown("Registrá tus cobranzas del día y realizá el cierre de caja antes de terminar la jornada.")
        
        hoy_str = datetime.now().strftime('%Y-%m-%d')
        if not df_historial.empty and "usuario_email" in df_historial.columns:
            df_mi_caja_hoy = df_historial[(df_historial["fecha"].dt.strftime('%Y-%m-%d') == hoy_str) & (df_historial["usuario_email"] == usuario_email_actual)]
        elif not df_historial.empty:
            df_mi_caja_hoy = df_historial[df_historial["fecha"].dt.strftime('%Y-%m-%d') == hoy_str]
        else:
            df_mi_caja_hoy = pd.DataFrame()

        ingresos_hoy = df_mi_caja_hoy[df_mi_caja_hoy["tipo"] == "Ingreso"]["monto"].sum() if not df_mi_caja_hoy.empty else 0.0
        gastos_hoy = df_mi_caja_hoy[df_mi_caja_hoy["tipo"] == "Gasto Negocio"]["monto"].sum() if not df_mi_caja_hoy.empty else 0.0
        saldo_teorico_hoy = ingresos_hoy - gastos_hoy

        col_mc1, col_mc2, col_mc3 = st.columns(3)
        col_mc1.metric("🟢 Ventas/Cobros del Día", f"$ {ingresos_hoy:,.2f}")
        col_mc2.metric("🔴 Gastos en Efectivo del Día", f"$ {gastos_hoy:,.2f}")
        col_mc3.metric("💼 SALDO A ENTREGAR EN CAJA", f"$ {saldo_teorico_hoy:,.2f}")

        st.markdown("---")
        st.subheader("📋 Mis Movimientos de Hoy")
        if df_mi_caja_hoy.empty:
            st.info("Aún no registraste cobros ni gastos el día de hoy.")
        else:
            st.dataframe(df_mi_caja_hoy[["fecha", "tipo", col_desc_detectada, "monto"]], use_container_width=True)

        st.markdown("---")
        with st.container(border=True):
            st.subheader("🔒 Arqueo y Cierre de Caja Diaria")
            st.markdown("Contá el dinero en efectivo del cajón e ingresalo abajo para cerrar el día:")
            
            monto_fisico_real = st.number_input("Monto Físico Real en Cajón ($):", min_value=0.0, step=100.0)
            diferencia_caja = monto_fisico_real - saldo_teorico_hoy
            
            if monto_fisico_real > 0:
                if diferencia_caja == 0:
                    st.success("🟢 ¡Caja Perfecta! El efectivo físico coincide exacto con el sistema.")
                elif diferencia_caja > 0:
                    st.info(f"🔵 Sobrante en Caja: $ {diferencia_caja:,.2f}")
                else:
                    st.error(f"🔴 Faltante en Caja: $ {abs(diferencia_caja):,.2f}")

            observacion_cierre = st.text_input("Observaciones / Notas del Cierre (Ej: Se dejó $5.000 para cambio)")

            if st.button("🔒 Confirmar y Enviar Cierre de Caja", type="primary", use_container_width=True):
                try:
                    res_sample_c = supabase.table("cierres_caja").select("*").limit(1).execute()
                    datos_sample_c = extraer_datos_respuesta(res_sample_c)
                    cols_c = list(datos_sample_c[0].keys()) if datos_sample_c else []
                    
                    registro_cierre = {
                        "fecha": datetime.now().isoformat(),
                        "usuario_email": usuario_email_actual,
                        "ingresos_sistema": ingresos_hoy,
                        "gastos_sistema": gastos_hoy,
                        "saldo_teorico": saldo_teorico_hoy,
                        "efectivo_real": monto_fisico_real,
                        "diferencia": diferencia_caja,
                        "observacion": observacion_cierre
                    }
                    if "owner_id" in cols_c and id_propietario_datos is not None:
                        registro_cierre["owner_id"] = int(id_propietario_datos)

                    supabase.table("cierres_caja").insert(registro_cierre).execute()
                    st.success("🎉 ¡Cierre de caja registrado y enviado al administrador exitosamente!")
                except Exception as e:
                    st.error(f"Error al registrar el cierre: {e}")

    # ==========================================
    # 🧾 CAJAS Y CIERRES DE EMPLEADOS
    # ==========================================
    elif seccion == "🧾 Cajas & Cierres Empleados" and rol_actual == "Admin":
        st.title("🧾 Panel de Control de Cajas y Cierres de Empleados")
        st.markdown("Revisá en tiempo real las cajas individuales de tu personal, descargá los reportes y gestioná los arqueos de caja.")

        try:
            res_cierres = supabase.table("cierres_caja").select("*").order("fecha", desc=True).execute()
            datos_cierres = extraer_datos_respuesta(res_cierres)
            df_cierres_tmp = pd.DataFrame(datos_cierres) if datos_cierres else pd.DataFrame()
            
            # Filtro estricto por dueño de taller
            if not df_cierres_tmp.empty and "owner_id" in df_cierres_tmp.columns and id_propietario_datos is not None:
                df_cierres = df_cierres_tmp[df_cierres_tmp["owner_id"].astype(str) == str(id_propietario_datos)]
            else:
                df_cierres = df_cierres_tmp if id_propietario_datos is None else pd.DataFrame()
        except Exception:
            df_cierres = pd.DataFrame()

        tab_cierres_hist, tab_cajas_vivo = st.tabs(["📋 Historial de Cierres Recibidos", "🔍 Auditar Cajas en Vivo"])

        with tab_cierres_hist:
            if df_cierres.empty:
                st.info("Aún no se registraron cierres de caja enviados por empleados.")
            else:
                df_exp_cierres = df_cierres.copy()
                if "fecha" in df_exp_cierres.columns:
                    df_exp_cierres["fecha"] = pd.to_datetime(df_exp_cierres["fecha"]).dt.strftime('%Y-%m-%d %H:%M:%S')
                
                csv_cierres_data = df_exp_cierres.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 Descargar Reporte de Cierres de Caja (Excel / CSV)",
                    data=csv_cierres_data,
                    file_name=f"cierres_caja_{st.session_state.nombre_taller}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                st.markdown("---")
                st.subheader("📋 Lista Detallada de Arqueos de Caja")
                
                for idx_cierre, row_cierre in df_cierres.iterrows():
                    with st.container(border=True):
                        col_c1, col_c2, col_c3 = st.columns([4, 4, 1])
                        
                        fecha_f = pd.to_datetime(row_cierre["fecha"]).strftime('%d/%m/%Y %H:%M') if "fecha" in row_cierre else "S/F"
                        col_c1.markdown(f"👤 **{row_cierre.get('usuario_email', 'Empleado')}**")
                        col_c1.caption(f"📅 Fecha de Cierre: {fecha_f}")
                        if row_cierre.get("observacion"):
                            col_c1.caption(f"📝 Nota: {row_cierre.get('observacion')}")
                            
                        col_c2.markdown(f"**Sistema:** $ {float(row_cierre.get('saldo_teorico', 0)):,.2f} | **Físico:** $ {float(row_cierre.get('efectivo_real', 0)):,.2f}")
                        dif_val = float(row_cierre.get('diferencia', 0))
                        if dif_val == 0:
                            col_c2.markdown("<span style='color:green; font-weight:bold;'>🟢 Caja Sin Diferencia</span>", unsafe_allow_html=True)
                        elif dif_val > 0:
                            col_c2.markdown(f"<span style='color:blue; font-weight:bold;'>🔵 Sobrante: $ {dif_val:,.2f}</span>", unsafe_allow_html=True)
                        else:
                            col_c2.markdown(f"<span style='color:red; font-weight:bold;'>🔴 Faltante: $ {abs(dif_val):,.2f}</span>", unsafe_allow_html=True)

                        with col_c3:
                            if st.button("🗑️", key=f"del_cierre_{row_cierre['id']}", help="Eliminar este cierre de caja"):
                                try:
                                    supabase.table("cierres_caja").delete().eq("id", int(row_cierre["id"])).execute()
                                    st.success("¡Cierre eliminado!")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al borrar: {e}")

        with tab_cajas_vivo:
            st.subheader("🔍 Movimientos del Día por Usuario")
            if not df_historial.empty and "usuario_email" in df_historial.columns:
                lista_usuarios = df_historial["usuario_email"].dropna().unique().tolist()
                user_filtro = st.selectbox("Seleccionar Usuario para Auditar:", lista_usuarios)
                
                df_audit_user = df_historial[df_historial["usuario_email"] == user_filtro]
                st.dataframe(df_audit_user[["fecha", "tipo", col_desc_detectada, "monto"]], use_container_width=True)
            else:
                st.info("No hay suficientes datos registrados con correo de usuario para filtrar.")

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
                        
                        fila_insertar = {
                            "fecha": datetime.now().isoformat(),
                            "tipo": tipo_db,
                            "monto": monto_op,
                            col_destino_desc: desc_op,
                            "usuario_email": usuario_email_actual
                        }
                        if "owner_id" in columnas_existentes_hist and id_propietario_datos is not None: fila_insertar["owner_id"] = int(id_propietario_datos)
                        
                        supabase.table("historial").insert(fila_insertar).execute()
                        st.success("¡Operación registrada con éxito!")
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
        st.title("📉 Calculadora Real de Punto de Equilibrio Financiero")
        st.markdown("Descubrí exactamente cuántos pesos y cuántos trabajos tenés que vender para cubrir el 100% de los costos fijos de tu taller.")
        
        tab_pe_moneda, tab_pe_unidades = st.tabs(["💵 Calculadora por Facturación Total ($)", "📦 Calculadora por Cantidad de Trabajos/Unidades"])

        with tab_pe_moneda:
            with st.container(border=True):
                st.subheader("1️⃣ Desglose de Costos Fijos Mensuales")
                col_cf1, col_cf2 = st.columns(2)
                
                alquiler = col_cf1.number_input("Alquiler Taller / Local ($):", value=80000.0, step=5000.0)
                servicios = col_cf2.number_input("Luz, Agua, Internet, Celular ($):", value=25000.0, step=2000.0)
                
                col_cf3, col_cf4 = st.columns(2)
                impuestos = col_cf3.number_input("Monotributo / IIBB / Contabilidad ($):", value=15000.0, step=1000.0)
                sueldos_fijos = col_cf4.number_input("Sueldos Fijos / Retiro Mínimo ($):", value=180000.0, step=10000.0)

                mantenimiento_equipos = st.number_input("Mantenimiento de Máquinas / Repuestos ($):", value=20000.0, step=2000.0)

                total_costos_fijos = alquiler + servicios + impuestos + sueldos_fijos + mantenimiento_equipos
                st.markdown(f"#### 💸 **Total Costos Fijos Mensuales:** `$ {total_costos_fijos:,.2f}`")

            st.markdown("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.subheader("2️⃣ Margen Promedio y Resultado Financiero")
                
                margen_promedio_pct = st.slider("Margen Promedio de Ganancia sobre Costo Variable (%)", min_value=10, max_value=300, value=60, step=5)
                
                margen_contribucion_ratio = (margen_promedio_pct / (100 + margen_promedio_pct))
                punto_equilibrio_pesos = total_costos_fijos / margen_contribucion_ratio if margen_contribucion_ratio > 0 else 0.0

                st.markdown("---")
                col_per1, col_per2 = st.columns(2)
                col_per1.metric("🏁 FACTURACIÓN MÍNIMA MENSUAL", f"$ {punto_equilibrio_pesos:,.2f}")
                col_per2.metric("📊 Margen de Contribución Real", f"{margen_contribucion_ratio * 100:.1f} %")

                mes_actual_str = datetime.now().strftime('%Y-%m')
                ingresos_mes_actual = 0.0
                if not df_historial.empty:
                    df_mes_act = df_historial[(df_historial["fecha"].dt.strftime('%Y-%m') == mes_actual_str) & (df_historial["tipo"] == "Ingreso")]
                    ingresos_mes_actual = df_mes_act["monto"].sum()

                diferencia_pe = ingresos_mes_actual - punto_equilibrio_pesos
                st.markdown("---")
                st.subheader("📈 Estado del Mes Actual")
                col_st1, col_st2 = st.columns(2)
                col_st1.metric("💵 Facturado en el Mes Actual", f"$ {ingresos_mes_actual:,.2f}")
                
                if diferencia_pe >= 0:
                    col_st2.metric("🎉 Superávit / Ganancia Neta", f"$ {diferencia_pe:,.2f}", delta="Caja Cubierta")
                    st.success("🟢 **¡Felicidades!** Ya cubriste todos los costos fijos del taller este mes. Todo lo que factures a partir de ahora es ganancia neta.")
                else:
                    col_st2.metric("⚠️ Falta Facturar", f"$ {abs(diferencia_pe):,.2f}", delta="-Aún sin cubrir")
                    st.info(f"💡 Te faltan facturar **$ {abs(diferencia_pe):,.2f}** para alcanzar el punto de equilibrio de este mes.")

        with tab_pe_unidades:
            st.subheader("📦 ¿Cuántas Unidades/Trabajos tenés que vender?")
            st.markdown("Ingresá el valor y costo promedio de tu trabajo más vendido para calcular el volumen necesario de producción:")

            with st.container(border=True):
                col_u1, col_u2 = st.columns(2)
                nombre_prod_estrella = col_u1.text_input("Producto / Trabajo Referencia:", value="Taza Personalizada / Bajada DTF")
                precio_venta_unitario = col_u2.number_input("Precio de Venta Promedio por Unidad ($):", value=4500.0, step=500.0)

                costo_variable_unitario = st.number_input("Costo Directo de Insumos por Unidad ($):", value=2000.0, step=200.0)

                margin_ganancia_unidad = precio_venta_unitario - costo_variable_unitario

                if margin_ganancia_unidad > 0:
                    unidades_necesarias = total_costos_fijos / margin_ganancia_unidad
                    st.markdown("---")
                    col_un1, col_un2 = st.columns(2)
                    col_un1.metric("🎯 UNIDADES MENSUALES A VENDER", f"{int(unidades_necesarias) + 1} unidades")
                    col_un2.metric("💰 Ganancia Neta por Unidad", f"$ {margin_ganancia_unidad:,.2f}")

                    unidades_diarias = (unidades_necesarias / 22)
                    st.info(f"📌 Para alcanzar el punto de equilibrio vendiendo solo *{nombre_prod_estrella}*, necesitás producir aproximadamente **{int(unidades_diarias) + 1} unidades por día hábil**.")
                else:
                    st.error("⚠️ El precio de venta debe ser mayor al costo de insumos para poder calcular el punto de equilibrio.")

    # ==========================================
    # 📦 STOCK DE INSUMOS
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
                                st.success(f"¡Insumo '{item_seleccionado}' eliminado!")
                                st.cache_data.clear(); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")
                                
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
    # 🎯 METAS DE AHORRO
    # ==========================================
    elif seccion == "🎯 Metas de Ahorro" and rol_actual == "Admin":
        st.title("🎯 Metas de Ahorro")
        try:
            res_metas = supabase.table("metas").select("*").execute()
            datos_metas_totales = extraer_datos_respuesta(res_metas)
            df_metas_tmp = pd.DataFrame(datos_metas_totales) if datos_metas_totales else pd.DataFrame()
            
            # FILTRO ESTRICTO DE METAS POR DUEÑO DE TALLER
            if not df_metas_tmp.empty and "owner_id" in df_metas_tmp.columns and id_propietario_datos is not None:
                df_metas = df_metas_tmp[df_metas_tmp["owner_id"].astype(str) == str(id_propietario_datos)]
            else:
                df_metas = df_metas_tmp if id_propietario_datos is None else pd.DataFrame()
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
                            res_dup = supabase.table("metas").select("*").eq("meta", nueva_meta_nombre).execute()
                            datos_dup = extraer_datos_respuesta(res_dup)
                            duplicado = any(str(d.get("owner_id")) == str(id_propietario_datos) for d in datos_dup)
                                    
                            if duplicado:
                                st.warning(f"⚠️ Ya tenés una alcancía llamada '{nueva_meta_nombre}'.")
                            else:
                                res_sample_m = supabase.table("metas").select("*").limit(1).execute()
                                datos_sample_m = extraer_datos_respuesta(res_sample_m)
                                columnas_metas = list(datos_sample_m[0].keys()) if datos_sample_m else []
                                
                                obj_col = "objetivo"
                                for c in ["objetivo", "objective", "monto_objetivo"]:
                                    if c in columnas_metas: obj_col = c; break
                                
                                nueva_fila_meta = {"meta": nueva_meta_nombre, "acumulado": 0.0, obj_col: float(objetivo_monto)}
                                if "owner_id" in columnas_metas and id_propietario_datos is not None:
                                    nueva_fila_meta["owner_id"] = int(id_propietario_datos)
                                
                                supabase.table("metas").insert(nueva_fila_meta).execute()
                                st.success(f"¡Alcancía '{nueva_meta_nombre}' creada con éxito!")
                                st.cache_data.clear(); st.rerun()
                        except Exception as e: st.error(f"Error: {e}")

        st.markdown("---")
        if df_metas.empty:
            st.info("📌 Todavía no tenés ninguna alcancía creada.")
        else:
            st.subheader("📌 Tus Alcancías Activas")
            for idx, row in df_metas.iterrows():
                with st.container(border=True):
                    col_obj_ver = 'objective' if 'objective' in row else ('objetivo' if 'objetivo' in row else None)
                    obj = float(row[col_obj_ver]) if col_obj_ver and row[col_obj_ver] is not None else 1.0
                    acum = float(row.get('acumulado', 0.0))
                    
                    porcentaje = (acum / obj) * 100 if obj > 0 else 0.0
                    col_m1, col_m2, col_m3 = st.columns([4, 3, 2])
                    
                    col_m1.markdown(f"🎯 **{row['meta']}**")
                    col_m1.progress(min(1.0, max(0.0, acum / obj)))
                    col_m1.caption(f"📈 Progreso: **{porcentaje:.1f}%**")
                    col_m2.markdown(f"**Ahorrado:** $ {acum:,.2f} / $ {obj:,.2f}")
                    
                    with col_m3:
                        monto_ahorrar = st.number_input("Sumar/Restar ($):", value=0.0, step=500.0, key=f"add_m_input_{row['id']}")
                        col_btns = st.columns(2)
                        with col_btns[0]:
                            if st.button("💾", key=f"btn_save_m_meta_{row['id']}"):
                                if acum + monto_ahorrar >= 0:
                                    supabase.table("metas").update({"acumulado": acum + monto_ahorrar}).eq("id", int(row["id"])).execute()
                                    st.cache_data.clear(); st.rerun()
                        with col_btns[1]:
                            if st.button("🗑️", key=f"btn_del_m_meta_{row['id']}"):
                                supabase.table("metas").delete().eq("id", int(row["id"])).execute()
                                st.cache_data.clear(); st.rerun()

    # ==========================================
    # 👥 PERSONAL DEL TALLER
    # ==========================================
    elif seccion == "👥 Personal del Taller" and rol_actual == "Admin":
        st.title("👥 Panel de Control de Usuarios y Empleados")
        st.markdown("Crea, gestiona y da de baja a los miembros del equipo de tu taller.")
        
        admin_id_actual = st.session_state.get("owner_id") or st.session_state.get("usuario_id")
        nombre_taller_actual = st.session_state.get("nombre_taller", "Olivia Imagen")
        
        try:
            res_usuarios_all = supabase.table("usuarios").select("*").eq("rol", "Empleado").execute()
            datos_u_all = extraer_datos_respuesta(res_usuarios_all)
            df_u_all = pd.DataFrame(datos_u_all) if datos_u_all else pd.DataFrame()
            
            if not df_u_all.empty:
                condicion_owner = (df_u_all["owner_id"].astype(str) == str(admin_id_actual)) if "owner_id" in df_u_all.columns else False
                col_taller = "nombre_taller" if "nombre_taller" in df_u_all.columns else ("taller" if "taller" in df_u_all.columns else None)
                condicion_taller = (df_u_all[col_taller] == nombre_taller_actual) if col_taller else False
                df_usuarios_db = df_u_all[condicion_owner | condicion_taller]
            else: df_usuarios_db = pd.DataFrame()
        except Exception as e:
            df_usuarios_db = pd.DataFrame()
            
        with st.container(border=True):
            st.subheader("🆕 Crear Nuevo Empleado")
            with st.form("form_crear_usuario", clear_on_submit=True):
                col_u1, col_u2 = st.columns(2)
                nuevo_email_user = col_u1.text_input("Correo Electrónico (Login)", placeholder="empleado@olivia.com")
                nuevo_pass_user = col_u2.text_input("Contraseña de Acceso", type="password", placeholder="••••••••")
                
                if st.form_submit_button("👥 Guardar Nuevo Miembro", type="primary", use_container_width=True):
                    if nuevo_email_user and nuevo_pass_user:
                        try:
                            res_sample = supabase.table("usuarios").select("*").limit(1).execute()
                            datos_sample = extraer_datos_respuesta(res_sample)
                            columnas_existentes = list(datos_sample[0].keys()) if datos_sample else []
                            
                            col_pass_detectada = "password"
                            for k in ["password", "contraseña", "contrasena", "clave", "pass"]:
                                if k in columnas_existentes: col_pass_detectada = k; break
                            
                            nuevo_empleado = {"email": nuevo_email_user, col_pass_detectada: nuevo_pass_user, "rol": "Empleado"}
                            if "owner_id" in columnas_existentes and admin_id_actual is not None: nuevo_empleado["owner_id"] = int(admin_id_actual)
                            if "nombre_taller" in columnas_existentes: nuevo_empleado["nombre_taller"] = nombre_taller_actual
                            elif "taller" in columnas_existentes: nuevo_empleado["taller"] = nombre_taller_actual
                                        
                            supabase.table("usuarios").insert(nuevo_empleado).execute()
                            st.success(f"¡Empleado '{nuevo_email_user}' registrado exitosamente!")
                            st.cache_data.clear(); st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
                    else: st.warning("Completá todos los campos.")
                        
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
                        st.caption(f"Rol: {row.get('rol', 'Empleado')}")
                    with col_emp2: st.markdown(f"🏢 Taller: **{nombre_taller_actual}**")
                    with col_emp3:
                        if st.button("🗑️", key=f"del_user_{row['id']}"):
                            try:
                                supabase.table("usuarios").delete().eq("id", int(row["id"])).execute()
                                st.success("¡Empleado eliminado!")
                                st.cache_data.clear(); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")
