---
status: accepted
---

# Concentrate Financial figure policy in one shared module

Date: 2026-09-08. Accepted during architecture exploration; implemented and verified in the [architecture audit](../audits/2026-09-08-architecture/README.md).

One shared module will own evidence selection, comparison eligibility, calculations, partial results, refusal reasons and Korean/English financial wording. The application and future benchmarks will use its interface. Model execution, database access and visual formatting remain outside its implementation. This concentrates policy knowledge and tests at one seam instead of constructing a benchmark answer and then revising its policy in application code.

Preserve current verified behavior and coverage during extraction; expansion of companies, metrics and question types is separate work. Historical benchmark results and archived harness source remain unchanged. Verify the extracted implementation against existing financial-answer cases, and document and test any discovered defect correction separately from behavior-preserving moves. This follows ADR 0005's deterministic financial policy and ADR 0006's explicit allowance for a later domain extraction.
