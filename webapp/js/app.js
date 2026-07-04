/* nCoin v0.2 — vanilla, no build step. Black & gold, no emoji: inline SVG icons. */

const tg = window.Telegram?.WebApp;
const $ = (id) => document.getElementById(id);

/* ───────── icons ───────── */
const P = {
  home: '<path d="M3 10.5 12 3l9 7.5M5 9.5V21h5v-6h4v6h5V9.5"/>',
  chart: '<path d="M4 19h16M6 16l4-5 3 3 5-7"/>',
  up: '<path d="M12 20V7M12 4l6 6M12 4 6 10"/>',
  trophy: '<path d="M8 21h8M12 17v4M7 4h10v4a5 5 0 0 1-10 0zM7 5H4v2a3 3 0 0 0 3 3M17 5h3v2a3 3 0 0 1-3 3"/>',
  wallet: '<path d="M3 7a2 2 0 0 1 2-2h13v3M3 7v10a2 2 0 0 0 2 2h14a1 1 0 0 0 1-1v-9H5a2 2 0 0 1-2-2Z"/><circle cx="16.5" cy="13.5" r="0.8"/>',
  bolt: '<path d="M13 2 5 13h5l-1 9 8-11h-5z"/>',
  flame: '<path d="M12 22c4 0 6.5-2.6 6.5-6.2 0-3-2-5-3.7-7C13.6 7.4 13 5.5 13 3c-3 2-4.3 4.6-4.6 6.8-.2-.6-.6-1.5-1.4-2.3C5.6 9.3 5 11.6 5 13.8 5 18.4 8 22 12 22Z"/>',
  pickaxe: '<path d="m14 7 3 3M5 21l7.5-7.5M14 4c3 .5 5.5 3 6 6M14 4c-2.5 0-5 .8-6.8 2.2M14 4l-1.5 1.5M20 10c0 2.5-.8 5-2.2 6.8M20 10l-1.5 1.5"/>',
  gift: '<path d="M4 11h16v10H4zM2 7h20v4H2zM12 7v14M12 7c-2 0-4.5-.8-4.5-2.7C7.5 2.4 11 2.6 12 7ZM12 7c2 0 4.5-.8 4.5-2.7C16.5 2.4 13 2.6 12 7Z"/>',
  news: '<path d="M4 9v6l4 1 9 5V3L8 8H4a1 1 0 0 0-1 1M18 9a3 3 0 0 1 0 6"/>',
  crown: '<path d="M4 18h16M5 16 4 7l4.5 3L12 5l3.5 5L20 7l-1 9z"/>',
  check: '<path d="M9 6h11M9 12h11M9 18h11M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2"/>',
  users: '<circle cx="9" cy="8" r="3.2"/><path d="M3.5 19c.6-3 2.8-4.5 5.5-4.5S13.9 16 14.5 19M15.5 5.6a3.2 3.2 0 0 1 0 5M17.5 14.7c1.7.6 2.7 2 3 4.3"/>',
  send: '<path d="m21 3-9 9M21 3l-6.5 18-3-8-8-3z"/>',
  down: '<path d="M12 4v13M12 20l-6-6M12 20l6-6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  stats: '<path d="M5 20V10M12 20V4M19 20v-7"/>',
  star: '<path d="m12 3 2.7 5.7 6.3.7-4.7 4.2 1.3 6.2L12 16.7 6.4 19.8l1.3-6.2L3 9.4l6.3-.7z"/>',
  layers: '<path d="m12 3 9 5-9 5-9-5zM3 13.5l9 5 9-5"/>',
  battery: '<path d="M3 8h14v8H3zM17 10h2a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1h-2M6 10.5v3M9 10.5v3"/>',
  chip: '<path d="M7 7h10v10H7zM10 10h4v4h-4zM12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>',
  snow: '<path d="M12 2v20M4 6l16 12M20 6 4 18M9 4l3 2 3-2M9 20l3-2 3 2"/>',
  factory: '<path d="M3 21V9l6 4V9l6 4V5h6v16zM7 17h2M12 17h2M17 17h2"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14 0 18M12 3c-3 3.5-3 14 0 18"/>',
  spark: '<path d="M12 2v5M12 17v5M2 12h5M17 12h5M5 5l3 3M16 16l3 3M19 5l-3 3M8 16l-3 3"/>',
  phone: '<path d="M8 2h8a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1ZM10 18h4"/>',
  coin: '<circle cx="12" cy="12" r="8"/><path d="M12 8v8M9.5 10c0-1 1-1.7 2.5-1.7s2.5.7 2.5 1.6c0 2.2-5 1.9-5 4.1 0 1 1 1.7 2.5 1.7s2.5-.7 2.5-1.6"/>',
  edit: '<path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
  chat: '<path d="M4 5h16v11H8l-4 4z"/><path d="M8 9h8M8 12h5"/>',
  card: '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18M7 15h3"/>',
  crypto: '<circle cx="12" cy="12" r="9"/><path d="M9 8h4a2 2 0 0 1 0 4H9zM9 12h4.5a2 2 0 0 1 0 4H9zM9 6v12M11 6v1M11 17v1"/>',
};
const ic = (name) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${P[name] || P.coin}</svg>`;

function mountIcons(root = document) {
  root.querySelectorAll("[data-ic]").forEach((el) => {
    const svg = ic(el.dataset.ic);
    if (el.tagName === "I") el.innerHTML = svg;
    else if (!el.querySelector("svg")) el.insertAdjacentHTML("afterbegin", svg);
  });
}

const UP_ICONS = {
  tap_power: "bolt", crit: "star", double_tap: "layers", energy_max: "battery",
  cpu: "chip", battery: "battery", cooling: "snow", farm: "factory",
  core_boost: "globe", xp_boost: "spark", ref_boost: "users",
};
const TASK_ICONS = { open: "phone", taps: "bolt", collect: "pickaxe", earn: "coin", invite: "users", link: "news" };

const LEAGUES = [
  { key: "bronze", name: "Bronze", color: "#c98a4b" },
  { key: "silver", name: "Silver", color: "#cfd6e4" },
  { key: "gold", name: "Gold", color: "#f2c94c" },
  { key: "platinum", name: "Platinum", color: "#8ee8dc" },
  { key: "diamond", name: "Diamond", color: "#8ab6ff" },
  { key: "legend", name: "Legend", color: "#ff8ad4" },
];
const leagueColor = (key) => (LEAGUES.find((l) => l.key === key) || LEAGUES[0]).color;
const shield = (key, size = 52) =>
  `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="${leagueColor(key)}" stroke-width="1.6" stroke-linejoin="round">
     <path d="M12 2 20 5v6c0 5-3.4 9.2-8 11-4.6-1.8-8-6-8-11V5Z"/>
     <path fill="${leagueColor(key)}" stroke="none" d="m12 7 1.6 3.2 3.4.4-2.5 2.3.7 3.4L12 14.6l-3.2 1.7.7-3.4L7 10.6l3.4-.4z"/>
   </svg>`;

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
const fmt = (n) => Math.floor(n).toLocaleString("en-US").replace(/,/g, " ");
// цена Coin в USD: до 6 знаков, без хвостовых нулей
const fmtPx = (p) => (+p).toFixed(6).replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
const fmtPrice = (p) => fmtPx(p) + " USD";
// баланс USD: 2 знака если ≥1, иначе 4, без хвостовых нулей
const fmtUsd = (u) => (+u).toFixed(u >= 1 ? 2 : 4).replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
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
  toastTimer = setTimeout(() => el.classList.add("hidden"), 2400);
}
const photoUrl = () => tg?.initDataUnsafe?.user?.photo_url || "";

/* ───────── state ───────── */
let S = null;
let syncMs = 0;
let pendingTaps = 0;
let unsyncedTaps = 0;
let optimisticGain = 0;
let flushing = false;

const nowSec = () => Date.now() / 1000;
const sinceSync = () => (performance.now() - syncMs) / 1000;

function applySnapshot(state) {
  S = state;
  syncMs = performance.now();
  unsyncedTaps = 0;
  optimisticGain = 0;
}
const localEnergy = () => Math.max(0, Math.min(S.clicker.energy_max, S.clicker.energy + sinceSync() * S.clicker.regen - unsyncedTaps));
const localHeat = () => Math.max(0, Math.min(S.clicker.heat_max, S.clicker.heat - sinceSync() * S.clicker.heat_decay + unsyncedTaps * S.clicker.heat_per_tap));
function localMined() {
  const m = S.mining;
  const el = Math.max(0, nowSec() - m.started_at) / 3600;
  return Math.min(el, m.window_hours) * m.rate;
}
const overheatLeft = () => Math.max(0, (S.clicker.overheat_until || 0) - nowSec());

/* ───────── nav ───────── */
const loaders = { market: loadMarket, earn: loadEarn, top: loadTop, wallet: loadWallet };
document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    haptic("light");
    document.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("active", b === btn));
    const name = btn.dataset.screen;
    document.querySelectorAll(".screen").forEach((s) => s.classList.toggle("active", s.id === "screen-" + name));
    loaders[name]?.();
  });
});

/* ───────── home ───────── */
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
  $("balCoins").textContent = fmt(S.user.coins + optimisticGain);
  $("balUsd").textContent = "≈ " + fmtUsd((S.user.coins + optimisticGain) * S.economy.usd_rate) + " USD";
}

function tickHome() {
  if (!S) return;
  const c = S.clicker;
  const e = localEnergy();
  const h = localHeat();
  $("energyTxt").textContent = `${Math.floor(e)}/${c.energy_max}`;
  $("energyFill").style.width = (e / c.energy_max) * 100 + "%";
  $("heatTxt").textContent = Math.round((h / c.heat_max) * 100) + "%";
  $("heatFill").style.width = (h / c.heat_max) * 100 + "%";

  const oh = overheatLeft();
  if (oh > 0) {
    $("overheatOverlay").classList.remove("hidden");
    $("overheatTimer").textContent = Math.ceil(oh);
  } else $("overheatOverlay").classList.add("hidden");

  const m = S.mining;
  const mined = localMined();
  const readyIn = Math.max(0, m.started_at + m.window_hours * 3600 - nowSec());
  $("miningRate").textContent = `+${fmt(m.rate)}/h`;
  $("miningAmount").textContent = `${fmt(mined)} / ${fmt(m.capacity)}`;
  $("miningTimer").textContent = readyIn > 0 ? hms(readyIn) : "FULL";
  $("miningFill").style.width = Math.min(100, (mined / m.capacity) * 100) + "%";
  $("collectBtn").textContent = mined >= 1 ? `Collect +${fmt(mined)}` : "Mining…";
  $("collectBtn").disabled = mined < 1;

  const combo = c.combo + unsyncedTaps;
  const badge = $("comboBadge");
  if (combo >= 10 && oh <= 0) {
    badge.classList.remove("hidden");
    badge.innerHTML = `Combo <b>${combo}</b>`;
  } else badge.classList.add("hidden");
}

/* ───────── tap: tilt + cracks ───────── */
function spawnPop(x, y, text, crit = false) {
  const wrap = $("particles");
  if (wrap.childElementCount > 46) wrap.firstChild?.remove();
  const el = document.createElement("span");
  el.className = "pop" + (crit ? " crit" : "");
  el.textContent = text;
  el.style.left = x + "px";
  el.style.top = y + "px";
  wrap.appendChild(el);
  setTimeout(() => el.remove(), 900);
}

function crackPath() {
  // ломаная «трещина» из центра наружу
  let d = "M0,0";
  const ang = Math.random() * Math.PI * 2;
  let x = 0, y = 0, r = 0;
  for (let i = 0; i < 3; i++) {
    r += 9 + Math.random() * 10;
    const a = ang + (Math.random() - 0.5) * 0.9;
    x = Math.cos(a) * r;
    y = Math.sin(a) * r;
    d += ` L${x.toFixed(1)},${y.toFixed(1)}`;
  }
  return d;
}
function spawnCrack(x, y) {
  const wrap = $("particles");
  const el = document.createElement("div");
  el.className = "crack";
  el.style.left = x + "px";
  el.style.top = y + "px";
  const paths = Array.from({ length: 5 }, () => `<path d="${crackPath()}"/>`).join("");
  el.innerHTML = `<svg viewBox="-37 -37 74 74">${paths}</svg>`;
  wrap.appendChild(el);
  const dent = document.createElement("div");
  dent.className = "dent";
  dent.style.left = x + "px";
  dent.style.top = y + "px";
  wrap.appendChild(dent);
  setTimeout(() => { el.remove(); dent.remove(); }, 600);
}

let tiltTimer;
$("core").addEventListener("pointerdown", (ev) => {
  if (!S) return;
  if (overheatLeft() > 0) { haptic("heavy"); return; }
  if (localEnergy() < 1) { toast("No energy — wait for regen", "err"); return; }

  pendingTaps++;
  unsyncedTaps++;
  optimisticGain += S.clicker.tap_power;
  haptic("light");

  const r = $("core").getBoundingClientRect();
  const nx = ((ev.clientX - r.left) / r.width - 0.5) * 2;
  const ny = ((ev.clientY - r.top) / r.height - 0.5) * 2;
  const tilt = $("plateTilt");
  tilt.style.transform = `rotateY(${(nx * 13).toFixed(1)}deg) rotateX(${(-ny * 13).toFixed(1)}deg) scale(0.965)`;
  clearTimeout(tiltTimer);
  tiltTimer = setTimeout(() => { tilt.style.transform = ""; }, 140);

  const wrapR = $("particles").getBoundingClientRect();
  const px = ev.clientX - wrapR.left;
  const py = ev.clientY - wrapR.top;
  spawnCrack(px, py);
  spawnPop(px - 10, py - 26, "+" + S.clicker.tap_power);
  renderBalance();
});

async function flushTaps() {
  if (flushing || !S || pendingTaps === 0) return;
  flushing = true;
  const count = pendingTaps;
  pendingTaps = 0;
  try {
    const r = await api("/tap", { count });
    const prevLevel = S.user.level;
    Object.assign(S.user, { coins: r.coins, level: r.level, xp: r.xp, xp_next: r.xp_next });
    Object.assign(S.clicker, { energy: r.energy, heat: r.heat, combo: r.combo, overheat_until: r.overheat_until });
    syncMs = performance.now();
    unsyncedTaps = 0;
    optimisticGain = 0;

    const coreR = $("core").getBoundingClientRect();
    const wrapR = $("particles").getBoundingClientRect();
    const cx = coreR.left - wrapR.left + coreR.width / 2;
    if (r.crits > 0) { spawnPop(cx - 30, 26, `CRIT x${r.crits}!`, true); notifyHaptic("success"); }
    if (r.combo_bonus > 0) spawnPop(cx - 50, 58, `Combo +${fmt(r.combo_bonus)}`, true);
    if (r.overheated) { toast("OVERHEAT! Cooling down…", "err"); notifyHaptic("error"); }
    if (r.level > prevLevel) levelUp(r.level);
    renderUser();
    renderBalance();
  } catch (e) {
    if (e.code === "overheat" || e.code === "no_energy") { unsyncedTaps = 0; optimisticGain = 0; }
    else toast(e.message, "err");
  } finally {
    flushing = false;
  }
}
setInterval(flushTaps, 650);

function levelUp(level) {
  const flash = document.createElement("div");
  flash.className = "lvl-flash";
  document.body.appendChild(flash);
  setTimeout(() => flash.remove(), 800);
  toast(`Level up! Lv ${level} — +1% income`, "ok");
  notifyHaptic("success");
}

/* ───────── collect / daily ───────── */
$("collectBtn").addEventListener("click", async () => {
  try {
    const r = await api("/collect", {});
    const prevLevel = S.user.level;
    Object.assign(S.user, { coins: r.coins, level: r.level, xp: r.xp, xp_next: r.xp_next });
    S.mining.started_at = nowSec();
    flyCoins();
    toast(`+${fmt(r.collected)} Coin collected`, "ok");
    notifyHaptic("success");
    if (r.level > prevLevel) levelUp(r.level);
    renderUser();
    renderBalance();
  } catch (e) { toast(e.message, "err"); }
});

function flyCoins() {
  const from = $("collectBtn").getBoundingClientRect();
  const to = $("balCoins").getBoundingClientRect();
  for (let i = 0; i < 9; i++) {
    const c = document.createElement("div");
    c.className = "fly-coin";
    c.innerHTML = `<img src="img/mell-coin.png" alt="">`;
    const x0 = from.left + Math.random() * from.width;
    const y0 = from.top;
    c.style.left = x0 + "px";
    c.style.top = y0 + "px";
    document.body.appendChild(c);
    requestAnimationFrame(() => {
      setTimeout(() => {
        c.style.transform = `translate(${to.left + to.width / 2 - x0}px, ${to.top - y0}px) scale(0.4)`;
        c.style.opacity = "0";
      }, i * 40);
    });
    setTimeout(() => c.remove(), 900 + i * 40);
  }
}

$("dailyBtn").addEventListener("click", async () => {
  try {
    const r = await api("/daily/claim", {});
    S.user.coins = r.coins;
    S.user.daily_available = false;
    toast(`Day ${r.day}: +${fmt(r.reward)} Coin`, "ok");
    notifyHaptic("success");
    renderUser();
    renderBalance();
  } catch (e) { toast(e.message, "err"); }
});

/* ───────── news + events ───────── */
async function loadNews() {
  try {
    const r = await api("/news");
    $("newsStrip").innerHTML = r.items
      .map(
        (n) => `
      <div class="news-card">
        <span class="news-tag ${n.tag === "NEW" ? "new" : "soon"}">${n.tag}</span>
        <span class="news-title">${n.title}</span>
        <span class="news-text">${n.text}</span>
      </div>`
      )
      .join("");
  } catch {}
}

async function loadEvents() {
  try {
    const r = await api("/events");
    const head = $("eventsHead");
    const strip = $("eventStrip");
    if (!r.items.length) {
      head.classList.add("hidden");
      strip.innerHTML = "";
      return;
    }
    head.classList.remove("hidden");
    strip.innerHTML = r.items
      .map((ev) => {
        const left = ev.left === null ? "" : ` · ${ev.left} left`;
        return `
      <div class="card glass event-card" data-ev="${ev.id}">
        <div class="event-mid">
          <div class="item-name">${ev.title}</div>
          <div class="item-sub">${ev.text || ""}</div>
          <div class="event-meta"><span data-timer="${ev.id}" data-ends="${Math.floor(Date.now()/1000)+ev.ends_in}"></span>${left}</div>
        </div>
        <button class="item-btn ${ev.claimed ? "done" : "gold"}" ${ev.claimed ? "disabled" : ""}>
          ${ev.claimed ? "Got it" : "+" + fmt(ev.reward)}
        </button>`;
      })
      .join("");
    strip.querySelectorAll("[data-ev]").forEach((card) => {
      const btn = card.querySelector("button");
      if (btn.disabled) return;
      btn.addEventListener("click", async () => {
        try {
          const res = await api("/events/claim", { id: +card.dataset.ev });
          if (S) S.user.coins = res.coins;
          toast(`Event: +${fmt(res.reward)} Coin`, "ok");
          notifyHaptic("success");
          renderBalance();
          loadEvents();
        } catch (e) { toast(e.message, "err"); }
      });
    });
  } catch {}
}
function tickEventTimers() {
  document.querySelectorAll("[data-timer]").forEach((el) => {
    const left = +el.dataset.ends - Math.floor(Date.now() / 1000);
    el.textContent = left > 0 ? hms(left) : "ended";
  });
}

/* ───────── exchange ───────── */
let exSide = "buy";
let exData = null;
let exTf = "day";
let exCtype = "candle";
let exOffset = 0;

$("exSeg").addEventListener("click", (e) => {
  const btn = e.target.closest(".seg-btn");
  if (!btn) return;
  exSide = btn.dataset.side;
  document.querySelectorAll("#exSeg .seg-btn").forEach((b) => b.classList.toggle("active", b === btn));
  const submit = $("exSubmit");
  submit.textContent = exSide === "buy" ? "Buy Coin" : "Sell Coin";
  submit.className = "btn-primary " + exSide;
  $("exBookTitle").textContent = exSide === "buy" ? "Buy orders" : "Sell orders";
  $("exTradesTitle").textContent = exSide === "buy" ? "Recent buys" : "Recent sells";
  recalcTrade();
  if (exData) { renderOrders(); renderTrades(); }
});
function recalcTrade() {
  const total = (+$("exPriceIn").value || 0) * (+$("exAmountIn").value || 0);
  $("exTotal").textContent = fmtUsd(total) + " USD";
  const feePct = exData ? exData.fee_pct : 0;
  const fee = exSide === "sell" ? (total * feePct) / 100 : 0;
  $("exFee").textContent = fmtUsd(fee) + " USD";
}
["exPriceIn", "exAmountIn"].forEach((id) => $(id).addEventListener("input", recalcTrade));

$("tfChips").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  exTf = chip.dataset.tf;
  document.querySelectorAll("#tfChips .chip").forEach((c) => c.classList.toggle("active", c === chip));
  loadChart();
});
$("ctypeChips").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  exCtype = chip.dataset.ctype;
  document.querySelectorAll("#ctypeChips .chip").forEach((c) => c.classList.toggle("active", c === chip));
  if (exCandles) drawChart(exCandles);
});

let exCandles = null;
async function loadChart() {
  try {
    const r = await api("/exchange/chart?tf=" + exTf);
    exCandles = r.candles;
    drawChart(exCandles);
  } catch {}
}

$("exSubmit").addEventListener("click", async () => {
  await placeOrder(exSide, +$("exPriceIn").value, +$("exAmountIn").value);
  $("exAmountIn").value = "";
});

async function placeOrder(side, price, amount) {
  try {
    const r = await api("/exchange/order", { side, price_usd: price, amount });
    notifyHaptic("success");
    toast(
      r.filled > 0
        ? `Filled ${fmt(r.filled)} Coin @ ${fmtPrice(r.avg_price)}`
        : "Order placed in the book",
      "ok"
    );
    if (S) S.user.coins = r.coins;
    loadMarket();
    loadChart();
  } catch (e) { toast(e.message, "err"); }
}

/* ── candlestick + line chart ── */
function drawChart(candles) {
  const cv = $("exChart");
  const dpr = window.devicePixelRatio || 1;
  const w = cv.clientWidth || 320;
  const h = 200;
  cv.width = w * dpr;
  cv.height = h * dpr;
  const ctx = cv.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);
  if (!candles || !candles.length) return;
  const cs = candles.length === 1 ? [candles[0], candles[0]] : candles;

  const highs = cs.map((c) => c.h), lows = cs.map((c) => c.l);
  let max = Math.max(...highs), min = Math.min(...lows);
  if (min === max) { min *= 0.995; max *= 1.005; }
  const pad = (max - min) * 0.12 || max * 0.02;
  max += pad; min -= pad;
  const PL = 4, PR = 4, PT = 8, PB = 8;
  const iw = w - PL - PR;
  const py = (v) => PT + (1 - (v - min) / (max - min)) * (h - PT - PB);
  const up = "#3ddc84", down = "#ff5d73";

  ctx.strokeStyle = "rgba(255,255,255,0.05)";
  ctx.lineWidth = 1;
  for (let g = 0; g <= 3; g++) {
    const yy = PT + (g / 3) * (h - PT - PB);
    ctx.beginPath(); ctx.moveTo(0, yy); ctx.lineTo(w, yy); ctx.stroke();
  }

  if (exCtype === "line") {
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, "rgba(232,193,90,0.28)");
    grad.addColorStop(1, "rgba(232,193,90,0)");
    const px = (i) => PL + (cs.length === 1 ? iw / 2 : (i / (cs.length - 1)) * iw);
    ctx.beginPath();
    cs.forEach((c, i) => (i ? ctx.lineTo(px(i), py(c.c)) : ctx.moveTo(px(0), py(c.c))));
    ctx.strokeStyle = "#e8c15a"; ctx.lineWidth = 2; ctx.lineJoin = "round"; ctx.stroke();
    ctx.lineTo(px(cs.length - 1), h); ctx.lineTo(px(0), h); ctx.closePath();
    ctx.fillStyle = grad; ctx.fill();
    return;
  }

  const n = cs.length;
  const slot = iw / n;
  const bw = Math.max(2, Math.min(14, slot * 0.6));
  cs.forEach((c, i) => {
    const cx = PL + slot * (i + 0.5);
    const col = c.c >= c.o ? up : down;
    ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(cx, py(c.h)); ctx.lineTo(cx, py(c.l)); ctx.stroke();
    const yO = py(c.o), yC = py(c.c);
    const top = Math.min(yO, yC), bh = Math.max(1, Math.abs(yC - yO));
    ctx.fillRect(cx - bw / 2, top, bw, bh);
  });
}

/* ── order book (clickable) + trades filtered by side ── */
function renderOrders() {
  const page = exSide === "buy" ? exData.orders_buy : exData.orders_sell;
  const list = $("exOrders");
  if (!page.items.length) {
    list.innerHTML = `<div class="item"><div class="item-mid" style="text-align:center;color:var(--txt-dim)">No ${exSide} orders yet</div></div>`;
    $("exLoadMore").classList.add("hidden");
    return;
  }
  list.innerHTML = page.items.map(orderRowHtml).join("");
  bindOrderRows(list);
  exOffset = page.items.length;
  $("exLoadMore").classList.toggle("hidden", !page.has_more);
}
function orderRowHtml(o) {
  const col = o.side === "buy" ? "var(--green)" : "var(--red)";
  return `
    <div class="item" data-oid="${o.id}" data-o='${JSON.stringify(o).replace(/'/g, "&#39;")}'>
      <div class="item-mid">
        <div class="item-name" style="color:${col}">${fmtPrice(o.price)}</div>
        <div class="item-sub">${fmt(o.amount)} Coin · ${o.name}</div>
      </div>
      <button class="item-btn ${o.side === "buy" ? "" : "gold"}">${o.side === "buy" ? "Sell" : "Buy"}</button>
    </div>`;
}
function bindOrderRows(list) {
  list.querySelectorAll("[data-oid]").forEach((el) => {
    if (el.dataset.bound) return;
    el.dataset.bound = "1";
    el.addEventListener("click", () => takeOrderSheet(JSON.parse(el.dataset.o)));
  });
}
$("exLoadMore").addEventListener("click", async () => {
  try {
    const r = await api(`/exchange/orders?side=${exSide}&offset=${exOffset}`);
    const list = $("exOrders");
    list.insertAdjacentHTML("beforeend", r.items.map(orderRowHtml).join(""));
    bindOrderRows(list);
    exOffset += r.items.length;
    $("exLoadMore").classList.toggle("hidden", !r.has_more);
  } catch (e) { toast(e.message, "err"); }
});

// клик по чужому ордеру → модалка: сколько взять по этой цене (беру противоположную сторону)
function takeOrderSheet(o) {
  const myside = o.side === "buy" ? "sell" : "buy";
  const verb = myside === "buy" ? "Buy" : "Sell";
  openSheet(`${verb} at ${fmtPrice(o.price)}`, `
    <div class="hint">${o.name} ${o.side === "buy" ? "wants to buy" : "is selling"} <b>${fmt(o.amount)}</b> Coin @ ${fmtPrice(o.price)}.</div>
    <div class="field"><label>Amount to ${verb.toLowerCase()} (Coin)</label>
      <input id="tkoAmount" type="number" inputmode="numeric" value="${o.amount}"></div>
    <div class="trade-total"><span>Total</span><b id="tkoTotal">${fmtUsd(o.amount * o.price)} USD</b></div>
    <button class="btn-primary ${myside}" id="tkoGo">${verb} Coin</button>`);
  $("tkoAmount").addEventListener("input", () => {
    $("tkoTotal").textContent = fmtUsd((+$("tkoAmount").value || 0) * o.price) + " USD";
  });
  $("tkoGo").addEventListener("click", async () => {
    const amt = Math.min(+$("tkoAmount").value || 0, o.amount);
    closeSheet();
    await placeOrder(myside, o.price, amt);
  });
}

function renderTrades() {
  const rows = exData.trades.filter((t) => t.side === exSide);
  $("exTrades").innerHTML = rows.length
    ? rows.map((t) => {
        const d = new Date(t.t * 1000);
        const hh = String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
        const col = t.side === "buy" ? "var(--green)" : "var(--red)";
        return `
      <div class="item">
        <div class="item-mid">
          <div class="item-name" style="color:${col}">${fmt(t.amount)} Coin</div>
          <div class="item-sub">@ ${fmtPrice(t.price)} · ${hh}</div>
        </div>
        <div class="item-sub">${t.mine ? "you" : t.side}</div>
      </div>`;
      }).join("")
    : `<div class="item"><div class="item-mid" style="text-align:center;color:var(--txt-dim)">No ${exSide} trades yet</div></div>`;
}

async function loadMarket() {
  try {
    const r = await api("/exchange");
    exData = r;
    $("exCoins").textContent = fmt(r.coins);
    $("exUsd").textContent = fmtUsd(r.usd);
    $("exPrice").textContent = fmtPrice(r.price);
    $("exFeePct").textContent = r.fee_pct;
    const ch = $("exChange");
    ch.textContent = (r.change_pct >= 0 ? "+" : "") + r.change_pct + "%";
    ch.className = "chart-change " + (r.change_pct >= 0 ? "up" : "down");
    if (!$("exPriceIn").value) $("exPriceIn").placeholder = fmtPx(r.price);
    recalcTrade();
    loadChart();

    $("exMyOrders").innerHTML = r.my_orders.length
      ? r.my_orders.map((o) => `
        <div class="item">
          <div class="item-ic">${ic(o.side === "buy" ? "down" : "up")}</div>
          <div class="item-mid">
            <div class="item-name" style="color:${o.side === "buy" ? "var(--green)" : "var(--red)"}">${o.side.toUpperCase()} ${fmt(o.amount)}</div>
            <div class="item-sub">@ ${fmtPrice(o.price)} · filled ${fmt(o.filled)}</div>
          </div>
          <button class="item-btn danger" data-cancel="${o.id}">Cancel</button>
        </div>`).join("")
      : `<div class="item"><div class="item-mid" style="text-align:center;color:var(--txt-dim)">No open orders</div></div>`;
    $("exMyOrders").querySelectorAll("[data-cancel]").forEach((b) =>
      b.addEventListener("click", async () => {
        try { await api("/exchange/cancel", { id: +b.dataset.cancel }); toast("Order cancelled", "ok"); loadMarket(); }
        catch (e) { toast(e.message, "err"); }
      })
    );

    renderOrders();
    renderTrades();

    $("exHolders").innerHTML = r.holders.map((h, i) => `
      <div class="item">
        <div class="rank-n ${i < 3 ? "top" + (i + 1) : ""}">${i + 1}</div>
        <div class="item-mid"><div class="item-name">${h.name}${h.me ? " · you" : ""}</div></div>
        <div class="item-sub mono">${fmt(h.coins)}</div>
      </div>`).join("");
    mountIcons($("screen-market"));
  } catch (e) { toast(e.message, "err"); }
}

/* ───────── earn (3-in-1) ───────── */
let upgrades = [];
let branch = "tap";

document.querySelectorAll("[data-open]").forEach((b) =>
  b.addEventListener("click", () => {
    haptic("light");
    $("earnRoot").classList.add("hidden");
    const map = { upgrades: "subUpgrades", tasks: "subTasks", friends: "subFriends" };
    $(map[b.dataset.open]).classList.remove("hidden");
    if (b.dataset.open === "upgrades") loadUpgrades();
    if (b.dataset.open === "tasks") loadTasks();
    if (b.dataset.open === "friends") loadFriends();
  })
);
document.querySelectorAll("[data-back]").forEach((b) =>
  b.addEventListener("click", () => {
    document.querySelectorAll(".subview").forEach((s) => s.classList.add("hidden"));
    $("earnRoot").classList.remove("hidden");
    loadEarn();
  })
);

function upgradeRow(u, compact = false) {
  const el = document.createElement("div");
  el.className = "item";
  const afford = S && S.user.coins + optimisticGain >= (u.cost ?? Infinity);
  el.innerHTML = `
    <div class="item-ic">${ic(UP_ICONS[u.id] || "up")}</div>
    <div class="item-mid">
      <div class="item-name">${u.name} <span class="lvl-tag">lv ${u.level}${u.maxed ? " · MAX" : ""}</span></div>
      <div class="item-sub">${u.desc}</div>
    </div>
    <button class="item-btn" ${u.maxed || !afford ? "disabled" : ""}>${u.maxed ? "MAX" : fmt(u.cost)}</button>`;
  if (!u.maxed) {
    el.querySelector("button").addEventListener("click", async () => {
      try {
        const r = await api("/upgrades/buy", { id: u.id });
        S.user.coins = r.coins;
        toast(`${u.name} → lv ${r.level}`, "ok");
        notifyHaptic("success");
        const fresh = await api("/state");
        applySnapshot(fresh);
        renderUser(); renderBalance();
        compact ? loadEarn() : loadUpgrades();
      } catch (e) { toast(e.message, "err"); }
    });
  }
  return el;
}

async function loadEarn() {
  try {
    const [up, t, f] = await Promise.all([api("/upgrades"), api("/tasks"), api("/friends")]);
    upgrades = up.items;

    const cheap = up.items.filter((u) => !u.maxed).sort((a, b) => a.cost - b.cost).slice(0, 3);
    const upWrap = $("earnUpPreview");
    upWrap.innerHTML = "";
    cheap.forEach((u) => upWrap.appendChild(upgradeRow(u, true)));

    const open = t.items.filter((x) => !x.claimed).slice(0, 3);
    const tWrap = $("earnTaskPreview");
    tWrap.innerHTML = "";
    open.forEach((task) => tWrap.appendChild(taskRow(task, true)));
    if (!open.length)
      tWrap.innerHTML = `<div class="item"><div class="item-mid" style="text-align:center;color:var(--txt-dim)">All tasks done</div></div>`;

    $("earnFriendPreview").innerHTML = `
      <div class="item">
        <div class="item-ic">${ic("users")}</div>
        <div class="item-mid">
          <div class="item-name">${f.count} friends</div>
          <div class="item-sub">+${fmt(f.bonus_inviter)} per invite · ${f.share_percent}% of their mining</div>
        </div>
      </div>`;
    window._friendsData = f;
  } catch (e) { toast(e.message, "err"); }
}

$("branchChips").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  branch = chip.dataset.branch;
  document.querySelectorAll("#branchChips .chip").forEach((c) => c.classList.toggle("active", c === chip));
  renderUpgrades();
});
async function loadUpgrades() {
  try {
    const r = await api("/upgrades");
    upgrades = r.items;
    renderUpgrades();
  } catch (e) { toast(e.message, "err"); }
}
function renderUpgrades() {
  const list = $("upgradeList");
  list.innerHTML = "";
  upgrades.filter((x) => x.branch === branch).forEach((u) => list.appendChild(upgradeRow(u)));
}

/* tasks */
const CAT_NAMES = { daily: "Daily", weekly: "Weekly", special: "Special" };
async function loadTasks() {
  try {
    const r = await api("/tasks");
    const list = $("taskList");
    list.innerHTML = "";
    for (const cat of ["daily", "weekly", "special"]) {
      const items = r.items.filter((t) => t.cat === cat);
      if (!items.length) continue;
      const head = document.createElement("div");
      head.className = "cat-head";
      head.textContent = CAT_NAMES[cat];
      list.appendChild(head);
      const wrap = document.createElement("div");
      wrap.className = "list";
      items.forEach((t) => wrap.appendChild(taskRow(t)));
      list.appendChild(wrap);
    }
  } catch (e) { toast(e.message, "err"); }
}

function taskRow(t, compact = false) {
  const el = document.createElement("div");
  el.className = "item";
  const done = t.progress >= t.goal;
  const pct = Math.min(100, (t.progress / t.goal) * 100);
  const linkLike = !!t.url && ["link", "channel", "social"].includes(t.kind);
  const iconName = t.icon || TASK_ICONS[t.kind] || "check";
  el.innerHTML = `
    <div class="item-ic">${ic(iconName)}</div>
    <div class="item-mid">
      <div class="item-name">${t.name}</div>
      <div class="item-sub">+${fmt(t.reward)} Coin · +${t.xp} XP${linkLike ? "" : ` · ${fmt(t.progress)}/${fmt(t.goal)}`}</div>
      ${linkLike || compact ? "" : `<div class="mini-bar"><span class="mini-fill" style="width:${pct}%"></span></div>`}
    </div>`;
  const btn = document.createElement("button");
  if (t.claimed) {
    btn.className = "item-btn done";
    btn.textContent = "Done";
    btn.disabled = true;
  } else if (linkLike) {
    btn.className = "item-btn ghost";
    btn.textContent = "Open";
    btn.addEventListener("click", () => {
      if (t.url.startsWith("https://t.me")) tg?.openTelegramLink ? tg.openTelegramLink(t.url) : window.open(t.url);
      else tg?.openLink ? tg.openLink(t.url) : window.open(t.url);
      btn.textContent = "Claim";
      btn.className = "item-btn";
      btn.onclick = () => claimTask(t.id, compact);
    });
  } else {
    btn.className = "item-btn";
    btn.textContent = "Claim";
    btn.disabled = !done;
    btn.addEventListener("click", () => claimTask(t.id, compact));
  }
  el.appendChild(btn);
  return el;
}
async function claimTask(id, compact = false) {
  try {
    const r = await api("/tasks/claim", { id });
    Object.assign(S.user, { coins: r.coins, xp: r.xp, level: r.level });
    toast(`+${fmt(r.reward)} Coin, +${r.xp} XP`, "ok");
    notifyHaptic("success");
    renderUser(); renderBalance();
    compact ? loadEarn() : loadTasks();
  } catch (e) { toast(e.message, "err"); }
}

/* friends */
let refLink = "";
async function loadFriends() {
  try {
    const r = window._friendsData || (await api("/friends"));
    window._friendsData = null;
    refLink = r.link;
    $("refLink").textContent = r.link;
    $("friendCount").textContent = r.count;
    $("refBonusTxt").innerHTML =
      `Invite friends — you get <b>+${fmt(r.bonus_inviter)}</b>, they get <b>+${fmt(r.bonus_friend)}</b>, plus <b>${r.share_percent}%</b> of their mining. Forever.`;
    const list = $("friendList");
    list.innerHTML = "";
    if (!r.friends.length) {
      list.innerHTML = `<div class="item"><div class="item-mid" style="text-align:center;color:var(--txt-dim)">No friends yet — share your link</div></div>`;
      return;
    }
    r.friends.forEach((f) => {
      const el = document.createElement("div");
      el.className = "item";
      el.innerHTML = `
        <div class="ava">${(f.name || "?")[0].toUpperCase()}</div>
        <div class="item-mid">
          <div class="item-name">${f.name}</div>
          <div class="item-sub">Lv ${f.level}</div>
        </div>
        <div class="item-sub mono">${fmt(f.earned)}</div>`;
      list.appendChild(el);
    });
  } catch (e) { toast(e.message, "err"); }
}
$("copyRefBtn").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(refLink); toast("Link copied", "ok"); }
  catch { toast(refLink); }
});
$("shareRefBtn").addEventListener("click", () => {
  const url = `https://t.me/share/url?url=${encodeURIComponent(refLink)}&text=${encodeURIComponent("Join me in nCoin — tap, mine, trade!")}`;
  tg?.openTelegramLink ? tg.openTelegramLink(url) : window.open(url);
});

