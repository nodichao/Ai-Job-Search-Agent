"""AI Job Search Agent -- Streamlit frontend.

This app contains no business logic: it only collects a CV and preferences,
calls the backend's agentic endpoint (POST /api/agent/search), and displays
exactly what the backend returns. Scores, ranks, and recommendation
decisions come from the backend's matching engine; this file never
recomputes or reinterprets them.
"""
import json
import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("JOB_AGENT_API_URL", "http://localhost:8000")
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("JOB_AGENT_API_TIMEOUT_SECONDS", "120"))
MAX_CV_FILE_BYTES = 5 * 1024 * 1024

JOB_TITLE_OPTIONS = [
    "Développeur Full-Stack",
    "Développeur Frontend",
    "Développeur Backend",
    "Technical Support Engineer",
    "Data Analyst",
]

LOCATION_OPTIONS = {
    "Dakar": {"locations": ["Dakar"], "countries": ["Senegal"]},
    "Partout au Sénégal": {"locations": [], "countries": ["Senegal"]},
    "Afrique": {"locations": [], "countries": []},
    "Partout dans le monde": {"locations": [], "countries": []},
    "Sans préférence": {"locations": [], "countries": []},
}

WORK_MODE_OPTIONS = {
    "Télétravail uniquement": True,
    "Télétravail et présentiel": None,
    "Présentiel uniquement": False,
    "Sans préférence": None,
}

SENIORITY_OPTIONS = {
    "Stage": ["INTERN"],
    "Junior": ["JUNIOR"],
    "Intermédiaire": ["MID"],
    "Senior": ["SENIOR"],
    "Sans préférence": [],
}

EMPLOYMENT_TYPE_OPTIONS = {
    "Temps plein": ["FULL_TIME"],
    "Temps partiel": ["PART_TIME"],
    "CDD": ["CONTRACT"],
    "Stage": ["INTERNSHIP"],
    "Freelance": ["FREELANCE"],
    "Sans préférence": [],
}

CURRENCY_OPTIONS = ["XOF", "USD", "EUR"]

DECISION_LABELS = {
    "RECOMMENDED": "✅ Recommandée",
    "REVIEW": "⚠️ À vérifier",
    "NOT_RECOMMENDED": "❌ Non recommandée",
    "INSUFFICIENT_EVIDENCE": "❔ Preuves insuffisantes",
}


st.set_page_config(page_title="AI Job Search Agent", page_icon="🔎", layout="wide")


def _build_preferences() -> dict:
    """Read the sidebar/form widgets and convert them into the backend's
    SearchPreferences shape. 'Sans préférence' choices become empty
    lists/null, never a fabricated constraint."""
    location_choice = LOCATION_OPTIONS[st.session_state["location_choice"]]
    seniority = SENIORITY_OPTIONS[st.session_state["seniority_choice"]]
    employment_types = EMPLOYMENT_TYPE_OPTIONS[st.session_state["employment_choice"]]
    remote = WORK_MODE_OPTIONS[st.session_state["work_mode_choice"]]

    job_titles = list(st.session_state.get("job_titles_choice", []))
    custom_title = st.session_state.get("custom_job_title", "").strip()
    if custom_title:
        job_titles.append(custom_title)

    skills = [item.strip() for item in st.session_state.get("skills_choice", "").split(",") if item.strip()]

    preferences: dict = {
        "jobTitles": job_titles,
        "locations": location_choice["locations"],
        "countries": location_choice["countries"],
        "remote": remote,
        "seniority": seniority,
        "employmentTypes": employment_types,
        "skills": skills,
    }

    if st.session_state.get("salary_no_preference", True):
        preferences["salary"] = None
    else:
        preferences["salary"] = {
            "minimum": st.session_state.get("salary_min") or None,
            "maximum": st.session_state.get("salary_max") or None,
            "currency": st.session_state.get("salary_currency"),
            "period": "month" if st.session_state.get("salary_period") == "Mensuel" else "year",
        }
    return preferences


def _call_agent(cv_file, preferences: dict) -> dict:
    files = {"file": (cv_file.name, cv_file.getvalue(), cv_file.type or "application/octet-stream")}
    data = {"preferences": json.dumps(preferences)}
    response = requests.post(
        f"{API_BASE_URL}/api/agent/search", files=files, data=data, timeout=REQUEST_TIMEOUT_SECONDS,
    )
    return response


def _offer_id(identity: dict) -> str | None:
    """Mirrors the backend's own stable offer id (app.services.agent_tools)
    so an explanation is joined to the exact offer it describes, never to a
    guessed position."""
    return identity.get("sourceId") or identity.get("id") or identity.get("slug")


