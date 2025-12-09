import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
from PIL import Image
import numpy as np

# --- CONFIGURACIÓN GENERAL DE LA PÁGINA ---
st.set_page_config(
    page_title="MarketMaster",
    page_icon="🚀",
    layout="wide"
)

# --- LÓGICA PARA MERCADO LIBRE (VERSIÓN ACTUALIZADA CON NUEVAS COLUMNAS) ---
def pagina_meli_bogota():
    st.markdown("### 🛒 Mercado Libre")
    
    # Nuevas columnas actualizadas según el nuevo formato de Mercado Libre
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

                    # --- INICIO DE LA LÓGICA DE LIMPIEZA DE DATOS ---
                    data_ERP = data_ERP[data_ERP['Codpro'].notna() & ~(data_ERP['Codpro'].isin(['', ' ']) | (data_ERP['Codpro'].str.contains('\x1a', na=False)))]
                    data_ERP = data_ERP[["Codpro", "Nompro", "Valuni", "us05", "us06"]]
                    data_ERP['us05'] = data_ERP['us05'].fillna(0)
                    data_ERP['us06'] = data_ERP['us06'].fillna(0)
                    data_ERP["Inventario_us05"] = data_ERP["us05"]
                    data_ERP["Inventario_us06"] = data_ERP["us06"]
                    data_ERP = data_ERP.drop(["us05", "us06"], axis=1)
                    data_ERP.rename(columns={'Codpro': 'SKU'}, inplace=True)

                    # Conversión inicial a texto
                    data_MELI['SKU'] = data_MELI['SKU'].astype(str)
                    data_ERP['SKU'] = data_ERP['SKU'].astype(str)
                    
                    # Limpieza de ".0"
                    data_MELI['SKU'] = data_MELI['SKU'].str.replace(r'\.0$', '', regex=True)

                    # Se eliminan espacios en blanco al inicio y final de los SKUs en AMBOS archivos
                    data_MELI['SKU'] = data_MELI['SKU'].str.strip()
                    data_ERP['SKU'] = data_ERP['SKU'].str.strip()

                    # Reemplazo de 'nan' a un valor nulo real
                    data_MELI['SKU'] = data_MELI['SKU'].replace('nan', np.nan)
                    data_ERP['SKU'] = data_ERP['SKU'].replace('nan', np.nan)
                    # --- FIN DE LA LÓGICA DE LIMPIEZA DE DATOS ---

                    merged_data = pd.merge(data_MELI, data_ERP, on='SKU', how='left')
                    merged_data['Original_Price'] = merged_data['MARKETPLACE_PRICE']
                    merged_data['original_order'] = merged_data.index
                    
                    grouped = merged_data.groupby('ITEM_ID')
                    processed_groups = []
                    for name, group in grouped:
                        if group.shape[0] == 1:
                            # Columnas que siempre son 0
                            group.loc[:, "STORE_STOCK_QUANTITY_71348291#COP1326882072"] = 0
                            group.loc[:, "STORE_STOCK_QUANTITY_71348293#COP1326882073"] = 0
                            # Actualizar inventario us06
                            group.loc[:, "STORE_STOCK_QUANTITY_71843625#COP1326882074"] = group["Inventario_us06"]
                            # Actualizar inventario us05
                            group.loc[:, "STORE_STOCK_QUANTITY_76644462#COP1326882075"] = group["Inventario_us05"]
                            # Actualizar precios
                            group.loc[:, "MARKETPLACE_PRICE"] = group["Valuni"]
                            group.loc[:, "MSHOPS_PRICE"] = group["Valuni"]
                        
                        elif group.shape[0] > 1:
                            # Columnas que siempre son 0
                            group.loc[:, "STORE_STOCK_QUANTITY_71348291#COP1326882072"] = 0
                            group.loc[:, "STORE_STOCK_QUANTITY_71348293#COP1326882073"] = 0
                            # Actualizar inventario us06 para variaciones con SKU
                            group.loc[group.SKU.notna(), "STORE_STOCK_QUANTITY_71843625#COP1326882074"] = group.loc[group.SKU.notna(), "Inventario_us06"]
                            # Actualizar inventario us05 para variaciones con SKU
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
                    
                    # Asegurar que las columnas de inventario que siempre son 0 se mantengan en 0
                    final_df['STORE_STOCK_QUANTITY_71348291#COP1326882072'] = 0
                    final_df['STORE_STOCK_QUANTITY_71348293#COP1326882073'] = 0
                    # Asegurar que las columnas de inventario activas no tengan NaN
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
                    st.dataframe(final_df.head())
                    st.download_button(label="⬇️ Descargar MELI modificado",
                                      data=output,
                                      file_name="MELI_ACTUALIZADO.xlsx",
                                      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
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

                    for df in [data_price, data_inventory]:
                        df.rename(columns={'SellerSku': 'sku'}, inplace=True)
                    for df in [data_price, data_inventory, data_erp]:
                        df['sku'] = df['sku'].astype(str).str.strip()
                    
                    data_price['ShopSku'] = data_price['ShopSku'].astype(str).str.replace('.0', '', regex=False)
                    data_inventory['ShopSku'] = data_inventory['ShopSku'].astype(str).str.replace('.0', '', regex=False)

                    # Procesar precios
                    st.info("Procesando archivo de precios...")
                    merged_price = pd.merge(data_price, data_erp[['sku', 'Valuni']], on='sku', how='left')
                    merged_price['PriceFalabella'] = merged_price['Valuni']
                    merged_price.drop(columns=['Valuni'], inplace=True)
                    
                    wb_price = load_workbook(uploaded_price)
                    ws_price = wb_price.active
                    for i, row in merged_price.iterrows():
                        for j, value in enumerate(row):
                            ws_price.cell(row=i+2, column=j+1, value=value)
                    
                    buffer_price = BytesIO()
                    wb_price.save(buffer_price)
                    buffer_price.seek(0)
                    
                    # Procesar inventario
                    st.info("Procesando archivo de inventario...")
                    merged_inventory = pd.merge(data_inventory, data_erp[['sku', 'Inventario_Falabella']], on='sku', how='left')
                    merged_inventory['QuantityFalabella'] = merged_inventory['Inventario_Falabella'].fillna(0).astype('int')
                    merged_inventory.drop(columns=['Inventario_Falabella'], inplace=True)
                    merged_inventory.rename(columns={'sku': 'SellerSku'}, inplace=True)
                    
                    csv_data = merged_inventory.to_csv(index=False, sep=';', encoding='utf-8-sig')

                    st.success("✅ ¡Archivos de Falabella procesados!")
                    
                    st.download_button("⬇️ Descargar precios modificados", buffer_price, "Precios_Falabella_Modificado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    st.download_button("⬇️ Descargar inventario modificado", csv_data, "Inventario_Falabella_Modificado.csv", mime="text/csv")
                    
                    st.markdown("#### Vista Previa Inventario")
                    st.dataframe(merged_inventory.head())

                except Exception as e:
                    st.error(f"❌ Error al procesar: {e}")

# --- LÓGICA GENÉRICA PARA RAPPI ---
def procesar_rappi(uploaded_file_rappi, uploaded_file_erp, mapeo_tienda_us, erp_cols_needed, ciudad_nombre):
    """
    Función genérica para procesar archivos de Rappi para cualquier ciudad.
    """
    try:
        # Definir las nuevas columnas del archivo Rappi
        column_names = [
            'vacia_borrar', 'ID', 'ID de tienda', 'Nombre de tienda', 'ID del producto', 'EAN', 'SKU',
            'Nombre del producto', 'Descripción', 'Presentación', 'Precio', 'Descuento', 'Disponibilidad', 'Unidades disponibles'
        ]

        data_RAPPI = pd.read_excel(uploaded_file_rappi, header=None, skiprows=5, names=column_names, sheet_name="Productos")
        data_ERP = pd.read_csv(uploaded_file_erp, delimiter=';', encoding='latin1')

        # Limpieza y preparación del DataFrame del ERP
        data_ERP = data_ERP[data_ERP['Codpro'].notna() & ~(data_ERP['Codpro'].isin(['', ' ']) | (data_ERP['Codpro'].str.contains('\x1a', na=False)))]
        data_ERP = data_ERP[erp_cols_needed]
        data_ERP.rename(columns={'Codpro': 'SKU'}, inplace=True)
        data_ERP['SKU'] = data_ERP['SKU'].astype(str)

        # Limpieza y preparación del DataFrame de Rappi
        data_RAPPI['SKU'] = data_RAPPI['SKU'].astype(str).str.replace('jugandoyeducandoco_', '')
        data_RAPPI['tienda_us'] = data_RAPPI['ID de tienda'].map(mapeo_tienda_us)

        # Función para obtener el inventario de la columna correcta del ERP
        def obtener_inventario(row, df_erp):
            col_inv = row['tienda_us']
            sku = row['SKU']
            if pd.notna(col_inv) and pd.notna(sku):
                inventario = df_erp.loc[df_erp['SKU'] == sku, col_inv]
                # Asegurarse de que el inventario sea un número y manejar NaN
                if not inventario.empty and pd.notna(inventario.iloc[0]):
                    return int(inventario.iloc[0])
            return 0 # Retornar 0 si no hay inventario o SKU

        # Aplicar la lógica de inventario y disponibilidad
        data_RAPPI['Inventario'] = data_RAPPI.apply(obtener_inventario, df_erp=data_ERP, axis=1)
        data_RAPPI['Disponibilidad'] = np.where(data_RAPPI['Inventario'] > 0, 'SI', 'NO')
        data_RAPPI['Unidades disponibles'] = data_RAPPI['Inventario']

        # Cruzar con ERP para obtener el precio correcto
        merged_data = pd.merge(data_RAPPI, data_ERP[['SKU', 'Valuni']], on='SKU', how='left')
        merged_data['Precio'] = merged_data['Valuni']

        # Preparar el DataFrame final con las columnas en el orden correcto
        columnas_finales = [
            'vacia_borrar', 'ID', 'ID de tienda', 'Nombre de tienda', 'ID del producto', 'EAN', 'SKU',
            'Nombre del producto', 'Descripción', 'Presentación', 'Precio', 'Descuento', 'Disponibilidad', 'Unidades disponibles'
        ]
        nuevo_df_rappi = merged_data[columnas_finales].copy()
        nuevo_df_rappi['SKU'] = "jugandoyeducandoco_" + nuevo_df_rappi['SKU'].astype(str)

        # Cargar el archivo original de Rappi para escribir los datos actualizados
        wb = load_workbook(uploaded_file_rappi)
        ws = wb['Productos']
        
        # Escribir los datos fila por fila, incluyendo la nueva columna
        for index, row in nuevo_df_rappi.iterrows():
            # El +1 es porque openpyxl es 1-indexed
            # El +6 es para saltar las 5 filas de encabezado del archivo original
            fila_destino = index + 6 
            for col_idx, value in enumerate(row, start=1):
                ws.cell(row=fila_destino, column=col_idx, value=value)

        # Guardar el archivo modificado en memoria
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Mostrar resultados en la UI
        st.success(f"✅ ¡Archivo de Rappi - {ciudad_nombre} procesado!")
        st.dataframe(nuevo_df_rappi.head())
        st.download_button(
            label=f"⬇️ Descargar Rappi {ciudad_nombre} modificado",
            data=output,
            file_name=f"RAPPI_{ciudad_nombre.replace(' ', '_')}_ACTUALIZADO.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"❌ Error al procesar: {e}")

# --- PÁGINA DE RAPPI POR CIUDAD ---
def pagina_rappi_ciudad(ciudad_nombre, titulo_seccion, tiendas, erp_cols, key_suffix):
    """
    Crea la interfaz de Streamlit para una ciudad específica de Rappi.
    """
    st.markdown(f"### 🛵 Rappi - {titulo_seccion}")

    uploaded_file_rappi = st.file_uploader("📤 Cargar archivo Excel de Rappi", type=['xlsx'], key=f"rappi_{key_suffix}_excel")
    uploaded_file_erp = st.file_uploader("🧾 Cargar archivo CSV de ERP", type=['csv'], key=f"rappi_{key_suffix}_erp")

    if uploaded_file_rappi and uploaded_file_erp:
        if st.button(f'🔄 Procesar Rappi {ciudad_nombre}', key=f"rappi_{key_suffix}_process"):
            with st.spinner('Procesando archivos...'):
                procesar_rappi(uploaded_file_rappi, uploaded_file_erp, tiendas, erp_cols, ciudad_nombre)

# --- LÓGICA PARA WIX ---
def pagina_wix():
    st.markdown("## 🌐 Wix")
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
        if st.button('🔄 Procesar Wix', key="wix_process"):
            with st.spinner('Procesando archivos...'):
                try:
                    data_wix = pd.read_csv(uploaded_file_wix, header=0, dtype={'sku': str})
                    # Renombrar columnas después de cargar
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
                    st.dataframe(merged_data.head())
                    
                    num_rows = merged_data.shape[0]
                    max_rows_per_file = 4000
                    num_files = (num_rows // max_rows_per_file) + (1 if num_rows % max_rows_per_file > 0 else 0)
                    
                    st.info(f"El archivo se dividirá en {num_files} parte(s).")
                                    
                    for i in range(num_files):
                        part = merged_data.iloc[i * max_rows_per_file : (i + 1) * max_rows_per_file]
                        output = part.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label=f"⬇️ Descargar Parte {i+1}",
                            data=output,
                            file_name=f"Wix_modificado_parte_{i+1}.csv",
                            mime="text/csv",
                            key=f"wix_download_{i}"
                        )

                except Exception as e:
                    st.error(f"❌ Error al procesar: {e}")

# --- APLICACIÓN PRINCIPAL (NAVEGACIÓN) ---
def main():
    # Mostrar logo en la barra lateral
    try:
        image = Image.open("logo_transparente.png")
        st.sidebar.image(image, use_container_width=True)
    except FileNotFoundError:
        st.sidebar.warning("Logo no encontrado.")

    st.sidebar.title("Menú de Navegación")
    st.sidebar.markdown("Selecciona la plataforma que deseas actualizar:")

    # Menú de selección en la barra lateral
    opciones = [
        "Mercado Libre",
        "Falabella",
        "Rappi - Bogotá",
        "Rappi - Barranquilla",
        "Rappi - Medellín",
        "Wix"
    ]
    opcion = st.sidebar.selectbox("Plataforma:", opciones)

    # Título principal de la aplicación
    st.title("🚀 MarketMaster")

    # Lógica para mostrar la página correcta según la selección
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
    elif opcion == "Wix":
        pagina_wix()

    st.sidebar.info("Esta app centraliza la actualización de inventarios y precios en múltiples plataformas.")

if __name__ == "__main__":
    main()
