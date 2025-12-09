import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
from PIL import Image
import numpy as np
import requests
import time

# --- CONFIGURACIÓN GENERAL DE LA PÁGINA ---
st.set_page_config(
    page_title="MarketMaster",
    page_icon="🚀",
    layout="wide"
)

# --- CONFIGURACIÓN DE SEGURIDAD PARA PRUEBAS ---
# ID del sitio de RESPALDO para pruebas automáticas
WIX_BACKUP_SITE_ID = "c9fb6114-70ad-4de2-ba0c-a1bb98e25883"
WIX_API_URL_QUERY = "https://www.wixapis.com/stores/v1/products/query"

# --- FUNCIONES AUXILIARES API WIX (AUTOMATIZACIÓN) ---
@st.cache_data(ttl=300, show_spinner=False)
def fetch_wix_products_backup(api_key):
    """
    Descarga el catálogo del sitio de BACKUP para sincronización.
    Retorna DF con columns: ['id', 'sku', 'current_price', 'current_stock', 'name']
    """
    headers = {
        'Authorization': api_key,
        'wix-site-id': WIX_BACKUP_SITE_ID, # Usamos forzadamente el ID de backup
        'Content-Type': 'application/json'
    }
    
    products = []
    offset = 0
    limit = 100
    
    progress_text = "Descargando catálogo de Wix (Backup)..."
    my_bar = st.progress(0, text=progress_text)

    try:
        while True:
            payload = {
                "includeHiddenProducts": True,
                "query": {
                    "paging": {
                        "limit": limit,
                        "offset": offset
                    }
                }
            }
            
            response = requests.post(WIX_API_URL_QUERY, headers=headers, json=payload, timeout=20)
            
            if response.status_code != 200:
                st.error(f"Error conectando a Wix Backup: {response.status_code}")
                break
            
            data = response.json()
            items = data.get('products', [])
            total_results = data.get('totalResults', 0)
            
            if not items:
                break
                
            for p in items:
                # Extraer datos clave
                pid = p.get('id')
                sku = p.get('sku', '')
                name = p.get('name', 'Sin Nombre')
                price = p.get('price', {}).get('price', 0)
                
                # Stock
                stock_info = p.get('stock', {})
                inventory = stock_info.get('quantity', 0)
                # Si trackInventory es false pero inStock es true, ponemos un flag o 999
                # Para efectos de sync, asumiremos que si es None es 0 o lo ignoramos si no maneja stock
                if inventory is None:
                    inventory = 0 

                products.append({
                    'id': pid,
                    'sku': str(sku).strip(), # Limpiar espacios
                    'name': name,
                    'current_price': float(price),
                    'current_stock': int(inventory)
                })
            
            if total_results > 0:
                current_len = len(products)
                percent = min(current_len / total_results, 1.0)
                my_bar.progress(percent, text=f"Descargando: {current_len} de {total_results}")

            if len(items) < limit:
                break
            
            offset += limit
            
        my_bar.empty()
        return pd.DataFrame(products)

    except Exception as e:
        st.error(f"Error crítico descargando Wix: {e}")
        return None

def update_wix_product_single(api_key, product_id, new_price=None, new_stock=None):
    """
    Actualiza un solo producto en Wix (Precio y/o Stock).
    """
    headers = {
        'Authorization': api_key,
        'wix-site-id': WIX_BACKUP_SITE_ID, # Forzamos backup
        'Content-Type': 'application/json'
    }
    
    url = f"https://www.wixapis.com/stores/v1/products/{product_id}"
    
    # Construir payload dinámico (PATCH)
    product_payload = {}
    
    if new_price is not None:
        product_payload["priceData"] = {"price": float(new_price)}
        
    if new_stock is not None:
        # Para actualizar stock vía updateProduct, debemos asegurar trackInventory=True
        product_payload["stock"] = {
            "trackInventory": True,
            "quantity": int(new_stock)
        }
        
    if not product_payload:
        return False, "Sin cambios"

    payload = {"product": product_payload}

    try:
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            return True, "OK"
        else:
            return False, f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)


