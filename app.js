/* 德国路标自练页：浏览 / 翻卡 / 测验。纯前端，学习记录存在 localStorage。 */
(function () {
  "use strict";

  const DATA = window.SIGN_DATA;
  const SIGNS = DATA.signs;
  const CATS = DATA.categories;
  const CAT_ORDER = Object.keys(CATS);
  const RULES = DATA.rules || [];
  const RCATS = DATA.ruleCategories || {};
  const RCAT_ORDER = Object.keys(RCATS);
  const SIGN_BY_ID = Object.fromEntries(SIGNS.map(s => [s.id, s]));
  const STORE_KEY = "gd-signs-progress-v1";
  const PREF_KEY = "gd-signs-prefs-v1";

  // ---------------------------------------------------------------- 状态

  let progress = load(STORE_KEY, {});           // id -> {ok, bad, streak, t}
  let prefs = Object.assign({ mode: "browse", cat: "all", coreOnly: true, hideKnown: false, quizType: "img2zh", rcat: "all", rsub: "cards" }, load(PREF_KEY, {}));
  let search = "";
  let current = null;                            // 翻卡 / 测验里当前的标志
  let revealed = false;
  let lastId = null;
  let session = { right: 0, wrong: 0 };
  let answered = false;

  function load(key, dflt) {
    try { return JSON.parse(localStorage.getItem(key)) || dflt; } catch (e) { return dflt; }
  }
  function save() {
    localStorage.setItem(STORE_KEY, JSON.stringify(progress));
    localStorage.setItem(PREF_KEY, JSON.stringify(prefs));
  }

  function rec(id) { return progress[id] || { ok: 0, bad: 0, streak: 0, t: 0 }; }
  function level(id) {                           // 0 没学过, 1 刚错过, 2 学习中, 3 掌握
    const r = rec(id);
    if (!r.ok && !r.bad) return 0;
    if (r.streak >= 3) return 3;
    if (r.streak === 0) return 1;
    return 2;
  }
  function mark(id, good) {
    const r = rec(id);
    if (good) { r.ok++; r.streak++; } else { r.bad++; r.streak = 0; }
    r.t = Date.now();
    progress[id] = r;
    save();
  }

  // ---------------------------------------------------------------- 筛选

  function pool() {
    const q = search.trim().toLowerCase();
    return SIGNS.filter(s =>
      (prefs.cat === "all" || s.cat === prefs.cat) &&
      (!prefs.coreOnly || s.core) &&
      (!prefs.hideKnown || level(s.id) < 3) &&
      (!q || (s.nr + " " + s.id + " " + s.de + " " + s.zh + " " + s.meaning).toLowerCase().includes(q)));
  }

  // 规则卡片的筛选；学习记录用 "r:" 前缀和路标分开
  const rid = r => "r:" + r.id;
  function rulesPool() {
    const q = search.trim().toLowerCase();
    return RULES.filter(r =>
      (prefs.rcat === "all" || r.cat === prefs.rcat) &&
      (!prefs.hideKnown || level(rid(r)) < 3) &&
      (!q || (r.q + " " + r.a + " " + (r.de || "") + " " + (r.note || "")).toLowerCase().includes(q)));
  }

  // 抽下一张：没学过和刚错过的优先，掌握的偶尔复习
  function pick(list, key) {
    key = key || (s => s.id);
    const cands = list.filter(s => key(s) !== lastId);
    if (!cands.length) return list[0] || null;
    const now = Date.now();
    const w = cands.map(s => {
      const r = rec(key(s)), lv = level(key(s));
      let x = lv === 0 ? 4 : lv === 1 ? 5 : lv === 2 ? 2.5 : 0.4;
      if (r.t && now - r.t > 86400e3) x += 1;        // 一天没见过的加一点
      if (r.t && now - r.t < 60e3) x *= 0.2;         // 刚刚见过的少出
      return x;
    });
    let r = Math.random() * w.reduce((a, b) => a + b, 0);
    for (let i = 0; i < cands.length; i++) { r -= w[i]; if (r <= 0) return cands[i]; }
    return cands[cands.length - 1];
  }

  // ---------------------------------------------------------------- 工具

  const $ = sel => document.querySelector(sel);
  function h(tag, attrs, ...kids) {
    const el = document.createElement(tag);
    for (const k in attrs || {}) {
      if (k === "class") el.className = attrs[k];
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), attrs[k]);
      else if (k === "html") el.innerHTML = attrs[k];
      else el.setAttribute(k, attrs[k]);
    }
    for (const kid of kids.flat()) if (kid != null) el.append(kid.nodeType ? kid : document.createTextNode(kid));
    return el;
  }
  function shuffle(a) { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
  const nrText = s => s.nr ? "Zeichen " + s.nr : "Zusatzzeichen";

  // ---------------------------------------------------------------- 顶部筛选

  function renderFilters() {
    const chips = $("#cats");
    chips.innerHTML = "";
    const rules = prefs.mode === "rules";
    if (rules) {
      chips.append(h("button", { class: prefs.rcat === "all" ? "on" : "", onclick: () => setRcat("all") }, "全部"));
      for (const k of RCAT_ORDER) chips.append(h("button", { class: prefs.rcat === k ? "on" : "", onclick: () => setRcat(k) }, RCATS[k].zh));
    } else {
      chips.append(h("button", { class: prefs.cat === "all" ? "on" : "", onclick: () => setCat("all") }, "全部"));
      for (const k of CAT_ORDER) chips.append(h("button", { class: prefs.cat === k ? "on" : "", onclick: () => setCat(k) }, CATS[k].zh));
    }
    $("#coreOnly").checked = prefs.coreOnly;
    $("#coreOnly").parentElement.style.display = rules ? "none" : "";
    $("#hideKnown").checked = prefs.hideKnown;
    document.querySelectorAll(".modes button").forEach(b => b.classList.toggle("on", b.dataset.mode === prefs.mode));
    $("#search").style.display = prefs.mode === "browse" || (rules && prefs.rsub === "list") ? "" : "none";
  }
  function setCat(c) { prefs.cat = c; save(); current = null; render(); }
  function setRcat(c) { prefs.rcat = c; save(); current = null; render(); }

  function renderStat() {
    const rules = prefs.mode === "rules";
    const list = rules ? rulesPool() : pool();
    const key = rules ? rid : (s => s.id);
    const n = list.length;
    const known = list.filter(s => level(key(s)) === 3).length;
    const learning = list.filter(s => level(key(s)) === 2).length;
    const bad = list.filter(s => level(key(s)) === 1).length;
    $("#stat").innerHTML = `<b>${n}</b> ${rules ? "张卡片" : "个标志"} · 已掌握 <b>${known}</b> · 学习中 ${learning} · 待复习 ${bad}` +
      `<span class="bar"><i style="width:${n ? Math.round(known / n * 100) : 0}%"></i></span>`;
  }

  // ---------------------------------------------------------------- 浏览

  function renderBrowse(main) {
    const list = pool();
    if (!list.length) { main.append(h("div", { class: "empty" }, "没有符合条件的标志。试试取消「只看考试重点」或换个类别。")); return; }
    for (const k of CAT_ORDER) {
      const items = list.filter(s => s.cat === k);
      if (!items.length) continue;
      main.append(h("div", { class: "cat-head" }, h("h2", null, CATS[k].zh), h("span", { class: "de" }, CATS[k].de), h("span", { class: "de" }, items.length + " 个")));
      main.append(h("p", { class: "cat-note" }, CATS[k].note));
      const grid = h("div", { class: "grid" });
      for (const s of items) {
        const lv = level(s.id);
        grid.append(h("div", { class: "card", onclick: () => openDetail(s), title: s.de },
          s.drawn ? h("span", { class: "badge" }, "示意") : null,
          lv ? h("span", { class: "dot " + (lv === 3 ? "ok" : lv === 1 ? "bad" : "mid") }) : null,
          h("img", { src: s.img, alt: s.de, loading: "lazy" }),
          h("div", { class: "nr" }, s.nr || "Zusatz"),
          h("div", { class: "zh" }, s.zh),
          h("div", { class: "de" }, s.de)));
      }
      main.append(grid);
    }
  }

  function detailNode(s) {
    const r = rec(s.id);
    return h("div", { class: "detail" },
      h("img", { src: s.img, alt: s.de }),
      h("div", null,
        h("div", { class: "nr" }, nrText(s)),
        h("h3", null, s.zh),
        h("p", { class: "de" }, s.de),
        h("p", { class: "meaning" }, s.meaning),
        h("div", { class: "cat" }, CATS[s.cat].zh + " · " + CATS[s.cat].de),
        s.drawn ? h("div", { class: "drawn" }, "示意图：按官方样式简化绘制，细节和真实标志有出入") : null,
        (r.ok || r.bad) ? h("div", { class: "rec" }, `答对 ${r.ok} 次，答错 ${r.bad} 次，连对 ${r.streak}`) : null));
  }
  function openDetail(s) {
    $("#modalBody").innerHTML = "";
    $("#modalBody").append(detailNode(s));
    $("#modal").hidden = false;
  }
  function closeDetail() { $("#modal").hidden = true; }

  // ---------------------------------------------------------------- 翻卡

  function renderCards(main) {
    const list = pool();
    if (!list.length) { main.append(h("div", { class: "empty" }, "这个范围里没有标志了。")); return; }
    if (!current || !list.some(s => s.id === current.id)) { current = pick(list); revealed = false; }
    const s = current;
    const stage = h("div", { class: "stage" });
    const big = h("div", { class: "big", onclick: () => { if (!revealed) { revealed = true; render(); } } },
      h("img", { src: s.img, alt: "" }));
    if (!revealed) {
      big.append(h("div", { class: "hint" }, "想一想这是什么，然后点卡片或按空格翻面"));
    } else {
      big.append(h("div", { class: "nr" }, nrText(s)), h("div", { class: "zh" }, s.zh), h("div", { class: "de" }, s.de), h("p", { class: "meaning" }, s.meaning));
      if (s.drawn) big.append(h("div", { class: "hint" }, "（示意图，细节与官方图有出入）"));
    }
    stage.append(big);
    if (!revealed) {
      stage.append(h("div", { class: "actions" }, h("button", { class: "btn primary", onclick: () => { revealed = true; render(); } }, "翻面")));
      stage.append(h("div", { class: "kbd" }, h("kbd", null, "空格"), " 翻面"));
    } else {
      stage.append(h("div", { class: "actions" },
        h("button", { class: "btn bad", onclick: () => answerCard(false) }, "不认识 / 记错了"),
        h("button", { class: "btn ok", onclick: () => answerCard(true) }, "认识")));
      stage.append(h("div", { class: "kbd" }, h("kbd", null, "1"), " 不认识　", h("kbd", null, "2"), " 认识"));
    }
    main.append(stage);
  }
  function answerCard(good) {
    mark(current.id, good);
    lastId = current.id;
    current = null; revealed = false;
    render();
  }

  // ---------------------------------------------------------------- 测验

  function distractors(s, n) {
    // 同类别优先，中文名不能重复；不够再从全部里补
    const same = SIGNS.filter(x => x.id !== s.id && x.cat === s.cat && x.zh !== s.zh);
    const other = SIGNS.filter(x => x.id !== s.id && x.cat !== s.cat);
    const out = [], seen = new Set([s.zh]);
    for (const x of shuffle(same).concat(shuffle(other))) {
      if (out.length >= n) break;
      if (seen.has(x.zh)) continue;
      seen.add(x.zh); out.push(x);
    }
    return out;
  }

  function renderQuiz(main) {
    const list = pool();
    if (!list.length) { main.append(h("div", { class: "empty" }, "这个范围里没有标志了。")); return; }
    if (!current || !list.some(s => s.id === current.id)) {
      current = pick(list); answered = false;
      current._opts = shuffle([current, ...distractors(current, 3)]);
    }
    const s = current, opts = s._opts;
    const stage = h("div", { class: "stage" });
    stage.append(h("div", { class: "quiz-type" },
      h("button", { class: prefs.quizType === "img2zh" ? "on" : "", onclick: () => setQuizType("img2zh") }, "看图选意思"),
      h("button", { class: prefs.quizType === "de2img" ? "on" : "", onclick: () => setQuizType("de2img") }, "看德文选图")));
    stage.append(h("div", { class: "score" }, "本轮 ", h("b", null, session.right), " 对 / ", h("b", null, session.wrong), " 错"));

    const optsBox = h("div", { class: "quiz-opts" });
    if (prefs.quizType === "img2zh") {
      stage.append(h("div", { class: "big", style: "cursor:default" }, h("img", { src: s.img, alt: "" }), h("div", { class: "hint" }, "这个标志是什么意思？")));
      opts.forEach((o, i) => optsBox.append(h("button", { class: "opt", onclick: () => answerQuiz(o, i) },
        h("span", { class: "k" }, i + 1), h("span", null, h("div", null, o.zh), h("div", { class: "de" }, o.de)))));
    } else {
      stage.append(h("div", { class: "big", style: "cursor:default;min-height:0" }, h("div", { class: "quiz-q" }, s.de), h("div", { class: "quiz-sub" }, nrText(s) + " · 下面哪个是它？")));
      optsBox.style.gridTemplateColumns = "1fr 1fr";
      opts.forEach((o, i) => optsBox.append(h("button", { class: "opt", onclick: () => answerQuiz(o, i) },
        h("span", { class: "k" }, i + 1), h("img", { src: o.img, alt: "" }))));
    }
    stage.append(optsBox);

    if (answered) {
      const btns = optsBox.querySelectorAll(".opt");
      btns.forEach((b, i) => { b.disabled = true; if (opts[i].id === s.id) b.classList.add("right"); else if (i === s._chosen) b.classList.add("wrong"); });
      const good = opts[s._chosen].id === s.id;
      stage.append(h("div", { class: "feedback " + (good ? "right" : "wrong") },
        h("div", null, h("b", null, good ? "对了。" : "错了。"), " ", s.zh, " ", h("span", { class: "de" }, "— " + s.de + (s.nr ? "（" + s.nr + "）" : ""))),
        h("p", { style: "margin:6px 0 0" }, s.meaning),
        !good && prefs.quizType === "img2zh" ? h("p", { style: "margin:6px 0 0", class: "de" }, "你选的「" + opts[s._chosen].zh + "」是：" + opts[s._chosen].meaning) : null));
      stage.append(h("div", { class: "actions" }, h("button", { class: "btn primary", onclick: nextQuiz }, "下一题")));
      stage.append(h("div", { class: "kbd" }, h("kbd", null, "空格"), " 下一题"));
    } else {
      stage.append(h("div", { class: "kbd" }, h("kbd", null, "1"), "–", h("kbd", null, "4"), " 选择"));
    }
    main.append(stage);
  }
  function setQuizType(t) { prefs.quizType = t; save(); current = null; render(); }
  function answerQuiz(o, i) {
    if (answered) return;
    answered = true;
    current._chosen = i;
    const good = o.id === current.id;
    mark(current.id, good);
    if (good) session.right++; else session.wrong++;
    render();
  }
  function nextQuiz() { lastId = current.id; current = null; answered = false; render(); }

  // ---------------------------------------------------------------- 规则卡片

  function ruleDistractors(r, n) {
    const same = RULES.filter(x => x.id !== r.id && x.cat === r.cat && x.a !== r.a);
    const other = RULES.filter(x => x.id !== r.id && x.cat !== r.cat && x.a !== r.a);
    const out = [], seen = new Set([r.a]);
    for (const x of shuffle(same).concat(shuffle(other))) {
      if (out.length >= n) break;
      if (seen.has(x.a)) continue;
      seen.add(x.a); out.push(x);
    }
    return out;
  }

  function ruleImg(r) {
    const s = r.img && SIGN_BY_ID[r.img];
    return s ? h("img", { src: s.img, alt: s.de, class: "rule-img" }) : null;
  }

  function renderRules(main) {
    const stage = h("div", { class: "stage" });
    stage.append(h("div", { class: "quiz-type" },
      h("button", { class: prefs.rsub === "cards" ? "on" : "", onclick: () => setRsub("cards") }, "翻卡"),
      h("button", { class: prefs.rsub === "quiz" ? "on" : "", onclick: () => setRsub("quiz") }, "选择题"),
      h("button", { class: prefs.rsub === "list" ? "on" : "", onclick: () => setRsub("list") }, "列表")));
    if (prefs.rcat !== "all") stage.append(h("p", { class: "cat-note", style: "text-align:center" }, RCATS[prefs.rcat].note));
    const list = rulesPool();
    if (!list.length) { stage.append(h("div", { class: "empty" }, "这个范围里没有卡片了。")); main.append(stage); return; }

    if (prefs.rsub === "list") {
      stage.classList.add("wide");
      for (const k of RCAT_ORDER) {
        const items = list.filter(r => r.cat === k);
        if (!items.length) continue;
        stage.append(h("div", { class: "cat-head" }, h("h2", null, RCATS[k].zh), h("span", { class: "de" }, items.length + " 张")));
        for (const r of items) {
          const lv = level(rid(r));
          stage.append(h("div", { class: "rule-row" },
            lv ? h("span", { class: "dot " + (lv === 3 ? "ok" : lv === 1 ? "bad" : "mid") }) : null,
            h("div", { class: "rule-q" }, r.q),
            h("div", { class: "rule-a" }, r.a),
            r.de ? h("div", { class: "de" }, r.de) : null,
            r.note ? h("div", { class: "rule-note" }, r.note) : null));
        }
      }
      main.append(stage);
      return;
    }

    if (!current || !list.some(r => r.id === current.id)) {
      current = pick(list, rid); revealed = false; answered = false;
      if (prefs.rsub === "quiz") current._opts = shuffle([current, ...ruleDistractors(current, 3)]);
    }
    const r = current;

    if (prefs.rsub === "cards") {
      const big = h("div", { class: "big rule", onclick: () => { if (!revealed) { revealed = true; render(); } } },
        h("div", { class: "nr" }, RCATS[r.cat].zh), ruleImg(r), h("div", { class: "rule-q" }, r.q));
      if (!revealed) {
        big.append(h("div", { class: "hint" }, "想好答案，点卡片或按空格翻面"));
      } else {
        big.append(h("div", { class: "zh" }, r.a), r.de ? h("div", { class: "de" }, r.de) : null, r.note ? h("p", { class: "meaning" }, r.note) : null);
      }
      stage.append(big);
      if (!revealed) {
        stage.append(h("div", { class: "actions" }, h("button", { class: "btn primary", onclick: () => { revealed = true; render(); } }, "翻面")));
        stage.append(h("div", { class: "kbd" }, h("kbd", null, "空格"), " 翻面"));
      } else {
        stage.append(h("div", { class: "actions" },
          h("button", { class: "btn bad", onclick: () => answerRule(false) }, "没记住"),
          h("button", { class: "btn ok", onclick: () => answerRule(true) }, "记住了")));
        stage.append(h("div", { class: "kbd" }, h("kbd", null, "1"), " 没记住　", h("kbd", null, "2"), " 记住了"));
      }
    } else {
      const opts = r._opts;
      stage.append(h("div", { class: "score" }, "本轮 ", h("b", null, session.right), " 对 / ", h("b", null, session.wrong), " 错"));
      stage.append(h("div", { class: "big rule", style: "cursor:default;min-height:0" }, h("div", { class: "nr" }, RCATS[r.cat].zh), ruleImg(r), h("div", { class: "rule-q" }, r.q)));
      const optsBox = h("div", { class: "quiz-opts" });
      opts.forEach((o, i) => optsBox.append(h("button", { class: "opt", onclick: () => answerRuleQuiz(o, i) }, h("span", { class: "k" }, i + 1), h("span", null, o.a))));
      stage.append(optsBox);
      if (answered) {
        const btns = optsBox.querySelectorAll(".opt");
        btns.forEach((b, i) => { b.disabled = true; if (opts[i].id === r.id) b.classList.add("right"); else if (i === r._chosen) b.classList.add("wrong"); });
        const good = opts[r._chosen].id === r.id;
        stage.append(h("div", { class: "feedback " + (good ? "right" : "wrong") },
          h("div", null, h("b", null, good ? "对了。" : "错了。"), " ", r.a, r.de ? h("span", { class: "de" }, " — " + r.de) : null),
          r.note ? h("p", { style: "margin:6px 0 0" }, r.note) : null,
          !good ? h("p", { style: "margin:6px 0 0", class: "de" }, "你选的「" + opts[r._chosen].a + "」是这道题的答案：" + opts[r._chosen].q) : null));
        stage.append(h("div", { class: "actions" }, h("button", { class: "btn primary", onclick: nextRule }, "下一题")));
        stage.append(h("div", { class: "kbd" }, h("kbd", null, "空格"), " 下一题"));
      } else {
        stage.append(h("div", { class: "kbd" }, h("kbd", null, "1"), "–", h("kbd", null, "4"), " 选择"));
      }
    }
    main.append(stage);
  }
  function setRsub(t) { prefs.rsub = t; save(); current = null; render(); }
  function answerRule(good) { mark(rid(current), good); lastId = rid(current); current = null; revealed = false; render(); }
  function answerRuleQuiz(o, i) {
    if (answered) return;
    answered = true;
    current._chosen = i;
    const good = o.id === current.id;
    mark(rid(current), good);
    if (good) session.right++; else session.wrong++;
    render();
  }
  function nextRule() { lastId = rid(current); current = null; answered = false; render(); }

  // ---------------------------------------------------------------- 主渲染

  function render() {
    renderFilters();
    renderStat();
    const main = $("#main");
    main.innerHTML = "";
    if (prefs.mode === "browse") renderBrowse(main);
    else if (prefs.mode === "cards") renderCards(main);
    else if (prefs.mode === "rules") renderRules(main);
    else renderQuiz(main);
  }

  document.querySelectorAll(".modes button").forEach(b => b.addEventListener("click", () => { prefs.mode = b.dataset.mode; current = null; save(); render(); }));
  $("#coreOnly").addEventListener("change", e => { prefs.coreOnly = e.target.checked; current = null; save(); render(); });
  $("#hideKnown").addEventListener("change", e => { prefs.hideKnown = e.target.checked; current = null; save(); render(); });
  $("#search").addEventListener("input", e => { search = e.target.value; render(); });
  $("#modalClose").addEventListener("click", closeDetail);
  $("#modal").addEventListener("click", e => { if (e.target === $("#modal")) closeDetail(); });
  $("#reset").addEventListener("click", () => { if (confirm("清除所有学习记录？")) { progress = {}; session = { right: 0, wrong: 0 }; save(); render(); } });

  document.addEventListener("keydown", e => {
    if (e.target.tagName === "INPUT") return;
    if (e.key === "Escape") { closeDetail(); return; }
    if (prefs.mode === "cards") {
      if (e.key === " " || e.key === "Enter") { e.preventDefault(); if (!revealed) { revealed = true; render(); } }
      else if (revealed && e.key === "1") answerCard(false);
      else if (revealed && e.key === "2") answerCard(true);
    } else if (prefs.mode === "quiz") {
      if ((e.key === " " || e.key === "Enter") && answered) { e.preventDefault(); nextQuiz(); }
      else if (!answered && /^[1-4]$/.test(e.key)) { const i = +e.key - 1; if (current._opts[i]) answerQuiz(current._opts[i], i); }
    } else if (prefs.mode === "rules" && current) {
      if (prefs.rsub === "cards") {
        if (e.key === " " || e.key === "Enter") { e.preventDefault(); if (!revealed) { revealed = true; render(); } }
        else if (revealed && e.key === "1") answerRule(false);
        else if (revealed && e.key === "2") answerRule(true);
      } else if (prefs.rsub === "quiz") {
        if ((e.key === " " || e.key === "Enter") && answered) { e.preventDefault(); nextRule(); }
        else if (!answered && /^[1-4]$/.test(e.key)) { const i = +e.key - 1; if (current._opts[i]) answerRuleQuiz(current._opts[i], i); }
      }
    }
  });

  render();
})();
