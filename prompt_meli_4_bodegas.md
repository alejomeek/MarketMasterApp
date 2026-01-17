# Prompt para Agregar "Mercado Libre - Av. 19 + Bulevar + Cedi + Oviedo"

---

Necesito que agregues una nueva configuración de Mercado Libre en @MarketMasterApp.py que combine inventarios de las 4 bodegas activas.

## 📋 Instrucciones

### 1. Crear Nueva Función

Duplica la función `pagina_meli_av19_bulevar_oviedo()` y renómbrala como `pagina_meli_av19_bulevar_cedi_oviedo()`.

### 2. Cambios Específicos en la Nueva Función

#### A) Cambiar el título (línea ~136)
```python
st.markdown("### 🛒 Mercado Libre - Av. 19 + Bulevar + Cedi + Oviedo")
```

#### B) Cambiar las keys de Streamlit (líneas ~147-151)
```python
uploaded_file_meli = st.file_uploader("📤 Cargar archivo Excel de Mercado Libre", type=['xlsx'], key="meli_4bod_excel")
uploaded_file_erp = st.file_uploader("🧾 Cargar archivo CSV de ERP", type=['csv'], key="meli_4bod_erp")

if uploaded_file_meli and uploaded_file_erp:
    if st.button('🔄 Procesar MELI (4 Bodegas)', key="meli_4bod_process"):
```

#### C) Agregar us06 a la carga de columnas (línea ~161)
```python
# Cargar columnas necesarias: us01, us02, us05, us06
data_ERP = data_ERP[["Codpro", "Nompro", "Valuni", "us01", "us02", "us05", "us06"]]
```

#### D) Preparar us06 (líneas ~162-170)
```python
data_ERP['us01'] = data_ERP['us01'].fillna(0)
data_ERP['us02'] = data_ERP['us02'].fillna(0)
data_ERP['us05'] = data_ERP['us05'].fillna(0)
data_ERP['us06'] = data_ERP['us06'].fillna(0)  # ← AGREGAR ESTA LÍNEA

data_ERP["Inventario_us01"] = data_ERP["us01"]
data_ERP["Inventario_us02"] = data_ERP["us02"]
data_ERP["Inventario_us05"] = data_ERP["us05"]
data_ERP["Inventario_us06"] = data_ERP["us06"]  # ← AGREGAR ESTA LÍNEA

data_ERP = data_ERP.drop(["us01", "us02", "us05", "us06"], axis=1)  # ← AGREGAR us06 al drop
```

#### E) Cambiar asignación de STORE_71843625 en productos SIN variaciones (línea ~202)
```python
if group.shape[0] == 1:
    # 71348291 -> us02
    group.loc[:, "STORE_STOCK_QUANTITY_71348291#COP1326882072"] = group["Inventario_us02"]
    # 71348293 -> us01
    group.loc[:, "STORE_STOCK_QUANTITY_71348293#COP1326882073"] = group["Inventario_us01"]
    # 71843625 -> us06  ← CAMBIAR DE 0 A us06
    group.loc[:, "STORE_STOCK_QUANTITY_71843625#COP1326882074"] = group["Inventario_us06"]
    # 76644462 -> us05
    group.loc[:, "STORE_STOCK_QUANTITY_76644462#COP1326882075"] = group["Inventario_us05"]
```

#### F) Cambiar asignación de STORE_71843625 en productos CON variaciones (línea ~216)
```python
elif group.shape[0] > 1:
    # 71348291 -> us02
    group.loc[group.SKU.notna(), "STORE_STOCK_QUANTITY_71348291#COP1326882072"] = group.loc[group.SKU.notna(), "Inventario_us02"]
    # 71348293 -> us01
    group.loc[group.SKU.notna(), "STORE_STOCK_QUANTITY_71348293#COP1326882073"] = group.loc[group.SKU.notna(), "Inventario_us01"]
    # 71843625 -> us06  ← CAMBIAR DE 0 A us06
    group.loc[group.SKU.notna(), "STORE_STOCK_QUANTITY_71843625#COP1326882074"] = group.loc[group.SKU.notna(), "Inventario_us06"]
    # 76644462 -> us05
    group.loc[group.SKU.notna(), "STORE_STOCK_QUANTITY_76644462#COP1326882075"] = group.loc[group.SKU.notna(), "Inventario_us05"]
```

