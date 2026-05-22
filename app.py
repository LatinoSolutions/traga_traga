from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "digest_log.csv"

CSV_COLUMNS = [
    "fecha",
    "hora",
    "comida_bebida",
    "tipo",
    "cantidad",
    "velocidad",
    "grasa",
    "gas_externo",
    "gas_cerveza",
    "gas_agua_con_gas",
    "gas_bebida_gaseosa",
    "fibra_fermentable",
    "burbujeo_inmediato",
    "presion_hinchazon",
    "dolor_molestia",
    "ubicacion_principal",
    "aparece_despues",
    "alivio_eructo",
    "alivio_gases",
    "bano",
    "ansiedad_antes",
    "movimiento_despues",
    "duracion_sintomas",
    "notas",
    "created_at",
]

NUMERIC_COLUMNS = [
    "burbujeo_inmediato",
    "presion_hinchazon",
    "dolor_molestia",
    "ansiedad_antes",
]

BOOL_COLUMNS = [
    "gas_externo",
    "gas_cerveza",
    "gas_agua_con_gas",
    "gas_bebida_gaseosa",
    "alivio_eructo",
    "alivio_gases",
]


st.set_page_config(
    page_title="Digestión / Presión / Gases Tracker",
    page_icon="📝",
    layout="centered",
)


def ensure_data_file() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        pd.DataFrame(columns=CSV_COLUMNS).to_csv(DATA_FILE, index=False)


def read_data_file(show_warning: bool = True) -> pd.DataFrame:
    ensure_data_file()
    try:
        return pd.read_csv(DATA_FILE)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=CSV_COLUMNS)
    except Exception:
        if show_warning:
            st.warning(
                "No se pudo leer el archivo de datos. Revisa o reemplaza "
                "`data/digest_log.csv` desde Export / Import."
            )
        return pd.DataFrame(columns=CSV_COLUMNS)


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    for column in CSV_COLUMNS:
        if column not in df.columns:
            df[column] = False if column in BOOL_COLUMNS else ""

    df = df[CSV_COLUMNS].copy()

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int)

    for column in BOOL_COLUMNS:
        df[column] = df[column].map(parse_bool).fillna(False).astype(bool)

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
    df["hora"] = df["hora"].astype(str).str.slice(0, 5)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["fecha_hora"] = pd.to_datetime(
        df["fecha"].astype(str) + " " + df["hora"].astype(str),
        errors="coerce",
    )
    return df


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "si", "sí", "x"}


@st.cache_data(ttl=2)
def load_data() -> pd.DataFrame:
    df = read_data_file()
    return normalize_dataframe(df)


def save_record(record: dict[str, object]) -> None:
    existing = read_data_file(show_warning=False)
    existing = normalize_dataframe(existing).drop(columns=["fecha_hora"])
    updated = pd.concat([existing, pd.DataFrame([record])], ignore_index=True)
    updated = updated[CSV_COLUMNS]
    updated.to_csv(DATA_FILE, index=False)
    st.cache_data.clear()


def replace_data(df: pd.DataFrame) -> None:
    normalized = normalize_dataframe(df).drop(columns=["fecha_hora"])
    normalized.to_csv(DATA_FILE, index=False)
    st.cache_data.clear()


def merge_data(df: pd.DataFrame) -> None:
    current = load_data().drop(columns=["fecha_hora"])
    incoming = normalize_dataframe(df).drop(columns=["fecha_hora"])
    merged = pd.concat([current, incoming], ignore_index=True)
    merged = merged.drop_duplicates(subset=CSV_COLUMNS, keep="last")
    merged.to_csv(DATA_FILE, index=False)
    st.cache_data.clear()


def metric_value(series: pd.Series, kind: str = "mean") -> str:
    if series.empty:
        return "0"
    if kind == "max":
        return str(int(series.max()))
    return f"{series.mean():.1f}"


def render_summary_cards(df: pd.DataFrame) -> None:
    cols = st.columns(2)
    cols[0].metric("Comidas registradas", len(df))
    cols[1].metric("Máximo dolor", metric_value(df["dolor_molestia"], "max"))

    cols = st.columns(3)
    cols[0].metric("Prom. burbujeo", metric_value(df["burbujeo_inmediato"]))
    cols[1].metric("Prom. presión", metric_value(df["presion_hinchazon"]))
    cols[2].metric("Prom. dolor", metric_value(df["dolor_molestia"]))


