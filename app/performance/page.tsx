"use client";

import { useEffect, useMemo, useState } from "react";
import AdminShell from "@/components/layout/AdminShell";

type PerformanceResult = "SUCCESS" | "FAILED";

type PerformanceOverview = {
  total_completed_signals: number;
  successful_signals: number;
  failed_signals: number;
  success_rate: number | null;

  total_predictions: number;
  correct_predictions: number;
  incorrect_predictions: number;
  prediction_accuracy: number | null;

  correct_safe_predictions: number;
  incorrect_safe_predictions: number;
  safe_prediction_precision: number | null;

  correct_mine_predictions: number;
  incorrect_mine_predictions: number;
  mine_prediction_precision: number | null;

  average_result_accuracy: number | null;
};

type ModelPerformance = {
  model_id: string;
  model_version: string;
  model_name: string;

  total_completed_signals: number;
  successful_signals: number;
  failed_signals: number;
  success_rate: number | null;

  prediction_accuracy: number | null;

  total_predictions: number;
  correct_predictions: number;
  incorrect_predictions: number;

  correct_safe_predictions: number;
  incorrect_safe_predictions: number;
  safe_prediction_precision: number | null;

  correct_mine_predictions: number;
  incorrect_mine_predictions: number;
  mine_prediction_precision: number | null;

  average_result_accuracy: number | null;
};

type BoardPerformance = {
  board_size: number;
  mine_count: number;

  total_completed_signals: number;

  successful_signals: number;
  failed_signals: number;
  success_rate: number | null;

  prediction_accuracy: number | null;

  total_predictions: number;
  correct_predictions: number;
  incorrect_predictions: number;

  correct_safe_predictions: number;
  incorrect_safe_predictions: number;
  safe_prediction_precision: number | null;

  correct_mine_predictions: number;
  incorrect_mine_predictions: number;
  mine_prediction_precision: number | null;

  average_result_accuracy: number | null;
};

type PerformanceRecent = {
  signal_id: string;
  result_id: string;

  game: string;

  board_size: number;
  mine_count: number;

  model_id: string | null;
  model_version: string | null;

  status: PerformanceResult;

  correct_predictions: number;
  incorrect_predictions: number;
  accuracy: number | null;

  correct_safe_predictions: number;
  incorrect_safe_predictions: number;

  correct_mine_predictions: number;
  incorrect_mine_predictions: number;

  confidence: number | null;

  recorded_at: string;
};

type PerformanceSignal = {
  id: string;
  signalNumber: string;
  mineCount: number;
  confidence: number | null;
  correct: number;
  incorrect: number;
  accuracy: number;
  attempts: number | null;
  result: PerformanceResult;
  completedAt: string;
};

type TrendItem = {
  day: string;
  accuracy: number;
  signals: number;
};

