/* nCoin v0.6 — P2P platform. Vanilla ES modules, no build. Black & gold. */

const tg = window.Telegram?.WebApp;
const $ = (id) => document.getElementById(id);

/* ───────── icons ───────── */
const P = {
  home: '<path d="M3 10.5 12 3l9 7.5M5 9.5V21h5v-6h4v6h5V9.5"/>',
  chart: '<path d="M4 19h16M6 16l4-5 3 3 5-7"/>',
  up: '<path d="M12 20V7M12 4l6 6M12 4 6 10"/>',
  trophy: '<path d="M8 21h8M12 17v4M7 4h10v4a5 5 0 0 1-10 0zM7 5H4v2a3 3 0 0 0 3 3M17 5h3v2a3 3 0 0 1-3 3"/>',
  wallet: '<path d="M3 7a2 2 0 0 1 2-2h13v3M3 7v10a2 2 0 0 0 2 2h14a1 1 0 0 0 1-1v-9H5a2 2 0 0 1-2-2Z"/><circle cx="16.5" cy="13.5" r="0.8"/>',
  gift: '<path d="M4 11h16v10H4zM2 7h20v4H2zM12 7v14M12 7c-2 0-4.5-.8-4.5-2.7C7.5 2.4 11 2.6 12 7ZM12 7c2 0 4.5-.8 4.5-2.7C16.5 2.4 13 2.6 12 7Z"/>',
  news: '<path d="M4 9v6l4 1 9 5V3L8 8H4a1 1 0 0 0-1 1M18 9a3 3 0 0 1 0 6"/>',
  crown: '<path d="M4 18h16M5 16 4 7l4.5 3L12 5l3.5 5L20 7l-1 9z"/>',
  check: '<path d="M9 6h11M9 12h11M9 18h11M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2"/>',
  users: '<circle cx="9" cy="8" r="3.2"/><path d="M3.5 19c.6-3 2.8-4.5 5.5-4.5S13.9 16 14.5 19M15.5 5.6a3.2 3.2 0 0 1 0 5M17.5 14.7c1.7.6 2.7 2 3 4.3"/>',
  send: '<path d="m21 3-9 9M21 3l-6.5 18-3-8-8-3z"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  stats: '<path d="M5 20V10M12 20V4M19 20v-7"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14 0 18M12 3c-3 3.5-3 14 0 18"/>',
  coin: '<circle cx="12" cy="12" r="8"/><path d="M12 8v8M9.5 10c0-1 1-1.7 2.5-1.7s2.5.7 2.5 1.6c0 2.2-5 1.9-5 4.1 0 1 1 1.7 2.5 1.7s2.5-.7 2.5-1.6"/>',
  edit: '<path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
  card: '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18M7 15h3"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  shield: '<path d="M12 3 20 6v5c0 5-3.4 8.6-8 10-4.6-1.4-8-5-8-10V6Z"/>',
};
const ic = (n) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${P[n] || P.coin}</svg>`;
function mountIcons(root = document) {
  root.querySelectorAll("[data-ic]").forEach((el) => {
    const svg = ic(el.dataset.ic);
    if (el.tagName === "I") el.innerHTML = svg;
    else if (!el.querySelector("svg")) el.insertAdjacentHTML("afterbegin", svg);
  });
}

/* ───────── api ───────── */
const authHeaders = {};
if (tg?.initData) authHeaders["X-Init-Data"] = tg.initData;
else authHeaders["X-Dev-User"] = localStorage.devUser || "1";

async function api(path, body) {
  const res = await fetch("/api" + path, {
    method: body !== undefined ? "POST" : "GET",
    headers: { ...authHeaders, "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { code: data.error || res.status, message: data.message || data.detail || "Error" };
  return data;
}
const haptic = (s = "light") => { try { tg?.HapticFeedback?.impactOccurred(s); } catch {} };
const notifyHaptic = (t = "success") => { try { tg?.HapticFeedback?.notificationOccurred(t); } catch {} };

/* ───────── utils ───────── */
const fmt = (n) => Math.round(+n || 0).toLocaleString("en-US").replace(/,/g, " ");
const uzs = (n) => fmt(n) + " UZS";
const esc = (s) => (s || "").toString().replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
function hms(sec) {
  sec = Math.max(0, Math.floor(sec));
  const h = String(Math.floor(sec / 3600)).padStart(2, "0");
  const m = String(Math.floor((sec % 3600) / 60)).padStart(2, "0");
  const s = String(sec % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}
let toastTimer;
function toast(msg, cls = "") {
  const el = $("toast");
  el.textContent = msg;
  el.className = "toast " + cls;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.add("hidden"), 2600);
}
const photoUrl = () => tg?.initDataUnsafe?.user?.photo_url || "";

/* ───────── sheet ───────── */
function openSheet(title, html) {
  $("sheetTitle").textContent = title;
  $("sheetBody").innerHTML = html;
  $("sheet").classList.remove("hidden");
  $("sheetBack").classList.remove("hidden");
  mountIcons($("sheetBody"));
}
function closeSheet() { $("sheet").classList.add("hidden"); $("sheetBack").classList.add("hidden"); }
$("sheetBack").addEventListener("click", closeSheet);

/* ───────── state ───────── */
let S = null;

function renderUser() {
  const u = S.user;
  $("userName").textContent = u.name;
  $("userLevel").textContent = "Lv " + u.level;
  $("xpFill").style.width = Math.min(100, (u.xp / u.xp_next) * 100) + "%";
  const ph = photoUrl();
  $("avaMini").innerHTML = ph ? `<img src="${ph}" alt="">` : (u.name || "N")[0].toUpperCase();
  $("vipPill").textContent = u.vip_name;
  const daily = $("dailyCard");
  if (u.daily_available) {
    daily.classList.remove("hidden");
    $("dailyInfo").textContent = `Day ${u.daily_next_day} — +${fmt(u.daily_next_reward)} Coin`;
  } else daily.classList.add("hidden");
}
function renderBalance() {
  $("balCoins").textContent = fmt(S.user.coins);
  $("balUzs").textContent = "≈ " + uzs(S.user.value_uzs);
}

/* ───────── nav ───────── */
const loaders = { home: loadHome, market: loadMarket, earn: loadEarn, top: loadTop, wallet: loadWallet };
document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    haptic("light");
    document.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("active", b === btn));
    const name = btn.dataset.screen;
    document.querySelectorAll(".screen").forEach((s) => s.classList.toggle("active", s.id === "screen-" + name));
    loaders[name]?.();
  });
});

/* ═════════ HOME ═════════ */
async function loadHome() {
  try {
    const r = await api("/market");
    $("hPrice").textContent = uzs(r.price);
    const ch = $("hChange");
    ch.textContent = (r.change_pct >= 0 ? "+" : "") + r.change_pct + "%";
    ch.className = "chart-change " + (r.change_pct >= 0 ? "up" : "down");
    $("homeDeals").innerHTML = r.trades.length ? r.trades.map(dealRow).join("") : emptyRow("No deals yet — be the first to trade");
    loadChart();
    loadNews();
    loadEvents();
  } catch (e) { toast(e.message, "err"); }
}
function dealRow(t) {
  const d = new Date(t.t * 1000);
  const hh = String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
  return `<div class="item">
      <div class="item-mid"><div class="item-name">${fmt(t.amount)} Coin</div>
        <div class="item-sub">@ ${uzs(t.price)} · ${hh}</div></div>
      <div class="item-sub mono">${uzs(t.total)}</div></div>`;
}
const emptyRow = (t) => `<div class="item"><div class="item-mid" style="text-align:center;color:var(--txt-dim)">${t}</div></div>`;

async function loadNews() {
  try {
    const r = await api("/news");
    const strip = $("newsStrip"), head = $("newsHead");
    if (!r.items.length) { strip.classList.add("hidden"); head.classList.add("hidden"); return; }
    strip.classList.remove("hidden"); head.classList.remove("hidden");
    strip.innerHTML = r.items.map((n) => `
      <div class="news-card"><span class="news-tag ${n.tag === "NEW" ? "new" : "soon"}">${esc(n.tag)}</span>
        <span class="news-title">${esc(n.title)}</span><span class="news-text">${esc(n.text)}</span></div>`).join("");
  } catch {}
}
async function loadEvents() {
  try {
    const r = await api("/events");
    const head = $("eventsHead"), strip = $("eventStrip");
    if (!r.items.length) { head.classList.add("hidden"); strip.innerHTML = ""; return; }
    head.classList.remove("hidden");
    strip.innerHTML = r.items.map((ev) => {
      const left = ev.left === null ? "" : ` · ${ev.left} left`;
      return `<div class="card glass event-card" data-ev="${ev.id}"><div class="event-mid">
          <div class="item-name">${esc(ev.title)}</div><div class="item-sub">${esc(ev.text || "")}</div>
          <div class="event-meta"><span data-timer="${ev.id}" data-ends="${Math.floor(Date.now()/1000)+ev.ends_in}"></span>${left}</div></div>
        <button class="item-btn ${ev.claimed ? "done" : "gold"}" ${ev.claimed ? "disabled" : ""}>${ev.claimed ? "Got it" : "+" + fmt(ev.reward)}</button></div>`;
    }).join("");
    strip.querySelectorAll("[data-ev]").forEach((card) => {
      const btn = card.querySelector("button");
      if (btn.disabled) return;
      btn.addEventListener("click", async () => {
        try {
          const res = await api("/events/claim", { id: +card.dataset.ev });
          if (S) { S.user.coins = res.coins; renderBalance(); }
          toast(`Event: +${fmt(res.reward)} Coin`, "ok"); notifyHaptic("success"); loadEvents();
        } catch (e) { toast(e.message, "err"); }
      });
    });
  } catch {}
}
setInterval(() => {
  document.querySelectorAll("[data-timer]").forEach((el) => {
    const left = +el.dataset.ends - Math.floor(Date.now() / 1000);
    el.textContent = left > 0 ? hms(left) : "ended";
  });
}, 1000);

/* ═════════ CHART (MELL / UZS) ═════════ */
let exTf = "1h", exCtype = "candle", exSec = 3600, exCandles = null;
const TF_CANDLE = ["15m", "30m", "1h"], TF_LINE = ["1h", "1d", "1w", "1mo"];
const TF_LABEL = { "15m": "15m", "30m": "30m", "1h": "1H", "1d": "1D", "1w": "1W", "1mo": "1M" };
const SLOT = 14;
let vOffset = 0, vShift = 0;

function renderTfChips() {
  const set = exCtype === "candle" ? TF_CANDLE : TF_LINE;
  if (!set.includes(exTf)) exTf = "1h";
  $("tfChips").innerHTML = set.map((t) => `<button class="chip ${t === exTf ? "active" : ""}" data-tf="${t}">${TF_LABEL[t]}</button>`).join("");
}
$("tfChips").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip"); if (!chip) return;
  exTf = chip.dataset.tf; vOffset = 0; vShift = 0; renderTfChips(); loadChart();
});
$("ctypeChips").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip"); if (!chip) return;
  exCtype = chip.dataset.ctype;
  document.querySelectorAll("#ctypeChips .chip").forEach((c) => c.classList.toggle("active", c === chip));
  vOffset = 0; vShift = 0; renderTfChips(); loadChart();
});
renderTfChips();

async function loadChart() {
  try {
    const r = await api("/market/chart?tf=" + exTf);
    exCandles = r.candles; exSec = r.sec || 3600; drawChart(exCandles);
  } catch {}
}
(() => {
  const cv = $("exChart"); let drag = null;
  cv.addEventListener("pointerdown", (e) => { drag = { x: e.clientX, y: e.clientY }; cv.setPointerCapture(e.pointerId); });
  cv.addEventListener("pointermove", (e) => {
    if (!drag || !exCandles) return;
    vOffset += (e.clientX - drag.x) / SLOT; vShift += e.clientY - drag.y;
    drag = { x: e.clientX, y: e.clientY }; drawChart(exCandles);
  });
  ["pointerup", "pointercancel"].forEach((ev) => cv.addEventListener(ev, () => (drag = null)));
})();
setInterval(() => {
  if (exCandles && $("screen-home").classList.contains("active")) drawChart(exCandles);
}, 1000);

const axp = (v) => Math.round(+v).toLocaleString("en-US").replace(/,/g, " ");
function axt(ep) {
  const d = new Date(ep * 1000), p = (x) => String(x).padStart(2, "0");
  if (exSec < 86400) return p(d.getHours()) + ":" + p(d.getMinutes());
  if (exSec < 604800 * 4) return p(d.getDate()) + "." + p(d.getMonth() + 1);
  return d.getFullYear() + "." + p(d.getMonth() + 1);
}
function candleCloseLeft() {
  if (!exCandles || !exCandles.length) return 0;
  return Math.max(0, exCandles[exCandles.length - 1].t + exSec - Math.floor(Date.now() / 1000));
}
function drawChart(candles) {
  const cv = $("exChart"), dpr = window.devicePixelRatio || 1;
  const w = cv.clientWidth || 320, h = 220;
  cv.width = w * dpr; cv.height = h * dpr;
  const ctx = cv.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  ctx.font = "10px -apple-system, BlinkMacSystemFont, sans-serif";
  if (!candles || !candles.length) return;
  const n = candles.length;
  const AX_R = 62, AX_B = 18, PT = 6, PL = 6;
  const plotW = w - PL - AX_R, plotH = h - PT - AX_B, FUT = 3;
  const visSlots = Math.max(1, Math.floor(plotW / SLOT));
  const minRight = Math.min(n - 1, visSlots - 1);
  let rightIdx = Math.round(n - 1 + vOffset);
  rightIdx = Math.max(minRight, Math.min(n - 1 + FUT, rightIdx));
  vOffset = rightIdx - (n - 1);
  const xOf = (i) => PL + plotW - SLOT / 2 - (rightIdx - i) * SLOT;
  const firstVis = Math.max(0, rightIdx - visSlots - 1), lastVis = Math.min(n - 1, rightIdx);
  const vis = candles.slice(firstVis, lastVis + 1);
  let max = Math.max(...vis.map((c) => c.h)), min = Math.min(...vis.map((c) => c.l));
  if (!isFinite(max) || min === max) { const m = max || 1; min = m * 0.999; max = m * 1.001; }
  const pad = (max - min) * 0.12 || max * 0.02; max += pad; min -= pad;
  let range = max - min;
  const shiftV = (vShift / plotH) * range; min -= shiftV; max -= shiftV; range = max - min;
  const py = (v) => PT + (1 - (v - min) / range) * plotH;
  const up = "#3ddc84", down = "#ff5d73", grid = "rgba(255,255,255,0.05)", axtxt = "rgba(245,242,234,0.42)";

  ctx.textAlign = "left"; ctx.textBaseline = "middle";
  for (let g = 0; g <= 4; g++) {
    const v = max - (g / 4) * range, yy = py(v);
    ctx.strokeStyle = grid; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(PL, yy); ctx.lineTo(PL + plotW, yy); ctx.stroke();
    ctx.fillStyle = axtxt; ctx.fillText(axp(v), PL + plotW + 6, yy);
  }
  ctx.textAlign = "center"; ctx.textBaseline = "top";
  const tstep = Math.max(1, Math.ceil(visSlots / 5));
  for (let i = firstVis; i <= lastVis; i++) {
    if ((rightIdx - i) % tstep !== 0) continue;
    const cx = xOf(i); if (cx < PL || cx > PL + plotW) continue;
    ctx.strokeStyle = grid; ctx.beginPath(); ctx.moveTo(cx, PT); ctx.lineTo(cx, PT + plotH); ctx.stroke();
    ctx.fillStyle = axtxt; ctx.fillText(axt(candles[i].t), cx, PT + plotH + 4);
  }
  if (exCtype === "line") {
    const grad = ctx.createLinearGradient(0, PT, 0, PT + plotH);
    grad.addColorStop(0, "rgba(232,193,90,0.22)"); grad.addColorStop(1, "rgba(232,193,90,0)");
    ctx.beginPath(); let started = false, lastX = PL;
    for (let i = firstVis; i <= lastVis; i++) {
      const cx = xOf(i);
      if (!started) { ctx.moveTo(cx, py(candles[i].c)); started = true; } else ctx.lineTo(cx, py(candles[i].c));
      lastX = cx;
    }
    ctx.strokeStyle = "#e8c15a"; ctx.lineWidth = 2; ctx.lineJoin = "round"; ctx.stroke();
    ctx.lineTo(lastX, PT + plotH); ctx.lineTo(PL, PT + plotH); ctx.closePath();
    ctx.fillStyle = grad; ctx.fill();
  } else {
    const bw = Math.max(2, Math.min(SLOT - 3, SLOT * 0.66));
    for (let i = firstVis; i <= lastVis; i++) {
      const c = candles[i], cx = xOf(i);
      if (cx < PL - SLOT || cx > PL + plotW + SLOT) continue;
      const col = c.c >= c.o ? up : down;
      ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(cx, py(c.h)); ctx.lineTo(cx, py(c.l)); ctx.stroke();
      const yO = py(c.o), yC = py(c.c), bh = Math.max(1, Math.abs(yC - yO));
      ctx.fillRect(Math.round(cx - bw / 2), Math.round(Math.min(yO, yC)), Math.round(bw), Math.round(bh));
    }
  }
  const lastC = candles[n - 1], lastCol = lastC.c >= lastC.o ? up : down, ly = py(lastC.c);
  if (ly > PT && ly < PT + plotH) {
    ctx.setLineDash([3, 3]); ctx.strokeStyle = lastCol; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(PL, ly); ctx.lineTo(PL + plotW, ly); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = lastCol; ctx.fillRect(PL + plotW, ly - 8, AX_R, 16);
    ctx.fillStyle = "#0b0a08"; ctx.textAlign = "left"; ctx.textBaseline = "middle";
    ctx.font = "bold 10px -apple-system, sans-serif"; ctx.fillText(axp(lastC.c), PL + plotW + 5, ly);
  }
  const left = candleCloseLeft();
  if (left > 0 && rightIdx >= n - 1) {
    const cx = Math.min(PL + plotW, Math.max(PL, xOf(n - 1)));
    const mm = Math.floor(left / 60), ss = left % 60, hh = Math.floor(mm / 60);
    const txt = hh > 0 ? `${hh}:${String(mm % 60).padStart(2, "0")}:${String(ss).padStart(2, "0")}` : `${mm}:${String(ss).padStart(2, "0")}`;
    ctx.font = "bold 10px -apple-system, sans-serif";
    const tw = ctx.measureText(txt).width + 10;
    ctx.fillStyle = "rgba(232,193,90,0.9)"; ctx.fillRect(cx - tw / 2, PT + plotH + 2, tw, 14);
    ctx.fillStyle = "#0b0a08"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(txt, cx, PT + plotH + 9);
  }
}

/* ═════════ MARKET (P2P) ═════════ */
let market = null;
async function loadMarket() {
  try {
    const r = await api("/market");
    market = r;
    $("mPrice").textContent = uzs(r.price);
    $("mCoins").textContent = fmt(r.coins);
    const ch = $("mChange");
    ch.textContent = (r.change_pct >= 0 ? "+" : "") + r.change_pct + "%";
    ch.className = "chart-change " + (r.change_pct >= 0 ? "up" : "down");
    $("feeNote").textContent = `fee ${r.fee_pct}%`;
    $("frozenNote").classList.toggle("hidden", !r.frozen);

    $("adList").innerHTML = r.ads.length ? r.ads.map(adRow).join("") : emptyRow("No sell offers yet");
    $("adList").querySelectorAll("[data-ad]").forEach((el) =>
      el.addEventListener("click", () => buySheet(JSON.parse(el.dataset.ad))));

    const myAds = r.my_ads || [];
    $("myAdsHead").classList.toggle("hidden", !myAds.length);
    $("myAds").innerHTML = myAds.map((a) => `
      <div class="item"><div class="item-ic">${ic("card")}</div>
        <div class="item-mid"><div class="item-name">${fmt(a.amount)} / ${fmt(a.total)} Coin</div>
          <div class="item-sub">@ ${uzs(a.price)} · ${esc(a.method_name)}</div></div>
        <button class="item-btn danger" data-close="${a.id}">Close</button></div>`).join("");
    $("myAds").querySelectorAll("[data-close]").forEach((b) =>
      b.addEventListener("click", async () => {
        try { const x = await api("/p2p/ad/close", { id: +b.dataset.close }); S.user.coins = x.coins; renderBalance(); toast("Ad closed", "ok"); loadMarket(); }
        catch (e) { toast(e.message, "err"); }
      }));
    mountIcons($("screen-market"));
  } catch (e) { toast(e.message, "err"); }
}
function adRow(a) {
  return `<div class="item ${a.busy ? "busy" : ""}" ${a.mine || a.busy ? "" : `data-ad='${esc(JSON.stringify(a))}'`}>
      <div class="item-ic">${ic("card")}</div>
      <div class="item-mid"><div class="item-name">${uzs(a.price)} <span class="item-sub">/ coin</span></div>
        <div class="item-sub">${fmt(a.amount)} Coin · ${esc(a.method_name)} · ${esc(a.seller)}</div></div>
      ${a.mine ? '<span class="item-sub">you</span>' : a.busy ? '<span class="item-sub">busy</span>' : '<button class="item-btn gold">Buy</button>'}</div>`;
}
function buySheet(a) {
  openSheet(`Buy from ${esc(a.seller)}`, `
    <div class="hint">Price <b>${uzs(a.price)}</b> per Coin · up to <b>${fmt(a.amount)}</b> Coin · ${esc(a.method_name)}</div>
    <div class="field"><label>Amount (Coin)</label><input id="buyAmt" type="number" inputmode="numeric" value="${a.amount}"></div>
    <div class="trade-total"><span>You pay</span><b id="buyTotal">${uzs(a.amount * a.price)}</b></div>
    <button class="btn-primary gold" id="buyGo">Open deal</button>`);
  const rc = () => $("buyTotal").textContent = uzs((Math.min(+$("buyAmt").value || 0, a.amount)) * a.price);
  $("buyAmt").addEventListener("input", rc);
  $("buyGo").addEventListener("click", async () => {
    const amt = Math.min(+$("buyAmt").value || 0, a.amount);
    if (amt < 1) return toast("Enter amount", "err");
    try {
      const r = await api("/p2p/deal", { ad_id: a.id, amount: amt });
      closeSheet(); notifyHaptic("success"); openDeal(r.deal_id);
    } catch (e) { toast(e.message, "err"); }
  });
}

$("newAdBtn").addEventListener("click", () => {
  if (!market) return;
  const methods = market.pay_methods || {};
  const opts = Object.entries(methods).map(([k, v]) => `<option value="${k}">${esc(v)}</option>`).join("");
  openSheet("Sell Coin — new ad", `
    <div class="hint">Your coins go into escrow. A buyer pays you by ${esc(Object.values(methods)[0] || "card")}, you release the coins.</div>
    <div class="field"><label>Price per Coin (UZS)</label><input id="adPrice" type="number" inputmode="numeric" value="${market.price}"></div>
    <div class="field"><label>Amount (Coin)</label><input id="adAmt" type="number" inputmode="numeric" placeholder="min 10"></div>
    <div class="field"><label>Payment method</label><select id="adMethod">${opts}</select></div>
    <div class="field"><label>Your requisites (card №, name…)</label><input id="adDetails" type="text" placeholder="8600 •••• •••• ••••"></div>
    <div class="trade-total"><span>You receive (est.)</span><b id="adTotal">0 UZS</b></div>
    <button class="btn-primary" id="adGo">Post ad</button>`);
  const rc = () => $("adTotal").textContent = uzs((+$("adPrice").value || 0) * (+$("adAmt").value || 0));
  ["adPrice", "adAmt"].forEach((i) => $(i).addEventListener("input", rc));
  $("adGo").addEventListener("click", async () => {
    try {
      const r = await api("/p2p/ad", {
        price_uzs: +$("adPrice").value || 0, amount: +$("adAmt").value || 0,
        pay_method: $("adMethod").value, pay_details: $("adDetails").value,
      });
      S.user.coins = r.coins; renderBalance(); closeSheet();
      toast("Ad posted — coins in escrow", "ok"); notifyHaptic("success"); loadMarket();
    } catch (e) { toast(e.message, "err"); }
  });
});

$("myDealsBtn").addEventListener("click", async () => {
  try {
    const r = await api("/market");
    const list = r.my_deals || [];
    openSheet("My deals", list.length ? list.map((d) => `
      <div class="item deal-item" data-deal="${d.id}"><div class="item-ic">${ic(d.role === "buyer" ? "up" : "chart")}</div>
        <div class="item-mid"><div class="item-name">${d.role === "buyer" ? "Buy" : "Sell"} ${fmt(d.amount)} Coin</div>
          <div class="item-sub">${uzs(d.total)} · ${esc(d.counterparty)}</div></div>
        <span class="deal-status s-${d.status}">${statusLabel(d.status)}</span></div>`).join("")
      : `<div class="hint">No deals yet.</div>`);
    $("sheetBody").querySelectorAll("[data-deal]").forEach((el) =>
      el.addEventListener("click", () => { closeSheet(); openDeal(+el.dataset.deal); }));
  } catch (e) { toast(e.message, "err"); }
});

/* ═════════ DEAL + CHAT ═════════ */
let curDeal = null, lastMsgId = 0, dealTimer = null;
const statusLabel = (s) => ({
  pending_payment: "Awaiting payment", paid: "Paid — confirm", completed: "Done",
  cancelled: "Cancelled", disputed: "Dispute", resolved: "Resolved",
}[s] || s);
const ACTION_LABEL = {
  paid: "✓ I paid", release: "Received — release", reject: "Not received",
  cancel: "Cancel", dispute: "Open dispute",
};
const ACTION_EP = { paid: "paid", release: "release", reject: "reject", cancel: "cancel", dispute: "dispute" };

async function openDeal(id) {
  curDeal = id; lastMsgId = 0;
  $("chatScroll").innerHTML = "";
  $("dealView").classList.remove("hidden");
  await refreshDeal();
  await pollMessages();
  clearInterval(dealTimer);
  dealTimer = setInterval(async () => { await pollMessages(); await refreshDeal(true); }, 2500);
}
function closeDeal() {
  clearInterval(dealTimer); dealTimer = null; curDeal = null;
  $("dealView").classList.add("hidden");
  loadMarket();
}
$("dealBack").addEventListener("click", closeDeal);

async function refreshDeal(quiet) {
  if (!curDeal) return;
  try {
    const d = await api("/p2p/deal/" + curDeal);
    $("dealTitle").textContent = `${d.role === "seller" ? "Sell" : "Buy"} ${fmt(d.amount)} Coin`;
    const st = $("dealStatus"); st.textContent = statusLabel(d.status); st.className = "deal-status s-" + d.status;
    const deadline = d.status === "pending_payment" && d.deadline ? Math.max(0, d.deadline - Math.floor(Date.now() / 1000)) : 0;
    $("dealInfo").innerHTML = `
      <div class="di-row"><span>Price</span><b>${uzs(d.price)}</b></div>
      <div class="di-row"><span>Amount</span><b>${fmt(d.amount)} Coin</b></div>
      <div class="di-row"><span>Total</span><b>${uzs(d.total)}</b></div>
      <div class="di-row"><span>${d.role === "seller" ? "Fee (coins)" : "You receive"}</span><b>${d.role === "seller" ? fmt(d.fee) + " Coin" : fmt(d.payout) + " Coin"}</b></div>
      <div class="di-row"><span>Method</span><b>${esc(d.pay_method)}</b></div>
      ${d.pay_details ? `<div class="di-row req"><span>Requisites</span><b class="mono">${esc(d.pay_details)}</b></div>` : ""}
      <div class="di-row"><span>Counterparty</span><b>${esc(d.counterparty)}</b></div>
      ${deadline ? `<div class="di-row"><span>Pay within</span><b class="mono" data-dead="${d.deadline}">${hms(deadline)}</b></div>` : ""}`;
    const acts = $("dealActions");
    acts.innerHTML = (d.actions || []).map((a) => {
      const cls = (a === "release" || a === "paid") ? "btn-primary gold" : (a === "dispute" || a === "reject" || a === "cancel") ? "btn-secondary" : "btn-primary";
      return `<button class="${cls}" data-act="${a}">${ACTION_LABEL[a]}</button>`;
    }).join("");
    acts.querySelectorAll("[data-act]").forEach((b) => b.addEventListener("click", () => dealAction(b.dataset.act)));
  } catch (e) { if (!quiet) toast(e.message, "err"); }
}
async function dealAction(act) {
  const ep = ACTION_EP[act]; if (!ep) return;
  if (act === "dispute" && !confirm("Open a dispute? Both accounts get frozen until an admin resolves it.")) return;
  try {
    await api("/p2p/deal/" + ep, { id: curDeal });
    notifyHaptic(act === "release" ? "success" : "warning");
    await refreshDeal(); await pollMessages();
    if (act === "release") { S = await api("/state"); renderBalance(); }
  } catch (e) { toast(e.message, "err"); }
}
async function pollMessages() {
  if (!curDeal) return;
  try {
    const r = await api(`/p2p/deal/${curDeal}/messages?after=${lastMsgId}`);
    if (!r.items.length) return;
    const box = $("chatScroll");
    const atBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 60;
    r.items.forEach((m) => { box.insertAdjacentHTML("beforeend", msgHtml(m)); lastMsgId = Math.max(lastMsgId, m.id); });
    if (atBottom) box.scrollTop = box.scrollHeight;
  } catch {}
}
function msgHtml(m) {
  if (m.kind === "system") return `<div class="msg-sys">${esc(m.body)}</div>`;
  const inner = m.kind === "photo" && m.media
    ? `<a href="${m.media}" target="_blank"><img class="msg-photo" src="${m.media}" alt=""></a>`
    : esc(m.body);
  return `<div class="msg ${m.mine ? "mine" : ""} ${m.sender === 0 ? "admin" : ""}">
      ${m.mine ? "" : `<div class="msg-name">${esc(m.name)}</div>`}<div class="msg-bubble">${inner}</div></div>`;
}
$("chatSend").addEventListener("click", sendMsg);
$("chatText").addEventListener("keydown", (e) => { if (e.key === "Enter") sendMsg(); });
async function sendMsg() {
  const t = $("chatText").value.trim(); if (!t || !curDeal) return;
  $("chatText").value = "";
  try { await api("/p2p/deal/message", { deal_id: curDeal, body: t }); await pollMessages(); }
  catch (e) { toast(e.message, "err"); }
}
$("chatPhoto").addEventListener("click", () => $("photoInput").click());
$("photoInput").addEventListener("change", async () => {
  const f = $("photoInput").files[0]; if (!f || !curDeal) return;
  const fd = new FormData(); fd.append("file", f);
  try {
    const res = await fetch(`/api/p2p/deal/${curDeal}/photo`, { method: "POST", headers: { ...authHeaders }, body: fd });
    if (!res.ok) throw 0; await pollMessages();
  } catch { toast("Photo upload failed", "err"); }
  $("photoInput").value = "";
});
setInterval(() => {
  document.querySelectorAll("[data-dead]").forEach((el) => {
    const left = +el.dataset.dead - Math.floor(Date.now() / 1000);
    el.textContent = left > 0 ? hms(left) : "expired";
  });
}, 1000);

/* ═════════ EARN ═════════ */
document.querySelectorAll("[data-open]").forEach((b) =>
  b.addEventListener("click", () => {
    haptic("light"); $("earnRoot").classList.add("hidden");
    const map = { tasks: "subTasks", friends: "subFriends" };
    $(map[b.dataset.open]).classList.remove("hidden");
    if (b.dataset.open === "tasks") loadTasks();
    if (b.dataset.open === "friends") loadFriends();
  }));
document.querySelectorAll("[data-back]").forEach((b) =>
  b.addEventListener("click", () => {
    document.querySelectorAll(".subview").forEach((s) => s.classList.add("hidden"));
    $("earnRoot").classList.remove("hidden"); loadEarn();
  }));

async function loadEarn() {
  try {
    if (S) $("capTxt").textContent = `${fmt(S.user.earned_today)} / ${fmt(S.user.earn_cap)}`;
    const [t, f] = await Promise.all([api("/tasks"), api("/friends")]);
    const open = t.items.filter((x) => !x.claimed).slice(0, 4);
    $("earnTaskPreview").innerHTML = "";
    open.forEach((task) => $("earnTaskPreview").appendChild(taskRow(task, true)));
    if (!open.length) $("earnTaskPreview").innerHTML = emptyRow("All tasks done");
    $("earnFriendPreview").innerHTML = `<div class="item"><div class="item-ic">${ic("users")}</div>
      <div class="item-mid"><div class="item-name">${f.count} friends</div>
        <div class="item-sub">+${fmt(f.bonus_inviter)} per invite</div></div></div>`;
    window._friends = f; mountIcons($("screen-earn"));
  } catch (e) { toast(e.message, "err"); }
}
const CAT = { daily: "Daily", weekly: "Weekly", special: "Special" };
async function loadTasks() {
  try {
    const r = await api("/tasks"); const list = $("taskList"); list.innerHTML = "";
    for (const cat of ["daily", "weekly", "special"]) {
      const items = r.items.filter((t) => t.cat === cat); if (!items.length) continue;
      const head = document.createElement("div"); head.className = "cat-head"; head.textContent = CAT[cat]; list.appendChild(head);
      const wrap = document.createElement("div"); wrap.className = "list";
      items.forEach((t) => wrap.appendChild(taskRow(t))); list.appendChild(wrap);
    }
  } catch (e) { toast(e.message, "err"); }
}
function taskRow(t, compact = false) {
  const el = document.createElement("div"); el.className = "item";
  const done = t.progress >= t.goal, pct = Math.min(100, (t.progress / t.goal) * 100);
  const linkLike = !!t.url && ["link", "channel", "social"].includes(t.kind);
  el.innerHTML = `<div class="item-ic">${ic("check")}</div>
    <div class="item-mid"><div class="item-name">${esc(t.name)}</div>
      <div class="item-sub">+${fmt(t.reward)} Coin${linkLike ? "" : ` · ${fmt(t.progress)}/${fmt(t.goal)}`}</div>
      ${linkLike || compact ? "" : `<div class="mini-bar"><span class="mini-fill" style="width:${pct}%"></span></div>`}</div>`;
  const btn = document.createElement("button");
  if (t.claimed) { btn.className = "item-btn done"; btn.textContent = "Done"; btn.disabled = true; }
  else if (linkLike) {
    btn.className = "item-btn ghost"; btn.textContent = "Open";
    btn.addEventListener("click", () => {
      tg?.openLink ? tg.openLink(t.url) : window.open(t.url);
      btn.textContent = "Claim"; btn.className = "item-btn"; btn.onclick = () => claimTask(t.id, compact);
    });
  } else { btn.className = "item-btn"; btn.textContent = "Claim"; btn.disabled = !done; btn.addEventListener("click", () => claimTask(t.id, compact)); }
  el.appendChild(btn); return el;
}
async function claimTask(id, compact) {
  try {
    const r = await api("/tasks/claim", { id });
    S = await api("/state");
    toast(`+${fmt(r.reward)} Coin`, "ok"); notifyHaptic("success");
    renderUser(); renderBalance(); compact ? loadEarn() : loadTasks();
  } catch (e) { toast(e.message, "err"); }
}
let refLink = "";
async function loadFriends() {
  try {
    const r = window._friends || (await api("/friends")); window._friends = null;
    refLink = r.link; $("refLink").textContent = r.link; $("friendCount").textContent = r.count;
    $("refBonusTxt").innerHTML = `Invite friends — you get <b>+${fmt(r.bonus_inviter)}</b>, they get <b>+${fmt(r.bonus_friend)}</b>.`;
    const list = $("friendList"); list.innerHTML = "";
    if (!r.friends.length) { list.innerHTML = emptyRow("No friends yet — share your link"); return; }
    r.friends.forEach((f) => {
      const el = document.createElement("div"); el.className = "item";
      el.innerHTML = `<div class="ava">${(f.name || "?")[0].toUpperCase()}</div>
        <div class="item-mid"><div class="item-name">${esc(f.name)}</div><div class="item-sub">Lv ${f.level}</div></div>
        <div class="item-sub mono">${fmt(f.earned)}</div>`;
      list.appendChild(el);
    });
  } catch (e) { toast(e.message, "err"); }
}
$("copyRefBtn").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(refLink); toast("Link copied", "ok"); } catch { toast(refLink); }
});
$("shareRefBtn").addEventListener("click", () => {
  const url = `https://t.me/share/url?url=${encodeURIComponent(refLink)}&text=${encodeURIComponent("Join me on nCoin P2P")}`;
  tg?.openTelegramLink ? tg.openTelegramLink(url) : window.open(url);
});

