<script lang="ts">
  import { onMount } from 'svelte';

  // ===== Mock DB (localStorage) =====
  const LS = { users:'db_users', currentUser:'auth_user', currentAdmin:'auth_admin' };
  const MASTER = { id:'master', pw:'master123' };

  if (!localStorage.getItem(LS.users)) localStorage.setItem(LS.users, JSON.stringify([]));

  // ===== Utils =====
  const sleep = (ms:number)=> new Promise(r=>setTimeout(r,ms));

  function showToast(msg:string) {
    toast = msg;
    toastVisible = true;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(()=> toastVisible = false, 1200);
  }

  // ===== DB helpers =====
  type User = { id:string; pw:string; attempts:number; stage:number; maxStage:number; };

  function db_readUsers(): User[] {
    return JSON.parse(localStorage.getItem(LS.users) || '[]');
  }
  function db_writeUsers(arr: User[]) {
    localStorage.setItem(LS.users, JSON.stringify(arr));
  }
  function db_findUser(id: string): User | undefined {
    return db_readUsers().find(u => u.id === id);
  }
  function ensureSchema(u: Partial<User>): User {
    const v:any = { attempts:0, stage:0, maxStage:0, ...u };
    if (v.maxStage === undefined) v.maxStage = v.stage|0;
    return v as User;
  }
  function db_upsertUser(user: User) {
    user = ensureSchema(user);
    const arr = db_readUsers().map(ensureSchema);
    const i = arr.findIndex(u => u.id === user.id);
    if (i >= 0) arr[i] = user; else arr.push(user);
    db_writeUsers(arr);
  }

  // ===== Probabilities & Assets =====
  const PROBS:number[] = [
    1, 1, 0.95, 0.95, 0.95,
    0.9, 0.9, 0.85, 0.85, 0.8,
    0.75, 0.75, 0.7, 0.65, 0.65,
    0.6, 0.55, 0.55, 0.5, 0.5,
    0.4, 0.3, 0.2, 0.1
  ]; // 0→1 ... 23→24
  const MAX_STAGE = 24;

  // 단계별 검 이미지: 필요 단계에만 채우면 자동 교체
  const SWORDS:string[] = Array.from({length: MAX_STAGE+1}, ()=>"");
  // 예) SWORDS[0] = "/img/sword0.png"; SWORDS[5] = "/img/sword5.png";

  // ===== Screens & State =====
  type Screen = 'login'|'signup'|'game'|'adminLogin'|'adminPanel';
  let screen: Screen = 'login';

  // 로그인/회원가입
  let liId = '', liPw = '';
  let suId = '', suPw = '', suIdHint = '';

  // 게임
  let rate = 100;
  let attemptsLeft = 0;
  let bestStage = '+0';
  let stageTitle = '+0';
  let weaponSrc = '';
  let showFallback = true;
  let btnDisabled = true;

  // 관리자
  let adId = '', adPw = '';
  let users: User[] = [];
  let selectedUserId = '';
  let admAttempts: number = 0;

  // 리더보드
  let leaderboard: User[] = [];
  let lbHint = '';

  // 토스트
  let toast = '';
  let toastVisible = false;
  let toastTimer:any = null;

  // ===== Helpers =====
  const hashIsAdmin = () => location.hash === '#admin';

  function switchScreen(next: Screen) {
    screen = next;
  }

  function getAuthedUser(): User | null {
    const uid = localStorage.getItem(LS.currentUser);
    if (!uid) return null;
    const u = db_findUser(uid);
    return u ? ensureSchema(u) : null;
  }
  function setUser(u: User) {
    db_upsertUser(u);
  }

  function updateGameView() {
    const u = getAuthedUser();
    if (!u) { switchScreen('login'); return; }
    const st = Math.max(0, Math.min(MAX_STAGE, u.stage|0));
    const p = (st < PROBS.length) ? PROBS[st] : PROBS[PROBS.length-1];

    stageTitle = `+${st}`;
    rate = Math.round(p * 10000) / 100;
    attemptsLeft = u.attempts|0;
    bestStage = `+${u.maxStage|0}`;

    const src = SWORDS[st];
    if (src) { weaponSrc = src; showFallback = false; }
    else { showFallback = true; weaponSrc = ''; }

    btnDisabled = u.attempts <= 0;
  }

  function refreshLeaderboard() {
    const me = localStorage.getItem(LS.currentUser);
    const arr = db_readUsers().map(ensureSchema);
    arr.sort((a,b)=> (b.maxStage|0) - (a.maxStage|0) || a.id.localeCompare(b.id));
    leaderboard = arr.slice(0, 20);
    const myRank = arr.findIndex(u=>u.id===me);
    lbHint = (me && myRank>=0) ? `내 순위 ${myRank+1}/${arr.length}` : `총 ${arr.length}명`;
  }

  function loadAdminData() {
    users = db_readUsers().map(ensureSchema);
    // 선택값 유지 or 첫 번째 선택
    if (!users.find(u=>u.id===selectedUserId)) selectedUserId = users[0]?.id || '';
    fillFormFromSelected();
    refreshUsersTable();
  }
  function fillFormFromSelected() {
    const u = db_findUser(selectedUserId);
    if (!u) { admAttempts = 0; return; }
    const v = ensureSchema(u);
    admAttempts = v.attempts|0;
  }
  function refreshUsersTable() {
    // users 바인딩만 새로고침하면 테이블은 자동 갱신
    users = db_readUsers().map(ensureSchema);
  }

  function route() {
    if (hashIsAdmin()) {
      if (localStorage.getItem(LS.currentAdmin)) {
        switchScreen('adminPanel');
        loadAdminData();
      } else {
        switchScreen('adminLogin');
      }
    } else {
      if (localStorage.getItem(LS.currentUser)) {
        switchScreen('game');
        updateGameView();
        refreshLeaderboard();
      } else {
        switchScreen('login');
      }
    }
  }

  // ===== Event Handlers =====
  function onGotoSignup() {
    switchScreen('signup');
    onSuIdInput(); // 즉시 힌트 갱신
  }

  function onSuIdInput() {
    const id = suId.trim();
    if (!id) { suIdHint = ''; return; }
    if (id.length > 20) { suIdHint = '20자 초과'; return; }
    if (id === MASTER.id) { suIdHint = '사용 불가'; return; }
    suIdHint = db_findUser(id) ? '이미 존재' : '사용 가능';
  }

  function onSignup() {
    const id = suId.trim(), pw = suPw;
    if (!id || !pw) return showToast('입력 필요');
    if (id.length > 20) return showToast('아이디 20자 이내');
    if (id === MASTER.id) return showToast('사용 불가');
    if (db_findUser(id)) return showToast('중복 아이디');
    db_upsertUser({ id, pw, attempts:0, stage:0, maxStage:0 });
    liId = id; liPw = ''; suId=''; suPw=''; suIdHint='';
    switchScreen('login');
  }

  function onLogin() {
    const id = liId.trim(), pw = liPw;
    if (id === MASTER.id && pw === MASTER.pw) {
      localStorage.setItem(LS.currentAdmin, MASTER.id);
      location.hash = '#admin';
      return;
    }
    const u = db_findUser(id);
    if (!u || u.pw !== pw) return showToast('로그인 실패');
    db_upsertUser(ensureSchema(u));
    localStorage.setItem(LS.currentUser, id);
    updateGameView(); refreshLeaderboard(); switchScreen('game');
  }

  function onEnhance() {
    const u = getAuthedUser(); if (!u) return;
    if (u.attempts <= 0) return showToast('시도 없음');

    const st = u.stage|0;
    const p  = (st < PROBS.length) ? PROBS[st] : PROBS[PROBS.length-1];
    const ok = Math.random() < p;

    if (ok) {
      if (st < MAX_STAGE) { u.stage = st+1; showToast(`성공 +${u.stage}`); }
      else showToast('최고 단계');
      if (u.stage > (u.maxStage||0)) u.maxStage = u.stage;
    } else {
      u.attempts = Math.max(0, (u.attempts|0)-1);
      u.stage = 1;
      showToast('실패');
    }
    setUser(u); updateGameView(); refreshLeaderboard();
  }

  function onLogout() {
    localStorage.removeItem(LS.currentUser);
    switchScreen('login');
  }

  function onAdminLogin() {
    const id = adId.trim(), pw = adPw;
    if (id === MASTER.id && pw === MASTER.pw) {
      localStorage.setItem(LS.currentAdmin, MASTER.id);
      switchScreen('adminPanel'); loadAdminData();
    } else {
      showToast('실패');
    }
  }
  function onAdminBackHome() {
    location.hash = '';
    if (localStorage.getItem(LS.currentUser)) { switchScreen('game'); updateGameView(); refreshLeaderboard(); }
    else { switchScreen('login'); }
  }
  function onAdminLogout() {
    localStorage.removeItem(LS.currentAdmin);
    location.hash = '#admin';
    switchScreen('adminLogin');
  }
  function onAdminGoMain() {
    location.hash = '';
    if (localStorage.getItem(LS.currentUser)) { switchScreen('game'); updateGameView(); refreshLeaderboard(); }
    else { switchScreen('login'); }
  }

  function onSaveAttempts() {
    const id = selectedUserId;
    const u = db_findUser(id);
    if (!u) return showToast('대상 선택');
    const v = ensureSchema(u);
    v.attempts = Math.max(0, parseInt(String(admAttempts||0),10));
    db_upsertUser(v);
    refreshUsersTable();
    showToast('저장');
  }

  function onReloadUsers() {
    loadAdminData();
    showToast('새로고침');
  }

  // ===== Lifecycle =====
  let syncInterval: any = null;

  // 서버에 현재 레벨 정보 동기화
  async function syncToServer() {
    const u = getAuthedUser();
    if (!u) return;

    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:8000/api/game/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          userId: u.id,
          currentStage: u.stage || 0,
          maxStage: u.maxStage || 0,
          attempts: u.attempts || 0
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      console.log('서버 동기화 성공');
    } catch (error) {
      console.error('서버 동기화 실패:', error);
    }
  }

  onMount(() => {
    window.addEventListener('hashchange', route);
    route();

    // 10초마다 서버와 동기화
    syncInterval = setInterval(() => {
      if (screen === 'game') {
        syncToServer();
      }
    }, 10000);

    // 정리 함수
    return () => {
      if (syncInterval) {
        clearInterval(syncInterval);
      }
    };
  });