# --- LÓGICA PARA MERCADO LIBRE ---
def pagina_meli_bogota():
    st.markdown("### 🛒 Mercado Libre")
    column_names = [
        'FAMILY_ID', 'ITEM_ID', 'PRODUCT_NUMBER', 'VARIATION_ID', 'SKU', 'TITLE', 'VARIATIONS',
        'STORE_STOCK_QUANTITY_71348291#COP1326882072', 'STORE_STOCK_QUANTITY_71843625#COP1326882074',
        'STORE_STOCK_QUANTITY_76644462#COP1326882075', 'STORE_STOCK_QUANTITY_71348293#COP1326882073',
        'TOTAL_STOCK_ALL_STORES', 'CHANNEL', 'MARKETPLACE_PRICE', 'MSHOPS_PRICE', 'MSHOPS_PRICE_SYNC',
        'CURRENCY_ID', 'LISTING_TYPE', 'FEE_PER_SALE_MARKETPLACE', 'FEE_PER_SALE_MSHOPS'
    ]
    uploaded_file_meli = st.file_uploader("📤 Cargar archivo Excel de Mercado Libre", type=['xlsx'], key="meli_bog_excel")
    uploaded_file_erp = st.file_uploader("🧾 Cargar archivo CSV de ERP", type=['csv'], key="meli_bog_erp")

    if uploaded_file_meli and uploaded_file_erp:
        if st.button('🔄 Procesar MELI', key="meli_bog_process"):
            with st.spinner('Procesando archivos...'):
                try:
                    data_MELI = pd.read_excel(uploaded_file_meli, header=None, skiprows=6, names=column_names, sheet_name="Publicaciones")
                    data_ERP = pd.read_csv(uploaded_file_erp, delimiter=';', encoding='latin1')
                    data_ERP = data_ERP[data_ERP['Codpro'].notna() & ~(data_ERP['Codpro'].isin(['', ' ']) | (data_ERP['Codpro'].str.contains('\x1a', na=False)))]
                    data_ERP = data_ERP[["Codpro", "Nompro", "Valuni", "us05", "us06"]]
                    data_ERP['us05'] = data_ERP['us05'].fillna(0)
                    data_ERP['us06'] = data_ERP['us06'].fillna(0)
                    data_ERP["Inventario_us05"] = data_ERP["us05"]
                    data_ERP["Inventario_us06"] = data_ERP["us06"]
                    data_ERP = data_ERP.drop(["us05", "us06"], axis=1)
                    data_ERP.rename(columns={'Codpro': 'SKU'}, inplace=True)
                    data_MELI['SKU'] = data_MELI['SKU'].astype(str)
                    data_ERP['SKU'] = data_ERP['SKU'].astype(str)
                    data_MELI['SKU'] = data_MELI['SKU'].str.replace(r'\.0$', '', regex=True)
                    data_MELI['SKU'] = data_MELI['SKU'].str.strip()
                    data_ERP['SKU'] = data_ERP['SKU'].str.strip()
                    data_MELI['SKU'] = data_MELI['SKU'].replace('nan', np.nan)
                    data_ERP['SKU'] = data_ERP['SKU'].replace('nan', np.nan)
                    merged_data = pd.merge(data_MELI, data_ERP, on='SKU', how='left')
                    merged_data['Original_Price'] = merged_data['MARKETPLACE_PRICE']
                    merged_data['original_order'] = merged_data.index
                    grouped = merged_data.groupby('ITEM_ID')
                    processed_groups = []
                    for name, group in grouped:
                        if group.shape[0] == 1:
                            group.loc[:, "STORE_STOCK_QUANTITY_71348291#COP1326882072"] = 0
                            group.loc[:, "STORE_STOCK_QUANTITY_71348293#COP1326882073"] = 0
                            group.loc[:, "STORE_STOCK_QUANTITY_71843625#COP1326882074"] = group["Inventario_us06"]
                            group.loc[:, "STORE_STOCK_QUANTITY_76644462#COP1326882075"] = group["Inventario_us05"]
                            group.loc[:, "MARKETPLACE_PRICE"] = group["Valuni"]
                            group.loc[:, "MSHOPS_PRICE"] = group["Valuni"]
                        elif group.shape[0] > 1:
                            group.loc[:, "STORE_STOCK_QUANTITY_71348291#COP1326882072"] = 0
                            group.loc[:, "STORE_STOCK_QUANTITY_71348293#COP1326882073"] = 0
                            group.loc[group.SKU.notna(), "STORE_STOCK_QUANTITY_71843625#COP1326882074"] = group.loc[group.SKU.notna(), "Inventario_us06"]
                            group.loc[group.SKU.notna(), "STORE_STOCK_QUANTITY_76644462#COP1326882075"] = group.loc[group.SKU.notna(), "Inventario_us05"]
                            variations_with_price = group.loc[group.SKU.notna() & group.Valuni.notna()]
                            if not variations_with_price.empty:
                                price_to_set = variations_with_price['Valuni'].iloc[0]
                                group.loc[group.SKU.isna(), "MARKETPLACE_PRICE"] = price_to_set
                                group.loc[group.SKU.isna(), "MSHOPS_PRICE"] = price_to_set
                        processed_groups.append(group)
                    final_df = pd.concat(processed_groups)
                    final_df['MARKETPLACE_PRICE'] = final_df['MARKETPLACE_PRICE'].fillna(final_df['Original_Price'])
                    final_df = final_df.sort_values('original_order')
                    final_df['STORE_STOCK_QUANTITY_71348291#COP1326882072'] = 0
                    final_df['STORE_STOCK_QUANTITY_71348293#COP1326882073'] = 0
                    final_df['STORE_STOCK_QUANTITY_71843625#COP1326882074'] = final_df['STORE_STOCK_QUANTITY_71843625#COP1326882074'].fillna(0)
                    final_df['STORE_STOCK_QUANTITY_76644462#COP1326882075'] = final_df['STORE_STOCK_QUANTITY_76644462#COP1326882075'].fillna(0)
                    final_df['VARIATION_ID'] = final_df['VARIATION_ID'].apply(lambda x: str(int(x)) if pd.notna(x) else None)
                    final_df = final_df.drop(['Nompro', 'Valuni', 'Inventario_us05', 'Inventario_us06', 'original_order', 'Original_Price'], axis=1)
                    wb = load_workbook(uploaded_file_meli)
                    ws = wb['Publicaciones']
                    for r_idx, row_data in final_df.iterrows():
                        for c_idx, value in enumerate(row_data, start=1):
                            ws.cell(row=r_idx + 7, column=c_idx, value=value)
                    output = BytesIO()
                    wb.save(output)
                    output.seek(0)
                    st.success("✅ ¡Archivo de MELI procesado!")
                    st.download_button(label="⬇️ Descargar MELI modificado", data=output, file_name="MELI_ACTUALIZADO.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                except Exception as e:
                    st.error(f"❌ Error al procesar: {e}")

# --- LÓGICA PARA FALABELLA ---
def pagina_falabella():
    st.markdown("### 🧩 Falabella")
    column_names_price = ['SellerSku', 'ShopSku', 'PriceFalabella', 'SalePriceFalabella', 'SaleStartDateFalabella', 'SaleEndDateFalabella', 'Name']
    column_names_inventory = ['SellerSku', 'ShopSku', 'QuantityFalabella', 'Name']
    uploaded_price = st.file_uploader("📦 Cargar archivo de precios (Excel)", type=['xlsx'], key="fala_price")
    uploaded_inventory = st.file_uploader("📊 Cargar archivo de inventario (CSV)", type=['csv'], key="fala_inv")
    uploaded_erp = st.file_uploader("🧾 Cargar archivo ERP (CSV)", type=['csv'], key="fala_erp")

    if uploaded_price and uploaded_inventory and uploaded_erp:
        if st.button("🔄 Procesar Falabella", key="fala_process"):
            with st.spinner('Procesando archivos...'):
                try:
                    data_price = pd.read_excel(uploaded_price, header=None, skiprows=1, names=column_names_price)
                    data_inventory = pd.read_csv(uploaded_inventory, header=None, skiprows=1, names=column_names_inventory, sep=';', encoding='utf-8')
                    data_erp = pd.read_csv(uploaded_erp, delimiter=';', encoding='latin1')
                    data_erp = data_erp[data_erp['Codpro'].notna() & ~(data_erp['Codpro'].isin(['', ' ']) | data_erp['Codpro'].str.contains('\x1a', na=False))]
                    data_erp = data_erp[['Codpro', 'Nompro', 'Valuni', 'us02']]
                    data_erp['us02'] = data_erp['us02'].fillna(0)
                    data_erp['Inventario_Falabella'] = data_erp['us02']
                    data_erp.drop(['us02'], axis=1, inplace=True)
                    data_erp.rename(columns={'Codpro': 'sku'}, inplace=True)
                    for df in [data_price, data_inventory]: df.rename(columns={'SellerSku': 'sku'}, inplace=True)
                    for df in [data_price, data_inventory, data_erp]: df['sku'] = df['sku'].astype(str).str.strip()
                    data_price['ShopSku'] = data_price['ShopSku'].astype(str).str.replace('.0', '', regex=False)
                    data_inventory['ShopSku'] = data_inventory['ShopSku'].astype(str).str.replace('.0', '', regex=False)
                    merged_price = pd.merge(data_price, data_erp[['sku', 'Valuni']], on='sku', how='left')
                    merged_price['PriceFalabella'] = merged_price['Valuni']
                    merged_price.drop(columns=['Valuni'], inplace=True)
                    wb_price = load_workbook(uploaded_price)
                    ws_price = wb_price.active
                    for i, row in merged_price.iterrows():
                        for j, value in enumerate(row): ws_price.cell(row=i+2, column=j+1, value=value)
                    buffer_price = BytesIO()
                    wb_price.save(buffer_price)
                    buffer_price.seek(0)
                    merged_inventory = pd.merge(data_inventory, data_erp[['sku', 'Inventario_Falabella']], on='sku', how='left')
                    merged_inventory['QuantityFalabella'] = merged_inventory['Inventario_Falabella'].fillna(0).astype('int')
                    merged_inventory.drop(columns=['Inventario_Falabella'], inplace=True)
                    merged_inventory.rename(columns={'sku': 'SellerSku'}, inplace=True)
                    csv_data = merged_inventory.to_csv(index=False, sep=';', encoding='utf-8-sig')
                    st.success("✅ ¡Archivos de Falabella procesados!")
                    st.download_button("⬇️ Descargar precios modificados", buffer_price, "Precios_Falabella_Modificado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    st.download_button("⬇️ Descargar inventario modificado", csv_data, "Inventario_Falabella_Modificado.csv", mime="text/csv")
                except Exception as e:
                    st.error(f"❌ Error al procesar: {e}")

# --- LÓGICA RAPPI GENÉRICA ---
def procesar_rappi(uploaded_file_rappi, uploaded_file_erp, mapeo_tienda_us, erp_cols_needed, ciudad_nombre):
    try:
        column_names = ['vacia_borrar', 'ID', 'ID de tienda', 'Nombre de tienda', 'ID del producto', 'EAN', 'SKU', 'Nombre del producto', 'Descripción', 'Presentación', 'Precio', 'Descuento', 'Disponibilidad', 'Unidades disponibles']
        data_RAPPI = pd.read_excel(uploaded_file_rappi, header=None, skiprows=5, names=column_names, sheet_name="Productos")
        data_ERP = pd.read_csv(uploaded_file_erp, delimiter=';', encoding='latin1')
        data_ERP = data_ERP[data_ERP['Codpro'].notna() & ~(data_ERP['Codpro'].isin(['', ' ']) | (data_ERP['Codpro'].str.contains('\x1a', na=False)))]
        data_ERP = data_ERP[erp_cols_needed]
        data_ERP.rename(columns={'Codpro': 'SKU'}, inplace=True)
        data_ERP['SKU'] = data_ERP['SKU'].astype(str)
        data_RAPPI['SKU'] = data_RAPPI['SKU'].astype(str).str.replace('jugandoyeducandoco_', '')
        data_RAPPI['tienda_us'] = data_RAPPI['ID de tienda'].map(mapeo_tienda_us)
        def obtener_inventario(row, df_erp):
            col_inv = row['tienda_us']
            sku = row['SKU']
            if pd.notna(col_inv) and pd.notna(sku):
                inventario = df_erp.loc[df_erp['SKU'] == sku, col_inv]
                if not inventario.empty and pd.notna(inventario.iloc[0]): return int(inventario.iloc[0])
            return 0
        data_RAPPI['Inventario'] = data_RAPPI.apply(obtener_inventario, df_erp=data_ERP, axis=1)
        data_RAPPI['Disponibilidad'] = np.where(data_RAPPI['Inventario'] > 0, 'SI', 'NO')
        data_RAPPI['Unidades disponibles'] = data_RAPPI['Inventario']
        merged_data = pd.merge(data_RAPPI, data_ERP[['SKU', 'Valuni']], on='SKU', how='left')
        merged_data['Precio'] = merged_data['Valuni']
        columnas_finales = ['vacia_borrar', 'ID', 'ID de tienda', 'Nombre de tienda', 'ID del producto', 'EAN', 'SKU', 'Nombre del producto', 'Descripción', 'Presentación', 'Precio', 'Descuento', 'Disponibilidad', 'Unidades disponibles']
        nuevo_df_rappi = merged_data[columnas_finales].copy()
        nuevo_df_rappi['SKU'] = "jugandoyeducandoco_" + nuevo_df_rappi['SKU'].astype(str)
        wb = load_workbook(uploaded_file_rappi)
        ws = wb['Productos']
        for index, row in nuevo_df_rappi.iterrows():
            fila_destino = index + 6 
            for col_idx, value in enumerate(row, start=1): ws.cell(row=fila_destino, column=col_idx, value=value)
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        st.success(f"✅ ¡Archivo de Rappi - {ciudad_nombre} procesado!")
        st.download_button(label=f"⬇️ Descargar Rappi {ciudad_nombre} modificado", data=output, file_name=f"RAPPI_{ciudad_nombre.replace(' ', '_')}_ACTUALIZADO.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.error(f"❌ Error al procesar: {e}")

def pagina_rappi_ciudad(ciudad_nombre, titulo_seccion, tiendas, erp_cols, key_suffix):
    st.markdown(f"### 🛵 Rappi - {titulo_seccion}")
    uploaded_file_rappi = st.file_uploader("📤 Cargar archivo Excel de Rappi", type=['xlsx'], key=f"rappi_{key_suffix}_excel")
    uploaded_file_erp = st.file_uploader("🧾 Cargar archivo CSV de ERP", type=['csv'], key=f"rappi_{key_suffix}_erp")
    if uploaded_file_rappi and uploaded_file_erp:
        if st.button(f'🔄 Procesar Rappi {ciudad_nombre}', key=f"rappi_{key_suffix}_process"):
            with st.spinner('Procesando archivos...'):
                procesar_rappi(uploaded_file_rappi, uploaded_file_erp, tiendas, erp_cols, ciudad_nombre)

# --- LÓGICA PARA WIX MANUAL (CSV) ---
def pagina_wix_manual():
    st.markdown("## 🌐 Wix (Manual - CSV)")
    column_names = [
        'handleId', 'fieldType', 'name', 'description', 'productImageUrl', 'collection', 'sku', 'ribbon', 
        'price', 'surcharge', 'visible', 'discountMode', 'discountValue', 'inventory', 'weight', 'cost',
        'productOptionName1', 'productOptionType1', 'productOptionDescription1', 'productOptionName2', 'productOptionType2', 'productOptionDescription2',
        'productOptionName3', 'productOptionType3', 'productOptionDescription3', 'productOptionName4', 'productOptionType4', 'productOptionDescription4',
        'productOptionName5', 'productOptionType5', 'productOptionDescription5', 'productOptionName6', 'productOptionType6', 'productOptionDescription6',
        'additionalInfoTitle1', 'additionalInfoDescription1', 'additionalInfoTitle2', 'additionalInfoDescription2',
        'additionalInfoTitle3', 'additionalInfoDescription3', 'additionalInfoTitle4', 'additionalInfoDescription4',
        'additionalInfoTitle5', 'additionalInfoDescription5', 'additionalInfoTitle6', 'additionalInfoDescription6',
        'customTextField1', 'customTextCharLimit1', 'customTextMandatory1', 'customTextField2', 'customTextCharLimit2', 'customTextMandatory2', 'brand'
    ]
    uploaded_file_wix = st.file_uploader("📤 Cargar archivo CSV de Wix", type=['csv'], key="wix_csv")
    uploaded_file_erp = st.file_uploader("🧾 Cargar archivo CSV de ERP", type=['csv'], key="wix_erp")

    if uploaded_file_wix and uploaded_file_erp:
        if st.button('🔄 Procesar Wix (CSV)', key="wix_process"):
            with st.spinner('Procesando archivos...'):
                try:
                    data_wix = pd.read_csv(uploaded_file_wix, header=0, dtype={'sku': str})
                    data_wix.columns = column_names
                    data_ERP = pd.read_csv(uploaded_file_erp, delimiter=';', encoding='latin1')
                    data_ERP = data_ERP[data_ERP['Codpro'].notna() & ~(data_ERP['Codpro'].isin(['', ' ']) | (data_ERP['Codpro'].str.contains('\x1a', na=False)))]
                    data_ERP = data_ERP[["Codpro", "Nompro", "Valuni", "us06"]]
                    data_ERP['us06'] = data_ERP['us06'].fillna(0)
                    data_ERP["Inventario_Wix"] = data_ERP["us06"]
                    data_ERP.drop(["us06"], axis=1, inplace=True)
                    data_ERP.rename(columns={'Codpro': 'sku'}, inplace=True)
                    data_ERP['sku'] = data_ERP['sku'].astype(str)
                    merged_data = pd.merge(data_wix, data_ERP, on='sku', how='left')
                    merged_data['Valuni'].fillna(0, inplace=True)
                    merged_data['Inventario_Wix'].fillna(0, inplace=True)
                    merged_data['inventory'] = merged_data['Inventario_Wix']
                    merged_data['price'] = merged_data['Valuni']
                    merged_data = merged_data.drop(["Nompro", "Valuni", "Inventario_Wix"], axis=1)
                    merged_data['visible'] = np.where(merged_data['inventory'] > 0, "TRUE", "FALSE")
                    st.success("✅ ¡Archivo de Wix procesado!")
                    num_rows = merged_data.shape[0]
                    max_rows_per_file = 4000
                    num_files = (num_rows // max_rows_per_file) + (1 if num_rows % max_rows_per_file > 0 else 0)
                    st.info(f"El archivo se dividirá en {num_files} parte(s).")
                    for i in range(num_files):
                        part = merged_data.iloc[i * max_rows_per_file : (i + 1) * max_rows_per_file]
                        output = part.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(label=f"⬇️ Descargar Parte {i+1}", data=output, file_name=f"Wix_modificado_parte_{i+1}.csv", mime="text/csv", key=f"wix_download_{i}")
                except Exception as e:
                    st.error(f"❌ Error al procesar: {e}")

# --- LÓGICA PARA WIX AUTOMATIZADO (NUEVA PÁGINA) ---
def pagina_wix_automatizada():
    st.markdown("## 🌐 Wix Automático 🤖 (Sitio de Backup)")
    st.warning(f"⚠️ **MODO PRUEBA ACTIVADO**: Los cambios se aplicarán exclusivamente al sitio con ID: `{WIX_BACKUP_SITE_ID}`")

    # Verificación de credenciales
    if 'wix_api' not in st.secrets:
        st.error("❌ Faltan credenciales en secrets.toml [wix_api]")
        return
    
    api_key = st.secrets["wix_api"]["api_key"]
    
    uploaded_file_erp = st.file_uploader("🧾 Cargar archivo CSV de ERP", type=['csv'], key="wix_erp_auto")

    if uploaded_file_erp:
        # Estado de la sesión para manejar el flujo de análisis -> confirmación -> sync
        if 'wix_sync_state' not in st.session_state:
            st.session_state.wix_sync_state = 'upload' # upload, analyzed, synced

        if st.button('🔍 1. Analizar Diferencias', key="analyze_wix"):
            with st.spinner('Conectando a Wix y descargando catálogo...'):
                # 1. Descargar catálogo actual (Live)
                df_wix_live = fetch_wix_products_backup(api_key)
            
            if df_wix_live is not None and not df_wix_live.empty:
                with st.spinner('Cruzando datos con el ERP...'):
                    # 2. Procesar ERP
                    try:
                        data_ERP = pd.read_csv(uploaded_file_erp, delimiter=';', encoding='latin1')
                        # Limpieza básica igual a la manual
                        data_ERP = data_ERP[data_ERP['Codpro'].notna() & ~(data_ERP['Codpro'].isin(['', ' ']) | (data_ERP['Codpro'].str.contains('\x1a', na=False)))]
                        data_ERP = data_ERP[["Codpro", "Nompro", "Valuni", "us06"]] # Usamos us06 para Wix
                        data_ERP['us06'] = data_ERP['us06'].fillna(0).astype(int)
                        data_ERP['Valuni'] = data_ERP['Valuni'].fillna(0).astype(float)
                        data_ERP.rename(columns={'Codpro': 'sku'}, inplace=True)
                        data_ERP['sku'] = data_ERP['sku'].astype(str).str.strip()
                        
                        # 3. Merge
                        merged = pd.merge(df_wix_live, data_ERP, on='sku', how='inner')
                        
                        # 4. Detectar cambios
                        # Tolerancia pequeña para floats en precio
                        merged['diff_price'] = np.abs(merged['current_price'] - merged['Valuni']) > 0.01
                        merged['diff_stock'] = merged['current_stock'] != merged['us06']
                        
                        to_update = merged[merged['diff_price'] | merged['diff_stock']].copy()
                        
                        # Guardar en sesión para el siguiente paso
                        st.session_state.wix_to_update = to_update
                        st.session_state.wix_sync_state = 'analyzed'
                        
                        st.success(f"Análisis completado. Total productos en Wix: {len(df_wix_live)}. Productos encontrados en ERP: {len(merged)}.")
                        
                    except Exception as e:
                        st.error(f"Error procesando ERP: {e}")

        # Mostrar resultados del análisis
        if st.session_state.get('wix_sync_state') == 'analyzed':
            df_update = st.session_state.wix_to_update
            
            if df_update.empty:
                st.info("✅ ¡Todo está sincronizado! No hay diferencias de precio ni stock entre Wix y el ERP.")
            else:
                st.warning(f"⚠️ Se encontraron **{len(df_update)}** productos con diferencias.")
                
                # Mostrar tabla de diferencias
                st.dataframe(
                    df_update[['sku', 'name', 'current_price', 'Valuni', 'current_stock', 'us06']]
                    .rename(columns={
                        'current_price': 'Precio Wix', 'Valuni': 'Precio ERP',
                        'current_stock': 'Stock Wix', 'us06': 'Stock ERP'
                    })
                )
                
                st.write("---")
                st.write("¿Estás seguro de aplicar estos cambios en el sitio de BACKUP?")
                
                if st.button("🚀 2. Ejecutar Sincronización"):
                    progress_bar = st.progress(0, text="Iniciando actualización...")
                    status_text = st.empty()
                    total_items = len(df_update)
                    success_count = 0
                    errors = []
                    
                    for idx, row in df_update.iterrows():
                        # Determinar qué enviar
                        new_p = row['Valuni'] if row['diff_price'] else None
                        new_s = row['us06'] if row['diff_stock'] else None
                        
                        status_text.text(f"Actualizando: {row['sku']} - {row['name'][:30]}...")
                        
                        ok, msg = update_wix_product_single(api_key, row['id'], new_price=new_p, new_stock=new_s)
                        
                        if ok:
                            success_count += 1
                        else:
                            errors.append(f"{row['sku']}: {msg}")
                        
                        # Actualizar barra
                        progress_bar.progress((idx + 1) / total_items)
                        time.sleep(0.1) # Pequeña pausa para no saturar
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    if errors:
                        st.error(f"Se actualizaron {success_count} productos, pero hubo {len(errors)} errores.")
                        with st.expander("Ver errores"):
                            for e in errors:
                                st.write(e)
                    else:
                        st.balloons()
                        st.success(f"✅ ¡Éxito! Se actualizaron {success_count} productos correctamente en el sitio de Backup.")
                    
                    # Resetear estado
                    st.session_state.wix_sync_state = 'upload'


# --- APLICACIÓN PRINCIPAL (NAVEGACIÓN) ---
def main():
    try:
        image = Image.open("logo_transparente.png")
        st.sidebar.image(image, use_container_width=True)
    except FileNotFoundError:
        st.sidebar.warning("Logo no encontrado.")

    st.sidebar.title("Menú de Navegación")
    st.sidebar.markdown("Selecciona la plataforma:")

    opciones = [
        "Mercado Libre",
        "Falabella",
        "Rappi - Bogotá",
        "Rappi - Barranquilla",
        "Rappi - Medellín",
        "Wix (Manual - CSV)",
        "Wix Automático (Backup)" # Nueva opción
    ]
    opcion = st.sidebar.selectbox("Plataforma:", opciones)

    st.title("🚀 MarketMaster")

    if opcion == "Mercado Libre":
        pagina_meli_bogota()
    elif opcion == "Falabella":
        pagina_falabella()
    elif opcion == "Rappi - Bogotá":
        pagina_rappi_ciudad(
            ciudad_nombre="Bogotá",
            titulo_seccion="Bogotá (Av.19 y Blv)",
            tiendas={900243006: 'us01', 900243075: 'us02'},
            erp_cols=["Codpro", "Nompro", "Valuni", "us01", "us02"],
            key_suffix="bog"
        )
    elif opcion == "Rappi - Barranquilla":
        pagina_rappi_ciudad(
            ciudad_nombre="Barranquilla",
            titulo_seccion="Barranquilla (Bvista y Cll 74)",
            tiendas={900243002: 'us04', 900246112: 'us03'},
            erp_cols=["Codpro", "Nompro", "Valuni", "us03", "us04"],
            key_suffix="bqa"
        )
    elif opcion == "Rappi - Medellín":
        pagina_rappi_ciudad(
            ciudad_nombre="Medellín",
            titulo_seccion="Medellín (Oviedo)",
            tiendas={900418701: 'us05'},
            erp_cols=["Codpro", "Nompro", "Valuni", "us05"],
            key_suffix="med"
        )
    elif opcion == "Wix (Manual - CSV)":
        pagina_wix_manual()
    elif opcion == "Wix Automático (Backup)":
        pagina_wix_automatizada()

    st.sidebar.info("Esta app centraliza la actualización de inventarios y precios en múltiples plataformas.")

if __name__ == "__main__":
    main()
