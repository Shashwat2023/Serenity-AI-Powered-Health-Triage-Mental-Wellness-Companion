class ChatInterface {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.userInput = document.getElementById('userInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.conversationHistory = [];
        
        this.initializeEventListeners();
        this.setInitialTime();
    }

    initializeEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.userInput.addEventListener('input', () => {
            this.userInput.style.height = 'auto';
            this.userInput.style.height = Math.min(this.userInput.scrollHeight, 120) + 'px';
        });

        // Auto-focus input
        setTimeout(() => {
            this.userInput.focus();
        }, 500);
    }

    setInitialTime() {
        const initialTime = document.getElementById('initialTime');
        initialTime.textContent = this.getCurrentTime();
    }

    getCurrentTime() {
        return new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false 
        });
    }

    async sendMessage() {
        const message = this.userInput.value.trim();
        
        if (!message) return;

        // Check for exit commands
        if (message.toLowerCase() === 'quit' || message.toLowerCase() === 'exit' || message.toLowerCase() === 'bye') {
            this.addMessage('Goodbye! Thank you for sharing with me. Remember to be kind to yourself today. 🌸', 'bot', 'calm');
            this.disableInput();
            return;
        }

        // Add user message to chat
        this.addMessage(message, 'user');
        this.userInput.value = '';
        this.userInput.style.height = 'auto';
        
        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await this.getBotResponse(message);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add bot response
            this.addMessage(response.response, 'bot', response.mood);
            
            // Add suggestion if available
            if (response.suggestion) {
                this.addSuggestion(response.suggestion);
            }

            // Scroll to bottom
            this.scrollToBottom();

        } catch (error) {
            console.error('Error:', error);
            this.hideTypingIndicator();
            this.addMessage("I'm here to listen. Could you tell me more about how you're feeling?", 'bot', 'neutral');
        }
    }

    async getBotResponse(message) {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                history: this.conversationHistory
            })
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        
        // Update conversation history
        this.conversationHistory.push({
            user: message,
            bot: data.response
        });

        // Keep only last 8 exchanges
        if (this.conversationHistory.length > 8) {
            this.conversationHistory = this.conversationHistory.slice(-8);
        }

        return data;
    }

    addMessage(content, sender, mood = 'neutral') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message message-loading`;
        
        if (mood && sender === 'bot') {
            messageDiv.setAttribute('data-mood', mood);
        }
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = this.getCurrentTime();

        // Handle line breaks in message content
        const paragraphs = content.split('\n\n');
        paragraphs.forEach((paragraph, index) => {
            const p = document.createElement('p');
            p.textContent = paragraph;
            if (index > 0) {
                p.style.marginTop = '8px';
            }
            messageContent.appendChild(p);
        });

        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addSuggestion(suggestion) {
        const suggestionDiv = document.createElement('div');
        suggestionDiv.className = 'message bot-message message-loading';
        
        const suggestionContent = document.createElement('div');
        suggestionContent.className = 'message-content suggestion-box';
        suggestionContent.textContent = suggestion;
        
        const suggestionTime = document.createElement('div');
        suggestionTime.className = 'message-time';
        suggestionTime.textContent = this.getCurrentTime();

        suggestionDiv.appendChild(suggestionContent);
        suggestionDiv.appendChild(suggestionTime);
        
        this.chatMessages.appendChild(suggestionDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        this.typingIndicator.classList.add('visible');
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.classList.remove('visible');
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    disableInput() {
        this.userInput.disabled = true;
        this.sendButton.disabled = true;
        this.userInput.placeholder = 'Conversation ended - Refresh page to start new chat';
    }
}

// Initialize chat when page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});

// Add some interactive effects
document.addEventListener('click', function(e) {
    // Add ripple effect to buttons
    if (e.target.matches('#sendButton') || e.target.closest('#sendButton')) {
        const button = e.target.matches('#sendButton') ? e.target : e.target.closest('#sendButton');
        const ripple = document.createElement('span');
        const diameter = Math.max(button.clientWidth, button.clientHeight);
        const radius = diameter / 2;
        
        ripple.style.width = ripple.style.height = diameter + 'px';
        ripple.style.left = (e.clientX - button.getBoundingClientRect().left - radius) + 'px';
        ripple.style.top = (e.clientY - button.getBoundingClientRect().top - radius) + 'px';
        ripple.classList.add('ripple');
        
        const existingRipple = button.querySelector('.ripple');
        if (existingRipple) {
            existingRipple.remove();
        }
        
        button.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }
});

// Add CSS for ripple effect
const rippleStyles = `
.ripple {
    position: absolute;
    border-radius: 50%;
    background-color: rgba(255, 255, 255, 0.6);
    transform: scale(0);
    animation: ripple-animation 0.6s linear;
}

@keyframes ripple-animation {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

#sendButton {
    position: relative;
    overflow: hidden;
}
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = rippleStyles;
document.head.appendChild(styleSheet);
