# Federer Automotriz

Una aplicación de gestión para un almacén de repuestos automotrices. Está pensada para controlar inventario, registrar clientes, procesar ventas y visualizar reportes financieros de forma rápida desde una interfaz web.

## ¿Para qué sirve?

Federer Automotriz ayuda a una tienda o taller de repuestos a llevar el control de:

- Inventario de productos por categoría y marca
- Stock mínimo y alertas de reorden
- Registro de clientes
- Emisión de facturas de venta
- Costo y utilidad por repuestos vendidos
- Historial de ventas y facturas
- Base de datos local con SQLite para operar sin servicios externos

## Funcionalidades principales

### 1) Almacén e inventario
- Ver todos los repuestos disponibles
- Consultar código, nombre, categoría, marca y precio de venta
- Ver el stock actual y el estado de cada producto
- Identificar artículos en nivel crítico de inventario

### 2) Búsqueda de repuestos
- Buscar por código, nombre o marca
- Ver resultados filtrados con información útil para la venta o reabastecimiento

### 3) Carga de nuevos repuestos
- Registrar un repuesto con:
  - código único
  - nombre
  - categoría
  - marca
  - costo
  - precio de venta
  - stock inicial
  - stock mínimo

### 4) Registro de clientes
- Guardar clientes con cédula/RIF, nombre, teléfono y dirección
- Permite asociar una factura a un cliente específico

### 5) Procesar venta
- Elegir cliente
- Elegir repuesto disponible
- Definir cantidad y método de pago
- Validar stock antes de registrar la factura
- Genera la venta y actualiza el inventario automáticamente

### 6) Reabastecimiento
- Incrementar stock de un repuesto específico
- Registrar la entrada de inventario en el historial

### 7) Reportes y ganancias
- Muestra ingresos totales
- Calcula costo de los repuestos vendidos
- Calcula utilidad antes de impuestos
- Muestra historial de facturas con subtotales, impuestos y totales

## Tecnologías utilizadas

- Python
- Streamlit
- SQLite
- Pandas

## Estructura del proyecto

- `app.py`: interfaz principal de la aplicación web
- `operaciones.py`: lógica del negocio, base de datos y reportes
- `base_datos_repuestos_gigante.db`: base de datos local SQLite

## Cómo ejecutar la app

1. Instala las dependencias:

```bash
pip install streamlit pandas
```

2. Desde la raíz del proyecto ejecuta:

```bash
streamlit run app.py
```

3. Abre la URL local que te muestre Streamlit en el navegador.

## Base de datos

La app usa SQLite para guardar:

- categorías
- marcas
- proveedores
- clientes
- repuestos
- facturas
- detalle de ventas
- ventas
- historial de inventario

La base de datos se inicializa automáticamente al arrancar la aplicación y además precarga datos de ejemplo para que puedas probar la app sin configuración previa.

## Caso de uso típico

Un taller o negocio de repuestos puede usar esta app para:

- revisar qué productos tienen stock bajo
- ingresar nuevos repuestos al almacén
- vender artículos a clientes
- emitir facturas con IVA incluido
- analizar ganancia real de las ventas
- llevar un registro del movimiento del inventario

## Resumen

Esta aplicación es un sistema simple pero práctico de punto de venta y control de inventario para repuestos automotrices. Su objetivo principal es ayudar a gestionar operación diaria del almacén sin necesidad de un ERP complejo, con una interfaz fácil de usar y almacenamiento local.
