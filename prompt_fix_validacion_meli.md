# Prompt para Claude Code: CORREGIR Validación de Schema MELI

---

## 🚨 PROBLEMA DETECTADO

La validación de schema no está funcionando porque estamos forzando los nombres de columnas con `names=column_names` ANTES de validar, lo que hace que Pandas ignore las columnas extras del archivo antiguo.

---

## 🎯 SOLUCIÓN

Necesitamos cambiar el orden: primero leer el archivo SIN forzar nombres, validar, y LUEGO aplicar los nombres si pasa la validación.

---

## 📝 INSTRUCCIONES

En las 3 funciones de MELI, reemplazar esta sección:

### **CÓDIGO ACTUAL (INCORRECTO):**

```python
data_MELI = pd.read_excel(uploaded_file_meli, header=None, skiprows=6, names=column_names, sheet_name="Publicaciones")

# Validación estricta del schema
expected_columns = [
    'FAMILY_ID', 'ITEM_ID', 'PRODUCT_NUMBER', 'VARIATION_ID', 'SKU', 'TITLE', 'VARIATIONS',
    'STORE_STOCK_QUANTITY_71348291#COP1326882072', 'STORE_STOCK_QUANTITY_71843625#COP1326882074',
    'STORE_STOCK_QUANTITY_76644462#COP1326882075', 'STORE_STOCK_QUANTITY_71348293#COP1326882073',
    'TOTAL_STOCK_ALL_STORES', 'STOCK_FULL', 'PRICE', 'CURRENCY_ID'
]

if list(data_MELI.columns) != expected_columns:
    st.error("""...""")
    return
```

---

### **CÓDIGO NUEVO (CORRECTO):**

```python
# Primero leer SIN forzar nombres para validar
data_MELI_raw = pd.read_excel(uploaded_file_meli, header=None, skiprows=6, sheet_name="Publicaciones")

# Validación: verificar que tenga exactamente 15 columnas
if data_MELI_raw.shape[1] != 15:
    st.error(f"""
    ❌ **Error: La plantilla de Mercado Libre no tiene el esquema esperado.**
    
    **Problema detectado:**
    - El archivo tiene **{data_MELI_raw.shape[1]} columnas**
    - Se esperaban **15 columnas**
    
    **Se esperaban estas 15 columnas en este orden:**
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
    
    **Nota técnica:** Si estás usando una plantilla antigua, tiene columnas obsoletas como 
    CHANNEL, MARKETPLACE_PRICE, MSHOPS_PRICE, WARRANTY_TYPE, etc. que ya no se usan.
    """)
    return  # Detener ejecución

# Si pasa la validación, AHORA SÍ aplicamos los nombres
data_MELI = data_MELI_raw.copy()
data_MELI.columns = column_names
```

---

## 🎯 UBICACIONES EXACTAS

Reemplazar en estas 3 funciones:

### **Función 1: `pagina_meli_cedi_oviedo()`**
- **Líneas aproximadas:** 34-69
- **Buscar desde:** `data_MELI = pd.read_excel(uploaded_file_meli...`
- **Hasta:** El `return` después del `st.error`

### **Función 2: `pagina_meli_av19_bulevar_oviedo()`**
- **Líneas aproximadas:** 186-221
- **Buscar desde:** `data_MELI = pd.read_excel(uploaded_file_meli...`
- **Hasta:** El `return` después del `st.error`

### **Función 3: `pagina_meli_av19_bulevar_cedi_oviedo()`**
- **Líneas aproximadas:** 346-381
- **Buscar desde:** `data_MELI = pd.read_excel(uploaded_file_meli...`
- **Hasta:** El `return` después del `st.error`

---

## 🔍 EXPLICACIÓN DEL CAMBIO

### **Por qué fallaba antes:**
```python
# ANTES: Forzábamos 15 nombres sobre 20 columnas
data_MELI = pd.read_excel(..., names=column_names)  # column_names tiene 15 elementos
# Pandas dice: "OK, le pongo estos 15 nombres y las otras 5 las ignoro"
# Resultado: data_MELI tiene 15 columnas (las primeras 15 del archivo)
# Validación: list(data_MELI.columns) == expected_columns → TRUE ❌ (falso positivo)
```

### **Por qué funciona ahora:**
```python
# AHORA: Primero leemos TODO
data_MELI_raw = pd.read_excel(..., header=None, skiprows=6)  # SIN names
# Validación: data_MELI_raw.shape[1] == 15 → FALSE si tiene 20 ✅
# Si tiene 20: Mostramos error y detenemos
# Si tiene 15: Continuamos y aplicamos nombres
```

---

## ✅ RESULTADO ESPERADO

Después de este cambio:

1. **Archivo con 20 columnas (antiguo):**
   ```
   ❌ Error: La plantilla de Mercado Libre no tiene el esquema esperado.
   
   Problema detectado:
   - El archivo tiene 20 columnas
   - Se esperaban 15 columnas
   
   [resto del mensaje...]
   ```

2. **Archivo con 15 columnas (nuevo):**
   ```
   ✅ Procesamiento normal
   ```

3. **Archivo con 12 columnas (corrupto):**
   ```
   ❌ Error: La plantilla de Mercado Libre no tiene el esquema esperado.
   
   Problema detectado:
   - El archivo tiene 12 columnas
   - Se esperaban 15 columnas
   
   [resto del mensaje...]
   ```

---

## 📋 CHECKLIST DE VALIDACIÓN

Después de hacer los cambios, prueba:

- [ ] Subir archivo con 20 columnas (antiguo) → Debe mostrar error
- [ ] El error debe decir "El archivo tiene 20 columnas"
- [ ] El error debe decir "Se esperaban 15 columnas"
- [ ] Subir archivo con 15 columnas (nuevo) → Debe procesar correctamente
- [ ] Los 3 cambios están implementados en las 3 funciones

---

## 🚀 INSTRUCCIÓN FINAL

Procede a reemplazar la lógica de validación en las 3 funciones de MELI. El cambio es pequeño pero crítico para que la validación funcione correctamente.

Gracias.
