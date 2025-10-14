"""
Test file for metrics package.

Run this to verify all metric functions work correctly.
"""

from text_metrics import bleu, rouge_l, squad_em, squad_token_f1, content_f1, score_texts


def test_basic_metrics():
    """Test basic metric calculations."""
    print("=" * 60)
    print("Testing Basic Metrics")
    print("=" * 60)

    # Test data
    candidate = "The cat sat on the mat."
    references = ["The cat is sitting on the mat.", "A cat sits on the mat."]

    # Test BLEU
    bleu_result = bleu(candidate, references)
    print(f"\n1. BLEU Score: {bleu_result['bleu']:.4f}")
    print(f"   - Brevity Penalty: {bleu_result['bp']:.4f}")
    print(f"   - Precisions by n-gram: {[f'{p:.4f}' for p in bleu_result['by_n']]}")

    # Test ROUGE-L
    rouge_result = rouge_l(candidate, references)
    print(f"\n2. ROUGE-L F1: {rouge_result['f1']:.4f}")
    print(f"   - Precision: {rouge_result['precision']:.4f}")
    print(f"   - Recall: {rouge_result['recall']:.4f}")
    print(f"   - LCS Length: {rouge_result['lcs']}")

    # Test SQuAD EM
    em_result = squad_em(candidate, references)
    print(f"\n3. SQuAD Exact Match: {em_result:.4f}")

    # Test SQuAD Token F1
    token_f1_result = squad_token_f1(candidate, references)
    print(f"\n4. SQuAD Token F1: {token_f1_result:.4f}")

    # Test Content F1
    content_result = content_f1(candidate, references)
    print(f"\n5. Content F1: {content_result['f1']:.4f}")
    print(f"   - Precision: {content_result['precision']:.4f}")
    print(f"   - Recall: {content_result['recall']:.4f}")


def test_comprehensive_scoring():
    """Test comprehensive scoring function."""
    print("\n" + "=" * 60)
    print("Testing Comprehensive Scoring")
    print("=" * 60)

    candidate = "Paris is the capital of France."
    reference = "The capital city of France is Paris."

    result = score_texts(candidate, reference)

    print(f"\nCandidate: {candidate}")
    print(f"Reference: {reference}")
    print("\nAll Metrics:")
    print(f"  BLEU:           {result['BLEU']:.4f}")
    print(f"  ROUGE-L:        {result['ROUGE_L']:.4f}")
    print(f"  SQuAD EM:       {result['SQuAD_EM']:.4f}")
    print(f"  SQuAD Token F1: {result['SQuAD_token_F1']:.4f}")
    print(f"  Content F1:     {result['ContentF1']:.4f}")
    print(f"\n  Aggregate Score: {result['Aggregate']:.4f}")
    print(f"  Weights: {result['Aggregate_weights']}")


def test_edge_cases():
    """Test edge cases."""
    print("\n" + "=" * 60)
    print("Testing Edge Cases")
    print("=" * 60)

    # Empty candidate
    print("\n1. Empty candidate:")
    result = bleu("", "reference text")
    print(f"   BLEU: {result['bleu']:.4f}")

    # Exact match
    print("\n2. Exact match:")
    text = "The quick brown fox."
    result = score_texts(text, text)
    print(f"   BLEU: {result['BLEU']:.4f}")
    print(f"   ROUGE-L: {result['ROUGE_L']:.4f}")
    print(f"   SQuAD EM: {result['SQuAD_EM']:.4f}")

    # Multiple references
    print("\n3. Multiple references:")
    candidate = "The dog runs fast."
    refs = ["The dog is running quickly.", "A fast dog runs.", "The dog runs rapidly."]
    result = score_texts(candidate, refs)
    print(f"   BLEU: {result['BLEU']:.4f}")
    print(f"   ROUGE-L: {result['ROUGE_L']:.4f}")
    print(f"   Best Token F1: {result['SQuAD_token_F1']:.4f}")


def test_rag_scenario():
    """Test realistic RAG evaluation scenario."""
    print("\n" + "=" * 60)
    print("Testing RAG Evaluation Scenario")
    print("=" * 60)

    # Simulate RAG system outputs
    question = "What is the capital of France?"

    ground_truth = "The capital of France is Paris."
    llm_answer_good = "Paris is the capital of France."
    llm_answer_verbose = "Paris is the capital of France. It is a beautiful city with many attractions like the Eiffel Tower."
    llm_answer_wrong = "The capital of France is Lyon."

    print(f"\nQuestion: {question}")
    print(f"Ground Truth: {ground_truth}")

    print("\n--- Good Answer ---")
    print(f"LLM Answer: {llm_answer_good}")
    result = score_texts(llm_answer_good, ground_truth)
    print(f"BLEU: {result['BLEU']:.4f} | ROUGE-L: {result['ROUGE_L']:.4f} | Aggregate: {result['Aggregate']:.4f}")

    print("\n--- Verbose Answer (may indicate hallucination) ---")
    print(f"LLM Answer: {llm_answer_verbose}")
    result = score_texts(llm_answer_verbose, ground_truth)
    print(f"BLEU: {result['BLEU']:.4f} | ROUGE-L: {result['ROUGE_L']:.4f} | Aggregate: {result['Aggregate']:.4f}")
    print(f"Content F1: {result['ContentF1']:.4f} (lower = more extra content)")

    print("\n--- Wrong Answer ---")
    print(f"LLM Answer: {llm_answer_wrong}")
    result = score_texts(llm_answer_wrong, ground_truth)
    print(f"BLEU: {result['BLEU']:.4f} | ROUGE-L: {result['ROUGE_L']:.4f} | Aggregate: {result['Aggregate']:.4f}")


if __name__ == "__main__":
    test_basic_metrics()
    test_comprehensive_scoring()
    test_edge_cases()
    test_rag_scenario()

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
