import csv
import io
import json
from pathlib import Path
from uuid import uuid4
from datetime import date
import streamlit as st
from domain import STAGES, OUTCOMES, route, eligible, numeric, suggest, response_record, stage_options, PREFIX, EXTRA

st.set_page_config(page_title='PeoplePulse | Experience Studio', page_icon='✦', layout='wide')
st.markdown('''<style>
.stApp {background: #f5f7fc;}
h1,h2,h3 {color:#152848;}
div[data-testid="stMetric"] {background:white;border:1px solid #e1e7f0;border-radius:16px;padding:18px;}
div.stButton > button[kind="primary"] {background:#3157d5;border:0;border-radius:9px;}
section[data-testid="stSidebar"] {background:#eaf0fa;}
</style>''', unsafe_allow_html=True)

ROOT=Path(__file__).parent
if 'bank' not in st.session_state:
    st.session_state.bank=json.loads((ROOT/'question_bank.json').read_text(encoding='utf-8'))
if 'candidates' not in st.session_state:
    st.session_state.candidates=[
        {'id':'demo-1','name':'Demo Candidate A','role':'QA Engineer','stages':STAGES[:4],'outcome':'Withdrawn','submitted':False},
        {'id':'demo-2','name':'Demo Candidate B','role':'Mechanical Engineer','stages':STAGES[:3],'outcome':'Rejection sent','submitted':False},
        {'id':'demo-3','name':'Demo Candidate C','role':'Procurement Officer','stages':STAGES.copy(),'outcome':'Offer signed','submitted':False},
    ]
for field in ['responses','actions']:
    if field not in st.session_state:
        st.session_state[field]=[]

bank=st.session_state.bank
questions={q['id']:q for q in bank['questions']}

def qtext(q,l):
    return q.get(l) or q['en']

def sopts(code,l):
    scale=bank['scales'][code]
    return (scale.get(l) or scale['en']).split(' | ')

def extra_rules():
    return {q['id']:q['rule'] for q in bank['questions'] if q.get('rule')}
with st.sidebar:
    st.title('✦ PeoplePulse')
    st.caption('EXPERIENCE STUDIO · MANAGEMENT DEMO')
    page=st.radio('Workspace', ['Overview','Candidates','Survey studio','Insights','Action plans','Question bank','Roadmap & export'])
    language=st.selectbox('Survey language / لغة السيرفي',['English','العربية'])
    st.divider()
    st.caption('Candidate experience · v0.1')
    st.caption('Demo only. No SAP connection, email delivery or external AI service.')
lang='ar' if language=='العربية' else 'en'
st.title('PeoplePulse')
st.caption('Listen carefully. Understand the experience. Follow through.')
st.info('Management demo • Synthetic data only • Changes last for this browser session. Download an export before leaving; refresh/restart may reset your work.')

def table(rows):
    if rows:
        st.dataframe(rows, hide_index=True, width='stretch')
    else:
        st.info('No records yet. Complete a demo survey to start.')

if page=='Overview':
    st.header('From feedback to follow-through')
    a,b,c,d=st.columns(4)
    a.metric('Demo candidates',len(st.session_state.candidates))
    b.metric('Survey responses',len(st.session_state.responses))
    c.metric('Open actions',sum(x['status']!='Completed' for x in st.session_state.actions))
    d.metric('Question library',len(questions))
    st.subheader('Your presentation journey')
    st.markdown('**1 · Candidates** — add a synthetic candidate and record the actual stages.\n\n**2 · Survey studio** — preview the relevant questions and submit a demo response.\n\n**3 · Insights** — review satisfaction and stage feedback.\n\n**4 · Action plans** — review suggestions, assign an owner and track progress.')
    table([{'Module':'Candidate experience','Readiness':'Working session demo'},
           {'Module':'Onboarding 30 / 60 / 90','Readiness':'Planned — not implemented'},
           {'Module':'Engagement','Readiness':'Planned — no Gallup benchmark or licensed questions'},
           {'Module':'Offboarding','Readiness':'Planned — not implemented'},
           {'Module':'SAP / email / persistent database','Readiness':'Future integration — not connected'}])

