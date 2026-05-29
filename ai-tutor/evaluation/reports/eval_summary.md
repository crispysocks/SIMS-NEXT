# RAG Evaluation Summary

**Dataset**: 34 cases

## Aggregate Metrics

| Pipeline | Diagnosis | Retrieval | Remediation | LLM Success | Fallback | Avg Latency |
|----------|-----------|-----------|-------------|-------------|----------|-------------|
| deterministic | 94%       | 94%       | 96%         | 0%          | 0%       | 1ms         |
| tfidf         | 94%       | 94%       | 96%         | 0%          | 100%     | 1ms         |
| hybrid        | 94%       | 94%       | 96%         | 0%          | 100%     | 1ms         |
| full_rag      | 94%       | 94%       | 96%         | 0%          | 100%     | 6326ms      |

## Per-Case Breakdown

### deterministic

| # | Topic | Student | Correct | Diagnosis | Labels | Retrieval | Remediation | Source | Latency |
|---|-------|---------|---------|-----------|--------|-----------|-------------|--------|---------|
|  0 | verb_tense            | go              | went            | ✓         | base_form_instead_of_past      | ✓         | 2/2         | —                    | 1ms     |
|  1 | verb_tense            | play            | played          | ✓         | base_form_instead_of_past      | ✓         | 1/1         | —                    | 1ms     |
|  2 | verb_tense            | eated           | ate             | ✓         | wrong_past_form                | ✓         | 1/1         | —                    | 1ms     |
|  3 | verb_tense            | runned          | ran             | ✓         | wrong_past_form                | ✓         | 1/1         | —                    | 1ms     |
|  4 | verb_tense            | studied         | had been studyi | ✓         | wrong_past_form                | ✓         | 1/1         | —                    | 1ms     |
|  5 | verb_tense            | watched         | were watching   | ✓         | wrong_past_form                | ✓         | 1/1         | —                    | 1ms     |
|  6 | subject_verb_agreeme  | go              | goes            | ✓         | missing_third_person_s         | ✓         | 2/2         | —                    | 1ms     |
|  7 | subject_verb_agreeme  | do              | does            | ✓         | missing_third_person_s         | ✓         | 2/2         | —                    | 1ms     |
|  8 | subject_verb_agreeme  | rain            | rains           | ✓         | missing_third_person_s         | ✓         | 2/2         | —                    | 1ms     |
|  9 | subject_verb_agreeme  | is              | are             | ✓         | plural_subject_error           | ✓         | 2/2         | —                    | 1ms     |
| 10 | subject_verb_agreeme  | have            | has             | ✓         | plural_subject_error           | ✓         | 2/2         | —                    | 1ms     |
| 11 | article_usage         | a               | an              | ✓         | a_vs_an_confusion              | ✓         | 2/2         | —                    | 1ms     |
| 12 | article_usage         | an              | a               | ✓         | a_vs_an_confusion              | ✓         | 2/2         | —                    | 1ms     |
| 13 | article_usage         | a               | an              | ✓         | a_vs_an_confusion              | ✓         | 2/2         | —                    | 1ms     |
| 14 | article_usage         |                 | The             | ✓         | missing_article                | ✓         | 1/1         | —                    | 1ms     |
| 15 | article_usage         | a               | the             | ✗         |                                | ✗         | 0/1         | —                    | 1ms     |
| 16 | article_usage         | the             |                 | ✗         |                                | ✗         | 0/1         | —                    | 1ms     |
| 17 | preposition_usage     | in              | on              | ✓         | wrong_preposition              | ✓         | 1/1         | —                    | 1ms     |
| 18 | preposition_usage     | on              | in              | ✓         | wrong_preposition              | ✓         | 1/1         | —                    | 1ms     |
| 19 | preposition_usage     | on              | at              | ✓         | wrong_preposition              | ✓         | 1/1         | —                    | 1ms     |
| 20 | preposition_usage     | in              | at              | ✓         | wrong_preposition              | ✓         | 1/1         | —                    | 1ms     |
| 21 | preposition_usage     | on              | in              | ✓         | wrong_preposition              | ✓         | 1/1         | —                    | 1ms     |
| 22 | sentence_correction   | She go to schoo | She went to sch | ✓         | base_form_instead_of_past, missing_third | ✓         | 3/3         | —                    | 1ms     |
| 23 | sentence_correction   | He don't likes  | He doesn't like | ✓         | missing_third_person_s         | ✓         | 2/2         | —                    | 1ms     |
| 24 | sentence_correction   | I have went to  | I have gone to  | ✓         | wrong_past_form                | ✓         | 2/2         | —                    | 1ms     |
| 25 | sentence_correction   | She is a honest | She is an hones | ✓         | a_vs_an_confusion              | ✓         | 2/2         | —                    | 1ms     |
| 26 | verb_tense            | walk            | walked          | ✓         | base_form_instead_of_past      | ✓         | 2/2         | —                    | 1ms     |
| 27 | verb_tense            | comed           | came            | ✓         | wrong_past_form                | ✓         | 1/1         | —                    | 1ms     |
| 28 | verb_tense            | singed          | sang            | ✓         | wrong_past_form                | ✓         | 1/1         | —                    | 1ms     |
| 29 | sentence_correction   | She has took my | She has taken m | ✓         | wrong_past_form                | ✓         | 2/2         | —                    | 1ms     |
| 30 | subject_verb_agreeme  | plays           | play            | ✓         | plural_subject_error           | ✓         | 2/2         | —                    | 1ms     |
| 31 | subject_verb_agreeme  | have            | has             | ✓         | plural_subject_error           | ✓         | 2/2         | —                    | 1ms     |
| 32 | sentence_correction   | They was very h | They were very  | ✓         | plural_subject_error           | ✓         | 2/2         | —                    | 1ms     |
| 33 | subject_verb_agreeme  | bark            | barks           | ✓         | missing_third_person_s         | ✓         | 2/2         | —                    | 1ms     |

