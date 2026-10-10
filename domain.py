"""Framework-independent demo rules. No SAP, email or AI calls."""
from datetime import date, timedelta

STAGES = ['Application', 'Screening call', 'HR interview', 'Technical interview', 'Assessment', 'Final behavioral interview', 'Reference / background checks']
OUTCOMES = ['In progress', 'Withdrawn', 'Rejection sent', 'Offer signed']
PREFIX = dict(zip(STAGES, ['P','S','H','T','A','F','R']))
PREFIX['Offer'] = 'O'
BLOCKS = {stage: [prefix + '0' + str(n) for n in range(1, 9)] for stage, prefix in PREFIX.items()}  # 8 questions per stage
EXTRA = 'Additional questions'   # questions added in the app that appear at the end of the survey
SURVEY_VERSION = 'demo-3'

def eligible(candidate):
    return candidate['outcome'] in OUTCOMES[1:]

def stage_options(candidate):
    """Stage blocks that can be previewed on their own for a closed journey."""
    options = [stage for stage in STAGES if stage in candidate['stages']]
    if candidate['outcome'] == 'Offer signed':
        options.append('Offer')
    return options

def route(candidate, aware=False, scope='full', questions=None):
    """scope='full' -> whole journey; scope=<stage name> -> only that stage's block.
    questions: the live question list (so added/deleted/reordered questions are respected)."""
    if not eligible(candidate):
        return []
    present = None
    blocks = BLOCKS
    if questions is not None:
        blocks = {stage: [] for stage in list(PREFIX) + [EXTRA]}
        for q in questions:
            if q['stage'] in blocks:
                blocks[q['stage']].append(q['id'])
        present = {q['id'] for q in questions}
    if scope != 'full':
        return list(blocks.get(scope, [])) if scope in stage_options(candidate) else []
    ids = ['B01','B02'] + (['B03','B04'] if aware else []) + ['B05'] + (['B06'] if aware else [])
    for stage in STAGES:
        if stage in candidate['stages']:
            ids += blocks[stage]
    ids += ['C01'] + (['C02'] if len(candidate['stages']) >= 2 else [])
    ids += blocks['Offer'] if candidate['outcome'] == 'Offer signed' else []
    ids += {'Withdrawn':['W01'],'Rejection sent':['J01'],'Offer signed':[]}[candidate['outcome']]
    ids += blocks.get(EXTRA, [])
    ids += ['G01','G02','G04']
    return [i for i in ids if present is None or i in present]

def numeric(value):
    if not isinstance(value, str):
        return None
    first = value.split(' ',1)[0]
    return int(first) if first.isdigit() else None

NO = ['No','لا']
YES = ['Yes','نعم']
LATE = ['10 to 30 minutes late','More than 30 minutes late','تأخر من 10 إلى 30 دقيقة','تأخر أكثر من 30 دقيقة']
SLOW = ['More than a week','I never heard back','أكثر من أسبوع','لم يصلني رد']
CONDUCT = ('Interviewer conduct', 'Have HR review feedback and consider interviewer coaching; do not assume misconduct.', 'HR supervisor', YES)

