# Frontend Integration for Semantic Similarity

## Summary

The semantic similarity metric has been successfully integrated into the frontend UI to display alongside other evaluation metrics.

## Changes Made

### 1. Test.jsx (`frontend/src/pages/Test.jsx`)

**Updated websocket message handlers to include semantic_similarity:**

- **Line ~177-187**: Added `semantic_similarity` to the `lexical_metrics_calculated` stage handler
- **Line ~202-220**: Added `semantic_similarity` to the `completed` event handler

**Table display (already present):**
- **Line ~1145**: Column header "A Sem" for Run A semantic similarity
- **Line ~1153**: Column header "B Sem" for Run B semantic similarity (when comparing two runs)
- **Line ~1182**: Display cell for Run A: `{evA.semantic_similarity !== null && evA.semantic_similarity !== undefined ? Number(evA.semantic_similarity).toFixed(2) : '-'}`
- **Line ~1188**: Display cell for Run B: `{evB.semantic_similarity !== null && evB.semantic_similarity !== undefined ? Number(evB.semantic_similarity).toFixed(2) : '-'}`

### 2. EvalResult.jsx (`frontend/src/pages/EvalResult.jsx`)

**Metric display (already present):**
- **Line ~145**: MetricCard component displays semantic similarity in the Lexical Metrics section:
  ```jsx
  <MetricCard 
    title="Semantic Similarity" 
    value={lg.semantic_similarity} 
    decimals={3} 
    description="Cosine similarity of answer embeddings" 
  />
  ```

## Backend Support

The backend already properly supports semantic similarity:

1. **Database**: `semantic_similarity` column exists in `evals` table (REAL type, nullable)
2. **API Models**: Both `EvalResponse` and `FullEvalResponse` include `semantic_similarity` field
3. **Service**: `RAGEvalService.generate_and_evaluate()` calculates and returns semantic similarity
4. **Websocket**: Progress events include semantic similarity in the result payload

## Display Format

- **Table View**: Displays as 2 decimal places (e.g., "0.92")
- **Details View**: Displays as 3 decimal places (e.g., "0.923")
- **Null Handling**: Shows "-" when value is null or undefined (backward compatibility)
- **Tooltip**: Details view includes description "Cosine similarity of answer embeddings"

## Testing

To verify the integration:

1. Run an evaluation for a QA pair
2. Check the Test Runs table - "A Sem" column should show the semantic similarity score
3. Click "Details A" to view the full evaluation
4. In the Lexical Metrics section, verify "Semantic Similarity" card displays the score
5. Compare with other metrics like BLEU and ROUGE-L

## Notes

- Semantic similarity is calculated using the same embedding model configured for the test
- Values range from 0.0 (completely different) to 1.0 (identical)
- The metric complements lexical metrics by capturing semantic meaning rather than just word overlap
- Backward compatible: existing evaluations without semantic similarity show "-"
