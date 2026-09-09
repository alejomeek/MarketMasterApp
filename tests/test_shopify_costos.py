import pandas as pd

from MarketMasterApp import preparar_costos_shopify


def test_preparar_costos_shopify_actualiza_solo_cost_per_item_y_exporta_columnas_minimas():
    shopify = pd.DataFrame(
        {
            "Handle": ["producto-a", "producto-b", "producto-a"],
            "Title": ["A", "B", "A"],
            "Variant SKU": ["'1001", "1002", ""],
            "Variant Price": ["100000.00", "200000.00", ""],
            "Cost per item": ["40000.00", "50000.00", ""],
        }
    )
    erp = pd.DataFrame({"Codpro": ["1001"], "Valuni": [45000]})

    resultado, actualizados, sin_cruzar = preparar_costos_shopify(shopify, erp)

    assert list(resultado.columns) == ["Handle", "Title", "Variant SKU", "Cost per item"]
    assert resultado.loc[0, "Cost per item"] == "45000.00"
    assert resultado.loc[1, "Cost per item"] == "50000.00"
    assert resultado.loc[2, "Cost per item"] == ""
    assert resultado.loc[0, "Handle"] == "producto-a"
    assert actualizados == 1
    assert sin_cruzar == 1


def test_preparar_costos_shopify_conserva_costo_si_valuni_no_es_valido():
    shopify = pd.DataFrame(
        {
            "Handle": ["producto-a"],
            "Title": ["A"],
            "Variant SKU": ["1001"],
            "Cost per item": ["40000.00"],
        }
    )
    erp = pd.DataFrame({"Codpro": ["1001"], "Valuni": ["no disponible"]})

    resultado, actualizados, sin_cruzar = preparar_costos_shopify(shopify, erp)

    assert resultado.loc[0, "Cost per item"] == "40000.00"
    assert actualizados == 0
    assert sin_cruzar == 1