# question id -> (theme, proposed action, owner, extra trigger values besides a score of 1-2)
RULES = {
    'P01': ('Application process', 'Review form length, mandatory fields and mobile experience.', 'Recruitment owner', []),
    'P02': ('Job description clarity', 'Review job-advert wording and requirements with the hiring manager.', 'Hiring manager', []),
    'P05': ('Application acknowledgement', 'Check that automatic acknowledgements are sent and understood.', 'Recruitment owner', NO),
    'P06': ('Next steps after applying', 'Review the acknowledgement message and the stated timeline.', 'Recruitment owner', []),
    'S01': ('Screening call', 'Review call standards and the call script with the recruiter.', 'HR supervisor', []),
    'S02': ('Call punctuality', 'Review scheduling and reminders for screening calls.', 'Recruitment owner', LATE),
    'S04': ('Salary conversation', 'Review how salary expectations are raised and explained in screening calls.', 'HR supervisor', []),
    'S05': ('English check instructions', 'Review how the English-language part is introduced.', 'Recruitment owner', []),
    'S07': ('Stage waiting time', 'Review turnaround after screening calls and agree a target.', 'HR supervisor', SLOW),
    'H01': ('Interviewer preparation', 'Brief interviewers on the candidate profile before HR interviews.', 'HR supervisor', []),
    'H05': ('Interview punctuality', 'Review scheduling and interviewer availability.', 'Recruitment owner', LATE),
    'H06': ('Interview comfort', 'Review how interviews open and the setting; consider interviewer coaching.', 'HR supervisor', []),
    'T01': ('Technical interview relevance', 'Review competency coverage and the technical question set for the role.', 'Hiring manager', []),
    'T04': ('Panel coordination', 'Agree panel roles and turn-taking before technical interviews.', 'HR supervisor', []),
    'T06': CONDUCT,
    'A01': ('Assessment instructions', 'Rewrite assessment instructions and test them with a colleague.', 'HR officer', []),
    'A02': ('Assessment burden', 'Review task length with the hiring manager and pilot a shorter assessment.', 'Hiring manager', []),
    'A03': ('Assessment relevance', 'Review assessment content against the role requirements.', 'Hiring manager', []),
    'A05': ('Assessment briefing', 'Add the content and expected duration to the assessment invitation.', 'HR officer', NO),
    'A06': ('Assessment fairness', 'Review whether the assessment design gives a fair chance to show ability.', 'HR supervisor', []),
    'A07': ('Stage waiting time', 'Review turnaround after the assessment and agree a target.', 'HR supervisor', SLOW),
    'F01': ('Behavioral interview', 'Calibrate the panel on behavioral probes and sufficient answer time.', 'HR supervisor', []),
    'F02': ('Panel coordination', 'Agree panel roles for the final interview and avoid overlapping questions.', 'HR supervisor', []),
    'F05': ('Interview comfort', 'Review panel size and how the final interview opens.', 'HR supervisor', []),
    'F07': CONDUCT,
    'R01': ('Check purpose', 'Explain the purpose of reference and background checks in the request message.', 'HR officer', []),
    'R02': ('Check requirements', 'Provide a clear checklist of the information and documents needed.', 'HR officer', []),
    'R04': ('Reference consent', 'Always inform candidates before contacting their references.', 'HR officer', NO),
    'R05': ('Personal data handling', 'Review how personal data is handled and communicated during checks.', 'HR supervisor', []),
    'R06': ('Updates during checks', 'Agree an update schedule while checks are in progress.', 'HR officer', []),
    'C01': ('Communication', 'Agree an update schedule and review delayed candidate updates.', 'Recruitment owner', ['No updates received','لم تصلني تحديثات']),
    'C02': ('Stage waiting time', 'Review stage handoffs and agree target turnaround times.', 'HR supervisor', []),
    'O01': ('Offer clarity', 'Review the offer explanation and provide a clear checklist of terms.', 'HR officer', []),
    'O02': ('Offer expectations', 'Review expectation mismatches; do not treat every difference as a breach.', 'HR officer', YES),
    'O03': ('Offer decision window', 'Review the standard time given to review and decide on an offer.', 'HR officer', []),
    'O05': ('Offer delivery', 'Review how and by whom offers are delivered.', 'HR officer', []),
    'O06': ('Pre-boarding clarity', 'Send a clear checklist covering the time between signing and the first day.', 'HR officer', []),
    'J01': ('Rejection communication', 'Review rejection wording for clarity and respectful closure.', 'HR officer', []),
}

def suggest(answers, extra_rules=None):
    """extra_rules: {question_id: {'theme','action','owner','triggers':[...],'low_score':bool}} for questions added in the app."""
    output=[]
    for key,value in answers.items():
        base=key.split('@')[0]
        if extra_rules and base in extra_rules:
            r=extra_rules[base]
            theme,task,owner,triggers,low=r['theme'],r['action'],r['owner'],r.get('triggers',[]),bool(r.get('low_score'))
        elif base in RULES:
            theme,task,owner,triggers=RULES[base]
            low=True
        else:
            continue
        score=numeric(value) if low else None
        if (score is not None and score <= 2) or (isinstance(value, str) and value in triggers):
            output.append({'theme':theme,'source_question':key,'action':task,'owner':owner,'due':str(date.today()+timedelta(days=14)),'status':'Proposed','evidence':value})
    return output

def response_record(candidate, answers, question_copy, response_id, scope='full'):
    # Data minimisation for demonstration only, not an anonymity guarantee.
    return {'id':response_id,'outcome':candidate['outcome'],
            'respondent': None if candidate['outcome']=='Rejection sent' else candidate['name'],
            'answers':answers,'questions':question_copy,'survey_version':SURVEY_VERSION,'scope':scope}
