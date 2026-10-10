"""Framework-independent demo rules. No SAP, email or AI calls."""
from datetime import date, timedelta

STAGES = ['Application', 'Screening call', 'HR interview', 'Technical interview', 'Assessment', 'Final behavioral interview', 'Reference / background checks']
OUTCOMES = ['In progress', 'Withdrawn', 'Rejection sent', 'Offer signed']
STAGE_IDS = dict(zip(STAGES, ['P01','S01','H01','T01','A01','F01','R01']))
INTERVIEWS = ['HR interview','Technical interview','Final behavioral interview']

def eligible(candidate):
    return candidate['outcome'] in OUTCOMES[1:]

def route(candidate, aware=False):
    if not eligible(candidate):
        return []
    ids = ['B01','B02'] + (['B03','B04'] if aware else []) + ['B05']
    for stage in STAGES:
        if stage in candidate['stages']:
            ids.append(STAGE_IDS[stage])
            if stage in INTERVIEWS:
                ids.append('I01@'+stage)
    ids += ['C01'] + (['C02'] if len(candidate['stages']) >= 2 else [])
    ids += [{'Withdrawn':'W01','Rejection sent':'J01','Offer signed':'O01'}[candidate['outcome']]]
    return ids + ['G01','G02','G04']

def numeric(value):
    if not isinstance(value, str):
        return None
    first = value.split(' ',1)[0]
    return int(first) if first.isdigit() else None

def suggest(answers):
    rules = {
        'C01': ('Communication', 'Agree an update schedule and review delayed candidate updates.', 'Recruitment owner'),
        'C02': ('Stage waiting time', 'Review stage handoffs and agree target turnaround times.', 'HR supervisor'),
        'A01': ('Assessment burden', 'Review task length with the hiring manager and pilot a shorter assessment.', 'Hiring manager'),
        'T01': ('Technical interview', 'Review competency coverage and opportunities to demonstrate relevant skills.', 'Hiring manager'),
        'F01': ('Behavioral interview', 'Calibrate the panel on behavioral probes and sufficient answer time.', 'HR supervisor'),
        'O01': ('Offer clarity', 'Review the offer explanation and provide a clear checklist of terms.', 'HR officer'),
        'J01': ('Rejection communication', 'Review rejection wording for clarity and respectful closure.', 'HR officer'),
        'I01': ('Interviewer conduct', 'Have HR review feedback and consider interviewer coaching; do not assume misconduct.', 'HR supervisor'),
    }
    output=[]
    for key,value in answers.items():
        base=key.split('@')[0]
        score=numeric(value)
        no_updates=base=='C01' and value in ['No updates received','لم تصلني تحديثات']
        if base in rules and ((score is not None and score <= 2) or no_updates):
            theme,task,owner=rules[base]
            output.append({'theme':theme,'source_question':key,'action':task,'owner':owner,'due':str(date.today()+timedelta(days=14)),'status':'Proposed','evidence':value})
    return output

def response_record(candidate, answers, question_copy, response_id):
    # Data minimisation for demonstration only, not an anonymity guarantee.
    return {'id':response_id,'outcome':candidate['outcome'],
            'respondent': None if candidate['outcome']=='Rejection sent' else candidate['name'],
            'answers':answers,'questions':question_copy,'survey_version':'demo-1'}
