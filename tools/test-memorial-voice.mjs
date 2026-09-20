/* Deterministic controller tests; no browser, speech service or dependencies required.
   Run: node --test tools/test-memorial-voice.mjs
   These tests simulate native API events; they do not certify an installed device voice. */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../memorial-voice.js', import.meta.url), 'utf8');
function setup(t, initialVoices = [], mode = 'native') {
  const calls = [], states = [], selections = [], timers = new Map(), listeners = new Map();
  let id = 0, voices = initialVoices, queue = [];
  const synth = {
    paused: false, speaking: false, pending: false,
    getVoices() { return voices; },
    addEventListener(name, fn) { listeners.set(name, fn); },
    removeEventListener(name) { listeners.delete(name); },
    speak(utterance) { calls.push(['speak', utterance]); queue.push(utterance); this.pending = true; },
    cancel() { calls.push(['cancel']); queue = []; this.pending = this.speaking = false; },
    pause() {
      calls.push(['pause']); this.paused = mode === 'native';
      if (mode === 'cancel-on-pause') { const current = queue[0]; this.cancel(); current?.onerror?.({error: 'interrupted'}); }
    },
    resume() { calls.push(['resume']); this.paused = false; }
  };
  const win = {
    speechSynthesis: synth,
    SpeechSynthesisUtterance: class { constructor(text) { this.text = text; this.voice = null; } },
    setTimeout(fn) { timers.set(++id, fn); return id; },
    clearTimeout(key) { timers.delete(key); }
  };
  vm.runInNewContext(source, {window: win});
  const player = win.MemorialVoiceController.createSpeechPlayer((s, selection) => { states.push(s); selections.push(selection); });
  t.after(() => player.destroy());
  const spoken = () => calls.filter(c => c[0] === 'speak').map(c => c[1]);
  return {
    player, synth, calls, states, selections, listeners, timers, spoken,
    voices(next) { voices = next; listeners.get('voiceschanged')?.(); },
    start(index = 0) { const utterance = spoken()[index]; synth.speaking = true; synth.pending = false; utterance.onstart?.(); return utterance; },
    get state() { return states.at(-1) || 'idle'; }
  };
}
const message = {lang: 'zh-TW', segments: ['第一句。', '第二句。']};

test('constructing and receiving voices never starts audio', t => {
  const h = setup(t);
  h.voices([{lang: 'zh-TW'}]);
  assert.equal(h.spoken().length, 0);
  assert.equal(h.calls.length, 0);
});

test('exact locale, base locale and browser default have deterministic fallback', t => {
  const h = setup(t, [{lang: 'en-GB'}, {lang: 'zh-CN'}, {lang: 'zh-TW'}, {lang: 'en-US'}]);
  h.player.play(message); assert.equal(h.spoken()[0].voice.lang, 'zh-TW');
  h.player.play({lang: 'en-US', segments: ['Hello.']}); assert.equal(h.spoken().at(-1).voice.lang, 'en-US');
  h.voices([{lang: 'zh-CN'}, {lang: 'en-GB'}]);
  h.player.play(message); assert.equal(h.spoken().at(-1).voice.lang, 'zh-CN');
  h.player.play({lang: 'en-US', segments: ['Hello.']}); assert.equal(h.spoken().at(-1).voice.lang, 'en-GB');
  h.voices([{lang: 'ja-JP'}]); h.player.play(message);
  assert.equal(h.spoken().at(-1).voice, null);
  assert.equal(h.spoken().at(-1).lang, 'zh-TW');
});

test('an empty initial list can play immediately; delayed voices apply to the next request', t => {
  const h = setup(t);
  h.player.play(message);
  assert.equal(h.spoken().length, 2);
  assert.equal(h.spoken()[0].voice, null);
  h.voices([{lang: 'zh-TW', localService: true}]);
  assert.equal(h.spoken().length, 2);
  h.player.stop(); h.player.play(message);
  assert.equal(h.spoken().at(-1).voice.lang, 'zh-TW');
});

test('available enhanced voices outrank the first basic local voice without changing locale', t => {
  const h = setup(t, [
    {lang: 'zh-TW', name: 'Standard', localService: true, default: true},
    {lang: 'zh-TW', name: 'Narrator', voiceURI: 'device.voice.enhanced.zh-TW', localService: true},
    {lang: 'zh-CN', name: 'Narrator (Premium)', localService: true}
  ]);
  h.player.play(message);
  assert.equal(h.spoken()[0].voice.voiceURI, 'device.voice.enhanced.zh-TW');
  assert.equal(h.spoken()[0].lang, 'zh-TW');
});

