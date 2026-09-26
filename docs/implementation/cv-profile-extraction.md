# CV Profile Extraction

`POST /api/profile/parse-cv` converts candidate supplied CV text into the existing canonical `UserProfile`. It is separate from profile persistence and search.

## Inputs and outputs

The endpoint accepts either:

- JSON: `{"cv_text":"..."}` with 1–100,000 characters;
- multipart form data: one `file` field containing a `.pdf` / `application/pdf` file or `.docx` / `application/vnd.openxmlformats-officedocument.wordprocessingml.document` file, at most 5 MiB.

It returns a validated `UserProfile`. Other formats, mismatched extension/MIME, empty input, malformed documents, encrypted PDFs, files over the size limit, and documents with no extractable text are rejected with a 4xx response. PDF text extraction is limited to 100 pages. DOCX extraction checks the ZIP structure, entry count, expanded size, and XML; embedded content is not executed. Text extraction runs in memory. The multipart parser may temporarily spool an upload while receiving it; the temporary handle is closed after the request and no application storage is written.

## Extraction rules

The configured LLM adapter uses structured output and the `UserProfile` field contract: `skills`, `jobTitles`, `experience`, `totalExperienceYears`, `education`, `languages`, `domains`, and `rawSourceMetadata`. CV content is explicitly treated as untrusted data. The prompt directs the model to ignore embedded instructions and extract only facts stated in the CV. Uncertain collections are empty; uncertain total experience is `null`. `rawSourceMetadata` remains empty because the repository defines no safe metadata extraction contract and the raw CV is not copied into it.

These instructions reduce hallucination risk; the application cannot independently prove that each returned fact is supported by the CV. Review extracted profiles before saving or relying on them.

## Configuration, privacy, and persistence

`OPENAI_API_KEY` and `LLM_MODEL` configure the existing OpenAI adapter. `REQUEST_TIMEOUT_SECONDS` supplies its request timeout. The application constructs the adapter without contacting the provider; the request is made only when `/parse-cv` is called. Provider calls use structured Chat Completions parsing with response storage disabled. No full CV or prompt is logged. The endpoint does not persist or overwrite the saved profile. The CV is transmitted to the configured provider, so its provider-side handling remains subject to that provider's terms and account settings.

Input/document validation failures return 4xx responses. Provider or structured-response failures return a generic 502 without provider messages, prompts, or CV text. The endpoint does not parse scanned-image OCR, password-protected documents, legacy `.doc`, or other document formats. PDF/DOCX uploads are capped at 5 MiB; extracted text is capped at 100,000 characters.

Automated tests inject a fake LLM and use generated in-memory documents. They do not call the provider.
