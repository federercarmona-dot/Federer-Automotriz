import sqlite3
import os
from datetime import datetime
import streamlit as st

DB_NAME = "base_datos_repuestos_gigante.db"

# =====================================================================
# 1. ARQUITECTURA Y ESQUEMA RELACIONAL DE LA BASE DE DATOS
# =====================================================================
class SistemaRepuestosBD:
    """Clase responsable de la conexión y creación del ecosistema relacional."""
    
    @staticmethod
    def obtener_conexion():
        """Establece la conexión con la base de datos y activa llaves foráneas."""
        conexion = sqlite3.connect(DB_NAME)
        conexion.execute("PRAGMA foreign_keys = ON;")
        return conexion

    @classmethod
    def inicializar_bd(cls):
        """Crea todas las tablas necesarias para una tienda de repuestos profesional."""
        with cls.obtener_conexion() as conexion:
            cursor = conexion.cursor()
            
            # Tabla de Categorías
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    descripcion TEXT
                )
            ''')

            # Tabla de Marcas de Vehículos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS marcas_vehiculos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL
                )
            ''')

            # Tabla de Proveedores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rif_ruc TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT
                )
            ''')

            # Tabla de Clientes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cedula_rif TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    telefono TEXT,
                    direccion TEXT
                )
            ''')

            # Tabla Principal de Repuestos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS repuestos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    categoria_id INTEGER,
                    marca_id INTEGER,
                    proveedor_id INTEGER,
                    precio_costo REAL NOT NULL CHECK(precio_costo >= 0),
                    precio_venta REAL NOT NULL CHECK(precio_venta >= precio_costo),
                    stock INTEGER NOT NULL CHECK(stock >= 0),
                    stock_minimo INTEGER DEFAULT 2 CHECK(stock_minimo >= 0),
                    FOREIGN KEY (categoria_id) REFERENCES categorias (id) ON DELETE SET NULL,
                    FOREIGN KEY (marca_id) REFERENCES marcas_vehiculos (id) ON DELETE SET NULL,
                    FOREIGN KEY (proveedor_id) REFERENCES proveedores (id) ON DELETE RESTRICT
                )
            ''')

            # Tabla de Facturas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS facturas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cliente_id INTEGER NOT NULL,
                    subtotal REAL NOT NULL CHECK(subtotal >= 0),
                    impuesto REAL NOT NULL CHECK(impuesto >= 0),
                    total REAL NOT NULL CHECK(total >= 0),
                    metodo_pago TEXT CHECK(metodo_pago IN ('Efectivo', 'Tarjeta', 'Transferencia')),
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE RESTRICT
                )
            ''')

            # Detalle de Ventas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ventas_detalle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    factura_id INTEGER NOT NULL,
                    repuesto_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                    precio_unitario REAL NOT NULL CHECK(precio_unitario >= 0),
                    precio_costo_historico REAL NOT NULL, 
                    total_linea REAL NOT NULL,
                    FOREIGN KEY (factura_id) REFERENCES facturas (id) ON DELETE CASCADE,
                    FOREIGN KEY (repuesto_id) REFERENCES repuestos (id) ON DELETE RESTRICT
                )
            ''')

            # Registro histórico de Inventario
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historial_inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repuesto_id INTEGER NOT NULL,
                    tipo_movimiento TEXT CHECK(tipo_movimiento IN ('ENTRADA', 'AJUSTE_MANUAL')),
                    cantidad INTEGER NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (repuesto_id) REFERENCES repuestos (id) ON DELETE CASCADE
                )
            ''')

            conexion.commit()

    @classmethod
    def precargar_datos_ejemplo(cls):
        """Inserta registros iniciales para que el sistema tenga datos al arrancar."""
        try:
            with cls.obtener_conexion() as conn:
                cursor = conn.cursor()
                
                cursor.executemany("INSERT OR IGNORE INTO categorias (id, nombre, descripcion) VALUES (?, ?, ?)", [
                    (1, "Motor", "Filtros, empacaduras, pistones y componentes del motor"),
                    (2, "Frenos", "Pastillas, discos, tambores y cilindros de freno"),
                    (3, "Suspensión", "Amortiguadores, terminales, rótulas y muñones"),
                    (4, "Sistema Eléctrico", "Baterías, alternadores, bujías y fusibles")
                ])
                
                cursor.executemany("INSERT OR IGNORE INTO marcas_vehiculos (id, nombre) VALUES (?, ?)", [
                    (1, "Toyota"), (2, "Chevrolet"), (3, "Ford"), (4, "Hyundai")
                ])
                
                cursor.execute("INSERT OR IGNORE INTO proveedores (id, rif_ruc, nombre, telefono, email) VALUES (?, ?, ?, ?, ?)",
                               (1, "J-30123456-7", "Distribuidora Repuestos Oriente C.A.", "0414-1234567", "ventas@reporiente.com"))
                
                cursor.execute("INSERT OR IGNORE INTO clientes (id, cedula_rif, nombre, telefono, direccion) VALUES (?, ?, ?, ?, ?)",
                               (1, "V-99999999", "Consumidor Final", "0000-0000000", "Mostrador"))
                
                repuestos_iniciales = [
                    ("ALT-TOY", "Alternador Hilux 2.7", 4, 1, 1, 80.0, 130.0, 8, 2),
                    ("PAST-CHEV", "Pastillas Freno Aveo Delanteras", 2, 2, 1, 12.0, 25.0, 15, 4),
                    ("AMOR-FORD", "Amortiguador Delantero Fiesta", 3, 3, 1, 22.0, 45.0, 10, 2),
                    ("BUJ-NGK", "Bujía NGK G-Power Universal", 4, 1, 1, 1.5, 4.0, 60, 10),
                    ("FIL-CHEV", "Filtro de Aceite Spark", 1, 2, 1, 3.0, 7.5, 25, 5)
                ]
                
                for rep in repuestos_iniciales:
                    cursor.execute('''
                        INSERT OR IGNORE INTO repuestos (codigo, nombre, categoria_id, marca_id, proveedor_id, precio_costo, precio_venta, stock, stock_minimo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', rep)
                
                conn.commit()
        except Exception:
            pass


# =====================================================================
# 2. CAPA DE ADMINISTRACIÓN DE INVENTARIO Y CATÁLOGOS
# =====================================================================
class AdministradorInventario:
    @staticmethod
    def registrar_repuesto(codigo, nombre, categoria_id, marca_id, proveedor_id, costo, venta, stock, stock_min):
        try:
            with SistemaRepuestosBD.obtener_conexion() as conn:
                conn.execute('''
                    INSERT INTO repuestos (codigo, nombre, categoria_id, marca_id, proveedor_id, precio_costo, precio_venta, stock, stock_minimo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (codigo.upper(), nombre, categoria_id, marca_id, proveedor_id, costo, venta, stock, stock_min))
                st.success(f"¡Repuesto '{nombre}' registrado exitosamente en el catálogo!")
        except sqlite3.IntegrityError:
            st.error("Error: El CÓDIGO de repuesto ya existe o los IDs asociados no son válidos.")

    @staticmethod
    def reabastecer_stock(repuesto_id, cantidad_ingreso):
        if cantidad_ingreso <= 0:
            st.error("La cantidad a ingresar debe ser mayor a cero.")
            return
        try:
            with SistemaRepuestosBD.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE repuestos SET stock = stock + ? WHERE id = ?", (cantidad_ingreso, repuesto_id))
                cursor.execute(
                    "INSERT INTO historial_inventario (repuesto_id, tipo_movimiento, cantidad) VALUES (?, 'ENTRADA', ?)",
                    (repuesto_id, cantidad_ingreso)
                )
                conn.commit()
                st.success(f"Se agregaron {cantidad_ingreso} unidades al Repuesto ID {repuesto_id}.")
        except Exception as e:
            st.error(f"Error al reabastecer inventario: {e}")

    @staticmethod
    def obtener_inventario_df():
        import pandas as pd
        with SistemaRepuestosBD.obtener_conexion() as conn:
            query = '''
                SELECT r.id, r.codigo, r.nombre, c.nombre as categoria, m.nombre as marca, r.precio_venta, r.stock, r.stock_minimo
                FROM repuestos r
                LEFT JOIN categorias c ON r.categoria_id = c.id
                LEFT JOIN marcas_vehiculos m ON r.marca_id = m.id
            '''
            df = pd.read_sql_query(query, conn)
            df['Estado'] = df.apply(lambda row: 'REORDEN' if row['stock'] <= row['stock_minimo'] else 'OK', axis=1)
            return df


# =====================================================================
# 3. CAPA TRANSACCIONAL: PROCESAMIENTO DE VENTAS Y FACTURACIÓN
# =====================================================================
class GestorVentas:
    @staticmethod
    def registrar_cliente(cedula, nombre, telefono, direccion):
        try:
            with SistemaRepuestosBD.obtener_conexion() as conn:
                conn.execute(
                    "INSERT INTO clientes (cedula_rif, nombre, telefono, direccion) VALUES (?, ?, ?, ?)",
                    (cedula, nombre, telefono, direccion)
                )
                st.success(f"Cliente '{nombre}' registrado con éxito.")
        except sqlite3.IntegrityError:
            st.error("El cliente con esa Cédula/RIF ya se encuentra registrado.")

    @staticmethod
    def obtener_clientes():
        with SistemaRepuestosBD.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, cedula_rif, nombre FROM clientes")
            return cursor.fetchall()

    @classmethod
    def realizar_venta_maestra(cls, cliente_id, lista_productos, metodo_pago="Efectivo"):
        conexion = SistemaRepuestosBD.obtener_conexion()
        cursor = conexion.cursor()
        
        try:
            cursor.execute("BEGIN TRANSACTION;")
            subtotal = 0.0
            operaciones_detalle = []
            
            for item in lista_productos:
                r_id = item['id']
                cant_pedida = item['cantidad']
                
                cursor.execute("SELECT nombre, precio_venta, precio_costo, stock FROM repuestos WHERE id = ?", (r_id,))
                prod = cursor.fetchone()
                
                if not prod:
                    raise ValueError(f"El repuesto ID {r_id} no existe en la tienda.")
                
                nombre_p, p_venta, p_costo, stock_actual = prod
                
                if stock_actual < cant_pedida:
                    raise ValueError(f"Stock insuficiente para '{nombre_p}'. Pedidos: {cant_pedida}, Disponibles: {stock_actual}")
                
                total_linea = p_venta * cant_pedida
                subtotal += total_linea
                operaciones_detalle.append((r_id, cant_pedida, p_venta, p_costo, total_linea, stock_actual - cant_pedida))
            
            impuesto = subtotal * 0.16
            total_factura = subtotal + impuesto
            
            cursor.execute('''
                INSERT INTO facturas (cliente_id, subtotal, impuesto, total, metodo_pago)
                VALUES (?, ?, ?, ?, ?)
            ''', (cliente_id, subtotal, impuesto, total_factura, metodo_pago))
            
            factura_id = cursor.lastrowid
            
            for r_id, cant, pv, pc, tl, nuevo_stock in operaciones_detalle:
                cursor.execute('''
                    INSERT INTO ventas_detalle (factura_id, repuesto_id, cantidad, precio_unitario, precio_costo_historico, total_linea)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (factura_id, r_id, cant, pv, pc, tl))
                
                cursor.execute("UPDATE repuestos SET stock = ? WHERE id = ?", (nuevo_stock, r_id))
                
            cursor.execute("COMMIT;")
            st.success(f"¡VENTA PROCESADA EXITOSAMENTE! Factura Nro: {factura_id} | Total con IVA: ${total_factura:.2f} ({metodo_pago})")
            return factura_id
            
        except Exception as e:
            cursor.execute("ROLLBACK;")
            st.error(f"TRANSACCIÓN CANCELADA: {e}")
            return None
        finally:
            conexion.close()


# =====================================================================
# 4. APLICACIÓN PRINCIPAL STREAMLIT
# =====================================================================
def main():
    st.set_page_config(page_title="Sistema de Repuestos Federer V", page_icon="🏎️", layout="wide")
    
    # Inicializar base de datos
    SistemaRepuestosBD.inicializar_bd()
    SistemaRepuestosBD.precargar_datos_ejemplo()

    st.sidebar.title("🏎️ Menú Principal")
    opcion = st.sidebar.radio("Seleccione una opción:", [
        "Ver Almacén e Inventario",
        "Buscar Repuesto",
        "Cargar Nuevo Repuesto",
        "Registrar Nuevo Cliente",
        "Procesar Factura de Venta",
        "Reabastecer Stock",
        "Reporte de Ganancias",
        "Historial de Facturas"
    ])

    if opcion == "Ver Almacén e Inventario":
        st.header("📦 Inventario en Tiempo Real")
        df = AdministradorInventario.obtener_inventario_df()
        st.dataframe(df, use_container_width=True)

    elif opcion == "Buscar Repuesto":
        st.header("🔍 Búsqueda de Repuestos")
        criterio = st.text_input("Ingrese el nombre o código del repuesto:")
        if criterio:
            with SistemaRepuestosBD.obtener_conexion() as conn:
                import pandas as pd
                query = f'''
                    SELECT r.id, r.codigo, r.nombre, m.nombre as marca, r.precio_venta, r.stock
                    FROM repuestos r
                    LEFT JOIN marcas_vehiculos m ON r.marca_id = m.id
                    WHERE r.nombre LIKE '%{criterio}%' OR r.codigo LIKE '%{criterio}%'
                '''
                df = pd.read_sql_query(query, conn)
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("No se encontraron repuestos con ese criterio.")

    elif opcion == "Cargar Nuevo Repuesto":
        st.header("➕ Registro de Producto Nuevo")
        with st.form("form_nuevo_repuesto"):
            cod = st.text_input("Código único de fábrica (Ej: FIL-202):")
            nom = st.text_input("Descripción / Nombre del repuesto:")
            cat_id = st.selectbox("Categoría", [1, 2, 3, 4], format_func=lambda x: ["", "Motor", "Frenos", "Suspensión", "Sistema Eléctrico"][x])
            mar_id = st.selectbox("Marca Compatible", [1, 2, 3, 4], format_func=lambda x: ["", "Toyota", "Chevrolet", "Ford", "Hyundai"][x])
            costo = st.number_input("Precio de Costo ($):", min_value=0.0, step=0.1)
            venta = st.number_input("Precio de Venta ($):", min_value=0.0, step=0.1)
            stock = st.number_input("Stock inicial:", min_value=0, step=1)
            st_min = st.number_input("Stock Mínimo (Alerta):", min_value=0, value=2, step=1)
            
            submit = st.form_submit_button("Guardar Repuesto")
            if submit:
                if cod and nom:
                    AdministradorInventario.registrar_repuesto(cod, nom, cat_id, mar_id, 1, costo, venta, stock, st_min)
                else:
                    st.error("Por favor complete los campos obligatorios.")

    elif opcion == "Registrar Nuevo Cliente":
        st.header("👤 Registro de Clientes")
        with st.form("form_cliente"):
            ced = st.text_input("Cédula o RIF:")
            nom = st.text_input("Nombre y Apellido:")
            tlf = st.text_input("Teléfono:")
            dire = st.text_area("Dirección:")
            submit = st.form_submit_button("Registrar Cliente")
            if submit:
                if ced and nom:
                    GestorVentas.registrar_cliente(ced, nom, tlf, dire)
                else:
                    st.error("Cédula y Nombre son obligatorios.")

    elif opcion == "Procesar Factura de Venta":
        st.header("🧾 Módulo de Facturación")
        df_inv = AdministradorInventario.obtener_inventario_df()
        st.subheader("Inventario Disponible")
        st.dataframe(df_inv, use_container_width=True)
        
        clientes = GestorVentas.obtener_clientes()
        cliente_dict = {f"{c[1]} - {c[2]}": c[0] for c in clientes}
        cliente_sel = st.selectbox("Seleccione Cliente:", list(cliente_dict.keys()))
        c_id = cliente_dict[cliente_sel] if cliente_sel else 1
        
        st.subheader("Carrito de Compras")
        if 'carrito' not in st.session_state:
            st.session_state.carrito = []
            
        col1, col2, col3 = st.columns(3)
        with col1:
            r_id = st.number_input("ID del Repuesto:", min_value=1, step=1)
        with col2:
            cant = st.number_input("Cantidad:", min_value=1, step=1)
        with col3:
            if st.button("Añadir al Carrito"):
                st.session_state.carrito.append({'id': int(r_id), 'cantidad': int(cant)})
                st.success("Artículo añadido.")

        if st.session_state.carrito:
            st.write("Items actuales en carrito:", st.session_state.carrito)
            metodo = st.selectbox("Método de Pago:", ["Efectivo", "Tarjeta", "Transferencia"])
            
            if st.button("Procesar Venta Final"):
                GestorVentas.realizar_venta_maestra(c_id, st.session_state.carrito, metodo)
                st.session_state.carrito = []
        else:
            st.info("El carrito está vacío.")

    elif opcion == "Reabastecer Stock":
        st.header("📈 Entrada de Stock")
        with st.form("form_reabastecer"):
            r_id = st.number_input("ID del Repuesto:", min_value=1, step=1)
            cant = st.number_input("Cantidad a sumar:", min_value=1, step=1)
            submit = st.form_submit_button("Actualizar Stock")
            if submit:
                AdministradorInventario.reabastecer_stock(int(r_id), int(cant))

    elif opcion == "Reporte de Ganancias":
        st.header("📊 Reporte Financiero de Caja")
        with SistemaRepuestosBD.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    SUM(total_linea) as ventas_totales,
                    SUM(cantidad * precio_costo_historico) as costo_total,
                    (SUM(total_linea) - SUM(cantidad * precio_costo_historico)) as utilidad_neta
                FROM ventas_detalle
            ''')
            res = cursor.fetchone()
            if res and res[0] is not None:
                col1, col2, col3 = st.cols(3) if hasattr(st, "cols") else st.columns(3)
                st.metric(label="Ingresos Netos Facturados", value=f"${res[0]:,.2f}")
                st.metric(label="Costo de Inversión Inicial", value=f"${res[1]:,.2f}")
                st.metric(label="Margen de Utilidad Neto", value=f"${res[2]:,.2f}")
            else:
                st.info("No se registran transacciones de venta facturadas.")

    elif opcion == "Historial de Facturas":
        st.header("📜 Historial de Auditoría de Facturas")
        import pandas as pd
        with SistemaRepuestosBD.obtener_conexion() as conn:
            query = '''
                SELECT f.id as Factura, f.fecha as Fecha, c.nombre as Cliente, f.total as Total, f.metodo_pago as Pago
                FROM facturas f
                JOIN clientes c ON f.cliente_id = c.id
                ORDER BY f.id DESC
            '''
            df = pd.read_sql_query(query, conn)
            st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()