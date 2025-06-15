from typing import Any, Dict, List

import streamlit as st


def data_display(products: List[Dict[str, Any]]) -> None:
    """
    Display product data in a structured format.

    Args:
        products: List of product dictionaries to display
    """
    if not products:
        st.info("Brak produktów do wyświetlenia")
        return

    st.subheader("Lista produktów")

    # Create a table of products
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        st.write("**Nazwa**")
    with col2:
        st.write("**Ilość**")
    with col3:
        st.write("**Cena**")

    for product in products:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(product.get("name", "Nieznana"))
        with col2:
            st.write(f"{product.get('quantity', 0)} {product.get('unit', 'szt.')}")
        with col3:
            st.write(f"{product.get('price', 0.0)} zł")