/* ───────── top / лиги ───────── */
let lbBy = "coins";
let lbLeague = "";
$("lbSeg").addEventListener("click", (e) => {
  const btn = e.target.closest(".seg-btn");
  if (!btn) return;
  lbBy = btn.dataset.by;
  document.querySelectorAll("#lbSeg .seg-btn").forEach((b) => b.classList.toggle("active", b === btn));
  loadTop();
});

function renderLeagueChips() {
  const wrap = $("leagueChips");
  if (wrap.childElementCount) return;
  const mk = (key, label, color) =>
    `<button class="chip ${key === lbLeague ? "active" : ""}" data-league="${key}">
       ${key ? `<span class="mini-shield">${shield(key, 15)}</span>` : ""}${label}
     </button>`;
  wrap.innerHTML = mk("", "All") + LEAGUES.map((l) => mk(l.key, l.name)).join("");
  wrap.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    lbLeague = chip.dataset.league;
    wrap.querySelectorAll(".chip").forEach((c) => c.classList.toggle("active", c === chip));
    loadTop();
  });
}

async function loadTop() {
  renderLeagueChips();
  try {
    const r = await api("/leaderboard?by=" + lbBy + (lbLeague ? "&league=" + lbLeague : ""));
    const ml = r.my_league;
    $("myLeague").innerHTML = `
      <div class="league-shield">${shield(ml.key)}</div>
      <div class="league-mid">
        <div class="league-name" style="color:${leagueColor(ml.key)}">${ml.name} League</div>
        <div class="league-next">${ml.next ? `${fmt(ml.next.min)} earned → ${ml.next.name}` : "Max league reached"}</div>
        <div class="mini-bar"><span class="mini-fill" style="width:${ml.progress * 100}%"></span></div>
      </div>
      <div class="chart-change up">#${fmt(r.me.rank)}</div>`;
    const my = $("myRank");
    my.classList.remove("hidden");
    my.innerHTML = `<span>Your rank${lbLeague ? " in league" : ""}</span><b>#${fmt(r.me.rank)} · ${fmt(r.me.value)}</b>`;
    $("lbList").innerHTML = r.top
      .map(
        (row) => `
      <div class="item">
        <div class="rank-n ${row.rank <= 3 ? "top" + row.rank : ""}">${row.rank}</div>
        <span class="mini-shield">${shield(row.league, 18)}</span>
        <div class="item-mid">
          <div class="item-name">${row.name}</div>
          <div class="item-sub">Lv ${row.level}</div>
        </div>
        <div class="item-sub mono">${fmt(row.value)}</div>
      </div>`
      )
      .join("");
  } catch (e) { toast(e.message, "err"); }
}

