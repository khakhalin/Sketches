# Agent-based modeling

Some experiments on agent-based modeling in Python. Mostly figuring best ways to do it in practice.

## Speed

Model with 500 bots, capped at 500 bots, running for 10 iterations:

| Variant                                                      | Time, s | Comments                                                     |
| ------------------------------------------------------------ | ------- | ------------------------------------------------------------ |
| Basic                                                        | 7.55    |                                                              |
| No agent vizualization                                       | 7.40    |                                                              |
| No canvas updates at all                                     | 6.88    | 9% of time                                                   |
| No feeding                                                   | 7.12    | 6% of time                                                   |
| No procreation                                               | 1.07    | 86% of time spent in procreation. Obviously a bottleneck. Zooming deeper. |
| Use `np.linalg.norm()` instead of calling a function that calls `np.linalg.norm()` inside it | 7.22    | 5% saved. Hmm. Strangely high cost just for calling a method from a class |
| One large if instead of nested ifs                           | 7.19    | Less than a % difference, so doesn't matter                  |
| Inherit position from one of the parents instead of a mean of both | 7.16    | 1% only                                                      |
| All reproduction-related checks, but no actual appending bots to the bot vector | 7.12    | 1% only                                                      |
| Distance check removed at all                                | 1.23    | 83%. OK, this is clearly the culprit.                        |
| Manhattan distance as an external method: `sum(abs(xy1-xy2))` | 4.38    | 40% saved                                                    |
| Manhattan distance in place                                  | 4.10    | 3% saved                                                     |
| Eucledian distances without `sqrt`, but calculated once per cycle (distance matrix, 3 lines of numpy) | 1.78    | 76% saving                                                   |

Conclusion: the best way to speed up the model is to part a bit with pure object-oriented approach, and replace it with a "global" (at least within the parental collection object) distance matrix. Essentially, we seem to have a clash of philosophies here. To make Python code fast, we need to run it Matlab-style, with as few rows of code (and calls to numpy) as possible. But it means working with smelly global variables, that need to stay synchronized with each other somehow.