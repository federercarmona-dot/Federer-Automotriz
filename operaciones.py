import sqlite3
import os
from datetime import datetime

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
    """Clase encargada de las operaciones del almacén y catálogos de repuestos."""
    
    @staticmethod
    def registrar_repuesto(codigo, nombre, categoria_id, marca_id, proveedor_id, costo, venta, stock, stock_min):
        try:
            with SistemaRepuestosBD.obtener_conexion() as conn:
                conn.execute('''
                    INSERT INTO repuestos (codigo, nombre, categoria_id, marca_id, proveedor_id, precio_costo, precio_venta, stock, stock_minimo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (codigo.upper(), nombre, categoria_id, marca_id, proveedor_id, costo, venta, stock, stock_min))
                print(f"\n✅ ¡Repuesto '{nombre}' registrado exitosamente en el catálogo!")
        except sqlite3.IntegrityError:
            print("\n⚠️ Error: El CÓDIGO de repuesto ya existe o los IDs asociados no son válidos.")

    @staticmethod
    def reabastecer_stock(repuesto_id, cantidad_ingreso):
        """Suma stock a un repuesto existente y deja registro en el historial."""
        if cantidad_ingreso <= 0:
            print("\n❌ La cantidad a ingresar debe ser mayor a cero.")
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
                print(f"\n✅ Se agregaron {cantidad_ingreso} unidades al Repuesto ID {repuesto_id}.")
        except Exception as e:
            print(f"\n❌ Error al reabastecer inventario: {e}")

    @staticmethod
    def buscar_por_nombre_o_codigo(criterio):
        """Busca repuestos que coincidan parcialmente con un texto o código."""
        with SistemaRepuestosBD.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.id, r.codigo, r.nombre, m.nombre, r.precio_venta, r.stock
                FROM repuestos r
                LEFT JOIN marcas_vehiculos m ON r.marca_id = m.id
                WHERE r.nombre LIKE ? OR r.codigo LIKE ?
            ''', (f"%{criterio}%", f"%{criterio}%"))
            filas = cursor.fetchall()
            
            if not filas:
                print(f"\n🔍 No se encontraron repuestos que coincidan con: '{criterio}'")
                return
                
            print("\n🔍 --- RESULTADOS DE BÚSQUEDA ---")
            print(f"{'ID':<4} | {'CÓDIGO':<10} | {'DESCRIPCIÓN':<30} | {'MARCA':<12} | {'PRECIO':<8} | {'STOCK'}")
            print("-" * 75)
            for f in filas:
                print(f"{f[0]:<4} | {f[1]:<10} | {f[2]:<30} | {str(f[3]):<12} | ${f[4]:<7.2f} | {f[5]}")

    @staticmethod
    def listar_inventario_completo():
        """Muestra de forma organizada todos los repuestos con alertas visuales de stock bajo."""
        with SistemaRepuestosBD.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.id, r.codigo, r.nombre, c.nombre, m.nombre, r.precio_venta, r.stock, r.stock_minimo
                FROM repuestos r
                LEFT JOIN categorias c ON r.categoria_id = c.id
                LEFT JOIN marcas_vehiculos m ON r.marca_id = m.id
            ''')
            filas = cursor.fetchall()
            
            print("\n" + "="*96)
            print(f"{'ID':<4} | {'CÓDIGO':<10} | {'DESCRIPCIÓN DEL REPUESTO':<30} | {'CATEGORÍA':<12} | {'MARCA':<10} | {'PRECIO':<8} | {'STOCK':<5} | {'ESTADO'}")
            print("="*96)
            for f in filas:
                alerta = "🔴 REORDEN" if f[6] <= f[7] else "🟢 OK"
                print(f"{f[0]:<4} | {f[1]:<10} | {f[2]:<30} | {str(f[3]):<12} | {str(f[4]):<10} | ${f[5]:<6.2f} | {f[6]:<5} | {alerta}")
            print("="*96 + "\n")


# =====================================================================
# 3. CAPA TRANSACCIONAL: PROCESAMIENTO DE VENTAS Y FACTURACIÓN
# =====================================================================
class GestorVentas:
    """Clase crítica que maneja la facturación y el resguardo de transacciones."""
    
    @staticmethod
    def registrar_cliente(cedula, nombre, telefono, direccion):
        try:
            with SistemaRepuestosBD.obtener_conexion() as conn:
                conn.execute(
                    "INSERT INTO clientes (cedula_rif, nombre, telefono, direccion) VALUES (?, ?, ?, ?)",
                    (cedula, nombre, telefono, direccion)
                )
                print(f"\n✅ Cliente '{nombre}' registrado con éxito.")
        except sqlite3.IntegrityError:
            print("\n⚠️ El cliente con esa Cédula/RIF ya se encuentra registrado.")

    @staticmethod
    def listar_clientes():
        with SistemaRepuestosBD.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, cedula_rif, nombre, telefono FROM clientes")
            filas = cursor.fetchall()
            
            print("\n--- CATÁLOGO DE CLIENTES ---")
            for f in filas:
                print(f"ID: {f[0]} | RIF: {f[1]} | Nombre: {f[2]} | Tlf: {f[3]}")

    @classmethod
    def realizar_venta_maestra(cls, cliente_id, lista_productos, metodo_pago="Efectivo"):
        """Procesa una venta multi-producto de manera transaccional controlada."""
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
            print(f"\n🎉 ¡VENTA PROCESADA EXITOSAMENTE!")
            print(f"🧾 Factura Nro: {factura_id} | Total con IVA: ${total_factura:.2f} ({metodo_pago})")
            return factura_id
            
        except Exception as e:
            cursor.execute("ROLLBACK;")
            print(f"\n❌ TRANSACCIÓN CANCELADA: {e}")
            return None
        finally:
            conexion.close()


# =====================================================================
# 4. CAPA ANALÍTICA: BALANCES GERENCIALES Y REPORTE DE CAJA
# =====================================================================
class ModuloReportes:
    """Calcula utilidades basándose en los costos de adquisición y precios de salida."""
    
    @staticmethod
    def ver_resumen_ganancias_caja():
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
            
            print("\n📊 " + "="*40)
            print("     REPORTE FINANCIERO DE CAJA      ")
            print("="*40)
            if res and res[0] is not None:
                print(f"💰 Ingresos Netos Facturados:  ${res[0]:,.2f}")
                print(f"📦 Costo de Inversión Inicial:  ${res[1]:,.2f}")
                print(f"📈 Margen de Utilidad Neto:    ${res[2]:,.2f}")
            else:
                print("No se registran transacciones de venta facturadas.")
            print("="*40 + "\n")

    @staticmethod
    def mostrar_historial_facturas():
        with SistemaRepuestosBD.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT f.id, f.fecha, c.nombre, f.total, f.metodo_pago
                FROM facturas f
                JOIN clientes c ON f.cliente_id = c.id
                ORDER BY f.id DESC
            ''')
            filas = cursor.fetchall()
            
            print("\n📜 --- HISTORIAL GENERAL DE AUDITORÍA DE FACTURAS ---")
            for f in filas:
                print(f"Factura Nº: {f[0]} | Fecha: {f[1]} | Cliente: {f[2]} | Total Cobrado: ${f[3]:.2f} | Pago: {f[4]}")

