# Run All Pending Evaluations Feature

## Overview
Added a "Run All Pending" button to the **Test page** that allows users to queue all pending evaluations for a test run with a single click.

## Location
**File**: `frontend/src/pages/Test.jsx`
**Page**: Test Runs page (the main test page where you compare runs)

## Features

### 1. **Smart Pending Detection**
- Automatically detects which QA pairs don't have completed evaluations
- Checks for existing evaluations by looking for BLEU or Answer Relevance scores
- Filters out already-completed evaluations to avoid duplicates

### 2. **Graceful Error Handling**
- Continues processing even if individual evaluations fail to queue
- Tracks both successful and failed queue attempts
- Provides detailed feedback to the user about successes and failures
- Uses try-catch blocks to prevent complete failure if one item errors

### 3. **Progress Tracking**
- Real-time progress display in the button text (e.g., "Running... (5/20)")
- Tracks completed, total, and failed counts
- Updates progress state as each evaluation is queued

### 4. **User Feedback**
- Toast notifications for:
  - Initial start message with count
  - Success message when all complete
  - Partial success message if some failed
  - Error message if all failed
  - Info message if no pending evaluations exist

### 5. **Rate Limiting Protection**
- 100ms delay between requests to avoid overwhelming the server
- Sequential processing (not parallel) to maintain stability
- Prevents duplicate evaluation triggers with backend 409 conflict detection

## How It Works

```javascript
const handleRunAllPending = async () => {
  // 1. Fetch all QA pairs for the project
  const allQaPairs = await qaAPI.getByProject(projectId);

  // 2. Get existing evaluations for this run
  const existingEvals = await evalsAPI.getByRun(runId);

  // 3. Filter to find pending items
  const pendingQaPairs = allQaPairs.filter(qa => !completedQaIds.has(qa.id));

  // 4. Queue each pending evaluation sequentially
  for (const qaPair of pendingQaPairs) {
    try {
      await evalsAPI.run({ test_run_id: runId, qa_pair_id: qaPair.id });
      // Track success
    } catch (error) {
      // Track failure, continue processing
    }
    await delay(100ms); // Rate limiting
  }
}
```

## UI Integration

### Button States
1. **Default State**: "Run All Pending" - Primary blue button
2. **Running State**: "Running... (X/Y)" - Disabled gray button
3. **Disabled**: Cannot click while running or when no run is selected

### Button Location
Located in the **QA Results** section header on the Test page, between the section title and the "Show Filters" button.

**How to find it:**
1. Navigate to a project
2. Click on a test
3. Select a test run from the dropdown (Test Run 1)
4. You'll see the "QA Results" table appear below
5. The "Run All Pending" button is in the header of that section

## Error Scenarios Handled

1. **No test run selected**: Shows error toast
2. **All evaluations complete**: Shows success message, exits early
3. **Individual evaluation fails**: Logs error, continues with next item
4. **Network errors**: Caught and displayed to user
5. **API errors**: Gracefully handled with error messages

## Backend Integration

Uses existing API endpoints:
- `qaAPI.getByProject(projectId)` - Get all QA pairs
- `evalsAPI.getByRun(runId)` - Get existing evaluations
- `evalsAPI.run({ test_run_id, qa_pair_id })` - Queue single evaluation

The backend already has:
- Duplicate prevention (409 conflict)
- WebSocket progress updates
- Async task execution
- Error handling

## State Management

New state variables added:
```javascript
const [runningAllPending, setRunningAllPending] = useState(false);
const [allPendingProgress, setAllPendingProgress] = useState({
  completed: 0,
  total: 0,
  failed: 0
});
```

## Usage

1. Navigate to a project
2. Click on a test
3. **Select a test run** from the dropdown (Test Run 1)
4. The QA Results table will appear
5. Click the **"Run All Pending"** button in the QA Results header
6. System queues all pending evaluations for that test run
7. Watch progress in button text (e.g., "Running... (15/47)")
8. Receive summary notification when complete
9. See real-time updates in the table as evaluations complete (via WebSocket)

## Benefits

- **Time Saving**: Queue all pending tests with one click instead of manually clicking each one
- **Reliability**: Graceful error handling ensures partial failures don't stop the entire batch
- **Transparency**: Clear progress tracking and feedback
- **Safe**: Rate limiting and duplicate prevention protect the system
- **User-Friendly**: Simple, intuitive interface with clear status messages

## Future Enhancements (Optional)

1. Add option to run with custom parameters (temperature, top_k, etc.)
2. Add cancel button to stop ongoing batch
3. Add option to retry only failed items
4. Show detailed progress modal instead of just button text
5. Add batch size configuration for rate limiting
