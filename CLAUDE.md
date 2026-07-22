# MarketMaster — Contexto para Claude

App Streamlit que centraliza la actualización de inventario y precios para múltiples canales ecommerce. El archivo principal es `MarketMasterApp.py` (~1300 líneas).

---

## ERP: formato y columnas de bodegas

El archivo ERP es un **CSV con separador `;` y encoding `latin1`**. Las columnas de inventario por bodega son:

| Columna ERP | Bodega / Ciudad |
|---|---|
| `us01` | Av. 19 (Bogotá) |
| `us02` | Bulevar (Bogotá) |
| `us03` | Calle 74 (Barranquilla) |
| `us04` | Bvista (Barranquilla) |
| `us05` | Oviedo (Medellín) — modo normal |
| `us06` | Cedi — modo normal |
| `us07` | Cedi — solo en modo Feria (ver abajo) |

Columnas clave del ERP: `Codpro` (SKU), `Nompro` (nombre), `Valuni` (precio unitario).

### Modo Feria del Libro

Toggle en el sidebar. Cuando está activo, el ERP inserta una bodega extra (Feria) y desplaza las columnas:

| | Normal | Feria |
|---|---|---|
| `us05` | Oviedo | **Feria** |
| `us06` | Cedi | **Oviedo** |
| `us07` | — | **Cedi** |

Controlado por `COLUMNAS_NORMAL` y `COLUMNAS_FERIA` al inicio del archivo. Cada función recibe `feria_mode=False` y resuelve las columnas dinámicamente con `mapa = COLUMNAS_FERIA if feria_mode else COLUMNAS_NORMAL`.

---

## Plataformas soportadas y sus funciones

### Mercado Libre

**Plantilla:** Excel `.xlsx`, hoja `"Publicaciones"`, 5 filas de encabezado (fila 1 = nombres, filas 2-5 se saltan con `skiprows=range(1,5)`). **Actualmente 16 columnas.**

#### Columnas MELI y su mapeo a bodegas

| Columna MELI (ID numérico) | Bodega |
|---|---|
| `STORE_STOCK_QUANTITY_71348291#COP1326882072` | Bulevar (`us02`) |
| `STORE_STOCK_QUANTITY_77329299#COP1326882076` | Calle 74 (`us03`) |
| `STORE_STOCK_QUANTITY_71843625#COP1326882074` | Cedi (`us06`) |
| `STORE_STOCK_QUANTITY_76644462#COP1326882075` | Oviedo (`us05`) |
| `STORE_STOCK_QUANTITY_71348293#COP1326882073` | Av. 19 (`us01`) |

#### Opciones del dropdown y qué bodegas activa cada una

| Opción | 71348291 Blv | 77329299 C74 | 71843625 Cedi | 76644462 Ovi | 71348293 Av19 |
|---|---|---|---|---|---|
| Cedi + Oviedo | 0 | 0 | us06 | us05 | 0 |
| Cedi + Oviedo + Calle 74 | 0 | us03 | us06 | us05 | 0 |
| Av19 + Blv + Oviedo | us02 | 0 | 0 | us05 | us01 |
| Av19 + Blv + Oviedo + Calle 74 | us02 | us03 | 0 | us05 | us01 |
| Av19 + Blv + Cedi + Oviedo | us02 | 0 | us06 | us05 | us01 |
| Av19 + Blv + Cedi + Oviedo + Calle 74 | us02 | us03 | us06 | us05 | us01 |

#### Parámetro `calle74`

Las 3 funciones MELI reciben `calle74=False`. Cuando `True`, carga `us03` del ERP y lo asigna a la columna `77329299`. Cuando `False`, la columna queda en 0.

#### Lógica de grupos (variaciones)

Los productos se agrupan por `ITEM_ID`:
- **1 fila** (producto simple): se asigna inventario y precio directo.
- **>1 fila** (con variaciones): las filas con `SKU` no nulo reciben inventario. La fila "padre" (SKU nulo) hereda el precio de la primera variación con SKU.

El precio tiene fallback: si no cruza con ERP, conserva el `PRICE` original de MELI.

#### Output

Se escribe de vuelta en la plantilla original (preservando formato con `openpyxl`). Datos desde fila 6. Las filas anteriores se borran con `ws.delete_rows(6, max_row - 5)` antes de escribir.

---

### Falabella

- **Archivos de entrada:** precios (Excel `.xlsx`) + inventario (CSV `;`) + ERP (CSV)
- **Bodega:** `us02` (Bulevar)
- **Output:** Excel de precios modificado + CSV de inventario
- Función: `pagina_falabella(feria_mode)`

---

### Rappi

Función genérica `procesar_rappi()` reutilizada para cada ciudad. El archivo Rappi es Excel `.xlsx`, hoja `"Productos"`, 5 filas de encabezado.

