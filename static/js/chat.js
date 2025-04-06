let chats = [];
let currentChatId = null;

function createNewChat() {
    const chatId = Date.now();
    const chatItem = {
        id: chatId,
        title: 'New Chat',
        messages: []
    };
    chats.push(chatItem);
    currentChatId = chatId;
    
    // Add to sidebar
    const chatList = document.getElementById('chatList');
    const chatElement = document.createElement('a');
    chatElement.href = '#';
    chatElement.className = 'nav-item';
    chatElement.setAttribute('data-chat-id', chatId);
    chatElement.innerHTML = `
        <span class="material-symbols-rounded">chat</span>
        ${chatItem.title}
    `;
    chatElement.onclick = (e) => {
        e.preventDefault();
        switchChat(chatId);
    };
    
    chatList.insertBefore(chatElement, chatList.firstChild);
    
    // Clear chat box
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML = '';
    
    // Add initial bot message
    const botDiv = document.createElement('div');
    botDiv.classList.add('message', 'bot-message');
    botDiv.innerHTML = `
        <div class="avatar">🤖</div>
        <p>Hey! I'm Cosmo. What's on your mind today?</p>
    `;
    chatBox.appendChild(botDiv);
}

function switchChat(chatId) {
    currentChatId = chatId;
    const chat = chats.find(c => c.id === chatId);
    if (!chat) return;
    
    // Update chat display
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML = '';
    chat.messages.forEach(msg => {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', msg.type === 'user' ? 'user-message' : 'bot-message');
        msgDiv.innerHTML = `<p>${msg.content}</p>`;
        chatBox.appendChild(msgDiv);
    });
    
    // Update active state in sidebar
    document.querySelectorAll('.chat-list .nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`.chat-list [data-chat-id="${chatId}"]`)?.classList.add('active');
}

// Initialize first chat
window.addEventListener('load', () => {
    if (chats.length === 0) {
        createNewChat();
    }
});