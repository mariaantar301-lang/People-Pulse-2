import csv
import io
import json
from pathlib import Path
from uuid import uuid4
from datetime import date
import streamlit as st
from domain import STAGES, OUTCOMES, route, eligible, numeric, suggest, response_record

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
    st.caption('One survey per closed demo journey. No survey for an in-progress application. This screen is an HR demonstration, not a public candidate portal.')
    candidates=st.session_state.candidates
    if not candidates:
        st.info('Add a demo candidate first.')
    else:
        idx=st.selectbox('Select demo journey',range(len(candidates)),format_func=lambda i:candidates[i]['name']+' · '+candidates[i]['outcome'])
        candidate=candidates[idx]
        if not eligible(candidate):
            st.warning('Survey unavailable: the journey is still in progress.')
        elif candidate['submitted']:
            st.success('This journey already has a response. See Insights and Action plans.')
        else:
            rejected=candidate['outcome']=='Rejection sent'
            st.warning('Rejection pathway demo: respondent name is omitted from the response record. This is NOT guaranteed anonymity: HR operates this shared demo session and can infer the person. Do not collect real candidate responses here.' if rejected else 'Identified pathway: the demo candidate name will appear with the response. Participation is voluntary.')
            with st.expander('Email preview — not sent'):
                st.write('Subject: Tell us about your recruitment experience')
                st.write('Thank you for your time. We invite you to share feedback on the stages you experienced. Participation is optional. This demonstration does not send messages or create a public survey link.')
            aware_options=['—','نعم','لا','غير متأكد'] if lang=='ar' else ['—','Yes','No','Unsure']
            aware=st.selectbox(questions['B02'][lang],aware_options,key='aware_'+candidate['id']+'_'+lang)
            ids=route(candidate,aware in ['Yes','نعم'])
            st.caption(f'{len(ids)} core/conditional items, including the awareness question above. All answers optional.')
            answers={'B02':aware} if aware!='—' else {}
            snapshot={}
            with st.form('survey_'+candidate['id']+'_'+lang):
                for key in ids:
                    q=questions[key.split('@')[0]]
                    label=q[lang]
                    if '@' in key:
                        stage=key.split('@')[1]
                        label=label.replace('[interview]',stage).replace('[المقابلة]',stage)
                    snapshot[key]=label
                    if key=='B02':
                        continue
                    code=q['scale'].split(' ')[0]
                    if code=='TEXT':
                        value=st.text_area(label,key='answer_'+candidate['id']+'_'+lang+'_'+key)
                    elif code=='REPUTATION_SOURCES':
                        value=st.multiselect(label,bank['scales'][code][lang].split(' | '),key='answer_'+candidate['id']+'_'+lang+'_'+key)
                    else:
                        if code=='LIKELIHOOD_0_10':
                            options=[str(n) for n in range(11)]
                        elif code in bank['scales']:
                            options=bank['scales'][code][lang].split(' | ')
                        else:
                            options=bank['scales']['QUALITY'][lang].split(' | ')
                        if key=='C01':
                            options+=['لم تصلني تحديثات' if lang=='ar' else 'No updates received']
                        options+=['لا ينطبق / لا أتذكر / أفضل عدم الإجابة' if lang=='ar' else 'Not applicable / Cannot recall / Prefer not to answer']
                        value=st.selectbox(label,['—']+options,key='answer_'+candidate['id']+'_'+lang+'_'+key)
                    if value and value!='—':
                        answers[key]=value
                submit=st.form_submit_button('حفظ الإجابة التجريبية' if lang=='ar' else 'Save demo response',type='primary')
            if submit:
                meaningful={k:v for k,v in answers.items() if not (isinstance(v,str) and ('Prefer not to answer' in v or 'أفضل عدم الإجابة' in v))}
                if not meaningful:
                    st.warning('No substantive answers to save. Participation is optional; you may leave this page.')
                else:
                    rid=uuid4().hex
                    st.session_state.responses.append(response_record(candidate,answers,snapshot,rid))
                    candidate['submitted']=True
                    for proposal in suggest(answers):
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
            if score is not None and scale in ['QUALITY','CLARITY','EASE','IMPRESSION','OPPORTUNITY','RELEVANCE','REASONABLENESS','SUFFICIENCY','SATISFACTION','WILLINGNESS']:
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
    st.header('Your editable question library')
    st.caption('47 original bilingual questions. The survey currently uses the core route; optional items remain in the library. Editing wording applies to future responses in this session; previous response wording is preserved.')
    qid=st.selectbox('Question',list(questions),format_func=lambda k:k+' · '+questions[k]['stage'])
    q=questions[qid]
    with st.form('question_'+qid):
        ar=st.text_area('Arabic wording',q['ar'])
        en=st.text_area('English wording',q['en'])
        st.write('Use: '+q['use']+' · Scale: '+q['scale'])
        st.write('Display condition: '+q['condition'])
        st.caption('Related source theme (not verbatim): '+q['source'])
        if st.form_submit_button('Save wording'):
            if ar.strip() and en.strip():
                q.update(ar=ar.strip(),en=en.strip())
                st.success('Saved for this session. Export the question bank to retain edits.')
            else:
                st.error('Both language versions are required.')
    st.download_button('Download question bank JSON',json.dumps(bank,ensure_ascii=False,indent=2),'question_bank.json','application/json')

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
