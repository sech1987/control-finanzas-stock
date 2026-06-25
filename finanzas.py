import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

ARCHIVO_DATOS = "datos_finanzas.json"

st.set_page_config(layout="wide", page_title="Finanzas & Stock Manager Pro", page_icon="📈")

# --- MEMORIA INTEGRADA CON PARCHE INTELIGENTE ---
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r") as archivo:
            datos = json.load(archivo)
            
        # Parches automáticos por compatibilidad de nuevas funciones
        if "stock_insumos" not in datos:
            datos["stock_insumos"] = []
        if "metas_ahorro" not in datos:
            datos["metas_ahorro"] = []
        if "categorias_negocio_ingreso" not in datos:
            datos["categorias_negocio_ingreso"] = ["Venta Producto", "Servicio"]
        if "categorias_negocio_gasto" not in datos:
            datos["categorias_negocio_gasto"] = ["Insumos", "Publicidad", "Herramientas"]
        if "categorias_personal_gasto" not in datos:
            datos["categorias_personal_gasto"] = ["Alimentos", "Servicios", "Ocio"]
            
        return datos
    else:
        return {
            "caja_negocio": 0.0, 
            "billetera_personal": 0.0,
            "costos_fijos_negocio": 50000.0,
            "categorias_negocio_ingreso": ["Venta Producto", "Servicio"],
            "categorias_negocio_gasto": ["Insumos", "Publicidad", "Herramientas"],
            "categorias_personal_gasto": ["Alimentos", "Servicios", "Ocio"],
            "stock_insumos": [], 
            "metas_ahorro": [],   
            "historial": []
        }

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, "w") as archivo:
        json.dump(datos, archivo, indent=4)

if "saldos" not in st.session_state:
    st.session_state.saldos = cargar_datos()

saldos = st.session_state.saldos

# --- 🔐 SISTEMA DE LOGIN DE ACCESO ---
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

