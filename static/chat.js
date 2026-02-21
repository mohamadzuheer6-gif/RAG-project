let currentChatId = null;


// =============================
// LOAD CHATS ON PAGE LOAD
// =============================
document.addEventListener("DOMContentLoaded", function () {
    loadChats();
});


// =============================
// LOAD ALL CHATS
// =============================
function loadChats() {
    fetch("/get_chats")
        .then(res => res.json())
        .then(data => {

            const chatList = document.getElementById("chatList");
            chatList.innerHTML = "";

            if (data.length === 0) {
                currentChatId = null;
                document.getElementById("messageFormeight").innerHTML = "";
                return;
            }

            data.forEach(chat => {

                const li = document.createElement("li");
                li.setAttribute("data-id", chat.id);
                li.classList.add("chat-item");

                if (chat.id === currentChatId) {
                    li.classList.add("active-chat");
                }

                li.innerHTML = `
                    <span class="chat-title">${chat.title}</span>
                    <div class="chat-actions">
                        <i class="fas fa-ellipsis-v menu-icon"></i>
                        <div class="chat-menu hidden">
                            <div class="menu-item rename">Rename</div>
                            <div class="menu-item delete">Delete</div>
                        </div>
                    </div>
                `;

                // CLICK CHAT
                li.addEventListener("click", function () {

                    if (currentChatId === chat.id) return;

                    currentChatId = chat.id;

                    document.querySelectorAll(".chat-item").forEach(item => {
                        item.classList.remove("active-chat");
                    });

                    li.classList.add("active-chat");

                    loadMessages(chat.id);
                });

                // MENU
                const menuIcon = li.querySelector(".menu-icon");
                const menu = li.querySelector(".chat-menu");

                menuIcon.addEventListener("click", function(e) {
                    e.stopPropagation();
                    closeAllMenus();
                    menu.classList.toggle("hidden");
                });

                // RENAME
                li.querySelector(".rename").addEventListener("click", function(e) {
                    e.stopPropagation();

                    const newTitle = prompt("Rename chat:", chat.title);
                    if (!newTitle || newTitle.trim() === "") return;

                    fetch(`/rename_chat/${chat.id}`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ title: newTitle.trim() })
                    })
                    .then(() => {
                        li.querySelector(".chat-title").textContent = newTitle.trim();
                        menu.classList.add("hidden");
                    });
                });

                // DELETE
                li.querySelector(".delete").addEventListener("click", function(e) {
                    e.stopPropagation();
                    menu.classList.add("hidden");
                    deleteChat(chat.id);
                });

                chatList.appendChild(li);
            });

            // AUTO LOAD FIRST CHAT IF NONE SELECTED
            if (!currentChatId && data.length > 0) {
                currentChatId = data[0].id;
                loadMessages(currentChatId);
            }

        });
}


// =============================
// LOAD MESSAGES
// =============================
function loadMessages(chatId) {

    currentChatId = chatId;

    const container = document.getElementById("messageFormeight");
    container.innerHTML = "";

    fetch(`/get_messages/${chatId}`)
        .then(res => res.json())
        .then(messages => {

            if (!messages || messages.length === 0) {
                return;
            }

            messages.forEach(msg => {
                addMessageToUI(msg.sender, msg.content);
            });

            scrollToBottom();
        })
        .catch(err => {
            console.error("Load messages error:", err);
        });
}


// =============================
// CREATE NEW CHAT
// =============================
document.getElementById("newChatBtn").addEventListener("click", function () {

    fetch("/create_chat", { method: "POST" })
    .then(res => res.json())
    .then(data => {

        currentChatId = data.chat_id;

        loadChats();
        loadMessages(currentChatId);

    });
});


// =============================
// SEND MESSAGE (Streaming)
// =============================
document.getElementById("messageArea").addEventListener("submit", function (e) {
    e.preventDefault();

    if (!currentChatId) {
        alert("Please create a new chat first.");
        return;
    }

    const input = document.getElementById("text");
    const message = input.value.trim();
    if (!message) return;

    input.value = "";

    addMessageToUI("user", message);
    scrollToBottom();

    const thinkingId = showThinking();

    setTimeout(() => {

        const thinkingElement = document.getElementById(thinkingId);
        if (thinkingElement) thinkingElement.remove();

        const botBubble = addMessageToUI("bot", "");
        scrollToBottom();

        const eventSource = new EventSource(
            `/stream_message?chat_id=${currentChatId}&message=${encodeURIComponent(message)}`
        );

        eventSource.onmessage = function (event) {

            if (event.data === "[DONE]") {
                eventSource.close();
                return;
            }

            botBubble.innerHTML += event.data;
            scrollToBottom();
        };

        eventSource.onerror = function () {
            eventSource.close();
            botBubble.innerHTML += "<br><small style='color:red;'>Error occurred.</small>";
        };

    }, 600);
});


// =============================
// UI HELPERS
// =============================
function addMessageToUI(sender, content) {

    const container = document.getElementById("messageFormeight");

    const div = document.createElement("div");
    div.className = sender === "user" ? "user-message" : "bot-message";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.innerHTML = content;

    div.appendChild(bubble);
    container.appendChild(div);

    return bubble;
}

function showThinking() {
    const container = document.getElementById("messageFormeight");
    const id = "thinking_" + Date.now();

    const div = document.createElement("div");
    div.className = "bot-message";
    div.id = id;

    div.innerHTML = `
        <div class="bubble">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    container.appendChild(div);
    scrollToBottom();

    return id;
}

function scrollToBottom() {
    const container = document.getElementById("messageFormeight");
    container.scrollTop = container.scrollHeight;
}

function deleteChat(chatId) {

    if (!confirm("Delete this chat?")) return;

    fetch(`/delete_chat/${chatId}`, { method: "DELETE" })
    .then(() => {

        if (currentChatId == chatId) {
            currentChatId = null;
            document.getElementById("messageFormeight").innerHTML = "";
        }

        loadChats();
    });
}

function closeAllMenus() {
    document.querySelectorAll(".chat-menu").forEach(menu => {
        menu.classList.add("hidden");
    });
}

document.addEventListener("click", closeAllMenus);

document.getElementById("toggleSidebar").addEventListener("click", function() {
    document.querySelector(".sidebar").classList.toggle("collapsed");
});