/* Optional 921 memorial narration. No autoplay, audio files or service dependencies.
   The controller accepts a createPlayer(onStateChange) adapter so a recording-backed
   player can later implement the same play/pause/resume/stop/destroy interface. */
(function (global) {
  'use strict';

  function createSpeechPlayer(onStateChange) {
    var synth, Utterance;
    try { synth = global.speechSynthesis; Utterance = global.SpeechSynthesisUtterance; } catch (_) {}
    if (!synth || typeof Utterance !== 'function' || typeof synth.speak !== 'function' ||
        typeof synth.cancel !== 'function' || typeof synth.pause !== 'function' || typeof synth.resume !== 'function') {
      return { supported: false, stop: function () {}, destroy: function () {} };
    }
    var voices = [], utterances = [], request = null, selection = null, lastSelection = null;
    var generation = 0, part = 0, boundary = 0, state = 'idle';
    var owned = false, restartNeeded = false, destroyed = false, hasStarted = false, startTimer = null;

    function notify(next) {
      if (state !== next || selection !== lastSelection) {
        state = next; lastSelection = selection; onStateChange(next, selection);
      }
    }
    function clearTimer() { global.clearTimeout(startTimer); startTimer = null; }
    function refreshVoices() {
      try { voices = Array.from(synth.getVoices() || []); } catch (_) { voices = []; }
    }
    function isKnownMale(voice) {
      if (!voice) return false;
      // Web Speech has no gender field. Use explicit labels/URI tokens or the
      // documented Microsoft catalogue, only for voices actually enumerated.
      var raw = (voice.name || '') + ' ' + (voice.voiceURI || '');
      var identity = raw.replace(/[_-]/g, ' ');
      if (/\bfemale\b|女[聲声性]/i.test(identity)) return false;
      if (/\bmale\b|男[聲声性]/i.test(identity)) return true;
      var locale = (voice.lang || '').toLowerCase().replace(/_/g, '-');
      var microsoft = /\bmicrosoft\b/i.test(identity) || /\b(?:zh|en)-[a-z]{2}-[a-z]+Neural\b/i.test(raw);
      if (!microsoft) return false;
      if (/^zh(?:-|$)/.test(locale)) return /\b(?:zhiwei|kangkang|yunxi(?:Neural)?|yunjhe(?:Neural)?)\b/i.test(identity);
      if (/^en(?:-|$)/.test(locale)) return /\b(?:david|mark|james|richard|george|ravi|sean|guy(?:Neural)?|ryan(?:Neural)?)\b/i.test(identity);
      return false;
    }
    function voicePreference(voice) {
      // The API has no standard quality field. These are optional hints in voices
      // actually returned by the browser, never a dependency on a specific name.
      var identity = (voice.name || '') + ' ' + (voice.voiceURI || '');
      var quality = /\b(premium|natural|neural)\b/i.test(identity) ? 3 :
        /\benhanced\b/i.test(identity) ? 2 : 0;
      return (isKnownMale(voice) ? 1000 : 0) + quality * 100 +
        (voice.default ? 10 : 0) + (voice.localService ? 1 : 0);
    }
    function selectVoice(locale) {
      var exact = locale.toLowerCase(), base = exact.split('-')[0];
      var matches = function (test) {
        var list = voices.filter(function (voice) { return test((voice.lang || '').toLowerCase().replace(/_/g, '-')); });
        return list.reduce(function (preferred, voice) {
          return !preferred || voicePreference(voice) > voicePreference(preferred) ? voice : preferred;
        }, null);
      };
      return matches(function (lang) { return lang === exact; }) ||
        (base === 'zh' && matches(function (lang) { return lang.indexOf('zh-hant') === 0; })) ||
        matches(function (lang) { return lang === base || lang.indexOf(base + '-') === 0; }) || null;
    }
    function cancelQueue() {
      generation += 1;
      clearTimer();
      utterances.forEach(function (utterance) {
        utterance.onstart = utterance.onend = utterance.onerror = utterance.onboundary = null;
      });
      utterances = [];
      if (owned) { try { synth.cancel(); } catch (_) {} }
      owned = false;
    }
    function fail() { cancelQueue(); notify('error'); }
    function watchStart() {
      clearTimer();
      startTimer = global.setTimeout(function () {
        if (state === 'starting') fail();
      }, 8000);
    }
    function preservePause() {
      restartNeeded = true;
      cancelQueue();
      notify('paused');
    }
    function startFromCheckpoint() {
      cancelQueue();
      if (!request || destroyed) return;
      if (part >= request.segments.length) { notify('ended'); return; }
      refreshVoices();
      var voice = selectVoice(request.lang), token = generation;
      selection = { male: isKnownMale(voice) };
      restartNeeded = false;
      hasStarted = false;
      owned = true;
      notify('starting');
      try {
        // Clear a prior paused engine in this same user gesture, never from a timer.
        synth.cancel();
        if (synth.paused) synth.resume();
        request.segments.forEach(function (text, index) {
          if (index < part) return;
          var offset = index === part ? boundary : 0;
          var utterance = new Utterance(text.slice(offset));
          utterance.lang = request.lang;
          if (voice) utterance.voice = voice; // A missing list/name uses the browser's locale default.
          // Stay close to the engine's natural pace instead of stretching syllables.
          utterance.rate = selection.male ? 0.93 : 0.95;
          utterance.pitch = 1;
          utterance.volume = 0.8;
          utterance.onstart = function () {
            if (token !== generation || destroyed) return;
            if (state === 'paused') { preservePause(); return; }
            clearTimer();
            hasStarted = true;
            part = index; boundary = offset;
            notify('playing');
          };
          utterance.onboundary = function (event) {
            if (token !== generation || destroyed || state === 'paused') return;
            if (Number.isFinite(event.charIndex) && event.charIndex >= 0) {
              part = index; boundary = Math.min(offset + event.charIndex, text.length);
            }
          };
          utterance.onend = function () {
            if (token !== generation || destroyed) return;
            if (state === 'paused') { preservePause(); return; }
            part = index + 1; boundary = 0;
            if (part === request.segments.length) {
              clearTimer(); owned = false; utterances = []; notify('ended');
            }
          };
          utterance.onerror = function () {
            if (token !== generation || destroyed) return;
            // Some mobile engines end/cancel an utterance when paused. Keep the
            // last real boundary (or current paragraph) for a user-initiated resume.
            if (state === 'paused') { preservePause(); return; }
            fail();
          };
          utterances.push(utterance); // Retain all utterances until the native queue finishes.
        });
        watchStart();
        // Queue the entire short narration directly in the click/keyboard gesture.
        // voiceschanged only refreshes choices; it never initiates playback.
        utterances.forEach(function (utterance) {
          if (token === generation) synth.speak(utterance);
        });
      } catch (_) { fail(); }
    }
    refreshVoices();
    if (synth.addEventListener) synth.addEventListener('voiceschanged', refreshVoices);
    return {
      supported: true,
      play: function (narration) {
        if (destroyed) return;
        request = narration; part = 0; boundary = 0;
        startFromCheckpoint();
      },
      pause: function () {
        if (destroyed || (state !== 'playing' && state !== 'starting')) return;
        clearTimer(); notify('paused');
        try {
          synth.pause();
          if (!synth.paused) preservePause();
        } catch (_) { preservePause(); }
      },
      resume: function () {
        if (destroyed || state !== 'paused') return;
        if (restartNeeded || (!synth.speaking && !synth.pending)) { startFromCheckpoint(); return; }
        try {
          notify(hasStarted ? 'playing' : 'starting');
          if (!hasStarted) watchStart();
          synth.resume();
          if (synth.paused) startFromCheckpoint();
        } catch (_) { startFromCheckpoint(); }
      },
      stop: function () { cancelQueue(); request = null; selection = null; part = 0; boundary = 0; notify('idle'); },
      destroy: function () {
        if (destroyed) return;
        destroyed = true; cancelQueue(); request = null; selection = null;
        if (synth.removeEventListener) synth.removeEventListener('voiceschanged', refreshVoices);
      }
    };
  }

  function englishYears(number) {
    var small = ['zero','one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen'];
    var tens = ['', '', 'twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety'];
    var word = number < 20 ? small[number] : number < 100 ? tens[Math.floor(number / 10)] + (number % 10 ? '-' + small[number % 10] : '') : String(number);
    return word.charAt(0).toUpperCase() + word.slice(1);
  }
  function narration(language, years, yearsZh) {
    return language === 'en' ? { lang: 'en-US', segments: [
      'On September 21, 1999, Taiwan was struck by the Chi-Chi earthquake.',
      englishYears(years) + ' years later, we still remember that day.',
      'We remember the past so that we can be better prepared for the next one.',
      'That is the question LinkGuard seeks to answer:',
      'When disaster strikes, when communications fail, can we still send the signal, and find the people who need us?'
    ] } : { lang: 'zh-TW', segments: [
      // Spoken form only: read the year as digits, without changing visible copy.
      '一九九九年九月二十一日，台灣發生了九二一集集大地震。',
      yearsZh + '年後，我們仍然記得那一天。',
      '而記住，是為了讓下一次的我們準備得更好。',
      '這也是 LinkGuard 想回答的問題：',
      '當災害發生，當通訊中斷，我們還能不能把訊號送出去，把人找回來？'
    ] };
  }
  var labels = {
    zh: {
      idle: ['播放紀念語音', '播放 921 紀念語音', ''],
      starting: ['暫停', '暫停 921 紀念語音', '正在準備語音'],
      playing: ['暫停', '暫停 921 紀念語音', '語音播放中'],
      paused: ['繼續', '繼續播放 921 紀念語音', '語音已暫停'],
      ended: ['重新播放', '重新播放 921 紀念語音', '語音播放完畢'],
      error: ['重試語音', '重新嘗試播放 921 紀念語音', '此裝置暫時無法播放語音，請重試。'],
      replay: '重新播放', replayLabel: '重新播放 921 紀念語音',
      malePlaying: '男聲旁白播放中', fallbackPlaying: '未找到男聲，正使用裝置音色播放'
    },
    en: {
      idle: ['LISTEN', 'Play 921 memorial voice', ''],
      starting: ['PAUSE', 'Pause 921 memorial voice', 'Preparing voice'],
      playing: ['PAUSE', 'Pause 921 memorial voice', 'Voice playing'],
      paused: ['RESUME', 'Resume 921 memorial voice', 'Voice paused'],
      ended: ['REPLAY', 'Replay 921 memorial voice', 'Voice finished'],
      error: ['TRY AGAIN', 'Retry 921 memorial voice', 'Voice is unavailable on this device right now. Please try again.'],
      replay: 'REPLAY', replayLabel: 'Replay 921 memorial voice',
      malePlaying: 'Male narration playing', fallbackPlaying: 'Playing · Male voice not found'
    }
  };

  function create(options) {
    var dialog = options.dialog, controls = dialog.querySelector('.memorial-voice');
    if (!controls) return null;
    var toggle = controls.querySelector('[data-voice-toggle]');
    var replay = controls.querySelector('[data-voice-replay]');
    var caption = controls.querySelector('[data-voice-status]');
    var language = options.language === 'en' ? 'en' : 'zh', state = 'idle', disposed = false, voiceSelection = null;
    function render(next, selection) {
      if (selection !== undefined) voiceSelection = selection;
      state = next;
      var copy = labels[language], current = copy[state];
      controls.setAttribute('data-state', state);
      toggle.querySelector('[data-voice-label]').textContent = current[0];
      toggle.setAttribute('aria-label', current[1]);
      caption.textContent = state === 'playing' && voiceSelection
        ? (voiceSelection.male ? copy.malePlaying : copy.fallbackPlaying) : current[2];
      replay.textContent = copy.replay;
      replay.setAttribute('aria-label', copy.replayLabel);
      if (state !== 'paused' && document.activeElement === replay) toggle.focus({ preventScroll: true });
      replay.hidden = state !== 'paused';
    }
    var player = (options.createPlayer || createSpeechPlayer)(render);
    if (!player.supported) return null;
    function canPlay() { return !disposed && dialog.open && !dialog.classList.contains('is-leaving'); }
    function play() {
      if (canPlay()) player.play(narration(language, options.years, options.yearsZh));
    }
    function togglePlayback() {
      if (!canPlay()) return;
      if (state === 'playing' || state === 'starting') player.pause();
      else if (state === 'paused') player.resume();
      else play();
    }
    function stop() { if (!disposed) player.stop(); }
    function onVisibility() { if (document.hidden) stop(); }
    toggle.addEventListener('click', togglePlayback);
    replay.addEventListener('click', play);
    global.addEventListener('pagehide', stop);
    document.addEventListener('visibilitychange', onVisibility);
    render('idle');
    controls.hidden = false;
    return {
      play: play,
      stop: stop,
      setLanguage: function (next) {
        next = next === 'en' ? 'en' : 'zh';
        if (next === language || disposed) return;
        language = next; player.stop(); render('idle');
      },
      destroy: function () {
        if (disposed) return;
        disposed = true; player.destroy();
        toggle.removeEventListener('click', togglePlayback);
        replay.removeEventListener('click', play);
        global.removeEventListener('pagehide', stop);
        document.removeEventListener('visibilitychange', onVisibility);
      }
    };
  }
  global.MemorialVoiceController = { create: create, createSpeechPlayer: createSpeechPlayer };
})(window);
