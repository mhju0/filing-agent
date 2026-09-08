# Conversation evaluation

`cases.json` fixes 120 bilingual scenarios: 80 development scenarios and 40 scenarios held out from execution. Each of 20 task families has three Korean and three English phrasings. Two phrasings per language are development material; the third is held out. The held-out set shares companies, metrics and task families with development, so it measures bounded paraphrase generalization, not unseen accounting tasks or arbitrary Korean language quality. The same implementing agent authored the scenarios; this is not independent human evaluation.

Multi-turn cases use the real API and its persisted context. The runner never sends expected values to the application. Expected company, metric, year, outcome and exact source-bound values are stored separately. Three trials use the fixed qualified model configuration; deterministic repetitions are not independent samples.

```sh
.venv/bin/python -m evals.run --split dev --trials 1 --output evals/results/dev-new.json
.venv/bin/python -m evals.run --split heldout --trials 3 --output evals/results/heldout-new.json
```

Run the local application and Ollama first. The runner creates isolated investigations in the Agent database and deletes them after retaining the result. It explicitly opts into diagnostic capture for reproducibility. Never use a prior output path: failures and partial experiments remain evidence.

The release threshold is at least 95% correct final task outcomes for **each language in each held-out trial**, plus all deterministic source/value/local-isolation invariants. Report useful answers and correct withheld/clarification outcomes separately. A fabricated financial amount blocks release regardless of aggregate accuracy. Exact final outcomes alone do not prove that every intermediate explanation, long conversation, operating system or failure condition is correct; separate contract and browser tests cover those boundaries.