/* ───────── wallet ───────── */
async function loadWallet() {
  try {
    const [p, w] = await Promise.all([api("/profile"), api("/wallet")]);
    const ph = photoUrl();
    $("avaBig").innerHTML = ph ? `<img src="${ph}" alt="">` : (p.name || "N")[0].toUpperCase();
    applyTheme(p.theme, ph);
    $("profName").textContent = p.name;
    const joined = new Date(p.created_at * 1000).toLocaleDateString();
    $("profSub").textContent = `id ${p.id} · joined ${joined}`;
    $("wCoins").textContent = fmt(p.coins);
    $("wUsd").textContent = fmtUsd(p.usd);
    const pct = p.change_pct;
    $("wToday").innerHTML =
      `Today: <b class="${pct === null || pct >= 0 ? "up" : "down"}">+${fmt(p.earned_today)} Coin${pct === null ? "" : ` (${pct >= 0 ? "+" : ""}${pct}%)`}</b>`;
    $("planName").innerHTML = w.vip_name;
    $("planName").insertAdjacentHTML("afterbegin", ic("crown"));
    $("planSlots").textContent = `${w.withdraw_used}/${w.withdraw_slots} withdraws used this week`;
    $("planFees").textContent =
      `Fees: trade ${w.fees.trade}% · send ${w.fees.p2p}% · withdraw ${w.fees.withdraw}%`;
    $("stMined").textContent = fmt(p.stats.mined);
    $("stTapped").textContent = fmt(p.stats.tapped);
    $("stRef").textContent = fmt(p.stats.ref_income);
    $("stTasks").textContent = fmt(p.stats.tasks_done);
    $("sendLimitNote").textContent =
      `Send limit today: ${fmt(w.p2p_sent_today)}/${fmt(w.p2p_daily_limit)} Coin`;

    $("qSend").onclick = () => p2pSheet(w);
    $("qWithdraw").onclick = () => withdrawSheet(w);
    $("qDeposit").onclick = () => topupSheet();
    $("qEdit").onclick = () => editProfileSheet(p);
    $("qSupport").onclick = () => supportSheet(w);
    $("planUpgrade").onclick = () => plansSheet(w);
  } catch (e) { toast(e.message, "err"); }
}

