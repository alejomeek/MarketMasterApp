# Prompt para Claude Code: Cambiar skiprows de 6 a 5 en Funciones MELI

---

## 📋 CONTEXTO

El formato del archivo de Mercado Libre cambió y ahora las primeras 5 filas son metadata (antes eran 6). Necesito actualizar el parámetro `skiprows` en las 3 funciones de MELI.

---

## 🎯 TAREA

Cambiar `skiprows=6` a `skiprows=5` en todas las llamadas a `pd.read_excel()` dentro de las 3 funciones de Mercado Libre.

---

## 📝 UBICACIONES EXACTAS

### **Función 1: `pagina_meli_cedi_oviedo()`**

**Buscar:**
```python
data_MELI_raw = pd.read_excel(uploaded_file_meli, header=None, skiprows=6, sheet_name="Publicaciones")
```

**Reemplazar con:**
```python
data_MELI_raw = pd.read_excel(uploaded_file_meli, header=None, skiprows=5, sheet_name="Publicaciones")
```

**Línea aproximada:** ~34

---

### **Función 2: `pagina_meli_av19_bulevar_oviedo()`**

**Buscar:**
```python
data_MELI_raw = pd.read_excel(uploaded_file_meli, header=None, skiprows=6, sheet_name="Publicaciones")
```

**Reemplazar con:**
```python
data_MELI_raw = pd.read_excel(uploaded_file_meli, header=None, skiprows=5, sheet_name="Publicaciones")
```

**Línea aproximada:** ~186

---

### **Función 3: `pagina_meli_av19_bulevar_cedi_oviedo()`**

**Buscar:**
```python
data_MELI_raw = pd.read_excel(uploaded_file_meli, header=None, skiprows=6, sheet_name="Publicaciones")
```

**Reemplazar con:**
```python
data_MELI_raw = pd.read_excel(uploaded_file_meli, header=None, skiprows=5, sheet_name="Publicaciones")
```

**Línea aproximada:** ~346

---

## 🔍 EXPLICACIÓN DEL CAMBIO

**Antes (skiprows=6):**
```
Fila 1: Metadata  ⏭️ Ignorada
Fila 2: Metadata  ⏭️ Ignorada
Fila 3: Metadata  ⏭️ Ignorada
Fila 4: Metadata  ⏭️ Ignorada
Fila 5: Metadata  ⏭️ Ignorada
Fila 6: Metadata  ⏭️ Ignorada
Fila 7: FAMILY_ID,ITEM_ID,... ← Empezaba a leer aquí
```

**Ahora (skiprows=5):**
```
Fila 1: Metadata  ⏭️ Ignorada
Fila 2: Metadata  ⏭️ Ignorada
Fila 3: Metadata  ⏭️ Ignorada
Fila 4: Metadata  ⏭️ Ignorada
Fila 5: Metadata  ⏭️ Ignorada
Fila 6: FAMILY_ID,ITEM_ID,... ← Empieza a leer aquí
```

---

## ✅ CHECKLIST DE VALIDACIÓN

Después de hacer los cambios, verifica:

- [ ] Función 1 (`pagina_meli_cedi_oviedo`) tiene `skiprows=5`
- [ ] Función 2 (`pagina_meli_av19_bulevar_oviedo`) tiene `skiprows=5`
- [ ] Función 3 (`pagina_meli_av19_bulevar_cedi_oviedo`) tiene `skiprows=5`
- [ ] No hay ningún otro `skiprows=6` en el código de MELI
- [ ] Total de cambios: 3 (uno por función)

---

## 🚀 RESULTADO ESPERADO

Después de este cambio:
- Las 3 funciones leerán desde la fila 6 del archivo (en lugar de la fila 7)
- Esto se alinea con el nuevo formato de exportación de Mercado Libre
- La validación de schema seguirá funcionando correctamente

---

## 🎯 INSTRUCCIÓN FINAL

Procede a cambiar `skiprows=6` a `skiprows=5` en las 3 funciones de MELI. Es un cambio simple pero crítico para que la lectura del archivo sea correcta.

Gracias.
