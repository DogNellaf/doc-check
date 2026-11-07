/* The checker's page on the Tabler vertical layout: examples and an upload, the result with its
   findings, the document and its fields, and the pages with what the company checks against.
   Plain JS, no build. */
(function () {
  "use strict";

  /* Icons from Lucide (ISC license, lucide.dev), 24×24 stroke paths */
  var DOC = '<path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"/><path d="M14 2v5a1 1 0 0 0 1 1h5"/>';
  var ICONS = {
    "file-text": DOC + '<path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "file-check": DOC + '<path d="m9 15 2 2 4-4"/>',
    "file-search": DOC + '<circle cx="11.5" cy="14.5" r="2.5"/><path d="M13.3 16.3 15 18"/>',
    "file-spreadsheet": DOC + '<path d="M8 13h2"/><path d="M14 13h2"/><path d="M8 17h2"/><path d="M14 17h2"/>',
    "file-pen": '<path d="M12.659 22H18a2 2 0 0 0 2-2V8a2.4 2.4 0 0 0-.706-1.706l-3.588-3.588A2.4 2.4 0 0 0 14 2H6a2 2 0 0 0-2 2v9.34"/><path d="M14 2v5a1 1 0 0 0 1 1h5"/><path d="M10.378 12.622a1 1 0 0 1 3 3.003L8.36 20.637a2 2 0 0 1-.854.506l-2.867.837a.5.5 0 0 1-.62-.62l.836-2.869a2 2 0 0 1 .506-.853z"/>',
    upload: '<path d="M12 3v12"/><path d="m17 8-5-5-5 5"/><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>',
    "upload-cloud": '<path d="M12 13v8"/><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="m8 17 4-4 4 4"/>',
    "triangle-alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "circle-alert": '<circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
    "circle-check": '<circle cx="12" cy="12" r="10"/><path d="m16 9-5.5 5.5L8 12"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "scan-text": '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 8h8"/><path d="M7 12h10"/><path d="M7 16h6"/>',
    receipt: '<path d="M12 17V7"/><path d="M16 8h-6a2 2 0 0 0 0 4h4a2 2 0 0 1 0 4H8"/><path d="M4 3a1 1 0 0 1 1-1 1.3 1.3 0 0 1 .7.2l.933.6a1.3 1.3 0 0 0 1.4 0l.934-.6a1.3 1.3 0 0 1 1.4 0l.933.6a1.3 1.3 0 0 0 1.4 0l.933-.6a1.3 1.3 0 0 1 1.4 0l.934.6a1.3 1.3 0 0 0 1.4 0l.933-.6A1.3 1.3 0 0 1 19 2a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1 1.3 1.3 0 0 1-.7-.2l-.933-.6a1.3 1.3 0 0 0-1.4 0l-.934.6a1.3 1.3 0 0 1-1.4 0l-.933-.6a1.3 1.3 0 0 0-1.4 0l-.933.6a1.3 1.3 0 0 1-1.4 0l-.934-.6a1.3 1.3 0 0 0-1.4 0l-.933.6a1.3 1.3 0 0 1-.7.2 1 1 0 0 1-1-1z"/>',
    "shield-check": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "book-open": '<path d="M12 5v16"/><path d="M20.001 19A2 2 0 0022 17V5a2 2 0 00-1.999-2L16 3.002A5 5 0 0012 5a5 5 0 00-4-2H4a2 2 0 00-2 2v12a2 2 0 001.999 2H8a5 5 0 014 2 5 5 0 014-2z"/>',
    scale: '<path d="M12 3v18"/><path d="m19 8 3 8a5 5 0 0 1-6 0zV7"/><path d="M3 7h1a17 17 0 0 0 8-2 17 17 0 0 0 8 2h1"/><path d="m5 8 3 8a5 5 0 0 1-6 0zV7"/><path d="M7 21h10"/>',
    truck: '<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/>',
    "clipboard-list": '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
    "building-2": '<path d="M10 12h4"/><path d="M10 8h4"/><path d="M14 21v-3a2 2 0 0 0-4 0v3"/><path d="M6 10H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2"/><path d="M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"/>',
    menu: '<path d="M4 5h16"/><path d="M4 12h16"/><path d="M4 19h16"/>',
    x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "eye": '<path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/>'
  };
  function icon(name, cls) {
    return '<svg class="icon dc-icon ' + (cls || "") + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICONS[name] || "") + "</svg>";
  }
  function paintIcons(root) {
    root.querySelectorAll("[data-icon]").forEach(function (el) {
      if (!el.querySelector("svg")) el.insertAdjacentHTML("afterbegin", icon(el.getAttribute("data-icon")));
    });
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function $(id) { return document.getElementById(id); }
  function plural(n, one, few, many) {
    var a = n % 10, b = n % 100;
    if (a === 1 && b !== 11) return one;
    if (a >= 2 && a <= 4 && (b < 12 || b > 14)) return few;
    return many;
  }
  function rub(v) {
    return Number(v).toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " ₽";
  }
  function num(v) { return String(v).replace(".", ","); }

  /* Tabler colours per level */
  var LEVEL = {
    high: { name: "Критично", color: "red", icon: "triangle-alert" },
    medium: { name: "Согласовать", color: "yellow", icon: "circle-alert" },
    low: { name: "Обратить внимание", color: "azure", icon: "info" }
  };
  var VERDICT_COLOR = { high: "red", medium: "yellow", low: "azure", ok: "green" };
  var STATUS = {
    same: ["Как в эталоне", "green"],
    reworded: ["Другая формулировка", "azure"],
    changed: ["Другие цифры", "yellow"],
    extra: ["Нет в эталоне", "purple"]
  };
  var KIND = {
    contract: { icon: "file-text", color: "blue" },
    invoice: { icon: "receipt", color: "green" },
    scan: { icon: "scan-text", color: "purple" }
  };
  function badge(level) {
    var lv = LEVEL[level];
    return '<span class="badge bg-' + lv.color + "-lt dc-badge-" + level + '">' + lv.name + "</span>";
  }
  function worstOf(levels) {
    return ["high", "medium", "low"].filter(function (l) { return levels.indexOf(l) >= 0; })[0];
  }

  var state = { current: null, examples: [], tab: "findings", busy: false, limit: 10 };

  // ------------------------------------------------------------------ data

  function api(path, opts) {
    return fetch("api/" + path, opts).then(function (r) {
      return r.json().then(function (body) {
        if (!r.ok) { var e = new Error(body.error || "Ошибка " + r.status); e.body = body; throw e; }
        return body;
      });
    });
  }

  function quota(remaining, limit) {
    if (remaining == null) return;
    var el = $("quota");
    el.textContent = "Сегодня осталось " + remaining + " из " + (limit || state.limit) + " проверок своих файлов. Примеры — без ограничений.";
    el.className = "d-block small mt-1 " + (remaining ? "text-secondary" : "text-warning");
  }

  function loadExamples() {
    api("examples").then(function (data) {
      state.examples = data.examples;
      state.limit = data.limit || state.limit;
      quota(data.remaining, data.limit);
      renderExamples();
      var first = data.examples.filter(function (e) { return e.ready; })[0];
      if (first) openExample(first.id);
      else $("result").innerHTML = emptyCard("Примеры не загрузились", "Загрузите свой договор или счёт.");
    }).catch(function () {
      $("result").innerHTML = emptyCard("Сервис проверки сейчас недоступен", "Обновите страницу через минуту.");
    });
  }

  function emptyCard(title, text) {
    return '<div class="card"><div class="empty"><div class="empty-icon">' + icon("file-search") + '</div><p class="empty-title">' + esc(title) + '</p><p class="empty-subtitle text-secondary">' + esc(text) + "</p></div></div>";
  }

  function renderExamples() {
    document.querySelectorAll(".dc-ex-col").forEach(function (el) { el.remove(); });
    var html = state.examples.map(function (e) {
      var v = e.verdict, k = KIND[e.id === "scan" ? "scan" : e.kind] || KIND.contract;
      var active = state.current && state.current.example === e.id;
      return '<div class="col-sm-6 col-xl-3 dc-ex-col">' +
        '<button type="button" class="card card-sm card-link dc-ex' + (active ? " card-active" : "") + '" data-example="' + esc(e.id) + '"' + (active ? ' aria-pressed="true"' : ' aria-pressed="false"') + (e.ready ? "" : " disabled") + ">" +
        '<span class="card-body">' +
        '<span class="dc-ex-head"><span class="avatar avatar-square bg-' + k.color + ' text-white">' + icon(k.icon) + "</span>" +
        '<span class="dc-ex-text"><b>' + esc(e.title) + '</b><span class="text-secondary small dc-ex-note">' + esc(e.note) + "</span></span></span>" +
        (v ? '<span class="dc-ex-verdict text-' + VERDICT_COLOR[v.level] + '"><span class="status-dot status-' + VERDICT_COLOR[v.level] + '"></span>' + esc(v.text) + "</span>" : '<span class="d-block small text-secondary mt-2">недоступен</span>') +
        "</span></button></div>";
    }).join("");
    $("drop-col").insertAdjacentHTML("beforebegin", html);
  }

  function openExample(id, scroll) {
    api("examples/" + encodeURIComponent(id)).then(function (r) {
      show(r);
      if (scroll) $("result").scrollIntoView({ block: "start", behavior: "smooth" });
    });
  }

  function upload(file) {
    if (!file || state.busy) return;
    state.busy = true;
    showPage("check");
    $("drop").classList.add("dc-drop-busy");
    $("result").innerHTML = '<div class="card"><div class="card-body"><div class="d-flex align-items-center gap-3"><div class="spinner-border text-primary" role="status"></div><div><b>Проверяю «' + esc(file.name) + '»</b><div class="text-secondary small">Читаю текст, сверяю пункты и строки. Скан распознаётся до полуминуты.</div></div></div><div class="progress progress-sm mt-3"><div class="progress-bar progress-bar-indeterminate"></div></div></div></div>';
    $("result").scrollIntoView({ block: "start", behavior: "smooth" });
    var form = new FormData();
    form.append("file", file);
    api("check", { method: "POST", body: form }).then(function (r) {
      quota(r.remaining, state.limit);
      show(r);
    }).catch(function (e) {
      if (e.body) quota(e.body.remaining, state.limit);
      var limit = e.body && e.body.kind === "limit";
      $("result").innerHTML = '<div class="alert alert-' + (limit ? "warning" : "danger") + '" role="alert"><div class="d-flex gap-2">' + icon("circle-alert", "alert-icon") + "<div>" + esc(e.message) + "</div></div></div>";
    }).then(function () {
      state.busy = false;
      $("drop").classList.remove("dc-drop-busy");
      $("file").value = "";
    });
  }

  // ------------------------------------------------------------------ result

  function show(r) {
    state.current = r;
    state.tab = "findings";
    renderExamples();
    render();
  }

  function render() {
    var r = state.current;
    var v = r.verdict, c = v.counts;
    var isContract = r.kind === "contract";
    var k = KIND[r.ocr ? "scan" : r.kind] || KIND.contract;
    var n = r.findings.length;
    var src = r.ocr ? '<span class="badge bg-purple-lt">скан, распознан OCR</span>' : '<span class="badge bg-secondary-lt">' + esc((r.fmt || "").toUpperCase()) + "</span>";
    if (r.lines_by === "model") src += ' <span class="badge bg-purple-lt">строки прочитала модель</span>';
    var fileLink = r.example ? '<a href="examples/' + encodeURIComponent(r.file) + '" target="_blank" rel="noopener">' + esc(r.file) + "</a>" : esc(r.file);
    var color = VERDICT_COLOR[v.level];

    var stats = ["high", "medium", "low"].map(function (l) {
      return '<div class="col-4 dc-stat"><div class="subheader">' + LEVEL[l].name + '</div><div class="h1 mb-0 dc-count' + (c[l] ? " text-" + LEVEL[l].color : " text-secondary") + '">' + c[l] + "</div></div>";
    }).join("");
    var bar = n ? '<div class="progress progress-separated mt-3" role="img" aria-label="Замечания по уровням">' + ["high", "medium", "low"].filter(function (l) { return c[l]; }).map(function (l) {
      return '<div class="progress-bar bg-' + LEVEL[l].color + '" style="width:' + (100 * c[l] / n).toFixed(1) + '%"></div>';
    }).join("") + "</div>" : "";

    var html =
      '<div class="card mb-3 dc-summary">' +
      '<div class="card-header">' +
      '<div class="dc-file"><span class="avatar bg-' + k.color + '-lt text-' + k.color + '">' + icon(k.icon) + "</span>" +
      '<div class="dc-file-text"><h3 class="card-title">' + fileLink + '</h3><div class="card-subtitle">' + (isContract ? "Договор · сверка с эталоном и правилами" : "Счёт · сверка с договором, спецификацией и заказом") + " " + src + "</div></div></div>" +
      '<div class="card-actions btn-list">' +
      '<a class="btn" href="api/report/' + encodeURIComponent(r.id) + '.xlsx">' + icon("file-spreadsheet") + "Excel</a>" +
      '<a class="btn btn-primary" href="api/report/' + encodeURIComponent(r.id) + '.docx">' + icon("file-pen") + (isContract ? "Word с правками" : "Письмо поставщику") + "</a>" +
      "</div></div>" +
      '<div class="card-body"><div class="row g-4 align-items-center">' +
      '<div class="col-lg-6"><div class="subheader mb-1">Итог проверки</div>' +
      '<div class="dc-verdict text-' + color + '">' + icon(v.level === "ok" ? "circle-check" : "triangle-alert") + "<span>" + esc(v.text) + "</span></div>" +
      '<div class="text-secondary mt-1">' + (n ? n + " " + plural(n, "замечание", "замечания", "замечаний") + (isContract ? " к договору. Правки уже размечены в Word." : " к счёту. Письмо поставщику уже составлено.") : isContract ? "Договор совпадает с эталоном и проходит правила юриста." : "Счёт сходится с договором, спецификацией и заказом.") + "</div></div>" +
      '<div class="col-lg-6"><div class="row g-2">' + stats + "</div>" + bar + "</div>" +
      "</div></div></div>" +
      '<div class="card dc-tabs-card">' +
      '<div class="card-header"><ul class="nav nav-tabs card-header-tabs dc-rtabs" role="tablist">' +
      tab("findings", "Замечания", n) + tab("doc", isContract ? "Пункты договора" : "Строки счёта", isContract ? r.clauses.length : r.lines.length) + tab("fields", "Реквизиты и поля", null) +
      "</ul></div>" +
      '<div id="rpanel" role="tabpanel"></div></div>';
    $("result").innerHTML = html;
    renderPanel();
  }

  function tab(id, name, count) {
    return '<li class="nav-item" role="presentation"><button type="button" class="nav-link' + (state.tab === id ? " active" : "") + '" data-rtab="' + id + '" role="tab" aria-selected="' + (state.tab === id) + '">' + esc(name) + (count != null ? ' <span class="badge bg-secondary-lt ms-2">' + count + "</span>" : "") + "</button></li>";
  }

  function renderPanel(focus) {
    var r = state.current, el = $("rpanel");
    if (state.tab === "findings") el.innerHTML = findingsHtml(r);
    else if (state.tab === "fields") el.innerHTML = fieldsHtml(r);
    else el.innerHTML = r.kind === "contract" ? clausesHtml(r) : linesHtml(r);
    document.querySelectorAll("[data-rtab]").forEach(function (b) {
      var on = b.getAttribute("data-rtab") === state.tab;
      b.classList.toggle("active", on);
      b.setAttribute("aria-selected", on);
    });
    if (focus) {
      var target = document.querySelector('[data-anchor="' + focus + '"]');
      if (target) {
        target.classList.add("dc-flash");
        target.scrollIntoView({ block: "center", behavior: "smooth" });
      }
    }
  }

  function findingsHtml(r) {
    if (!r.findings.length) return '<div class="empty"><div class="empty-icon text-green">' + icon("circle-check") + '</div><p class="empty-title">Замечаний нет</p><p class="empty-subtitle text-secondary">Документ совпадает с эталоном и проходит правила.</p></div>';
    var isContract = r.kind === "contract";
    return '<div class="list-group list-group-flush">' + r.findings.map(function (f) {
      var lv = LEVEL[f.level];
      var fixLabel = f.kind === "missing" ? "Вернуть пункт эталона " + f.ref : f.ref ? "Как в эталоне, п. " + f.ref : "Должно быть";
      return '<div class="list-group-item dc-finding dc-l-' + f.level + '">' +
        '<div class="row g-3 flex-nowrap">' +
        '<div class="col-auto d-none d-sm-block"><span class="avatar avatar-sm bg-' + lv.color + "-lt text-" + lv.color + '">' + icon(lv.icon) + "</span></div>" +
        '<div class="col dc-min0">' +
        '<div class="dc-finding-head">' + badge(f.level) +
        (f.where ? '<span class="text-secondary small">' + esc(f.where) + "</span>" : "") +
        (f.anchor ? '<button type="button" class="btn btn-sm btn-ghost-primary ms-auto" data-goto="' + esc(f.anchor) + '">' + icon("eye") + "В " + (isContract ? "договоре" : "счёте") + "</button>" : "") + "</div>" +
        '<div class="dc-finding-title">' + esc(f.title) + "</div>" +
        (f.why ? '<div class="text-secondary">' + esc(f.why) + "</div>" : "") +
        (f.quote && isContract ? '<div class="dc-quote"><span class="dc-quote-label">У поставщика</span>' + esc(f.quote) + "</div>" : "") +
        (f.fix ? '<div class="dc-fix"><span class="dc-quote-label">' + esc(fixLabel) + "</span>" + esc(f.fix) + "</div>" : "") +
        "</div></div></div>";
    }).join("") + "</div>";
  }

  function diffHtml(ops) {
    return ops.map(function (o) {
      if (o[0] === "=") return esc(o[1]);
      return o[0] === "-" ? '<del class="dc-del">' + esc(o[1]) + "</del>" : '<ins class="dc-ins">' + esc(o[1]) + "</ins>";
    }).join(" ");
  }

  function clausesHtml(r) {
    var section = null;
    var out = ['<div class="card-body py-2 border-bottom small text-secondary dc-legend"><span class="dc-del">зачёркнуто</span> — как в эталоне, <span class="dc-ins">подчёркнуто</span> — как у поставщика</div><div class="list-group list-group-flush">'];
    var missing = {};
    r.findings.forEach(function (f) { if (f.kind === "missing") (missing[f.anchor] = missing[f.anchor] || []).push(f); });
    r.clauses.forEach(function (c) {
      if (c.section !== section) {
        section = c.section;
        out.push('<div class="list-group-header">' + esc(section) + "</div>");
      }
      var st = STATUS[c.status];
      var worst = worstOf(c.levels);
      var body = c.status === "reworded" || c.status === "changed" ? diffHtml(c.diff) : esc(c.text);
      out.push('<div class="list-group-item dc-clause' + (worst ? " dc-l-" + worst : "") + '" data-anchor="' + esc(c.id) + '">' +
        '<div class="row g-3 flex-nowrap"><div class="col-auto dc-clause-num">' + esc(c.number) + '</div><div class="col dc-min0">' + body +
        '<div class="dc-clause-meta"><span class="badge bg-' + st[1] + '-lt">' + st[0] + "</span>" +
        (c.ref && c.ref !== c.number ? '<span class="text-secondary">п. ' + esc(c.ref) + " эталона</span>" : "") +
        (c.similarity != null && c.status !== "same" ? '<span class="text-secondary" title="Насколько текст похож на пункт эталона и доля общих слов">сходство ' + Math.min(1, c.similarity).toFixed(2) + " · слова " + c.lexical.toFixed(2) + "</span>" : "") +
        (worst ? badge(worst) : "") +
        "</div></div></div></div>");
      (missing[c.id] || []).forEach(function (f) {
        out.push('<div class="list-group-item dc-clause dc-l-medium" data-anchor="' + esc(f.anchor) + '-missing"><div class="row g-3 flex-nowrap"><div class="col-auto dc-clause-num">' + esc(f.ref) + '</div><div class="col dc-min0"><ins class="dc-ins">' + esc(f.fix) + '</ins><div class="dc-clause-meta"><span class="badge bg-yellow-lt">Нет в договоре, есть в эталоне</span></div></div></div></div>');
      });
    });
    out.push("</div>");
    return out.join("");
  }

  function linesHtml(r) {
    if (!r.lines.length) return '<div class="card-body text-secondary">Строки счёта не распознаны.</div>';
    var rows = r.lines.map(function (l) {
      var worst = worstOf(l.issues);
      var spec = l.spec ? (l.spec.price === l.price ? '<span class="text-secondary">' + esc(l.spec.price) + "</span>" : '<b class="text-red">' + esc(l.spec.price) + "</b>") : '<span class="text-secondary">нет</span>';
      var ord = l.ordered != null ? (l.ordered === l.qty ? '<span class="text-secondary">' + esc(l.ordered) + "</span>" : '<b class="text-red">' + esc(l.ordered) + "</b>") : '<span class="text-secondary">нет</span>';
      return '<tr class="' + (worst ? "dc-row-" + worst : "") + '" data-anchor="' + esc(l.id) + '">' +
        '<td class="text-secondary dc-n" data-label="№">' + l.n + '</td><td class="dc-name">' + esc(l.name) + (l.spec && l.spec.name !== l.name ? '<div class="small text-secondary">в спецификации: ' + esc(l.spec.name) + "</div>" : "") + "</td>" +
        '<td class="text-end" data-label="Кол-во">' + esc(l.qty) + " " + esc(l.unit) + '</td><td class="text-end" data-label="В заказе">' + ord + "</td>" +
        '<td class="text-end" data-label="Цена">' + esc(l.price) + '</td><td class="text-end" data-label="По спецификации">' + spec + '</td><td class="text-end" data-label="Сумма">' + esc(l.total) + "</td>" +
        '<td class="dc-lv">' + (worst ? badge(worst) : '<span class="text-green">' + icon("circle-check") + "</span>") + "</td></tr>";
    }).join("");
    var t = r.totals;
    return '<div class="table-responsive"><table class="table table-vcenter card-table table-mobile-md dc-lines"><thead><tr><th class="w-1">№</th><th>Наименование</th><th class="text-end">Кол-во</th><th class="text-end">В заказе</th><th class="text-end">Цена</th><th class="text-end">По спецификации</th><th class="text-end">Сумма</th><th class="w-1"></th></tr></thead><tbody>' + rows + "</tbody></table></div>" +
      '<div class="card-footer"><div class="datagrid dc-totals">' +
      [["Сумма строк", t.lines], ["Итого в счёте", t.total], ["НДС в счёте", t.vat], ["Всего к оплате", t.to_pay]].map(function (x) {
        return '<div class="datagrid-item"><div class="datagrid-title">' + x[0] + '</div><div class="datagrid-content">' + esc(x[1]) + "</div></div>";
      }).join("") + "</div></div>";
  }

  var REQ = [["inn", "ИНН"], ["kpp", "КПП"], ["ogrn", "ОГРН"], ["bank", "Банк"], ["bik", "БИК"], ["account", "Р/с"], ["corr_account", "К/с"]];
  function reqHtml(q) {
    return REQ.filter(function (k) { return q[k[0]]; }).map(function (k) {
      return '<div class="datagrid-item"><div class="datagrid-title">' + k[1] + '</div><div class="datagrid-content dc-num">' + esc(q[k[0]]) + "</div></div>";
    }).join("");
  }
  function fieldsHtml(r) {
    return '<div class="card-body"><div class="datagrid">' + r.fields.filter(function (f) { return !f.requisites; }).map(function (f) {
      return '<div class="datagrid-item"><div class="datagrid-title">' + esc(f.name) + '</div><div class="datagrid-content">' + esc(f.value) + "</div></div>";
    }).join("") + "</div></div>" +
      r.fields.filter(function (f) { return f.requisites; }).map(function (f) {
        return '<div class="card-body border-top"><div class="subheader mb-1">' + esc(f.name) + '</div><div class="fw-medium mb-3">' + esc(f.value) + '</div><div class="datagrid">' + reqHtml(f.requisites) + "</div></div>";
      }).join("");
  }

  // ------------------------------------------------------------------ company pages

  var company = null, companyLoading = null;
  function loadCompany() {
    if (companyLoading) return companyLoading;
    companyLoading = api("company").then(function (co) {
      company = co;
      $("org-name").textContent = co.name;
      if (co.requisites && co.requisites.inn) $("org-inn").textContent = "ИНН " + co.requisites.inn;
      $("count-reference").textContent = co.reference.length;
      $("count-rules").textContent = co.rules.length;
      $("count-orders").textContent = co.orders.length;
      renderCompany(co);
    }).catch(function () { companyLoading = null; });
    return companyLoading;
  }

  function renderCompany(co) {
    var section = null, ref = [];
    co.reference.forEach(function (c) {
      if (c.section !== section) {
        if (section !== null) ref.push("</div>");
        section = c.section;
        ref.push('<div class="dc-ref-section"><h3 class="dc-ref-title">' + esc(section) + "</h3>");
      }
      ref.push('<div class="dc-ref-clause"><span class="dc-ref-num">' + esc(c.number) + "</span><span>" + esc(c.text) + "</span></div>");
    });
    if (section !== null) ref.push("</div>");
    $("reference").innerHTML = ref.join("");

    var CHECK = { forbid: "Такого пункта быть не должно", require: "Пункт обязателен", max: "Не больше ", min: "Не меньше " };
    $("rules").innerHTML = co.rules.map(function (r) {
      var check = CHECK[r.check] + (r.limit != null ? num(r.limit) : "");
      return '<tr><td data-label="Уровень">' + badge(r.level) + '</td><td data-label="Правило" class="fw-medium">' + esc(r.title) + '</td><td data-label="Почему" class="text-secondary dc-why">' + esc(r.why) + '</td><td data-label="Проверка" class="text-nowrap">' + esc(check) + "</td></tr>";
    }).join("");

    var cards = [];
    if (co.requisites) {
      cards.push('<div class="col-lg-5"><div class="card"><div class="card-header"><div class="dc-file"><span class="avatar bg-primary text-white">К</span><div><h3 class="card-title">' + esc(co.name) + '</h3><div class="card-subtitle">Покупатель, реквизиты в эталоне</div></div></div></div><div class="card-body"><div class="datagrid">' + reqHtml(co.requisites) + "</div></div></div></div>");
    }
    co.suppliers.forEach(function (s) {
      var initials = s.name.replace(/^[^«]*«|»$/g, "").split(/\s+/).map(function (w) { return w.charAt(0); }).join("").slice(0, 2).toUpperCase();
      cards.push('<div class="col-lg-7"><div class="card">' +
        '<div class="card-header"><div class="dc-file"><span class="avatar bg-green-lt text-green">' + esc(initials) + '</span><div><h3 class="card-title">' + esc(s.name) + '</h3><div class="card-subtitle">Поставщик, договор ' + esc(s.contract) + "</div></div></div></div>" +
        '<div class="card-body"><div class="datagrid">' + reqHtml(s.requisites) + "</div></div>" +
        '<div class="card-header border-top"><h3 class="card-title">Спецификация</h3><div class="card-actions text-secondary small">цены с НДС ' + co.vat_rate + " %</div></div>" +
        '<div class="table-responsive"><table class="table table-vcenter card-table"><thead><tr><th>Позиция</th><th>Ед.</th><th class="text-end">Цена</th></tr></thead><tbody>' +
        s.spec.map(function (i) { return "<tr><td>" + esc(i.name) + '</td><td class="text-secondary">' + esc(i.unit) + '</td><td class="text-end text-nowrap dc-num">' + rub(i.price) + "</td></tr>"; }).join("") +
        "</tbody></table></div></div></div>");
    });
    $("suppliers").innerHTML = cards.join("");

    $("orders").innerHTML = co.orders.map(function (o) {
      return '<div class="col-lg-6"><div class="card">' +
        '<div class="card-header"><div class="dc-file"><span class="avatar bg-azure-lt text-azure">' + icon("clipboard-list") + '</span><div><h3 class="card-title">Заказ № ' + esc(o.number) + '</h3><div class="card-subtitle">от ' + esc(o.date) + (o.title ? " · " + esc(o.title) : "") + "</div></div></div>" +
        '<div class="card-actions"><span class="badge bg-secondary-lt">' + o.lines.length + " " + plural(o.lines.length, "позиция", "позиции", "позиций") + "</span></div></div>" +
        '<table class="table table-vcenter card-table"><thead><tr><th>Позиция</th><th class="text-end">Количество</th></tr></thead><tbody>' +
        o.lines.map(function (l) { return "<tr><td>" + esc(l.name) + '</td><td class="text-end text-nowrap dc-num">' + esc(l.qty) + " " + esc(l.unit) + "</td></tr>"; }).join("") +
        "</tbody></table></div></div>";
    }).join("");
  }

  // ------------------------------------------------------------------ navigation

  var PAGES = ["check", "reference", "rules", "suppliers", "orders"];
  function showPage(page) {
    if (PAGES.indexOf(page) < 0) page = "check";
    PAGES.forEach(function (p) { $("page-" + p).hidden = p !== page; });
    document.querySelectorAll(".navbar-nav .nav-link[data-page]").forEach(function (a) {
      var on = a.getAttribute("data-page") === page;
      a.parentNode.classList.toggle("active", on);
      if (on) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
    menu(false);
    if (page !== "check") loadCompany();
  }
  function menu(open) {
    var t = $("menu-toggle");
    $("sidebar-menu").classList.toggle("show", open);
    t.setAttribute("aria-expanded", open);
    t.setAttribute("aria-label", open ? "Закрыть меню" : "Меню");
    t.innerHTML = icon(open ? "x" : "menu");
  }

  // ------------------------------------------------------------------ events

  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-example],[data-rtab],[data-goto],[data-page],#menu-toggle");
    if (!t) return;
    if (t.id === "menu-toggle") menu(!$("sidebar-menu").classList.contains("show"));
    else if (t.hasAttribute("data-example")) openExample(t.getAttribute("data-example"), window.innerWidth < 992);
    else if (t.hasAttribute("data-rtab")) { state.tab = t.getAttribute("data-rtab"); renderPanel(); }
    else if (t.hasAttribute("data-goto")) { state.tab = "doc"; renderPanel(t.getAttribute("data-goto")); }
    else if (t.hasAttribute("data-page")) {
      e.preventDefault();
      var page = t.getAttribute("data-page");
      if (history.replaceState) history.replaceState(null, "", "#" + page);
      showPage(page);
      window.scrollTo(0, 0);
    }
  });
  $("file").addEventListener("change", function () { upload(this.files[0]); });
  var drop = $("drop");
  ["dragenter", "dragover"].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add("dc-drop-over"); }); });
  ["dragleave", "drop"].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove("dc-drop-over"); }); });
  drop.addEventListener("drop", function (e) { if (e.dataTransfer.files[0]) upload(e.dataTransfer.files[0]); });

  window.DocCheck = { open: openExample, upload: upload, page: showPage };
  paintIcons(document);
  showPage(location.hash.slice(1));
  loadExamples();
  loadCompany();
})();
