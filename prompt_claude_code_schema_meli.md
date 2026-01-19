# Prompt para Claude Code: Actualizar Schema de Mercado Libre + Validación

---

## 📋 CONTEXTO

Las columnas del archivo de Mercado Libre cambiaron. Necesito que actualices las 3 funciones de MELI en @MarketMasterApp.py y agregues validación estricta de schema.

---

## 🎯 TAREAS A REALIZAR

### **TAREA 1: Actualizar Schema en las 3 Funciones de MELI**

Las 3 funciones afectadas son:
1. `pagina_meli_cedi_oviedo()` (línea ~16)
2. `pagina_meli_av19_bulevar_oviedo()` (línea ~135)
3. `pagina_meli_av19_bulevar_cedi_oviedo()` (línea ~262)

#### **Nuevo Schema (15 columnas):**

```python
column_names = [
    'FAMILY_ID', 
    'ITEM_ID', 
    'PRODUCT_NUMBER', 
    'VARIATION_ID', 
    'SKU', 
    'TITLE', 
    'VARIATIONS',
    'STORE_STOCK_QUANTITY_71348291#COP1326882072', 
    'STORE_STOCK_QUANTITY_71843625#COP1326882074',
    'STORE_STOCK_QUANTITY_76644462#COP1326882075', 
    'STORE_STOCK_QUANTITY_71348293#COP1326882073',
    'TOTAL_STOCK_ALL_STORES', 
    'STOCK_FULL', 
    'PRICE', 
    'CURRENCY_ID'
]
```

**Cambios vs versión anterior:**
- ❌ Eliminadas: `CHANNEL`, `MARKETPLACE_PRICE`, `MSHOPS_PRICE`, `MSHOPS_PRICE_SYNC`, `LISTING_TYPE`, `FEE_PER_SALE_MARKETPLACE`, `FEE_PER_SALE_MSHOPS`
- ✅ Agregadas: `STOCK_FULL`, `PRICE` (reemplaza MARKETPLACE_PRICE y MSHOPS_PRICE)
- 📝 Total: 19 columnas → 15 columnas

---

### **TAREA 2: Actualizar Lógica de Precios**

En las 3 funciones, cambiar:

#### **A) Backup de precio original (líneas ~65, ~191, ~319)**

**ANTES:**
```python
merged_data['Original_Price'] = merged_data['MARKETPLACE_PRICE']
```

**AHORA:**
```python
merged_data['Original_Price'] = merged_data['PRICE']
```

#### **B) Asignación de precios en productos SIN variaciones (líneas ~80-81, ~207-208, ~336-337)**

**ANTES:**
```python
group.loc[:, "MARKETPLACE_PRICE"] = group["Valuni"]
group.loc[:, "MSHOPS_PRICE"] = group["Valuni"]
```

**AHORA:**
```python
group.loc[:, "PRICE"] = group["Valuni"]
```

#### **C) Asignación de precios en productos CON variaciones (líneas ~97-98, ~225-226, ~354-355)**

**ANTES:**
```python
group.loc[group.SKU.isna(), "MARKETPLACE_PRICE"] = price_to_set
group.loc[group.SKU.isna(), "MSHOPS_PRICE"] = price_to_set
```

**AHORA:**
```python
group.loc[group.SKU.isna(), "PRICE"] = price_to_set
```

#### **D) Restaurar precio original (líneas ~103, ~231, ~360)**

**ANTES:**
```python
final_df['MARKETPLACE_PRICE'] = final_df['MARKETPLACE_PRICE'].fillna(final_df['Original_Price'])
```

**AHORA:**
```python
final_df['PRICE'] = final_df['PRICE'].fillna(final_df['Original_Price'])
```

---

### **TAREA 3: Agregar Validación de Schema**

En las 3 funciones, **inmediatamente después** de cargar el archivo Excel (después de la línea `data_MELI = pd.read_excel(...)`), agregar:

```python
# Validación estricta del schema
expected_columns = [
    'FAMILY_ID', 'ITEM_ID', 'PRODUCT_NUMBER', 'VARIATION_ID', 'SKU', 'TITLE', 'VARIATIONS',
    'STORE_STOCK_QUANTITY_71348291#COP1326882072', 'STORE_STOCK_QUANTITY_71843625#COP1326882074',
    'STORE_STOCK_QUANTITY_76644462#COP1326882075', 'STORE_STOCK_QUANTITY_71348293#COP1326882073',
    'TOTAL_STOCK_ALL_STORES', 'STOCK_FULL', 'PRICE', 'CURRENCY_ID'
]

if list(data_MELI.columns) != expected_columns:
    st.error("""
    ❌ **Error: La plantilla de Mercado Libre no tiene el esquema esperado.**
    
    **Se esperaban 15 columnas en este orden:**
    1. FAMILY_ID
    2. ITEM_ID
    3. PRODUCT_NUMBER
    4. VARIATION_ID
    5. SKU
    6. TITLE
    7. VARIATIONS
    8. STORE_STOCK_QUANTITY_71348291#COP1326882072
    9. STORE_STOCK_QUANTITY_71843625#COP1326882074
    10. STORE_STOCK_QUANTITY_76644462#COP1326882075
    11. STORE_STOCK_QUANTITY_71348293#COP1326882073
    12. TOTAL_STOCK_ALL_STORES
    13. STOCK_FULL
    14. PRICE
    15. CURRENCY_ID
    
    **Por favor:**
    - Descarga la plantilla más reciente desde tu panel de Mercado Libre
    - O escribe a Alejandro o envía mensaje en el grupo de WhatsApp de MarketMaster
    """)
    return  # Detener ejecución
```