| Ciudad | Función dropdown | ID tienda → columna ERP |
|---|---|---|
| Bogotá | `pagina_rappi_ciudad(...)` | `900243006` → `us01` (Av.19), `900243075` → `us02` (Blv) |
| Barranquilla | `pagina_rappi_ciudad(...)` | `900243002` → `us04` (Bvista), `900246112` → `us03` (C74) |
| Medellín | `pagina_rappi_ciudad(...)` | `900418701` → `us05` (normal) / `us06` (feria) |

Los SKUs en Rappi tienen prefijo `jugandoyeducandoco_` que se limpia antes del cruce y se restaura al final. La disponibilidad (`SI`/`NO`) se calcula según `Inventario > 0`.

---

### Wix — deprecado

**Canal deprecado:** ya no se vende por Wix. Las funciones antiguas siguen en `MarketMasterApp.py` solo por trazabilidad, pero las opciones de Wix fueron retiradas del menú principal y no deben usarse para operación diaria.

CSV de exportación de Wix. Tiene 53 columnas con nombres fijos definidos en `column_names`.

| Opción | Bodegas sumadas |
|---|---|
| Av. 19 + Bulevar | `us01 + us02` |
| Av. 19 + Bulevar + Cedi | `us01 + us02 + col_cedi` |

El campo `visible` se calcula: `TRUE` si `inventory > 0`, `FALSE` si no. El output se parte en fragmentos de 4000 filas (límite de importación de Wix).

---

### Shopify

Dos secciones independientes en la misma página:

1. **Inventario:** CSV de "Inventory Export". Selector manual:
   - `Lunes a viernes`: `us01 + us02 + col_cedi` (normal `us06`, feria `us07`).
   - `Sábado o domingo`: `us01 + us02`.
   Columna de salida: `On hand (new)`.
2. **Precios:** CSV de "Products Export". Solo actualiza `Variant Price` donde hay match por SKU. Exporta solo 4 columnas mínimas: `Handle`, `Title`, `Variant SKU`, `Variant Price`.

Los SKUs del export de Shopify pueden tener prefijo `'` (truco de Excel) que se limpia con `str.lstrip("'")` solo para el cruce, sin modificar la columna original.

### Shopify con descuento

Opción independiente del menú. Es una copia funcional de la página Shopify normal:
- **Inventario:** mismo flujo que Shopify normal, con selector `Lunes a viernes` / `Sábado o domingo` y soporte de modo Feria.
- **Precios:** aplica un descuento permanente del 10% a productos de estas marcas:

`Maisto`, `Clementoni`, `Learning Resources`, `Asmodee`, `Be Amazing! Toys`, `VTech`, `Infantino`.

Entrada para precios: CSV(s) de "Products Export" de Shopify. La sección de precios con descuento no usa ERP.

Lógica:
- Detecta marca desde `Marca (product.metafields.custom.marca)` si existe, o desde `Vendor`.
- Aplica el match por producto/`Handle` para cubrir variantes aunque Shopify deje la marca vacía en filas secundarias.
- Copia el `Variant Price` actual a `Variant Compare At Price`.
- Calcula el nuevo `Variant Price` como `precio_actual * 0.90`.
- Redondea el resultado a la centena más cercana, dejando los últimos dos dígitos en `00`.
- Exporta solo filas de variantes afectadas con columnas mínimas: `Handle`, `Title`, `Variant SKU`, `Variant Price`, `Variant Compare At Price`.

---

### Addi

Dos secciones independientes:

1. **Precios:** Excel `.xlsx` ("Base Prices"). Llave de cruce: `Ref ID (View Only)` ↔ `Codpro`. Actualiza columnas `Cost Price` y `Base Price` (redondeadas a entero). Preserva formato del Excel original con `openpyxl`.
2. **Inventario:** `.xls` o `.xlsx` (soporta ambos con `engine='calamine'`). Bodegas: `us01 + us02`. Actualiza `TotalQuantity`. El output es `.xls` (Excel 97-2003) usando `xlwt`.

---

## Patrones comunes del código

- **Limpieza de SKU** (idéntica en todas las funciones): `astype(str)` → `str.replace(r'\.0$','',regex=True)` → `str.strip()` → `replace('nan', np.nan)`.
- **Limpieza ERP:** se filtran filas con `Codpro` nulo, vacío o con carácter `\x1a` (EOF de DOS).
- **Merge:** siempre `how='left'` sobre el archivo de la plataforma (preserva todas las filas originales).
- **Fallback de precio:** `final_df['PRICE'].fillna(final_df['Original_Price'])` — si no cruza con ERP, conserva el precio original.
- **`VARIATION_ID`:** se convierte a `str(int(x))` para evitar notación científica; leer como `str` desde el inicio si hay problemas de precisión con floats grandes.
