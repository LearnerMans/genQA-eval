import { useState, useEffect, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { useToast } from '../components/Toaster';
import { fetchTestRuns, fetchEvaluationsForRun, qaAPI } from '../services/api';

const Analytics = ({ projectId, testId }) => {
  const [loading, setLoading] = useState(true);
  const [testRuns, setTestRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(null);
  const [evaluations, setEvaluations] = useState([]);
  const [qaPairs, setQAPairs] = useState({});
  const [selectedMetric, setSelectedMetric] = useState('answer_relevance');
  const [selectedBin, setSelectedBin] = useState(null);
  const { showToast } = useToast();

  // Load test runs
  useEffect(() => {
    const loadTestRuns = async () => {
      try {
        setLoading(true);
        const runs = await fetchTestRuns(testId);
        console.log('All test runs:', runs);
        // Show all test runs (test_runs don't have training_status - that's on the test itself)
        setTestRuns(runs);
        if (runs.length > 0) {
          setSelectedRunId(runs[0].id);
        }
      } catch (error) {
        showToast('Failed to load test runs', 'error');
        console.error('Error loading test runs:', error);
      } finally {
        setLoading(false);
      }
    };

    if (testId) {
      loadTestRuns();
    }
  }, [testId, showToast]);

  // Load evaluations for selected run
  useEffect(() => {
    const loadEvaluations = async () => {
      if (!selectedRunId) return;

      try {
        setLoading(true);
        const evals = await fetchEvaluationsForRun(selectedRunId);
        setEvaluations(evals);

        // Fetch all unique QA pairs
        const uniqueQAIds = [...new Set(evals.map(e => e.qa_pair_id))];
        console.log('Unique QA IDs:', uniqueQAIds);
        const qaData = {};
        await Promise.all(
          uniqueQAIds.map(async (qaId) => {
            try {
              const qa = await qaAPI.getById(qaId);
              console.log(`Fetched QA pair ${qaId}:`, qa);
              qaData[qaId] = qa;
            } catch (err) {
              console.error(`Failed to fetch QA pair ${qaId}:`, err);
            }
          })
        );
        console.log('All QA pairs data:', qaData);
        setQAPairs(qaData);
      } catch (error) {
        showToast('Failed to load evaluations', 'error');
        console.error('Error loading evaluations:', error);
      } finally {
        setLoading(false);
      }
    };

    loadEvaluations();
  }, [selectedRunId, showToast]);

  // Calculate histogram data
  const histogramData = useMemo(() => {
    if (!evaluations.length) return [];

    const metrics = {
      answer_relevance: { min: 1, max: 5, bins: 5, label: 'Answer Relevance' },
      context_relevance: { min: 1, max: 5, bins: 5, label: 'Context Relevance' },
      groundedness: { min: 1, max: 5, bins: 5, label: 'Groundedness' },
      bleu: { min: 0, max: 1, bins: 10, label: 'BLEU' },
      rouge_l: { min: 0, max: 1, bins: 10, label: 'ROUGE-L' }
    };

    const metric = metrics[selectedMetric];
    if (!metric) return [];

    const binSize = (metric.max - metric.min) / metric.bins;
    const bins = Array.from({ length: metric.bins }, (_, i) => {
      const start = metric.min + i * binSize;
      const end = start + binSize;
      return {
        range: `${start.toFixed(2)}-${end.toFixed(2)}`,
        start,
        end,
        count: 0,
        qaIds: []
      };
    });

    evaluations.forEach(eval_item => {
      // Handle rouge_l fallback to rouge for backward compatibility
      let value = eval_item[selectedMetric];
      if (selectedMetric === 'rouge_l') {
        value = eval_item.rouge_l ?? eval_item.rouge;
      }

      if (value !== null && value !== undefined) {
        const binIndex = Math.min(
          Math.floor((value - metric.min) / binSize),
          metric.bins - 1
        );
        if (binIndex >= 0 && binIndex < bins.length) {
          bins[binIndex].count++;
          bins[binIndex].qaIds.push({
            qa_pair_id: eval_item.qa_pair_id,
            eval_id: eval_item.eval_id,
            value: value
          });
        }
      }
    });

    return bins;
  }, [evaluations, selectedMetric]);

  // Get QA pairs for selected bin
  const selectedQAPairs = useMemo(() => {
    if (selectedBin === null) return [];
    return histogramData[selectedBin]?.qaIds || [];
  }, [selectedBin, histogramData]);

  // Calculate summary statistics
  const statistics = useMemo(() => {
    if (!evaluations.length) return null;

    const values = evaluations
      .map(e => {
        // Handle rouge_l fallback to rouge for backward compatibility
        if (selectedMetric === 'rouge_l') {
          return e.rouge_l ?? e.rouge;
        }
        return e[selectedMetric];
      })
      .filter(v => v !== null && v !== undefined);

    if (!values.length) return null;

    const sum = values.reduce((a, b) => a + b, 0);
    const mean = sum / values.length;
    const sorted = [...values].sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)];
    const min = Math.min(...values);
    const max = Math.max(...values);
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);

    return { mean, median, min, max, stdDev, count: values.length };
  }, [evaluations, selectedMetric]);

  // Custom tooltip for histogram
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-surface border border-border rounded-lg p-3 shadow-lg">
          <p className="font-semibold text-text">{payload[0].payload.range}</p>
          <p className="text-primary font-medium">{payload[0].value} QA pairs</p>
        </div>
      );
    }
    return null;
  };

  const getBarColor = (index) => {
    const colors = [
      'var(--color-primary)',
      'var(--color-accent)',
      'var(--color-info)',
      'var(--color-success)',
      'var(--color-warning)',
      '#6366f1', // indigo
      '#ec4899', // pink
      '#14b8a6', // teal
      '#f97316', // orange
      '#8b5cf6'  // purple
    ];
    return colors[index % colors.length];
  };

  const navigateToEval = (qaId) => {
    window.location.hash = `#project/${projectId}/test/${testId}/run/${selectedRunId}/qa/${qaId}`;
  };

  const navigateBack = () => {
    window.location.hash = `#project/${projectId}/test/${testId}`;
  };

  if (loading && !evaluations.length) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-2">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
          <span className="text-text">Loading analytics...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={navigateBack}
          className="text-primary hover:underline mb-4 flex items-center gap-2"
        >
          <span>←</span> Back to Test
        </button>
        <h1 className="font-heading font-bold text-2xl text-text mb-2">Analytics Dashboard</h1>
        <p className="text-text opacity-70">Evaluation metrics overview and distribution analysis</p>
      </div>

      {/* Test Run Selector */}
      <div className="mb-6 border border-secondary rounded-lg p-4 bg-background">
        <label className="block font-semibold text-text mb-2">Select Test Run:</label>
        {testRuns.length === 0 ? (
          <div className="text-text opacity-70 py-2">
            No test runs available. Create and run a test run first to see analytics.
          </div>
        ) : (
          <select
            value={selectedRunId || ''}
            onChange={(e) => setSelectedRunId(e.target.value)}
            className="w-full md:w-96 px-3 py-2 border border-secondary rounded-lg bg-background text-text focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {testRuns.map(run => (
              <option key={run.id} value={run.id}>
                {new Date(run.created_at).toLocaleString()} - Run {run.id.slice(0, 8)}
              </option>
            ))}
          </select>
        )}
      </div>

      {testRuns.length === 0 ? null : evaluations.length === 0 ? (
        <div className="text-center py-12 text-text opacity-70">
          No evaluations available for this test run.
        </div>
      ) : (
        <>
          {/* Metric Selector */}
          <div className="mb-6 border border-secondary rounded-lg p-4 bg-background">
            <label className="block font-semibold text-text mb-3">Select Metric:</label>
            <div className="flex flex-wrap gap-2">
              {[
                { id: 'answer_relevance', label: 'Answer Relevance' },
                { id: 'context_relevance', label: 'Context Relevance' },
                { id: 'groundedness', label: 'Groundedness' },
                { id: 'bleu', label: 'BLEU' },
                { id: 'rouge_l', label: 'ROUGE-L' }
              ].map(metric => (
                <button
                  key={metric.id}
                  onClick={() => {
                    setSelectedMetric(metric.id);
                    setSelectedBin(null);
                  }}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    selectedMetric === metric.id
                      ? 'bg-primary text-white'
                      : 'bg-secondary text-text hover:bg-opacity-80'
                  }`}
                >
                  {metric.label}
                </button>
              ))}
            </div>
          </div>

          {/* Statistics Summary */}
          {statistics && (
            <div className="mb-6 grid grid-cols-2 md:grid-cols-6 gap-4">
              {[
                { label: 'Count', value: statistics.count },
                { label: 'Mean', value: statistics.mean.toFixed(3) },
                { label: 'Median', value: statistics.median.toFixed(3) },
                { label: 'Min', value: statistics.min.toFixed(3) },
                { label: 'Max', value: statistics.max.toFixed(3) },
                { label: 'Std Dev', value: statistics.stdDev.toFixed(3) }
              ].map((stat, idx) => (
                <div key={idx} className="border border-secondary rounded-lg p-4 bg-background">
                  <div className="text-text opacity-70 text-sm mb-1">{stat.label}</div>
                  <div className="font-heading font-bold text-xl text-text">{stat.value}</div>
                </div>
              ))}
            </div>
          )}

          {/* Histogram */}
          <div className="mb-6 border border-secondary rounded-lg p-6 bg-background">
            <h2 className="font-heading font-bold text-lg text-text mb-4">
              Distribution of {selectedMetric.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
            </h2>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart
                data={histogramData}
                onClick={(data) => {
                  if (data && data.activeTooltipIndex !== undefined) {
                    setSelectedBin(data.activeTooltipIndex);
                  }
                }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis
                  dataKey="range"
                  stroke="var(--color-text)"
                  tick={{ fill: 'var(--color-text)' }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis
                  stroke="var(--color-text)"
                  tick={{ fill: 'var(--color-text)' }}
                  label={{ value: 'Number of QA Pairs', angle: -90, position: 'insideLeft', style: { fill: 'var(--color-text)' } }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="count"
                  cursor="pointer"
                  radius={[8, 8, 0, 0]}
                >
                  {histogramData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={selectedBin === index ? 'var(--color-accent)' : getBarColor(index)}
                      opacity={selectedBin !== null && selectedBin !== index ? 0.4 : 1}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-sm text-text opacity-70 mt-2 text-center">
              Click on a bar to view QA pairs in that range
            </p>
          </div>

          {/* Selected Bin QA Pairs */}
          {selectedBin !== null && selectedQAPairs.length > 0 && (
            <div className="border border-secondary rounded-lg p-6 bg-background">
              <h3 className="font-heading font-bold text-lg text-text mb-4">
                QA Pairs in range {histogramData[selectedBin].range} ({selectedQAPairs.length} pairs)
              </h3>
              <div className="space-y-4 max-h-[600px] overflow-y-auto">
                {selectedQAPairs.map((qa, idx) => {
                  const evalItem = evaluations.find(e => e.qa_pair_id === qa.qa_pair_id);
                  const qaPair = qaPairs[qa.qa_pair_id];
                  console.log('Rendering QA pair:', { qa, evalItem, qaPair });
                  return (
                    <div
                      key={idx}
                      onClick={() => navigateToEval(qa.qa_pair_id)}
                      className="border border-border rounded-lg p-4 hover:bg-secondary cursor-pointer transition-colors"
                    >
                      {/* Header with ID and Score */}
                      <div className="flex justify-between items-start mb-3">
                        <div className="font-medium text-text">QA Pair: {qa.qa_pair_id.slice(0, 8)}...</div>
                        <div className="px-3 py-1 rounded-full text-sm font-semibold" style={{
                          backgroundColor: 'var(--color-primary)',
                          color: 'white'
                        }}>
                          {qa.value.toFixed(2)}
                        </div>
                      </div>

                      {(evalItem || qaPair) && (
                        <div className="space-y-3">
                          {/* Question */}
                          <div>
                            <div className="font-semibold text-text text-sm mb-1">Question:</div>
                            <div className="text-sm text-text opacity-90 pl-3 border-l-2 border-primary">
                              {qaPair?.question || 'N/A'}
                            </div>
                          </div>

                          {/* Expected Answer */}
                          <div>
                            <div className="font-semibold text-text text-sm mb-1">Expected Answer:</div>
                            <div className="text-sm text-text opacity-90 pl-3 border-l-2 border-success">
                              {qaPair?.answer || 'N/A'}
                            </div>
                          </div>

                          {/* Generated Answer */}
                          <div>
                            <div className="font-semibold text-text text-sm mb-1">Generated Answer:</div>
                            <div className="text-sm text-text opacity-90 pl-3 border-l-2 border-accent">
                              {evalItem?.answer || 'N/A'}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Analytics;