test('quality hints use only available voices and do not outrank a matching locale', t => {
  const h = setup(t, [
    {lang: 'en-GB', name: 'Narrator (Premium)'},
    {lang: 'en-US', name: 'Standard', localService: true},
    {lang: 'en-US', name: 'Narrator (Natural)'}
  ]);
  h.player.play({lang: 'en-US', segments: ['Hello.']});
  assert.equal(h.spoken()[0].voice.name, 'Narrator (Natural)');
  assert.equal(h.spoken()[0].voice.lang, 'en-US');
  h.voices([{lang: 'en-US', name: 'Standard'}, {lang: 'en-GB', name: 'Narrator (Premium)'}]);
  h.player.play({lang: 'en-US', segments: ['Hello.']});
  assert.equal(h.spoken().at(-1).voice.name, 'Standard');
});

test('without quality hints, the system default is preferred within the same locale', t => {
  const h = setup(t, [
    {lang: 'zh-TW', name: 'First', localService: true},
    {lang: 'zh-TW', name: 'Preferred', localService: true, default: true}
  ]);
  h.player.play(message);
  assert.equal(h.spoken()[0].voice.name, 'Preferred');
  assert.equal(h.spoken().length, 2);
});

test('all short paragraphs use quiet parameters and are queued in order', t => {
  const h = setup(t); h.player.play(message);
  assert.deepEqual(h.spoken().map(u => u.text), message.segments);
  for (const u of h.spoken()) {
    assert.equal(u.rate, 0.95); assert.equal(u.pitch, 1); assert.equal(u.volume, 0.8);
  }
  h.start(); h.player.pause(); assert.equal(h.state, 'paused');
  h.player.resume(); assert.equal(h.state, 'playing');
  assert.equal(h.spoken().length, 2, 'native resume must not queue duplicates');
  assert.equal(h.calls.filter(c => c[0] === 'resume').length, 1);
});

test('a known Taiwanese male voice wins over a higher-quality female in the same locale', t => {
  const h = setup(t, [
    {lang: 'zh-TW', name: 'Female narrator (Premium)', default: true},
    {lang: 'zh-TW', name: 'Microsoft Zhiwei', localService: true},
    {lang: 'zh-TW', name: 'Microsoft YunJhe Online (Natural)'}
  ]);
  h.player.play(message);
  assert.equal(h.spoken()[0].voice.name, 'Microsoft YunJhe Online (Natural)');
  assert.equal(h.spoken()[0].rate, 0.93);
  assert.equal(h.spoken()[0].pitch, 1, 'do not lower a female voice to imitate a male voice');
  assert.equal(h.selections.at(-1).male, true);
});

test('explicit male URI tokens are recognized without assuming an Apple voice name', t => {
  const h = setup(t, [
    {lang: 'zh-TW', name: 'Other', voiceURI: 'device.siri_female_zh-TW', default: true},
    {lang: 'zh-TW', name: 'Installed voice', voiceURI: 'device.siri_male_zh-TW'}
  ]);
  h.player.play(message);
  assert.equal(h.spoken()[0].voice.voiceURI, 'device.siri_male_zh-TW');
  assert.equal(h.selections.at(-1).male, true);
});

test('female labels and unspecified voices never get reported as confirmed male', t => {
  const h = setup(t, [{lang: 'zh-TW', name: 'Female narrator', voiceURI: 'device_female_voice'}]);
  h.player.play(message);
  assert.equal(h.selections.at(-1).male, false);
  assert.equal(h.spoken()[0].rate, 0.95);
  assert.equal(h.spoken()[0].pitch, 1);
  h.voices([{lang: 'zh-TW', name: 'Unknown voice'}]); h.player.play(message);
  assert.equal(h.selections.at(-1).male, false);
  h.voices([]); h.player.play(message);
  assert.equal(h.selections.at(-1).male, false);
  assert.equal(h.spoken().at(-1).voice, null);
});

test('the male preference never substitutes the wrong language or region', t => {
  const h = setup(t, [
    {lang: 'en-US', name: 'Microsoft Guy Online (Natural)'},
    {lang: 'zh-CN', name: 'Microsoft Yunxi Online (Natural)'},
    {lang: 'zh-TW', name: 'Female narrator'}
  ]);
  h.player.play(message);
  assert.equal(h.spoken()[0].voice.lang, 'zh-TW');
  assert.equal(h.selections.at(-1).male, false);
  h.player.play({lang: 'en-US', segments: ['Hello.']});
  assert.equal(h.spoken().at(-1).voice.name, 'Microsoft Guy Online (Natural)');
  assert.equal(h.selections.at(-1).male, true);
  h.player.stop(); assert.equal(h.selections.at(-1), null);
});