# --- 🔓 DISEÑO DE LA BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.markdown("<h2 style='color: #4F46E5; margin-top: 0px;'>⚡ Panel de Control</h2>", unsafe_allow_html=True)
    if st.button("Cerrar Sesión 🔓", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()
    st.markdown("---")
    
    seccion = st.radio(
        "Navegación:",
        ["🏠 Dashboard General", "📝 Nueva Operación", "📦 Stock de Insumos", "📉 Punto de Equilibrio", "🎯 Metas de Ahorro", "⚙️ Ajustes"]
    )
    st.markdown("---")
    st.caption("FSM Pro - Edición Comercial")

# --- SECCIÓN 1: DASHBOARD GENERAL ---
if seccion == "🏠 Dashboard General":
    st.markdown("<h1 style='color: #4F46E5; margin-bottom: 0px;'>🏠 Panel de Control</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 16px;'>Estado de tus cajas y rendimiento en tiempo real.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    if saldos["caja_negocio"] < 10000:
        st.warning("⚠️ **Alerta de Liquidez:** La caja del negocio está por debajo del mínimo recomendado ($10,000).")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("<p style='color: #94A3B8; font-size: 14px; font-weight: bold; letter-spacing: 1px; margin-bottom: 5px;'>FONDOS DISPONIBLES EMPRENDIMIENTO</p>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color: #38BDF8; font-size: 42px; margin-top: 0px; margin-bottom: 5px;'>$ {saldos['caja_negocio']:,.2f}</h2>", unsafe_allow_html=True)
            st.markdown("<span style='color: #64748B; font-size: 13px;'>Disponibles para compras de insumos y operación.</span>", unsafe_allow_html=True)
            
    with col2:
        with st.container(border=True):
            st.markdown("<p style='color: #94A3B8; font-size: 14px; font-weight: bold; letter-spacing: 1px; margin-bottom: 5px;'>FINANZAS PERSONALES (LIBRE)</p>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color: #34D399; font-size: 42px; margin-top: 0px; margin-bottom: 5px;'>$ {saldos['billetera_personal']:,.2f}</h2>", unsafe_allow_html=True)
            st.markdown("<span style='color: #64748B; font-size: 13px;'>Dinero tuyo, separado de las cuentas del negocio.</span>", unsafe_allow_html=True)
        
    # --- SALDOS DISPONIBLES POR CAJA ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("💡 Distribución Interna Recomendada (Porcentajes del Taller)")
    
    monto_negocio_total = max(0.0, saldos["caja_negocio"])
    caja_insumos = monto_negocio_total * 0.40
    caja_sueldos = monto_negocio_total * 0.40
    caja_mantenimiento = monto_negocio_total * 0.20
    
    sub_col1, sub_col2, sub_col3 = st.columns(3)
    with sub_col1:
        with st.container(border=True):
            st.markdown("<p style='color: #38BDF8; font-size: 13px; font-weight: bold; margin-bottom:2px;'>🛠️ CAJA INSUMOS (40%)</p>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='margin-top:0px;'>$ {caja_insumos:,.2f}</h3>", unsafe_allow_html=True)
    with sub_col2:
        with st.container(border=True):
            st.markdown("<p style='color: #A78BFA; font-size: 13px; font-weight: bold; margin-bottom:2px;'>💰 CAJA SUELDOS (40%)</p>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='margin-top:0px;'>$ {caja_sueldos:,.2f}</h3>", unsafe_allow_html=True)
    with sub_col3:
        with st.container(border=True):
            st.markdown("<p style='color: #FBBF24; font-size: 13px; font-weight: bold; margin-bottom:2px;'>🔧 MANTENIMIENTO (20%)</p>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='margin-top:0px;'>$ {caja_mantenimiento:,.2f}</h3>", unsafe_allow_html=True)

    st.markdown("<br><hr style='border-color: #334155;'><br>", unsafe_allow_html=True)
    
    if not saldos["historial"]:
        st.info("No hay movimientos registrados todavía.")
    else:
        df = pd.DataFrame(saldos["historial"])
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["Mes"] = df["fecha"].dt.strftime("%Y-%m")
        
        # Filtro global de mes
        mes_sel = st.selectbox("📆 Seleccionar Período de Análisis:", sorted(df["Mes"].unique(), reverse=True))
        df_mes = df[df["Mes"] == mes_sel]
        
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.markdown("### 📊 Resumen Gastos del Negocio")
            df_n_gasto = df_mes[(df_mes["cuenta"] == "Negocio") & (df_mes["tipo"] == "Gasto")]
            if not df_n_gasto.empty:
                st.bar_chart(df_n_gasto.groupby("categoria")["monto"].sum())
            else: st.caption("Sin egresos este mes.")
                
        with g_col2:
            st.markdown("### 📊 Resumen Gastos Personales")
            df_p_gasto = df_mes[(df_mes["cuenta"] == "Personal") & (df_mes["tipo"] == "Gasto")]
            if not df_p_gasto.empty:
                st.bar_chart(df_p_gasto.groupby("categoria")["monto"].sum())
            else: st.caption("Sin egresos este mes.")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- HISTORIALES SEPARADOS POR PESTAÑAS (TABS) ---
        st.subheader("📋 Libros de Registro Separados")
        tab_ingresos, tab_egresos = st.tabs(["📥 Historial de INGRESOS (Ventas)", "📤 Historial de EGRESOS (Gastos Taller / Personal)"])
        
        # --- PESTAÑA 1: HISTORIAL DE INGRESOS ---
        with tab_ingresos:
            col_b1, col_b2 = st.columns([2, 1])
            with col_b1:
                filtro_pago = st.selectbox("🔍 Filtrar Ingresos por Estado:", ["Todos", "💰 Total Pagado", "📝 Seña", "🤝 Fiado"], key="f_pago")
            
            df_ingresos = df_mes[df_mes["tipo"] == "Ingreso"]
            if filtro_pago != "Todos":
                estado_limpio = filtro_pago.split(" ")[1]
                df_ingresos = df_ingresos[df_ingresos["estado_pago"] == estado_limpio]
            
            # Botón para descargar CSV de ingresos filtrados
            with col_b2:
                st.write("<br>", unsafe_allow_html=True) 
                if not df_ingresos.empty:
                    csv_ingresos = df_ingresos.to_csv(index=False).encode('utf-8')
                    st.download_button(label="📥 Descargar CSV Ingresos", data=csv_ingresos, file_name=f"ingresos_{mes_sel}.csv", mime="text/csv", use_container_width=True)
                else:
                    st.button("📥 Descargar CSV Ingresos", disabled=True, use_container_width=True)
                    
            if df_ingresos.empty:
                st.info("No hay ingresos registrados para este filtro.")
            else:
                for idx, row in df_ingresos[::-1].iterrows():
                    with st.container(border=True):
                        col_h1, col_h2, col_h3, col_h4 = st.columns([1, 2, 4, 1])
                        with col_h1: st.caption(str(row["fecha"].strftime("%Y-%m-%d")))
                        with col_h2: st.markdown(f"**$ {row['monto']:,.2f}**")
                        with col_h3:
                            est = row.get("estado_pago", "Total")
                            met = row.get("metodo_pago", "Efectivo")
                            st.markdown(f"🔹 *{row['categoria']}* — {row['detalle']}")
                            st.caption(f"Condición: **{est}** | Cobrado por: **{met}**")
                        with col_h4:
                            if st.button("🗑️", key=f"del_ing_{idx}"):
                                sals = st.session_state.saldos
                                sals["caja_negocio"] -= row["monto"]
                                sals["historial"].pop(idx)
                                guardar_datos(sals)
                                st.rerun()

        # --- PESTAÑA 2: HISTORIAL DE EGRESOS ---
        with tab_egresos:
            col_be1, col_be2 = st.columns([2, 1])
            with col_be1:
                filtro_destino = st.selectbox("🔍 Filtrar Egresos por Destino:", ["Todos", "🛠️ Gastos del Negocio (Taller)", "🏠 Gastos Personales"], key="f_dest")
            
            df_egresos = df_mes[df_mes["tipo"] == "Gasto"]
            if filtro_destino == "🛠️ Gastos del Negocio (Taller)":
                df_egresos = df_egresos[df_egresos["cuenta"] == "Negocio"]
            elif filtro_destino == "🏠 Gastos Personales":
                df_egresos = df_egresos[df_egresos["cuenta"] == "Personal"]
                
            # Botón para descargar CSV de egresos filtrados
            with col_be2:
                st.write("<br>", unsafe_allow_html=True) 
                if not df_egresos.empty:
                    csv_egresos = df_egresos.to_csv(index=False).encode('utf-8')
                    st.download_button(label="📥 Descargar CSV Egresos", data=csv_egresos, file_name=f"egresos_{mes_sel}.csv", mime="text/csv", use_container_width=True)
                else:
                    st.button("📥 Descargar CSV Egresos", disabled=True, use_container_width=True)

            if df_egresos.empty:
                st.info("No hay egresos registrados para este filtro.")
            else:
                for idx, row in df_egresos[::-1].iterrows():
                    with st.container(border=True):
                        col_e1, col_e2, col_e3, col_e4 = st.columns([1, 2, 4, 1])
                        with col_e1: st.caption(str(row["fecha"].strftime("%Y-%m-%d")))
                        with col_e2: st.markdown(f"**$ {row['monto']:,.2f}**")
                        with col_e3:
                            if row["cuenta"] == "Negocio":
                                etiqueta = "⚙️ GASTO TALLER"
                                estilo_txt = f"<span style='color:#38BDF8; font-weight:bold;'>{etiqueta}</span>"
                            else:
                                etiqueta = "👤 PERSONAL"
                                estilo_txt = f"<span style='color:#34D399; font-weight:bold;'>{etiqueta}</span>"
                                
                            st.markdown(f"{estilo_txt} | *{row['categoria']}*")
                            st.markdown(f"{row['detalle']}")
                        with col_e4:
                            if st.button("🗑️", key=f"del_egr_{idx}"):
                                sals = st.session_state.saldos
                                if row["cuenta"] == "Negocio": sals["caja_negocio"] += row["monto"]
                                else: sals["billetera_personal"] += row["monto"]
                                sals["historial"].pop(idx)
                                guardar_datos(sals)
                                st.rerun()

# --- SECCIÓN 2: REGISTRAR MOVIMIENTOS ---
elif seccion == "📝 Nueva Operación":
    st.title("📝 Carga de Movimientos")
    opcion = st.selectbox("¿Qué vas a registrar hoy?", ["Registrar Venta", "Registrar Gasto Negocio", "Retirar Sueldo", "Registrar Gasto Personal"])
    
    with st.container(border=True):
        if opcion == "Registrar Venta":
            monto = st.number_input("Monto ingresado hoy ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría de la venta", saldos["categorias_negocio_ingreso"])
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                est_pago = st.selectbox("Condición de la venta:", ["Total Pagado", "Seña", "Fiado"])
                estado_guardar = "Total" if est_pago == "Total Pagado" else est_pago
            with col_v2:
                met_pago = st.selectbox("Método de cobro:", ["Efectivo", "Mercado Pago", "Transferencia", "Tarjeta"])
            
            nota = st.text_input("Detalle o Nombre del Cliente:", placeholder="Ej: Juan Perez - Seña cartel de acrílico")
            
            st.markdown("---")
            descuenta_stock = st.checkbox("¿Esta venta consumió algún insumo del stock?")
            insumo_seleccionado = None
            cantidad_a_descontar = 0
            
            if descuenta_stock and saldos["stock_insumos"]:
                lista_nombres_insumos = [i["item"] for i in saldos["stock_insumos"]]
                insumo_seleccionado = st.selectbox("Selecciona el insumo consumido:", lista_nombres_insumos)
                cantidad_a_descontar = st.number_input("Cantidad utilizada:", min_value=1, step=1)

            if st.button("Guardar Registro", type="primary"):
                if descuenta_stock and insumo_seleccionado:
                    for insumo in saldos["stock_insumos"]:
                        if insumo["item"] == insumo_seleccionado:
                            insumo["cantidad"] = max(0, insumo["cantidad"] - cantidad_a_descontar)
                            nota += f" (Consumió {cantidad_a_descontar} un. de {insumo_seleccionado})"
                
                saldos["caja_negocio"] += monto
                saldos["historial"].append({
                    "fecha": datetime.now().strftime("%Y-%m-%d"), 
                    "cuenta": "Negocio", 
                    "tipo": "Ingreso", 
                    "monto": monto, 
                    "categoria": categoria, 
                    "detalle": nota,
                    "estado_pago": estado_guardar,
                    "metodo_pago": met_pago
                })
                guardar_datos(saldos)
                st.toast(f"🎯 Venta ({met_pago} - {estado_guardar}) guardada")
                st.rerun()

        elif opcion == "Registrar Gasto Negocio":
            monto = st.number_input("Monto ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", saldos["categorias_negocio_gasto"])
            met_pago = st.selectbox("Pagado desde:", ["Efectivo", "Mercado Pago", "Transferencia", "Tarjeta"])
            nota = st.text_input("Detalle del gasto:", placeholder="Ej: Compra de acrílicos")
            if st.button("Guardar Registro", type="primary"):
                saldos["caja_negocio"] -= monto
                saldos["historial"].append({
                    "fecha": datetime.now().strftime("%Y-%m-%d"), 
                    "cuenta": "Negocio", 
                    "tipo": "Gasto", 
                    "monto": monto, 
                    "categoria": categoria, 
                    "detalle": nota,
                    "estado_pago": "Total",
                    "metodo_pago": met_pago
                })
                guardar_datos(saldos)
                st.toast("📉 Gasto registrado")
                st.rerun()

        elif opcion == "Retirar Sueldo":
            monto = st.number_input("Monto a extraer ($)", min_value=0.0, max_value=saldos["caja_negocio"], step=50.0)
            if st.button("Confirmar Retiro", type="primary"):
                saldos["caja_negocio"] -= monto
                saldos["billetera_personal"] += monto
                f = datetime.now().strftime("%Y-%m-%d")
                saldos["historial"].append({"fecha": f, "cuenta": "Negocio", "tipo": "Gasto", "monto": monto, "categoria": "Retiro de Socio", "detalle": "Retiro de ganancias", "estado_pago": "Total", "metodo_pago": "Efectivo"})
                saldos["historial"].append({"fecha": f, "cuenta": "Personal", "tipo": "Ingreso", "monto": monto, "categoria": "Sueldo", "detalle": "Ingreso desde Negocio", "estado_pago": "Total", "metodo_pago": "Efectivo"})
                guardar_datos(saldos)
                st.toast("🔄 Traspaso completado")
                st.rerun()

        elif opcion == "Registrar Gasto Personal":
            monto = st.number_input("Monto ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", saldos["categorias_personal_gasto"])
            nota = st.text_input("Detalle del gasto:", placeholder="Ej: Compra supermercado")
            if st.button("Guardar Registro", type="primary"):
                saldos["billetera_personal"] -= monto
                saldos["historial"].append({"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Personal", "tipo": "Gasto", "monto": monto, "categoria": categoria, "detalle": nota, "estado_pago": "Total", "metodo_pago": "Efectivo"})
                guardar_datos(saldos)
                st.toast("🏠 Gasto personal guardado")
                st.rerun()

# --- SECCIÓN 3: STOCK DE INSUMOS ---
elif seccion == "📦 Stock de Insumos":
    st.title("📦 Control de Inventario e Insumos")
    
    with st.expander("➕ Agregar Nuevo Insumo al Stock"):
        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1: nombre_i = st.text_input("Nombre del material/artículo:")
        with col_i2: cant_i = st.number_input("Cantidad Inicial:", min_value=0, step=1)
        with col_i3: minimo_i = st.number_input("Stock Mínimo Alerta:", min_value=0, step=1)
        
        if st.button("Registrar Insumo", type="primary"):
            if nombre_i.strip():
                saldos["stock_insumos"].append({"item": nombre_i.strip(), "cantidad": cant_i, "minimo": minimo_i})
                guardar_datos(saldos)
                st.toast(f"📦 {nombre_i} añadido")
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Lista de Inventario Actual")
    
    if not saldos["stock_insumos"]:
        st.info("No tienes insumos cargados en el stock todavía.")
    else:
        for idx, insumo in enumerate(saldos["stock_insumos"]):
            es_critico = insumo["cantidad"] <= insumo["minimo"]
            color_cartel = "🔴 Falta reponer" if es_critico else "🟢 Stock Ok"
            
            with st.container(border=True):
                c_name, c_status, c_cant, c_actions, c_del = st.columns([3, 2, 2, 3, 1])
                with c_name: st.markdown(f"**{insumo['item']}**")
                with c_status: st.caption(color_cartel)
                with c_cant: st.markdown(f"Unidades: `{insumo['cantidad']}` (Mín: {insumo['minimo']})")
                with c_actions:
                    btn_menos, btn_mas = st.columns(2)
                    with btn_menos: 
                        if st.button("➖ Usar 1", key=f"min_{idx}") and insumo["cantidad"] > 0:
                            insumo["cantidad"] -= 1
                            guardar_datos(saldos)
                            st.rerun()
                    with btn_mas:
                        if st.button("➕ Sumar 1", key=f"add_{idx}"):
                            insumo["cantidad"] += 1
                            guardar_datos(saldos)
                            st.rerun()
                with c_del:
                    if st.button("🗑️", key=f"del_insumo_{idx}"):
                        saldos["stock_insumos"].pop(idx)
                        guardar_datos(saldos)
                        st.rerun()

# --- SECCIÓN 4: PUNTO DE EQUILIBRIO ---
elif seccion == "📉 Punto de Equilibrio":
    st.title("📉 Análisis de Punto de Equilibrio")
    costos_fijos = saldos.get("costos_fijos_negocio", 50000.0)
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        with st.container(border=True):
            st.markdown("#### 🛠️ Tus Costos Fijos")
            nuevos_costos = st.number_input("Costos fijos mensuales ($):", min_value=0.0, value=costos_fijos, step=1000.0)
            if nuevos_costos != costos_fijos:
                saldos["costos_fijos_negocio"] = nuevos_costos
                guardar_datos(saldos)
                st.rerun()
    with col_c2:
        with st.container(border=True):
            st.markdown("#### 🎯 Simulador de Márgenes")
            precio_promedio = st.number_input("Precio de venta estimado ($):", min_value=1.0, value=2000.0)
            costo_promedio = st.number_input("Costo de insumos por unidad ($):", min_value=0.0, value=800.0)
        
    margen = precio_promedio - costo_promedio
    if margen > 0:
        unidades = costos_fijos / margen
        dinero_total = unidades * precio_promedio
        st.markdown("---")
        res1, res2 = st.columns(2)
        with res1: st.metric("Unidades mensuales para cubrir costos:", f"{int(unidades)} un.")
        with res2: st.metric("Facturación mínima requerida:", f"${dinero_total:,.2f}")

# --- SECCIÓN 5: METAS DE AHORRO MULTIALCANCÍA ---
elif seccion == "🎯 Metas de Ahorro":
    st.title("🎯 Objetivos y Metas de Ahorro Múltiples")
    st.write("Crea diferentes alcancías virtuales y asigna tus ahorros personales.")
    
    with st.expander("➕ Crear Nueva Meta de Ahorro"):
        col_m1, col_m2 = st.columns(2)
        with col_m1: nombre_m = st.text_input("¿Para qué estás ahorrando?:", placeholder="Ej: Nueva Maquina, Vacaciones")
        with col_m2: monto_m = st.number_input("Monto Meta Necesario ($):", min_value=1.0, step=1000.0)
        
        if st.button("Crear Meta", type="primary"):
            if nombre_m.strip():
                saldos["metas_ahorro"].append({"meta": nombre_m.strip(), "objetivo": monto_m, "acumulado": 0.0})
                guardar_datos(saldos)
                st.toast(f"🎯 Meta '{nombre_m}' creada")
                st.rerun()

    st.markdown("---")
    st.subheader("Alcancías Virtuales")
    
    if not saldos["metas_ahorro"]:
        st.info("No tienes metas creadas todavía.")
    else:
        for idx, m in enumerate(saldos["metas_ahorro"]):
            porcentaje = min(m["acumulado"] / m["objetivo"], 1.0) if m["objetivo"] > 0 else 0.0
            
            with st.container(border=True):
                st.markdown(f"### 🚀 {m['meta']}")
                st.write(f"Progreso: **${m['acumulado']:,.2f}** de **${m['objetivo']:,.2f}**")
                st.progress(porcentaje)
                
                col_b1, col_b2, col_b3 = st.columns([2, 2, 4])
                with col_b1:
                    monto_poner = st.number_input("Poner dinero ($):", min_value=0.0, max_value=saldos["billetera_personal"], step=100.0, key=f"in_{idx}")
                    if st.button("📥 Sumar a Meta", key=f"btn_in_{idx}"):
                        m["acumulado"] += monto_poner
                        saldos["billetera_personal"] -= monto_poner
                        guardar_datos(saldos)
                        st.rerun()
                with col_b2:
                    monto_sacar = st.number_input("Retirar dinero ($):", min_value=0.0, max_value=m["acumulado"], step=100.0, key=f"out_{idx}")
                    if st.button("📤 Devolver a Billetera", key=f"btn_out_{idx}"):
                        m["acumulado"] -= monto_sacar
                        saldos["billetera_personal"] += monto_sacar
                        guardar_datos(saldos)
                        st.rerun()
                with col_b3:
                    st.write("")
                    st.write("")
                    if st.button("🗑️ Eliminar Meta", key=f"del_meta_{idx}"):
                        saldos["billetera_personal"] += m["acumulado"]
                        saldos["metas_ahorro"].pop(idx)
                        guardar_datos(saldos)
                        st.rerun()

# --- SECCIÓN 6: AJUSTES ---
elif seccion == "⚙️ Ajustes":
    st.title("⚙️ Personalización de Categorías")
    st.write("Gestioná las opciones disponibles en los menús desplegables.")
    
    cat_tipo = st.radio("Modificar lista de:", ["Ingresos Negocio", "Gastos Negocio", "Gastos Personales"], horizontal=True)
    clave_lista = "categorias_negocio_ingreso" if cat_tipo == "Ingresos Negocio" else "categorias_negocio_gasto" if cat_tipo == "Gastos Negocio" else "categorias_personal_gasto"
    
    st.markdown("---")
    st.subheader(f"📋 Categorías Actuales ({cat_tipo})")
    for indice, cat in enumerate(saldos[clave_lista]):
        col_text, col_btn = st.columns([4, 1])
        with col_text: st.markdown(f"🔹 **{cat}**")
        with col_btn:
            if st.button("🗑️ Borrar", key=f"del_{clave_lista}_{indice}"):
                saldos[clave_lista].remove(cat)
                guardar_datos(saldos)
                st.rerun()
                
    st.markdown("---")
    st.subheader("➕ Agregar Nueva Categoría")
    col_input, col_add = st.columns([3, 1])
    with col_input: nueva_cat = st.text_input("Nombre de la categoría:", placeholder="Ej: Grabado Láser", label_visibility="collapsed")
    with col_add:
        if st.button("Añadir ➕", use_container_width=True, type="primary"):
            if nueva_cat.strip() and nueva_cat not in saldos[clave_lista]:
                saldos[clave_lista].append(nueva_cat.strip())
                guardar_datos(saldos)
                st.rerun()