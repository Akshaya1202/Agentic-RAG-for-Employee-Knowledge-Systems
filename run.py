import json
import os
from app.evals.correctness import correctness
from app.evals.relevance import relevance
from app.evals.groundness import groundedness
from app.agents.hybrid_agents import run_query

def main():
    dataset_path = os.path.join("app", "evals", "eval_dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} evaluation samples.")
    print("=" * 60)

    for i, sample in enumerate(data, start=1):
        question = sample["question"]
        reference_answer = sample["reference_answer"]

        print(f"Sample {i}:")
        print(f"  Question: {question}")
        print(f"  Reference Answer: {reference_answer}")

        # Generate student answer using the RAG app
        try:
            print("  Generating response from RAG agent...")
            rag_response = run_query(question)
            student_answer = rag_response.get("answer", "")
            documents = rag_response.get("documents", [])
            print(f"  RAG Student Answer: {student_answer}")
        except Exception as e:
            print(f"  Error generating response from RAG: {e}")
            student_answer = sample.get("student_answer", "")
            documents = []
            print(f"  Using dataset student_answer fallback: {student_answer}")

        inputs = {"question": question}
        outputs = {"answer": student_answer, "documents": documents}

        reference_outputs = {"answer": reference_answer}

        try:
            correct_res = correctness(inputs, outputs, reference_outputs)
            print(f"  Correctness Grade: {correct_res.get('correct')}")
            print(f"  Correctness Explanation: {correct_res.get('explanation')}")
        except Exception as e:
            print(f"  Correctness Grade: Error (might require running Ollama model): {e}")

        try:
            relevance_res = relevance(inputs, outputs)
            print(f"  Relevance Grade: {relevance_res.get('relevant')}")
            print(f"  Relevance Explanation: {relevance_res.get('explanation')}")
        except Exception as e:
            print(f"  Relevance Grade: Error (might require running Ollama model): {e}")

        try:
            grounded_res = groundedness(inputs, outputs)
            print(f"  Groundedness Grade: {grounded_res.get('grounded')}")
            print(f"  Groundedness Explanation: {grounded_res.get('explanation')}")
        except Exception as e:
            print(f"  Groundedness Grade: Error (might require running Ollama model): {e}")


        print("-" * 60)

if __name__ == "__main__":
    main()