const THEMES = {
  gold: ["#6b4c12", "#e8c15a"],
  violet: ["#3b1d6e", "#a97bff"],
  cyan: ["#0e4d5c", "#46e0ff"],
  crimson: ["#5c1420", "#ff6b6b"],
  emerald: ["#0f4a30", "#58d68d"],
  mono: ["#2a2a2e", "#c9ccd4"],
};
function themeDeep(theme) {
  if (theme && theme.startsWith("#")) return theme; // кастомный цвет
  return (THEMES[theme] || THEMES.gold)[0];
}
function applyTheme(theme, photo) {
  const deep = themeDeep(theme);
  const bg = $("heroBg");
  if (photo) bg.style.backgroundImage = `url(${photo})`;
  else bg.style.backgroundImage = `radial-gradient(circle at 50% 0%, ${deep}, #0b0a08 70%)`;
}

/* ───────── deposit / topup ───────── */
function topupSheet() {
  openSheet("Top up balance", `
    <div class="pay-methods" id="payMethods">
      <button class="pay glass-thin" data-m="visa">${ic("card")}<span>Visa / MC</span></button>
      <button class="pay glass-thin" data-m="crypto">${ic("crypto")}<span>USDT crypto</span></button>
    </div>
    <div class="field"><label>Amount (USD)</label><input id="tuAmount" type="number" step="1" inputmode="decimal" placeholder="10"></div>
    <div class="hint" id="tuHint">Choose a method. Payments are processed manually for now — admin credits your USD after payment.</div>
    <button class="btn-primary" id="tuSend" disabled>Select method</button>`);
  let method = "";
  $("payMethods").querySelectorAll(".pay").forEach((b) =>
    b.addEventListener("click", () => {
      method = b.dataset.m;
      $("payMethods").querySelectorAll(".pay").forEach((x) => x.classList.toggle("active", x === b));
      $("tuSend").disabled = false;
      $("tuSend").textContent = "Request top-up";
    })
  );
  $("tuSend").addEventListener("click", async () => {
    if (!method) return;
    try {
      const r = await api("/wallet/topup", { method, amount_usd: +$("tuAmount").value });
      closeSheet();
      toast(`Top-up via ${r.method}: $${r.amount_usd} — pending`, "ok");
      notifyHaptic("success");
    } catch (e) { toast(e.message, "err"); }
  });
}

