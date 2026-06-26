import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(layout="wide", page_title="Finanzas & Stock Manager Pro", page_icon="📈")

# --- 🔌 CONEXIÓN DIRECTA CON GOOGLE SHEETS ---
# Inicializa la conexión nativa utilizando la URL que guardaste en Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_gsheets():
    try:
        # Intenta leer la pestaña 'historial' de la planilla
        df = conn.read(worksheet="historial", ttl="0d")
        # Si la planilla está vacía, nos devuelve un DataFrame limpio estructurado
        if df.empty or df.columns.tolist() == [0]:
            return pd.DataFrame(columns=["fecha", "cuenta", "tipo", "monto", "categoria", "detalle", "estado_pago", "metodo_pago"])
        return df
    except Exception:
        # Si la pestaña no existe o está en blanco, estructura la tabla de base
        return pd.DataFrame(columns=["fecha", "cuenta", "tipo", "monto", "categoria", "detalle", "estado_pago", "metodo_pago"])

def guardar_datos_gsheets(df):
    # Sube el DataFrame actualizado a la pestaña 'historial' de Google Sheets
    conn.update(worksheet="historial", data=df)

# Carga de datos en tiempo real al vuelo
df_historial = cargar_datos_gsheets()

# --- 🧮 CÁLCULO DE SALDOS AL VUELO ---
# En lugar de usar variables fijas, calculamos los totales sumando y restando las filas del Excel
caja_negocio = 0.0
billetera_personal = 0.0

if not df_historial.empty:
    # Procesar Ingresos y Gastos del Negocio
    ingresos_n = df_historial[(df_historial["cuenta"] == "Negocio") & (df_historial["tipo"] == "Ingreso") & (df_historial["estado_pago"] != "Presupuesto")]["monto"].astype(float).sum()
    gastos_n = df_historial[(df_historial["cuenta"] == "Negocio") & (df_historial["tipo"] == "Gasto")]["monto"].astype(float).sum()
    caja_negocio = ingresos_n - gastos_n

    # Procesar Ingresos y Gastos Personales
    ingresos_p = df_historial[(df_historial["cuenta"] == "Personal") & (df_historial["tipo"] == "Ingreso")]["monto"].astype(float).sum()
    gastos_p = df_historial[(df_historial["cuenta"] == "Personal") & (df_historial["tipo"] == "Gasto")]["monto"].astype(float).sum()
    billetera_personal = ingresos_p - gastos_p

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
        ["🏠 Dashboard General", "📝 Nueva Operación"]
    )
    st.markdown("---")
    st.caption("FSM Pro - Edición Sincronizada")

