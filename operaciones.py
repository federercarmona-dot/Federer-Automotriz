import sqlite3

import pandas as pd

DB_NAME = "base_datos_repuestos_gigante.db"


class SistemaRepuestosBD:
    @staticmethod
    def obtener_conexion():
        conexion = sqlite3.connect(DB_NAME, timeout=10)
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion

    @classmethod
    def inicializar_bd(cls):
        with cls.obtener_conexion() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    descripcion TEXT
                );
                CREATE TABLE IF NOT EXISTS marcas_vehiculos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL
                );
                CREATE TABLE IF NOT EXISTS proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rif_ruc TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT
                );
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cedula_rif TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    telefono TEXT,
                    direccion TEXT
                );
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
                    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
                    FOREIGN KEY (marca_id) REFERENCES marcas_vehiculos(id) ON DELETE SET NULL,
                    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id) ON DELETE RESTRICT
                );
                CREATE TABLE IF NOT EXISTS facturas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cliente_id INTEGER NOT NULL,
                    subtotal REAL NOT NULL CHECK(subtotal >= 0),
                    impuesto REAL NOT NULL CHECK(impuesto >= 0),
                    total REAL NOT NULL CHECK(total >= 0),
                    metodo_pago TEXT CHECK(metodo_pago IN ('Efectivo', 'Tarjeta', 'Transferencia')),
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT
                );
                CREATE TABLE IF NOT EXISTS ventas_detalle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    factura_id INTEGER NOT NULL,
                    repuesto_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                    precio_unitario REAL NOT NULL CHECK(precio_unitario >= 0),
                    precio_costo_historico REAL NOT NULL,
                    total_linea REAL NOT NULL,
                    FOREIGN KEY (factura_id) REFERENCES facturas(id) ON DELETE CASCADE,
                    FOREIGN KEY (repuesto_id) REFERENCES repuestos(id) ON DELETE RESTRICT
                );
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    factura_id INTEGER NOT NULL,
                    repuesto_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                    precio_unitario REAL NOT NULL CHECK(precio_unitario >= 0),
                    precio_costo_historico REAL NOT NULL,
                    total_linea REAL NOT NULL,
                    FOREIGN KEY (factura_id) REFERENCES facturas(id) ON DELETE CASCADE,
                    FOREIGN KEY (repuesto_id) REFERENCES repuestos(id) ON DELETE RESTRICT
                );
                CREATE TABLE IF NOT EXISTS historial_inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repuesto_id INTEGER NOT NULL,
                    tipo_movimiento TEXT CHECK(tipo_movimiento IN ('ENTRADA', 'AJUSTE_MANUAL')),
                    cantidad INTEGER NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (repuesto_id) REFERENCES repuestos(id) ON DELETE CASCADE
                );
                INSERT OR IGNORE INTO ventas (
                    id, factura_id, repuesto_id, cantidad, precio_unitario,
                    precio_costo_historico, total_linea
                )
                SELECT id, factura_id, repuesto_id, cantidad, precio_unitario,
                       precio_costo_historico, total_linea
                FROM ventas_detalle;
                """
            )

    @classmethod
    def precargar_datos_ejemplo(cls):
        with cls.obtener_conexion() as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO categorias (id, nombre, descripcion) VALUES (?, ?, ?)",
                [
                    (1, "Motor", "Componentes del motor"),
                    (2, "Frenos", "Componentes de freno"),
                    (3, "Suspensión", "Componentes de suspensión"),
                    (4, "Sistema Eléctrico", "Componentes eléctricos"),
                ],
            )
            conn.executemany(
                "INSERT OR IGNORE INTO marcas_vehiculos (id, nombre) VALUES (?, ?)",
                [(1, "Toyota"), (2, "Chevrolet"), (3, "Ford"), (4, "Hyundai")],
            )
            conn.execute(
                "INSERT OR IGNORE INTO proveedores (id, rif_ruc, nombre) VALUES (1, ?, ?)",
                ("J-30123456-7", "Distribuidora Repuestos Oriente C.A."),
            )
            conn.execute(
                "INSERT OR IGNORE INTO clientes (id, cedula_rif, nombre, telefono, direccion) VALUES (1, ?, ?, ?, ?)",
                ("V-99999999", "Consumidor Final", "0000-0000000", "Mostrador"),
            )
            conn.executemany(
                """INSERT OR IGNORE INTO repuestos
                (codigo, nombre, categoria_id, marca_id, proveedor_id,
                 precio_costo, precio_venta, stock, stock_minimo)
                VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?)""",
                [
                    ("ALT-TOY", "Alternador Hilux 2.7", 4, 1, 80.0, 130.0, 8, 2),
                    ("PAST-CHEV", "Pastillas Freno Aveo Delanteras", 2, 2, 12.0, 25.0, 15, 4),
                    ("AMOR-FORD", "Amortiguador Delantero Fiesta", 3, 3, 22.0, 45.0, 10, 2),
                    ("BUJ-NGK", "Bujía NGK G-Power Universal", 4, 1, 1.5, 4.0, 60, 10),
                    ("FIL-CHEV", "Filtro de Aceite Spark", 1, 2, 3.0, 7.5, 25, 5),
                ],
            )


class AdministradorInventario:
    @staticmethod
    def obtener_catalogos():
        with SistemaRepuestosBD.obtener_conexion() as conn:
            categorias = conn.execute("SELECT id, nombre FROM categorias ORDER BY nombre").fetchall()
            marcas = conn.execute("SELECT id, nombre FROM marcas_vehiculos ORDER BY nombre").fetchall()
        return categorias, marcas

    @staticmethod
    def obtener_inventario_df():
        query = """
            SELECT r.id, r.codigo, r.nombre, c.nombre AS categoria,
                   m.nombre AS marca, r.precio_venta, r.stock, r.stock_minimo
            FROM repuestos r
            LEFT JOIN categorias c ON r.categoria_id = c.id
            LEFT JOIN marcas_vehiculos m ON r.marca_id = m.id
            ORDER BY r.nombre
        """
        with SistemaRepuestosBD.obtener_conexion() as conn:
            df = pd.read_sql_query(query, conn)
        df["Estado"] = df.apply(
            lambda fila: "REORDEN" if fila["stock"] <= fila["stock_minimo"] else "OK",
            axis=1,
        )
        return df

    @staticmethod
    def buscar_repuestos(criterio):
        query = """
            SELECT r.id, r.codigo, r.nombre, c.nombre AS categoria,
                   m.nombre AS marca, r.precio_venta, r.stock, r.stock_minimo
            FROM repuestos r
            LEFT JOIN categorias c ON r.categoria_id = c.id
            LEFT JOIN marcas_vehiculos m ON r.marca_id = m.id
            WHERE r.codigo LIKE ? OR r.nombre LIKE ? OR m.nombre LIKE ?
            ORDER BY r.nombre
        """
        patron = f"%{criterio.strip()}%"
        with SistemaRepuestosBD.obtener_conexion() as conn:
            df = pd.read_sql_query(query, conn, params=(patron, patron, patron))
        df["Estado"] = df.apply(
            lambda fila: "REORDEN" if fila["stock"] <= fila["stock_minimo"] else "OK",
            axis=1,
        )
        return df

    @staticmethod
    def obtener_repuestos():
        with SistemaRepuestosBD.obtener_conexion() as conn:
            return conn.execute(
                "SELECT id, codigo, nombre, precio_venta, stock FROM repuestos ORDER BY nombre"
            ).fetchall()

    @staticmethod
    def registrar_repuesto(codigo, nombre, categoria_id, marca_id, costo,
                           venta, stock, stock_minimo):
        if not codigo.strip() or not nombre.strip():
            raise ValueError("El código y el nombre son obligatorios.")
        if venta < costo:
            raise ValueError("El precio de venta no puede ser menor que el costo.")
        with SistemaRepuestosBD.obtener_conexion() as conn:
            conn.execute(
                """INSERT INTO repuestos
                (codigo, nombre, categoria_id, marca_id, proveedor_id,
                 precio_costo, precio_venta, stock, stock_minimo)
                VALUES (?, ?, ?, ?, (SELECT id FROM proveedores ORDER BY id LIMIT 1), ?, ?, ?, ?)""",
                (codigo.strip().upper(), nombre.strip(), categoria_id, marca_id,
                 costo, venta, stock, stock_minimo),
            )

    @staticmethod
    def reabastecer_stock(repuesto_id, cantidad):
        if cantidad <= 0:
            raise ValueError("La cantidad a ingresar debe ser mayor que cero.")
        with SistemaRepuestosBD.obtener_conexion() as conn:
            cursor = conn.execute(
                "UPDATE repuestos SET stock = stock + ? WHERE id = ?",
                (cantidad, repuesto_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("El repuesto seleccionado ya no existe.")
            conn.execute(
                "INSERT INTO historial_inventario (repuesto_id, tipo_movimiento, cantidad) VALUES (?, 'ENTRADA', ?)",
                (repuesto_id, cantidad),
            )


class GestorVentas:
    @staticmethod
    def obtener_clientes():
        with SistemaRepuestosBD.obtener_conexion() as conn:
            return conn.execute(
                "SELECT id, cedula_rif, nombre, telefono FROM clientes ORDER BY nombre"
            ).fetchall()

    @staticmethod
    def registrar_cliente(cedula_rif, nombre, telefono, direccion=""):
        if not cedula_rif.strip() or not nombre.strip():
            raise ValueError("La cédula/RIF y el nombre son obligatorios.")
        with SistemaRepuestosBD.obtener_conexion() as conn:
            conn.execute(
                "INSERT INTO clientes (cedula_rif, nombre, telefono, direccion) VALUES (?, ?, ?, ?)",
                (cedula_rif.strip(), nombre.strip(), telefono.strip(), direccion.strip()),
            )

    @staticmethod
    def procesar_venta(cliente_id, repuesto_id, cantidad, metodo_pago):
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")
        if metodo_pago not in ("Efectivo", "Tarjeta", "Transferencia"):
            raise ValueError("El método de pago no es válido.")

        conn = SistemaRepuestosBD.obtener_conexion()
        try:
            conn.execute("BEGIN IMMEDIATE")
            producto = conn.execute(
                "SELECT precio_venta, precio_costo, stock FROM repuestos WHERE id = ?",
                (repuesto_id,),
            ).fetchone()
            if producto is None:
                raise ValueError("El repuesto seleccionado no existe.")
            precio_venta, precio_costo, stock = producto
            if cantidad > stock:
                raise ValueError(f"Stock insuficiente. Disponibles: {stock}.")
            subtotal = precio_venta * cantidad
            impuesto = subtotal * 0.16
            total = subtotal + impuesto
            cursor = conn.execute(
                "INSERT INTO facturas (cliente_id, subtotal, impuesto, total, metodo_pago) VALUES (?, ?, ?, ?, ?)",
                (cliente_id, subtotal, impuesto, total, metodo_pago),
            )
            factura_id = cursor.lastrowid
            datos_venta = (factura_id, repuesto_id, cantidad, precio_venta,
                           precio_costo, subtotal)
            conn.execute(
                """INSERT INTO ventas
                (factura_id, repuesto_id, cantidad, precio_unitario,
                 precio_costo_historico, total_linea) VALUES (?, ?, ?, ?, ?, ?)""",
                datos_venta,
            )
            conn.execute(
                """INSERT INTO ventas_detalle
                (factura_id, repuesto_id, cantidad, precio_unitario,
                 precio_costo_historico, total_linea) VALUES (?, ?, ?, ?, ?, ?)""",
                datos_venta,
            )
            actualizacion = conn.execute(
                "UPDATE repuestos SET stock = stock - ? WHERE id = ? AND stock >= ?",
                (cantidad, repuesto_id, cantidad),
            )
            if actualizacion.rowcount != 1:
                raise ValueError("El stock cambió durante la operación; vuelve a intentar.")
            conn.commit()
            return factura_id, total
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class ModuloReportes:
    @staticmethod
    def obtener_resumen():
        with SistemaRepuestosBD.obtener_conexion() as conn:
            return conn.execute(
                """SELECT COALESCE(SUM(total), 0), COALESCE(SUM(subtotal), 0)
                FROM facturas"""
            ).fetchone()

    @staticmethod
    def obtener_utilidad():
        with SistemaRepuestosBD.obtener_conexion() as conn:
            return conn.execute(
                """SELECT COALESCE(SUM(v.total_linea), 0),
                          COALESCE(SUM(v.cantidad * v.precio_costo_historico), 0)
                   FROM ventas v"""
            ).fetchone()

    @staticmethod
    def obtener_historial_facturas_df():
        query = """
            SELECT f.id AS Factura, f.fecha AS Fecha, c.nombre AS Cliente,
                   f.subtotal AS Subtotal, f.impuesto AS Impuesto,
                   f.total AS Total, f.metodo_pago AS Pago
            FROM facturas f
            JOIN clientes c ON c.id = f.cliente_id
            ORDER BY f.id DESC
        """
        with SistemaRepuestosBD.obtener_conexion() as conn:
            return pd.read_sql_query(query, conn)