/* ═════════ TOP ═════════ */
async function loadTop() {
  try {
    const r = await api("/leaderboard?by=coins");
    if (r.me) {
      const mr = $("myRank"); mr.classList.remove("hidden");
      mr.innerHTML = `<span>Your rank</span><b>#${r.me.rank}</b><span class="mono">${fmt(r.me.value)}</span>`;
    }
    $("lbList").innerHTML = r.top.filter((u) => u.id !== 0).map((u) => `
      <div class="item"><div class="rank-n ${u.rank <= 3 ? "top" + u.rank : ""}">${u.rank}</div>
        <div class="item-mid"><div class="item-name">${esc(u.name)}${u.id === S?.user.id ? " · you" : ""}</div>
          <div class="item-sub">Lv ${u.level}</div></div>
        <div class="item-sub mono">${fmt(u.value)}</div></div>`).join("");
  } catch (e) { toast(e.message, "err"); }
}

/* ═════════ WALLET ═════════ */
async function loadWallet() {
  try {
    const u = S.user;
    const ph = photoUrl();
    $("avaBig").innerHTML = ph ? `<img src="${ph}" alt="">` : (u.name || "N")[0].toUpperCase();
    $("profName").textContent = u.name;
    $("profSub").textContent = "@" + (u.username || "player") + " · Lv " + u.level;
    $("wCoins").textContent = fmt(u.coins);
    $("wUzs").textContent = fmt(u.value_uzs);
    $("stRef").textContent = fmt(u.ref_count);
    $("stTasks").textContent = fmt(u.coins);
    const md = await api("/market");
    const mine = (md.my_deals || []);
    $("stDeals").textContent = fmt(mine.filter((d) => d.status === "completed" || d.status === "resolved").length);
    $("stVolume").textContent = fmt(mine.reduce((s, d) => s + (d.status === "completed" ? d.amount : 0), 0));
    $("supportNote").textContent = "Need help? Open a dispute inside the deal chat — an admin will step in.";
    $("staffCard").classList.toggle("hidden", !u.is_staff);
    if (u.is_staff) loadDisputeBadge();
    mountIcons($("screen-wallet"));
  } catch (e) { toast(e.message, "err"); }
}
async function loadDisputeBadge() {
  try { const r = await api("/p2p/disputes"); $("disputeBadge").textContent = r.items.length; } catch {}
}
$("staffCard").addEventListener("click", async () => {
  try {
    const r = await api("/p2p/disputes");
    openSheet("Open disputes", r.items.length ? r.items.map((d) => `
      <div class="dispute-card glass-thin"><div class="item-mid">
        <div class="item-name">Deal #${d.id} · ${fmt(d.amount)} Coin (${uzs(d.total)})</div>
        <div class="item-sub">Buyer ${esc(d.buyer)} ↔ Seller ${esc(d.seller)}</div></div>
        <div class="row-btns" style="margin-top:8px">
          <button class="btn-secondary" data-open-deal="${d.id}">Open chat</button>
          <button class="btn-primary gold" data-res="release" data-id="${d.id}">→ Buyer</button>
          <button class="btn-primary" data-res="refund" data-id="${d.id}">→ Seller</button></div></div>`).join("")
      : `<div class="hint">No open disputes 🎉</div>`);
    $("sheetBody").querySelectorAll("[data-open-deal]").forEach((b) =>
      b.addEventListener("click", () => { closeSheet(); openDeal(+b.dataset.openDeal); }));
    $("sheetBody").querySelectorAll("[data-res]").forEach((b) =>
      b.addEventListener("click", async () => {
        if (!confirm(`Resolve deal #${b.dataset.id}: coins ${b.dataset.res === "release" ? "to buyer" : "to seller"}?`)) return;
        try {
          await api("/p2p/resolve", { deal_id: +b.dataset.id, action: b.dataset.res });
          toast("Dispute resolved", "ok"); closeSheet(); loadDisputeBadge();
        } catch (e) { toast(e.message, "err"); }
      }));
  } catch (e) { toast(e.message, "err"); }
});

$("dailyBtn").addEventListener("click", async () => {
  try {
    const r = await api("/daily/claim", {});
    S = await api("/state");
    toast(`Day ${r.day}: +${fmt(r.reward)} Coin`, "ok"); notifyHaptic("success");
    renderUser(); renderBalance();
  } catch (e) { toast(e.message, "err"); }
});
$("qEdit").addEventListener("click", () => {
  openSheet("Edit profile", `
    <div class="field"><label>Display name</label><input id="pnName" type="text" maxlength="32" value="${esc(S.user.name)}"></div>
    <button class="btn-primary" id="pnSave">Save</button>`);
  $("pnSave").addEventListener("click", async () => {
    try {
      const r = await api("/profile/update", { name: $("pnName").value });
      S.user.name = r.name; renderUser(); closeSheet(); loadWallet(); toast("Saved", "ok");
    } catch (e) { toast(e.message, "err"); }
  });
});

/* ═════════ init ═════════ */
async function boot() {
  try { tg?.ready(); tg?.expand(); } catch {}
  try {
    S = await api("/auth", {});
    renderUser(); renderBalance();
    loadHome();
    mountIcons();
  } catch (e) {
    toast("Auth failed: " + (e.message || e.code), "err");
  }
}
boot();
