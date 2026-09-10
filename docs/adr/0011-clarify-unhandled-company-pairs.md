# Clarify company pairs outside verified coverage

Date: 2026-09-10.

The intent model can return only supported company identifiers. A request naming
one supported company and one unsupported company could therefore lose the
unsupported name and become a valid single-company report. For example,
“Compare Samsung and Tesla revenue in 2023” could become a Samsung report.

The question guard now removes supported aliases and the bounded request grammar
from the reader's whole question. Meaningful residual text, including an
unsupported company name or an unsupported qualifier such as a business segment,
makes the company selection unresolved. Deterministic Financial figure policy then
asks for a supported company instead of answering a narrower question. This check
applies independently of the model's selected action or company.

Pairs made entirely of supported aliases continue to policy resolution. Direct
corrections between supported companies, basis corrections, single-company
aliases (including Samsung Electronics), and bounded company-free follow-ups keep
their existing behavior. Basis corrections are removed before company correction
and residual-scope checks so their negation cannot erase the named company. This
is a conservative guard for bounded financial requests, not general-purpose
named-entity recognition; expanding company or request coverage remains separate
work.