#### G) Cambiar consolidación final de STORE_71843625 (línea ~237)
```python
# ANTES (en la función av19_bulevar_oviedo)
final_df['STORE_STOCK_QUANTITY_71843625#COP1326882074'] = 0

# AHORA (en la nueva función)
final_df['STORE_STOCK_QUANTITY_71843625#COP1326882074'] = final_df['STORE_STOCK_QUANTITY_71843625#COP1326882074'].fillna(0)
```

#### H) Agregar us06 al drop de columnas finales (línea ~241)
```python
final_df = final_df.drop(['Nompro', 'Valuni', 'Inventario_us01', 'Inventario_us02', 'Inventario_us05', 'Inventario_us06', 'original_order', 'Original_Price'], axis=1)
```

#### I) Cambiar nombre del archivo de salida (línea ~257)
```python
file_name="MELI_AV19_BLV_CEDI_OVI_ACTUALIZADO.xlsx"
```

### 3. Actualizar el Menú Principal

#### A) Agregar opción en el menú (línea ~510)
```python
opciones = [
    "Mercado Libre - Cedi + Oviedo",
    "Mercado Libre - Av. 19 + Bulevar + Oviedo",
    "Mercado Libre - Av. 19 + Bulevar + Cedi + Oviedo",  # ← NUEVA OPCIÓN
    "Falabella",
    "Rappi - Bogotá",
    "Rappi - Barranquilla",
    "Rappi - Medellín",
    "Wix"
]
```

#### B) Agregar routing (después de línea ~528)
```python
elif opcion == "Mercado Libre - Av. 19 + Bulevar + Cedi + Oviedo":
    pagina_meli_av19_bulevar_cedi_oviedo()
```

---

## 🎯 Resumen de la Configuración

La nueva configuración debe quedar así:

| Tienda MELI | Bodega ERP | Valor |
|-------------|------------|-------|
| STORE_71348291 (COP1326882072) | us02 | Inventario Bulevar |
| STORE_71348293 (COP1326882073) | us01 | Inventario Av. 19 |
| STORE_71843625 (COP1326882074) | us06 | Inventario Cedi |
| STORE_76644462 (COP1326882075) | us05 | Inventario Oviedo |

---

## ⚠️ Punto Crítico

La **diferencia clave** con la configuración "Av. 19 + Bulevar + Oviedo" es que:
- En "Av19+Blv+Ovi": STORE_71843625 siempre es 0
- En "Av19+Blv+Cedi+Ovi": STORE_71843625 toma el valor de us06

Por favor, asegúrate de cambiar tanto las líneas de asignación (202 y 216) como la línea de consolidación final (237).

---

## ✅ Checklist de Validación

Por favor verifica que:
- [ ] La nueva función tiene keys únicos de Streamlit (meli_4bod_*)
- [ ] Se cargan las 4 columnas: us01, us02, us05, us06
- [ ] Se hace fillna(0) en las 4 columnas
- [ ] Se crean las 4 columnas de inventario: Inventario_us01, Inventario_us02, Inventario_us05, Inventario_us06
- [ ] STORE_71843625 se asigna desde Inventario_us06 (NO 0)
- [ ] La consolidación final usa fillna(0) para STORE_71843625 (NO asignación directa a 0)
- [ ] Se hace drop de las 4 columnas de inventario al final
- [ ] La opción aparece en el menú
- [ ] El routing funciona correctamente

---

Procede con los cambios. Gracias.