### tfidf

| # | Topic | Student | Correct | Diagnosis | Labels | Retrieval | Remediation | Source | Latency |
|---|-------|---------|---------|-----------|--------|-----------|-------------|--------|---------|
|  0 | verb_tense            | go              | went            | ✓         | base_form_instead_of_past      | ✓         | 2/2         | template fallback    | 1ms     |
|  1 | verb_tense            | play            | played          | ✓         | base_form_instead_of_past      | ✓         | 1/1         | template fallback    | 1ms     |
|  2 | verb_tense            | eated           | ate             | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 1ms     |
|  3 | verb_tense            | runned          | ran             | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 1ms     |
|  4 | verb_tense            | studied         | had been studyi | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 1ms     |
|  5 | verb_tense            | watched         | were watching   | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 1ms     |
|  6 | subject_verb_agreeme  | go              | goes            | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 1ms     |
|  7 | subject_verb_agreeme  | do              | does            | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 1ms     |
|  8 | subject_verb_agreeme  | rain            | rains           | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 1ms     |
|  9 | subject_verb_agreeme  | is              | are             | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 1ms     |
| 10 | subject_verb_agreeme  | have            | has             | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 1ms     |
| 11 | article_usage         | a               | an              | ✓         | a_vs_an_confusion              | ✓         | 2/2         | template fallback    | 1ms     |
| 12 | article_usage         | an              | a               | ✓         | a_vs_an_confusion              | ✓         | 2/2         | template fallback    | 1ms     |
| 13 | article_usage         | a               | an              | ✓         | a_vs_an_confusion              | ✓         | 2/2         | template fallback    | 1ms     |
| 14 | article_usage         |                 | The             | ✓         | missing_article                | ✓         | 1/1         | template fallback    | 1ms     |
| 15 | article_usage         | a               | the             | ✗         |                                | ✗         | 0/1         | template fallback    | 1ms     |
| 16 | article_usage         | the             |                 | ✗         |                                | ✗         | 0/1         | template fallback    | 1ms     |
| 17 | preposition_usage     | in              | on              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 1ms     |
| 18 | preposition_usage     | on              | in              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 1ms     |
| 19 | preposition_usage     | on              | at              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 1ms     |
| 20 | preposition_usage     | in              | at              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 1ms     |
| 21 | preposition_usage     | on              | in              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 1ms     |
| 22 | sentence_correction   | She go to schoo | She went to sch | ✓         | base_form_instead_of_past, missing_third | ✓         | 3/3         | template fallback    | 1ms     |
| 23 | sentence_correction   | He don't likes  | He doesn't like | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 1ms     |
| 24 | sentence_correction   | I have went to  | I have gone to  | ✓         | wrong_past_form                | ✓         | 2/2         | template fallback    | 1ms     |
| 25 | sentence_correction   | She is a honest | She is an hones | ✓         | a_vs_an_confusion              | ✓         | 2/2         | template fallback    | 1ms     |
| 26 | verb_tense            | walk            | walked          | ✓         | base_form_instead_of_past      | ✓         | 2/2         | template fallback    | 1ms     |
| 27 | verb_tense            | comed           | came            | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 1ms     |
| 28 | verb_tense            | singed          | sang            | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 1ms     |
| 29 | sentence_correction   | She has took my | She has taken m | ✓         | wrong_past_form                | ✓         | 2/2         | template fallback    | 1ms     |
| 30 | subject_verb_agreeme  | plays           | play            | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 1ms     |
| 31 | subject_verb_agreeme  | have            | has             | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 1ms     |
| 32 | sentence_correction   | They was very h | They were very  | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 1ms     |
| 33 | subject_verb_agreeme  | bark            | barks           | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 1ms     |

