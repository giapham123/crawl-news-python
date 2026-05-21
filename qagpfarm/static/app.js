const form = document.querySelector("#ask-form");
const input = document.querySelector("#question");
const sendButton = document.querySelector("#send-button");
const clearButton = document.querySelector("#clear-chat");
const messages = document.querySelector("#messages");

const STORAGE_KEY = "gpfarm-chat-history";
let history = loadHistory();

function loadHistory() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

function saveHistory() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(-12)));
}

function appendMessage(role, content, extraClass = "") {
  const message = document.createElement("div");
  message.className = `message ${role} ${extraClass}`.trim();
  message.textContent = content;
  messages.appendChild(message);
  messages.scrollTop = messages.scrollHeight;
  return message;
}

function renderMessages() {
  messages.replaceChildren();
  if (history.length === 0) {
    appendMessage("assistant", "Chào bạn, GP Farm có thể hỗ trợ mình về sản phẩm, giá, tồn kho hoặc gợi ý quà tặng nhé!");
    return;
  }
  history.forEach((item) => appendMessage(item.role, item.content));
}

async function ask(question, previousHistory, onChunk) {
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history: previousHistory }),
  });

  if (!response.ok) {
    let message = "Không gửi được câu hỏi";
    try {
      const data = await response.json();
      message = data.error || message;
    } catch {
      message = await response.text();
    }
    throw new Error(message);
  }

  const contentType = response.headers.get("Content-Type") || "";
  if (contentType.includes("application/json")) {
    const data = await response.json();
    return data.answer;
  }

  if (!response.body) {
    return response.text();
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let answer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    const chunk = decoder.decode(value, { stream: true });
    answer += chunk;
    onChunk(answer);
  }

  const tail = decoder.decode();
  if (tail) {
    answer += tail;
    onChunk(answer);
  }
  return answer;
}

function setBusy(isBusy) {
  input.disabled = isBusy;
  sendButton.disabled = isBusy;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) {
    return;
  }

  const previousHistory = history.slice();
  input.value = "";
  history.push({ role: "user", content: question });
  appendMessage("user", question);
  const pending = appendMessage("assistant", "Đang trả lời...", "pending");
  setBusy(true);

  try {
    const answer = await ask(question, previousHistory, (partialAnswer) => {
      pending.classList.remove("pending");
      pending.textContent = partialAnswer;
      messages.scrollTop = messages.scrollHeight;
    });
    pending.classList.remove("pending");
    pending.textContent = answer;
    history.push({ role: "assistant", content: answer });
    saveHistory();
  } catch (error) {
    pending.classList.remove("pending");
    pending.textContent = error.message;
  } finally {
    setBusy(false);
    input.focus();
  }
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

clearButton.addEventListener("click", () => {
  history = [];
  saveHistory();
  renderMessages();
  input.focus();
});

renderMessages();
