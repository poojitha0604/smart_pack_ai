// SmartPack AI frontend. Talks to the Flask backend (same origin when served by Flask).
var API = window.SMARTPACK_API || "/api";
var $ = function (i) { return document.getElementById(i); };
var FOOD_NAMES = ["Apple", "Banana", "Mango", "Orange", "Tomato", "Potato", "Onion", "Carrot", "Potato Chips", "Bread"];
var S = { img: "", note: null, res: null };

function fillSel(id, vals) {
  var el = $(id), v = el.value;
  el.innerHTML = vals.map(function (x) { return '<option value="' + x + '">' + t(x) + "</option>"; }).join("");
  if (v) el.value = v;
}

function fillFood() {
  var el = $("food"), v = el.value;
  el.innerHTML = '<option value="">' + t("pick") + "</option>" +
    FOOD_NAMES.map(function (x) { return '<option value="' + x + '">' + t(x) + "</option>"; }).join("");
  el.value = v;   // "" (nothing chosen) until the user or the detector picks a food
}
function updateItem() { $("itemName").textContent = $("food").value ? t($("food").value) : t("pick"); }
$("food").onchange = updateItem;

function noteText() {
  if (!S.note) return "";
  var k = S.note[0];
  if (k === "n_det") return t(k, t(S.note[1]), S.note[2]);
  if (k === "n_low") return t(k, S.note[1].map(function (f) { return t(f); }).join(", "));
  if (k === "n_guess" || k === "n_ai") return t(k, t(S.note[1]));
  return t(k);
}

function apply() {
  document.documentElement.lang = ["en", "hi", "te"][li];
  document.querySelectorAll("[data-i]").forEach(function (e) { e.textContent = t(e.getAttribute("data-i")); });
  fillFood();
  fillSel("storage", ["Ambient", "Chilled", "Frozen"]);
  $("detNote").textContent = noteText();
  updateItem();
  if (S.res) render();
}

function show(n) {
  ["p1", "p2", "p3"].forEach(function (p, i) {
    $(p).classList.toggle("hide", i + 1 !== n);
  });
  window.scrollTo(0, 0);
}

// ---- language ----
$("lang").onchange = function () {
  li = +this.value;
  try { localStorage.setItem("sp_lang", li); } catch (e) {}
  apply();
};
try { var sv = localStorage.getItem("sp_lang"); if (sv) { li = +sv; $("lang").value = sv; } } catch (e) {}

// ---- step 1: upload + detect (POST /api/detect-food) ----
$("drop").onclick = function () { $("file").click(); };
$("file").onchange = async function (e) {
  var f = e.target.files[0];
  if (!f) return;
  S.img = URL.createObjectURL(f);
  $("prev").src = S.img;
  S.note = ["working"];
  $("food").value = "";          // never keep the previous (or first) food by accident
  apply();
  show(2);
  var fd = new FormData();
  fd.append("image", f);
  try {
    var r = await fetch(API + "/detect-food", { method: "POST", body: fd });
    var d = await r.json();
    var preds = d.predictions || [];
    if (d.status === "ok") S.note = ["n_det", preds[0].food, Math.round(preds[0].probability * 100)];
    else if (d.status === "ai") S.note = ["n_ai", preds[0].food];
    else if (d.status === "none") S.note = ["n_none"];
    else if (d.status === "low_confidence") S.note = ["n_low", preds.map(function (p) { return p.food; })];
    else if (preds.length) S.note = ["n_guess", preds[0].food];
    else S.note = ["n_manual"];
    apply();
    if (preds.length) $("food").value = preds[0].food;
    updateItem();
  } catch (err) {
    S.note = ["n_err"];
    apply();
  }
};
$("back1").onclick = function () { show(1); };

// ---- step 2: details -> recommendation (POST /api/recommend) ----
$("go").onclick = async function () {
  if (!$("food").value) { alert(t("pick")); return; }
  var body = {
    food: $("food").value,
    shelf_life: +$("life").value || 1,
    storage_type: $("storage").value,
    travel_hours: +$("hours").value || 1,
    temperature: +$("temp").value
  };
  $("go").disabled = true;
  try {
    var r = await fetch(API + "/recommend", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
    });
    var d = await r.json();
    if (!r.ok) throw new Error(d.error || "error");
    S.res = d;
    render();
    show(3);
  } catch (err) {
    alert(t("err_rec"));
  }
  $("go").disabled = false;
};

