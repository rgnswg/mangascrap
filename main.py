import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
from PyPDF2 import PdfMerger

BASE_URL = "https://lectormanga.io/capitulo/one-piece-"
OUTPUT_DIR = "one_piece"
PDF_DIR = os.path.join(OUTPUT_DIR, "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def descargar_capitulo(numero):
    pdf_path = os.path.join(PDF_DIR, f"one_piece_{numero:04}.pdf")
    if os.path.exists(pdf_path):
        print(f"> Cap {numero} ya descargado, skip...")
        return pdf_path

    url = f"{BASE_URL}{numero:.2f}"
    print(f"\n>Descargando capítulo {numero} -> {url}")

    driver = get_driver()
    driver.get(url)
    scroll_to_bottom(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    imagenes = [img.get("data-src") for img in soup.select("#gallery p img") if img.get("data-src")]
    if not imagenes:
        print(f">No se encontraron imágenes para el capítulo {numero}")
        return None

    cap_dir = os.path.join(OUTPUT_DIR, f"cap_{numero}")
    os.makedirs(cap_dir, exist_ok=True)

    rutas_locales = []
    for i, img_url in enumerate(imagenes, start=1):
        img_data = requests.get(img_url).content
        img_path = os.path.join(cap_dir, f"{i:03}.jpg")
        with open(img_path, "wb") as f:
            f.write(img_data)
        rutas_locales.append(img_path)
        print(f">Página {i} descargada")

    imgs_rgb = [Image.open(r).convert("RGB") for r in rutas_locales]
    imgs_rgb[0].save(pdf_path, save_all=True, append_images=imgs_rgb[1:])
    print(f"📚 PDF creado: {pdf_path}")

    return pdf_path

def unir_pdfs(archivos_pdf, nombre_salida):
    merger = PdfMerger()
    for pdf in archivos_pdf:
        merger.append(pdf)
    merger.write(nombre_salida)
    merger.close()
    print(f"\n>Mega PDF creado: {nombre_salida}")

if __name__ == "__main__":
    todos_pdfs = []
    for cap in range(1, 1156):
        pdf = descargar_capitulo(cap)
        if pdf:
            todos_pdfs.append(pdf)

    unir_pdfs(todos_pdfs, os.path.join(OUTPUT_DIR, "one_piece_completo.pdf"))
