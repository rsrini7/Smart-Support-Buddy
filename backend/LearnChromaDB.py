import marimo

__generated_with = "0.12.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import chromadb
    from app.core.config import settings
    client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
    collection = client.get_or_create_collection("production_issues")
    return chromadb, client, collection, settings


@app.cell
def _(collection):
    collection.count()
    return


if __name__ == "__main__":
    app.run()
