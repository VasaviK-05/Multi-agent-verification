// Display only: this does not classify, register, validate or authorize requests.
// Never use these rows to update answer state or construct an API payload.
const DECIMAL = "-?(?:0|[1-9][0-9]{0,14})(?:\\.[0-9]{1,6})?";
const decimalValue = new RegExp(`^${DECIMAL}$`);
const factPlusQuestion = new RegExp(
  `^What is the (population|area) of ([A-Za-z][A-Za-z '\\-]{0,79}), and what is that \\1 plus (${DECIMAL})( square kilometres)?\\? Give both values\\.$`,
  "i",
);

const groupDecimal = (text) => {
  // Group the original decimal digits without Number conversion or rounding.
  const [whole, fraction] = text.split(".");
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return fraction === undefined ? grouped : `${grouped}.${fraction}`;
};

export const getAnswerPresentation = (question, answer) => {
  if (typeof question !== "string" || typeof answer !== "string") return null;
  const match = factPlusQuestion.exec(question.trim());
  if (!match || Boolean(match[4]) !== (match[1].toLowerCase() === "area")) return null;
  let fields;
  try {
    fields = JSON.parse(answer);
  } catch {
    return null;
  }
  if (!fields || Array.isArray(fields) || typeof fields !== "object") return null;
  const keys = Object.keys(fields);
  if (keys.length !== 2 || !keys.includes("base") || !keys.includes("derived")) return null;
  if (![fields.base, fields.derived].every(value => typeof value === "string" && decimalValue.test(value))) return null;
  // JSON.parse alone accepts duplicate keys; those are not the known structure.
  if ((answer.match(/"(?:base|derived)"\s*:/g) || []).length !== 2) return null;
  const measure = match[1].toLowerCase() === "population" ? "Population" : "Area";
  const units = match[4] ? " square kilometres" : "";
  return [
    { label: `${measure} of ${match[2]}${units ? " (square kilometres)" : ""}`, value: groupDecimal(fields.base) },
    { label: `${measure} after adding ${groupDecimal(match[3])}${units}`, value: groupDecimal(fields.derived) },
  ];
};
