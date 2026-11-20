// Frontend for Resume Chatbot - SSE streaming

const API_BASE = "";
const STORAGE_KEY = "chatbot_session_id";

const chatArea = document.getElementById("chatArea");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const inputForm = document.getElementById("inputForm");
const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");
const uploadStatus = document.getElementById("uploadStatus");
const clearBtn = document.getElementById("clearBtn");
const sessionIdEl = document.getElementById("sessionId");

let sessionId = localStorage.getItem(STORAGE_KEY) || "default";
let isStreaming = false;
let eventSource = null;

function updateSessionDisplay() {
    sessionIdEl.innerHTML = `Session: <code>${sessionId}</code>`;
}

function addMessage(role, content, streaming = false) {
    const wrapper = document.createElement("div");
    wrapper.className = `message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = role === "user" ? "You" : "AI";

    const bubble = document.createElement("div");
    bubble.className = "bubble" + (streaming ? " streaming" : "");
    bubble.textContent = content;

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
    chatArea.appendChild(wrapper);
    scrollToBottom();

    return bubble;
}

function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
}

function setInputEnabled(enabled) {
    messageInput.disabled = !enabled;
    sendBtn.disabled = !enabled || messageInput.value.trim() === "";
    uploadBtn.disabled = !enabled;
}

async function sendMessage(text) {
    if (isStreaming) return;

    // Add user message
    addMessage("user", text);
    messageInput.value = "";
    messageInput.style.height = "auto";
    setInputEnabled(false);
    isStreaming = true;

    // Create assistant message bubble for streaming
    const assistantBubble = addMessage("assistant", "", true);

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text, session_id: sessionId })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.content) {
                            assistantBubble.textContent += data.content;
                            assistantBubble.classList.add("streaming");
                            scrollToBottom();
                        }
                        if (data.done) {
                            assistantBubble.classList.remove("streaming");
                        }
                    } catch (e) {
                        console.warn("Parse error:", e, line);
                    }
                }
            }
        }
    } catch (err) {
        console.error(err);
        assistantBubble.textContent = "Error: " + err.message;
        assistantBubble.classList.remove("streaming");
    } finally {
        isStreaming = false;
        setInputEnabled(true);
        messageInput.focus();
    }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", sessionId);

    uploadStatus.textContent = "Uploading...";
    uploadStatus.className = "upload-status";
    uploadBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) throw new Error("Upload failed");
        const data = await response.json();

        uploadStatus.textContent = `Uploaded: ${data.filename} (${data.chars} chars)`;
        uploadStatus.className = "upload-status success";
    } catch (err) {
        uploadStatus.textContent = "Error: " + err.message;
        uploadStatus.className = "upload-status error";
    } finally {
        uploadBtn.disabled = false;
        fileInput.value = "";
    }
}

async function clearSession() {
    try {
        await fetch(`${API_BASE}/session/${sessionId}`, { method: "DELETE" });
    } catch (e) {
        console.warn("Clear session failed:", e);
    }

    // Clear UI
    chatArea.innerHTML = "";
    addMessage("assistant", "Hi. I know Arkaprabha's resume. Ask me about his experience, skills, education, or paste a job description to see what matches.");
    sessionContext = "";
}

function autoResizeTextarea() {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 180) + "px";
}

// Event listeners
inputForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = messageInput.value.trim();
    if (text && !isStreaming) {
        sendMessage(text);
    }
});

messageInput.addEventListener("input", () => {
    autoResizeTextarea();
    sendBtn.disabled = messageInput.value.trim() === "" || isStreaming;
});

messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        const text = messageInput.value.trim();
        if (text && !isStreaming) {
            sendMessage(text);
        }
    }
});

uploadBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
    if (e.target.files[0]) {
        uploadFile(e.target.files[0]);
    }
});

clearBtn.addEventListener("click", clearSession);

// Init
updateSessionDisplay();
messageInput.focus();