</script>

<!-- ===== UI ===== -->
<div class="frame">
  <h1 class="title"><b>검</b> 강화하기</h1>

  <!-- 로그인 -->
  {#if screen === 'login'}
  <section class="screen active">
    <div class="stack">
      <div class="row">
        <label class="label">아이디</label>
        <input bind:value={liId} placeholder="아이디" autocomplete="username" />
      </div>
      <div class="row">
        <label class="label">비밀번호</label>
        <input bind:value={liPw} type="password" placeholder="비밀번호" autocomplete="current-password" />
      </div>
      <div class="row">
        <button class="btn primary" type="button" on:click={onLogin}>로그인</button>
      </div>
      <div class="row center">
        <button class="btn gray" type="button" on:click={onGotoSignup}>회원가입</button>
      </div>
    </div>
  </section>
  {/if}

  <!-- 회원가입 -->
  {#if screen === 'signup'}
  <section class="screen active">
    <div class="stack">
      <div class="row">
        <label class="label">아이디(≤20자)</label>
        <input bind:value={suId} maxlength="20" autocomplete="off" on:input={onSuIdInput} />
        <div class="label" style="font-size:12px">{suIdHint}</div>
      </div>
      <div class="row">
        <label class="label">비밀번호</label>
        <input bind:value={suPw} type="password" />
      </div>
      <div class="row">
        <button class="btn primary" type="button" on:click={onSignup}>가입</button>
      </div>
      <div class="row center">
        <button class="btn gray" type="button" on:click={() => switchScreen('login')}>로그인으로</button>
      </div>
    </div>
  </section>
  {/if}

  <!-- 게임 -->
  {#if screen === 'game'}
  <section class="screen active">
    <div class="game-grid">
      <div class="panel">
        <div class="stagebox">
          <div style="text-align:center">
            {#if !showFallback}
              <img class="weapon" alt="weapon" src={weaponSrc} />
            {:else}
              <svg class="fallback" viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
                <g stroke="#000" stroke-width="10" fill="#ddd">
                  <path d="M210 40 L250 80 L130 200 L100 240 L60 200 L100 170 Z" />
                  <rect x="120" y="170" width="40" height="30" rx="6" />
                </g>
              </svg>
            {/if}
            <div class="stage-title">{stageTitle}</div>
            <div class="stats">
              <div class="stat">성공률 <span>{rate}</span>%</div>
              <div class="stat">시도 <span>{attemptsLeft}</span></div>
              <div class="stat">최고 <span>{bestStage}</span></div>
            </div>
          </div>
        </div>
      </div>

      <div class="panel center">
        <button class="btn bigbtn" type="button" disabled={btnDisabled} on:click={onEnhance}>강화</button>
        <div class="logout-area" style="width:100%">
          <button class="btn" type="button" on:click={onLogout}>로그아웃</button>
        </div>
      </div>

      <div class="panel leader">
        <h3 style="margin:0 0 8px;font-weight:900">리더보드</h3>
        <table class="table">
          <thead><tr><th>#</th><th>아이디</th><th>최대</th></tr></thead>
          <tbody>
            {#each leaderboard as u, i}
              <tr class={localStorage.getItem(LS.currentUser) === u.id ? 'me' : ''}>
                <td>{i+1}</td><td>{u.id}</td><td>+{u.maxStage|0}</td>
              </tr>
            {/each}
          </tbody>
        </table>
        <div style="margin-top:6px;font-weight:900">{lbHint}</div>
      </div>
    </div>
  </section>
  {/if}

  <!-- 마스터 로그인 -->
  {#if screen === 'adminLogin'}
  <section class="screen active">
    <div class="stack">
      <div class="row">
        <label class="label">마스터 아이디</label>
        <input bind:value={adId} />
      </div>
      <div class="row">
        <label class="label">비밀번호</label>
        <input bind:value={adPw} type="password" />
      </div>
      <div class="row">
        <button class="btn primary" type="button" on:click={onAdminLogin}>로그인</button>
      </div>
      <div class="row center">
        <button class="btn gray" type="button" on:click={onAdminBackHome}>메인으로</button>
      </div>
    </div>
  </section>
  {/if}

  <!-- 마스터 패널 -->
  {#if screen === 'adminPanel'}
  <section class="screen active">
    <div class="grid">
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
        <div class="row">
          <label class="label">회원</label>
          <select bind:value={selectedUserId} on:change={fillFormFromSelected}>
            {#each users as u}
              <option value={u.id}>{u.id}</option>
            {/each}
          </select>
        </div>
        <button class="btn gray" type="button" on:click={onReloadUsers}>새로고침</button>
        <button class="btn" type="button" on:click={onAdminLogout}>로그아웃</button>
        <button class="btn gray" type="button" on:click={onAdminGoMain}>메인으로</button>
      </div>

      <div class="panel">
        <h4 style="margin:0 0 8px">시도횟수</h4>
        <div style="display:flex;gap:10px;align-items:end;flex-wrap:wrap">
          <div class="row">
            <label class="label">시도</label>
            <input type="number" min="0" bind:value={admAttempts} />
          </div>
          <button class="btn blue" type="button" on:click={onSaveAttempts}>저장</button>
        </div>
      </div>

      <div class="panel">
        <h4 style="margin:0 0 8px">회원 현황</h4>
        <table class="table">
          <thead><tr><th>아이디</th><th>시도</th><th>현재</th><th>최대</th></tr></thead>
          <tbody>
            {#each users as u}
              <tr>
                <td>{u.id}</td><td>{u.attempts|0}</td><td>+{u.stage|0}</td><td>+{u.maxStage|0}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  </section>
  {/if}

  <!-- 토스트 -->
  {#if toastVisible}
    <div class="toast">{toast}</div>
  {/if}
</div>

<style>
  :root{ --bg:#202225; --panel:#fff; --ink:#111; --shadow:rgba(0,0,0,.25); --accent:#ff2a2a; --blue:#3a6bff; }
  *{box-sizing:border-box} html,body{height:100%}
  body{margin:0;background:var(--bg);display:grid;place-items:center;font-family:Pretendard,Segoe UI,Arial,Apple SD Gothic Neo,sans-serif}
  .frame{width:min(1100px,96vw);min-height:640px;background:var(--panel);border:4px solid #000;border-radius:14px;box-shadow:0 8px 0 #000, 0 16px 28px var(--shadow);padding:22px}
  .title{margin:0;text-align:center;font-weight:900;font-size:44px;letter-spacing:1px;color:#fff;text-shadow:-4px 4px 0 #000}
  .title b{color:var(--accent)}
  .row{display:grid;gap:6px}
  .label{font-weight:900}
  input,select{border:3px solid #000;border-radius:10px;padding:10px 12px;font-weight:800}
  .btn{cursor:pointer;border:3px solid #000;border-radius:10px;background:#fff;padding:10px 16px;font-weight:900;display:inline-grid;place-items:center;transition:transform .02s}
  .btn:active{transform:translateY(2px)}
  .btn.primary{background:linear-gradient(#ffd38a,#ffae00)}
  .btn.blue{background:linear-gradient(#cfe0ff,#7ea4ff)}
  .btn.gray{background:#f1f1f1}
  .center{display:grid;place-items:center}
  .stack{display:grid;gap:14px;max-width:420px;margin:26px auto}
  .grid{display:grid;gap:12px}

  .game-grid{display:grid;grid-template-columns:1fr 1fr .9fr;gap:24px;margin-top:8px}
  @media (max-width:980px){ .game-grid{grid-template-columns:1fr 1fr} .leader{grid-column:1 / -1} }
  @media (max-width:720px){ .game-grid{grid-template-columns:1fr} }
  .panel{border:3px solid #000;border-radius:12px;padding:16px;background:#fff}
  .stagebox{display:grid;place-items:center;min-height:320px;background:#f7f7f7;border:3px solid #000;border-radius:10px}
  .stage-title{font-weight:900;font-size:36px;margin-top:6px}
  .stats{display:grid;gap:6px;margin-top:10px;text-align:center}
  .stat{font-weight:900}
  .bigbtn{width:220px;height:220px;border-radius:50%;background:radial-gradient(circle at 50% 45%, #777 0%, #5a5a5a 48%, #3a3a3a 49%, #333 100%);box-shadow:4px 4px 0 #000, 0 12px 18px var(--shadow);color:#fff;text-shadow:-3px 3px 0 #000;font-weight:900;font-size:20px}
  .bigbtn:disabled{filter:grayscale(1) brightness(.8);cursor:not-allowed}
  .logout-area{display:flex;justify-content:flex-end;margin-top:12px}
  .toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#111;color:#fff;border:3px solid #000;border-radius:10px;padding:10px 14px;font-weight:900}

  .table{width:100%;border-collapse:collapse}
  .table th,.table td{border:2px solid #000;padding:6px 8px;text-align:left}
  .table th{background:#f2f2f2}
  .me{background:#fff5d6}

  .weapon{max-width:46%;max-height:72%;filter:drop-shadow(6px 6px 0 #000);image-rendering:pixelated}
  .fallback{width:170px;height:auto;filter:drop-shadow(6px 6px 0 #000)}
</style>