elif page=='Candidates':
    st.header('Candidate journeys')
    st.caption('Assessment comes after the technical interview and before the final behavioral interview. Select only stages actually experienced; skipped stages are allowed.')
    table([{'Demo name':x['name'],'Role':x['role'],'Outcome':x['outcome'],'Stages':', '.join(x['stages']),'Survey completed':x['submitted']} for x in st.session_state.candidates])
    with st.form('add_candidate'):
        st.subheader('Add a synthetic candidate')
        name=st.text_input('Demo name',placeholder='Demo Candidate D')
        role=st.text_input('Role',placeholder='QA Engineer')
        stages=st.multiselect('Stages actually experienced',STAGES,default=STAGES[:1])
        outcome=st.selectbox('Outcome',OUTCOMES)
        add=st.form_submit_button('Add candidate',type='primary')
        if add:
            if not name.strip() or not role.strip():
                st.error('Enter a demo name and role.')
            else:
                st.session_state.candidates.append({'id':uuid4().hex,'name':name.strip(),'role':role.strip(),'stages':[s for s in STAGES if s in stages],'outcome':outcome,'submitted':False})
                st.rerun()
    editable=[x for x in st.session_state.candidates if not x['submitted']]
    if editable:
        with st.expander('Update an unfinished demo journey'):
            selected=st.selectbox('Candidate',range(len(editable)),format_func=lambda i:editable[i]['name'])
            candidate=editable[selected]
            with st.form('edit_'+candidate['id']):
                stages=st.multiselect('Experienced stages',STAGES,default=candidate['stages'])
                outcome=st.selectbox('Current outcome',OUTCOMES,index=OUTCOMES.index(candidate['outcome']))
                if st.form_submit_button('Save journey'):
                    candidate.update(stages=[s for s in STAGES if s in stages],outcome=outcome)
                    st.rerun()

