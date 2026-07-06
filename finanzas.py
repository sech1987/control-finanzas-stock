import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime, timezone
from supabase import create_client, Client
import io

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
                        if email_input == "admin@olivia.com" and pass_input == "taller2026":
                            st.session_state.autenticado = True
                            st.session_state.usuario_id = 1
                            st.session_state.nombre_taller = "Olivia Imagen"
                            st.session_state.user_rol = "Admin"
                            st.rerun()
                        
                        pass_encriptada = encriptar_contrasena(pass_input)
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
        opciones_menu = ["🏠 Dashboard General", "📝 Nueva Operación", "🧮 Calculadora de Costos", "📦 Stock de Insumos", "📉 Punto de Equilibrio", "🎯 Metas de Ahorro", "⚙️ Configurar Categorías", "📊 Mi Cierre de Caja", "👥 Personal del Taller"]
    else:
        opciones_menu = ["📝 Nueva Operación", "📦 Stock de Insumos", "📊 Mi Cierre de Caja"]
        
    seccion = st.radio("Navegación:", opciones_menu)
    st.markdown("---")
    
    # --- BOTÓN INTERNO DE ALERTA DE STOCK EN SIDEBAR ---
    if not df_stock.empty:
        criticos = df_stock[df_stock["cantidad"] <= df_stock["minimo"]]
        if not criticos.empty:
            st.error(f"⚠️ ¡Falta reponer {len(criticos)} insumos!")