**Ubicación exacta:** Después de estas líneas aproximadamente:
- Función 1 (Cedi+Ovi): Después de línea ~35
- Función 2 (Av19+Blv+Ovi): Después de línea ~154
- Función 3 (Av19+Blv+Cedi+Ovi): Después de línea ~281

---

### **TAREA 4: Verificar que STOCK_FULL no se toque**

Asegúrate de que en ninguna parte del código se modifique la columna `STOCK_FULL`. Esta columna debe permanecer intacta durante todo el procesamiento.

---

## 📊 RESUMEN DE CAMBIOS POR FUNCIÓN

### **Para CADA una de las 3 funciones:**

1. ✅ Actualizar `column_names` (19 cols → 15 cols)
2. ✅ Agregar validación de schema después de `pd.read_excel()`
3. ✅ Cambiar `merged_data['Original_Price'] = merged_data['MARKETPLACE_PRICE']` → `merged_data['PRICE']`
4. ✅ Cambiar asignación de precios en productos SIN variaciones (2 líneas → 1 línea)
5. ✅ Cambiar asignación de precios en productos CON variaciones (2 líneas → 1 línea)
6. ✅ Cambiar restauración de precio original (`MARKETPLACE_PRICE` → `PRICE`)

**Total de cambios por función: 6 cambios**
**Total en las 3 funciones: 18 cambios**

---

## ✅ CHECKLIST DE VALIDACIÓN

Por favor verifica después de hacer los cambios:

### **Schema:**
- [ ] Las 3 funciones tienen el nuevo `column_names` con 15 columnas
- [ ] El orden de las columnas es exacto
- [ ] No hay columnas antiguas (CHANNEL, MARKETPLACE_PRICE, etc.)

### **Validación:**
- [ ] Las 3 funciones validan el schema después de `pd.read_excel()`
- [ ] El mensaje de error menciona las 15 columnas
- [ ] El mensaje menciona "escribir a Alejandro o WhatsApp"
- [ ] La función usa `return` para detener ejecución si falla validación

### **Lógica de Precios:**
- [ ] Se usa `PRICE` en lugar de `MARKETPLACE_PRICE`
- [ ] Ya no se usa `MSHOPS_PRICE` en ninguna parte
- [ ] Productos sin variaciones: 1 línea de asignación de precio (no 2)
- [ ] Productos con variaciones: 1 línea de asignación de precio (no 2)
- [ ] Backup de precio original usa `PRICE`
- [ ] Restauración de precio usa `PRICE`

### **STOCK_FULL:**
- [ ] La columna `STOCK_FULL` no se modifica en ninguna parte
- [ ] La columna `STOCK_FULL` está en `column_names`
- [ ] La columna `STOCK_FULL` está en la validación

---

## 🎯 RESULTADO ESPERADO

Después de estos cambios:

1. **Las 3 funciones de MELI funcionarán con el nuevo formato** de Mercado Libre
2. **Si alguien sube un archivo con el formato antiguo**, verá un error claro y sabrá qué hacer
3. **La lógica de precios está simplificada** (1 columna en lugar de 2)
4. **El código es más robusto** gracias a la validación estricta

---

## 📝 NOTAS IMPORTANTES

1. **Mantén toda la lógica de inventarios intacta** - Solo estamos cambiando schema y precios
2. **Las 4 columnas STORE_STOCK_QUANTITY siguen igual** - No cambian
3. **La lógica de variaciones sigue igual** - Solo cambia la columna de precio
4. **STOCK_FULL es read-only** - No la toques en ningún procesamiento

---

## 🚀 INSTRUCCIÓN FINAL

Procede a hacer todos los cambios en las 3 funciones de MELI:
1. `pagina_meli_cedi_oviedo()`
2. `pagina_meli_av19_bulevar_oviedo()`
3. `pagina_meli_av19_bulevar_cedi_oviedo()`

Después de completar, confirma que los 18 cambios (6 por función × 3 funciones) fueron implementados correctamente.

Gracias.