// ---- step 3: result page (dynamic: same page for every food) ----
function lv(level, value) { return t("v_" + level) + (value ? " (" + String(value).replace(/</g, "&lt;") + ")" : ""); }

function render() {
  var d = S.res, f = d.food, p = d.packaging, i = d.inputs;
  var rows = [
    ["OTR", lv(p.otr_level, p.otr_value)],
    ["WVTR", lv(p.wvtr_level, p.wvtr_value)],
    ["thk", p.thickness],
    ["seal", t("v_" + p.sealability)],
    ["strg", t("v_" + p.strength)],
    ["map", t(p.map_suitable ? "yes" : "no")]
  ];
  var why = [t(f.category) + " · " + t("moisture") + ": " + t("v_" + f.moisture) + " · " + t("fat") + ": " + t("v_" + f.fat)]
    .concat(d.why.map(function (k) { return t(k); }));
  var hrs = i.travel_hours || "";
  why.push(t("storage") + ": " + t(i.storage_type) + " · " + t("hrs") + ": " + hrs + " · " + t("life") + ": " + i.shelf_life);
  var method = d.method === "ml" ? t("m_ml", Math.round((d.model_probability || 0) * 100)) : t("m_rules");
  var g = d.guide;
  function items(arr) { return "<ul>" + arr.map(function (x) { return "<li>" + x + "</li>"; }).join("") + "</ul>"; }

  $("p3").innerHTML =
    '<div class="grid"><div class="card"><img class="food" src="' + S.img + '" alt="' + t(f.name) + '">' +
    '<div class="itemlbl" style="margin-top:14px">' + t("item") + '</div><h1>' + f.emoji + " " + t(f.name) + "</h1>" +
    '<span class="tag">' + t(f.category) + '</span><span class="tag">' + t("moisture") + ": " + t("v_" + f.moisture) +
    '</span><span class="tag">' + t("fat") + ": " + t("v_" + f.fat) + '</span><span class="tag">' + t("v_" + f.ph) +
    '</span><span class="tag">' + t("resp") + ": " + t("v_" + f.respiration) + "</span></div>" +
    '<div class="card"><p style="margin:0">' + t("rec") + '</p><div class="big">' + t(p.id) + "</div><table>" +
    rows.map(function (r) { return "<tr><td>" + t(r[0]) + "</td><td>" + r[1] + "</td></tr>"; }).join("") +
    '</table><p style="font-size:12px;margin:10px 0 0">' + method + "</p></div></div>" +

    '<div class="card guide"><h2>' + t("pack_h") + '</h2><p><span class="tag risk risk-' + g.risk + '">' + t("risk") + ": " + t("v_" + g.risk) + "</span></p>" +
    "<p>" + t(g.causes) + "</p>" +
    "<h3>" + t("steps_h") + "</h3>" + items(g.packing_steps.map(function (k) { return t(k); })) +
    "<h3>" + t("travel_h") + " (" + hrs + " " + t("hr_u") + ")</h3><p>" + t(g.travel_tip) + "</p>" +
    "<h3>" + t("temp_h") + " (" + i.temperature + " °C)</h3>" +
    g.temperature_tips.map(function (x) { return "<p>" + t(x.key, x.arg || "") + "</p>"; }).join("") + "</div>" +

    '<div class="card"><h2>' + t("why") + "</h2>" + items(why) + "</div>" +
    '<div class="card"><h2>' + t("stor") + "</h2><p>" + f.storage_temp + ". " + t(f.note) + '.</p><p style="margin:0">' +
    t("plan") + ": " + t(i.storage_type) + ", " + i.temperature + " °C, " + i.shelf_life + "</p></div>" +
    '<div class="grid"><div class="card"><h2>' + t("alt") + '</h2><p style="margin:0">' + t(d.alternative.id) +
    '</p></div><div class="card"><h2>' + t("eco") + '</h2><p style="margin:0">' + t(d.eco_option.id) + "</p></div></div>" +
    '<p style="font-size:12px">' + t("foot") + '</p><button class="btn" id="again">' + t("again") + "</button>";
  $("again").onclick = function () { $("file").value = ""; S.res = null; show(1); };
}

apply();
