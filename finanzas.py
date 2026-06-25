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
            
        # Parche automático para compatibilidad de versiones
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
        
    st.markdown("<br><hr style='border-color: #334155;'><br>", unsafe_allow_html=True)
    
    if not saldos["historial"]:
        st.info("No hay movimientos registrados todavía.")
    else:
        df = pd.DataFrame(saldos["historial"])
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["Mes"] = df["fecha"].dt.strftime("%Y-%m")
        mes_sel = st.selectbox("📆 Seleccionar Período:", sorted(df["Mes"].unique(), reverse=True))
        df_mes = df[df["Mes"] == mes_sel]
        
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.markdown("### 📊 Distribución de Gastos del Negocio")
            df_n_gasto = df_mes[(df_mes["cuenta"] == "Negocio") & (df_mes["tipo"] == "Gasto")]
            if not df_n_gasto.empty:
                resumen_gasto_n = df_n_gasto.groupby("categoria")["monto"].sum()
                st.scatter_chart(resumen_gasto_n)  # Usamos scatter como alternativa visual o bar expandida si se prefiere
                # Alternativa limpia nativa Streamlit para pastel/proporciones en formato dataframe resumido
                st.dataframe(resumen_gasto_n.to_frame(name="Total Gastado ($)"), use_container_width=True)
            else: 
                st.caption("Sin egresos este mes.")
                
        with g_col2:
            st.markdown("### 📊 Distribución de Gastos Personales")
            df_p_gasto = df_mes[(df_mes["cuenta"] == "Personal") & (df_mes["tipo"] == "Gasto")]
            if not df_p_gasto.empty:
                resumen_gasto_p = df_p_gasto.groupby("categoria")["monto"].sum()
                st.bar_chart(resumen_gasto_p)
                st.dataframe(resumen_gasto_p.to_frame(name="Total Gastado ($)"), use_container_width=True)
            else: 
                st.caption("Sin egresos este mes.")

        st.markdown("---")
        st.subheader("📥 Exportar Datos")
        csv_data = df_mes.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Descargar Reporte del Mes (CSV)", data=csv_data, file_name=f"reporte_{mes_sel}.csv", mime="text/csv")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Registro Histórico Detallado")
        
        # --- MEJORA: TABLA INTERACTIVA CON OPCIÓN DE BORRADO DE MOVIMIENTOS ---
        for idx, row in df_mes[::-1].iterrows():
            with st.container(border=True):
                col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([1, 2, 2, 3, 1])
                with col_h1:
                    st.caption(str(row["fecha"].strftime("%Y-%m-%d")))
                with col_h2:
                    color_t = "🟢" if row["tipo"] == "Ingreso" else "🔴"
                    st.markdown(f"{color_t} **{row['tipo']}** ({row['cuenta']})")
                with col_h3:
                    st.markdown(f"**$ {row['monto']:,.2f}**")
                with col_h4:
                    st.markdown(f"*{row['categoria']}* - {row['detalle']}")
                with col_h5:
                    if st.button("🗑️", key=f"del_mov_{idx}"):
                        # Revertir los saldos antes de borrar
                        monto_revertir = row["monto"]
                        if row["cuenta"] == "Negocio":
                            if row["tipo"] == "Ingreso": saldos["caja_negocio"] -= monto_revertir
                            else: saldos["caja_negocio"] += monto_revertir
                        elif row["cuenta"] == "Personal":
                            if row["tipo"] == "Ingreso": saldos["billetera_personal"] -= monto_revertir
                            else: saldos["billetera_personal"] += monto_revertir
                        
                        # Borrar del historial
                        saldos["historial"].pop(idx)
                        guardar_datos(saldos)
                        st.rerun()

# --- SECCIÓN 2: REGISTRAR MOVIMIENTOS ---
elif seccion == "📝 Nueva Operación":
    st.title("📝 Carga de Movimientos")
    opcion = st.selectbox("¿Qué vas a registrar hoy?", ["Registrar Venta", "Registrar Gasto Negocio", "Retirar Sueldo", "Registrar Gasto Personal"])
    
    with st.container(border=True):
        if opcion == "Registrar Venta":
            monto = st.number_input("Monto total de la venta ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", saldos["categorias_negocio_ingreso"])
            nota = st.text_input("Detalle o Nombre del Cliente:", placeholder="Ej: Juan Perez - Seña mate grabado")
            
            # --- MEJORA: VINCULACIÓN CON STOCK DE INSUMOS ---
            st.markdown("---")
            descuenta_stock = st.checkbox("¿Esta venta consumió algún insumo del stock?")
            insumo_seleccionado = None
            cantidad_a_descontar = 0
            
            if descuenta_stock and saldos["stock_insumos"]:
                lista_nombres_insumos = [i["item"] for i in saldos["stock_insumos"]]
                insumo_seleccionado = st.selectbox("Selecciona el insumo consumido:", lista_nombres_insumos)
                cantidad_a_descontar = st.number_input("Cantidad utilizada:", min_value=1, step=1)
            elif descuenta_stock and not saldos["stock_insumos"]:
                st.caption("⚠️ No hay insumos cargados en la sección de Stock todavía.")

            if st.button("Guardar Registro", type="primary"):
                # Si seleccionó descontar stock, hacemos el descuento primero
                if descuenta_stock and insumo_seleccionado:
                    for insumo in saldos["stock_insumos"]:
                        if insumo["item"] == insumo_seleccionado:
                            insumo["cantidad"] = max(0, insumo["cantidad"] - cantidad_a_descontar)
                            nota += f" (Consumió {cantidad_a_descontar} un. de {insumo_seleccionado})"
                
                saldos["caja_negocio"] += monto
                saldos["historial"].append({"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Negocio", "tipo": "Ingreso", "monto": monto, "categoria": categoria, "detalle": nota})
                guardar_datos(saldos)
                st.toast("🎯 ¡Venta guardada e inventario actualizado!")
                st.rerun()

        elif opcion == "Registrar Gasto Negocio":
            monto = st.number_input("Monto ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", saldos["categorias_negocio_gasto"])
            nota = st.text_input("Detalle del gasto:", placeholder="Ej: Compra de insumos laser")
            if st.button("Guardar Registro", type="primary"):
                saldos["caja_negocio"] -= monto
                saldos["historial"].append({
                    "fecha": datetime.now().strftime("%Y-%m-%d"), 
                    "cuenta": "Negocio", 
                    "tipo": "Gasto", 
                    "monto": monto, 
                    "categoria": categoria, 
                    "detalle": nota
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
                saldos["historial"].append({"fecha": f, "cuenta": "Negocio", "tipo": "Gasto", "monto": monto, "categoria": "Retiro de Socio", "detalle": "Retiro de ganancias"})
                saldos["historial"].append({"fecha": f, "cuenta": "Personal", "tipo": "Ingreso", "monto": monto, "categoria": "Sueldo", "detalle": "Ingreso desde Negocio"})
                guardar_datos(saldos)
                st.toast("🔄 Traspaso completado")
                st.rerun()

        elif opcion == "Registrar Gasto Personal":
            monto = st.number_input("Monto ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", saldos["categorias_personal_gasto"])
            nota = st.text_input("Detalle del gasto:", placeholder="Ej: Compra supermercado")
            if st.button("Guardar Registro", type="primary"):
                saldos["billetera_personal"] -= monto
                saldos["historial"].append({"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Personal", "tipo": "Gasto", "monto": monto, "categoria": categoria, "detalle": nota})
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
                st.toast(f"📦 {nombre_i} añadido al inventario")
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