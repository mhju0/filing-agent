# Filing Agent

Language for investigating company disclosures through Korean and English conversations.

## Language

**Filing reader**:
An individual who investigates company disclosures through questions, follow-ups, and direct inspection of the evidence.

**Financial figure**:
A displayed financial value associated with a company, metric, and fiscal period. A reported figure represents a Financial Fact; a derived figure is calculated from reported facts and retains its operands' sources.

**Financial Fact**:
A reported metric value normalized by Filing Digest from a Corporate Filing, with its period, currency, and scale. Its presence in Digest does not alone establish Agent's stronger source-verification or comparison eligibility requirements.

**Corporate Filing**:
An official company disclosure in a regulatory filing system, following Filing Digest's domain terminology. It is distinct from a conversation, citation, or collection of filings.

**Filing Identity**:
A regulator and that regulator's stable filing identifier, following Filing Digest's terminology. A local database UUID identifies a stored record and is not a substitute for this identity across corpus rebuilds.

**Original-filing source**:
The original company disclosure underlying a financial figure or source excerpt, reachable through a link to that specific filing. A company homepage or an internal identifier alone is not an original-filing source link.

**Source excerpt**:
Text reproduced from a filing in its original language. A translation is a separately labeled rendering of that excerpt.

**Citation**:
A reference from an answer claim to a filing excerpt and its source identity. Resolving that reference does not by itself establish that the excerpt supports the claim.

**Annual comparison**:
A comparison of the same company's financial metric across fiscal years, with the periods and units identified. Absolute and percentage changes are derived figures whose validity depends on comparable underlying reported figures.

**Coverage**:
The company, metric, and fiscal-period combinations supported by the available filing evidence. A company's presence alone does not establish coverage for every metric or year.

**Source catalog**:
A versioned collection associating exact filing identities with original-filing source metadata for a particular corpus snapshot.
_Avoid_: Source manifest (use source catalog in product and planning language).

**Replay investigation**:
A recorded sequence of filing questions, results, and evidence that a reader can explore without making live model or filing requests.

**Saved investigation**:
A private filing conversation the reader explicitly retains until deletion, including its original answers, citations, and source version. Reopening preserves those results; a rerun is a new result.

**Filing snapshot**:
A fixed, versioned collection of filings and verified evidence defining the available coverage at a particular release. Its source dates describe the collection's freshness independently of when a question is answered.

**Live investigation**:
A conversation in the owner’s local application whose questions trigger real model and tool execution against the supported filing snapshot. Live execution does not imply automatic access to newly published filings.