elif page=='Survey studio':
    st.header('Survey studio')
    st.caption('Surveys open only for closed demo journeys (no survey for an in-progress application). Send the full journey, or preview a single 8-question stage block. This screen is an HR demonstration, not a public candidate portal.')
    candidates=st.session_state.candidates
    if not candidates:
        st.info('Add a demo candidate first.')
    else:
        idx=st.selectbox('Select demo journey',range(len(candidates)),format_func=lambda i:candidates[i]['name']+' · '+candidates[i]['outcome'])
        candidate=candidates[idx]
        if not eligible(candidate):
            st.warning('Survey unavailable: the journey is still in progress.')
        else:
            scope=st.selectbox('Survey scope',['full']+stage_options(candidate),format_func=lambda x:'Full journey (all experienced stages)' if x=='full' else 'Stage block only: '+x,key='scope_'+candidate['id'])
            pulses=candidate.setdefault('pulses',[])
            done=candidate['submitted'] if scope=='full' else scope in pulses
            rejected=candidate['outcome']=='Rejection sent'
            if done:
                st.success('This survey scope already has a response. See Insights and Action plans.')
            else:
                st.warning('Rejection pathway demo: respondent name is omitted from the response record. This is NOT guaranteed anonymity: HR operates this shared demo session and can infer the person. Do not collect real candidate responses here.' if rejected else 'Identified pathway: the demo candidate name will appear with the response. Participation is voluntary.')
                with st.expander('Email preview — not sent'):
                    st.write('Subject: Tell us about your recruitment experience')
                    st.write('Thank you for your time. We invite you to share feedback on the stages you experienced. Participation is optional. This demonstration does not send messages or create a public survey link.')
                answers={}
                aware='—'
                if scope=='full':
                    aware_options=['—','نعم','لا','غير متأكد'] if lang=='ar' else ['—','Yes','No','Unsure']
                    aware=st.selectbox(qtext(questions['B02'],lang),aware_options,key='aware_'+candidate['id']+'_'+lang)
                    if aware!='—':
                        answers['B02']=aware
                ids=route(candidate,aware in ['Yes','نعم'],scope,bank['questions'])
                st.caption(f'{len(ids)} items in this survey' + (', including the awareness question above' if scope=='full' else '') + '. All answers optional.')
                snapshot={}
                with st.form('survey_'+candidate['id']+'_'+scope+'_'+lang):
                    for key in ids:
                        q=questions[key.split('@')[0]]
                        label=qtext(q,lang)
                        snapshot[key]=label
                        if key=='B02':
                            continue
                        code=q['scale'].split(' ')[0]
                        wkey='answer_'+candidate['id']+'_'+scope+'_'+lang+'_'+key
                        if code=='TEXT':
                            value=st.text_area(label,key=wkey)
                        elif code=='REPUTATION_SOURCES' or code.endswith('_MULTI'):
                            value=st.multiselect(label,sopts(code,lang),key=wkey)
                        else:
                            if code=='LIKELIHOOD_0_10':
                                options=[str(n) for n in range(11)]
                            elif code in bank['scales']:
                                options=sopts(code,lang)
                            else:
                                options=sopts('QUALITY',lang)
                            if key=='C01':
                                options+=['لم تصلني تحديثات' if lang=='ar' else 'No updates received']
                            options+=['لا ينطبق / لا أتذكر / أفضل عدم الإجابة' if lang=='ar' else 'Not applicable / Cannot recall / Prefer not to answer']
                            value=st.selectbox(label,['—']+options,key=wkey)
                        if value and value!='—':
                            answers[key]=value
                    submit=st.form_submit_button('حفظ الإجابة التجريبية' if lang=='ar' else 'Save demo response',type='primary')
                if submit:
                    meaningful={k:v for k,v in answers.items() if not (isinstance(v,str) and ('Prefer not to answer' in v or 'أفضل عدم الإجابة' in v))}
                    if not meaningful:
                        st.warning('No substantive answers to save. Participation is optional; you may leave this page.')
                    else:
                        rid=uuid4().hex
                        st.session_state.responses.append(response_record(candidate,answers,snapshot,rid,scope))
                        if scope=='full':
                            candidate['submitted']=True
                        else:
                            pulses.append(scope)
                        for proposal in suggest(answers,extra_rules()):
                            st.session_state.actions.append(dict(proposal,id=uuid4().hex,response_id=rid))
                        st.success('Response saved. Open Insights or Action plans from the sidebar.')

elif page=='Insights':
    st.header('Experience insights')
    selected=st.selectbox('Outcome segment',['All']+OUTCOMES[1:])
    responses=[r for r in st.session_state.responses if selected=='All' or r['outcome']==selected]
    satisfaction=[numeric(r['answers'].get('G01')) for r in responses]
    satisfaction=[n for n in satisfaction if n is not None]
    advocacy=[numeric(r['answers'].get('G02')) for r in responses]
    advocacy=[n for n in advocacy if n is not None]
    a,b,c=st.columns(3)
    a.metric('Responses',len(responses))
    b.metric('Satisfaction / 5',f'{sum(satisfaction)/len(satisfaction):.1f}' if satisfaction else '—',help=f'Valid answers: {len(satisfaction)}')
    c.metric('Candidate advocacy',f'{100*(sum(n>=9 for n in advocacy)-sum(n<=6 for n in advocacy))/len(advocacy):.0f}' if advocacy else '—',help=f'% 9–10 minus % 0–6. Valid answers: {len(advocacy)}. Not employee eNPS.')
    st.caption('Descriptive demo results; no external benchmarks or causal claims. Outcome groups may differ systematically. Missing and non-numeric answers are excluded from scores.')
    grouped={}
    for r in responses:
        for key,value in r['answers'].items():
            score=numeric(value)
            scale=questions.get(key.split('@')[0],{}).get('scale')
            if score is not None and (str(scale).startswith('RATING_') or scale in ['QUALITY','CLARITY','EASE','IMPRESSION','OPPORTUNITY','RELEVANCE','REASONABLENESS','SUFFICIENCY','SATISFACTION','WILLINGNESS','PREPARED','AGREEMENT','COMFORT']):
                grouped.setdefault(key,[]).append(score)
    if grouped:
        import pandas as pd
        rows=[{'Question':k,'Mean / 5':round(sum(v)/len(v),2),'Valid answers':len(v)} for k,v in grouped.items()]
        st.bar_chart(pd.DataFrame(rows).set_index('Question')['Mean / 5'],color='#3157d5')
        table(rows)
    for r in responses:
        with st.expander(r['outcome']+' · '+(r['respondent'] or 'Name omitted — demo only')):
            table([{'Question':r['questions'].get(k,k),'Answer':', '.join(v) if isinstance(v,list) else v} for k,v in r['answers'].items()])

