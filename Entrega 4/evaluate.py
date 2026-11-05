import json
from pathlib import Path

from config import TOP_K
from rag import RAGSystem

GOLDEN_SET = Path(__file__).parent / "golden_set.json"


def recall_at_k(fuentes: list[str], esperado: str, k: int = TOP_K) -> float:
    return 1.0 if esperado in fuentes[:k] else 0.0


def precision_at_k(fuentes: list[str], esperado: str, k: int = TOP_K) -> float:
    return fuentes[:k].count(esperado) / k


def evaluar(nombre: str, recuperar, golden_set: list[dict]) -> None:
    """Imprime las métricas de un recuperador, por pregunta y en promedio."""
    print(f"\n=== {nombre} ===")
    recalls, precisions = [], []
    for caso in golden_set:
        fuentes = [doc.metadata["source"] for doc in recuperar(caso["pregunta"])]
        recall = recall_at_k(fuentes, caso["documento_id_esperado"])
        precision = precision_at_k(fuentes, caso["documento_id_esperado"])
        recalls.append(recall)
        precisions.append(precision)
        print(f"R@{TOP_K}={recall:.0f}  P@{TOP_K}={precision:.2f}  {caso['pregunta']}")
    print(
        f"Promedio: Recall@{TOP_K}={sum(recalls) / len(recalls):.2f}  "
        f"Precision@{TOP_K}={sum(precisions) / len(precisions):.2f}"
    )


def main() -> None:
    golden_set = json.loads(GOLDEN_SET.read_text(encoding="utf-8"))
    rag = RAGSystem()
    evaluar("Híbrido (BM25 + vectorial)", rag.retrieve, golden_set)
    evaluar("Solo vectorial", rag.vectorial.invoke, golden_set)
    evaluar("Solo BM25", rag.bm25.invoke, golden_set)


if __name__ == "__main__":
    main()