### hybrid

| # | Topic | Student | Correct | Diagnosis | Labels | Retrieval | Remediation | Source | Latency |
|---|-------|---------|---------|-----------|--------|-----------|-------------|--------|---------|
|  0 | verb_tense            | go              | went            | ✓         | base_form_instead_of_past      | ✓         | 2/2         | template fallback    | 1ms     |
|  1 | verb_tense            | play            | played          | ✓         | base_form_instead_of_past      | ✓         | 1/1         | template fallback    | 1ms     |
|  2 | verb_tense            | eated           | ate             | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 1ms     |
|  3 | verb_tense            | runned          | ran             | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 1ms     |
|  4 | verb_tense            | studied         | had been studyi | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 1ms     |
|  5 | verb_tense            | watched         | were watching   | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 1ms     |
|  6 | subject_verb_agreeme  | go              | goes            | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 1ms     |
|  7 | subject_verb_agreeme  | do              | does            | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 1ms     |
|  8 | subject_verb_agreeme  | rain            | rains           | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 1ms     |
|  9 | subject_verb_agreeme  | is              | are             | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 1ms     |
| 10 | subject_verb_agreeme  | have            | has             | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 1ms     |
| 11 | article_usage         | a               | an              | ✓         | a_vs_an_confusion              | ✓         | 2/2         | template fallback    | 1ms     |
| 12 | article_usage         | an              | a               | ✓         | a_vs_an_confusion              | ✓         | 2/2         | template fallback    | 1ms     |
| 13 | article_usage         | a               | an              | ✓         | a_vs_an_confusion              | ✓         | 2/2         | template fallback    | 1ms     |
| 14 | article_usage         |                 | The             | ✓         | missing_article                | ✓         | 1/1         | template fallback    | 1ms     |
| 15 | article_usage         | a               | the             | ✗         |                                | ✗         | 0/1         | template fallback    | 1ms     |
| 16 | article_usage         | the             |                 | ✗         |                                | ✗         | 0/1         | template fallback    | 1ms     |
| 17 | preposition_usage     | in              | on              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 1ms     |
| 18 | preposition_usage     | on              | in              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 1ms     |
| 19 | preposition_usage     | on              | at              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 1ms     |
| 20 | preposition_usage     | in              | at              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 1ms     |
| 21 | preposition_usage     | on              | in              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 1ms     |
| 22 | sentence_correction   | She go to schoo | She went to sch | ✓         | base_form_instead_of_past, missing_third | ✓         | 3/3         | template fallback    | 1ms     |
| 23 | sentence_correction   | He don't likes  | He doesn't like | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 1ms     |
| 24 | sentence_correction   | I have went to  | I have gone to  | ✓         | wrong_past_form                | ✓         | 2/2         | template fallback    | 1ms     |
| 25 | sentence_correction   | She is a honest | She is an hones | ✓         | a_vs_an_confusion              | ✓         | 2/2         | template fallback    | 1ms     |
| 26 | verb_tense            | walk            | walked          | ✓         | base_form_instead_of_past      | ✓         | 2/2         | template fallback    | 1ms     |
| 27 | verb_tense            | comed           | came            | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 1ms     |
| 28 | verb_tense            | singed          | sang            | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 1ms     |
| 29 | sentence_correction   | She has took my | She has taken m | ✓         | wrong_past_form                | ✓         | 2/2         | template fallback    | 1ms     |
| 30 | subject_verb_agreeme  | plays           | play            | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 1ms     |
| 31 | subject_verb_agreeme  | have            | has             | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 1ms     |
| 32 | sentence_correction   | They was very h | They were very  | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 1ms     |
| 33 | subject_verb_agreeme  | bark            | barks           | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 1ms     |

