import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from fpdf import FPDF
from utils import crear_carpeta, limpiar_nombre
from scraping_js import scrapear_imagenes_js
import unicodedata
import sys


def limpiar_texto_pdf(texto):
    if not texto:
        return ""
    texto = texto.replace("—", "-").replace("–", "-")
    texto = unicodedata.normalize("NFKD", texto)
    return texto.encode("latin-1", "ignore").decode("latin-1")

# ========== SCRAPING NORMAL (HTML) ==========
def obtener_imagenes_html(url):
    print(f"Descargando HTML de: {url}")
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        return soup.find_all("img")
    except Exception as e:
        print(f"Error al descargar HTML: {e}")
        return []

def descargar_imagen(src, carpeta_destino):
    try:
        resp_img = requests.get(src, timeout=12)
        img_data = resp_img.content
        nombre_archivo = limpiar_nombre(os.path.basename(src))
        path = os.path.join(carpeta_destino, nombre_archivo)
        with open(path, "wb") as f:
            f.write(img_data)
        img_pil = Image.open(BytesIO(img_data))
        return path, img_pil
    except Exception as e:
        print(f"✘ No se pudo descargar {src} ({e})")
        return None, None

def analizar_imagenes(url, carpeta_destino):
    imagenes_html = obtener_imagenes_html(url)
    imagenes_info = []
    print(f"Procesando {len(imagenes_html)} imágenes encontradas...")
    for img in imagenes_html:
        src = img.get("src")
        if not src:
            continue
        if not src.startswith("http"):
            src = requests.compat.urljoin(url, src)
        alt = img.get("alt", "")
        path, img_pil = descargar_imagen(src, carpeta_destino)
        if path and img_pil:
            ancho, alto = img_pil.size
            formato = img_pil.format
            imagenes_info.append({
                "nombre": os.path.basename(path),
                "url": src,
                "alt": alt,
                "ancho": ancho,
                "alto": alto,
                "formato": formato,
                "path_local": path
            })
            print(f"✔ {os.path.basename(path)} - {ancho}x{alto}px [{formato}]")
    print(f"Total imágenes procesadas: {len(imagenes_info)}")
    return imagenes_info

# ========== PDF ==========
# ...arriba igual...

def generar_pdf_informe(imagenes, fuentes, colores, pdf_path):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, "Informe de imágenes, fuentes y colores (Infinitool Scraper)", ln=True, align='C')

    # ======= Fuentes =======
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Fuentes principales detectadas en la web:", ln=True)
    pdf.set_font("Arial", '', 11)
    for fuente in fuentes:
        pdf.cell(0, 8, f"- {fuente}", ln=True)
    pdf.ln(6)

    # ======= Colores =======
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Colores principales detectados en la web:", ln=True)
    pdf.set_font("Arial", '', 11)
    for color in colores[:20]:  # Muestra máximo 20 colores
        pdf.cell(0, 8, f"- {color}", ln=True)
    pdf.ln(10)

    # ======= Imágenes =======
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 8, "Resumen de imágenes encontradas y descargadas:", ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(40, 8, "Miniatura", 1)
    pdf.cell(75, 8, "Archivo/URL", 1)
    pdf.cell(30, 8, "Tamaño", 1)
    pdf.cell(20, 8, "Formato", 1)
    pdf.cell(80, 8, "Texto alternativo", 1)
    pdf.ln()

    for img in imagenes:
        pdf.set_font("Arial", '', 9)
        y = pdf.get_y()
        x = pdf.get_x()
        try:
            pdf.image(img["path_local"], x + 2, y + 2, 22, 15)
        except:
            pass
        pdf.cell(40, 19, '', 1, 0, 'C')
        pdf.set_xy(x+40, y)
        nombre_corto = limpiar_texto_pdf(img['nombre'][:35])
        pdf.multi_cell(75, 6.5, f"{nombre_corto}\n{limpiar_texto_pdf(img['url'][:60])}...", border=1)
        pdf.set_xy(x+115, y)
        pdf.cell(30, 19, f"{img['ancho']}x{img['alto']}", 1, 0, 'C')
        pdf.set_xy(x+145, y)
        pdf.cell(20, 19, img['formato'], 1, 0, 'C')
        pdf.set_xy(x+165, y)
        alt_corto = limpiar_texto_pdf(img['alt'][:90] if img['alt'] else "-")
        pdf.multi_cell(80, 6.5, alt_corto, border=1)
        pdf.set_y(y+19)

    pdf.output(pdf_path)
    print(f"\n✔ Informe PDF generado: {pdf_path}")

# ========== PROGRAMA PRINCIPAL ==========
def main():
    print("==== INFNITOOL SCRAPER (by Infinix) ====")
    # Si hay argumentos, use esos. Si no, caiga en input tradicional.
    if len(sys.argv) >= 3:
        url = sys.argv[1]
        opcion = sys.argv[2]
    else:
        url = input("Pegue la URL que desea analizar:\n> ").strip()
        opcion = input("Digite 1 o 2: ").strip()

    if not url.startswith("http"):
        print("URL inválida. Debe comenzar con http o https.")
        return

    crear_carpeta('imagenes_descargadas')
    crear_carpeta('reportes')

    if opcion == "2":
        chromedriver_path = "chromedriver-win64/chromedriver.exe"
        imagenes, fuentes, colores = scrapear_imagenes_js(url, "imagenes_descargadas", chromedriver_path)
    else:
        print("Use la opción 2 para scraping profesional de MOMNT.")
        return

    if not imagenes:
        print("No se encontraron imágenes.")
        return

    pdf_path = os.path.join("reportes", "reporte_imagenes.pdf")
    generar_pdf_informe(imagenes, fuentes, colores, pdf_path)
    print("\n✔ Informe PDF generado: %s" % pdf_path)
    print("\n¡Proceso terminado! El PDF está en la carpeta 'reportes'.\n")

if __name__ == "__main__":
    main()
