"""
Anonimiza personas en archivos *_Todos.xlsx usando columnas Nombres y Apellidos.
Cada archivo tiene sus propios ID anónimos (S1, S2, ..., Sn) independientes.
Guarda resultados en Desarrollo curricular/pre-processed.
"""
from pathlib import Path

import pandas as pd


def normalizar_clave(nombres: str, apellidos: str) -> tuple[str, str]:
    """Normaliza nombres y apellidos para agrupar la misma persona."""
    n = str(nombres).strip() if pd.notna(nombres) else ""
    a = str(apellidos).strip() if pd.notna(apellidos) else ""
    return (n, a)


def buscar_columnas(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """Encuentra columnas Nombres y Apellidos (insensible a mayúsculas)."""
    cols_upper = {c.strip().upper(): c for c in df.columns if isinstance(c, str)}
    col_n = cols_upper.get("NOMBRES") or cols_upper.get("NOMBRE")
    col_a = cols_upper.get("APELLIDOS") or cols_upper.get("APELLIDO")
    return (col_n, col_a)


def main() -> None:
    base = Path(__file__).resolve().parent
    carpeta_dc = base / "Desarrollo curricular"
    carpeta_out = carpeta_dc / "pre-processed"

    if not carpeta_dc.exists():
        print(f"No se encontró la carpeta: {carpeta_dc}")
        return

    # Archivos que terminan en _Todos.xlsx
    archivos = sorted(carpeta_dc.glob("*_Todos.xlsx"))
    if not archivos:
        print("No se encontraron archivos '*_Todos.xlsx' en Desarrollo curricular.")
        return

    print("Archivos a procesar:")
    for f in archivos:
        print("  -", f.name)

    carpeta_out.mkdir(parents=True, exist_ok=True)

    # Por cada archivo: personas únicas solo de ese archivo, IDs S1..Sn propios
    for ruta in archivos:
        try:
            df = pd.read_excel(ruta, engine="openpyxl")
        except Exception as e:
            print(f"Error leyendo {ruta.name}: {e}")
            continue
        col_nombres, col_apellidos = buscar_columnas(df)
        if col_nombres is None or col_apellidos is None:
            print(f"  Saltando {ruta.name}: no se encontraron columnas Nombres y Apellidos.")
            continue

        # Personas únicas solo en este archivo
        personas_archivo: set[tuple[str, str]] = set()
        for _, row in df[[col_nombres, col_apellidos]].iterrows():
            personas_archivo.add(normalizar_clave(row[col_nombres], row[col_apellidos]))
        personas_ordenadas = sorted(personas_archivo)
        mapping: dict[tuple[str, str], str] = {
            p: f"S{i}" for i, p in enumerate(personas_ordenadas, start=1)
        }

        claves = df.apply(
            lambda row: normalizar_clave(row[col_nombres], row[col_apellidos]), axis=1
        )
        df["ID_anonimo"] = claves.map(mapping)

        salida = carpeta_out / ruta.name
        try:
            df.to_excel(salida, index=False)
            n = len(personas_ordenadas)
            print(f"  {ruta.name}: {n} personas únicas (S1..S{n}) -> {salida.name}")
        except Exception as e:
            print(f"  Error guardando {ruta.name}: {e}")

    print(f"\nArchivos anonimizados guardados en: {carpeta_out}")


if __name__ == "__main__":
    main()
