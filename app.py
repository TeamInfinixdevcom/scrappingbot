from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = "infinixsecretkey"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('web_url')
        modo = request.form.get('modo', '2')
        if not url or not url.startswith("http"):
            flash("Debe ingresar una URL válida (con http o https).")
            return redirect(url_for('index'))

        # Eliminar el PDF anterior si existe
        try:
            if os.path.exists("reportes/reporte_imagenes.pdf"):
                os.remove("reportes/reporte_imagenes.pdf")
        except Exception as e:
            pass

        # Ejecutar el scraper con los argumentos adecuados
        try:
            cmd = f'python infinitool_scraper.py "{url}" {modo}'
            os.system(cmd)
        except Exception as e:
            flash(f"Ocurrió un error ejecutando el scraper: {e}")
            return redirect(url_for('index'))

        if os.path.exists("reportes/reporte_imagenes.pdf"):
            return redirect(url_for('descargar'))
        else:
            flash("No se generó el informe. Intente con otra URL o modo.")
            return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/descargar')
def descargar():
    pdf_path = "reportes/reporte_imagenes.pdf"
    if not os.path.exists(pdf_path):
        flash("No existe el PDF para descargar.")
        return redirect(url_for('index'))
    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
