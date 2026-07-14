import os
import io
import base64
import pickle
import numpy as np
import matplotlib
# Evita que Matplotlib intente abrir ventanas gráficas en el servidor de Render
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from flask import Flask, render_template, request

app = Flask(__name__)

# ----------------------------
#   Cargar modelos estimados
# ----------------------------
# Buscamos el archivo pkl. Si está en la raíz o en src, lo cargamos de forma segura.
ruta_pkl = "parametros_wood.pkl"
if not os.path.exists(ruta_pkl) and os.path.exists("src/parametros_wood.pkl"):
    ruta_pkl = "src/parametros_wood.pkl"

try:
    with open(ruta_pkl, "rb") as f:
        parametros = pickle.load(f)
except FileNotFoundError:
    # Parámetros de respaldo por si aún no subes tu archivo .pkl
    parametros = {
        "Holstein": {"a": 15.0, "b": 0.2, "c": 0.04},
        "Jersey": {"a": 12.0, "b": 0.15, "c": 0.03}
    }

# Modelo Wood
def wood(t, a, b, c):
    return a * (t**b) * np.exp(-c * t)

# Calcular pico
def calcular_pico(a, b, c):
    t_pico = b / c
    y_pico = wood(t_pico, a, b, c)
    return t_pico, y_pico

@app.route('/', methods=['GET', 'POST'])
def index():
    # Valores por defecto al cargar la página por primera vez
    raza_seleccionada = list(parametros.keys())[0]
    semanas = 1
    pred = None
    t_pico, y_pico = None, None
    grafica_base64 = None

    if request.method == 'POST':
        # Obtener datos enviados desde el formulario HTML
        raza_seleccionada = request.form.get('raza')
        semanas = int(request.form.get('semanas', 1))

    # Realizar cálculos con los parámetros de la raza seleccionada
    a = parametros[raza_seleccionada]["a"]
    b = parametros[raza_seleccionada]["b"]
    c = parametros[raza_seleccionada]["c"]

    pred = wood(semanas, a, b, c)
    t_pico, y_pico = calcular_pico(a, b, c)

    # -------------------
    #   GENERAR GRÁFICA EN MEMORIA
    # -------------------
    t_plot = np.linspace(1, 360, 360)
    y_plot = wood(t_plot, a, b, c)

    plt.figure(figsize=(8, 4))
    plt.plot(t_plot, y_plot, label="Curva Wood", color="blue")
    plt.scatter([t_pico], [y_pico], color="red", zorder=5, label=f"Pico ({t_pico:.1f} sem)")
    plt.axvline(x=semanas, color="green", linestyle="--", label=f"Semana elegida ({semanas})")
    plt.title(f"Curva de lactancia - {raza_seleccionada}")
    plt.xlabel("Semanas posparto")
    plt.ylabel("Litros/día")
    plt.legend()
    plt.tight_layout()

    # Convertimos la gráfica a formato base64 para incrustarla en el HTML sin guardarla en disco
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    grafica_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close() # Cerramos la figura para liberar memoria del servidor

    return render_template(
        'index.html',
        razas=list(parametros.keys()),
        raza_seleccionada=raza_seleccionada,
        semanas=semanas,
        pred=f"{pred:.2f}",
        t_pico=f"{t_pico:.1f}",
        y_pico=f"{y_pico:.2f}",
        grafica=grafica_base64
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