/* ───────── edit profile ───────── */
function editProfileSheet(p) {
  const themeBtns = Object.keys(THEMES)
    .map((k) => `<button class="theme-dot ${p.theme === k ? "active" : ""}" data-theme="${k}" style="background:linear-gradient(135deg,${THEMES[k][1]},${THEMES[k][0]})"></button>`)
    .join("");
  const custom = p.theme && p.theme.startsWith("#") ? p.theme : "#e8c15a";
  openSheet("Edit profile", `
    <div class="field"><label>Display name</label><input id="epName" maxlength="32" placeholder="${p.name}" value="${p.name}"></div>
    <div class="field"><label>Background</label>
      <div class="theme-row" id="epThemes">${themeBtns}
        <label class="theme-dot custom" style="background:${custom}">
          <input type="color" id="epColor" value="${custom}" style="opacity:0;width:100%;height:100%">
        </label>
      </div>
    </div>
    <div class="hint">Pick a preset or your own color. Avatar comes from your Telegram photo.</div>
    <button class="btn-primary" id="epSave">Save</button>`);
  let theme = p.theme;
  $("epThemes").querySelectorAll(".theme-dot[data-theme]").forEach((b) =>
    b.addEventListener("click", () => {
      theme = b.dataset.theme;
      $("epThemes").querySelectorAll(".theme-dot").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      applyTheme(theme, photoUrl());
    })
  );
  $("epColor").addEventListener("input", (e) => {
    theme = e.target.value;
    e.target.parentElement.style.background = theme;
    $("epThemes").querySelectorAll(".theme-dot[data-theme]").forEach((x) => x.classList.remove("active"));
    applyTheme(theme, photoUrl());
  });
  $("epSave").addEventListener("click", async () => {
    try {
      const r = await api("/profile/update", { name: $("epName").value, theme });
      closeSheet();
      toast("Profile updated", "ok");
      notifyHaptic("success");
      if (S) { S.user.name = r.name; renderUser(); }
      loadWallet();
    } catch (e) { toast(e.message, "err"); }
  });
}

