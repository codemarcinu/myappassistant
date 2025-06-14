document.addEventListener('DOMContentLoaded', () => {

    // Stan aplikacji
    const appState = {
        activeTab: 'chat',
        activeAgent: 'budget',
        sidebarOpen: false,
    };

    // Dane agentów (można je dynamicznie ładować)
    const agents = {
        parser: { name: 'Parser Paragonów', icon: '📄' },
        analyst: { name: 'Analityk Wydatków', icon: '📊' },
        budget: { name: 'Doradca Budżetowy', icon: '💰' },
        planner: { name: 'Planista Posiłków', icon: '🍽️' },
        sql: { name: 'Asystent SQL', icon: '🔍' },
    };

    // Elementy DOM
    const elements = {
        sidebar: document.getElementById('sidebar'),
        sidebarToggle: document.getElementById('sidebarToggle'),
        tabBtns: document.querySelectorAll('.tab-btn'),
        tabContents: document.querySelectorAll('.tab-content'),
        agentBtns: document.querySelectorAll('.agent-btn'),
        chatInput: document.getElementById('chatInput'),
        sendBtn: document.getElementById('sendBtn'),
        chatMessages: document.getElementById('chatMessages'),
        pantryProducts: document.getElementById('pantryProducts'),
    };
    
    // --- INICJALIZACJA ---
    function init() {
        // Ustawienie event listenerów
        elements.tabBtns.forEach(btn => btn.addEventListener('click', handleTabClick));
        elements.agentBtns.forEach(btn => btn.addEventListener('click', handleAgentClick));
        elements.sendBtn.addEventListener('click', handleSendMessage);
        elements.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSendMessage();
        });
        elements.sidebarToggle.addEventListener('click', toggleSidebar);
        
        // Delegacja eventów dla dynamicznych elementów w spiżarni
        elements.pantryProducts.addEventListener('click', handlePantryAction);
    }

    // --- HANDLERY EVENTÓW ---

    function handleTabClick(e) {
        const tabId = e.currentTarget.dataset.tab;
        if (tabId === appState.activeTab) return;

        appState.activeTab = tabId;

        // Aktualizacja przycisków
        elements.tabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });

        // Aktualizacja zawartości
        elements.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === `${tabId}Tab`);
        });
    }

    function handleAgentClick(e) {
        const agentId = e.currentTarget.dataset.agent;
        if (agentId === appState.activeAgent) return;

        appState.activeAgent = agentId;

        elements.agentBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.agent === agentId);
        });
        
        addSystemMessage(`Agent przełączony na: ${agents[agentId].name}`);
    }

    function handleSendMessage() {
        const userInput = elements.chatInput.value.trim();
        if (!userInput) return;

        // Dodaj wiadomość użytkownika do UI
        addMessage(userInput, 'user');
        elements.chatInput.value = '';

        // Symulacja odpowiedzi AI
        setTimeout(() => {
            const aiResponse = generateAiResponse(userInput);
            addMessage(aiResponse, 'ai');
        }, 1000);
    }
    
    function handlePantryAction(e) {
        const target = e.target;
        if (target.tagName !== 'BUTTON') return;
        
        const productItem = target.closest('.product-item');
        if (!productItem) return;
        
        if (target.textContent === 'Edytuj') {
            editProduct(productItem);
        } else if (target.textContent === 'Usuń') {
            deleteProduct(productItem);
        }
    }

    function toggleSidebar() {
        appState.sidebarOpen = !appState.sidebarOpen;
        elements.sidebar.classList.toggle('open', appState.sidebarOpen);
    }
    
    // --- FUNKCJE POMOCNICZE ---

    function addMessage(text, type) {
        const messageEl = document.createElement('div');
        messageEl.classList.add('message', `${type}-message`);
        
        const contentEl = document.createElement('div');
        contentEl.classList.add('message-content');
        contentEl.textContent = text;
        
        messageEl.appendChild(contentEl);
        elements.chatMessages.appendChild(messageEl);
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight; // Auto-scroll
    }
    
    function addSystemMessage(text) {
        const messageEl = document.createElement('div');
        messageEl.classList.add('system-message');
        messageEl.textContent = text;
        elements.chatMessages.appendChild(messageEl);
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }

    function generateAiResponse(input) {
        const lowerInput = input.toLowerCase();
        if (lowerInput.includes('dodaj') && lowerInput.includes('mleko')) {
            addProductToPantry({ name: 'Mleko', category: 'Nabiał', expiry: '2025-06-25'});
            return "Dodałem Mleko do Twojej spiżarni. Czy coś jeszcze?";
        }
        if (lowerInput.includes('paragon')) {
            return "Oczywiście, prześlij mi zdjęcie lub plik z paragonem, a ja go przeanalizuję.";
        }
        if (lowerInput.includes('wydatki')) {
            return "W tym miesiącu wydałeś 256.78 zł na jedzenie. Najwięcej na produkty z kategorii 'Mięso'. Czy chcesz szczegółowy raport?";
        }
        return "Przetwarzam Twoje zapytanie... To jest symulowana odpowiedź. W prawdziwej aplikacji tutaj nastąpiłoby wywołanie API do backendu.";
    }
    
    function addProductToPantry({ name, category, expiry }) {
        const productEl = document.createElement('div');
        productEl.classList.add('product-item');
        productEl.innerHTML = `
            <div class="product-info">
                <h4>${name}</h4>
                <p class="product-category">${category}</p>
                <p class="product-expiry">Wygasa: ${expiry}</p>
            </div>
            <div class="product-actions">
                <button class="btn btn--sm btn--outline">Edytuj</button>
                <button class="btn btn--sm btn--outline">Usuń</button>
            </div>
        `;
        elements.pantryProducts.prepend(productEl); // Dodaj na górze listy
    }
    
    function editProduct(productEl) {
        const productName = productEl.querySelector('h4').textContent;
        const newName = prompt(`Wprowadź nową nazwę dla "${productName}":`, productName);
        if (newName && newName.trim() !== "") {
            productEl.querySelector('h4').textContent = newName.trim();
            addSystemMessage(`Zaktualizowano produkt: ${newName.trim()}`);
        }
    }
    
    function deleteProduct(productEl) {
        const productName = productEl.querySelector('h4').textContent;
        if (confirm(`Czy na pewno chcesz usunąć "${productName}"?`)) {
            productEl.style.animation = 'fadeOut 0.3s ease-in-out';
            setTimeout(() => {
                productEl.remove();
                addSystemMessage(`Usunięto produkt: ${productName}`);
            }, 300);
        }
    }

    // Uruchomienie aplikacji
    init();
}); 