def compact_table(df: pd.DataFrame, high: bool = False) -> None:
    if df.empty:
        st.info("No hay registros para mostrar.")
        return

    visible = df[
        [
            "fecha",
            "hora",
            "comida_bebida",
            "tipo",
            "burbujeo_inmediato",
            "presion_hinchazon",
            "dolor_molestia",
            "gas_externo",
            "ubicacion_principal",
            "notas",
        ]
    ].copy()

    visible = visible.rename(
        columns={
            "fecha": "Fecha",
            "hora": "Hora",
            "comida_bebida": "Comida / bebida",
            "tipo": "Tipo",
            "burbujeo_inmediato": "Burbujeo",
            "presion_hinchazon": "Presión",
            "dolor_molestia": "Dolor",
            "gas_externo": "Gas externo",
            "ubicacion_principal": "Ubicación",
            "notas": "Notas",
        }
    )

    if high:
        styled = visible.style.apply(highlight_high_symptoms, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.dataframe(visible, use_container_width=True, hide_index=True)


def highlight_high_symptoms(row: pd.Series) -> list[str]:
    is_high = row["Burbujeo"] >= 6 or row["Presión"] >= 6 or row["Dolor"] >= 6
    return ["background-color: #ffe8e8" if is_high else "" for _ in row]


def symptom_long(df: pd.DataFrame) -> pd.DataFrame:
    return df.melt(
        id_vars=["fecha_hora"],
        value_vars=["burbujeo_inmediato", "presion_hinchazon", "dolor_molestia"],
        var_name="síntoma",
        value_name="intensidad",
    ).replace(
        {
            "burbujeo_inmediato": "Burbujeo",
            "presion_hinchazon": "Presión / hinchazón",
            "dolor_molestia": "Dolor / molestia",
        }
    )


def bar_average(df: pd.DataFrame, group_column: str, title: str) -> None:
    if df.empty:
        st.info("No hay datos suficientes para este gráfico.")
        return

    grouped = (
        symptom_long(df.assign(fecha_hora=df[group_column]))
        .rename(columns={"fecha_hora": group_column})
        .groupby([group_column, "síntoma"], as_index=False)["intensidad"]
        .mean()
    )

    fig = px.bar(
        grouped,
        x=group_column,
        y="intensidad",
        color="síntoma",
        barmode="group",
        title=title,
        labels={"intensidad": "Promedio", group_column: ""},
        height=360,
    )
    st.plotly_chart(fig, use_container_width=True)


def trigger_summary(df: pd.DataFrame) -> pd.DataFrame:
    triggers = {
        "Grasa alta": df["grasa"].eq("Alta"),
        "Fibra/Fermentable alta": df["fibra_fermentable"].eq("Alta"),
        "Gas externo": df["gas_externo"],
        "Comer rápido": df["velocidad"].eq("Rápido"),
        "Cantidad grande": df["cantidad"].eq("Grande"),
        "Ansiedad >= 6": df["ansiedad_antes"].ge(6),
    }
    rows = [
        {"factor": name, "veces": int(mask.sum())}
        for name, mask in triggers.items()
        if int(mask.sum()) > 0
    ]
    return pd.DataFrame(rows).sort_values("veces", ascending=False) if rows else pd.DataFrame()


def render_disclaimer() -> None:
    st.caption(
        "Registro personal descriptivo. Esta app no diagnostica enfermedades, no da consejo médico "
        "y no reemplaza una evaluación profesional."
    )


def page_new_record() -> None:
    st.subheader("Nuevo registro")
    render_disclaimer()

    with st.form("new_record", clear_on_submit=True):
        col_date, col_time = st.columns(2)
        entry_date = col_date.date_input("Fecha", value=date.today())
        entry_time = col_time.time_input(
            "Hora",
            value=datetime.now().time().replace(second=0, microsecond=0),
        )

        food = st.text_input("Comida / bebida", placeholder="Ej: arroz con pollo, café, licuado...")

        col_type, col_amount = st.columns(2)
        food_type = col_type.selectbox("Tipo", ["Sólido", "Licuado", "Líquido", "Snack"])
        amount = col_amount.selectbox("Cantidad", ["Pequeña", "Media", "Grande"], index=1)

        col_speed, col_fat = st.columns(2)
        speed = col_speed.selectbox("Velocidad al comer", ["Lento", "Normal", "Rápido"], index=1)
        fat = col_fat.selectbox("Grasa", ["Baja", "Media", "Alta"], index=1)

        st.markdown("**Gas externo**")
        gas_cols = st.columns(3)
        gas_beer = gas_cols[0].checkbox("Cerveza")
        gas_water = gas_cols[1].checkbox("Agua con gas")
        gas_soda = gas_cols[2].checkbox("Bebida gaseosa")

        fiber = st.select_slider("Fibra/Fermentable", options=["Baja", "Media", "Alta"], value="Media")

        st.markdown("**Síntomas**")
        bubbling = st.slider("Burbujeo inmediato", 0, 10, 0)
        pressure = st.slider("Presión/Hinchazón", 0, 10, 0)
        pain = st.slider("Dolor/Molestia", 0, 10, 0)

        location = st.multiselect(
            "Ubicación principal",
            [
                "Ombligo",
                "Arriba ombligo",
                "Derecha",
                "Izquierda",
                "Abajo izquierda",
                "Abdomen superior",
                "Cambiante",
            ],
        )
        appears_after = st.selectbox("Aparece después de", ["Inmediato", "10–30 min", "1–2 h", "3+ h"])

        relief_cols = st.columns(2)
        relief_burp = relief_cols[0].checkbox("Alivio por eructo")
        relief_gas = relief_cols[1].checkbox("Alivio por gases")

        bathroom = st.selectbox("Baño", ["Normal", "Estreñido", "Suelto", "No fui"])
        anxiety = st.slider("Ansiedad antes de comer", 0, 10, 0)

        col_move, col_duration = st.columns(2)
        movement = col_move.selectbox("Movimiento después", ["Caminé", "Me acosté", "Sentado", "Otro"])
        duration = col_duration.selectbox("Duración síntomas", ["<15 min", "15–60 min", "1–3 h", "3+ h"])

        notes = st.text_area("Notas libres", height=90)

        submitted = st.form_submit_button("Guardar registro", use_container_width=True)

    if submitted:
        if not food.strip():
            st.error("Comida / bebida no puede estar vacío.")
            return

        record = {
            "fecha": entry_date.isoformat(),
            "hora": entry_time.strftime("%H:%M"),
            "comida_bebida": food.strip(),
            "tipo": food_type,
            "cantidad": amount,
            "velocidad": speed,
            "grasa": fat,
            "gas_externo": gas_beer or gas_water or gas_soda,
            "gas_cerveza": gas_beer,
            "gas_agua_con_gas": gas_water,
            "gas_bebida_gaseosa": gas_soda,
            "fibra_fermentable": fiber,
            "burbujeo_inmediato": bubbling,
            "presion_hinchazon": pressure,
            "dolor_molestia": pain,
            "ubicacion_principal": ", ".join(location),
            "aparece_despues": appears_after,
            "alivio_eructo": relief_burp,
            "alivio_gases": relief_gas,
            "bano": bathroom,
            "ansiedad_antes": anxiety,
            "movimiento_despues": movement,
            "duracion_sintomas": duration,
            "notas": notes.strip(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        save_record(record)
        st.success("Registro guardado.")


def page_today(df: pd.DataFrame) -> None:
    st.subheader("Hoy")
    today_df = df[df["fecha"] == date.today()].sort_values("fecha_hora", ascending=False)
    render_summary_cards(today_df)
    compact_table(today_df)


def page_dashboard(df: pd.DataFrame) -> None:
    st.subheader("Dashboard")
    if df.empty:
        st.info("Agrega registros para ver gráficos.")
        return

    ordered = df.dropna(subset=["fecha_hora"]).sort_values("fecha_hora")

    for column, title, label in [
        ("presion_hinchazon", "Línea temporal de presión/hinchazón", "Presión"),
        ("burbujeo_inmediato", "Línea temporal de burbujeo", "Burbujeo"),
        ("dolor_molestia", "Línea temporal de dolor", "Dolor"),
    ]:
        fig = px.line(
            ordered,
            x="fecha_hora",
            y=column,
            markers=True,
            title=title,
            labels={"fecha_hora": "Fecha y hora", column: label},
            height=320,
        )
        fig.update_yaxes(range=[0, 10])
        st.plotly_chart(fig, use_container_width=True)

    type_counts = df["tipo"].value_counts().reset_index()
    type_counts.columns = ["tipo", "registros"]
    fig = px.bar(type_counts, x="tipo", y="registros", title="Registros por tipo de comida", height=320)
    st.plotly_chart(fig, use_container_width=True)

    bar_average(df, "grasa", "Promedio de síntomas por nivel de grasa")
    bar_average(df, "fibra_fermentable", "Promedio de síntomas por nivel fibra/fermentable")

    gas_df = df.copy()
    gas_df["gas_externo_label"] = gas_df["gas_externo"].map({True: "Con gas externo", False: "Sin gas externo"})
    bar_average(gas_df, "gas_externo_label", "Promedio de síntomas con gas externo vs sin gas externo")


def page_high_symptoms(df: pd.DataFrame) -> None:
    st.subheader("Síntomas altos")
    high_df = df[
        df["presion_hinchazon"].ge(6)
        | df["dolor_molestia"].ge(6)
        | df["burbujeo_inmediato"].ge(6)
    ].sort_values("fecha_hora", ascending=False)
    compact_table(high_df, high=True)


def page_safe_foods(df: pd.DataFrame) -> None:
    st.subheader("Comidas seguras")
    safe_df = df[
        df["burbujeo_inmediato"].le(2)
        & df["presion_hinchazon"].le(2)
        & df["dolor_molestia"].le(2)
    ].sort_values("fecha_hora", ascending=False)
    compact_table(safe_df)


def page_external_gas(df: pd.DataFrame) -> None:
    st.subheader("Gas externo")
    gas_df = df[df["gas_externo"]].sort_values("fecha_hora", ascending=False)
    st.write("Registros con cerveza, agua con gas o bebida gaseosa.")
    compact_table(gas_df)

    if df.empty:
        return

    comparison = (
        df.assign(gas_externo=df["gas_externo"].map({True: "Con gas externo", False: "Sin gas externo"}))
        .groupby("gas_externo")[["burbujeo_inmediato", "presion_hinchazon", "dolor_molestia"]]
        .mean()
        .round(1)
        .reset_index()
        .rename(
            columns={
                "gas_externo": "Grupo",
                "burbujeo_inmediato": "Prom. burbujeo",
                "presion_hinchazon": "Prom. presión",
                "dolor_molestia": "Prom. dolor",
            }
        )
    )
    st.markdown("**Comparación simple**")
    st.dataframe(comparison, use_container_width=True, hide_index=True)


def page_doctor(df: pd.DataFrame) -> None:
    st.subheader("Para el doctor")
    render_disclaimer()

    since = date.today() - timedelta(days=6)
    recent = df[df["fecha"] >= since].sort_values("fecha_hora", ascending=False)

    st.markdown("**Resumen últimos 7 días**")
    render_summary_cards(recent)

    if not recent.empty:
        st.write("Síntomas máximos")
        max_table = pd.DataFrame(
            [
                {"Síntoma": "Burbujeo", "Máximo": int(recent["burbujeo_inmediato"].max())},
                {"Síntoma": "Presión/Hinchazón", "Máximo": int(recent["presion_hinchazon"].max())},
                {"Síntoma": "Dolor/Molestia", "Máximo": int(recent["dolor_molestia"].max())},
            ]
        )
        st.dataframe(max_table, use_container_width=True, hide_index=True)

        triggers = trigger_summary(recent)
        st.write("Factores frecuentes registrados")
        if triggers.empty:
            st.info("No hay factores frecuentes detectados en los últimos 7 días.")
        else:
            st.dataframe(
                triggers.rename(columns={"factor": "Factor", "veces": "Veces"}),
                use_container_width=True,
                hide_index=True,
            )

        st.write("Registros con dolor >= 5")
        pain_records = recent[recent["dolor_molestia"].ge(5)]
        compact_table(pain_records, high=True)

    csv = recent.drop(columns=["fecha_hora"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button(
        "Exportar reporte CSV",
        data=csv,
        file_name=f"reporte_digestivo_{date.today().isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
    )


def page_export_import(df: pd.DataFrame) -> None:
    st.subheader("Export / Import")

    csv = df.drop(columns=["fecha_hora"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar CSV",
        data=csv,
        file_name="digest_log.csv",
        mime="text/csv",
        use_container_width=True,
    )

    uploaded = st.file_uploader("Subir CSV existente", type=["csv"])
    if uploaded is None:
        return

    try:
        incoming = pd.read_csv(uploaded)
        preview = normalize_dataframe(incoming)
    except Exception as exc:
        st.error(f"No se pudo leer el CSV: {exc}")
        return

    st.write(f"Registros detectados: {len(preview)}")
    compact_table(preview.head(10))

    mode = st.radio("Qué hacer con el CSV subido", ["Mergear con datos actuales", "Reemplazar datos actuales"])

    if mode == "Reemplazar datos actuales":
        confirm = st.checkbox("Confirmo que quiero reemplazar todos los datos actuales")
        if st.button("Reemplazar datos", disabled=not confirm, use_container_width=True):
            replace_data(preview)
            st.success("Datos reemplazados.")
            st.rerun()
    else:
        if st.button("Mergear datos", use_container_width=True):
            merge_data(preview)
            st.success("Datos mergeados.")
            st.rerun()


def main() -> None:
    ensure_data_file()
    df = load_data()

    st.title("Digestión / Presión / Gases Tracker")
    st.caption("Datos locales en CSV. Pensado para registrar y llevar observaciones al médico.")

    page = st.sidebar.radio(
        "Navegación",
        [
            "Nuevo registro",
            "Hoy",
            "Dashboard",
            "Síntomas altos",
            "Comidas seguras",
            "Gas externo",
            "Para el doctor",
            "Export / Import",
        ],
    )

    if page == "Nuevo registro":
        page_new_record()
    elif page == "Hoy":
        page_today(df)
    elif page == "Dashboard":
        page_dashboard(df)
    elif page == "Síntomas altos":
        page_high_symptoms(df)
    elif page == "Comidas seguras":
        page_safe_foods(df)
    elif page == "Gas externo":
        page_external_gas(df)
    elif page == "Para el doctor":
        page_doctor(df)
    elif page == "Export / Import":
        page_export_import(df)


if __name__ == "__main__":
    main()
