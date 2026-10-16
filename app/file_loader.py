from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xlsm"}


def load_file(file_path: str | Path) -> pd.DataFrame:
    """Load a supported CSV or Excel file into a DataFrame."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Expected a file, received: {path}")

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            f"Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if extension == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)

    if df.empty and len(df.columns) == 0:
        raise ValueError("The file contains no columns or data.")

    if len(df.columns) == 0:
        raise ValueError("The file contains no columns.")

    if not all(isinstance(column, str) for column in df.columns):
        df.columns = [str(column) for column in df.columns]

    if not df.columns.is_unique:
        raise ValueError(
            "The file contains duplicate column names. "
            "Rename them so each column has a unique name."
        )

    return df


def profile_dataframe(df: pd.DataFrame) -> dict:
    """Generate a structured data-quality and schema profile."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    columns = []

    for column in df.columns:
        series = df[column]

        columns.append(
            {
                "name": str(column),
                "data_type": str(series.dtype),
                "non_null_count": int(series.notna().sum()),
                "missing_count": int(series.isna().sum()),
                "missing_percentage": (
                    round(float(series.isna().mean() * 100), 2)
                    if len(df) > 0
                    else 0.0
                ),
                "unique_count": int(series.nunique()),
            }
        )

    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "duplicate_row_count": int(df.duplicated().sum()),
        "columns": columns,
    }


def load_and_profile(file_path: str | Path) -> dict:
    """Load a supported file and return its data and profile."""

    df = load_file(file_path)

    return {
        "dataframe": df,
        "profile": profile_dataframe(df),
    }