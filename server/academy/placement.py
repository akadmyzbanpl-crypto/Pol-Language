# Original question bank. Provisional grammar/reading screening, not a validated CEFR exam.
QUESTIONS = [
(0,'She ___ a student.',['am','is','are','be'],1),
(0,'Choose the opposite of "old".',['new','late','slow','long'],0),
(0,'I have two ___.',['child','childs','children','childes'],2),
(0,'They ___ football every Friday.',['plays','play','playing','played now'],1),
(1,'We ___ to the cinema yesterday.',['go','going','went','gone'],2),
(1,'There is ___ milk in the fridge.',['some','many','a','any of'],0),
(1,'This book is ___ than that one.',['interesting','most interesting','more interesting','interest'],2),
(1,'I am interested ___ learning English.',['on','at','in','for'],2),
(2,'I have lived here ___ 2020.',['for','since','during','at'],1),
(2,'If it rains, we ___ at home.',['will stay','stayed','would stayed','staying'],0),
(2,'The letter ___ yesterday.',['sent','was sent','has send','is sending'],1),
(2,'The train had already left when I arrived. What happened first?',['I arrived','The train left','Both happened together','We cannot tell'],1),
(3,'If I ___ more time, I would learn another language.',['have','had','will have','having'],1),
(3,'She suggested ___ earlier.',['leave','to leaving','leaving','left'],2),
(3,'Despite ___ tired, he finished the report.',['be','was','being','is'],2),
(3,'"The findings are tentative." This means they are ___.',['final','provisional','unrelated','identical'],1),
(4,'Had I known about the delay, I ___ later.',['would have left','will leave','have left','would leaving'],0),
(4,'Not only ___ the task, but she also improved the process.',['she completed','did she complete','she did complete','completed she'],1),
(4,'The evidence is compelling, ___ not conclusive.',['albeit','because','therefore','unless'],0),
(4,'"His account was corroborated." It was ___.',['contradicted','supported by other evidence','forgotten','shortened'],1),
]
LEVELS=['A1','A2','B1','B2','C1']

def next_question(answers):
    used={a['q'] for a in answers}
    difficulty=1
    if answers:
        last=answers[-1]
        difficulty=max(0,min(4,QUESTIONS[last['q']][0]+(1 if last['correct'] else -1)))
    candidates=[i for i in range(len(QUESTIONS)) if i not in used]
    return min(candidates,key=lambda i:abs(QUESTIONS[i][0]-difficulty))

def result(answers):
    correct=[QUESTIONS[a['q']][0] for a in answers if a['correct']]
    score=round(len(correct)/len(answers)*100)
    band=0
    # Require at least two correct answers at a band to suggest it.
    for level in range(5):
        if sum(d>=level for d in correct)>=2: band=level
    return score,LEVELS[band]