# =====================================================================
# 5. MENÚ INTERACTIVO EN CONSOLA (INTERFAZ DE USUARIO CONTINUA)
# =====================================================================
def mostrar_menu_principal():
    print("\n==================================================")
    print("  🏎️  SISTEMA AVANZADO DE REPUESTOS 'FEDERER V' 🏎️")
    print("==================================================")
    print("1. Ver Almacén e Inventario de Repuestos")
    print("2. Buscar Repuesto por Nombre o Código")
    print("3. Cargar / Registrar un Nuevo Repuesto")
    print("4. Registrar un Nuevo Cliente en la Base de Datos")
    print("5. Procesar Nueva Factura de Venta (Carrito)")
    print("6. Cargar Entrada de Stock (Reabastecer)")
    print("7. Ver Reporte Completo de Ganancias y Caja")
    print("8. Ver Historial de Facturas Emitidas")
    print("9. Salir del Sistema")
    print("==================================================")

def bucle_aplicacion():
    SistemaRepuestosBD.inicializar_bd()
    SistemaRepuestosBD.precargar_datos_ejemplo()
    
    while True:
        mostrar_menu_principal()
        opcion = input("Seleccione una opción (1-9): ").strip()
        
        if opcion == "1":
            print("\n--- INVENTARIO EN TIEMPO REAL ---")
            AdministradorInventario.listar_inventario_completo()
            
        elif opcion == "2":
            criterio = input("\nIngrese el nombre o código del repuesto a buscar: ").strip()
            AdministradorInventario.buscar_por_nombre_o_codigo(criterio)
            
        elif opcion == "3":
            print("\n--- REGISTRO DE PRODUCTO NUEVO ---")
            try:
                cod = input("Código único de fábrica (Ej: FIL-202): ").strip()
                nom = input("Descripción / Nombre del repuesto: ").strip()
                print("Categorías base: 1-Motor, 2-Frenos, 3-Suspensión, 4-Eléctrico")
                cat_id = int(input("Número de ID de Categoría (1-4): "))
                print("Marcas compatibles: 1-Toyota, 2-Chevrolet, 3-Ford, 4-Hyundai")
                mar_id = int(input("Número de ID de Marca (1-4): "))
                costo = float(input("Precio de Costo de adquisición ($): "))
                venta = float(input("Precio de Venta final al cliente ($): "))
                stock = int(input("Unidades físicas ingresando a almacén: "))
                st_min = int(input("Mínimo crítico para alerta de reorden: "))
                
                AdministradorInventario.registrar_repuesto(cod, nom, cat_id, mar_id, 1, costo, venta, stock, st_min)
            except ValueError:
                print("\n❌ Error: Los datos de precio, categorías y stocks deben ser numéricos.")
            
        elif opcion == "4":
            print("\n--- REGISTRO DE CLIENTES ---")
            ced = input("Cédula o RIF del cliente: ").strip()
            nom = input("Nombre y Apellido completo: ").strip()
            tlf = input("Número telefónico de contacto: ").strip()
            dire = input("Dirección de entrega / domicilio: ").strip()
            GestorVentas.registrar_cliente(ced, nom, tlf, dire)
            
        elif opcion == "5":
            print("\n--- MÓDULO DE FACTURACIÓN ---")
            AdministradorInventario.listar_inventario_completo()
            GestorVentas.listar_clientes()
            
            try:
                c_id = int(input("\nID del Cliente que compra (Use 1 para Consumidor Final): "))
                carrito = []
                
                while True:
                    r_id = input("ID del Repuesto a vender (o marca 'F' para cerrar venta): ").strip()
                    if r_id.upper() == 'F':
                        break
                    
                    cant = int(input(f"Cantidad de piezas para el Repuesto ID {r_id}: "))
                    carrito.append({'id': int(r_id), 'cantidad': cant})
                    print("🛒 Artículo añadido al carro de compras.")
                
                if carrito:
                    met = input("Método de pago (Efectivo / Tarjeta / Transferencia): ").strip().capitalize()
                    if met not in ['Efectivo', 'Tarjeta', 'Transferencia']:
                        met = 'Efectivo'
                    GestorVentas.realizar_venta_maestra(c_id, carrito, met)
                else:
                    print("\n⚠️ El carrito de compras está vacío.")
            except ValueError:
                print("\n❌ Error: Los identificadores y cantidades ingresadas deben ser números enteros.")
            
        elif opcion == "6":
            print("\n--- REABASTECIMIENTO DE PRODUCTO ---")
            try:
                r_id = int(input("ID del Repuesto a ingresar mercancía: "))
                cant = int(input("Cantidad de nuevas unidades recibidas: "))
                AdministradorInventario.reabastecer_stock(r_id, cant)
            except ValueError:
                print("\n❌ Error: Ingrese números enteros válidos.")
                
        elif opcion == "7":
            ModuloReportes.ver_resumen_ganancias_caja()
            
        elif opcion == "8":
            ModuloReportes.mostrar_historial_facturas()
            
        elif opcion == "9":
            print("\n🤖 Guardando datos y cerrando conexiones con la base de datos... ¡Mucho éxito en tu negocio!")
            break
        else:
            print("\n⚠️ Opción no válida del menú, intente de nuevo marcando un número del 1 al 9.")

# =====================================================================
# BLOQUE DEFINITIVO DE ARRANQUE LIMPIO
# =====================================================================
if __name__ == "__main__":
    bucle_aplicacion()
    