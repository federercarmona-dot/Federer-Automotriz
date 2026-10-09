import sqlite3

import streamlit as st

from operaciones import (
    AdministradorInventario,
    GestorVentas,
    ModuloReportes,
    SistemaRepuestosBD,
)


def main():
    st.set_page_config(
        page_title="Federer Automotriz | Inventario",
        page_icon="🏎️",
        layout="wide",
    )
    SistemaRepuestosBD.inicializar_bd()
    SistemaRepuestosBD.precargar_datos_ejemplo()

    st.sidebar.title("Federer Automotriz")
    opcion = st.sidebar.radio(
        "Seleccione una opción:",
        [
            "Ver Almacén e Inventario",
            "Buscar Repuesto",
            "Cargar Nuevo Repuesto",
            "Registrar Nuevo Cliente",
            "Procesar Factura de Venta",
            "Reabastecer Stock",
            "Reporte de Ganancias & Historial de Facturas",
        ],
    )

    if opcion == "Ver Almacén e Inventario":
        st.header("Almacén e inventario")
        st.dataframe(
            AdministradorInventario.obtener_inventario_df(),
            use_container_width=True,
            hide_index=True,
        )

    elif opcion == "Buscar Repuesto":
        st.header("Buscar repuesto")
        criterio = st.text_input("Código, nombre o marca")
        if criterio.strip():
            resultados = AdministradorInventario.buscar_repuestos(criterio)
            if resultados.empty:
                st.info("No se encontraron repuestos con ese criterio.")
            else:
                st.dataframe(resultados, use_container_width=True, hide_index=True)

    elif opcion == "Cargar Nuevo Repuesto":
        st.header("Cargar nuevo repuesto")
        categorias, marcas = AdministradorInventario.obtener_catalogos()
        if not categorias or not marcas:
            st.warning("No hay categorías o marcas configuradas para registrar productos.")
        else:
            categoria_ids = {nombre: identificador for identificador, nombre in categorias}
            marca_ids = {nombre: identificador for identificador, nombre in marcas}
            with st.form("form_nuevo_repuesto"):
                codigo = st.text_input("Código único")
                nombre = st.text_input("Nombre del repuesto")
                categoria = st.selectbox("Categoría", list(categoria_ids))
                marca = st.selectbox("Marca", list(marca_ids))
                col_costo, col_venta = st.columns(2)
                costo = col_costo.number_input("Precio de costo", min_value=0.0, step=0.1)
                precio_venta = col_venta.number_input("Precio de venta", min_value=0.0, step=0.1)
                col_stock, col_minimo = st.columns(2)
                stock = col_stock.number_input("Stock inicial", min_value=0, step=1)
                stock_minimo = col_minimo.number_input(
                    "Stock mínimo", min_value=0, value=2, step=1
                )
                guardar = st.form_submit_button("Guardar repuesto")
            if guardar:
                try:
                    AdministradorInventario.registrar_repuesto(
                        codigo,
                        nombre,
                        categoria_ids[categoria],
                        marca_ids[marca],
                        costo,
                        precio_venta,
                        int(stock),
                        int(stock_minimo),
                    )
                    st.success(f"Repuesto '{nombre.strip()}' registrado.")
                except (sqlite3.IntegrityError, ValueError) as error:
                    st.error(f"No se pudo registrar el repuesto: {error}")

    elif opcion == "Registrar Nuevo Cliente":
        st.header("Registrar nuevo cliente")
        with st.form("form_cliente"):
            cedula_rif = st.text_input("Cédula o RIF")
            nombre = st.text_input("Nombre y apellido")
            telefono = st.text_input("Teléfono")
            direccion = st.text_area("Dirección (opcional)")
            guardar = st.form_submit_button("Registrar cliente")
        if guardar:
            try:
                GestorVentas.registrar_cliente(cedula_rif, nombre, telefono, direccion)
                st.success(f"Cliente '{nombre.strip()}' registrado.")
            except (sqlite3.IntegrityError, ValueError) as error:
                st.error(f"No se pudo registrar el cliente: {error}")

    elif opcion == "Procesar Factura de Venta":
        st.header("Procesar factura de venta")
        clientes = GestorVentas.obtener_clientes()
        repuestos = AdministradorInventario.obtener_repuestos()
        if not clientes:
            st.warning("Registra al menos un cliente antes de emitir una factura.")
        elif not repuestos:
            st.warning("No hay repuestos disponibles para vender.")
        else:
            cliente_opciones = {
                f"{cedula} | {nombre}": identificador
                for identificador, cedula, nombre, _ in clientes
            }
            repuesto_opciones = {
                f"{codigo} | {nombre} | stock: {stock} | ${precio:.2f}": identificador
                for identificador, codigo, nombre, precio, stock in repuestos
                if stock > 0
            }
            if not repuesto_opciones:
                st.warning("Todos los repuestos están sin stock.")
            else:
                with st.form("form_factura_venta"):
                    cliente = st.selectbox("Cliente", list(cliente_opciones))
                    repuesto = st.selectbox("Repuesto", list(repuesto_opciones))
                    cantidad = st.number_input("Cantidad", min_value=1, step=1)
                    metodo_pago = st.selectbox(
                        "Método de pago", ["Efectivo", "Tarjeta", "Transferencia"]
                    )
                    procesar = st.form_submit_button("Registrar venta")
                if procesar:
                    try:
                        factura_id, total = GestorVentas.procesar_venta(
                            cliente_opciones[cliente],
                            repuesto_opciones[repuesto],
                            int(cantidad),
                            metodo_pago,
                        )
                        st.success(f"Factura N.º {factura_id} registrada. Total: ${total:,.2f}")
                    except (sqlite3.Error, ValueError) as error:
                        st.error(f"No se pudo procesar la venta: {error}")

    elif opcion == "Reabastecer Stock":
        st.header("Reabastecer stock")
        repuestos = AdministradorInventario.obtener_repuestos()
        if not repuestos:
            st.info("No hay repuestos registrados.")
        else:
            opciones = {
                f"{codigo} | {nombre} | stock actual: {stock}": identificador
                for identificador, codigo, nombre, _, stock in repuestos
            }
            with st.form("form_reabastecer"):
                repuesto = st.selectbox("Repuesto", list(opciones))
                cantidad = st.number_input("Unidades recibidas", min_value=1, step=1)
                actualizar = st.form_submit_button("Actualizar stock")
            if actualizar:
                try:
                    AdministradorInventario.reabastecer_stock(
                        opciones[repuesto], int(cantidad)
                    )
                    st.success(f"Se agregaron {int(cantidad)} unidades al inventario.")
                except (sqlite3.Error, ValueError) as error:
                    st.error(f"No se pudo reabastecer el stock: {error}")

    elif opcion == "Reporte de Ganancias & Historial de Facturas":
        st.header("Ganancias e historial de facturas")
        total_facturado, subtotal = ModuloReportes.obtener_resumen()
        ingresos_venta, costo_venta = ModuloReportes.obtener_utilidad()
        utilidad = ingresos_venta - costo_venta
        col_ingresos, col_costos, col_utilidad = st.columns(3)
        col_ingresos.metric("Ingresos cobrados", f"${total_facturado:,.2f}")
        col_costos.metric("Costo de los repuestos vendidos", f"${costo_venta:,.2f}")
        col_utilidad.metric("Utilidad antes de impuestos", f"${utilidad:,.2f}")
        st.caption(f"Subtotal de ventas antes de impuesto: ${subtotal:,.2f}")
        st.subheader("Historial de facturas")
        historial = ModuloReportes.obtener_historial_facturas_df()
        if historial.empty:
            st.info("Todavía no hay facturas registradas.")
        else:
            st.dataframe(historial, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
