import pytest
import time

from selenium import webdriver


@pytest.mark.skip(reason="Wymaga ręcznego uruchomienia serwera Streamlit")
def test_streamlit_upload():
    driver = webdriver.Chrome()
    driver.get("http://localhost:8501")
    time.sleep(2)  # Poczekaj na załadowanie strony
    # Tu można dodać interakcje z UI, np. upload pliku, kliknięcia
    driver.quit()
