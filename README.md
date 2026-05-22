# Digestión / Presión / Gases Tracker

Aplicación pequeña en Streamlit para registrar comidas, bebidas, síntomas digestivos, burbujeo, presión abdominal, gases, eructos, ansiedad y ubicación del malestar.

Esta app no diagnostica enfermedades, no da consejo médico y no reemplaza evaluación médica. Solo ayuda a guardar datos locales para revisarlos o llevarlos a una consulta.

## Funciones

- Formulario mobile-friendly para nuevos registros.
- Persistencia local en `data/digest_log.csv`.
- Vista de registros de hoy con resumen.
- Filtros de síntomas altos y comidas seguras.
- Comparación simple de registros con gas externo vs sin gas externo.
- Dashboard con gráficos de línea y barras.
- Exportación e importación de CSV.
- Vista "Para el doctor" con resumen descriptivo de los últimos 7 días.

## Requisitos

- Python 3.10 o superior.
- Dependencias listadas en `requirements.txt`.

## Correr localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Streamlit abrirá una URL local, normalmente `http://localhost:8501`.

Si `data/digest_log.csv` no existe, la app lo crea automáticamente con los encabezados necesarios.

## Subir a GitHub

```bash
git init
git add app.py requirements.txt README.md .gitignore data/.gitkeep
git commit -m "Initial digest tracker app"
git branch -M main
git remote add origin git@github.com:LatinoSolutions/traga_traga.git
git push -u origin main
```

Si el repositorio ya existe localmente, usa solo los comandos `git add`, `git commit`, `git remote add origin` y `git push` que correspondan.

## Desplegar en Streamlit Community Cloud

1. Sube este proyecto a GitHub.
2. Entra a [Streamlit Community Cloud](https://streamlit.io/cloud).
3. Elige "New app".
4. Selecciona el repositorio `LatinoSolutions/traga_traga`, rama `main` y archivo principal `app.py`.
5. Pulsa "Deploy".

En Streamlit Community Cloud, los archivos creados localmente por la app pueden no ser persistentes según el entorno. Usa la descarga CSV con frecuencia si quieres conservar una copia de seguridad de tus registros.

## Privacidad

- No usa APIs externas.
- No envía datos a terceros.
- Guarda todo en CSV local dentro de `data/digest_log.csv`.
- `data/*.csv` y `data/*.json` están ignorados por Git para evitar subir registros personales o médicos accidentalmente.
- Si despliegas la app en la nube, revisa quién tendrá acceso a la URL y al repositorio.

## Nota médica

Esta app no reemplaza evaluación médica. Su objetivo es registrar observaciones personales para revisarlas con un profesional de salud.
