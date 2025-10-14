"""
Text evaluation metrics for RAG systems.

This module provides implementations of common NLG evaluation metrics:
- BLEU: Bilingual Evaluation Understudy (multi-reference with smoothing)
- ROUGE-L: Longest Common Subsequence based metric
- SQuAD EM: Exact Match
- SQuAD Token F1: Token-level F1 score
- Content F1: Content-word based F1 for hallucination detection

All metrics support multi-reference evaluation and are designed for
evaluating generated text against reference answers.
"""

import math
import re
from collections import Counter
from typing import List, Dict, Tuple, Union

# ---------- Tokenization & normalization ----------

_WORD_RE = re.compile(r"\w+|\S", re.UNICODE)

def _tokenize(text: str) -> List[str]:
    """Language-agnostic tokenization: casefold and split into words & symbols."""
    return _WORD_RE.findall(text.casefold())

def _normalize_for_em(text: str) -> str:
    """SQuAD-style normalization: lowercase, remove punctuation/articles/extra spaces."""
    text = text.casefold()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def _content_tokens(toks: List[str]) -> List[str]:
    """Filter tokens: drop digits and very short tokens (crude content filter)."""
    return [t for t in toks if not t.isdigit() and len(t) >= 3]

# ---------- N-grams, precision, BP ----------

