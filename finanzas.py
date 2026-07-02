import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(layout="wide", page_title="Finanzas & Stock Manager Pro", page_icon="📈")

# --- FUNCIONES DE BASE DE DATOS LOCAL (CSV) ---
def cargar_datos_local(nombre_archivo, columnas):
    if os.path.exists(nombre_archivo):
        try:
            return pd.read_csv(nombre_archivo)
        except Exception:
            return pd.DataFrame(columns=columnas)
    return pd.DataFrame(columns=columnas)

def guardar_datos_local(df, nombre_archivo):
    df.to_csv(nombre_archivo, index=False)

# Archivos Locales
FILE_HISTORIAL = "historial_local.csv"
FILE_STOCK = "stock_local.csv"
FILE_METAS = "metas_local.csv"
FILE_CATEGORIAS = "categorias_local.csv"

# Carga inicial de datos
df_historial = cargar_datos_local(FILE_HISTORIAL, ["fecha", "cuenta", "tipo", "monto", "categoria", "detalle", "estado_pago", "metodo_pago"])
df_stock = cargar_datos_local(FILE_STOCK, ["item", "cantidad", "minimo"])
df_metas = cargar_datos_local(FILE_METAS, ["meta", "objetivo", "acumulado"])
df_cat_local = cargar_datos_local(FILE_CATEGORIAS, ["tipo_categoria", "nombre_categoria"])

# --- PROCESAMIENTO DE CATEGORÍAS ---
if df_cat_local.empty:
    categorias_ingreso = ["Venta Producto", "Servicio", "Diseño", "Otros"]
    categorias_gasto_negocio = ["Insumos", "Publicidad", "Herramientas", "Otros"]
    categorias_gasto_personal = ["Alimentos", "Servicios", "Ocio", "Otros"]
else:
    categorias_ingreso = df_cat_local[df_cat_local["tipo_categoria"] == "Ingreso"]["nombre_categoria"].tolist()
    categorias_gasto_negocio = df_cat_local[df_cat_local["tipo_categoria"] == "Gasto Negocio"]["nombre_categoria"].tolist()
    categorias_gasto_personal = df_cat_local[df_cat_local["tipo_categoria"] == "Gasto Personal"]["nombre_categoria"].tolist()
    
    if not categorias_ingreso: categorias_ingreso = ["Otros"]
    if not categorias_gasto_negocio: categorias_gasto_negocio = ["Otros"]
    if not categorias_gasto_personal: categorias_gasto_personal = ["Otros"]

# --- CÁLCULO DE SALDOS AL VUELO ---
caja_negocio = 0.0
billetera_personal = 0.0

if not df_historial.empty:
    df_historial["monto"] = pd.to_numeric(df_historial["monto"], errors='coerce').fillna(0.0)
    ingresos_n = df_historial[(df_historial["cuenta"] == "Negocio") & (df_historial["tipo"] == "Ingreso") & (df_historial["estado_pago"] != "Presupuesto")]["monto"].sum()
    gastos_n = df_historial[(df_historial["cuenta"] == "Negocio") & (df_historial["tipo"] == "Gasto")]["monto"].sum()
    caja_negocio = ingresos_n - gastos_n

    ingresos_p = df_historial[(df_historial["cuenta"] == "Personal") & (df_historial["tipo"] == "Ingreso")]["monto"].sum()
    gastos_p = df_historial[(df_historial["cuenta"] == "Personal") & (df_historial["tipo"] == "Gasto")]["monto"].sum()
    billetera_personal = ingresos_p - gastos_p

# --- SISTEMA DE LOGIN ---
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

