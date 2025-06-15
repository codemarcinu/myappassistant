from typing import Any, Dict, List

import pandas as pd
import streamlit as st


def data_display(products: List[Dict[str, Any]]) -> None:
    """Wyświetla produkty w formie tabeli lub komunikat, jeśli pusto."""
    if not products:
        st.info("Twoja spiżarnia jest pusta. Dodaj produkty za pomocą czatu.")
    else:
        df = pd.DataFrame(products)
        st.dataframe(df, use_container_width=True)
