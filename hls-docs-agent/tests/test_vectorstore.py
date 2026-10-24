import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.vectorstore import Chunk, LocalVectorStore, chunk_markdown


def test_chunk_markdown_splits_and_respects_max_chars(tmp_path):
    content = "Para one.\n\n" + ("word " * 300) + "\n\nPara three."
    f = tmp_path / "doc.md"
    f.write_text(content)

    chunks = chunk_markdown(f, max_chars=200)

    assert len(chunks) >= 2
    assert all(c.source == "doc.md" for c in chunks)
    assert all(isinstance(c, Chunk) for c in chunks)


def test_vectorstore_returns_most_relevant_chunk_first():
    chunks = [
        Chunk(id="a", text="Loop pipelining overlaps iterations to increase throughput.", source="a.md"),
        Chunk(id="b", text="AES encryption secures data in transit and at rest.", source="b.md"),
        Chunk(id="c", text="Resource sharing binds multiple operations to one hardware unit.", source="c.md"),
    ]
    store = LocalVectorStore(collection_name="test_collection")
    store.index(chunks)

    hits = store.query("what is loop pipelining used for", n_results=1)

    assert len(hits) == 1
    assert hits[0]["source"] == "a.md"


def test_query_before_index_raises():
    store = LocalVectorStore(collection_name="test_collection_2")
    try:
        store.query("anything")
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass
