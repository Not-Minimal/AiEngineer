from urllib.request import urlopen

from config import DATA_DIR

BASE_URL = "https://raw.githubusercontent.com/fastapi/fastapi/master/docs/es/docs"

# destino en data/ -> ruta en la documentación de FastAPI
ARCHIVOS = {
    "tutorial/first-steps.md": "tutorial/first-steps.md",
    "tutorial/path-params.md": "tutorial/path-params.md",
    "tutorial/query-params.md": "tutorial/query-params.md",
    "tutorial/query-params-str-validations.md": "tutorial/query-params-str-validations.md",
    "tutorial/body.md": "tutorial/body.md",
    "tutorial/response-model.md": "tutorial/response-model.md",
    "tutorial/handling-errors.md": "tutorial/handling-errors.md",
    "tutorial/dependencies.md": "tutorial/dependencies/index.md",
    "tutorial/security.md": "tutorial/security/index.md",
    "tutorial/middleware.md": "tutorial/middleware.md",
    "tutorial/cors.md": "tutorial/cors.md",
    "tutorial/sql-databases.md": "tutorial/sql-databases.md",
    "tutorial/background-tasks.md": "tutorial/background-tasks.md",
    "tutorial/testing.md": "tutorial/testing.md",
    "tutorial/bigger-applications.md": "tutorial/bigger-applications.md",
    "advanced/middleware.md": "advanced/middleware.md",
    "advanced/websockets.md": "advanced/websockets.md",
    "advanced/events.md": "advanced/events.md",
    "advanced/settings.md": "advanced/settings.md",
    "advanced/custom-response.md": "advanced/custom-response.md",
}


def main() -> None:
    for destino, origen in ARCHIVOS.items():
        ruta = DATA_DIR / destino
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(f"{BASE_URL}/{origen}") as respuesta:
            ruta.write_bytes(respuesta.read())
    print(f"Descargados {len(ARCHIVOS)} archivos en {DATA_DIR}")


if __name__ == "__main__":
    main()
