# Natural-Language Search Preferences

`POST /api/search/from-text` turns user-stated job-search preferences into the existing `SearchPreferences` model and runs the existing search pipeline.

## Request and response

The request keeps the same explicit candidate profile used by structured search:

```json
{
  "profile": {"skills": ["Python"], "jobTitles": ["Backend Engineer"]},
  "preferences_text": "Find backend roles in Dakar. Python is required; remote is preferred."
}
```

`preferences_text` must contain 1–20,000 characters and must not be whitespace-only. The successful response has the same `SearchResponse` structure as `POST /api/search`: results, matches, excluded offers, ranking, and collection metadata.

## Processing and extraction

The existing `LLMService.parse_preferences` operation uses the configured `GroqLLMService`, `GROQ_API_KEY`, `GROQ_MODEL`, and `REQUEST_TIMEOUT_SECONDS`. Structured output is validated against a strict extraction schema and then converted to `SearchPreferences`. Only explicit preference strengths are copied; filtering's existing default for an unspecified strength remains `PREFERRED`. `REQUIRED` is emitted only for clearly non-negotiable wording. Missing or ambiguous criteria stay empty or `null`; there is no inference of hybrid versus remote, location, salary units, or other missing fields. Quoted or pasted third-party material is not followed as instructions or adopted as a preference unless the user clearly adopts its criteria.

The route calls the existing `criteria_from_preferences` builder and `SearchRuntime.pipeline`, then uses the same response mapping as structured search. It does not save the parsed preferences or supplied profile and does not make search requests if preference parsing fails. Connector failures keep their existing isolated failure reporting.

## Errors, privacy, and limitations

Malformed requests, missing fields, empty text, and text over 20,000 characters return 422. A provider error, refusal, empty or malformed structured result, or invalid preference schema returns a generic 502; the search pipeline is not run. The endpoint does not log user text or provider exception details. Preference text is sent to the configured LLM provider when the endpoint is called; provider-side handling follows the configured account and provider terms. Application startup does not create a provider client or make a request.

The model's extraction remains probabilistic: schema validation confirms shape and allowed values, not that every parsed preference is faithfully grounded in the user's wording. Review the parsed preferences through the resulting search behavior; this API does not return a separate parsed-preferences object.

Automated tests inject fake LLM services and connector fixtures. They do not call the provider or external job sources.
