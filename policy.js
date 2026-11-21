"use strict";

const catalog = [
  {title:"Tiny kitchen, big mess", topic:"Comedy", engagement:.98, learn:.09, relax:.98, explore:.29},
  {title:"Commuter comedy", topic:"Comedy", engagement:.95, learn:.10, relax:.89, explore:.25},
  {title:"A very stubborn cat", topic:"Comedy", engagement:.92, learn:.09, relax:.86, explore:.20},
  {title:"Why suspension cables sag", topic:"Engineering", engagement:.61, learn:.91, relax:.36, explore:.74},
  {title:"Where bridge vibrations come from", topic:"Engineering", engagement:.59, learn:.90, relax:.25, explore:.66},
  {title:"Map a city by its rivers", topic:"Geography", engagement:.65, learn:.92, relax:.49, explore:.98},
  {title:"A quiet walk along the coast", topic:"Nature", engagement:.73, learn:.27, relax:.92, explore:.76}
];

const recovery = [-.61,-.69,-.52,-.42,-.25,-.04,.17,.32,.51,.53,.65,.72];
const flat = [-.61,-.69,-.52,-.43,-.47,-.46,-.44,-.50,-.48,-.40,-.48,-.47];

function makeTrace(values, qualityFrom = Infinity, degradedQuality = .28) {
  return values.map((value, index) => ({
    value,
    quality: value === null ? 0 : index >= qualityFrom ? degradedQuality : .9
  }));
}

const scenarios = {
  recovery: makeTrace(recovery),
  flat: makeTrace(flat),
  dropout: makeTrace([...recovery.slice(0, 8), null, null, null, null]),
  artifact: makeTrace([...flat.slice(0, 8), .58, .64, .62, .66], 8)
};

function signalPolicy(samples, enabled, feedback, { minQuality = .65 } = {}) {
  if (!enabled) return {adjustment:0, reason:"Signal off. Ranking uses goals and explicit feedback."};
  if (feedback !== 0) return {adjustment:0, reason:"Explicit feedback takes precedence over the signal."};
  if (samples.length < 6) return {adjustment:0, reason:"Collecting two three-window segments."};
  const early = samples.slice(0,3);
  const recent = samples.slice(-3);
  if ([...early,...recent].some(sample => !Number.isFinite(sample.value) || !Number.isFinite(sample.quality) || sample.quality < minQuality)) {
    return {adjustment:0, reason:"Signal unavailable or below the quality threshold. Using goal-based ranking."};
  }
  const mean = values => values.reduce((sum, sample) => sum + sample.value,0) / values.length;
  const delta = mean(recent) - mean(early);
  if (delta >= .35) return {adjustment:.16, reason:"Sustained recovery in the synthetic trace. Applying a small topic boost."};
  return {adjustment:0, reason:"No sustained recovery. Keeping the goal-based order."};
}

function rankItems(items, goal, feedback, adjustment) {
  const topicAdjustment = feedback === 0 ? adjustment : feedback * .28;
  const ranked = items.map(item => {
    const base = .25 * item.engagement + .75 * item[goal];
    const change = item.topic === "Engineering" ? topicAdjustment : 0;
    return {...item, score:base + change, change};
  }).sort((a,b) => b.score - a.score);
  const top = ranked.slice(0,3);
  if (top.length === 3 && top.every(item => item.topic === top[0].topic)) {
    const alternative = ranked.slice(3).find(item => item.topic !== top[0].topic && item.score >= top[2].score - .15);
    if (alternative) top[2] = {...alternative, diversity:true};
  }
  return top;
}

if (typeof module !== "undefined") {
  module.exports = { catalog, scenarios, signalPolicy, rankItems };
}