/* ───────── support (контакты из админки) ───────── */
function supportSheet(w) {
  const s = (w && w.support) || {};
  let buttons = "";
  if (s.tg) {
    const u = s.tg.replace(/^@/, "");
    buttons += `<button class="btn-primary" id="supTg">Message @${u}</button>`;
  }
  if (s.email) {
    buttons += `<button class="btn-secondary" id="supMail" style="margin-top:8px">Email ${s.email}</button>`;
  }
  if (!buttons) {
    buttons = `<button class="btn-primary" id="supBot">Open bot chat</button>`;
  }
  openSheet("Support", `
    <div class="hint" style="font-size:14px;text-align:center">${s.text || "Need help? Contact us."}<br><br>Your id: <b>${S ? S.user.id : ""}</b> — mention it.</div>
    ${buttons}
    <button class="btn-secondary" id="supClose" style="margin-top:8px">Close</button>`);
  if (s.tg) $("supTg").addEventListener("click", () => {
    const url = "https://t.me/" + s.tg.replace(/^@/, "");
    tg?.openTelegramLink ? tg.openTelegramLink(url) : window.open(url);
  });
  if (s.email) $("supMail").addEventListener("click", () => {
    tg?.openLink ? tg.openLink("mailto:" + s.email) : (window.location.href = "mailto:" + s.email);
  });
  if (!s.tg && !s.email) $("supBot").addEventListener("click", () => (tg?.close ? tg.close() : toast("Open the bot")));
  $("supClose").addEventListener("click", closeSheet);
}

