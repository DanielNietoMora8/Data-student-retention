import re
from pathlib import Path

import pandas as pd


def detectar_columna_programa(df: pd.DataFrame) -> str | None:
    """
    Intenta identificar automáticamente la columna que contiene el nombre del programa.
    Regla: nombre de columna que contenga 'PROG' y tenga al menos un valor con 'DESARROLLO'.
    """
    columnas = list(df.columns)
    for col in columnas:
        nombre_upper = str(col).upper()
        if "PROG" not in nombre_upper:
            continue
        serie = df[col].astype(str).str.upper()
        if serie.str.contains("SISTEMAS ELECTROMECÁNICOS", na=False).any():
            return col
    # Fallback: si no se encontró con 'DESARROLLO', devolver primera que tenga 'PROG'
    for col in columnas:
        if "PROG" in str(col).upper():
            return col
    return None


def extraer_periodo_desde_nombre(nombre_archivo: str) -> str | None:
    """
    Intenta extraer algo como '20221' o '20232' del nombre de archivo.
    """
    m = re.search(r"(20\d{2}[12])", nombre_archivo)
    if m:
        return m.group(1)
    return None


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    carpeta_dc = base_dir / "Desarrollo curricular"

    if not carpeta_dc.exists():
        print(f"No se encontró la carpeta: {carpeta_dc}")
        return

    archivos = sorted(carpeta_dc.glob("Desarrollo Curricular Notas*.xlsx"))
    if not archivos:
        print("No se encontraron archivos 'Desarrollo Curricular Notas*.xlsx' en la carpeta.")
        return

    print("Archivos encontrados:")
    for f in archivos:
        print(" -", f.name)

    dfs_filtrados: list[pd.DataFrame] = []
    resumen_archivos: list[tuple[str, int]] = []

    for ruta in archivos:
        print(f"\n=== Procesando archivo: {ruta.name} ===")
        try:
            df = pd.read_excel(ruta, engine="openpyxl")
        except Exception as e:
            print(f"  Error leyendo el archivo, se omite. Detalle: {e}")
            continue

        print(f"  Filas totales: {len(df)} | Columnas: {len(df.columns)}")

        col_programa = detectar_columna_programa(df)
        if col_programa is None:
            print("  No se pudo identificar columna de programa (nombre que contenga 'PROG'). Se omite este archivo.")
            continue

        print(f"  Columna de programa detectada: {col_programa}")

        serie_prog = df[col_programa].astype(str).str.upper()
        mask_ds = serie_prog.str.contains("SISTEMAS ELECTROMECÁNICOS", na=False)
        df_ds = df.loc[mask_ds].copy()

        n_ds = len(df_ds)
        print(f"  Registros filtrados para Desarrollo de Software (contiene 'SISTEMAS ELECTROMECÁNICOS'): {n_ds}")

        if n_ds == 0:
            continue

        # Agregar metadatos útiles
        df_ds["ORIGEN_ARCHIVO"] = ruta.name
        periodo = extraer_periodo_desde_nombre(ruta.name)
        if periodo is not None:
            df_ds["PERIODO_ARCHIVO"] = periodo

        dfs_filtrados.append(df_ds)
        resumen_archivos.append((ruta.name, n_ds))

    if not dfs_filtrados:
        print("\nNo se encontraron registros de programas que contengan 'SISTEMAS ELECTROMECÁNICOS' en ningún archivo.")
        return

    df_total = pd.concat(dfs_filtrados, ignore_index=True)
    salida = carpeta_dc / "Sistemas_Electromecanicos_Todos.xlsx"

    print(f"\nTotal de registros de Desarrollo de Software en todos los archivos: {len(df_total)}")
    print("Detalle por archivo:")
    for nombre, n in resumen_archivos:
        print(f" - {nombre}: {n} registros")

    try:
        df_total.to_excel(salida, index=False)
        print(f"\nArchivo consolidado generado en: {salida}")
    except Exception as e:
        print(f"\nError al guardar el archivo consolidado: {e}")


if __name__ == "__main__":
    main()

