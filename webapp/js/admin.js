/* nCoin admin panel — vanilla. */

const tg = window.Telegram?.WebApp;
const $ = (id) => document.getElementById(id);

const P = {
  users: '<circle cx="9" cy="8" r="3.2"/><path d="M3.5 19c.6-3 2.8-4.5 5.5-4.5S13.9 16 14.5 19M15.5 5.6a3.2 3.2 0 0 1 0 5M17.5 14.7c1.7.6 2.7 2 3 4.3"/>',
  wallet: '<path d="M3 7a2 2 0 0 1 2-2h13v3M3 7v10a2 2 0 0 0 2 2h14a1 1 0 0 0 1-1v-9H5a2 2 0 0 1-2-2Z"/><circle cx="16.5" cy="13.5" r="0.8"/>',
  chart: '<path d="M4 19h16M6 16l4-5 3 3 5-7"/>',
  gift: '<path d="M4 11h16v10H4zM2 7h20v4H2zM12 7v14M12 7c-2 0-4.5-.8-4.5-2.7C7.5 2.4 11 2.6 12 7ZM12 7c2 0 4.5-.8 4.5-2.7C16.5 2.4 13 2.6 12 7Z"/>',
  crown: '<path d="M4 18h16M5 16 4 7l4.5 3L12 5l3.5 5L20 7l-1 9z"/>',
  check: '<path d="M9 6h11M9 12h11M9 18h11M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2"/>',
  news: '<path d="M4 9v6l4 1 9 5V3L8 8H4a1 1 0 0 0-1 1M18 9a3 3 0 0 1 0 6"/>',
};
const ic = (n) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${P[n] || ""}</svg>`;
function mountIcons(root = document) {
  root.querySelectorAll("[data-ic]").forEach((el) => {
    const svg = ic(el.dataset.ic);
    if (el.tagName === "I") el.innerHTML = svg;
    else if (!el.querySelector("svg")) el.insertAdjacentHTML("afterbegin", svg);
  });
}

/* auth */
const authHeaders = {};
if (tg?.initData) authHeaders["X-Init-Data"] = tg.initData;
else authHeaders["X-Dev-User"] = localStorage.devUser || "5939110751";

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

/* utils */
const fmt = (n) => Math.floor(n).toLocaleString("en-US").replace(/,/g, " ");
const fmtPx = (p) => (+p).toFixed(6).replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
const fmtUsd = (u) => (+u).toFixed(u >= 1 ? 2 : 4).replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
const date = (t) => (t ? new Date(t * 1000).toLocaleDateString() : "—");
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

/* nav */
function go(name) {
  document.querySelectorAll(".ascreen").forEach((s) => s.classList.toggle("active", s.id === "a-" + name));
  window.scrollTo(0, 0);
  const load = { dashboard: loadDashboard, users: loadUsers, requests: loadRequests, market: loadMarket, tasks: loadTasksAdmin, events: loadEvents, news: loadNews, settings: loadSettings };
  load[name]?.();
}
document.querySelectorAll("[data-go]").forEach((b) => b.addEventListener("click", () => go(b.dataset.go)));
document.querySelectorAll("[data-home]").forEach((b) => b.addEventListener("click", () => go("dashboard")));

/* ═══ dashboard ═══ */
let chartKind = "price";
let chartTf = "day";

$("chartKind").addEventListener("click", (e) => {
  const btn = e.target.closest(".seg-btn");
  if (!btn) return;
  chartKind = btn.dataset.kind;
  document.querySelectorAll("#chartKind .seg-btn").forEach((b) => b.classList.toggle("active", b === btn));
  $("chartTitle").textContent = { price: "Price", users: "New users", volume: "Trade volume" }[chartKind];
  loadChart();
});
$("aTf").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  chartTf = chip.dataset.tf;
  document.querySelectorAll("#aTf .chip").forEach((c) => c.classList.toggle("active", c === chip));
  loadChart();
});

async function loadChart() {
  try {
    const r = await api(`/admin/chart?kind=${chartKind}&tf=${chartTf}`);
    const pts = r.points.map((p) => (chartKind === "price" ? p.p : p.v));
    drawChart(pts, chartKind === "price");
  } catch (e) { toast(e.message, "err"); }
}

function drawChart(vals, isLine) {
  const cv = $("aChart");
  const dpr = window.devicePixelRatio || 1;
  const w = cv.clientWidth || 320;
  const h = 150;
  cv.width = w * dpr;
  cv.height = h * dpr;
  const ctx = cv.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);
  if (!vals.length) vals = [0];
  if (vals.length === 1) vals = [vals[0], vals[0]]; // одна точка → плоская линия
  let min = Math.min(...vals), max = Math.max(...vals);
  if (min === max) { min = min * 0.98 - 1; max = max * 1.02 + 1; }
  const n = vals.length;
  const px = (i) => 8 + (n === 1 ? (w - 16) / 2 : (i / (n - 1)) * (w - 16));
  const py = (v) => 12 + (1 - (v - min) / (max - min)) * (h - 28);

  if (isLine || n > 1) {
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, "rgba(232,193,90,0.3)");
    grad.addColorStop(1, "rgba(232,193,90,0)");
    ctx.beginPath();
    vals.forEach((v, i) => (i ? ctx.lineTo(px(i), py(v)) : ctx.moveTo(px(0), py(v))));
    ctx.strokeStyle = "#e8c15a";
    ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    ctx.stroke();
    ctx.lineTo(px(n - 1), h);
    ctx.lineTo(px(0), h);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();
  } else {
    const bw = Math.min(40, (w - 16) / n - 6);
    vals.forEach((v, i) => {
      const x = px(i) - bw / 2;
      const y = py(v);
      ctx.fillStyle = "rgba(232,193,90,0.7)";
      ctx.fillRect(x, y, bw, h - y - 2);
    });
  }
}

async function loadDashboard() {
  try {
    const r = await api("/admin/stats");
    $("topPrice").textContent = fmtPx(r.market.price) + " USD";
    const m = r.market;
    $("kpiGrid").innerHTML = [
      ["Users", fmt(r.users.total), `+${r.users.new_24h} today · ${r.users.active_24h} active`],
      ["Coin supply", fmt(r.supply.coins), "in players' wallets"],
      ["USD supply", fmtUsd(r.supply.usd), "on balances"],
      ["Price", fmtPx(m.price), `official ${fmtPx(m.official)}`],
      ["Band", `${fmtPx(m.band_min)}–${fmtPx(m.band_max)}`, "today's corridor"],
      ["Volume 24h", fmt(m.volume_24h), `${m.trades_24h} trades`],
      ["Open orders", fmt(m.open_orders), "on the book"],
      ["Pending", `${r.pending.withdraws + r.pending.deposits}`, `${r.pending.withdraws} wd · ${r.pending.deposits} dep`],
    ]
      .map(([label, val, sub]) => `<div class="kpi"><span>${label}</span><b>${val}</b><div class="sub">${sub}</div></div>`)
      .join("");

    const pend = r.pending.withdraws + r.pending.deposits;
    const badge = $("reqBadge");
    badge.textContent = pend;
    badge.classList.toggle("hidden", pend === 0);

    $("topPlayers").innerHTML = r.top
      .map(
        (u, i) => `
      <div class="item">
        <div class="rank-n ${i < 3 ? "top" + (i + 1) : ""}">${i + 1}</div>
        <div class="item-mid">
          <div class="item-name">${u.name}</div>
          <div class="item-sub">Lv ${u.level} · ${u.vip_name} · earned ${fmt(u.total_earned)}</div>
        </div>
        <div class="u-bal"><div class="c">${fmt(u.coins)}</div><div class="u">${fmtUsd(u.usd)} USD</div></div>
      </div>`
      )
      .join("");
    loadChart();
  } catch (e) {
    toast(e.message, "err");
    if (e.code === 403) document.body.innerHTML =
      `<div style="display:grid;place-items:center;height:100vh;text-align:center;color:#f5f2ea">
        <div><h2>Admins only</h2><p style="opacity:.6">${e.message}</p></div></div>`;
  }
}

/* ═══ users ═══ */
$("userSearchBtn").addEventListener("click", () => loadUsers());
$("userSearch").addEventListener("keydown", (e) => { if (e.key === "Enter") loadUsers(); });

async function loadUsers() {
  try {
    const q = $("userSearch").value.trim();
    const r = await api("/admin/users?q=" + encodeURIComponent(q));
    $("usersCount").textContent = `${r.total} users`;
    $("usersList").innerHTML = r.items.length
      ? r.items.map(userRow).join("")
      : `<div class="item"><div class="item-mid" style="text-align:center;color:var(--txt-dim)">Nothing found</div></div>`;
    $("usersList").querySelectorAll("[data-uid]").forEach((el) =>
      el.addEventListener("click", () => userSheet(+el.dataset.uid))
    );
  } catch (e) { toast(e.message, "err"); }
}

function userRow(u) {
  const tags =
    (u.vip ? `<span class="u-tag vip">${u.vip_name}</span>` : "") +
    (u.banned ? `<span class="u-tag ban">BANNED</span>` : "") +
    (u.frozen ? `<span class="u-tag freeze">FROZEN</span>` : "");
  return `
    <div class="item" data-uid="${u.id}">
      <div class="item-mid">
        <div class="item-name">${u.name} <span class="lvl-tag">id ${u.id}</span></div>
        <div class="item-sub">Lv ${u.level} · ${u.ref_count} refs · joined ${date(u.created_at)}</div>
        ${tags ? `<div class="u-badges">${tags}</div>` : ""}
      </div>
      <div class="u-bal"><div class="c">${fmt(u.coins)}</div><div class="u">${fmtUsd(u.usd)} USD</div></div>
    </div>`;
}

async function userSheet(uid) {
  try {
    const u = await api("/admin/users/" + uid);
    const sources = u.sources
      .map((s) => {
        const amt = s.currency === "coin" ? fmt(s.total) : fmtUsd(s.total) + " USD";
        const cls = s.total >= 0 ? "pos" : "neg";
        return `<div class="src-row"><span>${s.reason} <span style="opacity:.5">×${s.ops}</span></span><span class="amt ${cls}">${s.total >= 0 ? "+" : ""}${amt}</span></div>`;
      })
      .join("");
    openSheet(
      u.name,
      `<div class="muted">id ${u.id} · Lv ${u.level} · ${u.vip_name} · ${u.ref_count} refs</div>
       <div class="market-now">
         <div><span>Coin</span><b>${fmt(u.coins)}</b></div>
         <div><span>USD</span><b>${fmtUsd(u.usd)}</b></div>
         <div><span>Earned</span><b>${fmt(u.total_earned)}</b></div>
       </div>
       <div class="muted">Money sources (where it came from):</div>
       <div class="src-list">${sources || "<div class='muted'>no ledger yet</div>"}</div>
       <div class="act-grid">
         <button class="btn-secondary" data-act="${u.banned ? "unban" : "ban"}">${u.banned ? "Unban" : "Ban"}</button>
         <button class="btn-secondary" data-act="${u.frozen ? "unfreeze" : "freeze"}">${u.frozen ? "Unfreeze" : "Freeze"}</button>
         <button class="btn-secondary" id="uVip">Set VIP</button>
         <button class="btn-secondary" id="uGive">Give Coin</button>
         <button class="btn-secondary" id="uGiveUsd">Give USD</button>
         <button class="btn-secondary" id="uClose">Close</button>
       </div>`
    );
    const doAct = async (action, value) => {
      try {
        await api(`/admin/users/${uid}/action`, { action, value });
        toast("Done", "ok");
        closeSheet();
        loadUsers();
      } catch (e) { toast(e.message, "err"); }
    };
    $("sheetBody").querySelectorAll("[data-act]").forEach((b) =>
      b.addEventListener("click", () => doAct(b.dataset.act))
    );
    $("uGive").addEventListener("click", () => {
      const v = prompt("Give how many Coin? (negative to remove)");
      if (v) doAct("give", +v);
    });
    $("uGiveUsd").addEventListener("click", () => {
      const v = prompt("Give how many USD?");
      if (v) doAct("give_usd", +v);
    });
    $("uVip").addEventListener("click", () => {
      const v = prompt("Set VIP tier 0-3", String(u.vip));
      if (v !== null) doAct("vip", +v);
    });
    $("uClose").addEventListener("click", closeSheet);
  } catch (e) { toast(e.message, "err"); }
}

/* ═══ requests ═══ */
async function loadRequests() {
  try {
    const r = await api("/admin/requests");
    $("wdList").innerHTML = r.withdraws.length
      ? r.withdraws.map((w) => reqRow(w, "withdraw")).join("")
      : `<div class="item"><div class="item-mid" style="text-align:center;color:var(--txt-dim)">No pending withdrawals</div></div>`;
    $("depList").innerHTML = r.deposits.length
      ? r.deposits.map((d) => reqRow(d, "deposit")).join("")
      : `<div class="item"><div class="item-mid" style="text-align:center;color:var(--txt-dim)">No pending deposits</div></div>`;
    bindReq();
  } catch (e) { toast(e.message, "err"); }
}
function reqRow(r, type) {
  const info =
    type === "withdraw"
      ? `${r.amount_usd} USD (fee ${fmtUsd(r.fee_usd)}) · ${r.vip_name}`
      : `wants ${r.tier_name}`;
  return `
    <div class="item">
      <div class="item-mid">
        <div class="item-name">#${r.id} · ${r.name}</div>
        <div class="item-sub">id ${r.user_id} · ${info}</div>
      </div>
      <div class="row-btns" style="width:auto;gap:6px">
        <button class="item-btn" data-ok="${type}:${r.id}">OK</button>
        <button class="item-btn danger" data-no="${type}:${r.id}">No</button>
      </div>
    </div>`;
}
function bindReq() {
  const decide = async (raw, approve) => {
    const [type, id] = raw.split(":");
    try {
      await api("/admin/requests/" + type, { id: +id, approve });
      toast(approve ? "Approved" : "Declined", "ok");
      loadRequests();
    } catch (e) { toast(e.message, "err"); }
  };
  $("a-requests").querySelectorAll("[data-ok]").forEach((b) => b.addEventListener("click", () => decide(b.dataset.ok, true)));
  $("a-requests").querySelectorAll("[data-no]").forEach((b) => b.addEventListener("click", () => decide(b.dataset.no, false)));
}

/* ═══ market ═══ */
function mkPreview() {
  const o = +$("mkOfficialIn").value || 0;
  const d = +$("mkDeltaIn").value || 0;
  $("mkBandPreview").textContent = o
    ? `Band: ${fmtPx(Math.max(0, o - d))} – ${fmtPx(o + d)} USD`
    : "";
}
async function loadMarket() {
  try {
    const r = await api("/admin/market");
    $("mkLast").textContent = fmtPx(r.last);
    $("mkOfficial").textContent = fmtPx(r.official);
    $("mkMin").textContent = fmtPx(r.day_min);
    $("mkMax").textContent = fmtPx(r.day_max);
    $("mkUpdated").textContent = "Updated: " + (r.updated_at ? new Date(r.updated_at * 1000).toLocaleString() : "—");
    $("mkOfficialIn").value = r.official;
    $("mkDeltaIn").value = r.delta;
    mkPreview();
  } catch (e) { toast(e.message, "err"); }
}
["mkOfficialIn", "mkDeltaIn"].forEach((id) => $(id).addEventListener("input", mkPreview));
$("mkSave").addEventListener("click", async () => {
  try {
    const r = await api("/admin/market", {
      official_usd: +$("mkOfficialIn").value,
      delta_usd: +$("mkDeltaIn").value || 0,
      push_trade: $("mkPush").checked,
    });
    toast("Price set → " + fmtPx(r.official) + " USD", "ok");
    loadMarket();
  } catch (e) { toast(e.message, "err"); }
});

/* ═══ news ═══ */
let nwTag = "NEW";
$("nwTag").addEventListener("click", (e) => {
  const b = e.target.closest(".seg-btn"); if (!b) return;
  nwTag = b.dataset.tag;
  document.querySelectorAll("#nwTag .seg-btn").forEach((x) => x.classList.toggle("active", x === b));
});
$("nwCreate").addEventListener("click", async () => {
  try {
    await api("/admin/news", { tag: nwTag, title: $("nwTitle").value.trim(), text: $("nwText").value.trim(), sort: +$("nwSort").value || 0 });
    toast("Card added", "ok");
    $("nwTitle").value = ""; $("nwText").value = "";
    loadNews();
  } catch (e) { toast(e.message, "err"); }
});
async function loadNews() {
  try {
    const r = await api("/admin/news");
    $("nwList").innerHTML = r.items.length
      ? r.items.map((n) => `
        <div class="item">
          <div class="item-mid">
            <div class="item-name">${n.title} <span class="lvl-tag">${n.tag}</span>${n.active ? "" : ' <span class="u-tag ban">off</span>'}</div>
            <div class="item-sub">${n.text || ""}</div>
          </div>
          <div class="row-btns" style="width:auto;gap:6px">
            <button class="item-btn ${n.active ? "" : "gold"}" data-nt="${n.id}" data-a="${n.active ? "0" : "1"}">${n.active ? "Hide" : "Show"}</button>
            <button class="item-btn danger" data-nd="${n.id}">Del</button>
          </div>
        </div>`).join("")
      : `<div class="item"><div class="item-mid" style="text-align:center;color:var(--txt-dim)">No cards</div></div>`;
    $("nwList").querySelectorAll("[data-nt]").forEach((b) => b.addEventListener("click", async () => {
      try { await api("/admin/news/toggle", { id: +b.dataset.nt, active: b.dataset.a === "1" }); loadNews(); } catch (e) { toast(e.message, "err"); }
    }));
    $("nwList").querySelectorAll("[data-nd]").forEach((b) => b.addEventListener("click", async () => {
      try { await api("/admin/news/delete", { id: +b.dataset.nd }); loadNews(); } catch (e) { toast(e.message, "err"); }
    }));
  } catch (e) { toast(e.message, "err"); }
}

/* ═══ settings (support + VIP) ═══ */
async function loadSettings() {
  try {
    const r = await api("/admin/settings");
    $("setTg").value = r.support_tg || "";
    $("setEmail").value = r.support_email || "";
    $("setText").value = r.support_text || "";
    $("setVip").innerHTML = r.vip.map((v) => `
      <div class="vip-edit" data-tier="${v.tier}">
        <div class="vip-edit-name">${v.name}</div>
        <input class="v-price" type="number" step="0.5" value="${v.price}" placeholder="price $">
        <input class="v-disc" type="number" value="${v.discount}" placeholder="disc %">
        <input class="v-wd" type="number" value="${v.withdraws}" placeholder="wd/wk">
      </div>`).join("");
  } catch (e) { toast(e.message, "err"); }
}
$("setSave").addEventListener("click", async () => {
  try {
    const vip = [...document.querySelectorAll("#setVip .vip-edit")].map((row) => ({
      tier: +row.dataset.tier,
      price: +row.querySelector(".v-price").value || 0,
      discount: +row.querySelector(".v-disc").value || 0,
      withdraws: +row.querySelector(".v-wd").value || 0,
    }));
    await api("/admin/settings", {
      support_tg: $("setTg").value.trim(),
      support_email: $("setEmail").value.trim(),
      support_text: $("setText").value.trim(),
      vip,
    });
    toast("Settings saved", "ok");
  } catch (e) { toast(e.message, "err"); }
});

/* ═══ tasks ═══ */
let tkKind = "channel";
$("tkKind").addEventListener("click", (e) => {
  const btn = e.target.closest(".seg-btn");
  if (!btn) return;
  tkKind = btn.dataset.kind;
  document.querySelectorAll("#tkKind .seg-btn").forEach((b) => b.classList.toggle("active", b === btn));
});
$("tkCreate").addEventListener("click", async () => {
  try {
    await api("/admin/tasks", {
      title: $("tkTitle").value.trim(),
      url: $("tkUrl").value.trim(),
      reward: +$("tkReward").value,
      xp: +$("tkXp").value || 0,
      kind: tkKind,
    });
    toast("Task created", "ok");
    ["tkTitle", "tkUrl", "tkReward", "tkXp"].forEach((id) => ($(id).value = ""));
    loadTasksAdmin();
  } catch (e) { toast(e.message, "err"); }
});
async function loadTasksAdmin() {
  try {
    const r = await api("/admin/tasks");
    $("tkList").innerHTML = r.items.length
      ? r.items.map(tkRow).join("")
      : `<div class="item"><div class="item-mid" style="text-align:center;color:var(--txt-dim)">No tasks yet</div></div>`;
    $("tkList").querySelectorAll("[data-toggle]").forEach((b) =>
      b.addEventListener("click", async () => {
        try {
          await api("/admin/tasks/toggle", { id: +b.dataset.toggle, active: b.dataset.active === "1" });
          loadTasksAdmin();
        } catch (e) { toast(e.message, "err"); }
      })
    );
    $("tkList").querySelectorAll("[data-del]").forEach((b) =>
      b.addEventListener("click", async () => {
        try {
          await api("/admin/tasks/delete", { id: +b.dataset.del });
          toast("Deleted", "ok");
          loadTasksAdmin();
        } catch (e) { toast(e.message, "err"); }
      })
    );
  } catch (e) { toast(e.message, "err"); }
}
function tkRow(t) {
  return `
    <div class="item">
      <div class="item-mid">
        <div class="item-name">${t.title} ${t.active ? "" : '<span class="u-tag ban">off</span>'}</div>
        <div class="item-sub">${t.kind} · +${fmt(t.reward)} Coin · +${t.xp} XP · ${t.claims} claims</div>
      </div>
      <div class="row-btns" style="width:auto;gap:6px">
        <button class="item-btn ${t.active ? "" : "gold"}" data-toggle="${t.id}" data-active="${t.active ? "0" : "1"}">${t.active ? "Stop" : "Start"}</button>
        <button class="item-btn danger" data-del="${t.id}">Del</button>
      </div>
    </div>`;
}

/* ═══ events ═══ */
$("evCreate").addEventListener("click", async () => {
  try {
    await api("/admin/events", {
      title: $("evTitle").value.trim(),
      text: $("evText").value.trim(),
      reward: +$("evReward").value,
      minutes: +$("evMinutes").value,
      max_claims: +$("evMax").value || 0,
    });
    toast("Event launched", "ok");
    ["evTitle", "evText", "evReward", "evMinutes", "evMax"].forEach((id) => ($(id).value = ""));
    loadEvents();
  } catch (e) { toast(e.message, "err"); }
});
async function loadEvents() {
  try {
    const r = await api("/admin/events");
    $("evList").innerHTML = r.items.length
      ? r.items.map(evRow).join("")
      : `<div class="item"><div class="item-mid" style="text-align:center;color:var(--txt-dim)">No events yet</div></div>`;
    $("evList").querySelectorAll("[data-toggle]").forEach((b) =>
      b.addEventListener("click", async () => {
        try {
          await api("/admin/events/toggle", { id: +b.dataset.toggle, active: b.dataset.active === "1" });
          loadEvents();
        } catch (e) { toast(e.message, "err"); }
      })
    );
  } catch (e) { toast(e.message, "err"); }
}
function evRow(e) {
  const live = e.active && e.ends_in > 0;
  const claims = e.max_claims ? `${e.claims}/${e.max_claims}` : `${e.claims}`;
  return `
    <div class="item">
      <div class="item-mid">
        <div class="item-name">${e.title} ${live ? "" : '<span class="u-tag ban">off</span>'}</div>
        <div class="item-sub">+${fmt(e.reward)} Coin · ${claims} claims · ${live ? hms(e.ends_in) + " left" : "ended"}</div>
      </div>
      <button class="item-btn ${e.active ? "danger" : ""}" data-toggle="${e.id}" data-active="${e.active ? "0" : "1"}">
        ${e.active ? "Stop" : "Start"}
      </button>
    </div>`;
}

/* ═══ sheet / boot ═══ */
function openSheet(title, html) {
  $("sheetTitle").textContent = title;
  $("sheetBody").innerHTML = html;
  $("sheet").classList.remove("hidden");
  $("sheetBack").classList.remove("hidden");
}
function closeSheet() {
  $("sheet").classList.add("hidden");
  $("sheetBack").classList.add("hidden");
}
$("sheetBack").addEventListener("click", closeSheet);

setInterval(() => { if ($("a-events").classList.contains("active")) loadEvents(); }, 5000);

(function boot() {
  try { tg?.ready?.(); tg?.expand?.(); tg?.setBackgroundColor?.("#0b0a08"); } catch {}
  mountIcons();
  loadDashboard();
})();
