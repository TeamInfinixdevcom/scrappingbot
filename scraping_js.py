from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import requests
from PIL import Image
from io import BytesIO
from utils import limpiar_nombre
import os, re, time
from urllib.parse import urljoin

def extraer_background_images(driver):
    """
    Busca elementos con estilos inline que tengan 'background-image' y extrae las URLs.
    """
    elementos = driver.find_elements(By.XPATH, "//*[contains(@style, 'background-image')]")
    bg_urls = []
    for el in elementos:
        style = el.get_attribute("style")
        found = re.findall(r'background-image:\s*url\((.*?)\)', style)
        for url in found:
            url = url.strip('"\'')

            # Convierte relativa a absoluta
            if not url.startswith("http"):
                base = driver.current_url
                url = urljoin(base, url)
            bg_urls.append(url)
    return bg_urls

def extraer_fuentes(driver):
    """
    Busca fuentes usadas en CSS externos.
    """
    links = driver.find_elements(By.XPATH, "//link[@rel='stylesheet']")
    fuentes = set()
    for l in links:
        href = l.get_attribute("href")
        if href and href.startswith("http"):
            try:
                css = requests.get(href, timeout=10).text
                found = re.findall(r"font-family:\s*([^;]+);", css)
                for f in found:
                    fuente = f.strip().split(',')[0].replace('"', '').replace("'", "")
                    if fuente and fuente.lower() != "inherit":
                        fuentes.add(fuente)
            except:
                pass
    return list(fuentes) if fuentes else ["No detectadas"]

def extraer_colores(driver):
    """
    Busca colores HEX y RGB usados en CSS externos.
    """
    links = driver.find_elements(By.XPATH, "//link[@rel='stylesheet']")
    colores = set()
    for l in links:
        href = l.get_attribute("href")
        if href and href.startswith("http"):
            try:
                css = requests.get(href, timeout=10).text
                found = re.findall(r'#[0-9a-fA-F]{6}', css)
                for c in found:
                    colores.add(c)
                found2 = re.findall(r'rgb\([^)]+\)', css)
                for c in found2:
                    colores.add(c)
            except:
                pass
    return list(colores) if colores else ["No detectados"]

def descargar_imagen_real(src, carpeta_destino, alt, imagenes_descargadas, info_imagenes, background=False):
    """
    Descarga la imagen si es real (image/*), la procesa y agrega al listado.
    """
    if src in imagenes_descargadas:
        return
    nombre_archivo = limpiar_nombre(os.path.basename(src))
    try:
        r = requests.get(src, timeout=15)
        # Filtro: solo imágenes reales
        if not r.headers.get("Content-Type", "").startswith("image/"):
            print(f"✘ {src} NO es imagen real, es {r.headers.get('Content-Type')}")
            return
        img_data = r.content
        path = os.path.join(carpeta_destino, nombre_archivo)
        with open(path, "wb") as f:
            f.write(img_data)
        img_pil = Image.open(BytesIO(img_data))
        ancho, alto = img_pil.size
        formato = img_pil.format
        info_imagenes.append({
            "nombre": nombre_archivo,
            "url": src,
            "alt": alt if alt else ("background-image" if background else "(sin alt)"),
            "ancho": ancho,
            "alto": alto,
            "formato": formato,
            "path_local": path
        })
        imagenes_descargadas.add(src)
        label = "(background)" if background else ""
        print(f"✔ {nombre_archivo} - {ancho}x{alto}px [{formato}] {label}")
    except Exception as e:
        print(f"✘ No se pudo descargar {src} ({e})")

def scrapear_imagenes_js(url, carpeta_destino, chromedriver_path):
    """
    - Simula scroll y avanza sliders.
    - Descarga solo imágenes reales (image/*), todos los formatos.
    - Extrae fuentes y colores.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)
    driver.implicitly_wait(10)

    # Scroll para lazy-load
    for i in range(5):
        driver.execute_script(f"window.scrollTo(0, {i*2500});")
        time.sleep(1.2)

    # Avanzar sliders/carouseles
    slider_selectors = [
        ".swiper-button-next", ".slick-next", ".carousel-control-next", ".slider-arrow-next"
    ]
    for sel in slider_selectors:
        try:
            btns = driver.find_elements(By.CSS_SELECTOR, sel)
            for btn in btns:
                for _ in range(25):
                    try:
                        btn.click()
                        time.sleep(0.4)
                    except:
                        break
        except:
            continue

    time.sleep(2)

    info_imagenes = []
    imagenes_descargadas = set()

    # <img>
    imagenes = driver.find_elements(By.TAG_NAME, "img")
    print(f"Encontradas {len(imagenes)} imágenes <img>.")
    for img in imagenes:
        src = img.get_attribute("src")
        alt = img.get_attribute("alt") or ""
        if not src or not src.startswith("http"):
            continue
        descargar_imagen_real(src, carpeta_destino, alt, imagenes_descargadas, info_imagenes)

    # background-image
    bg_urls = extraer_background_images(driver)
    print(f"Encontradas {len(bg_urls)} imágenes background-image.")
    for src in bg_urls:
        if not src.startswith("http"):
            continue
        descargar_imagen_real(src, carpeta_destino, None, imagenes_descargadas, info_imagenes, background=True)

    fuentes = extraer_fuentes(driver)
    colores = extraer_colores(driver)
    driver.quit()
    print(f"Total imágenes reales descargadas (sin duplicados): {len(info_imagenes)}")
    return info_imagenes, fuentes, colores