type ConfidencePerformance = {
  range: string;
  signals: number;
  accuracy: number;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

const PERFORMANCE_API =
  `${API_URL}/api/performance`;


export default function PerformancePage() {
  const [period, setPeriod] = useState("7 Days");
  const [mineFilter, setMineFilter] = useState("All Mines");
  const [search, setSearch] = useState("");

  const [overview, setOverview] =
    useState<PerformanceOverview | null>(null);

  const [models, setModels] =
    useState<ModelPerformance[]>([]);

  const [boardPerformance, setBoardPerformance] =
    useState<BoardPerformance[]>([]);

  const [recentPerformance, setRecentPerformance] =
    useState<PerformanceRecent[]>([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);


  // ------------------------------------------------------------
  // LOAD PERFORMANCE DATA
  // ------------------------------------------------------------

  useEffect(() => {
    let cancelled = false;

    async function loadPerformance() {
      setIsLoading(true);
      setErrorMessage(null);

      try {
        const [
          overviewResponse,
          modelsResponse,
          boardResponse,
          recentResponse,
        ] = await Promise.all([
          fetch(
            `${PERFORMANCE_API}/overview`,
            {
              method: "GET",
              credentials: "include",
              cache: "no-store",
            }
          ),

          fetch(
            `${PERFORMANCE_API}/models`,
            {
              method: "GET",
              credentials: "include",
              cache: "no-store",
            }
          ),

          fetch(
            `${PERFORMANCE_API}/board`,
            {
              method: "GET",
              credentials: "include",
              cache: "no-store",
            }
          ),

          fetch(
            `${PERFORMANCE_API}/recent?limit=100`,
            {
              method: "GET",
              credentials: "include",
              cache: "no-store",
            }
          ),
        ]);


        if (!overviewResponse.ok) {
          throw new Error(
            "Unable to load performance overview."
          );
        }

        if (!modelsResponse.ok) {
          throw new Error(
            "Unable to load model performance."
          );
        }

        if (!boardResponse.ok) {
          throw new Error(
            "Unable to load board performance."
          );
        }

        if (!recentResponse.ok) {
          throw new Error(
            "Unable to load recent performance."
          );
        }


        const [
          overviewData,
          modelsData,
          boardData,
          recentData,
        ] = await Promise.all([
          overviewResponse.json(),
          modelsResponse.json(),
          boardResponse.json(),
          recentResponse.json(),
        ]);


        if (cancelled) {
          return;
        }


        setOverview(overviewData);

        setModels(
          Array.isArray(modelsData)
            ? modelsData
            : []
        );

        setBoardPerformance(
          Array.isArray(boardData)
            ? boardData
            : []
        );

        setRecentPerformance(
          Array.isArray(recentData)
            ? recentData
            : []
        );

      } catch (error) {
        if (cancelled) {
          return;
        }

        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to load performance data."
        );
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }


    loadPerformance();


    return () => {
      cancelled = true;
    };
  }, []);


  // ------------------------------------------------------------
  // FORMAT RECENT RESULTS FOR EXISTING UI
  // ------------------------------------------------------------

  const performanceSignals =
    useMemo<PerformanceSignal[]>(() => {
      return recentPerformance.map(
        (item) => ({
          id: item.result_id,

          signalNumber:
            formatSignalNumber(
              item.signal_id
            ),

          mineCount:
            item.mine_count,

          confidence:
            item.confidence,

          correct:
            item.correct_predictions,

          incorrect:
            item.incorrect_predictions,

          accuracy:
            item.accuracy ?? 0,

          /*
           * The current Performance API does not expose
           * prediction attempts.
           */
          attempts: null,

          result:
            item.status,

          completedAt:
            formatDateTime(
              item.recorded_at
            ),
        })
      );
    }, [recentPerformance]);


  // ------------------------------------------------------------
  // FILTERED SIGNALS
  // ------------------------------------------------------------

  const filteredSignals =
    useMemo(() => {
      const normalizedSearch =
        search.trim().toLowerCase();

      return performanceSignals.filter(
        (signal) => {
          const matchesSearch =
            signal.signalNumber
              .toLowerCase()
              .includes(normalizedSearch);

          const matchesMine =
            mineFilter === "All Mines" ||
            signal.mineCount ===
              Number(mineFilter);

          return (
            matchesSearch &&
            matchesMine
          );
        }
      );
    }, [
      performanceSignals,
      search,
      mineFilter,
    ]);


  // ------------------------------------------------------------
  // MINE PERFORMANCE
  // ------------------------------------------------------------

  const minePerformance =
    useMemo(() => {
      return [...boardPerformance]
        .sort(
          (a, b) =>
            a.mine_count -
            b.mine_count
        )
        .map((item) => ({
          mines:
            `${item.mine_count} Mines`,

          signals:
            item.total_completed_signals,

          accuracy:
            item.prediction_accuracy ?? 0,

          success:
            item.successful_signals,
        }));
    }, [boardPerformance]);


  // ------------------------------------------------------------
  // CONFIDENCE PERFORMANCE
  // ------------------------------------------------------------

  const confidencePerformance =
    useMemo<ConfidencePerformance[]>(() => {
      const ranges = [
        {
          label: "90–100%",
          min: 90,
          max: 100,
        },
        {
          label: "80–89%",
          min: 80,
          max: 89.999,
        },
        {
          label: "70–79%",
          min: 70,
          max: 79.999,
        },
        {
          label: "Below 70%",
          min: -Infinity,
          max: 69.999,
        },
      ];


      return ranges.map((range) => {
        const matching =
          recentPerformance.filter(
            (item) => {
              if (
                item.confidence === null ||
                item.confidence === undefined
              ) {
                return false;
              }

              return (
                item.confidence >= range.min &&
                item.confidence <= range.max
              );
            }
          );


        const accuracy =
          matching.length > 0
            ? matching.reduce(
                (total, item) =>
                  total +
                  (item.accuracy ?? 0),
                0
              ) /
              matching.length
            : 0;


        return {
          range: range.label,
          signals: matching.length,
          accuracy: roundNumber(
            accuracy
          ),
        };
      });
    }, [recentPerformance]);


  // ------------------------------------------------------------
  // ACCURACY TREND
  // ------------------------------------------------------------

  const trendData =
    useMemo<TrendItem[]>(() => {
      const grouped =
        new Map<
          string,
          {
            accuracyTotal: number;
            signals: number;
          }
        >();


      const filteredByPeriod =
        filterRecentByPeriod(
          recentPerformance,
          period
        );


      for (const item of filteredByPeriod) {
        const date =
          new Date(
            item.recorded_at
          );

        const key =
          getDateKey(date);


        const existing =
          grouped.get(key) ?? {
            accuracyTotal: 0,
            signals: 0,
          };


        existing.accuracyTotal +=
          item.accuracy ?? 0;

        existing.signals += 1;

        grouped.set(
          key,
          existing
        );
      }


      const sorted =
        [...grouped.entries()]
          .sort(
            ([a], [b]) =>
              a.localeCompare(b)
          );


      if (sorted.length === 0) {
        return [];
      }


      return sorted.map(
        ([dateKey, value]) => ({
          day:
            formatTrendDate(
              dateKey
            ),

          accuracy:
            roundNumber(
              value.accuracyTotal /
                value.signals
            ),

          signals:
            value.signals,
        })
      );
    }, [
      recentPerformance,
      period,
    ]);


  // ------------------------------------------------------------
  // DISPLAY TREND
  // ------------------------------------------------------------

  const displayTrend =
    useMemo(() => {
      if (trendData.length <= 7) {
        return trendData;
      }

      return trendData.slice(
        trendData.length - 7
      );
    }, [trendData]);


  // ------------------------------------------------------------
  // SUMMARY VALUES
  // ------------------------------------------------------------

  const overallAccuracy =
    overview?.prediction_accuracy ?? 0;

  const successfulSignals =
    overview?.successful_signals ?? 0;

  const failedSignals =
    overview?.failed_signals ?? 0;

  const evaluatedSignals =
    overview?.total_completed_signals ?? 0;

  const correctPredictions =
    overview?.correct_predictions ?? 0;

  const incorrectPredictions =
    overview?.incorrect_predictions ?? 0;

  const totalPredictions =
    overview?.total_predictions ?? 0;


  // ------------------------------------------------------------
  // LOADING STATE
  // ------------------------------------------------------------

  if (isLoading) {
    return (
      <AdminShell>
        <div className="performance-page">
          <div className="performance-page-header">
            <div>
              <div className="performance-breadcrumb">
                Intelligence / Performance
              </div>

              <h1>Performance</h1>

              <p>
                Monitor signal accuracy, outcomes, and
                model performance over time.
              </p>
            </div>
          </div>

          <div className="performance-card">
            <div
              style={{
                minHeight: "320px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexDirection: "column",
                gap: "14px",
              }}
            >
              <div
                style={{
                  width: "34px",
                  height: "34px",
                  borderRadius: "50%",
                  border:
                    "3px solid rgba(34, 158, 217, 0.18)",
                  borderTopColor:
                    "#229ed9",
                  animation:
                    "performanceSpin 0.8s linear infinite",
                }}
              />

              <strong>
                Loading performance data...
              </strong>

              <span
                style={{
                  color: "#7c8795",
                  fontSize: "13px",
                }}
              >
                Fetching the latest evaluation metrics.
              </span>
            </div>
          </div>

          <style jsx>{`
            @keyframes performanceSpin {
              to {
                transform: rotate(360deg);
              }
            }
          `}</style>
        </div>
      </AdminShell>
    );
  }


  // ------------------------------------------------------------
  // ERROR STATE
  // ------------------------------------------------------------

  if (errorMessage) {
    return (
      <AdminShell>
        <div className="performance-page">

          <div className="performance-page-header">
            <div>
              <div className="performance-breadcrumb">
                Intelligence / Performance
              </div>

              <h1>Performance</h1>

              <p>
                Monitor signal accuracy, outcomes, and
                model performance over time.
              </p>
            </div>
          </div>


          <div className="performance-card">
            <div
              style={{
                padding: "60px 30px",
                textAlign: "center",
              }}
            >
              <div
                style={{
                  width: "54px",
                  height: "54px",
                  borderRadius: "50%",
                  margin: "0 auto 16px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background:
                    "rgba(239, 68, 68, 0.10)",
                  color: "#ef4444",
                  fontSize: "24px",
                  fontWeight: 700,
                }}
              >
                !
              </div>

              <h2
                style={{
                  marginBottom: "8px",
                }}
              >
                Unable to load performance
              </h2>

              <p
                style={{
                  color: "#7c8795",
                  marginBottom: "20px",
                }}
              >
                {errorMessage}
              </p>

              <button
                className="performance-view-button"
                onClick={() =>
                  window.location.reload()
                }
              >
                Try Again
              </button>
            </div>
          </div>

        </div>
      </AdminShell>
    );
  }


  return (
    <AdminShell>
      <div className="performance-page">

        {/* HEADER */}
        <div className="performance-page-header">
          <div>
            <div className="performance-breadcrumb">
              Intelligence / Performance
            </div>

            <h1>Performance</h1>

            <p>
              Monitor signal accuracy, outcomes, and model
              performance over time.
            </p>
          </div>

          <div className="performance-header-actions">

            <select
              className="performance-period-select"
              value={period}
              onChange={(e) =>
                setPeriod(e.target.value)
              }
            >
              <option>7 Days</option>
              <option>30 Days</option>
              <option>90 Days</option>
              <option>All Time</option>
            </select>

            <button
              className="performance-export-button"
              onClick={() =>
                exportPerformance(
                  filteredSignals
                )
              }
            >
              ↓ Export
            </button>

          </div>
        </div>


        {/* SUMMARY */}
        <div className="performance-stats-grid">

          <PerformanceStat
            label="Overall Accuracy"
            value={`${formatNumber(
              overallAccuracy
            )}%`}
            description="Observed prediction accuracy"
            icon="◎"
            type="blue"
            positive
          />

          <PerformanceStat
            label="Successful Signals"
            value={String(
              successfulSignals
            )}
            description={`${formatPercentage(
              overview?.success_rate
            )}% of evaluated signals`}
            icon="✓"
            type="green"
          />

          <PerformanceStat
            label="Failed Signals"
            value={String(
              failedSignals
            )}
            description={`${formatFailurePercentage(
              overview?.success_rate
            )}% of evaluated signals`}
            icon="!"
            type="red"
          />

          <PerformanceStat
            label="Signals Evaluated"
            value={String(
              evaluatedSignals
            )}
            description="Across completed signals"
            icon="◉"
            type="purple"
          />

        </div>


        {/* MAIN ANALYTICS */}
        <div className="performance-main-grid">

          {/* TREND */}
          <div className="performance-card performance-trend-card">

            <div className="performance-card-header">

              <div>
                <h2>Accuracy Trend</h2>

                <p>
                  Observed prediction accuracy over the selected
                  period.
                </p>
              </div>

              <div className="performance-legend">
                <span>
                  <i />
                  Accuracy
                </span>
              </div>

            </div>


            <div className="performance-chart">

              <div className="performance-y-axis">
                <span>100%</span>
                <span>80%</span>
                <span>60%</span>
                <span>40%</span>
                <span>20%</span>
                <span>0%</span>
              </div>


              <div className="performance-chart-area">

                <div className="performance-grid-lines">
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                </div>


                <svg
                  className="performance-line-chart"
                  viewBox="0 0 700 280"
                  preserveAspectRatio="none"
                >

                  {buildTrendPoints(
                    displayTrend
                  ).length > 0 && (
                    <>
                      <polyline
                        points={buildTrendPoints(
                          displayTrend
                        )}
                        fill="none"
                        stroke="#229ed9"
                        strokeWidth="4"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />

                      {buildTrendCoordinates(
                        displayTrend
                      ).map(
                        ([cx, cy], index) => (
                          <circle
                            key={index}
                            cx={cx}
                            cy={cy}
                            r="5"
                            fill="#ffffff"
                            stroke="#229ed9"
                            strokeWidth="3"
                          />
                        )
                      )}
                    </>
                  )}

                </svg>


                <div className="performance-chart-labels">

                  {displayTrend.length > 0 ? (
                    displayTrend.map(
                      (item, index) => (
                        <span
                          key={`${item.day}-${index}`}
                        >
                          {item.day}
                        </span>
                      )
                    )
                  ) : (
                    <span>
                      No trend data
                    </span>
                  )}

                </div>

              </div>

            </div>

          </div>


          {/* PERIOD SUMMARY */}
          <div className="performance-card performance-period-card">

            <div className="performance-card-header">

              <div>
                <h2>Period Summary</h2>

                <p>
                  Current evaluation period.
                </p>
              </div>

              <div className="performance-summary-icon">
                ◈
              </div>

            </div>


            <div className="performance-summary-body">

              <div className="performance-big-number">
                {formatNumber(
                  overallAccuracy
                )}%
              </div>

              <span className="performance-summary-label">
                Observed accuracy
              </span>


              <div className="performance-progress">
                <span
                  style={{
                    width: `${clampPercentage(
                      overallAccuracy
                    )}%`,
                  }}
                />
              </div>


              <div className="performance-summary-row">
                <span>
                  Correct predictions
                </span>

                <strong>
                  {correctPredictions}
                </strong>
              </div>


              <div className="performance-summary-row">
                <span>
                  Incorrect predictions
                </span>

                <strong>
                  {incorrectPredictions}
                </strong>
              </div>


              <div className="performance-summary-row">
                <span>
                  Total predictions
                </span>

                <strong>
                  {totalPredictions}
                </strong>
              </div>


              <div className="performance-summary-row">
                <span>
                  Signals evaluated
                </span>

                <strong>
                  {evaluatedSignals}
                </strong>
              </div>

            </div>

          </div>

        </div>


        {/* BREAKDOWN */}
        <div className="performance-breakdown-grid">

          {/* MINE COUNT */}
          <div className="performance-card">

            <div className="performance-card-header">

              <div>
                <h2>
                  Performance by Mine Count
                </h2>

                <p>
                  Observed accuracy grouped by board
                  configuration.
                </p>
              </div>

            </div>


            <div className="performance-breakdown-list">

              {minePerformance.length > 0 ? (
                minePerformance.map(
                  (item) => (
                    <div
                      className="performance-breakdown-item"
                      key={item.mines}
                    >

                      <div className="performance-breakdown-top">

                        <div>
                          <strong>
                            {item.mines}
                          </strong>

                          <span>
                            {item.signals} signals
                          </span>
                        </div>

                        <strong className="performance-breakdown-value">
                          {formatNumber(
                            item.accuracy
                          )}%
                        </strong>

                      </div>


                      <div className="performance-bar">
                        <span
                          style={{
                            width: `${clampPercentage(
                              item.accuracy
                            )}%`,
                          }}
                        />
                      </div>


                      <div className="performance-breakdown-footer">

                        <span>
                          {item.success} successful
                        </span>

                        <span>
                          {Math.max(
                            item.signals -
                              item.success,
                            0
                          )} failed
                        </span>

                      </div>

                    </div>
                  )
                )
              ) : (
                <div className="performance-empty">
                  <div>◉</div>

                  <strong>
                    No board performance data
                  </strong>

                  <span>
                    Completed results will appear here.
                  </span>
                </div>
              )}

            </div>

          </div>


          {/* CONFIDENCE */}
          <div className="performance-card">

            <div className="performance-card-header">

              <div>
                <h2>
                  Performance by Confidence
                </h2>

                <p>
                  Compare observed outcomes against model
                  confidence ranges.
                </p>
              </div>

            </div>


            <div className="performance-confidence-list">

              {confidencePerformance.map(
                (item) => (
                  <div
                    className="performance-confidence-row"
                    key={item.range}
                  >

                    <div className="performance-confidence-label">

                      <strong>
                        {item.range}
                      </strong>

                      <span>
                        {item.signals} signals
                      </span>

                    </div>


                    <div className="performance-confidence-bar">

                      <span
                        style={{
                          width: `${clampPercentage(
                            item.accuracy
                          )}%`,
                        }}
                      />

                    </div>


                    <strong className="performance-confidence-value">
                      {formatNumber(
                        item.accuracy
                      )}%
                    </strong>

                  </div>
                )
              )}

            </div>

          </div>

        </div>


        {/* RECENT PERFORMANCE */}
        <div className="performance-card performance-recent-card">

          <div className="performance-card-header performance-recent-header">

            <div>
              <h2>
                Recent Performance
              </h2>

              <p>
                Latest evaluated signals and their observed
                outcomes.
              </p>
            </div>

            <button
              className="performance-view-button"
              onClick={() => {
                window.location.href =
                  "/signal-results";
              }}
            >
              View Results
            </button>

          </div>


          {/* FILTERS */}
          <div className="performance-filters">

            <div className="performance-search">

              <span>⌕</span>

              <input
                type="text"
                placeholder="Search signal..."
                value={search}
                onChange={(e) =>
                  setSearch(e.target.value)
                }
              />

            </div>


            <select
              className="performance-filter-select"
              value={mineFilter}
              onChange={(e) =>
                setMineFilter(e.target.value)
              }
            >
              <option>
                All Mines
              </option>

              <option value="3">
                3 Mines
              </option>

              <option value="5">
                5 Mines
              </option>

              <option value="7">
                7 Mines
              </option>
            </select>


            <button
              className="performance-reset-button"
              onClick={() => {
                setSearch("");
                setMineFilter(
                  "All Mines"
                );
              }}
            >
              Reset
            </button>

          </div>


          {/* DESKTOP TABLE */}
          <div className="performance-table-wrapper">

            <table className="performance-table">

              <thead>
                <tr>
                  <th>Signal</th>
                  <th>Mines</th>
                  <th>Confidence</th>
                  <th>Correct</th>
                  <th>Incorrect</th>
                  <th>Accuracy</th>
                  <th>Attempts</th>
                  <th>Result</th>
                  <th>Completed</th>
                </tr>
              </thead>


              <tbody>

                {filteredSignals.map(
                  (signal) => (
                    <tr key={signal.id}>

                      <td>
                        <span className="performance-signal">
                          {signal.signalNumber}
                        </span>
                      </td>


                      <td>
                        <span className="performance-mine-pill">
                          {signal.mineCount}
                        </span>
                      </td>


                      <td>
                        <span className="performance-confidence">
                          {formatConfidence(
                            signal.confidence
                          )}
                        </span>
                      </td>


                      <td>
                        <span className="performance-correct">
                          {signal.correct}
                        </span>
                      </td>


                      <td>
                        <span className="performance-incorrect">
                          {signal.incorrect}
                        </span>
                      </td>


                      <td>

                        <div className="performance-table-accuracy">

                          <div>
                            <span
                              style={{
                                width: `${clampPercentage(
                                  signal.accuracy
                                )}%`,
                              }}
                            />
                          </div>

                          <strong>
                            {formatNumber(
                              signal.accuracy
                            )}%
                          </strong>

                        </div>

                      </td>


                      <td>
                        <span className="performance-attempts">
                          {formatAttempts(
                            signal.attempts
                          )}
                        </span>
                      </td>


                      <td>
                        <PerformanceResultBadge
                          result={
                            signal.result
                          }
                        />
                      </td>


                      <td>
                        <span className="performance-date">
                          {signal.completedAt}
                        </span>
                      </td>

                    </tr>
                  )
                )}

              </tbody>

            </table>


            {filteredSignals.length === 0 && (
              <div className="performance-empty">

                <div>⌕</div>

                <strong>
                  No performance records found
                </strong>

                <span>
                  Try changing your search or filter.
                </span>

              </div>
            )}

          </div>


          {/* MOBILE */}
          <div className="performance-mobile-list">

            {filteredSignals.map(
              (signal) => (
                <div
                  className="performance-mobile-item"
                  key={signal.id}
                >

                  <div className="performance-mobile-top">

                    <div>

                      <strong>
                        {signal.signalNumber}
                      </strong>

                      <span>
                        {signal.mineCount} mines ·{" "}
                        {formatAttempts(
                          signal.attempts
                        )} attempts
                      </span>

                    </div>

                    <PerformanceResultBadge
                      result={
                        signal.result
                      }
                    />

                  </div>


                  <div className="performance-mobile-grid">

                    <div>
                      <span>
                        Confidence
                      </span>

                      <strong>
                        {formatConfidence(
                          signal.confidence
                        )}
                      </strong>
                    </div>


                    <div>
                      <span>
                        Correct
                      </span>

                      <strong className="mobile-green">
                        {signal.correct}
                      </strong>
                    </div>


                    <div>
                      <span>
                        Incorrect
                      </span>

                      <strong className="mobile-red">
                        {signal.incorrect}
                      </strong>
                    </div>


                    <div>
                      <span>
                        Accuracy
                      </span>

                      <strong>
                        {formatNumber(
                          signal.accuracy
                        )}%
                      </strong>
                    </div>

                  </div>


                  <div className="performance-mobile-progress">

                    <span
                      style={{
                        width: `${clampPercentage(
                          signal.accuracy
                        )}%`,
                      }}
                    />

                  </div>


                  <div className="performance-mobile-date">
                    {signal.completedAt}
                  </div>

                </div>
              )
            )}

          </div>


          {/* PAGINATION */}
          <div className="performance-pagination">

            <span>
              Showing {filteredSignals.length} of{" "}
              {performanceSignals.length} signals
            </span>

            <div>
              <button disabled>
                Previous
              </button>

              <button className="active">
                1
              </button>

              <button disabled>
                2
              </button>

              <button disabled>
                3
              </button>

              <button disabled>
                Next
              </button>
            </div>

          </div>

        </div>

      </div>
    </AdminShell>
  );
}


/* =========================================================
   STAT
========================================================= */

function PerformanceStat({
  label,
  value,
  description,
  icon,
  type,
  positive,
}: {
  label: string;
  value: string;
  description: string;
  icon: string;
  type:
    | "blue"
    | "green"
    | "red"
    | "purple";
  positive?: boolean;
}) {
  return (
    <div className="performance-stat-card">

      <div
        className={`performance-stat-icon ${type}`}
      >
        {icon}
      </div>

      <div className="performance-stat-content">

        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>

        <small
          className={
            positive
              ? "positive"
              : ""
          }
        >
          {description}
        </small>

      </div>

    </div>
  );
}


/* =========================================================
   RESULT BADGE
========================================================= */

function PerformanceResultBadge({
  result,
}: {
  result: PerformanceResult;
}) {
  return (
    <span
      className={`performance-result-badge ${result.toLowerCase()}`}
    >
      <span />

      {result}
    </span>
  );
}


/* =========================================================
   HELPERS
========================================================= */

function roundNumber(
  value: number
): number {
  return Math.round(
    value * 100
  ) / 100;
}


function formatNumber(
  value: number
): string {
  return roundNumber(
    value
  ).toString();
}


function clampPercentage(
  value: number
): number {
  if (!Number.isFinite(value)) {
    return 0;
  }

  return Math.max(
    0,
    Math.min(
      100,
      value
    )
  );
}


function formatConfidence(
  confidence: number | null
): string {
  if (
    confidence === null ||
    confidence === undefined
  ) {
    return "—";
  }

  return `${formatNumber(
    confidence
  )}%`;
}


function formatAttempts(
  attempts: number | null
): string {
  if (
    attempts === null ||
    attempts === undefined
  ) {
    return "—";
  }

  return String(
    attempts
  );
}


function formatPercentage(
  value: number | null | undefined
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "0";
  }

  return formatNumber(
    value
  );
}


function formatFailurePercentage(
  successRate:
    | number
    | null
    | undefined
): string {
  if (
    successRate === null ||
    successRate === undefined
  ) {
    return "0";
  }

  return formatNumber(
    Math.max(
      0,
      100 - successRate
    )
  );
}


/* =========================================================
   SIGNAL NUMBER
========================================================= */

function formatSignalNumber(
  signalId: string
): string {
  const compact =
    signalId
      .replace(/-/g, "")
      .slice(0, 6)
      .toUpperCase();

  return `SIG-${compact}`;
}


/* =========================================================
   DATE FORMATTING
========================================================= */

function formatDateTime(
  value: string
): string {
  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return date.toLocaleString(
    undefined,
    {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }
  );
}


function getDateKey(
  date: Date
): string {
  const year =
    date.getFullYear();

  const month =
    String(
      date.getMonth() + 1
    ).padStart(2, "0");

  const day =
    String(
      date.getDate()
    ).padStart(2, "0");

  return `${year}-${month}-${day}`;
}


function formatTrendDate(
  dateKey: string
): string {
  const date =
    new Date(
      `${dateKey}T00:00:00`
    );

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return dateKey;
  }

  return date.toLocaleDateString(
    undefined,
    {
      weekday: "short",
    }
  );
}


