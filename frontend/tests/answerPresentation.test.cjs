const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const presentation = import("../src/answerPresentation.js");
const source = fs.readFileSync("frontend/src/App.jsx", "utf8");
const QUESTION = "What is the population of Cameroon, and what is that population plus 1000? Give both values.";
const ANSWER = ' \n{ "base":"29879337", "derived":"29880337" }\n ';

test("formats labels and digit groups without changing the answer", async () => {
  const { getAnswerPresentation } = await presentation;
  const before = ANSWER;
  const rows = getAnswerPresentation(QUESTION, ANSWER);
  assert.deepEqual(rows, [
    {label:"Population of Cameroon", value:"29,879,337"},
    {label:"Population after adding 1,000", value:"29,880,337"},
  ]);
  assert.equal(ANSWER, before);
  assert.ok(rows.every(row => !["base", "derived"].includes(row.label)));
  assert.match(source, /<strong>\{label\}:<\/strong> \{value\}/);
  assert.match(source, /\)\) : answer}/);
});

const unsupported = [
  "Paris", "864", '{"answer":"Paris"}', '{"base":1,"derived":2}',
  '{"base":"1","derived":"2","extra":"3"}',
  '{"base":"1","base":"2","derived":"3"}',
  '{"base":"1e3","derived":"2"}', '{"base":"NaN","derived":"2"}',
  '["1","2"]', 'null', '{broken',
];
for (const answer of unsupported) test(`raw fallback: ${answer}`, async () => {
  const {getAnswerPresentation} = await presentation;
  assert.equal(getAnswerPresentation(QUESTION, answer), null);
});

test("unrecognized question retains raw presentation", async () => {
  const {getAnswerPresentation} = await presentation;
  assert.equal(getAnswerPresentation("Explain these values.", ANSWER), null);
  assert.equal(getAnswerPresentation("What is the capital of Trinidad and Tobago?", ANSWER), null);
});

test("preserves decimal digits and handles the matching area unit", async () => {
  const {getAnswerPresentation} = await presentation;
  const q = "What is the area of Georgia, and what is that area plus 1000 square kilometres? Give both values.";
  const rows = getAnswerPresentation(q, '{"base":"69700.123456","derived":"70700.123456"}');
  assert.equal(rows[0].value,"69,700.123456");
  assert.equal(rows[1].value,"70,700.123456");
  assert.equal(getAnswerPresentation(q.replace(" square kilometres", ""), ANSWER), null);
});

test("validation submits the original string after presentation", async () => {
  const {getAnswerPresentation} = await presentation;
  getAnswerPresentation(QUESTION, ANSWER);
  const requests = [];
  const scope = {
    API_URL:"http://offline.invalid", question:QUESTION, answer:ANSWER, questionId:17,
    pendingSession:{current:null}, generationRequest:{current:null}, validationRequest:{current:null},
    viewRevision:{current:1}, activeSession:{current:"session-1"}, questionsRevision:{current:0},
    fetch:async (url, options) => {
      requests.push({url,options});
      return {ok:true,json:async()=> options ? {final_status:"uncertain"} : []};
    },
  };
  for (const name of ["Error","Loading","Result","ShowResults","QuestionsLoading","SessionQuestions","History"]) scope["set"+name]=()=>{};
  vm.createContext(scope);
  const body = source.slice(source.indexOf("  const validateAnswer = async"),source.indexOf("  const submitFeedback = async"));
  vm.runInContext(body+";globalThis.run = validateAnswer;",scope);
  await scope.run("");
  const payload=JSON.parse(requests[0].options.body);
  assert.equal(payload.answer,ANSWER);
  assert.equal(scope.answer,ANSWER);
  assert.equal(payload.question_id,17);
  assert.equal(payload.session_id,"session-1");
});

test("restored history formats the same exact answer without a validation result", async () => {
  const {getAnswerPresentation} = await presentation;
  const state={};
  const scope={item:{question_id:17,question:QUESTION,generated_answer:ANSWER,history_state:"generated_only"}};
  for(const name of ["QuestionId","Question","SubmittedQuestion","Answer","Context","Result","ShowResults","Error"])scope["set"+name]=value=>{state[name]=value;};
  vm.createContext(scope);
  const start=source.indexOf("setQuestionId(item.question_id ?? null);",source.indexOf("sessionQuestions.map"));
  const end=source.indexOf('setError("");',start)+'setError("");'.length;
  vm.runInContext(source.slice(start,end),scope);
  assert.equal(state.Answer,ANSWER);
  assert.equal(state.Result,null);
  assert.equal(state.ShowResults,false);
  assert.equal(getAnswerPresentation(state.SubmittedQuestion,state.Answer)[0].value,"29,879,337");
  assert.ok(source.includes('item.history_state === "generated_only"'));
  assert.ok(source.includes("Not validated"));
});
