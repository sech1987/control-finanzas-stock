import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(layout="wide", page_title="Finanzas & Stock Manager Pro", page_icon="📈")

# --- 🔌 CONEXIÓN CON GOOGLE SHEETS (BASE DE DATOS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_gsheets(pestana):
    try:
        df = conn.read(worksheet=pestana, ttl="0d")
        if df.empty or df.columns.tolist() == [0] or df.columns.tolist() == [""]:
            if pestana == "historial":
                return pd.DataFrame(columns=["fecha", "cuenta", "tipo", "monto", "categoria", "detalle", "estado_pago", "metodo_pago"])
            elif pestana == "stock":
                return pd.DataFrame(columns=["item", "cantidad", "minimo"])
            elif pestana == "metas":
                return pd.DataFrame(columns=["meta", "objetivo", "acumulado"])
            elif pestana == "categorias":
                return pd.DataFrame(columns=["tipo_categoria", "nombre_categoria"])
        return df
    except Exception:
        if pestana == "historial":
            return pd.DataFrame(columns=["fecha", "cuenta", "tipo", "monto", "categoria", "detalle", "estado_pago", "metodo_pago"])
        elif pestana == "stock":
            return pd.DataFrame(columns=["item", "cantidad", "minimo"])
        elif pestana == "metas":
            return pd.DataFrame(columns=["meta", "objetivo", "acumulado"])
        elif pestana == "categorias":
            return pd.DataFrame(columns=["tipo_categoria", "nombre_categoria"])

def guardar_datos_gsheets(df, pestana):
    # Forzar que no se guarden índices numéricos raros
    conn.update(worksheet=pestana, data=df)

# Carga de datos en tiempo real desde la nube
df_historial = cargar_datos_gsheets("historial")
df_stock = cargar_datos_gsheets("stock")
df_metas = cargar_datos_gsheets("metas")
df_cat_cloud = cargar_datos_gsheets("categorias")

# --- 📋 PROCESAMIENTO DE CATEGORÍAS ---
# Si la nube no tiene categorías, usamos las del taller por defecto para arrancar
if df_cat_cloud.empty:
    categorias_ingreso = ["Venta Producto", "Servicio", "Diseño", "Otros"]
    categorias_gasto_negocio = ["Insumos", "Publicidad", "Herramientas", "Otros"]
    categorias_gasto_personal = ["Alimentos", "Servicios", "Ocio", "Otros"]
else:
    categorias_ingreso = df_cat_cloud[df_cat_cloud["tipo_categoria"] == "Ingreso"]["nombre_categoria"].tolist()
    categorias_gasto_negocio = df_cat_cloud[df_cat_cloud["tipo_categoria"] == "Gasto Negocio"]["nombre_categoria"].tolist()
    categorias_gasto_personal = df_cat_cloud[df_cat_cloud["tipo_categoria"] == "Gasto Personal"]["nombre_categoria"].tolist()
    
    # Asegurar que siempre tengan al menos "Otros" por seguridad
    if not categorias_ingreso: categorias_ingreso = ["Otros"]
    if not categorias_gasto_negocio: categorias_gasto_negocio = ["Otros"]
    if not categorias_gasto_personal: categorias_gasto_personal = ["Otros"]

# --- 🧮 CÁLCULO DE SALDOS AL VUELO ---
caja_negocio = 0.0
billetera_personal = 0.0

if not df_historial.empty:
    df_historial["monto"] = df_historial["monto"].astype(float)
    ingresos_n = df_historial[(df_historial["cuenta"] == "Negocio") & (df_historial["tipo"] == "Ingreso") & (df_historial["estado_pago"] != "Presupuesto")]["monto"].sum()
    gastos_n = df_historial[(df_historial["cuenta"] == "Negocio") & (df_historial["tipo"] == "Gasto")]["monto"].sum()
    caja_negocio = ingresos_n - gastos_n

    ingresos_p = df_historial[(df_historial["cuenta"] == "Personal") & (df_historial["tipo"] == "Ingreso")]["monto"].sum()
    gastos_p = df_historial[(df_historial["cuenta"] == "Personal") & (df_historial["tipo"] == "Gasto")]["monto"].sum()
    billetera_personal = ingresos_p - gastos_p