# --- SECCIÓN 1: DASHBOARD GENERAL ---
if seccion == "🏠 Dashboard General":
    st.markdown("<h1 style='color: #4F46E5; margin-bottom: 0px;'>🏠 Panel de Control</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 16px;'>Sincronizado en la nube para múltiples dispositivos.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    if caja_negocio < 10000:
        st.warning("⚠️ **Alerta de Liquidez:** La caja del negocio está por debajo del mínimo recomendado ($10,000).")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("<p style='color: #94A3B8; font-size: 14px; font-weight: bold; letter-spacing: 1px; margin-bottom: 5px;'>FONDOS DISPONIBLES EMPRENDIMIENTO</p>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color: #38BDF8; font-size: 42px; margin-top: 0px; margin-bottom: 5px;'>$ {caja_negocio:,.2f}</h2>", unsafe_allow_html=True)
            st.markdown("<span style='color: #64748B; font-size: 13px;'>Disponibles para compras de insumos y operación.</span>", unsafe_allow_html=True)
            
    with col2:
        with st.container(border=True):
            st.markdown("<p style='color: #94A3B8; font-size: 14px; font-weight: bold; letter-spacing: 1px; margin-bottom: 5px;'>FINANZAS PERSONALES (LIBRE)</p>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color: #34D399; font-size: 42px; margin-top: 0px; margin-bottom: 5px;'>$ {billetera_personal:,.2f}</h2>", unsafe_allow_html=True)
            st.markdown("<span style='color: #64748B; font-size: 13px;'>Dinero tuyo, separado de las cuentas del negocio.</span>", unsafe_allow_html=True)
        
    # --- SALDOS DISPONIBLES POR CAJA (PREVISIÓN) ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("💡 Distribución Interna Recomendada (Porcentajes del Taller)")
    
    monto_negocio_total = max(0.0, caja_negocio)
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
    
    if df_historial.empty:
        st.info("No hay movimientos registrados en la nube todavía.")
    else:
        # Asegurar formato de tipos para procesar filtros
        df_historial["fecha"] = pd.to_datetime(df_historial["fecha"])
        df_historial["Mes"] = df_historial["fecha"].dt.strftime("%Y-%m")
        df_historial["monto"] = df_historial["monto"].astype(float)
        
        mes_sel = st.selectbox("📆 Seleccionar Período de Análisis:", sorted(df_historial["Mes"].unique(), reverse=True))
        df_mes = df_historial[df_historial["Mes"] == mes_sel]
        
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
        tab_ingresos, tab_egresos = st.tabs(["📥 Historial de INGRESOS (Ventas)", "📤 Historial de EGRESOS (Gastos)"])
        
        with tab_ingresos:
            col_b1, col_b2 = st.columns([2, 1])
            with col_b1:
                filto_p = st.selectbox("🔍 Filtrar Ingresos por Estado:", ["Todos", "💰 Total Pagado", "📝 Seña", "🤝 Fiado", "📄 Presupuesto"], key="f_pago")
            
            df_ingresos = df_mes[df_mes["tipo"] == "Ingreso"]
            if filto_p != "Todos":
                estado_limpio = filto_p.split(" ")[1]
                df_ingresos = df_ingresos[df_ingresos["estado_pago"] == ( "Total" if estado_limpio == "Total" else estado_limpio )]
            
            with col_b2:
                st.write("<br>", unsafe_allow_html=True) 
                if not df_ingresos.empty:
                    st.download_button(label="📥 Descargar CSV Ingresos", data=df_ingresos.to_csv(index=False).encode('utf-8'), file_name=f"ingresos_{mes_sel}.csv", mime="text/csv", use_container_width=True)
            
            if df_ingresos.empty:
                st.info("No hay ingresos bajo este filtro.")
            else:
                for idx, row in df_ingresos[::-1].iterrows():
                    with st.container(border=True):
                        col_h1, col_h2, col_h3, col_h4 = st.columns([1, 2, 4, 1])
                        with col_h1: st.caption(str(row["fecha"].strftime("%Y-%m-%d")))
                        with col_h2: st.markdown(f"**$ {row['monto']:,.2f}**")
                        with col_h3:
                            st.markdown(f"🔹 *{row['categoria']}* — {row['detalle']}")
                            st.caption(f"Condición: **{row['estado_pago']}** | Cobrado por: **{row['metodo_pago']}**")
                        with col_h4:
                            if st.button("🗑️", key=f"del_ing_{idx}"):
                                df_historial = df_historial.drop(idx)
                                guardar_datos_gsheets(df_historial)
                                st.rerun()

        with tab_egresos:
            col_be1, col_be2 = st.columns([2, 1])
            with col_be1:
                filtro_destino = st.selectbox("🔍 Filtrar Egresos por Destino:", ["Todos", "🛠️ Gastos del Negocio (Taller)", "🏠 Gastos Personales"], key="f_dest")
            
            df_egresos = df_mes[df_mes["tipo"] == "Gasto"]
            if filtro_destino == "🛠️ Gastos del Negocio (Taller)":
                df_egresos = df_egresos[df_egresos["cuenta"] == "Negocio"]
            elif filtro_destino == "🏠 Gastos Personales":
                df_egresos = df_egresos[df_egresos["cuenta"] == "Personal"]
                
            with col_be2:
                st.write("<br>", unsafe_allow_html=True) 
                if not df_egresos.empty:
                    st.download_button(label="📥 Descargar CSV Egresos", data=df_egresos.to_csv(index=False).encode('utf-8'), file_name=f"egresos_{mes_sel}.csv", mime="text/csv", use_container_width=True)

            if df_egresos.empty:
                st.info("No hay egresos bajo este filtro.")
            else:
                for idx, row in df_egresos[::-1].iterrows():
                    with st.container(border=True):
                        col_e1, col_e2, col_e3, col_e4 = st.columns([1, 2, 4, 1])
                        with col_e1: st.caption(str(row["fecha"].strftime("%Y-%m-%d")))
                        with col_e2: st.markdown(f"**$ {row['monto']:,.2f}**")
                        with col_e3:
                            lbl = "⚙️ GASTO TALLER" if row["cuenta"] == "Negocio" else "👤 PERSONAL"
                            clr = "#38BDF8" if row["cuenta"] == "Negocio" else "24d399"
                            st.markdown(f"<span style='color:{clr}; font-weight:bold;'>{lbl}</span> | *{row['categoria']}*", unsafe_allow_html=True)
                            st.markdown(f"{row['detalle']}")
                        with col_e4:
                            if st.button("🗑️", key=f"del_egr_{idx}"):
                                df_historial = df_historial.drop(idx)
                                guardar_datos_gsheets(df_historial)
                                st.rerun()

# --- SECCIÓN 2: REGISTRAR MOVIMIENTOS ---
elif seccion == "📝 Nueva Operación":
    st.title("📝 Carga de Movimientos")
    opcion = st.selectbox("¿Qué vas a registrar hoy?", ["Registrar Venta / Presupuesto", "Registrar Gasto Negocio", "Retirar Sueldo", "Registrar Gasto Personal"])
    
    with st.container(border=True):
        if opcion == "Registrar Venta / Presupuesto":
            if "ultimo_comprobante" not in st.session_state:
                st.session_state.ultimo_comprobante = None
                st.session_state.tipo_comprobante = None

            monto = st.number_input("Monto total de la operación ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", ["Venta Producto", "Servicio", "Diseño", "Otros"])
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                est_pago = st.selectbox("Condición de la operación:", ["Total Pagado", "Seña", "Fiado", "Presupuesto"])
                estado_guardar = "Total" if est_pago == "Total Pagado" else est_pago
            with col_v2:
                met_pago = st.selectbox("Método de cobro / Referencia:", ["Efectivo", "Mercado Pago", "Transferencia", "Tarjeta", "Ninguno (Presupuesto)"])
            
            cliente_nombre = st.text_input("Nombre del Cliente (Opcional, para comprobante):")
            nota = st.text_input("Detalle del trabajo / Producto:")
            
            if st.button("Guardar Registro e Imprimir Comprobante", type="primary"):
                detalle_final = f"Cliente: {cliente_nombre} | {nota}" if cliente_nombre else nota
                
                # Crear nueva fila de datos
                nueva_fila = pd.DataFrame([{
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "cuenta": "Negocio",
                    "tipo": "Ingreso",
                    "monto": float(monto),
                    "categoria": categoria,
                    "detalle": detalle_final,
                    "estado_pago": estado_guardar,
                    "metodo_pago": met_pago
                }])
                
                # Concatenar a la base de datos de la nube y subir
                df_historial = pd.concat([df_historial, nueva_fila], ignore_index=True)
                guardar_datos_gsheets(df_historial)
                
                # Generador de textos para enviar
                fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                nom_c = cliente_nombre.strip() if cliente_nombre else "Cliente"
                
                if estado_guardar == "Total":
                    st.session_state.ultimo_comprobante = f"🧾 *COMPROBANTE DE PAGO*\n\n📅 *Fecha:* {fecha_hoy}\n👤 *Cliente:* {nom_c}\n💼 *Detalle:* {nota}\n💰 *Total Abonado:* $ {monto:,.2f}\n💳 *Medio:* {met_pago}\n\n¡Muchas gracias!"
                    st.session_state.tipo_comprobante = "¡Recibo guardado en la nube!"
                elif estado_guardar == "Seña":
                    st.session_state.ultimo_comprobante = f"📝 *COMPROBANTE DE SEÑA*\n\n📅 *Fecha:* {fecha_hoy}\n👤 *Cliente:* {nom_c}\n💼 *Detalle:* {nota}\n💵 *Monto Señado:* $ {monto:,.2f}\n💳 *Medio:* {met_pago}\n\n📌 *Estado:* En producción."
                    st.session_state.tipo_comprobante = "¡Seña guardada en la nube!"
                elif estado_guardar == "Presupuesto":
                    st.session_state.ultimo_comprobante = f"📄 *PRESUPUESTO ESTIMADO*\n\n📅 *Fecha:* {fecha_hoy}\n👤 *Cliente:* {nom_c}\n💼 *Detalle:* {nota}\n💵 *Inversión Total:* $ {monto:,.2f}\n\n⚠️ Validez: 7 días."
                    st.session_state.tipo_comprobante = "¡Presupuesto guardado!"
                else:
                    st.session_state.ultimo_comprobante = f"🤝 *REGISTRO DE CUENTA CORRIENTE*\n\n📅 *Fecha:* {fecha_hoy}\n👤 *Cliente:* {nom_c}\n💼 *Detalle:* {nota}\n📉 *Saldo Pendiente:* $ {monto:,.2f}"
                    st.session_state.tipo_comprobante = "¡Fiado guardado!"
                st.rerun()

            if st.session_state.ultimo_comprobante:
                st.success(st.session_state.tipo_comprobante)
                st.text_area("Texto para WhatsApp:", value=st.session_state.ultimo_comprobante, height=150)
                if st.button("Cargar otro movimiento"):
                    st.session_state.ultimo_comprobante = None
                    st.rerun()

        elif opcion == "Registrar Gasto Negocio":
            monto = st.number_input("Monto ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", ["Insumos", "Publicidad", "Herramientas", "Otros"])
            met_pago = st.selectbox("Pagado desde:", ["Efectivo", "Mercado Pago", "Transferencia", "Tarjeta"])
            nota = st.text_input("Detalle del gasto:")
            if st.button("Guardar Gasto en la Nube", type="primary"):
                nueva_fila = pd.DataFrame([{"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Negocio", "tipo": "Gasto", "monto": float(monto), "categoria": categoria, "detalle": nota, "estado_pago": "Total", "metodo_pago": met_pago}])
                df_historial = pd.concat([df_historial, nueva_fila], ignore_index=True)
                guardar_datos_gsheets(df_historial)
                st.toast("📉 Gasto sincronizado")
                st.rerun()

        elif opcion == "Retirar Sueldo":
            monto = st.number_input("Monto a extraer ($)", min_value=0.0, max_value=caja_negocio, step=50.0)
            if st.button("Confirmar Retiro Multidispositivo", type="primary"):
                f = datetime.now().strftime("%Y-%m-%d")
                fila_g = pd.DataFrame([{"fecha": f, "cuenta": "Negocio", "tipo": "Gasto", "monto": float(monto), "categoria": "Retiro de Socio", "detalle": "Retiro ganancias", "estado_pago": "Total", "metodo_pago": "Efectivo"}])
                fila_i = pd.DataFrame([{"fecha": f, "cuenta": "Personal", "tipo": "Ingreso", "monto": float(monto), "categoria": "Sueldo", "detalle": "Ingreso desde Negocio", "estado_pago": "Total", "metodo_pago": "Efectivo"}])
                df_historial = pd.concat([df_historial, fila_g, fila_i], ignore_index=True)
                guardar_datos_gsheets(df_historial)
                st.toast("🔄 Traspaso sincronizado")
                st.rerun()

        elif opcion == "Registrar Gasto Personal":
            monto = st.number_input("Monto ($)", min_value=0.0, step=50.0)
            categoria = st.selectbox("Categoría", ["Alimentos", "Servicios", "Ocio", "Otros"])
            nota = st.text_input("Detalle del gasto:")
            if st.button("Guardar Gasto Personal", type="primary"):
                nueva_fila = pd.DataFrame([{"fecha": datetime.now().strftime("%Y-%m-%d"), "cuenta": "Personal", "tipo": "Gasto", "monto": float(monto), "categoria": categoria, "detalle": nota, "estado_pago": "Total", "metodo_pago": "Efectivo"}])
                df_historial = pd.concat([df_historial, nueva_fila], ignore_index=True)
                guardar_datos_gsheets(df_historial)
                st.toast("🏠 Gasto personal sincronizado")
                st.rerun()