def _render_offer_card(offer: dict, match: dict, explanations_by_id: dict) -> None:
    matching = match["matching"]
    recommendation = match["recommendation"]
    position = offer.get("position", {})
    company = offer.get("company", {})
    location = offer.get("location", {})
    employment = offer.get("employment", {})

    decision = recommendation.get("decision", "INSUFFICIENT_EVIDENCE")
    title = position.get("title") or "(titre inconnu)"
    company_name = company.get("name") or "Entreprise non précisée"

    with st.container(border=True):
        header_col, score_col = st.columns([4, 1])
        with header_col:
            st.markdown(f"### {title}")
            st.caption(f"{company_name} · {DECISION_LABELS.get(decision, decision)}")
        with score_col:
            if matching.get("score") is not None:
                st.metric("Score", f"{matching['score']:.0f}/100")
            else:
                st.metric("Score", "N/A")

        info_cols = st.columns(4)
        locations = location.get("locations") or []
        countries = location.get("countries") or []
        info_cols[0].markdown(f"**Localisation**\n\n{', '.join(locations + countries) or 'Non précisée'}")
        remote_value = location.get("remote")
        remote_text = "Oui" if remote_value is True else "Non" if remote_value is False else "Inconnu"
        info_cols[1].markdown(f"**Télétravail**\n\n{remote_text}")
        info_cols[2].markdown(f"**Contrat**\n\n{employment.get('type', 'UNKNOWN')}")
        info_cols[3].markdown(f"**Séniorité**\n\n{employment.get('seniority', 'UNKNOWN')}")

        offer_id = _offer_id(offer.get("identity", {}))
        narrative = explanations_by_id.get(offer_id) if offer_id else None
        if narrative:
            explanation = narrative["explanation"]
            source_label = "Généré par l'IA" if narrative["source"] == "llm" else "Résumé déterministe (secours)"
            st.markdown(f"**Explication** _{('(' + source_label + ')')}_")
            st.write(explanation.get("summary", ""))
            cols = st.columns(2)
            with cols[0]:
                if explanation.get("strengths"):
                    st.markdown("**Points forts**")
                    for item in explanation["strengths"]:
                        st.markdown(f"- {item}")
                if explanation.get("constraints"):
                    st.markdown("**Restrictions / incompatibilités**")
                    for item in explanation["constraints"]:
                        st.markdown(f"- {item}")
            with cols[1]:
                if explanation.get("gaps"):
                    st.markdown("**Éléments manquants**")
                    for item in explanation["gaps"]:
                        st.markdown(f"- {item}")
                if explanation.get("uncertainties"):
                    st.markdown("**Informations inconnues**")
                    for item in explanation["uncertainties"]:
                        st.markdown(f"- {item}")
            if explanation.get("recommendationContext"):
                st.caption(f"Pourquoi cette décision : {explanation['recommendationContext']}")

        with st.expander("Détails techniques du matching"):
            st.json(matching)
            st.json(recommendation)

        apply_url = (offer.get("application") or {}).get("applyUrl") or offer.get("identity", {}).get("offerUrl")
        if apply_url:
            st.markdown(f"[Voir l'offre originale]({apply_url})")


def _identity_key(identity: dict) -> tuple:
    return (identity.get("sourceId"), identity.get("id"), identity.get("slug"), identity.get("offerUrl"))


def render_results(body: dict) -> None:
    explanations_by_id = {item["offerId"]: item for item in body.get("explanations", [])}
    matches = body.get("matches", [])
    ranking = body.get("ranking", {"offers": []})

    if not matches:
        st.warning(
            "Aucune offre n'a été trouvée pour ces préférences. Essayez d'élargir la localisation, "
            "le mode de travail ou l'intitulé de poste."
        )
        return

    st.success(f"{len(matches)} offre(s) analysée(s) — {ranking.get('total', 0)} recommandée(s) par le moteur.")

    show_all = st.checkbox("Afficher aussi les offres non recommandées", value=False)

    # `matches` only carries the offer's identity (offerIdentity); the full
    # offer facts (title, company, location...) live in `results`, exactly
    # like the existing /api/search contract this endpoint reuses unchanged.
    offers_by_key = {_identity_key(offer["identity"]): offer for offer in body.get("results", [])}
    ranked_keys = {_identity_key(ranked["offer"]["identity"]) for ranked in ranking.get("offers", [])}

    ordered_matches = sorted(
        matches,
        key=lambda m: (
            _identity_key(m["offerIdentity"]) not in ranked_keys,
            -(m["matching"]["score"] if m["matching"]["score"] is not None else -1),
        ),
    )

    displayed = 0
    for match in ordered_matches:
        decision = match["recommendation"]["decision"]
        if not show_all and decision not in {"RECOMMENDED", "REVIEW"}:
            continue
        offer = offers_by_key.get(_identity_key(match["offerIdentity"]))
        if offer is None:
            continue
        _render_offer_card(offer, match, explanations_by_id)
        displayed += 1

    if displayed == 0:
        st.info("Aucune offre recommandée pour l'instant. Cochez la case ci-dessus pour voir toutes les offres analysées.")