/* ───────── sheets ───────── */
function openSheet(title, bodyHtml) {
  $("sheetTitle").textContent = title;
  $("sheetBody").innerHTML = bodyHtml;
  $("sheet").classList.remove("hidden");
  $("sheetBack").classList.remove("hidden");
}
function closeSheet() {
  $("sheet").classList.add("hidden");
  $("sheetBack").classList.add("hidden");
}
$("sheetBack").addEventListener("click", closeSheet);

function p2pSheet(w) {
  const left = Math.max(0, w.p2p_daily_limit - w.p2p_sent_today);
  openSheet("Send Coin", `
    <div class="field"><label>To (telegram id or @username)</label><input id="p2pTo" placeholder="@friend"></div>
    <div class="field"><label>Amount</label><input id="p2pAmount" type="number" inputmode="numeric" placeholder="min ${fmt(w.p2p_min)}"></div>
    <div class="hint">Fee ${w.fees.p2p}% · daily limit ${fmt(w.p2p_daily_limit)} Coin · left today: ${fmt(left)}</div>
    <button class="btn-primary" id="p2pSend">Send</button>`);
  $("p2pSend").addEventListener("click", async () => {
    try {
      const r = await api("/wallet/transfer", { to: $("p2pTo").value.trim(), amount: +$("p2pAmount").value });
      if (S) S.user.coins = r.coins;
      closeSheet();
      toast(`Sent ${fmt(r.sent)} (they got ${fmt(r.received)})`, "ok");
      notifyHaptic("success");
      renderBalance();
      loadWallet();
    } catch (e) { toast(e.message, "err"); }
  });
}