test('an asynchronously installed male voice applies only to the next user request', t => {
  const h = setup(t, []); h.player.play(message); h.start();
  h.voices([{lang: 'zh-TW', name: 'Microsoft Zhiwei'}]);
  assert.equal(h.spoken().length, 2);
  assert.equal(h.selections.at(-1).male, false);
  h.player.play(message);
  assert.equal(h.spoken().at(-1).voice.name, 'Microsoft Zhiwei');
  assert.equal(h.selections.at(-1).male, true);
});

test('mobile engines that cancel on pause resume from a real boundary', t => {
  const h = setup(t, [], 'cancel-on-pause'); h.player.play(message);
  const u = h.start(); u.onboundary({charIndex: 1});
  h.player.pause(); assert.equal(h.state, 'paused');
  h.player.resume();
  assert.equal(h.spoken().at(-2).text, '一句。');
  assert.equal(h.spoken().at(-1).text, '第二句。');
});

test('pausing before the first voice starts preserves startup failure handling', t => {
  const h = setup(t); h.player.play(message); h.player.pause();
  assert.equal(h.state, 'paused');
  h.player.resume();
  assert.equal(h.state, 'starting');
  assert.equal(h.spoken().length, 2, 'pending narration must not be queued twice');
  for (const fn of h.timers.values()) fn();
  assert.equal(h.state, 'error', 'a silent engine must not leave a false playing state');
  h.player.play(message); h.start(h.spoken().length - message.segments.length);
  assert.equal(h.state, 'playing');
});

test('a native pause no-op is canceled safely and resumes the current paragraph', t => {
  const h = setup(t, [], 'ignored-pause'); h.player.play(message); h.start();
  const before = h.calls.filter(c => c[0] === 'cancel').length;
  h.player.pause();
  assert.equal(h.state, 'paused');
  assert.ok(h.calls.filter(c => c[0] === 'cancel').length > before);
  h.player.resume(); assert.equal(h.spoken().at(-2).text, '第一句。');
});

test('replay cancels its old queue and stale end/error callbacks cannot change its state', t => {
  const h = setup(t); h.player.play(message);
  const old = h.start(), staleEnd = old.onend, staleError = old.onerror;
  h.player.play(message);
  staleEnd(); staleError({error: 'interrupted'});
  assert.equal(h.state, 'starting');
  assert.equal(h.spoken().length, 4);
  assert.equal(h.calls.at(-3)[0], 'cancel');
});

test('only the last paragraph completes playback; a completed narration can replay', t => {
  const h = setup(t); h.player.play(message);
  h.start(0).onend(); assert.notEqual(h.state, 'ended');
  h.start(1).onend(); assert.equal(h.state, 'ended');
  h.player.play(message); assert.equal(h.state, 'starting');
  assert.equal(h.spoken().at(-2).text, '第一句。');
});

test('stop cancels pending/paused speech and ignores late events', t => {
  const h = setup(t); h.player.play(message);
  const u = h.start(), onend = u.onend; h.player.pause(); h.player.stop();
  assert.equal(h.state, 'idle'); assert.equal(h.synth.pending, false);
  onend(); assert.equal(h.state, 'idle');
  const before = h.spoken().length; h.player.resume(); assert.equal(h.spoken().length, before);
});

test('native error and silent startup failures remain retryable', t => {
  const h = setup(t); h.player.play(message);
  h.spoken()[0].onerror({error: 'voice-unavailable'}); assert.equal(h.state, 'error');
  h.player.play(message); assert.equal(h.state, 'starting');
  for (const fn of h.timers.values()) fn();
  assert.equal(h.state, 'error');
  h.player.play(message); assert.equal(h.state, 'starting');
});

test('destroy cancels speech, removes listeners and cannot resume later', t => {
  const h = setup(t); h.player.play(message); h.player.destroy();
  assert.equal(h.listeners.size, 0); assert.equal(h.timers.size, 0);
  const before = h.spoken().length;
  h.player.play(message); h.player.resume(); assert.equal(h.spoken().length, before);
});

test('missing API does not throw or require voice UI', () => {
  const win = {};
  vm.runInNewContext(source, {window: win});
  const player = win.MemorialVoiceController.createSpeechPlayer(() => {});
  assert.equal(player.supported, false);
  assert.doesNotThrow(() => { player.stop(); player.destroy(); });
});
