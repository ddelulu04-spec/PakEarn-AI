function getTime() {
    return new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function scrollToBottom() {
    const area = document.getElementById('messages');
    area.scrollTop = area.scrollHeight;
}

function addUserMessage(text) {
    const area = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'msg-row user-row';
    div.innerHTML = `
        <div class="bubble user-bubble">
            ${text.replace(/\n/g, '<br>')}
            <span class="msg-time">${getTime()}</span>
        </div>`;
    area.appendChild(div);
    scrollToBottom();
}

function addTyping() {
    const area = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'msg-row ai-row';
    div.id = 'typing-row';
    div.innerHTML = `
        <div class="ai-bubble-avatar">AI</div>
        <div class="typing-bubble">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>`;
    area.appendChild(div);
    scrollToBottom();
}

function removeTyping() {
    const t = document.getElementById('typing-row');
    if (t) t.remove();
}

function addAIMessage(text, searched) {
    const area = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'msg-row ai-row';

    const formatted = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

    div.innerHTML = `
        <div class="ai-bubble-avatar">AI</div>
        <div class="bubble ai-bubble">
            ${searched ? '<span class="searched-tag">Web Search Used</span><br>' : ''}
            ${formatted}
            <span class="msg-time">${getTime()}</span>
        </div>`;
    area.appendChild(div);
    scrollToBottom();
}

function updateProfile(userName) {
    if (userName) {
        fetch('/profile')
            .then(r => r.json())
            .then(data => {
                const box = document.getElementById('profile-box');
                let html = '';
                if (data.name) html += `<p><strong>Name:</strong> ${data.name}</p>`;
                if (data.skills_mentioned) html += `<p style="margin-top:4px"><strong>Skills:</strong> mentioned</p>`;
                if (!html) html = '<p class="profile-empty">Chat to build your profile</p>';
                box.innerHTML = html;
            });
    }
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const btn = document.getElementById('send-btn');
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    input.style.height = 'auto';
    btn.disabled = true;

    addUserMessage(text);
    addTyping();

    // Show search indicator if needed
    const searchWords = ['fiverr','upwork','youtube','earning','freelance','how to start','latest'];
    if (searchWords.some(w => text.toLowerCase().includes(w))) {
        document.getElementById('search-indicator').classList.add('show');
    }

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text})
        });
        const data = await res.json();

        removeTyping();
        document.getElementById('search-indicator').classList.remove('show');
        addAIMessage(data.reply, data.searched);
        updateProfile(data.user_name);

    } catch (err) {
        removeTyping();
        addAIMessage('Sorry, something went wrong. Please try again.');
    }

    btn.disabled = false;
    input.focus();
}

function sendQuick(text) {
    document.getElementById('user-input').value = text;
    sendMessage();
}

function clearChat() {
    fetch('/clear').then(() => {
        document.getElementById('messages').innerHTML = `
        <div class="msg-row ai-row">
            <div class="ai-bubble-avatar">AI</div>
            <div class="bubble ai-bubble">
                <p>New conversation started! What would you like to know about earning online?</p>
                <span class="msg-time">${getTime()}</span>
            </div>
        </div>`;
    });
}