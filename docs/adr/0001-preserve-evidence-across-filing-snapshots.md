# Preserve saved evidence across filing snapshots

Owner-approved in design interview round 6: the first release answers live questions against a fixed, verified filing snapshot, and saved investigations retain their original answers, citations, and source/catalog version until deleted. An explicit rerun creates a new result; validated source updates may change new answers but never silently rewrite saved ones, preserving the evidence a reader originally relied on at the cost of maintaining historical result provenance and showing source freshness explicitly.

New comparisons use the latest verified, comparable figures within the supported snapshot, with restatements labeled only when established by evidence. A newer filing date alone does not establish comparability or restatement; uncertain calculations are withheld. Storage design must support retained evidence versions and deletion together, and distinguish real-time execution from automatically current filing coverage.
