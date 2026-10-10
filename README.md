# PeoplePulse — management demo

A Streamlit candidate-experience prototype with 85 original bilingual question-bank items (8 per stage block). Core survey routing, responses, insights and editable rule-based action plans work within one browser session. This is a new standalone Python demo, not a migration of the earlier React/Sites application.

## Deploy
Upload the contents of this folder directly to the root of the private `mariaantar301-lang/people-pulse` repository. Do not upload the ZIP itself. Select the actual branch shown on GitHub (usually `main` after the first upload), with entrypoint `streamlit_app.py`. Use Python 3.12. No secrets or paid API keys are needed.

Keep the Streamlit app private. Verify Settings → Sharing → Only specific people can view this app before sharing. Community Cloud permits one private app at a time; do not make an existing app public or delete it to bypass that limit without deciding explicitly.

## Local use
`python -m pip install -r requirements.txt`

`python -m streamlit run streamlit_app.py`

## Five-minute presentation
1. Open Overview and explain working versus planned modules.
2. Open Candidates; inspect Demo Candidate A (withdrawn after technical).
3. Open Survey studio; select Candidate A. Choose prior awareness and see reputation questions appear.
4. Give communication and interview conduct a score of 2; answer overall satisfaction and advocacy. Submit.
5. Open Insights to view actual submitted answers.
6. Open Action plans, edit the proposed action, owner, date and status.
7. Preview the rejection and signed-offer paths. An in-progress candidate cannot submit.
8. Export the snapshot and action CSV before leaving.

## Data and privacy
Synthetic data only. No persistent database: session data can disappear on refresh, disconnect, server restart or redeploy and is not shared across viewers. Manual JSON export is available; snapshot restoration is not implemented.

Rejection response records omit the respondent name but this shared HR demonstration does NOT guarantee anonymity. HR can correlate the selected journey and its completion. No real candidate feedback should be collected. Identity separation, cohort protection and anonymous-response security require a different production architecture.

No email is sent. No public candidate portal, SAP connector, real scheduled automation, AI service, external benchmarks or Gallup/Korn Ferry content is included. Action suggestions use simple disclosed rules and require human review.

## Question builder (Question bank page)
Add, edit, reorder and delete questions in English from inside the app, and choose the answer type (rating 1–5, yes/no, yes/no/unsure, single choice, multiple choice, score 0–10, text). A rating, yes/no or single-choice question can optionally propose an action plan item (theme, action, owner) for the answers you pick. Arabic wording is optional; English is shown when it is empty. Changes last for the browser session: use Download question bank JSON and replace `question_bank.json` in GitHub to keep them, or load a saved file back from the Import / export tab. The awareness question (B02) and the two overall scores (G01, G02) are locked from deletion.

## Editing and extension
`domain.py`: stage order, outcome triggers, core question routing, response schema and action rules.

`question_bank.json`: 85 questions (8 per stage block: Application, Screening call, HR interview, Technical interview, Assessment, Final behavioral interview, Reference / background checks, Offer), bilingual wording, scales, routing notes and thematic source links. Optional questions are available for review but not activated by the current core route.

`streamlit_app.py`: presentation and session UI. Onboarding, engagement and offboarding are roadmap items, not implemented modules.

Question wording is original, informed by SurveyMonkey, Qualtrics and Greenhouse themes. It is not certified, psychometrically validated or benchmark-equivalent. Test bilingual comprehension before real use.

References:
- https://www.surveymonkey.com/templates/candidate-experience-survey-template/
- https://www.qualtrics.com/support/employee-experience/creating-ee-project/common-use-cases-ee/candidate-experience-program/
- https://support.greenhouse.io/hc/en-us/articles/20996918310555-Sample-survey-questions

## Tests
`python -m unittest discover -s tests -v`
