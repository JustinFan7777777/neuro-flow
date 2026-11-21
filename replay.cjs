"use strict";

const assert = require("node:assert/strict");
const { catalog, scenarios, signalPolicy, rankItems } = require("./policy.js");

const cases = {
  ...scenarios,
  artifactWithHighReportedQuality: scenarios.artifact.map(sample => ({ ...sample, quality: .9 })),
  recoveryWithLowReportedQuality: scenarios.recovery.map(sample => ({ ...sample, quality: .28 }))
};

function topTitle(adjustment, feedback = 0) {
  return rankItems(catalog, "learn", feedback, adjustment)[0].title;
}

const baseline = topTitle(0);

function runTrace(samples, minQuality) {
  const choices = [];
  for (let end = 1; end <= samples.length; end++) {
    const policy = signalPolicy(samples.slice(0, end), true, 0, { minQuality });
    choices.push(topTitle(policy.adjustment));
  }
  const firstChange = choices.findIndex(title => title !== baseline);
  return {
    changedWindows: choices.filter(title => title !== baseline).length,
    firstChangeSecond: firstChange === -1 ? null : firstChange,
    finalTop: choices.at(-1)
  };
}

const results = Object.entries(cases).map(([scenario, samples]) => {
  for (let end = 1; end <= samples.length; end++) {
    const prefix = samples.slice(0, end);
    assert.equal(signalPolicy(prefix, false, 0).adjustment, 0);
    for (const feedback of [-1, 1]) {
      assert.equal(signalPolicy(prefix, true, feedback).adjustment, 0);
      assert.equal(topTitle(.16, feedback), topTitle(0, feedback));
    }
  }
  return { scenario, gated: runTrace(samples, .65), ungated: runTrace(samples, 0) };
});

console.log(JSON.stringify({
  input: "Deterministic synthetic traces with one window per simulated second",
  goal: "learn",
  baselineTop: baseline,
  windowsPerScenario: scenarios.recovery.length,
  results
}, null, 2));