/* =========================================================
   PERIOD FILTER
========================================================= */

function filterRecentByPeriod(
  records: PerformanceRecent[],
  period: string
): PerformanceRecent[] {
  if (
    period === "All Time"
  ) {
    return records;
  }

  const now =
    new Date();

  const days =
    period === "30 Days"
      ? 30
      : period === "90 Days"
        ? 90
        : 7;

  const cutoff =
    new Date(now);

  cutoff.setDate(
    cutoff.getDate() -
      (days - 1)
  );

  return records.filter(
    (item) => {
      const date =
        new Date(
          item.recorded_at
        );

      return (
        !Number.isNaN(
          date.getTime()
        ) &&
        date >= cutoff
      );
    }
  );
}


/* =========================================================
   TREND CHART
========================================================= */

function buildTrendCoordinates(
  data: TrendItem[]
): Array<
  [number, number]
> {
  if (
    data.length === 0
  ) {
    return [];
  }

  const left = 15;
  const right = 680;

  const top = 20;
  const bottom = 250;

  const usableWidth =
    right - left;

  const usableHeight =
    bottom - top;

  return data.map(
    (item, index) => {
      const x =
        data.length === 1
          ? left
          : left +
            (
              index /
              (data.length - 1)
            ) *
              usableWidth;

      const accuracy =
        clampPercentage(
          item.accuracy
        );

      const y =
        bottom -
        (
          accuracy /
          100
        ) *
          usableHeight;

      return [
        Number(
          x.toFixed(2)
        ),
        Number(
          y.toFixed(2)
        ),
      ];
    }
  );
}