def _ngrams(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
    """Generate n-grams from token list."""
    return [tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def _clip_counts_across_refs(cand: Counter, refs_ngrams: List[Counter]) -> int:
    """Clip candidate n-gram counts by max reference count (multi-ref BLEU)."""
    total = 0
    for g, c in cand.items():
        max_ref = max((r.get(g, 0) for r in refs_ngrams), default=0)
        total += min(c, max_ref)
    return total

def _effective_ref_len(c_len: int, ref_lens: List[int]) -> int:
    """Choose reference length closest to candidate (BLEU standard)."""
    return min(ref_lens, key=lambda rl: (abs(rl - c_len), rl))

def _brevity_penalty(c_len: int, r_len: int) -> float:
    """Calculate BLEU brevity penalty."""
    if c_len == 0:
        return 0.0
    if c_len > r_len:
        return 1.0
    return math.exp(1 - r_len / c_len)

# ---------- ROUGE-L (best over refs) ----------

def _lcs_length(a: List[str], b: List[str]) -> int:
    """Calculate longest common subsequence length using dynamic programming."""
    m, n = len(a), len(b)
    dp = [0] * (n + 1)
    for i in range(1, m + 1):
        prev = 0
        ai = a[i-1]
        for j in range(1, n + 1):
            tmp = dp[j]
            if ai == b[j-1]:
                dp[j] = prev + 1
            else:
                dp[j] = dp[j] if dp[j] >= dp[j-1] else dp[j-1]
            prev = tmp
    return dp[n]

def rouge_l(candidate: str, references: Union[str, List[str]], beta: float = 1.0) -> Dict[str, float]:
    """
    Calculate ROUGE-L score (Longest Common Subsequence).

    Args:
        candidate: Generated text to evaluate
        references: Reference text(s) - can be single string or list
        beta: F-score beta parameter (default 1.0 for F1)

    Returns:
        Dict with precision, recall, f1, and lcs length
    """
    if isinstance(references, str):
        references = [references]
    c_toks = _tokenize(candidate)
    if not c_toks:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "lcs": 0}
    best = {"precision": 0.0, "recall": 0.0, "f1": 0.0, "lcs": 0}
    beta2 = beta * beta
    for ref in references:
        r_toks = _tokenize(ref)
        if not r_toks:
            continue
        lcs = _lcs_length(c_toks, r_toks)
        p = lcs / len(c_toks)
        r = lcs / len(r_toks)
        f1 = 0.0 if (p == 0 and r == 0) else (1 + beta2) * p * r / (r + beta2 * p)
        if f1 > best["f1"]:
            best = {"precision": p, "recall": r, "f1": f1, "lcs": lcs}
    return best

# ---------- BLEU (multi-ref, Chen & Cherry smoothing1) ----------

def bleu(candidate: str,
         references: Union[str, List[str]],
         max_n: int = 4,
         smooth: bool = True,
         weights: List[float] = None) -> Dict[str, Union[float, List[float]]]:
    """
    Calculate BLEU score with multi-reference support.

    Uses modified n-gram precision, geometric mean, and brevity penalty.
    Smoothing uses Chen & Cherry method 1 (add-one on higher-order precisions).

    Args:
        candidate: Generated text to evaluate
        references: Reference text(s) - can be single string or list
        max_n: Maximum n-gram order (default 4)
        smooth: Apply Chen & Cherry smoothing (default True)
        weights: Per-n-gram weights (default uniform)

    Returns:
        Dict with bleu score, per-n precisions, and brevity penalty
    """
    if isinstance(references, str):
        references = [references]

    c_toks = _tokenize(candidate)
    if not c_toks:
        return {"bleu": 0.0, "by_n": [0.0]*max_n, "bp": 0.0}

    refs_tok = [_tokenize(r) for r in references]
    ref_lens = [len(rt) for rt in refs_tok]
    if weights is None:
        weights = [1.0/max_n] * max_n

    precisions = []
    # precompute reference n-gram counters
    refs_ngrams_by_n = [
        [Counter(_ngrams(rt, n)) for rt in refs_tok] for n in range(1, max_n+1)
    ]
    c_len = len(c_toks)
    eff_r_len = _effective_ref_len(c_len, ref_lens)
    bp = _brevity_penalty(c_len, eff_r_len)

    smooth_m1 = 1  # smoothing counter
    for n in range(1, max_n + 1):
        cand_ngrams = Counter(_ngrams(c_toks, n))
        overlap = _clip_counts_across_refs(cand_ngrams, refs_ngrams_by_n[n-1])
        denom = max(1, sum(cand_ngrams.values()))
        p = overlap / denom if denom else 0.0
        if smooth and p == 0.0:
            # Chen & Cherry m1: add 1/(2^k * denom) after first zero
            p = 1.0 / (denom * (2 ** smooth_m1))
            smooth_m1 += 1
        precisions.append(p)

    # geometric mean
    log_sum = 0.0
    for w, p in zip(weights, precisions):
        log_sum += w * (math.log(p) if p > 0 else -1e9)
    geo_mean = math.exp(log_sum) if log_sum > -1e8 else 0.0
    score = bp * geo_mean
    return {"bleu": score, "by_n": precisions, "bp": bp}

# ---------- SQuAD EM & token-F1 ----------

def squad_em(candidate: str, references: Union[str, List[str]]) -> float:
    """
    Calculate SQuAD-style Exact Match score.

    Args:
        candidate: Generated text to evaluate
        references: Reference text(s) - can be single string or list

    Returns:
        1.0 if exact match with any reference, 0.0 otherwise
    """
    if isinstance(references, str):
        references = [references]
    cand = _normalize_for_em(candidate)
    return 1.0 if any(cand == _normalize_for_em(r) for r in references) else 0.0

def squad_token_f1(candidate: str, references: Union[str, List[str]]) -> float:
    """
    Calculate SQuAD-style token-level F1 score.

    Args:
        candidate: Generated text to evaluate
        references: Reference text(s) - can be single string or list

    Returns:
        Best F1 score across all references
    """
    if isinstance(references, str):
        references = [references]
    cand = _normalize_for_em(candidate).split()
    if not cand:
        return 0.0
    best = 0.0
    for r in references:
        ref = _normalize_for_em(r).split()
        if not ref:
            continue
        common = Counter(cand) & Counter(ref)
        num = sum(common.values())
        if num == 0:
            f1 = 0.0
        else:
            p = num / len(cand)
            s = num / len(ref)  # recall
            f1 = 2 * p * s / (p + s)
        best = max(best, f1)
    return best

# ---------- Content-word F1 (light hallucination/verbosity check) ----------

def content_f1(candidate: str, references: Union[str, List[str]]) -> Dict[str, float]:
    """
    Calculate content-word F1 for hallucination/verbosity detection.

    Filters to content words (length >= 3, non-digit) to focus on meaningful overlap.

    Args:
        candidate: Generated text to evaluate
        references: Reference text(s) - can be single string or list

    Returns:
        Dict with precision, recall, and f1
    """
    if isinstance(references, str):
        references = [references]
    c = _content_tokens(_tokenize(candidate))
    if not c:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    best = (0.0, 0.0, 0.0)
    for r in references:
        r_t = _content_tokens(_tokenize(r))
        if not r_t:
            continue
        inter = Counter(c) & Counter(r_t)
        num = sum(inter.values())
        p = num / len(c) if c else 0.0
        rc = num / len(r_t) if r_t else 0.0
        f1 = 0.0 if (p == 0 and rc == 0) else 2 * p * rc / (p + rc)
        if f1 > best[2]:
            best = (p, rc, f1)
    return {"precision": best[0], "recall": best[1], "f1": best[2]}

# ---------- Final convenience wrapper & aggregate ----------

def score_texts(candidate: str,
                references: Union[str, List[str]],
                max_n: int = 4,
                smooth: bool = True,
                aggregate_weights: Tuple[float, float, float, float] = (0.30, 0.40, 0.20, 0.10)
                ) -> Dict[str, Union[float, List[float]]]:
    """
    Comprehensive text evaluation with multiple metrics.

    Computes BLEU, ROUGE-L, SQuAD EM/F1, Content F1, and a weighted aggregate score.

    Args:
        candidate: Generated text to evaluate
        references: Reference text(s) - can be single string or list
        max_n: Maximum n-gram order for BLEU (default 4)
        smooth: Apply BLEU smoothing (default True)
        aggregate_weights: Tuple of (BLEU_w, ROUGE_L_w, ContentF1_w, EM_w)
                          Must sum to 1.0

    Returns:
        Dict containing all metric scores and aggregate score
    """
    if isinstance(references, str):
        references = [references]

    b = bleu(candidate, references, max_n=max_n, smooth=smooth)
    r = rouge_l(candidate, references)
    em = squad_em(candidate, references)
    sf1 = squad_token_f1(candidate, references)
    cf = content_f1(candidate, references)

    w_bleu, w_rouge, w_cf1, w_em = aggregate_weights
    aggregate = (w_bleu * b["bleu"]
                 + w_rouge * r["f1"]
                 + w_cf1 * cf["f1"]
                 + w_em * em)

    return {
        # Core metrics
        "BLEU": b["bleu"],
        "BLEU_by_n": b["by_n"],
        "BLEU_BP": b["bp"],
        "ROUGE_L": r["f1"],
        "ROUGE_L_precision": r["precision"],
        "ROUGE_L_recall": r["recall"],
        "ROUGE_L_lcs": r["lcs"],
        # QA-style metrics
        "SQuAD_EM": em,
        "SQuAD_token_F1": sf1,
        # Content-word F1
        "ContentF1": cf["f1"],
        "ContentF1_precision": cf["precision"],
        "ContentF1_recall": cf["recall"],
        # Aggregate (tunable)
        "Aggregate": aggregate,
        "Aggregate_weights": {
            "BLEU": w_bleu,
            "ROUGE_L": w_rouge,
            "ContentF1": w_cf1,
            "EM": w_em
        },
    }

# --- Example usage ---
if __name__ == "__main__":
    refs = ["The cat is sitting on the mat.", "A cat sits on the mat."]
    gen = "The cat sat on the mat."
    result = score_texts(gen, refs)

    print("Example Evaluation Results:")
    print(f"BLEU: {result['BLEU']:.4f}")
    print(f"ROUGE-L F1: {result['ROUGE_L']:.4f}")
    print(f"SQuAD EM: {result['SQuAD_EM']:.4f}")
    print(f"SQuAD Token F1: {result['SQuAD_token_F1']:.4f}")
    print(f"Content F1: {result['ContentF1']:.4f}")
    print(f"Aggregate Score: {result['Aggregate']:.4f}")