def main() -> None:
    st.title("AI Job Search Agent")
    st.write(
        "Déposez votre CV, indiquez vos préférences, puis lancez la recherche. "
        "L'agent extrait votre profil, interroge le moteur de recherche et de matching existant, "
        "puis explique les résultats -- sans jamais modifier les scores ou le classement calculés par le moteur."
    )

    if "result" not in st.session_state:
        st.session_state["result"] = None
    if "error" not in st.session_state:
        st.session_state["error"] = None

    st.header("1. Votre CV")
    cv_file = st.file_uploader("Importer votre CV (PDF ou DOCX, 5 Mo max)", type=["pdf", "docx"])
    if cv_file is not None:
        size_kb = len(cv_file.getvalue()) / 1024
        st.caption(f"Fichier sélectionné : {cv_file.name} ({size_kb:.0f} Ko)")
        if len(cv_file.getvalue()) > MAX_CV_FILE_BYTES:
            st.error("Ce fichier dépasse la limite de 5 Mo autorisée par le backend.")

    st.header("2. Vos préférences")
    col1, col2 = st.columns(2)
    with col1:
        st.multiselect(
            "Postes recherchés", JOB_TITLE_OPTIONS, default=[], key="job_titles_choice",
            help="Sélectionnez un ou plusieurs postes, ou saisissez un intitulé personnalisé ci-dessous.",
        )
        st.text_input("Autre intitulé de poste (facultatif)", key="custom_job_title")
        st.selectbox("Localisation souhaitée", list(LOCATION_OPTIONS), key="location_choice")
        if st.session_state.get("location_choice") in {"Afrique", "Partout dans le monde"}:
            st.caption(
                "Le filtrage géographique par continent n'est pas pris en charge par le backend actuel : "
                "aucun filtre de pays ne sera appliqué pour ce choix."
            )
        st.selectbox("Mode de travail", list(WORK_MODE_OPTIONS), key="work_mode_choice")
    with col2:
        st.selectbox("Niveau d'expérience", list(SENIORITY_OPTIONS), key="seniority_choice")
        st.selectbox("Type de contrat", list(EMPLOYMENT_TYPE_OPTIONS), key="employment_choice")
        st.text_input(
            "Compétences recherchées (séparées par une virgule, facultatif)",
            key="skills_choice",
            help="Ce sont vos préférences de recherche, distinctes des compétences qui seront extraites de votre CV.",
        )

    st.subheader("Salaire")
    st.checkbox("Sans préférence salariale / à négocier", value=True, key="salary_no_preference")
    if not st.session_state.get("salary_no_preference", True):
        salary_cols = st.columns(4)
        salary_cols[0].number_input("Minimum", min_value=0, step=10_000, key="salary_min")
        salary_cols[1].number_input("Maximum", min_value=0, step=10_000, key="salary_max")
        salary_cols[2].selectbox("Devise", CURRENCY_OPTIONS, key="salary_currency")
        salary_cols[3].selectbox("Période", ["Mensuel", "Annuel"], key="salary_period")

    st.divider()
    can_search = cv_file is not None and len(cv_file.getvalue()) <= MAX_CV_FILE_BYTES if cv_file else False
    search_clicked = st.button("Rechercher des offres", type="primary", disabled=not can_search)

    if search_clicked and cv_file is not None:
        st.session_state["result"] = None
        st.session_state["error"] = None
        preferences = _build_preferences()
        with st.spinner("Recherche en cours (extraction du CV, recherche des offres, calcul des scores, "
                         "préparation des explications)... cela peut prendre jusqu'à une minute."):
            try:
                response = _call_agent(cv_file, preferences)
            except requests.exceptions.Timeout:
                st.session_state["error"] = "Le backend n'a pas répondu à temps. Réessayez dans un instant."
            except requests.exceptions.ConnectionError:
                st.session_state["error"] = f"Impossible de joindre le backend à l'adresse {API_BASE_URL}."
            else:
                if response.status_code == 200:
                    st.session_state["result"] = response.json()
                else:
                    try:
                        detail = response.json().get("detail", "Erreur inconnue")
                    except ValueError:
                        detail = "Erreur inconnue"
                    st.session_state["error"] = f"Le backend a renvoyé une erreur ({response.status_code}) : {detail}"

    if st.session_state.get("error"):
        st.error(st.session_state["error"])

    if st.session_state.get("result"):
        body = st.session_state["result"]
        st.header("3. Résultats")

        if body.get("warnings"):
            for warning in body["warnings"]:
                st.warning(warning)

        with st.expander("Étapes réellement exécutées par l'agent"):
            for step in body.get("steps", []):
                icon = {"success": "✅", "fallback": "⚠️", "error": "❌"}.get(step["status"], "•")
                detail = f" — {step['detail']}" if step.get("detail") else ""
                st.markdown(f"{icon} `{step['tool']}` : {step['status']}{detail}")

        with st.expander("Profil extrait de votre CV"):
            st.json(body.get("profile", {}))

        meta = body.get("meta", {})
        st.caption(
            f"{meta.get('total', 0)} offre(s) collectée(s) depuis {', '.join(meta.get('sources', [])) or 'aucune source'} "
            f"en {meta.get('durationMs', 0)} ms."
        )

        render_results(body)


if __name__ == "__main__":
    main()
