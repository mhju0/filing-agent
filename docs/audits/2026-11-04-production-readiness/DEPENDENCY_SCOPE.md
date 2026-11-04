# Dependency coverage follow-up · 2026-11-04

[Verified] The final repository-wide manifest pass found the same two vulnerable development packages in the retained `design/alternatives` studies. The earlier audit covered the live application and verification toolchain; their zero-advisory results remain accurate. This follow-up closes the separate archived-study workspace without editing dated reports or redesigning the studies.

[Verified] Updated only Vite 8.2.2 → 8.2.4 and source-map-js 1.2.1 → 1.2.2. `npm audit` failed before the patch with two high-severity package entries and reports zero after it. Both Node 24.22.2 production builds pass. All nine emitted HTML/JS/CSS/font files are byte-identical before and after the security patches. The archived browser/screenshot harness was not rerun because output bytes are identical and its default writes would replace historical verification artifacts.

[Verified] Final known-advisory results are zero for all three npm lockfiles: `slice/web`, `verification` and `design/alternatives`. The qualified Python runtime lockfile also reports zero. A fresh resolution/audit of `bench/requirements.txt` reports zero; that permissive requirements file is not represented as a lockfile or as proof that every older version it permits is safe.

[Verified] The archived studies are not live deployment inputs and are excluded from the downloadable application's explicit source allowlist. The 27-file production artifact, runtime/UI source and verified production release remain unchanged. No second deployment is needed for this tooling-only follow-up.

[Verified] [Machine-readable audit and all nine build hashes](dependency-followup.json) accompany this record. Earlier [findings](README.md) and [production verification](DEPLOYMENT.md) retain their exact scope and dates.