# --- 🔐 SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #4F46E5;'>💼 Finanzas & Stock Manager Pro</h1>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.container(border=True):
            st.markdown("<h3 style='margin-top:0px;'>🔒 Iniciar Sesión</h3>", unsafe_allow_html=True)
            usuario = st.text_input("Usuario")
            contrasena = st.text_input("Contraseña", type="password") 
            if st.button("Ingresar al Panel", use_container_width=True, type="primary"):
                if usuario == "admin" and contrasena == "1234":
                    st.session_state.autenticado = True
                    st.rerun()
                else: 
                    st.error("Usuario o contraseña incorrectos")
    st.stop()

# --- 🔓 NAVEGACIÓN ---
with st.sidebar:
    st.markdown("<h2 style='color: #4F46E5; margin-top: 0px;'>⚡ Panel de Control</h2>", unsafe_allow_html=True)
    if st.button("Cerrar Sesión 🔓", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()
    st.markdown("---")
    
    seccion = st.radio(
        "Navegación:",
        ["🏠 Dashboard General", "📝 Nueva Operación", "📦 Stock de Insumos", "📉 Punto de Equilibrio", "🎯 Metas de Ahorro", "⚙️ Configurar Categorías"]
    )
    st.markdown("---")
    st.caption("FSM Pro - Sincronización Multi-Dispositivo")

# --- 🏠 DASHBOARD GENERAL ---
if seccion == "🏠 Dashboard General":
    st.markdown("<h1 style='color: #4F46E5; margin-bottom: 0px;'>🏠 Panel de Control</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 16px;'>Sincronizado en la nube en tiempo real.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    if caja_negocio < 10000:
        st.warning("⚠️ **Alerta de Liquidez:** La caja del negocio está por debajo del mínimo recomendado ($10,000).")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("<p style='color: #94A3B8; font-size: 14px; font-weight: bold; letter-spacing: 1px; margin-bottom: 5px;'>FONDOS DISPONIBLES EMPRENDIMIENTO</p>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color: #38BDF8; font-size: 42px; margin-top: 0px; margin-bottom: 5px;'>$ {caja_negocio:,.2f}</h2>", unsafe_allow_html=True)
            
    with col2:
        with st.container(border=True):
            st.markdown("<p style='color: #94A3B8; font-size: 14px; font-weight: bold; letter-spacing: 1px; margin-bottom: 5px;'>FINANZAS PERSONALES (LIBRE)</p>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color: #34D399; font-size: 42px; margin-top: 0px; margin-bottom: 5px;'>$ {billetera_personal:,.2f}</h2>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("💡 Distribución Interna Recomendada (Porcentajes del Taller)")
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
        st.info("No hay movimientos registrados en la nube todavía.")
    else:
        df_historial["fecha"] = pd.to_datetime(df_historial["fecha"])
        df_historial["Mes"] = df_historial["fecha"].dt.strftime("%Y-%m")
        
        mes_sel = st.selectbox("📆 Seleccionar Período de Análisis:", sorted(df_historial["Mes"].unique(), reverse=True))
        df_mes = df_historial[df_historial["Mes"] == mes_sel]
        
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.markdown("### 📊 Resumen Gastos del Negocio")
            df_n_gasto = df_mes[(df_mes["cuenta"] == "Negocio") & (df_mes["tipo"] == "Gasto")]
            if not df_n_gasto.empty: st.bar_chart(df_n_gasto.groupby("categoria")["monto"].sum())
            else: st.caption("Sin egresos este mes.")
        with g_col2:
            st.markdown("### 📊 Resumen Gastos Personales")
            df_p_gasto = df_mes[(df_mes["cuenta"] == "Personal") & (df_mes["tipo"] == "Gasto")]
            if not df_p_gasto.empty: st.bar_chart(df_p_gasto.groupby("categoria")["monto"].sum())
            else: st.caption("Sin egresos este mes.")

        st.markdown("<br>", unsafe_allow_html=True)
        tab_ingresos, tab_egresos = st.tabs(["📥 Historial de INGRESOS (Ventas)", "📤 Historial de EGRESOS (Gastos)"])
        
        with tab_ingresos:
            filto_p = st.selectbox("🔍 Filtrar Ingresos por Estado:", ["Todos", "💰 Total Pagado", "📝 Seña", "🤝 Fiado", "📄 Presupuesto"], key="f_pago")
            df_ingresos = df_mes[df_mes["tipo"] == "Ingreso"]
            if filto_p != "Todos":
                estado_limpio = filto_p.split(" ")[1]
                df_ingresos = df_ingresos[df_ingresos["estado_pago"] == ("Total" if estado_limpio == "Total" else estado_limpio)]
            
            for idx, row in df_ingresos[::-1].iterrows():
                with st.container(border=True):
                    col_h1, col_h2, col_h3, col_h4 = st.columns([1, 2, 4, 1])
                    with col_h1: st.caption(str(row["fecha"].strftime("%Y-%m-%d")))
                    with col_h2: st.markdown(f"**$ {row['monto']:,.2f}**")
                    with col_h3:
                        st.markdown(f"🔹 *{row['categoria']}* — {row['detalle']}")
                        st.caption(f"Condición: **{row['estado_pago']}** | Medio: **{row['metodo_pago']}**")
                    with col_h4:
                        if st.button("🗑️", key=f"del_ing_{idx}"):
                            df_historial = df_historial.drop(idx)
                            guardar_datos_gsheets(df_historial, "historial")
                            st.rerun()

        with tab_egresos:
            df_egresos = df_mes[df_mes["tipo"] == "Gasto"]
            for idx, row in df_egresos[::-1].iterrows():
                with st.container(border=True):
                    col_e1, col_e2, col_e3, col_e4 = st.columns([1, 2, 4, 1])
                    with col_e1: st.caption(str(row["fecha"].strftime("%Y-%m-%d")))
                    with col_e2: st.markdown(f"**$ {row['monto']:,.2f}**")
                    with col_e3:
                        lbl = "⚙️ GASTO TALLER" if row["cuenta"] == "Negocio" else "👤 PERSONAL"
                        st.markdown(f"**{lbl}** | *{row['categoria']}*\n\n{row['detalle']}")
                    with col_e4:
                        if st.button("🗑️", key=f"del_egr_{idx}"):
                            df_historial = df_historial.drop(idx)
                            guardar_datos_gsheets(df_historial, "historial")
                            st.rerun()

# --- 📝 NUEVA OPERACIÓN ---
elif seccion == "📝 Nueva Operación":
    st.title("📝 Carga de Movimientos")
    opcion = st.selectbox("¿Qué vas a registrar hoy?", ["Registrar Venta / Presupuesto", "Registrar Gasto Negocio", "Retirar Sueldo", "Registrar Gasto Personal"])
    
    with st.container(border=True):
        if opcion == "Registrar Venta / Presupuesto":
            if "ultimo_comprobante" not in st.session_state:
                st.session_state.ultimo_comprobante = None
                st.session_state.tipo_comprobante = None

            monto = st.number_input("Monto total ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", categorias_ingreso)
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                est_pago = st.selectbox("Condición:", ["Total Pagado", "Seña", "Fiado", "Presupuesto"])
                estado_guardar = "Total" if est_pago == "Total Pagado" else est_pago
            with col_v2:
                met_pago = st.selectbox("Medio de Cobro:", ["Efectivo", "Mercado Pago", "Transferencia", "Tarjeta", "Ninguno (Presupuesto)"])
            
            cliente_nombre = st.text_input("Nombre del Cliente (Opcional):")
            nota = st.text_input("Detalle del trabajo / Producto:")
            
            st.markdown("---")
            descuenta_stock = st.checkbox("¿Esta venta consumió algún insumo del stock?")
            insumo_seleccionado = None
            cantidad_a_descontar = 0
            
            if descuenta_stock and not df_stock.empty:
                insumo_seleccionado = st.selectbox("Selecciona el insumo:", df_stock["item"].tolist())
                cantidad_a_descontar = st.number_input("Cantidad utilizada:", min_value=1, step=1)

            if st.button("Guardar e Imprimir Comprobante", type="primary"):
                detalle_final = nota
                if descuenta_stock and insumo_seleccionado is not None:
                    idx_insumo = df_stock[df_stock["item"] == insumo_seleccionado].index[0]
                    df_stock.at[idx_insumo, "cantidad"] = max(0, int(df_stock.at[idx_insumo, "cantidad"]) - cantidad_a_descontar)
                    guardar_datos_gsheets(df_stock, "stock")
                    detalle_final += f" (Consumió {cantidad_a_descontar} un. de {insumo_seleccionado})"
                
                detalle_final = f"Cliente: {cliente_nombre} | {detalle_final}" if cliente_nombre else detalle_final
                
                nueva_fila = pd.DataFrame([{"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Negocio", "tipo": "Ingreso", "monto": float(monto), "categoria": categoria, "detalle": detalle_final, "estado_pago": estado_guardar, "metodo_pago": met_pago}])
                df_historial = pd.concat([df_historial, nueva_fila], ignore_index=True)
                guardar_datos_gsheets(df_historial, "historial")
                
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
                nueva_fila = pd.DataFrame([{"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Negocio", "tipo": "Gasto", "monto": float(monto), "categoria": categoria, "detalle": nota, "estado_pago": "Total", "metodo_pago": met_pago}])
                df_historial = pd.concat([df_historial, nueva_fila], ignore_index=True)
                guardar_datos_gsheets(df_historial, "historial")
                st.rerun()

        elif opcion == "Retirar Sueldo":
            monto = st.number_input("Monto a extraer ($)", min_value=0.0, max_value=caja_negocio, step=50.0)
            if st.button("Confirmar Retiro", type="primary"):
                f = datetime.now().strftime("%Y-%m-%d")
                fila_g = pd.DataFrame([{"fecha": f, "cuenta": "Negocio", "tipo": "Gasto", "monto": float(monto), "categoria": "Retiro de Socio", "detalle": "Retiro ganancias", "estado_pago": "Total", "metodo_pago": "Efectivo"}])
                fila_i = pd.DataFrame([{"fecha": f, "cuenta": "Personal", "tipo": "Ingreso", "monto": float(monto), "categoria": "Sueldo", "detalle": "Ingreso desde Negocio", "estado_pago": "Total", "metodo_pago": "Efectivo"}])
                df_historial = pd.concat([df_historial, fila_g, fila_i], ignore_index=True)
                guardar_datos_gsheets(df_historial, "historial")
                st.rerun()

        elif opcion == "Registrar Gasto Personal":
            monto = st.number_input("Monto ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", categorias_gasto_personal)
            nota = st.text_input("Detalle:")
            if st.button("Guardar Gasto Personal", type="primary"):
                nueva_fila = pd.DataFrame([{"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Personal", "tipo": "Gasto", "monto": float(monto), "categoria": categoria, "detalle": nota, "estado_pago": "Total", "metodo_pago": "Efectivo"}])
                df_historial = pd.concat([df_historial, nueva_fila], ignore_index=True)
                guardar_datos_gsheets(df_historial, "historial")
                st.rerun()

# --- 📦 STOCK DE INSUMOS ---
elif seccion == "📦 Stock de Insumos":
    st.title("📦 Control de Inventario e Insumos Cloud")
    
    with st.expander("➕ Agregar Nuevo Insumo al Stock"):
        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1: nombre_i = st.text_input("Nombre del material:")
        with col_i2: cant_i = st.number_input("Cantidad Inicial:", min_value=0, step=1)
        with col_i3: minimo_i = st.number_input("Stock Mínimo Alerta:", min_value=0, step=1)
        
        if st.button("Registrar Insumo", type="primary"):
            if nombre_i.strip():
                nueva_fila = pd.DataFrame([{"item": nombre_i.strip(), "cantidad": int(cant_i), "minimo": int(minimo_i)}])
                df_stock = pd.concat([df_stock, nueva_fila], ignore_index=True)
                guardar_datos_gsheets(df_stock, "stock")
                st.rerun()

    st.markdown("---")
    if df_stock.empty:
        st.info("No tienes insumos cargados en la nube todavía.")
    else:
        for idx, row in df_stock.iterrows():
            es_critico = int(row["cantidad"]) <= int(row["minimo"])
            color_cartel = "🔴 Falta reponer" if es_critico else "🟢 Stock Ok"
            
            with st.container(border=True):
                c_name, c_status, c_cant, c_actions, c_del = st.columns([3, 2, 2, 3, 1])
                with c_name: st.markdown(f"**{row['item']}**")
                with c_status: st.caption(color_cartel)
                with c_cant: st.markdown(f"Unidades: `{row['cantidad']}` (Mín: {row['minimo']})")
                with c_actions:
                    btn_menos, btn_mas = st.columns(2)
                    with btn_menos: 
                        if st.button("➖ Usar 1", key=f"min_{idx}"):
                            df_stock.at[idx, "cantidad"] = max(0, int(row["cantidad"]) - 1)
                            guardar_datos_gsheets(df_stock, "stock")
                            st.rerun()
                    with btn_mas:
                        if st.button("➕ Sumar 1", key=f"add_{idx}"):
                            df_stock.at[idx, "cantidad"] = int(row["cantidad"]) + 1
                            guardar_datos_gsheets(df_stock, "stock")
                            st.rerun()
                with c_del:
                    if st.button("🗑️", key=f"del_insumo_{idx}"):
                        df_stock = df_stock.drop(idx)
                        guardar_datos_gsheets(df_stock, "stock")
                        st.rerun()

# --- 📉 PUNTO DE EQUILIBRIO ---
elif seccion == "📉 Punto de Equilibrio":
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
elif seccion == "🎯 Metas de Ahorro":
    st.title("🎯 Alcancías Virtuales en la Nube")
    
    with st.expander("➕ Crear Nueva Meta de Ahorro"):
        col_m1, col_m2 = st.columns(2)
        with col_m1: nombre_m = st.text_input("¿Para qué estás ahorrando?:")
        with col_m2: monto_m = st.number_input("Monto Meta Necesario ($):", min_value=1.0, step=1000.0)
        
        if st.button("Crear Meta", type="primary"):
            if nombre_m.strip():
                nueva_fila = pd.DataFrame([{"meta": nombre_m.strip(), "objetivo": float(monto_m), "acumulado": 0.0}])
                df_metas = pd.concat([df_metas, nueva_fila], ignore_index=True)
                guardar_datos_gsheets(df_metas, "metas")
                st.rerun()

    st.markdown("---")
    if df_metas.empty:
        st.info("No tienes metas creadas todavía.")
    else:
        for idx, row in df_metas.iterrows():
            porcentaje = min(float(row["acumulado"]) / float(row["objetivo"]), 1.0) if float(row["objetivo"]) > 0 else 0.0
            with st.container(border=True):
                st.markdown(f"### 🚀 {row['meta']}")
                st.write(f"Progreso: **${float(row['acumulado']):,.2f}** de **${float(row['objetivo']):,.2f}**")
                st.progress(porcentaje)
                
                col_b1, col_b2, col_b3 = st.columns([2, 2, 4])
                with col_b1:
                    monto_poner = st.number_input("Sumar dinero ($):", min_value=0.0, max_value=billetera_personal, step=100.0, key=f"in_{idx}")
                    if st.button("📥 Sumar", key=f"btn_in_{idx}"):
                        df_metas.at[idx, "acumulado"] = float(row["acumulado"]) + monto_poner
                        nueva_f = pd.DataFrame([{"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Personal", "tipo": "Gasto", "monto": float(monto_poner), "categoria": "Ahorro", "detalle": f"Destinado a meta: {row['meta']}", "estado_pago": "Total", "metodo_pago": "Efectivo"}])
                        df_historial = pd.concat([df_historial, nueva_f], ignore_index=True)
                        guardar_datos_gsheets(df_historial, "historial")
                        guardar_datos_gsheets(df_metas, "metas")
                        st.rerun()
                with col_b2:
                    monto_sacar = st.number_input("Retirar dinero ($):", min_value=0.0, max_value=float(row["acumulado"]), step=100.0, key=f"out_{idx}")
                    if st.button("📤 Retirar", key=f"btn_out_{idx}"):
                        df_metas.at[idx, "acumulado"] = float(row["acumulado"]) - monto_sacar
                        nueva_f = pd.DataFrame([{"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Personal", "tipo": "Ingreso", "monto": float(monto_sacar), "categoria": "Ahorro", "detalle": f"Retiro de meta: {row['meta']}", "estado_pago": "Total", "metodo_pago": "Efectivo"}])
                        df_historial = pd.concat([df_historial, nueva_f], ignore_index=True)
                        guardar_datos_gsheets(df_historial, "historial")
                        guardar_datos_gsheets(df_metas, "metas")
                        st.rerun()
                with col_b3:
                    st.write("<br>", unsafe_allow_html=True)
                    if st.button("🗑️ Eliminar Meta", key=f"del_meta_{idx}"):
                        df_metas = df_metas.drop(idx)
                        guardar_datos_gsheets(df_metas, "metas")
                        st.rerun()

# --- ⚙️ CONFIGURACIÓN DE CATEGORÍAS (LA PESTAÑA QUE FALTABA) ---
elif seccion == "⚙️ Configurar Categorías":
    st.title("⚙️ Gestión Personalizada de Categorías")
    st.markdown("Agregá o eliminá las categorías de tu negocio. Se actualizarán al instante en todos tus dispositivos conectados.")
    
    with st.container(border=True):
        st.subheader("➕ Agregar Nueva Categoría")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            tipo_nueva = st.selectbox("¿A qué módulo pertenece?", ["Ingreso", "Gasto Negocio", "Gasto Personal"])
        with col_c2:
            nombre_nueva = st.text_input("Nombre de la categoría (Ej: Impresiones, Yerba, Envíos):")
            
        if st.button("Guardar Nueva Categoría", type="primary"):
            if nombre_nueva.strip():
                nueva_cat_df = pd.DataFrame([{"tipo_categoria": tipo_nueva, "nombre_categoria": nombre_nueva.strip()}])
                df_cat_cloud = pd.concat([df_cat_cloud, nueva_cat_df], ignore_index=True)
                guardar_datos_gsheets(df_cat_cloud, "categorias")
                st.toast(f"✅ Categoría '{nombre_nueva}' agregada")
                st.rerun()
                
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Categorías Activas Actualmente")
    
    if df_cat_cloud.empty:
        st.info("Actualmente estás usando las categorías estándar del taller. Agregá una arriba para empezar a personalizar tus libros.")
    else:
        tab_ver_i, tab_ver_gn, tab_ver_gp = st.tabs(["📥 Categorías de Ventas", "🛠️ Categorías de Taller", "🏠 Categorías Personales"])
        
        with tab_ver_i:
            cats = df_cat_cloud[df_cat_cloud["tipo_categoria"] == "Ingreso"]
            if cats.empty: st.caption("Usando lista por defecto.")
            for idx, r in cats.iterrows():
                col_v_n, col_v_b = st.columns([5, 1])
                col_v_n.markdown(f"▪️ {r['nombre_categoria']}")
                if col_v_b.button("🗑️", key=f"del_cat_{idx}"):
                    df_cat_cloud = df_cat_cloud.drop(idx)
                    guardar_datos_gsheets(df_cat_cloud, "categorias")
                    st.rerun()
                    
        with tab_ver_gn:
            cats = df_cat_cloud[df_cat_cloud["tipo_categoria"] == "Gasto Negocio"]
            if cats.empty: st.caption("Usando lista por defecto.")
            for idx, r in cats.iterrows():
                col_v_n, col_v_b = st.columns([5, 1])
                col_v_n.markdown(f"▪️ {r['nombre_categoria']}")
                if col_v_b.button("🗑️", key=f"del_cat_{idx}"):
                    df_cat_cloud = df_cat_cloud.drop(idx)
                    guardar_datos_gsheets(df_cat_cloud, "categorias")
                    st.rerun()
                    
        with tab_ver_gp:
            cats = df_cat_cloud[df_cat_cloud["tipo_categoria"] == "Gasto Personal"]
            if cats.empty: st.caption("Usando lista por defecto.")
            for idx, r in cats.iterrows():
                col_v_n, col_v_b = st.columns([5, 1])
                col_v_n.markdown(f"▪️ {r['nombre_categoria']}")
                if col_v_b.button("🗑️", key=f"del_cat_{idx}"):
                    df_cat_cloud = df_cat_cloud.drop(idx)
                    guardar_datos_gsheets(df_cat_cloud, "categorias")
                    st.rerun()