# --- 🏠 DASHBOARD GENERAL ---
if seccion == "🏠 Dashboard General" and rol_actual == "Admin":
    st.title("🏠 Panel de Control General")
    
    # --- ALERTAS DE SALDOS DESFAVORABLES ---
    if caja_negocio < 0:
        st.error("⚠️ Alerta: La caja del emprendimiento se encuentra con saldo negativo / desfavorable.")
    if billetera_personal < 0:
        st.warning("⚠️ Alerta: Las finanzas personales registran saldo en rojo.")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("<p style='color: #94A3B8; font-size: 14px; font-weight: bold;'>FONDOS DISPONIBLES EMPRENDIMIENTO</p>", unsafe_allow_html=True)
            color_n = "#F87171" if caja_negocio < 0 else "#38BDF8"
            st.markdown(f"<h2 style='color: {color_n}; font-size: 42px; margin-top: 0px;'>$ {caja_negocio:,.2f}</h2>", unsafe_allow_html=True)
    with col2:
        with st.container(border=True):
            st.markdown("<p style='color: #94A3B8; font-size: 14px; font-weight: bold;'>FINANZAS PERSONALES (LIBRE)</p>", unsafe_allow_html=True)
            color_p = "#F87171" if billetera_personal < 0 else "#34D399"
            st.markdown(f"<h2 style='color: {color_p}; font-size: 42px; margin-top: 0px;'>$ {billetera_personal:,.2f}</h2>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("💡 Distribución Interna Recomendada")
    monto_negocio_total = max(0.0, caja_negocio)
    sub_col1, sub_col2, sub_col3 = st.columns(3)
    with sub_col1:
        with st.container(border=True): st.markdown(f"<p style='color: #38BDF8; font-size:13px; font-weight:bold; margin-bottom:2px;'>🛠️ CAJA INSUMOS (40%)</p><h3>$ {monto_negocio_total * 0.40:,.2f}</h3>", unsafe_allow_html=True)
    with sub_col2:
        with st.container(border=True): st.markdown(f"<p style='color: #A78BFA; font-size:13px; font-weight:bold; margin-bottom:2px;'>💰 CAJA SUELDOS (40%)</p><h3>$ {monto_negocio_total * 0.40:,.2f}</h3>", unsafe_allow_html=True)
    with sub_col3:
        with st.container(border=True): st.markdown(f"<p style='color: #FBBF24; font-size:13px; font-weight:bold; margin-bottom:2px;'>🔧 MANTENIMIENTO (20%)</p><h3>$ {monto_negocio_total * 0.20:,.2f}</h3>", unsafe_allow_html=True)

    st.markdown("<br><hr style='border-color: #334155;'><br>", unsafe_allow_html=True)
    
    if df_historial.empty:
        st.info("No hay movimientos registrados todavía.")
    else:
        # --- 📥 BAJAR PLANILLA EXCEL NATIVA ---
        st.subheader("📊 Exportar Historial Completo")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_historial.to_excel(writer, index=False, sheet_name='Movimientos')
        st.download_button(
            label="📥 Descargar Planilla de Movimientos (Excel)",
            data=buffer.getvalue(),
            file_name=f"Planilla_Movimientos_{st.session_state.nombre_taller}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.markdown("<br>", unsafe_allow_html=True)

        df_historial["fecha"] = pd.to_datetime(df_historial["fecha"])
        df_historial["Mes"] = df_historial["fecha"].dt.strftime("%Y-%m")
        
        mes_sel = st.selectbox("📆 Seleccionar Período:", sorted(df_historial["Mes"].unique(), reverse=True))
        df_mes = df_historial[df_historial["Mes"] == mes_sel]
        
        tab_ingresos, tab_egresos = st.tabs(["📥 Historial de INGRESOS (Ventas)", "📤 Historial de EGRESOS (Gastos)"])
        
        with tab_ingresos:
            df_ingresos = df_mes[df_mes["tipo"] == "Ingreso"]
            for idx, row in df_ingresos[::-1].iterrows():
                with st.container(border=True):
                    col_h1, col_h2, col_h3, col_h4 = st.columns([1, 2, 4, 1])
                    with col_h1: st.caption(str(row["fecha"].strftime("%Y-%m-%d")))
                    with col_h2: st.markdown(f"**$ {float(row['monto']):,.2f}**")
                    with col_h3:
                        st.markdown(f"🔹 *{row['categoria']}* — {row['detalle']}")
                        st.caption(f"Condición: **{row['estado_pago']}** | Medio: **{row['metodo_pago']}**")
                    with col_h4:
                        if st.button("🗑️", key=f"del_ing_{row['id']}"):
                            supabase.table("historial").delete().eq("id", int(row["id"])).execute()
                            st.rerun()

        with tab_egresos:
            df_egresos = df_mes[df_mes["tipo"] == "Gasto"]
            for idx, row in df_egresos[::-1].iterrows():
                with st.container(border=True):
                    col_e1, col_e2, col_e3, col_e4 = st.columns([1, 2, 4, 1])
                    with col_e1: st.caption(str(row["fecha"].strftime("%Y-%m-%d")))
                    with col_e2: st.markdown(f"**$ {float(row['monto']):,.2f}**")
                    with col_e3:
                        lbl = "⚙️ GASTO TALLER" if row["cuenta"] == "Negocio" else "👤 PERSONAL"
                        st.markdown(f"**{lbl}** | *{row['categoria']}*\n\n{row['detalle']}")
                    with col_e4:
                        if st.button("🗑️", key=f"del_egr_{row['id']}"):
                            supabase.table("historial").delete().eq("id", int(row["id"])).execute()
                            st.rerun()

# --- 📝 NUEVA OPERACIÓN (CON DESCUENTO CONECTADO DE STOCK) ---
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
            
            # --- INTERFAZ DE CONEXIÓN CON STOCK ---
            descuenta_stock = False
            insumo_seleccionado = None
            cantidad_a_descontar = 0
            
            if not df_stock.empty and categoria == "Venta Producto":
                descuenta_stock = st.checkbox("🔄 ¿Esta venta descuenta materiales del Stock?")
                if descuenta_stock:
                    col_st1, col_st2 = st.columns(2)
                    with col_st1:
                        insumo_seleccionado = st.selectbox("Seleccionar Insumo consumido:", df_stock["item"].tolist())
                    with col_st2:
                        cantidad_a_descontar = st.number_input("Cantidad de unidades utilizadas:", min_value=1, value=1, step=1)

            col_v1, col_v2 = st.columns(2)
            with col_v1:
                est_pago = st.selectbox("Condición:", ["Total Pagado", "Seña", "Fiado", "Presupuesto"])
                estado_guardar = "Total" if est_pago == "Total Pagado" else est_pago
            with col_v2:
                met_pago = st.selectbox("Medio de Cobro:", ["Efectivo", "Mercado Pago", "Transferencia", "Tarjeta", "Ninguno (Presupuesto)"])
            
            cliente_nombre = st.text_input("Nombre del Cliente (Opcional):")
            nota = st.text_input("Detalle del trabajo / Producto:")

            if st.button("Guardar e Imprimir Comprobante", type="primary"):
                detalle_final = nota
                if descuenta_stock and insumo_seleccionado:
                    detalle_final = f"{detalle_final} [Descontado {cantidad_a_descontar} un. de {insumo_seleccionado}]"
                
                detalle_final = f"Cliente: {cliente_nombre} | {detalle_final}" if cliente_nombre else detalle_final
                
                datos_insertar = {
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "cuenta": "Negocio",
                    "tipo": "Ingreso",
                    "monto": float(monto),
                    "categoria": categoria,
                    "detalle": detalle_final,
                    "estado_pago": estado_guardar,
                    "metodo_pago": met_pago,
                    "usuario_id": data_scope_id
                }
                supabase.table("historial").insert(datos_insertar).execute()
                
                # EJECUTAR EL DESCUENTO DE STOCK EN TIEMPO REAL
                if descuenta_stock and insumo_seleccionado:
                    fila_insumo = df_stock[df_stock["item"] == insumo_seleccionado].iloc[0]
                    id_insumo = int(fila_insumo["id"])
                    cant_actual = int(fila_insumo["cantidad"])
                    nueva_cantidad = max(0, cant_actual - cantidad_a_descontar)
                    
                    # Impactamos directo la reducción en Supabase
                    supabase.table("stock").update({"cantidad": nueva_cantidad}).eq("id", id_insumo).execute()
                
                fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                nom_c = cliente_nombre.strip() if cliente_nombre else "Cliente"
                
                if estado_guardar == "Total":
                    st.session_state.ultimo_comprobante = f"🧾 *COMPROBANTE DE PAGO*\n\n📅 *Fecha:* {fecha_hoy}\n👤 *Cliente:* {nom_c}\n💼 *Detalle:* {nota}\n💰 *Total Abonado:* $ {monto:,.2f}\n💳 *Medio:* {met_pago}\n\n¡Muchas gracias!"
                    st.session_state.tipo_comprobante = "¡Recibo guardado!"
                elif estado_guardar == "Seña":
                    st.session_state.ultimo_comprobante = f"📝 *COMPROBANTE DE SEÑA*\n\n📅 *Fecha:* {fecha_hoy}\n👤 *Cliente:* {nom_c}\n💼 *Detalle:* {nota}\n💵 *Monto Señado:* $ {monto:,.2f}\n💳 *Medio:* {met_pago}\n\n📌 *Estado pedido:* En producción."
                    st.session_state.tipo_comprobante = "¡Seña guardada!"
                elif estado_guardar == "Presupuesto":
                    st.session_state.ultimo_comprobante = f"📄 *PRESUPUESTO ESTIMADO*\n\n📅 *Fecha:* {fecha_hoy}\n👤 *Cliente:* {nom_c}\n💼 *Detalle:* {nota}\n💵 *Inversión Estimada:* $ {monto:,.2f}\n\n⚠️ Validez: 7 días."
                    st.session_state.tipo_comprobante = "¡Presupuesto guardado!"
                else:
                    st.session_state.ultimo_comprobante = f"🤝 *REGISTRO DE CUENTA CORRIENTE*\n\n📅 *Fecha:* {fecha_hoy}\n👤 *Cliente:* {nom_c}\n💼 *Detalle:* {nota}\n📉 *Saldo Pendiente:* $ {monto:,.2f}"
                    st.session_state.tipo_comprobante = "¡Fiado registrado!"
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
                datos_insertar = {"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Negocio", "tipo": "Gasto", "monto": float(monto), "categoria": categoria, "detalle": nota, "estado_pago": "Total", "metodo_pago": met_pago, "usuario_id": data_scope_id}
                supabase.table("historial").insert(datos_insertar).execute()
                st.rerun()

        elif opcion == "Retirar Sueldo" and rol_actual == "Admin":
            monto = st.number_input("Monto a extraer ($)", min_value=0.0, max_value=caja_negocio, step=50.0)
            if st.button("Confirmar Retiro", type="primary"):
                f = datetime.now().strftime("%Y-%m-%d")
                gasto_n = {"fecha": f, "cuenta": "Negocio", "tipo": "Gasto", "monto": float(monto), "categoria": "Retiro de Socio", "detalle": "Retiro ganancias", "estado_pago": "Total", "metodo_pago": "Efectivo", "usuario_id": data_scope_id}
                ingreso_p = {"fecha": f, "cuenta": "Personal", "tipo": "Ingreso", "monto": float(monto), "categoria": "Sueldo", "detalle": "Ingreso desde Negocio", "estado_pago": "Total", "metodo_pago": "Efectivo", "usuario_id": data_scope_id}
                supabase.table("historial").insert([gasto_n, ingreso_p]).execute()
                st.rerun()

        elif opcion == "Registrar Gasto Personal" and rol_actual == "Admin":
            monto = st.number_input("Monto ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", categorias_gasto_personal)
            nota = st.text_input("Detalle:")
            if st.button("Guardar Gasto Personal", type="primary"):
                datos_insertar = {"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Personal", "tipo": "Gasto", "monto": float(monto), "categoria": "Gasto Personal", "detalle": nota, "estado_pago": "Total", "metodo_pago": "Efectivo", "usuario_id": data_scope_id}
                supabase.table("historial").insert(datos_insertar).execute()
                st.rerun()

# --- 🧮 CALCULADORA DE COSTOS ---
elif seccion == "🧮 Calculadora de Costos" and rol_actual == "Admin":
    st.title("🧮 Calculadora de Costos y Precio de Venta")
    col_calc1, col_calc2 = st.columns([4, 3])
    with col_calc1:
        with st.container(border=True):
            st.subheader("📋 Datos del Producto")
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
            st.markdown("<p style='text-align: center; color: #94A3B8; font-weight: bold; font-size: 14px;'>PRECIO SUGERIDO AL CLIENTE</p>", unsafe_allow_html=True)
            st.markdown(f"<h1 style='text-align: center; color: #34D399; font-size: 50px; margin-top: 0px;'>$ {precio_venta_sugerido:,.2f}</h1>", unsafe_allow_html=True)
            st.markdown("---")
            st.write(f"📦 **Materiales:** $ {costo_materiales:,.2f}")
            st.write(f"👤 **Mano de Obra:** $ {costo_mano_obra:,.2f}")
            st.write(f"⚡ **Costos Fijos:** $ {costo_fijos_prod:,.2f}")
            st.markdown(f"📉 **Costo Base Total:** $ {costo_total_fabricacion:,.2f}")
            st.markdown(f"💰 **Tu Ganancia Neta ({porcentaje_ganancia}%):** $ {monto_ganancia_comercial:,.2f}")
            
            st.markdown("---")
            desc_prod = nombre_prod if nombre_prod.strip() else "Producto Personalizado"
            texto_presupuesto = f"📄 *PRESUPUESTO ESTIMADO*\n\n✨ *Detalle:* {desc_prod}\n💰 *Inversión Total:* $ {precio_venta_sugerido:,.2f}\n\n📌 *Condición:* Seña del 50% para iniciar producción. Validez por 7 días."
            st.text_area("Copiá esto para pegar en WhatsApp:", value=texto_presupuesto, height=140)

# --- 📦 STOCK DE INSUMOS ---
elif seccion == "📦 Stock de Insumos":
    st.title("📦 Control de Inventario Personalizado")
    
    with st.expander("➕ Agregar Nuevo Insumo al Stock"):
        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1: nombre_i = st.text_input("Nombre del material:")
        with col_i2: cant_i = st.number_input("Cantidad Inicial:", min_value=0, step=1)
        with col_i3: minimo_i = st.number_input("Stock Mínimo Alerta:", min_value=0, step=1)
        
        if st.button("Registrar Insumo", type="primary"):
            if nombre_i.strip():
                insumo = {"item": nombre_i.strip(), "cantidad": int(cant_i), "minimo": int(minimo_i), "usuario_id": data_scope_id}
                supabase.table("stock").insert(insumo).execute()
                st.rerun()

    st.markdown("---")
    if df_stock.empty:
        st.info("No tienes insumos cargados todavía.")
    else:
        for idx, row in df_stock.iterrows():
            es_critico = int(row["cantidad"]) <= int(row["minimo"])
            color_cartel = "🔴 Falta reponer / Stock Crítico" if es_critico else "🟢 Stock Ok"
            
            with st.container(border=True):
                c_name, c_status, c_cant, c_actions, c_del = st.columns([3, 2, 2, 3, 1])
                with c_name: st.markdown(f"**{row['item']}**")
                with c_status: 
                    if es_critico: st.error(color_cartel)
                    else: st.success(color_cartel)
                with c_cant: st.markdown(f"Unidades: `{row['cantidad']}` (Mín: {row['minimo']})")
                with c_actions:
                    btn_menos, btn_mas = st.columns(2)
                    with btn_menos: 
                        if st.button("➖ Usar 1", key=f"min_{row['id']}"):
                            nueva_cant = max(0, int(row["cantidad"]) - 1)
                            supabase.table("stock").update({"cantidad": nueva_cant}).eq("id", int(row["id"])).execute()
                            st.rerun()
                    with btn_mas:
                        if st.button("➕ Sumar 1", key=f"add_{row['id']}"):
                            nueva_cant = int(row["cantidad"]) + 1
                            supabase.table("stock").update({"cantidad": nueva_cant}).eq("id", int(row["id"])).execute()
                            st.rerun()
                with c_del:
                    if st.button("🗑️", key=f"del_insumo_{row['id']}"):
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
        with res1: st.metric("Unidades mensuales necesarias:", f"{int(unidades)} un.")
        with res2: st.metric("Facturación mínima requerida:", f"${unidades * precio_promedio:,.2f}")

# --- 🎯 METAS DE AHORRO ---
elif seccion == "🎯 Metas de Ahorro" and rol_actual == "Admin":
    st.title("🎯 Alcancías Virtuales")
    with st.expander("➕ Crear Nueva Meta de Ahorro"):
        col_m1, col_m2 = st.columns(2)
        with col_m1: nombre_m = st.text_input("¿Para qué estás ahorrando?:")
        with col_m2: monto_m = st.number_input("Monto Meta Necesario ($):", min_value=1.0, step=1000.0)
        if st.button("Crear Meta", type="primary"):
            if nombre_m.strip():
                meta = {"meta": nombre_m.strip(), "objetivo": float(monto_m), "acumulado": 0.0, "usuario_id": data_scope_id}
                supabase.table("metas").insert(meta).execute()
                st.rerun()

# --- ⚙️ CONFIGURACIÓN DE CATEGORÍAS ---
elif seccion == "⚙️ Configurar Categorías" and rol_actual == "Admin":
    st.title("⚙️ Gestión Personalizada de Categorías")
    with st.container(border=True):
        st.subheader("➕ Agregar Nueva Categoría")
        col_c1, col_c2 = st.columns(2)
        with col_c1: tipo_nueva = st.selectbox("¿A qué módulo pertenece?", ["Ingreso", "Gasto Negocio", "Gasto Personal"])
        with col_c2: nombre_nueva = st.text_input("Nombre de la categoría:")
        if st.button("Guardar Nueva Categoría", type="primary"):
            if nombre_nueva.strip():
                nueva_cat = {"tipo_categoria": tipo_nueva, "nombre_categoria": nombre_nueva.strip(), "usuario_id": data_scope_id}
                supabase.table("categorias").insert(nueva_cat).execute()
                st.rerun()

# --- 📊 MI CIERRE DE CAJA ---
elif seccion == "📊 Mi Cierre de Caja":
    st.title("📊 Resumen del Día (Cierre de Caja)")
    
    fecha_hoy_db = datetime.now().strftime("%Y-%m-%d")
    fecha_hoy_legible = datetime.now().strftime("%d/%m/%Y")
    st.markdown(f"### 📆 Movimientos del día de hoy: **{fecha_hoy_legible}**")
    
    if df_historial.empty:
        st.info("No se registran movimientos cargados hoy.")
    else:
        df_historial["fecha_txt"] = pd.to_datetime(df_historial["fecha"]).dt.strftime("%Y-%m-%d")
        df_hoy = df_historial[df_historial["fecha_txt"] == fecha_hoy_db]
        
        if df_hoy.empty:
            st.info("Todavía no se cargaron operaciones en el transcurso del día de hoy.")
        else:
            hoy_efectivo = df_hoy[(df_hoy["tipo"] == "Ingreso") & (df_hoy["metodo_pago"] == "Efectivo")]["monto"].sum()
            hoy_mp = df_hoy[(df_hoy["tipo"] == "Ingreso") & (df_hoy["metodo_pago"] == "Mercado Pago")]["monto"].sum()
            hoy_transf = df_hoy[(df_hoy["tipo"] == "Ingreso") & (df_hoy["metodo_pago"] == "Transferencia")]["monto"].sum()
            hoy_tarjeta = df_hoy[(df_hoy["tipo"] == "Ingreso") & (df_hoy["metodo_pago"] == "Tarjeta")]["monto"].sum()
            
            hoy_gastos = df_hoy[df_hoy["tipo"] == "Gasto"]["monto"].sum()
            total_recaudado_hoy = hoy_efectivo + hoy_mp + hoy_transf + hoy_tarjeta
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                with st.container(border=True): st.markdown(f"<p style='color: #FBBF24; font-size:13px; font-weight:bold; margin-bottom:2px;'>💵 EFECTIVO EN CAJA</p><h3>$ {hoy_efectivo:,.2f}</h3>", unsafe_allow_html=True)
            with c2:
                with st.container(border=True): st.markdown(f"<p style='color: #38BDF8; font-size:13px; font-weight:bold; margin-bottom:2px;'>💙 MERCADO PAGO</p><h3>$ {hoy_mp:,.2f}</h3>", unsafe_allow_html=True)
            with c3:
                with st.container(border=True): st.markdown(f"<p style='color: #A78BFA; font-size:13px; font-weight:bold; margin-bottom:2px;'>🏛️ TRANSFERENCIAS</p><h3>$ {hoy_transf:,.2f}</h3>", unsafe_allow_html=True)
            with c4:
                with st.container(border=True): st.markdown(f"<p style='color: #34D399; font-size:13px; font-weight:bold; margin-bottom:2px;'>💰 TOTAL RECAUDADO</p><h3>$ {total_recaudado_hoy:,.2f}</h3>", unsafe_allow_html=True)
                
            st.markdown(f"<p style='color: #F87171; font-size:14px; margin-top:5px; font-weight:bold;'>⚠️ Gastos del taller registrados hoy:</p> $ {hoy_gastos:,.2f}", unsafe_allow_html=True)
            st.markdown("<br><hr style='border-color: #334155;'><br>", unsafe_allow_html=True)
            
            st.subheader("📋 Detalle de operaciones del turno:")
            for idx, r in df_hoy[::-1].iterrows():
                tipo_icono = "📥 Ingreso" if r["tipo"] == "Ingreso" else "📤 Gasto"
                with st.container(border=True):
                    col_b1, col_b2, col_b3 = st.columns([2, 5, 2])
                    col_b1.markdown(f"**{tipo_icono}** | `{r['metodo_pago']}`")
                    col_b2.markdown(f"*{r['categoria']}* — {r['detalle']}")
                    col_b3.markdown(f"<h4 style='text-align:right; margin:0px;'>$ {float(r['monto']):,.2f}</h4>", unsafe_allow_html=True)

# --- 👥 GESTIÓN DE PERSONAL ---
elif seccion == "👥 Personal del Taller" and rol_actual == "Admin":
    st.title("👥 Panel de Control de Colaboradores")
    st.subheader("Añadir accesos para tus empleados de forma autónoma")
    
    with st.container(border=True):
        st.markdown("### ✨ Registrar Nuevo Colaborador")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1: nombre_emp = st.text_input("Nombre del Empleado (Ej: Juan Perez):").strip()
        with col_p2: email_emp = st.text_input("Correo de Trabajo (Ej: juan@taller.com):").strip().lower()
        with col_p3: pass_emp = st.text_input("Creale una Contraseña:", type="password")
        
        if st.button("Registrar Colaborador en el Taller", type="primary"):
            if nombre_emp and email_emp and pass_emp:
                try:
                    check_mail = supabase.table("usuarios").select("id").eq("email", email_emp).execute()
                    if check_mail.data:
                        st.error("❌ Este correo ya está registrado por otro usuario.")
                    else:
                        hash_seguro_emp = encriptar_contrasena(pass_emp)
                        nuevo_empleado = {
                            "nombre_taller": st.session_state.nombre_taller,
                            "email": email_emp,
                            "contrasena": hash_seguro_emp,
                            "rol": "Empleado",
                            "owner_id": u_id
                        }
                        supabase.table("usuarios").insert(nuevo_empleado).execute()
                        st.success(f"🎉 ¡Acceso creado con éxito para {nombre_emp}!")
                except Exception as e:
                    st.error(f"Error al guardar colaborador: {e}")
            else:
                st.warning("Por favor, completa todos los campos del formulario.")
                
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Colaboradores con acceso activo:")
    
    try:
        res_team = supabase.table("usuarios").select("*").eq("owner_id", u_id).eq("rol", "Empleado").execute()
        if res_team.data:
            for emp in res_team.data:
                with st.container(border=True):
                    col_t1, col_t2, col_t3 = st.columns([4, 4, 2])
                    with col_t1: st.markdown(f"👤 **{emp['email'].split('@')[0].capitalize()}**")
                    with col_t2: st.caption(f"Correo de acceso: {emp['email']}")
                    with col_t3:
                        if st.button("Revocar Acceso 🗑️", key=f"del_emp_{emp['id']}", use_container_width=True):
                            supabase.table("usuarios").delete().eq("id", int(emp['id'])).execute()
                            st.success("Acceso revocado.")
                            st.rerun()
        else:
            st.info("Todavía no diste de alta a ningún empleado en tu equipo.")
    except Exception:
        st.info("No se pudo cargar la nómina de personal activo.")