function withdrawSheet(w) {
  if (!w.withdraw_slots) {
    openSheet("Withdraw", `
      <div class="hint" style="text-align:center;font-size:14px">
        Withdrawals need a plan.<br><br>
        VIP 1 — 1× / week<br>VIP 2 — 2× / week<br>VIP 3 — 4× / week<br><br>
        Upgrade your plan below.
      </div>
      <button class="btn-primary" id="wdGoPlans">See plans</button>`);
    $("wdGoPlans").addEventListener("click", () => plansSheet(w));
    return;
  }
  const methods = (w.withdraw_methods || []).map(
    (m) => `<button class="pay glass-thin" data-wm="${m.key}" data-field="${m.field}">${ic("card")}<span>${m.name}</span></button>`
  ).join("");
  openSheet("Withdraw USD", `
    <div class="hint">Where do you want to withdraw?</div>
    <div class="pay-methods three" id="wdMethods">${methods}</div>
    <div class="field"><label>Amount (USD)</label><input id="wdAmount" type="number" step="1" inputmode="decimal" placeholder="min ${fmt(w.withdraw_min_usd)}"></div>
    <div class="field"><label id="wdDetailsLabel">Details</label><input id="wdDetails" placeholder="Select a method first" disabled></div>
    <div class="hint">Balance: ${fmtUsd(w.usd)} USD · fee ${w.fees.withdraw}% · slots: ${w.withdraw_used}/${w.withdraw_slots}. Sell Coin on the Exchange to get USD.</div>
    <button class="btn-primary" id="wdSend" disabled>Choose method</button>`);
  let method = "";
  $("wdMethods").querySelectorAll(".pay").forEach((b) =>
    b.addEventListener("click", () => {
      method = b.dataset.wm;
      $("wdMethods").querySelectorAll(".pay").forEach((x) => x.classList.toggle("active", x === b));
      $("wdDetailsLabel").textContent = b.dataset.field;
      $("wdDetails").disabled = false;
      $("wdDetails").placeholder = b.dataset.field;
      $("wdSend").disabled = false;
      $("wdSend").textContent = "Request withdraw";
    })
  );
  $("wdSend").addEventListener("click", async () => {
    if (!method) return;
    try {
      const r = await api("/wallet/withdraw", {
        amount_usd: +$("wdAmount").value,
        method,
        details: $("wdDetails").value.trim(),
      });
      closeSheet();
      toast(`Request #${r.request_id} sent: ${r.amount_usd} USD`, "ok");
      notifyHaptic("success");
      loadWallet();
    } catch (e) { toast(e.message, "err"); }
  });
}

function plansSheet(w) {
  const rows = w.tiers
    .filter((t) => t.tier > 0)
    .map(
      (t) => `
    <div class="tier-row ${w.vip === t.tier ? "mine" : ""}">
      <div><b>${t.name}</b><div class="tier-sub">${t.withdraw_per_week}× withdraw / week · −${t.discount || 0}% fees</div></div>
      <button class="item-btn ${w.vip >= t.tier ? "done" : ""}" data-tier="${t.tier}" ${w.vip >= t.tier ? "disabled" : ""}>
        ${w.vip >= t.tier ? "Active" : fmt(t.deposit_usd) + " USD"}
      </button>
    </div>`
    )
    .join("");
  openSheet("Your plan", `
    <div class="tiers">${rows}</div>
    <div class="hint" style="margin-top:10px">Deposit request goes to admin, payment confirmed manually. TON — soon.</div>`);
  $("sheetBody").querySelectorAll("[data-tier]").forEach((b) =>
    b.addEventListener("click", async () => {
      try {
        await api("/wallet/deposit", { tier: +b.dataset.tier });
        closeSheet();
        toast("Request sent — admin will contact you", "ok");
        notifyHaptic("success");
      } catch (e) { toast(e.message, "err"); }
    })
  );
}

/* ───────── boot ───────── */
async function boot() {
  try {
    tg?.ready?.();
    tg?.expand?.();
    try { tg?.setHeaderColor?.("#0b0a08"); tg?.setBackgroundColor?.("#0b0a08"); } catch {}
    mountIcons();
    const state = await api("/auth", {});
    applySnapshot(state);
    renderUser();
    renderBalance();
    tickHome();
    loadNews();
    loadEvents();
  } catch (e) {
    document.body.innerHTML =
      `<div style="display:grid;place-items:center;height:100vh;text-align:center;padding:24px;color:#f5f2ea;background:#0b0a08">
        <div><h2 style="margin:12px 0 6px">Can't connect</h2>
        <p style="opacity:.6">${e.message || e}</p></div></div>`;
  }
}

setInterval(tickHome, 250);
setInterval(tickEventTimers, 1000);
setInterval(async () => {
  if (!S || document.hidden || pendingTaps > 0 || flushing) return;
  try {
    const fresh = await api("/state");
    applySnapshot(fresh);
    renderUser();
    renderBalance();
  } catch {}
}, 45000);
document.addEventListener("visibilitychange", () => { if (!document.hidden && S) boot(); });

boot();