### full_rag

| # | Topic | Student | Correct | Diagnosis | Labels | Retrieval | Remediation | Source | Latency |
|---|-------|---------|---------|-----------|--------|-----------|-------------|--------|---------|
|  0 | verb_tense            | go              | went            | ✓         | base_form_instead_of_past      | ✓         | 2/2         | template fallback    | 5856ms  |
|  1 | verb_tense            | play            | played          | ✓         | base_form_instead_of_past      | ✓         | 1/1         | template fallback    | 2725ms  |
|  2 | verb_tense            | eated           | ate             | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 9199ms  |
|  3 | verb_tense            | runned          | ran             | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 12623ms |
|  4 | verb_tense            | studied         | had been studyi | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 2804ms  |
|  5 | verb_tense            | watched         | were watching   | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 4615ms  |
|  6 | subject_verb_agreeme  | go              | goes            | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 8610ms  |
|  7 | subject_verb_agreeme  | do              | does            | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 3675ms  |
|  8 | subject_verb_agreeme  | rain            | rains           | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 4044ms  |
|  9 | subject_verb_agreeme  | is              | are             | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 9603ms  |
| 10 | subject_verb_agreeme  | have            | has             | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 3890ms  |
| 11 | article_usage         | a               | an              | ✓         | a_vs_an_confusion              | ✓         | 2/2         | template fallback    | 4876ms  |
| 12 | article_usage         | an              | a               | ✓         | a_vs_an_confusion              | ✓         | 2/2         | template fallback    | 5588ms  |
| 13 | article_usage         | a               | an              | ✓         | a_vs_an_confusion              | ✓         | 2/2         | template fallback    | 8245ms  |
| 14 | article_usage         |                 | The             | ✓         | missing_article                | ✓         | 1/1         | template fallback    | 4977ms  |
| 15 | article_usage         | a               | the             | ✗         |                                | ✗         | 0/1         | template fallback    | 8324ms  |
| 16 | article_usage         | the             |                 | ✗         |                                | ✗         | 0/1         | template fallback    | 8494ms  |
| 17 | preposition_usage     | in              | on              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 5156ms  |
| 18 | preposition_usage     | on              | in              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 6902ms  |
| 19 | preposition_usage     | on              | at              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 4572ms  |
| 20 | preposition_usage     | in              | at              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 5196ms  |
| 21 | preposition_usage     | on              | in              | ✓         | wrong_preposition              | ✓         | 1/1         | template fallback    | 6732ms  |
| 22 | sentence_correction   | She go to schoo | She went to sch | ✓         | base_form_instead_of_past, missing_third | ✓         | 3/3         | template fallback    | 6198ms  |
| 23 | sentence_correction   | He don't likes  | He doesn't like | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 7856ms  |
| 24 | sentence_correction   | I have went to  | I have gone to  | ✓         | wrong_past_form                | ✓         | 2/2         | template fallback    | 2530ms  |
| 25 | sentence_correction   | She is a honest | She is an hones | ✓         | a_vs_an_confusion              | ✓         | 2/2         | template fallback    | 4305ms  |
| 26 | verb_tense            | walk            | walked          | ✓         | base_form_instead_of_past      | ✓         | 2/2         | template fallback    | 3830ms  |
| 27 | verb_tense            | comed           | came            | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 9068ms  |
| 28 | verb_tense            | singed          | sang            | ✓         | wrong_past_form                | ✓         | 1/1         | template fallback    | 4222ms  |
| 29 | sentence_correction   | She has took my | She has taken m | ✓         | wrong_past_form                | ✓         | 2/2         | template fallback    | 7729ms  |
| 30 | subject_verb_agreeme  | plays           | play            | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 9692ms  |
| 31 | subject_verb_agreeme  | have            | has             | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 7639ms  |
| 32 | sentence_correction   | They was very h | They were very  | ✓         | plural_subject_error           | ✓         | 2/2         | template fallback    | 7159ms  |
| 33 | subject_verb_agreeme  | bark            | barks           | ✓         | missing_third_person_s         | ✓         | 2/2         | template fallback    | 8155ms  |
