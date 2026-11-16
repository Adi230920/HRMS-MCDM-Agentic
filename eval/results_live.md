### TABLE 1 (cases A_inflator, B_humble, C_split only)

| Case | Expected | Single LLM | Majority vote of initial agent votes | Council |
| :--- | :--- | :--- | :--- | :--- |
| A_inflator | DO_NOT_ADVANCE | DO_NOT_ADVANCE | DO_NOT_ADVANCE | DO_NOT_ADVANCE |
| B_humble | ADVANCE | ADVANCE | ADVANCE | REVIEW |
| C_split | REVIEW | DO_NOT_ADVANCE | DO_NOT_ADVANCE | DO_NOT_ADVANCE |
| Correct | 3 | 2 | 2 | 1 |

### TABLE 2 (all finished cases)

| Case | Expected | Council | Score | Agreement rate | Debate argued | Veto | LLM calls | Duration seconds |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| A_inflator | DO_NOT_ADVANCE | DO_NOT_ADVANCE | 0.094 | 1.00 | True | True | 9 | 77.75 |
| B_humble | ADVANCE | REVIEW | 0.800 | 1.00 | True | False | 7 | 69.61 |
| C_split | REVIEW | DO_NOT_ADVANCE | 0.125 | 1.00 | True | True | 9 | 94.40 |
| D_subtle_perf_lie | DO_NOT_ADVANCE | DO_NOT_ADVANCE | 0.000 | 1.00 | True | True | 8 | 37.73 |
| E_subtle_scale_lie | DO_NOT_ADVANCE | DO_NOT_ADVANCE | 0.094 | 1.00 | True | True | 8 | 45.39 |
| F_all_strong | ADVANCE | REVIEW | 0.806 | 1.00 | True | False | 10 | 84.18 |

### TABLE 3 (providers)

| Role | Provider and Model Actually Used | Number of Fallbacks | Number of 429 or Empty Replies | Average Latency (s) |
| :--- | :--- | :--- | :--- | :--- |
| extractor | groq:qwen/qwen3.8-27b | 0 | 0 | 0.80 |
| technical | gemini:gemini-3.5-flash-lite | 0 | 0 | 5.16 |
| delivery | groq:openai/gpt-oss-120b | 0 | 0 | 3.70 |
| collaboration | gemini:gemini-3.5-flash-lite, openrouter:openrouter/free | 5 | 5 | 22.19 |
| moderator | gemini:gemini-3.5-flash-lite | 0 | 0 | 1.88 |
| chair | groq:openai/gpt-oss-120b | 0 | 0 | 2.25 |

total cases finished: 6
council correct count: 3
baseline correct count: 5
total LLM calls: 51
average duration per run: 68.18s
