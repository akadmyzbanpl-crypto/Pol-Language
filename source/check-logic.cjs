// Focused checks of actual filter, adaptive placement and routing decisions.
const assert = require('node:assert/strict');
const logic = require('../public_html/assets/site.js');
const config = require('./site-config.json');
assert.equal(logic.filterCourses(config.courses, 'آیلتس', '', '').length, 1);
assert.equal(logic.filterCourses(config.courses, '', 'online', '').length, 2);
assert.equal(logic.filterCourses(config.courses, '', 'onsite', 'ielts').length, 0);
assert.equal(logic.filterCourses(config.courses, 'انگليسي', '', 'general').length, 1);
for (const strategy of ['correct', 'wrong', 'mixed']) {
  const answers=[];
  for (let i=0;i<12;i++) {
    const q=logic.nextQuestion(answers);
    assert.equal(answers.some(a=>a.q===q), false);
    const correct=logic.QUESTIONS[q][3];
    const choice=strategy==='correct' || (strategy==='mixed' && i%2===0) ? correct : (correct+1)%4;
    answers.push({q,choice});
  }
  const result=logic.placementResult(answers);
  assert.equal(result.score,{correct:100,wrong:0,mixed:50}[strategy]);
  if (strategy==='correct') assert.equal(result.level,'C1');
  if (strategy==='wrong') assert.equal(result.level,'A1');
  const previous=answers.pop();
  assert.equal(logic.nextQuestion(answers),previous.q);
}
assert.equal(logic.backendOrigin('https://panel.example.com','example.com'),'https://panel.example.com');
assert.equal(logic.backendOrigin('http://panel.example.com','example.com'),'');
assert.equal(logic.backendOrigin('http://localhost:8000',''), 'http://localhost:8000');
assert.equal(logic.backendOrigin('http://localhost:8000','example.com'),'');
assert.equal(logic.backendOrigin('javascript:alert(1)',''), '');
assert.equal(logic.backendOrigin('https://name:pass@example.com',''), '');
assert.equal(logic.backendOrigin('https://panel.example.com/path',''), '');
assert.equal(logic.coursePath('/courses/7/'),'/courses/7/');
assert.equal(logic.coursePath('//example.com/'),'/courses/');
assert.equal(logic.coursePath(''),'/courses/');
console.log('PASS: filtering, adaptive questions, back navigation, score and backend routing.');