elif page=='Action plans':
    st.header('Turn feedback into an owned action')
    st.caption('Rule-based suggestions, not AI-generated or validated conclusions. Scores 1–2 on selected questions trigger review; HR decides whether action is warranted. No messages or tasks are sent externally.')
    actions=st.session_state.actions
    if not actions:
        st.info('Submit a survey with a low score on communication, waiting time, assessment, interviews or offer clarity to see suggestions.')
    for action in actions:
        with st.expander(action['theme']+' · '+action['status'],expanded=True):
            st.caption('Evidence: '+action['source_question']+' → '+action['evidence'])
            with st.form('action_'+action['id']):
                task=st.text_area('Action to review',action['action'])
                owner=st.text_input('Responsible owner — demo assignment',action['owner'])
                due=st.date_input('Target date',date.fromisoformat(action['due']))
                statuses=['Proposed','Approved','In progress','Completed','Dismissed']
                status=st.selectbox('Status',statuses,index=statuses.index(action['status']))
                if st.form_submit_button('Save action'):
                    if not task.strip() or not owner.strip():
                        st.error('Keep an action description and responsible owner.')
                    else:
                        action.update(action=task.strip(),owner=owner.strip(),due=str(due),status=status)
                        st.rerun()

elif page=='Question bank':
    st.header('Question builder')
    st.caption(f'{len(questions)} questions. Add, edit, reorder or delete questions in English and choose the answer type, like a form builder. Changes last for this browser session: download the question bank when you are done and replace question_bank.json in GitHub to keep them.')
    LOCKED=['B02','G01','G02']
    ANSWER_TYPES=['Rating (1–5)','Yes / No','Yes / No / Unsure','Single choice (pick one)','Multiple choice (select all)','Score 0–10','Text answer']
    WHERES=list(PREFIX)+[EXTRA]
    where_label=lambda x:'End of survey (additional question)' if x==EXTRA else 'Stage block: '+x
    flash=st.session_state.pop('builder_flash',None)
    if flash:
        st.success(flash)
    tab_add,tab_edit,tab_manage,tab_io=st.tabs(['Add question','Edit wording','Manage · reorder · delete','Import / export'])

    with tab_add:
        n=st.session_state.setdefault('builder_n',0)
        where=st.selectbox('Where should it appear?',WHERES,format_func=where_label,key=f'nb_where_{n}')
        text=st.text_area('Question (English)',key=f'nb_text_{n}')
        kind=st.selectbox('Answer type',ANSWER_TYPES,key=f'nb_kind_{n}')
        low=high=''
        options=[]
        if kind=='Rating (1–5)':
            c1,c2=st.columns(2)
            low=c1.text_input('Label for 1 (optional)',placeholder='Very poor',key=f'nb_low_{n}').strip()
            high=c2.text_input('Label for 5 (optional)',placeholder='Excellent',key=f'nb_high_{n}').strip()
            options=['1 '+low if low else '1','2','3','4','5 '+high if high else '5']
        elif kind in ['Single choice (pick one)','Multiple choice (select all)']:
            raw=st.text_area('Answer options — one per line',key=f'nb_opts_{n}')
            options=[o.strip() for o in raw.splitlines() if o.strip()]
        elif kind=='Yes / No':
            options=['Yes','No']
        elif kind=='Yes / No / Unsure':
            options=['Yes','No','Unsure']
        elif kind=='Score 0–10':
            options=[str(i) for i in range(11)]
        st.caption('Preview — answers are always optional, and a "Not applicable / Cannot recall" option is added automatically.')
        label=text.strip() or 'Your question will appear here'
        if kind=='Text answer':
            st.text_area(label,disabled=True,key=f'nb_prev_{n}')
        elif kind=='Multiple choice (select all)':
            st.multiselect(label,options,disabled=True,key=f'nb_prev_{n}')
        else:
            st.selectbox(label,['—']+options,disabled=True,key=f'nb_prev_{n}')
        use_rule=False
        triggers=[]
        theme=task=owner=''
        if kind in ['Rating (1–5)','Yes / No','Yes / No / Unsure','Single choice (pick one)']:
            use_rule=st.checkbox('Propose an action plan item for certain answers',key=f'nb_rule_{n}')
            if use_rule:
                if kind=='Rating (1–5)':
                    st.caption('Triggers when the score is 1 or 2.')
                elif kind=='Yes / No':
                    triggers=[st.radio('Trigger when the answer is',['No','Yes'],horizontal=True,key=f'nb_trig_{n}')]
                elif kind=='Yes / No / Unsure':
                    triggers=st.multiselect('Trigger on these answers',['No','Unsure','Yes'],default=['No'],key=f'nb_trig_{n}')
                else:
                    triggers=st.multiselect('Trigger on these answers',options,key=f'nb_trig_{n}')
                theme=st.text_input('Action theme',placeholder='e.g. Office supplies',key=f'nb_theme_{n}').strip()
                task=st.text_area('Proposed action',key=f'nb_task_{n}').strip()
                owner=st.text_input('Responsible owner',value='HR officer',key=f'nb_owner_{n}').strip()
        if st.button('Add question',type='primary',key=f'nb_add_{n}'):
            errors=[]
            if not text.strip():
                errors.append('Write the question text.')
            if kind in ['Single choice (pick one)','Multiple choice (select all)']:
                if len(options)<2:
                    errors.append('Add at least two answer options.')
                if len({o.lower() for o in options})!=len(options):
                    errors.append('Answer options must be different from each other.')
            if any('|' in x for x in options+[low,high]):
                errors.append('Do not use the | character in answer options or labels.')
            if use_rule and (not theme or not task or not owner or (kind!='Rating (1–5)' and not triggers)):
                errors.append('Complete the action fields and choose at least one trigger answer.')
            over=sum(q['stage']==where for q in bank['questions'])>=8 and where!=EXTRA
            if errors:
                st.error(' '.join(errors))
            else:
                prefix=PREFIX.get(where,'X')
                nums=[int(q['id'][1:]) for q in bank['questions'] if q['id'][:1]==prefix and q['id'][1:].isdigit()]
                qid=f'{prefix}{max(nums,default=0)+1:02d}'
                if kind=='Rating (1–5)':
                    scale='RATING_'+qid
                    bank['scales'][scale]={'ar':' | '.join(options),'en':' | '.join(options),'notes':'Custom rating added in the app.'}
                elif kind in ['Single choice (pick one)','Multiple choice (select all)']:
                    scale='CHOICE_'+qid+('_MULTI' if kind.startswith('Multiple') else '')
                    bank['scales'][scale]={'ar':' | '.join(options),'en':' | '.join(options),'notes':'Custom options added in the app.'}
                else:
                    scale={'Yes / No':'YES_NO','Yes / No / Unsure':'YES_NO_UNSURE','Score 0–10':'LIKELIHOOD_0_10','Text answer':'TEXT'}[kind]
                new_q={'id':qid,'stage':where,'use':'Custom','ar':'','en':text.strip(),'scale':scale,'condition':'Added in the app','action':task,'source':'Added by user in the app'}
                if use_rule:
                    expand={'Yes':['Yes','نعم'],'No':['No','لا'],'Unsure':['Unsure','غير متأكد']}
                    trig=[v for t in triggers for v in expand.get(t,[t])] if kind!='Rating (1–5)' else []
                    new_q['rule']={'theme':theme,'action':task,'owner':owner,'triggers':trig,'low_score':kind=='Rating (1–5)'}
                bank['questions'].append(new_q)
                st.session_state.builder_n=n+1
                st.session_state.builder_flash=f'Added {qid} to {where_label(where)}.'+(' This block now has more than 8 questions; consider trimming.' if over else '')
                st.rerun()

    with tab_edit:
        qid=st.selectbox('Question to edit',list(questions),format_func=lambda k:k+' · '+questions[k]['stage']+' · '+questions[k]['en'][:60],key='edit_pick')
        q=questions[qid]
        with st.form('question_'+qid):
            en=st.text_area('English wording',q['en'])
            ar=st.text_area('Arabic wording (optional — English is shown when empty)',q.get('ar',''))
            choice_text=None
            if str(q['scale']).startswith('CHOICE_'):
                choice_text=st.text_area('Answer options — one per line',q['scale'] and '\n'.join(bank['scales'][q['scale']]['en'].split(' | ')))
            st.write('Use: '+q['use']+' · Answer type: '+q['scale'])
            st.write('Display condition: '+q['condition'])
            st.caption('Related source theme (not verbatim): '+q['source'])
            if st.form_submit_button('Save changes'):
                new_opts=[o.strip() for o in choice_text.splitlines() if o.strip()] if choice_text is not None else None
                if not en.strip():
                    st.error('English wording is required.')
                elif new_opts is not None and (len(new_opts)<2 or len({o.lower() for o in new_opts})!=len(new_opts) or any('|' in o for o in new_opts)):
                    st.error('Use at least two different answer options, without the | character.')
                else:
                    q.update(en=en.strip(),ar=ar.strip())
                    if new_opts is not None:
                        bank['scales'][q['scale']].update(en=' | '.join(new_opts),ar=' | '.join(new_opts))
                    st.success('Saved for this session. Download the question bank to keep it.')

    with tab_manage:
        groups=list(dict.fromkeys(q['stage'] for q in bank['questions']))
        table([{'Block':g,'Questions':sum(q['stage']==g for q in bank['questions']),'Note':'More than 8 — consider trimming' if g in PREFIX and sum(q['stage']==g for q in bank['questions'])>8 else ''} for g in groups])
        group=st.selectbox('Block to manage',groups,key='manage_group')
        pending=st.session_state.get('pending_delete')
        members=[q for q in bank['questions'] if q['stage']==group]
        for pos,q in enumerate(members):
            c1,c2,c3,c4=st.columns([8,1,1,1])
            c1.write(f"**{q['id']}** · {q['en']}  \n:gray[{q['scale'].split(' ')[0]}]")
            if c2.button('↑',key='up_'+q['id'],disabled=pos==0):
                a=bank['questions'].index(q); b=bank['questions'].index(members[pos-1])
                bank['questions'][a],bank['questions'][b]=bank['questions'][b],bank['questions'][a]
                st.rerun()
            if c3.button('↓',key='down_'+q['id'],disabled=pos==len(members)-1):
                a=bank['questions'].index(q); b=bank['questions'].index(members[pos+1])
                bank['questions'][a],bank['questions'][b]=bank['questions'][b],bank['questions'][a]
                st.rerun()
            if q['id'] in LOCKED:
                c4.caption('🔒')
            elif c4.button('🗑',key='del_'+q['id']):
                st.session_state.pending_delete=q['id']
                st.rerun()
        if pending and pending in questions:
            st.warning(f"Delete {pending} — “{questions[pending]['en']}”? Past responses keep their saved wording.")
            d1,d2=st.columns(2)
            if d1.button('Yes, delete it',type='primary',key='confirm_delete'):
                victim=questions[pending]
                bank['questions']=[x for x in bank['questions'] if x['id']!=pending]
                still_used={x['scale'] for x in bank['questions']}
                if str(victim['scale']).startswith(('RATING_','CHOICE_')) and victim['scale'] not in still_used:
                    bank['scales'].pop(victim['scale'],None)
                st.session_state.pending_delete=None
                st.session_state.builder_flash=f'Deleted {pending}.'
                st.rerun()
            if d2.button('Cancel',key='cancel_delete'):
                st.session_state.pending_delete=None
                st.rerun()
        st.caption('🔒 Locked questions drive the awareness gate and the satisfaction / advocacy scores, so they cannot be deleted (you can still edit their wording).')

    with tab_io:
        st.download_button('Download question bank JSON',json.dumps(bank,ensure_ascii=False,indent=2),'question_bank.json','application/json')
        st.caption('Upload the downloaded file to GitHub (replace question_bank.json) to make your changes permanent. After a refresh you can also load it back here for this session.')
        uploaded=st.file_uploader('Load a saved question bank',type=['json'],key='bank_upload')
        if uploaded is not None and st.button('Replace the current question bank with this file',key='bank_load'):
            try:
                data=json.loads(uploaded.getvalue().decode('utf-8'))
                qs=data['questions']
                scs=data['scales']
                ids=[x['id'] for x in qs]
                problems=[]
                if len(ids)!=len(set(ids)):
                    problems.append('duplicate question ids')
                if not all(k in ids for k in LOCKED):
                    problems.append('missing required questions '+', '.join(LOCKED))
                for x in qs:
                    if not all(k in x for k in ['id','stage','en','scale']) or str(x['scale']).split(' ')[0] not in scs:
                        problems.append('question '+str(x.get('id'))+' is incomplete')
                        break
                    if 'rule' in x and not all(k in x['rule'] for k in ['theme','action','owner']):
                        problems.append('question '+str(x['id'])+' has an invalid action rule')
                        break
                if problems:
                    st.error('This file cannot be loaded: '+'; '.join(problems)+'.')
                else:
                    st.session_state.bank=data
                    st.session_state.builder_flash='Question bank loaded.'
                    st.rerun()
            except Exception:
                st.error('This file is not a valid question bank JSON.')

