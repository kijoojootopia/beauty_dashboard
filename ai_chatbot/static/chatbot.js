(() => {
  "use strict";
  const loader = document.getElementById("ai-chatbot-loader");
  if (!loader || document.getElementById("ai-chat-window")) return;
  const authenticated = loader.dataset.authenticated === "true";
  const prefix = "beauport.chat.v1.";
  const storageKey = prefix + loader.dataset.session;
  let saved = {};
  try {
    Object.keys(sessionStorage).filter(key => key.startsWith(prefix) &&
      (key !== storageKey || !authenticated)).forEach(key => sessionStorage.removeItem(key));
    saved = authenticated ? JSON.parse(sessionStorage.getItem(storageKey) || "{}") : {};
  } catch (_) { /* Storage is optional. */ }
  if (!saved || typeof saved !== "object") saved = {};
  let messages = Array.isArray(saved.messages) ? saved.messages.filter(item =>
    item && ["user", "assistant"].includes(item.role) && typeof item.content === "string" &&
    item.content.length > 0 && item.content.length <= (item.role === "user" ? 4000 : 24000)).slice(-40) : [];
  let mode = saved.mode === "open" ? "open" : "minimized";
  let busy = false;
  let controller = null;
  let generation = 0;
  let rect = saved.rect;
  const panel = document.createElement("section");
  panel.id = "ai-chat-window";
  panel.className = "ai-chat-window";
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-modal", "false");
  panel.setAttribute("aria-labelledby", "ai-chat-title");
  panel.innerHTML = `
    <header class="ai-chat-header">
      <div class="ai-chat-drag" tabindex="0" role="button" aria-label="챗봇 창 이동: 방향키 또는 드래그">
        <strong id="ai-chat-title">BEAUPORT AI</strong><small>수출 준비를 함께하는 도우미</small>
      </div>
      <div class="ai-chat-actions">
        <button type="button" data-action="reset" title="새 대화" aria-label="새 대화">↻</button>
        <button type="button" data-action="minimize" title="최소화" aria-label="챗봇 최소화">−</button>
        <button type="button" data-action="close" title="닫기" aria-label="챗봇 닫기">×</button>
      </div>
    </header>
    <p class="ai-chat-info">등록된 대시보드 자료를 참고합니다. 질문과 조회 자료는 AI 답변 생성에 사용됩니다.</p>
    <div class="ai-chat-messages" role="log" aria-label="챗봇 대화" aria-live="polite" tabindex="0"></div>
    <p class="ai-chat-status" role="status"></p>
    <form class="ai-chat-compose">
      <label for="ai-chat-input">궁금한 내용을 입력하세요</label>
      <textarea id="ai-chat-input" maxlength="4000" placeholder="미국 수출 비중처럼 등록 자료를 물어보세요"></textarea>
      <div class="ai-chat-compose-row"><small>Enter 전송 · Shift+Enter 줄바꿈</small><button class="ai-chat-send" type="submit">보내기</button></div>
      <a class="ai-chat-login" hidden>로그인하고 대화하기</a>
    </form>
    <button class="ai-chat-resize" type="button" title="드래그 또는 방향키로 크기 조절" aria-label="챗봇 크기 조절: 방향키 또는 드래그">◢</button>`;
  const restore = document.createElement("button");
  restore.type = "button";
  restore.setAttribute("aria-controls", "ai-chat-window");
  restore.className = "ai-chat-restore";
  restore.textContent = "AI 챗봇";
  document.body.append(panel, restore);
  const log = panel.querySelector(".ai-chat-messages");
  const status = panel.querySelector(".ai-chat-status");
  const input = panel.querySelector("textarea");
  const form = panel.querySelector("form");
  const send = panel.querySelector(".ai-chat-send");
  const drag = panel.querySelector(".ai-chat-drag");
  const resize = panel.querySelector(".ai-chat-resize");
  const login = panel.querySelector(".ai-chat-login");
  login.href = loader.dataset.login;
  login.hidden = authenticated;
  input.disabled = !authenticated;
  send.disabled = !authenticated;
  if (typeof saved.draft === "string" && authenticated) input.value = saved.draft.slice(0, 4000);

  function persist() {
    if (!authenticated) return;
    try { sessionStorage.setItem(storageKey, JSON.stringify({mode, rect, messages, draft: input.value})); }
    catch (_) { /* Continue with in-memory state when storage is unavailable. */ }
  }
  function fit(candidate) {
    const viewport = window.visualViewport;
    const vw = viewport ? viewport.width : window.innerWidth;
    const vh = viewport ? viewport.height : window.innerHeight;
    const ox = viewport ? viewport.offsetLeft : 0;
    const oy = viewport ? viewport.offsetTop : 0;
    const maxW = Math.max(1, vw - 16);
    const maxH = Math.max(1, vh - 16);
    const finite = (value, fallback) => Number.isFinite(value) ? value : fallback;
    const width = Math.min(maxW, Math.max(Math.min(320, maxW), finite(candidate?.width, 400)));
    const height = Math.min(maxH, Math.max(Math.min(360, maxH), finite(candidate?.height, 560)));
    const x = Math.min(ox + vw - width - 8, Math.max(ox + 8, finite(candidate?.x, ox + vw - width - 24)));
    const y = Math.min(oy + vh - height - 8, Math.max(oy + 8, finite(candidate?.y, oy + vh - height - 24)));
    rect = {x, y, width, height};
    panel.style.left = x + "px";
    panel.style.top = y + "px";
    panel.style.width = width + "px";
    panel.style.height = height + "px";
    panel.style.right = "auto";
    panel.style.bottom = "auto";
  }
  function setMode(next, focus = true) {
    mode = next;
    panel.hidden = next !== "open";
    restore.hidden = next === "open";
    restore.setAttribute("aria-expanded", String(next === "open"));
    fit(rect);
    persist();
    if (focus) {
      if (next === "open") (authenticated ? input : login).focus({preventScroll: true});
      else restore.focus({preventScroll: true});
    }
  }
  function appendMessage(role, content) {
    const bubble = document.createElement("div");
    bubble.className = "ai-chat-message";
    bubble.dataset.role = role;
    const label = document.createElement("span");
    label.className = "ai-chat-message-label";
    label.textContent = role === "user" ? "나" : "BEAUPORT AI";
    bubble.append(label, document.createTextNode(content));
    log.append(bubble);
    log.scrollTop = log.scrollHeight;
  }
  function render() {
    log.replaceChildren();
    if (!messages.length) appendMessage("assistant", authenticated
      ? "안녕하세요! 화장품 수출 통계와 등록 자료, 뷰포트 사용 방법을 물어보세요."
      : "로그인 후 AI 도우미와 대화할 수 있어요.");
    messages.forEach(item => appendMessage(item.role, item.content));
  }
  function historyForRequest() {
    const history = [];
    let length = 0;
    for (const item of messages.slice(-20).reverse()) {
      if (length + item.content.length > 48000) break;
      history.unshift(item);
      length += item.content.length;
    }
    return history;
  }
  restore.addEventListener("click", () => setMode("open"));
  panel.querySelector('[data-action="close"]').addEventListener("click", () => setMode("minimized"));
  panel.querySelector('[data-action="minimize"]').addEventListener("click", () => setMode("minimized"));
  panel.querySelector('[data-action="reset"]').addEventListener("click", () => {
    if ((messages.length || input.value || busy) && !window.confirm("현재 대화를 지우고 새 대화를 시작할까요?")) return;
    generation += 1;
    controller?.abort();
    controller = null;
    busy = false;
    messages = [];
    input.value = "";
    status.textContent = "";
    send.disabled = !authenticated;
    render();
    persist();
    if (authenticated) input.focus();
  });
  panel.addEventListener("keydown", event => {
    if (event.key === "Escape" && !event.isComposing) { event.preventDefault(); setMode("minimized"); }
  });
  input.addEventListener("input", persist);
  input.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing && event.keyCode !== 229) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  function readableMessage(value, fallback) {
    if (typeof value !== "string" || !value.trim()) return fallback;
    // Older server responses or decoding failures must not leak mojibake into the UI.
    if (/\?{2,}|\uFFFD/.test(value)) return fallback;
    return value;
  }

  form.addEventListener("submit", async event => {
    event.preventDefault();
    const question = input.value.trim();
    if (busy || !authenticated || !question) return;
    const history = historyForRequest();
    const currentGeneration = ++generation;
    const requestController = new AbortController();
    controller = requestController;
    busy = true;
    send.disabled = true;
    status.textContent = "답변을 작성하고 있어요…";
    messages.push({role: "user", content: question});
    messages = messages.slice(-40);
    input.value = "";
    render();
    persist();
    const timeout = window.setTimeout(() => requestController.abort(), 150000);
    try {
      const response = await fetch(loader.dataset.api, {
        method: "POST", credentials: "same-origin", signal: requestController.signal,
        headers: {"Content-Type": "application/json", "X-CSRF-Token": loader.dataset.csrf},
        body: JSON.stringify({message: question, history})
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        if (response.status === 401) throw new Error("로그인이 만료되었습니다. 새로고침 후 로그인해 주세요.");
        throw new Error(readableMessage(data.message, "답변을 받지 못했습니다. 잠시 후 다시 시도해 주세요."));
      }
      if (typeof data.reply !== "string" || !data.reply.trim()) throw new Error("답변이 비어 있습니다. 다시 시도해 주세요.");
      if (currentGeneration !== generation) return;
      messages.push({role: "assistant", content: data.reply});
      messages = messages.slice(-40);
      appendMessage("assistant", data.reply);
      status.textContent = "";
    } catch (error) {
      if (currentGeneration !== generation) return;
      messages.pop();
      if (!input.value) input.value = question;
      render();
      status.textContent = error.name === "AbortError" ? "응답 시간이 초과되었습니다. 다시 보내 주세요."
        : error instanceof TypeError ? "서버에 연결할 수 없습니다. 연결을 확인하고 다시 보내 주세요." : readableMessage(error.message, "응답을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      window.clearTimeout(timeout);
      if (currentGeneration === generation) {
        busy = false;
        controller = null;
        send.disabled = !authenticated;
        persist();
      }
    }
  });
  function makeHandle(handle, resizing) {
    let start = null;
    handle.addEventListener("pointerdown", event => {
      if (event.button !== 0) return;
      event.preventDefault();
      handle.focus({preventScroll: true});
      start = {px: event.clientX, py: event.clientY, ...rect};
      handle.setPointerCapture(event.pointerId);
    });
    handle.addEventListener("pointermove", event => {
      if (!start) return;
      const dx = event.clientX - start.px, dy = event.clientY - start.py;
      fit(resizing ? {...start, width: start.width + dx, height: start.height + dy}
        : {...start, x: start.x + dx, y: start.y + dy});
    });
    const end = () => { start = null; persist(); };
    handle.addEventListener("pointerup", end);
    handle.addEventListener("pointercancel", end);
    handle.addEventListener("lostpointercapture", end);
    handle.addEventListener("keydown", event => {
      const delta = {ArrowLeft: [-16, 0], ArrowRight: [16, 0], ArrowUp: [0, -16], ArrowDown: [0, 16]}[event.key];
      if (!delta) return;
      event.preventDefault();
      fit(resizing ? {...rect, width: rect.width + delta[0], height: rect.height + delta[1]}
        : {...rect, x: rect.x + delta[0], y: rect.y + delta[1]});
      persist();
    });
  }
  makeHandle(drag, false);
  makeHandle(resize, true);
  const onResize = () => { fit(rect); persist(); };
  window.addEventListener("resize", onResize);
  window.visualViewport?.addEventListener("resize", onResize);
  window.visualViewport?.addEventListener("scroll", onResize);
  window.addEventListener("pagehide", () => { persist(); controller?.abort(); });
  window.addEventListener("pageshow", event => { if (event.persisted) window.location.reload(); });
  // Logout clears this tab's retained messages before navigation.
  document.querySelectorAll('form[action]').forEach(element => {
    if (new URL(element.action, location.href).pathname.endsWith("/logout")) {
      element.addEventListener("submit", () => {
        generation += 1;
        controller?.abort();
        messages = [];
        input.value = "";
        try { sessionStorage.removeItem(storageKey); } catch (_) {}
      });
    }
  });
  render();
  setMode(mode, false);
})();