function buildTrendPoints(
  data: TrendItem[]
): string {
  return buildTrendCoordinates(
    data
  )
    .map(
      ([x, y]) =>
        `${x},${y}`
    )
    .join(" ");
}


/* =========================================================
   CSV EXPORT
========================================================= */

function exportPerformance(
  records: PerformanceSignal[]
): void {
  if (
    records.length === 0
  ) {
    return;
  }

  const header = [
    "Signal",
    "Mines",
    "Confidence",
    "Correct",
    "Incorrect",
    "Accuracy",
    "Attempts",
    "Result",
    "Completed",
  ];


  const rows =
    records.map(
      (record) => [
        record.signalNumber,
        record.mineCount,
        record.confidence ??
          "",
        record.correct,
        record.incorrect,
        record.accuracy,
        record.attempts ??
          "",
        record.result,
        record.completedAt,
      ]
    );


  const csv = [
    header,
    ...rows,
  ]
    .map(
      (row) =>
        row
          .map(
            (value) =>
              `"${String(
                value
              ).replace(
                /"/g,
                '""'
              )}"`
          )
          .join(",")
    )
    .join("\n");


  const blob =
    new Blob(
      [csv],
      {
        type:
          "text/csv;charset=utf-8;",
      }
    );


  const url =
    URL.createObjectURL(
      blob
    );


  const link =
    document.createElement(
      "a"
    );

  link.href = url;

  link.download =
    `performance-${new Date()
      .toISOString()
      .slice(0, 10)}.csv`;

  document.body.appendChild(
    link
  );

  link.click();

  document.body.removeChild(
    link
  );

  URL.revokeObjectURL(
    url
  );
} 