elif page=='Roadmap & export':
    st.header('Presentation pack & integration roadmap')
    st.markdown('''**Working now:** synthetic candidate journeys; outcome-based survey routing; bilingual questions; session responses; descriptive insights; rule-based actions; editable owners and statuses.

**Not implemented:** durable storage, multi-user synchronization, real identity separation, public respondent links, email delivery, scheduled sends, SAP integration, tenant isolation, engagement benchmarks and AI generation.

**Next modules:** onboarding checkpoints at 30/60/90 days, engagement feedback and offboarding. These are planned, not working screens in this version.

**Future integration contract:** company ID, application ID, employee ID, stage-event type, occurred-at timestamp, survey version and idempotency key. Real rejection responses must be isolated from identifiable delivery records. This contract is a design proposal, not a tested SAP connector.

**Before production:** IT-approved hosting and retention, persistent database, permissions, audited anonymity design, mail provider, scheduler, backups, secure secrets and vendor-confirmed SAP APIs/licensing.
''')
    payload={'schema_version':1,'demo_only':True,'candidates':st.session_state.candidates,'responses':st.session_state.responses,'actions':st.session_state.actions}
    st.download_button('Download demo snapshot JSON',json.dumps(payload,ensure_ascii=False,indent=2),'peoplepulse_demo_snapshot.json','application/json')
    output=io.StringIO()
    writer=csv.writer(output)
    writer.writerow(['theme','action','owner','due','status'])
    def safe_csv(value):
        value=str(value)
        return "'"+value if value.lstrip().startswith(('=','+','-','@')) else value
    for action in st.session_state.actions:
        writer.writerow([safe_csv(action[k]) for k in ['theme','action','owner','due','status']])
    st.download_button('Download action plan CSV',output.getvalue().encode('utf-8-sig'),'peoplepulse_actions.csv','text/csv')
    st.caption('Exports are manual backups for review. This version does not restore snapshots. To retain edited question wording for future sessions, replace question_bank.json in GitHub.')
