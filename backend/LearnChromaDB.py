import marimo

__generated_with = "0.12.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import chromadb
    client = chromadb.PersistentClient(path="./backend/data/chroma")
    collection = client.get_or_create_collection("issues")
    return chromadb, client, collection


@app.cell
def _(collection):
    collection.count()
    return


if __name__ == "__main__":
    app.run()