# --- NAVEGACIÓN ---
with st.sidebar:
    st.markdown("<h2 style='color: #4F46E5; margin-top: 0px;'>⚡ Panel de Control</h2>", unsafe_allow_html=True)
    if st.button("Cerrar Sesión 🔓", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()
    st.markdown("---")
    seccion = st.radio(
        "Navegación:",
        ["🏠 Dashboard General", "📝 Nueva Operación", "🧮 Calculadora de Costos", "📦 Stock de Insumos", "📉 Punto de Equilibrio", "🎯 Metas de Ahorro", "⚙️ Configurar Categorías"]
    )
    st.markdown("---")
    st.caption("FSM Pro - Versión Local Estable")

# --- 🏠 DASHBOARD GENERAL ---
if seccion == "🏠 Dashboard General":
    st.title("🏠 Panel de Control General")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("<p style='color: #94A3B8; font-size: 14px; font-weight: bold;'>FONDOS DISPONIBLES EMPRENDIMIENTO</p>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color: #38BDF8; font-size: 42px; margin-top: 0px;'>$ {caja_negocio:,.2f}</h2>", unsafe_allow_html=True)
    with col2:
        with st.container(border=True):
            st.markdown("<p style='color: #94A3B8; font-size: 14px; font-weight: bold;'>FINANZAS PERSONALES (LIBRE)</p>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color: #34D399; font-size: 42px; margin-top: 0px;'>$ {billetera_personal:,.2f}</h2>", unsafe_allow_html=True)
        
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
                        if st.button("🗑️", key=f"del_ing_{idx}"):
                            df_historial = df_historial.drop(idx)
                            guardar_datos_local(df_historial, FILE_HISTORIAL)
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
                        if st.button("🗑️", key=f"del_egr_{idx}"):
                            df_historial = df_historial.drop(idx)
                            guardar_datos_local(df_historial, FILE_HISTORIAL)
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

            if st.button("Guardar e Imprimir Comprobante", type="primary"):
                detalle_final = nota
                detalle_final = f"Cliente: {cliente_nombre} | {detalle_final}" if cliente_nombre else detalle_final
                
                nueva_fila = pd.DataFrame([{"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Negocio", "tipo": "Ingreso", "monto": float(monto), "categoria": categoria, "detalle": detalle_final, "estado_pago": estado_guardar, "metodo_pago": met_pago}])
                df_historial = pd.concat([df_historial, nueva_fila], ignore_index=True)
                guardar_datos_local(df_historial, FILE_HISTORIAL)
                
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
                guardar_datos_local(df_historial, FILE_HISTORIAL)
                st.rerun()

        elif opcion == "Retirar Sueldo":
            monto = st.number_input("Monto a extraer ($)", min_value=0.0, max_value=caja_negocio, step=50.0)
            if st.button("Confirmar Retiro", type="primary"):
                f = datetime.now().strftime("%Y-%m-%d")
                fila_g = pd.DataFrame([{"fecha": f, "cuenta": "Negocio", "tipo": "Gasto", "monto": float(monto), "categoria": "Retiro de Socio", "detalle": "Retiro ganancias", "estado_pago": "Total", "metodo_pago": "Efectivo"}])
                fila_i = pd.DataFrame([{"fecha": f, "cuenta": "Personal", "tipo": "Ingreso", "monto": float(monto), "categoria": "Sueldo", "detalle": "Ingreso desde Negocio", "estado_pago": "Total", "metodo_pago": "Efectivo"}])
                df_historial = pd.concat([df_historial, fila_g, fila_i], ignore_index=True)
                guardar_datos_local(df_historial, FILE_HISTORIAL)
                st.rerun()

        elif opcion == "Registrar Gasto Personal":
            monto = st.number_input("Monto ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", categorias_gasto_personal)
            nota = st.text_input("Detalle:")
            if st.button("Guardar Gasto Personal", type="primary"):
                nueva_fila = pd.DataFrame([{"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Personal", "tipo": "Gasto", "monto": float(monto), "categoria": "Categoría", "detalle": nota, "estado_pago": "Total", "metodo_pago": "Efectivo"}])
                df_historial = pd.concat([df_historial, nueva_fila], ignore_index=True)
                guardar_datos_local(df_historial, FILE_HISTORIAL)
                st.rerun()

# --- 🧮 CALCULADORA DE COSTOS (NUEVA PESTAÑA) ---
elif seccion == "🧮 Calculadora de Costos":
    st.title("🧮 Calculadora de Costos y Precio de Venta")
    st.markdown("Usa esta herramienta para calcular presupuestos precisos rápido y saber cuánto cobrar.")
    
    col_calc1, col_calc2 = st.columns([4, 3])
    
    with col_calc1:
        with st.container(border=True):
            st.subheader("📋 Datos del Producto")
            nombre_prod = st.text_input("Nombre del producto / trabajo:", placeholder="Ej: Remera Estampada DTF / Mate Grabado Láser")
            
            st.markdown("---")
            st.markdown("**💰 1. Costo de Materiales directos**")
            costo_materiales = st.number_input("Suma total de materiales usados ($):", min_value=0.0, value=0.0, step=100.0, help="Precio de compra de la remera base, vinilo, madera, insumos, etc.")
            
            st.markdown("---")
            st.markdown("**⏱️ 2. Mano de Obra y Tiempo (Diseño/Armado)**")
            c1, c2 = st.columns(2)
            with c1:
                tiempo_horas = st.number_input("Tiempo estimado de trabajo (Horas):", min_value=0.0, value=0.5, step=0.25, help="Tiempo en Corel, preparación de máquinas y armado final.")
            with c2:
                precio_hora_trabajo = st.number_input("Valor de tu hora de trabajo ($):", min_value=0.0, value=4000.0, step=500.0, help="Cuánto querés que valga tu hora de mano de obra neta.")
            
            costo_mano_obra = tiempo_horas * precio_hora_trabajo
            st.caption(f"💵 Costo total de mano de obra: **$ {costo_mano_obra:,.2f}**")
            
            st.markdown("---")
            st.markdown("**🔧 3. Costos Fijos y Desgaste (Taller)**")
            costo_fijos_prod = st.number_input("Costo de estructura fijo por producto ($):", min_value=0.0, value=500.0, step=100.0, help="Monto estimado para cubrir luz, amortización del plotter/láser, alquiler, etc.")
            
            st.markdown("---")
            st.markdown("**📈 4. Margen de Ganancia Comercial**")
            porcentaje_ganancia = st.slider("Porcentaje de ganancia deseado encima del costo (%):", min_value=0, max_value=300, value=50, step=5)

    # Cálculos finales matemáticos
    costo_total_fabricacion = costo_materiales + costo_mano_obra + costo_fijos_prod
    monto_ganancia_comercial = costo_total_fabricacion * (porcentaje_ganancia / 100.0)
    precio_venta_sugerido = costo_total_fabricacion + monto_ganancia_comercial

    with col_calc2:
        with st.container(border=True):
            st.markdown("<p style='text-align: center; color: #94A3B8; font-weight: bold; font-size: 14px;'>PRECIO SUGERIDO AL CLIENTE</p>", unsafe_allow_html=True)
            st.markdown(f"<h1 style='text-align: center; color: #34D399; font-size: 50px; margin-top: 0px;'>$ {precio_venta_sugerido:,.2f}</h1>", unsafe_allow_html=True)
            st.markdown("---")
            
            st.markdown("### 📊 Desglose Técnico:")
            st.write(f"📦 **Materiales directos:** $ {costo_materiales:,.2f}")
            st.write(f"👤 **Tu tiempo de mano de obra:** $ {costo_mano_obra:,.2f}")
            st.write(f"⚡ **Costos estructurales taller:** $ {costo_fijos_prod:,.2f}")
            st.markdown(f"📉 **Costo Base Real:** $ {costo_total_fabricacion:,.2f}")
            st.markdown(f"🔥 **Tu Ganancia Neta Líquida ({porcentaje_ganancia}%):** $ {monto_ganancia_comercial:,.2f}")
            
            st.markdown("---")
            st.subheader("📲 Texto rápido para presupuestar:")
            desc_prod = nombre_prod if nombre_prod.strip() else "Producto Personalizado"
            texto_presupuesto = f"📄 *PRESUPUESTO ESTIMADO*\n\n✨ *Detalle:* {desc_prod}\n💰 *Inversión Total:* $ {precio_venta_sugerido:,.2f}\n\n📌 *Condición:* Seña del 50% para iniciar producción.\n\n¡Cualquier consulta quedo a tu disposición! 🙌"
            st.text_area("Copiá esto para pegar en WhatsApp:", value=texto_presupuesto, height=140)

# --- 📦 STOCK DE INSUMOS ---
elif seccion == "📦 Stock de Insumos":
    st.title("📦 Control de Inventario e Insumos (Manual)")
    
    with st.expander("➕ Agregar Nuevo Insumo al Stock"):
        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1: nombre_i = st.text_input("Nombre del material:")
        with col_i2: cant_i = st.number_input("Cantidad Inicial:", min_value=0, step=1)
        with col_i3: minimo_i = st.number_input("Stock Mínimo Alerta:", min_value=0, step=1)
        
        if st.button("Registrar Insumo", type="primary"):
            if nombre_i.strip():
                nueva_fila = pd.DataFrame([{"item": nombre_i.strip(), "cantidad": int(cant_i), "minimo": int(minimo_i)}])
                df_stock = pd.concat([df_stock, nueva_fila], ignore_index=True)
                guardar_datos_local(df_stock, FILE_STOCK)
                st.rerun()

    st.markdown("---")
    if df_stock.empty:
        st.info("No tienes insumos cargados todavía.")
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
                            guardar_datos_local(df_stock, FILE_STOCK)
                            st.rerun()
                    with btn_mas:
                        if st.button("➕ Sumar 1", key=f"add_{idx}"):
                            df_stock.at[idx, "cantidad"] = int(row["cantidad"]) + 1
                            guardar_datos_local(df_stock, FILE_STOCK)
                            st.rerun()
                with c_del:
                    if st.button("🗑️", key=f"del_insumo_{idx}"):
                        df_stock = df_stock.drop(idx)
                        guardar_datos_local(df_stock, FILE_STOCK)
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
    st.title("🎯 Alcancías Virtuales")
    
    with st.expander("➕ Crear Nueva Meta de Ahorro"):
        col_m1, col_m2 = st.columns(2)
        with col_m1: nombre_m = st.text_input("¿Para qué estás ahorrando?:")
        with col_m2: monto_m = st.number_input("Monto Meta Necesario ($):", min_value=1.0, step=1000.0)
        
        if st.button("Crear Meta", type="primary"):
            if nombre_m.strip():
                nueva_fila = pd.DataFrame([{"meta": nombre_m.strip(), "objetivo": float(monto_m), "acumulado": 0.0}])
                df_metas = pd.concat([df_metas, nueva_fila], ignore_index=True)
                guardar_datos_local(df_metas, FILE_METAS)
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
                        guardar_datos_local(df_historial, FILE_HISTORIAL)
                        guardar_datos_local(df_metas, FILE_METAS)
                        st.rerun()
                with col_b2:
                    monto_sacar = st.number_input("Retirar dinero ($):", min_value=0.0, max_value=float(row["acumulado"]), step=100.0, key=f"out_{idx}")
                    if st.button("📤 Retirar", key=f"btn_out_{idx}"):
                        df_metas.at[idx, "acumulado"] = float(row["acumulado"]) - monto_sacar
                        nueva_f = pd.DataFrame([{"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Personal", "tipo": "Ingreso", "monto": float(monto_sacar), "categoria": "Ahorro", "detalle": f"Retiro de meta: {row['meta']}", "estado_pago": "Total", "metodo_pago": "Efectivo"}])
                        df_historial = pd.concat([df_historial, nueva_f], ignore_index=True)
                        guardar_datos_local(df_historial, FILE_HISTORIAL)
                        guardar_datos_local(df_metas, FILE_METAS)
                        st.rerun()
                with col_b3:
                    st.write("<br>", unsafe_allow_html=True)
                    if st.button("🗑️ Eliminar Meta", key=f"del_meta_{idx}"):
                        df_metas = df_metas.drop(idx)
                        guardar_datos_local(df_metas, FILE_METAS)
                        st.rerun()

# --- ⚙️ CONFIGURACIÓN DE CATEGORÍAS ---
elif seccion == "⚙️ Configurar Categorías":
    st.title("⚙️ Gestión Personalizada de Categorías")
    
    with st.container(border=True):
        st.subheader("➕ Agregar Nueva Categoría")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            tipo_nueva = st.selectbox("¿A qué módulo pertenece?", ["Ingreso", "Gasto Negocio", "Gasto Personal"])
        with col_c2:
            nombre_nueva = st.text_input("Nombre de la categoría:")
            
        if st.button("Guardar Nueva Categoría", type="primary"):
            if nombre_nueva.strip():
                nueva_cat_df = pd.DataFrame([{"tipo_categoria": tipo_nueva, "nombre_categoria": nombre_nueva.strip()}])
                df_cat_local = pd.concat([df_cat_local, nueva_cat_df], ignore_index=True)
                guardar_datos_local(df_cat_local, FILE_CATEGORIAS)
                st.toast(f"✅ Categoría '{nombre_nueva}' agregada")
                st.rerun()
                
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Categorías Activas")
    if not df_cat_local.empty:
        for idx, r in df_cat_local.iterrows():
            col_v_n, col_v_b = st.columns([5, 1])
            col_v_n.markdown(f"▪️ **{r['tipo_categoria']}**: {r['nombre_categoria']}")
            if col_v_b.button("🗑️", key=f"del_cat_{idx}"):
                df_cat_local = df_cat_local.drop(idx)
                guardar_datos_local(df_cat_local, FILE_CATEGORIAS)
                st.rerun()