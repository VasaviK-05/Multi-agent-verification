const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('frontend/src/App.jsx', 'utf8');
const generate = source.slice(source.indexOf('  const generateAnswer = async'), source.indexOf('  const validateAnswer = async'));
function fixture() {
  const calls = [], state = {};
  const answer = '  {"base":"29879337","derived":"29880337"}  ';
  const item = {question_id: 17, question: 'registered question', generated_answer: answer, history_state: 'generated_only'};
  const scope = { API_URL: 'http://offline.invalid', question: 'registered question',
    pendingSession: {current:null}, generationRequest:{current:null},validationRequest:{current:null},
    viewRevision:{current:1},activeSession:{current:'session-1'},questionsRevision:{current:0},
    resetConversation:()=>1,
    fetch:async (url, options)=>{calls.push({url,options});return {ok:true,json:async()=>options ? {question_id:17,answer} : [item]};},
    getResponseErrorMessage:async()=> 'safe error',
  };
  for (const name of ['Question','QuestionId','SubmittedQuestion','Answer','Generating','QuestionsLoading','SessionQuestions','Error','Context','Result','ShowResults']) {
    scope['set'+name] = value => {state[name]=value;};
  }
  vm.createContext(scope);
  vm.runInContext(generate+'; globalThis.runGeneration = generateAnswer;',scope);
  return {scope,calls,state,answer,item};
}
test('generation sends session and preserves exact JSON string while refreshing history', async()=>{
 const f=fixture();await f.scope.runGeneration();
 assert.deepEqual(JSON.parse(f.calls[0].options.body),{question:'registered question',session_id:'session-1'});
 assert.equal(f.state.Answer,f.answer);
 assert.equal(f.state.SessionQuestions[0].history_state,'generated_only');
 assert.equal(f.calls[1].url,'http://offline.invalid/sessions/session-1/questions');
 assert.equal(f.scope.generationRequest.current,null);
});
test('restoring generated-only history keeps identifiers and no validation result',()=>{
 const f=fixture(); f.scope.item=f.item;
 const start=source.indexOf('setQuestionId(item.question_id ?? null);',source.indexOf('sessionQuestions.map'));
 const end=source.indexOf('setError("");',start)+'setError("");'.length;
 vm.runInContext(source.slice(start,end),f.scope);
 assert.equal(f.state.Answer,f.answer);
 assert.equal(f.state.QuestionId,17);
 assert.equal(f.state.Result,null);
 assert.equal(f.state.ShowResults,false);
});
test('stale generation cannot update history or answer after navigation',async()=>{
 const f=fixture();let release;
 f.scope.fetch=()=>new Promise(resolve=>{release=resolve;});
 const pending=f.scope.runGeneration();f.scope.viewRevision.current++;
 release({ok:true,json:async()=>({question_id:17,answer:f.answer})});await pending;
 assert.equal(f.state.Answer,undefined);
 assert.equal(f.state.SessionQuestions,undefined);
});
