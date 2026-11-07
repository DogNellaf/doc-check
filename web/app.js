/* The checker's page: examples, an upload, the result with findings, the document and its fields,
   and what the company checks against. Plain JS, no build. */
(function () {
  "use strict";

  /* Icons from Lucide (ISC license, lucide.dev), 24×24 stroke paths */
  var ICONS = {
    "file-text": '<path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"/><path d="M14 2v5a1 1 0 0 0 1 1h5"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "file-check": '<path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"/><path d="M14 2v5a1 1 0 0 0 1 1h5"/><path d="m9 15 2 2 4-4"/>',
    upload: '<path d="M12 3v12"/><path d="m17 8-5-5-5 5"/><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>',
    download: '<path d="M12 15V3"/><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/>',
    "triangle-alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "circle-check": '<circle cx="12" cy="12" r="10"/><path d="m16 9-5.5 5.5L8 12"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "scan-text": '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 8h8"/><path d="M7 12h10"/><path d="M7 16h6"/>',
    receipt: '<path d="M12 17V7"/><path d="M16 8h-6a2 2 0 0 0 0 4h4a2 2 0 0 1 0 4H8"/><path d="M4 3a1 1 0 0 1 1-1 1.3 1.3 0 0 1 .7.2l.933.6a1.3 1.3 0 0 0 1.4 0l.934-.6a1.3 1.3 0 0 1 1.4 0l.933.6a1.3 1.3 0 0 0 1.4 0l.933-.6a1.3 1.3 0 0 1 1.4 0l.934.6a1.3 1.3 0 0 0 1.4 0l.933-.6A1.3 1.3 0 0 1 19 2a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1 1.3 1.3 0 0 1-.7-.2l-.933-.6a1.3 1.3 0 0 0-1.4 0l-.934.6a1.3 1.3 0 0 1-1.4 0l-.933-.6a1.3 1.3 0 0 0-1.4 0l-.933.6a1.3 1.3 0 0 1-1.4 0l-.934-.6a1.3 1.3 0 0 0-1.4 0l-.933.6a1.3 1.3 0 0 1-.7.2 1 1 0 0 1-1-1z"/>',
    "file-spreadsheet": '<path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"/><path d="M14 2v5a1 1 0 0 0 1 1h5"/><path d="M8 13h2"/><path d="M14 13h2"/><path d="M8 17h2"/><path d="M14 17h2"/>',
    "file-pen": '<path d="M12.659 22H18a2 2 0 0 0 2-2V8a2.4 2.4 0 0 0-.706-1.706l-3.588-3.588A2.4 2.4 0 0 0 14 2H6a2 2 0 0 0-2 2v9.34"/><path d="M14 2v5a1 1 0 0 0 1 1h5"/><path d="M10.378 12.622a1 1 0 0 1 3 3.003L8.36 20.637a2 2 0 0 1-.854.506l-2.867.837a.5.5 0 0 1-.62-.62l.836-2.869a2 2 0 0 1 .506-.853z"/>',
    "shield-check": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "book-open": '<path d="M12 5v16"/><path d="M20.001 19A2 2 0 0022 17V5a2 2 0 00-1.999-2L16 3.002A5 5 0 0012 5a5 5 0 00-4-2H4a2 2 0 00-2 2v12a2 2 0 001.999 2H8a5 5 0 014 2 5 5 0 014-2z"/>'
  };
  function icon(name, cls) {
    return '<svg class="dc-icon ' + (cls || "") + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICONS[name] || "") + "</svg>";
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

  var LEVEL = {
    high: { name: "Критично", cls: "bg-red-lt text-red", icon: "triangle-alert" },
    medium: { name: "Согласовать", cls: "bg-yellow-lt text-yellow", icon: "triangle-alert" },
    low: { name: "Обратить внимание", cls: "bg-secondary-lt text-secondary", icon: "info" }
  };
  var VERDICT = { high: "danger", medium: "warning", low: "info", ok: "success" };
  var STATUS = {
    same: ["Как в эталоне", "dc-st-same"],
    reworded: ["Другая формулировка", "dc-st-reworded"],
    changed: ["Другие цифры", "dc-st-changed"],
    extra: ["Нет в эталоне", "dc-st-extra"]
  };

  var state = { current: null, examples: [], tab: "findings", busy: false };

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
    $("quota").textContent = "Своих проверок сегодня: осталось " + remaining + " из " + (limit || 10) + ". Примеры — без ограничений.";
  }

  function loadExamples() {
    api("examples").then(function (data) {
      state.examples = data.examples;
      state.limit = data.limit;
      quota(data.remaining, data.limit);
      renderExamples();
      var first = data.examples.filter(function (e) { return e.ready; })[0];
      if (first) openExample(first.id);
      else $("result").innerHTML = '<div class="card"><div class="card-body text-secondary">Примеры не загрузились. Загрузите свой документ.</div></div>';
    }).catch(function () {
      $("result").innerHTML = '<div class="card"><div class="card-body text-danger">Сервис проверки сейчас недоступен. Обновите страницу через минуту.</div></div>';
    });
  }

  function renderExamples() {
    $("examples").innerHTML = state.examples.map(function (e) {
      var v = e.verdict;
      var ic = e.id === "scan" ? "scan-text" : e.kind === "invoice" ? "receipt" : "file-text";
      return '<button type="button" class="list-group-item list-group-item-action dc-ex' + (state.current && state.current.example === e.id ? " active" : "") + '" data-example="' + esc(e.id) + '"' + (e.ready ? "" : " disabled") + ">" +
        '<span class="dc-ex-icon">' + icon(ic) + "</span>" +
        '<span class="dc-ex-text"><b>' + esc(e.title) + '</b><span class="text-secondary small">' + esc(e.note) + "</span>" +
        (v ? '<span class="badge ' + LEVEL_BADGE(v.level) + ' mt-1">' + esc(v.text) + "</span>" : '<span class="small text-secondary">недоступен</span>') +
        "</span></button>";
    }).join("");
  }
  function LEVEL_BADGE(level) {
    return { high: "bg-red-lt", medium: "bg-yellow-lt", low: "bg-azure-lt", ok: "bg-green-lt" }[level] || "";
  }

  function openExample(id, scroll) {
    api("examples/" + encodeURIComponent(id)).then(function (r) {
      show(r);
      // on a phone the result is below the list: bring it into view after a tap
      if (scroll && window.innerWidth < 992) $("result").scrollIntoView({ block: "start", behavior: "smooth" });
    });
  }

  function upload(file) {
    if (!file || state.busy) return;
    state.busy = true;
    $("drop").classList.add("dc-drop-busy");
    $("result").innerHTML = '<div class="card"><div class="card-body"><div class="d-flex align-items-center gap-3"><div class="spinner-border text-primary" role="status"></div><div><b>Проверяю «' + esc(file.name) + '»</b><div class="text-secondary small">Читаю текст, сверяю пункты и строки. Скан распознаётся до полуминуты.</div></div></div></div></div>';
    var form = new FormData();
    form.append("file", file);
    api("check", { method: "POST", body: form }).then(function (r) {
      quota(r.remaining, state.limit);
      show(r);
    }).catch(function (e) {
      if (e.body) quota(e.body.remaining, state.limit);
      $("result").innerHTML = '<div class="alert alert-' + (e.body && e.body.kind === "limit" ? "warning" : "danger") + '" role="alert">' + esc(e.message) + "</div>";
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
    var src = r.ocr ? '<span class="badge bg-purple-lt">' + icon("scan-text") + " скан, распознан OCR</span>" : '<span class="badge bg-secondary-lt">' + esc((r.fmt || "").toUpperCase()) + "</span>";
    if (r.lines_by === "model") src += ' <span class="badge bg-purple-lt">строки прочитала модель</span>';
    var fileLink = r.example ? '<a href="examples/' + encodeURIComponent(r.file) + '" target="_blank" rel="noopener">' + esc(r.file) + "</a>" : esc(r.file);
    var n = r.findings.length;
    var html =
      '<div class="card dc-result">' +
      '<div class="card-header dc-result-head">' +
      '<div class="dc-result-file">' + icon(isContract ? "file-text" : "receipt") + "<div><div class=\"fw-bold\">" + fileLink + '</div><div class="small text-secondary">' + (isContract ? "Договор · сверка с эталоном и правилами" : "Счёт · сверка с договором, спецификацией и заказом") + " " + src + "</div></div></div>" +
      '<div class="dc-downloads">' +
      '<a class="btn btn-outline-secondary btn-sm" href="api/report/' + encodeURIComponent(r.id) + '.xlsx">' + icon("file-spreadsheet") + "Excel</a>" +
      '<a class="btn btn-primary btn-sm" href="api/report/' + encodeURIComponent(r.id) + '.docx">' + icon("file-pen") + (isContract ? "Word с правками" : "Письмо поставщику") + "</a>" +
      "</div></div>" +
      '<div class="card-body pb-0">' +
      '<div class="alert alert-' + VERDICT[v.level] + ' dc-verdict" role="status">' + icon(v.level === "ok" ? "circle-check" : "triangle-alert") +
      '<div><b>' + esc(v.text) + '</b><div class="small">' +
      (n ? "Критично: " + c.high + " · согласовать: " + c.medium + " · обратить внимание: " + c.low : "Замечаний нет") + "</div></div></div>" +
      '<ul class="nav nav-tabs dc-rtabs" role="tablist">' +
      tab("findings", "Замечания", n) + tab("doc", isContract ? "Пункты договора" : "Строки счёта", isContract ? r.clauses.length : r.lines.length) + tab("fields", "Поля", null) +
      "</ul></div>" +
      '<div class="card-body" id="rpanel"></div></div>';
    $("result").innerHTML = html;
    renderPanel();
  }

  function tab(id, name, count) {
    return '<li class="nav-item" role="presentation"><button type="button" class="nav-link' + (state.tab === id ? " active" : "") + '" data-rtab="' + id + '" role="tab" aria-selected="' + (state.tab === id) + '">' + esc(name) + (count != null ? ' <span class="badge bg-secondary-lt ms-1">' + count + "</span>" : "") + "</button></li>";
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
    if (!r.findings.length) return '<div class="text-secondary">Расхождений не нашлось.</div>';
    var isContract = r.kind === "contract";
    return '<div class="dc-findings">' + r.findings.map(function (f) {
      var lv = LEVEL[f.level];
      var fixLabel = f.kind === "missing" ? "Вернуть пункт эталона " + f.ref : f.ref ? "Как в эталоне, п. " + f.ref : "Должно быть";
      return '<div class="dc-finding dc-l-' + f.level + '">' +
        '<div class="dc-finding-head"><span class="badge ' + lv.cls + '">' + esc(lv.name) + "</span>" +
        (f.where ? '<span class="text-secondary small">' + esc(f.where) + "</span>" : "") +
        (f.anchor ? '<button type="button" class="btn btn-link btn-sm p-0 ms-auto" data-goto="' + esc(f.anchor) + '">показать в ' + (isContract ? "договоре" : "счёте") + "</button>" : "") + "</div>" +
        '<div class="dc-finding-title">' + esc(f.title) + "</div>" +
        (f.why ? '<div class="dc-finding-why">' + esc(f.why) + "</div>" : "") +
        (f.quote && isContract ? '<blockquote class="dc-quote">' + esc(f.quote) + "</blockquote>" : "") +
        (f.fix ? '<div class="dc-fix"><span class="small text-secondary">' + esc(fixLabel) + ":</span> " + esc(f.fix) + "</div>" : "") +
        "</div>";
    }).join("") + "</div>";
  }

  function diffHtml(ops) {
    return ops.map(function (o) {
      if (o[0] === "=") return esc(o[1]);
      return o[0] === "-" ? '<del class="dc-del">' + esc(o[1]) + "</del>" : '<ins class="dc-ins">' + esc(o[1]) + "</ins>";
    }).join(" ");
  }

  function clausesHtml(r) {
    var section = null, out = ['<div class="dc-legend small text-secondary mb-2"><span class="dc-del">зачёркнуто</span> — как в эталоне, <span class="dc-ins">подчёркнуто</span> — как у поставщика</div><div class="dc-clauses">'];
    var missing = {};
    r.findings.forEach(function (f) { if (f.kind === "missing") (missing[f.anchor] = missing[f.anchor] || []).push(f); });
    r.clauses.forEach(function (c) {
      if (c.section !== section) {
        section = c.section;
        out.push('<div class="dc-section">' + esc(section) + "</div>");
      }
      var st = STATUS[c.status];
      var worst = ["high", "medium", "low"].filter(function (l) { return c.levels.indexOf(l) >= 0; })[0];
      var body = c.status === "reworded" || c.status === "changed" ? diffHtml(c.diff) : esc(c.text);
      out.push('<div class="dc-clause ' + st[1] + (worst ? " dc-l-" + worst : "") + '" data-anchor="' + esc(c.id) + '">' +
        '<div class="dc-clause-num">' + esc(c.number) + "</div>" +
        '<div class="dc-clause-body">' + body +
        '<div class="dc-clause-meta"><span class="dc-st">' + st[0] + (c.ref && c.ref !== c.number ? ", п. " + esc(c.ref) + " эталона" : "") + "</span>" +
        (c.dense != null && c.status !== "same" ? '<span class="text-secondary" title="Сходство по смыслу и доля общих слов с пунктом эталона">смысл ' + c.dense.toFixed(2) + " · слова " + c.lexical.toFixed(2) + "</span>" : "") +
        (worst ? '<span class="badge ' + LEVEL[worst].cls + '">' + LEVEL[worst].name + "</span>" : "") +
        "</div></div></div>");
      (missing[c.id] || []).forEach(function (f) {
        out.push('<div class="dc-clause dc-st-missing dc-l-medium" data-anchor="' + esc(f.anchor) + '-missing"><div class="dc-clause-num">' + esc(f.ref) + '</div><div class="dc-clause-body"><ins class="dc-ins-missing">' + esc(f.fix) + '</ins><div class="dc-clause-meta"><span class="dc-st">Нет в договоре, есть в эталоне</span></div></div></div>');
      });
    });
    out.push("</div>");
    return out.join("");
  }

  function linesHtml(r) {
    if (!r.lines.length) return '<div class="text-secondary">Строки счёта не распознаны.</div>';
    var rows = r.lines.map(function (l) {
      var worst = ["high", "medium", "low"].filter(function (x) { return l.issues.indexOf(x) >= 0; })[0];
      var spec = l.spec ? (l.spec.price === l.price ? '<span class="text-secondary">' + esc(l.spec.price) + "</span>" : '<b class="text-red">' + esc(l.spec.price) + "</b>") : '<span class="text-secondary">нет</span>';
      var ord = l.ordered != null ? (l.ordered === l.qty ? '<span class="text-secondary">' + esc(l.ordered) + "</span>" : '<b class="text-red">' + esc(l.ordered) + "</b>") : '<span class="text-secondary">нет</span>';
      return '<tr class="' + (worst ? "dc-row-" + worst : "") + '" data-anchor="' + esc(l.id) + '">' +
        "<td>" + l.n + "</td><td>" + esc(l.name) + (l.spec && l.spec.name !== l.name ? '<div class="small text-secondary">в спецификации: ' + esc(l.spec.name) + "</div>" : "") + "</td>" +
        '<td class="text-end">' + esc(l.qty) + " " + esc(l.unit) + '</td><td class="text-end">' + ord + "</td>" +
        '<td class="text-end">' + esc(l.price) + '</td><td class="text-end">' + spec + '</td><td class="text-end">' + esc(l.total) + "</td>" +
        "<td>" + (worst ? '<span class="badge ' + LEVEL[worst].cls + '">' + LEVEL[worst].name + "</span>" : '<span class="text-green">' + icon("circle-check") + "</span>") + "</td></tr>";
    }).join("");
    var t = r.totals;
    return '<div class="table-responsive"><table class="table table-vcenter card-table dc-lines"><thead><tr><th>№</th><th>Наименование</th><th class="text-end">Кол-во</th><th class="text-end">В заказе</th><th class="text-end">Цена</th><th class="text-end">По спецификации</th><th class="text-end">Сумма</th><th></th></tr></thead><tbody>' + rows + "</tbody></table></div>" +
      '<dl class="dc-totals"><dt>Сумма строк</dt><dd>' + esc(t.lines) + "</dd><dt>Итого в счёте</dt><dd>" + esc(t.total) + "</dd><dt>НДС в счёте</dt><dd>" + esc(t.vat) + "</dd><dt>Всего к оплате</dt><dd>" + esc(t.to_pay) + "</dd></dl>";
  }

  var REQ = [["inn", "ИНН"], ["kpp", "КПП"], ["ogrn", "ОГРН"], ["account", "Р/с"], ["bank", "Банк"], ["bik", "БИК"], ["corr_account", "К/с"]];
  function fieldsHtml(r) {
    return '<dl class="dc-fields">' + r.fields.map(function (f) {
      var req = f.requisites ? REQ.filter(function (k) { return f.requisites[k[0]]; }).map(function (k) {
        return '<span class="dc-req"><span class="text-secondary">' + k[1] + "</span> " + esc(f.requisites[k[0]]) + "</span>";
      }).join("") : "";
      return "<dt>" + esc(f.name) + "</dt><dd>" + esc(f.value) + (req ? '<div class="dc-reqs">' + req + "</div>" : "") + "</dd>";
    }).join("") + "</dl>";
  }

  // ------------------------------------------------------------------ company page

  var companyLoaded = false;
  function loadCompany() {
    if (companyLoaded) return;
    companyLoaded = true;
    api("company").then(function (co) {
      var section = null;
      $("reference").innerHTML = co.reference.map(function (c) {
        var h = c.section !== section ? '<div class="dc-section">' + esc((section = c.section)) + "</div>" : "";
        return h + '<p><b>' + esc(c.number) + ".</b> " + esc(c.text) + "</p>";
      }).join("");
      $("rules").innerHTML = co.rules.map(function (r) {
        return '<div class="list-group-item"><span class="badge ' + LEVEL[r.level].cls + ' mb-1">' + LEVEL[r.level].name + "</span><div class=\"fw-bold\">" + esc(r.title) + '</div><div class="small text-secondary">' + esc(r.why) + "</div></div>";
      }).join("");
      $("suppliers").innerHTML = co.suppliers.map(function (s) {
        return "<div class=\"fw-bold\">" + esc(s.name) + '</div><div class="small text-secondary mb-2">Договор ' + esc(s.contract) + " · р/с " + esc(s.requisites.account) + ", БИК " + esc(s.requisites.bik) + ", " + esc(s.requisites.bank) + "</div>" +
          '<table class="table table-sm"><tbody>' + s.spec.map(function (i) { return "<tr><td>" + esc(i.name) + '</td><td class="text-end text-nowrap">' + esc(Number(i.price).toLocaleString("ru-RU", { minimumFractionDigits: 2 })) + " ₽</td></tr>"; }).join("") + "</tbody></table>";
      }).join("") + '<div class="small text-secondary">Цены с НДС ' + co.vat_rate + " %.</div>";
      $("orders").innerHTML = co.orders.map(function (o) {
        return '<div class="fw-bold">Заказ № ' + esc(o.number) + " от " + esc(o.date) + '</div><ul class="small mb-3">' + o.lines.map(function (l) { return "<li>" + esc(l.name) + " — " + esc(l.qty) + " " + esc(l.unit) + "</li>"; }).join("") + "</ul>";
      }).join("");
    }).catch(function () { companyLoaded = false; });
  }

  // ------------------------------------------------------------------ events

  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-example],[data-rtab],[data-goto],[data-page]");
    if (!t) return;
    if (t.hasAttribute("data-example")) openExample(t.getAttribute("data-example"), true);
    else if (t.hasAttribute("data-rtab")) { state.tab = t.getAttribute("data-rtab"); renderPanel(); }
    else if (t.hasAttribute("data-goto")) { state.tab = "doc"; renderPanel(t.getAttribute("data-goto")); }
    else if (t.hasAttribute("data-page")) {
      var page = t.getAttribute("data-page");
      document.querySelectorAll("[data-page]").forEach(function (b) {
        var on = b === t;
        b.classList.toggle("active", on);
        if (on) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
      });
      $("page-check").hidden = page !== "check";
      $("page-company").hidden = page !== "company";
      if (page === "company") loadCompany();
    }
  });
  $("file").addEventListener("change", function () { upload(this.files[0]); });
  var drop = $("drop");
  ["dragenter", "dragover"].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add("dc-drop-over"); }); });
  ["dragleave", "drop"].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove("dc-drop-over"); }); });
  drop.addEventListener("drop", function (e) { if (e.dataTransfer.files[0]) upload(e.dataTransfer.files[0]); });

  window.DocCheck = { open: openExample, upload: upload };
  paintIcons(document);
  loadExamples();
})();
