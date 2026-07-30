const API_URL = "/api/v1";

const SUPABASE_URL = "https://jfivjloqhtmwuidrgveu.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpmaXZqbG9xaHRtd3VpZHJndmV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU0MzEyMjUsImV4cCI6MjEwMTAwNzIyNX0.7nOWy2KDtPCddA3NmB8LeldrKrZmewczXf9oUdt-ac4";

let supabaseClient;
try {
    if (!window.supabase) {
        throw new Error("SDK do Supabase não carregou. Verifique sua internet, proxy ou bloqueador de anúncios (AdBlock).");
    }
    supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
} catch (err) {
    alert("ERRO CRÍTICO NO FRONTEND: " + err.message);
    document.addEventListener("DOMContentLoaded", () => {
        document.body.innerHTML = `<div style="padding:40px; color:#e74c3c; font-family:sans-serif; text-align:center;">
            <h2>Erro de Inicialização</h2>
            <p>${err.message}</p>
        </div>`;
    });
}
let session = null;

// DOM Elements - Chat
const chatInput = document.getElementById("chat-input");
const temaInput = document.getElementById("tema-input");
const sendBtn = document.getElementById("send-btn");
const attachBtn = document.getElementById("attach-btn");
const fileUpload = document.getElementById("file-upload");
const messagesContainer = document.getElementById("messages-container");
const imagePreviewContainer = document.getElementById("image-preview-container");
const imagePreview = document.getElementById("image-preview");
const removeImageBtn = document.getElementById("remove-image");
const historyList = document.getElementById("history-list");
const displayUserName = document.getElementById("display-user-name");

// DOM Elements - Mobile Menu
const menuToggle = document.getElementById("menu-toggle");
const sidebar = document.querySelector(".sidebar");

if (menuToggle) {
    menuToggle.addEventListener("click", () => {
        sidebar.classList.toggle("open");
    });
}

// DOM Elements - Auth
const authOverlay = document.getElementById("auth-overlay");
const emailInput = document.getElementById("auth-email");
const passInput = document.getElementById("auth-pass");
const authError = document.getElementById("auth-error");
const btnAuthSubmit = document.getElementById("btn-auth-submit");
const toggleAuthMode = document.getElementById("toggle-auth-mode");
const authTitle = document.getElementById("auth-title");
const authSubtitle = document.getElementById("auth-subtitle");
const btnLogout = document.getElementById("btn-logout");

let authMode = "login"; // 'login' ou 'register'
let selectedFile = null;

/* ==========================================================================
   Autenticação e Sessão
   ========================================================================== */

// Verifica estado da sessão ao carregar a página
async function initAuth() {
    const { data: { session: currentSession } } = await supabaseClient.auth.getSession();
    handleSessionUpdate(currentSession);

    // Escuta mudanças (login, logout)
    supabaseClient.auth.onAuthStateChange((_event, newSession) => {
        handleSessionUpdate(newSession);
    });
}

function handleSessionUpdate(newSession) {
    session = newSession;
    if (session) {
        authOverlay.classList.add("hidden");
        const email = session.user.email;
        displayUserName.textContent = email.split("@")[0];
        loadHistory();
    } else {
        authOverlay.classList.remove("hidden");
    }
}

function showAuthError(msg) {
    authError.textContent = msg;
    authError.classList.remove("hidden");
}

function hideAuthError() {
    authError.classList.add("hidden");
}

toggleAuthMode.addEventListener("click", (e) => {
    e.preventDefault();
    hideAuthError();
    if (authMode === "login") {
        authMode = "register";
        authTitle.textContent = "Criar Conta";
        authSubtitle.textContent = "Cadastre-se para corrigir suas redações";
        btnAuthSubmit.textContent = "Cadastrar";
        toggleAuthMode.textContent = "Já tem uma conta? Faça login";
    } else {
        authMode = "login";
        authTitle.textContent = "Bem-vindo ao Reda1000";
        authSubtitle.textContent = "Faça login para corrigir suas redações";
        btnAuthSubmit.textContent = "Entrar";
        toggleAuthMode.textContent = "Não tem conta? Cadastre-se";
    }
});

btnAuthSubmit.addEventListener("click", async (e) => {
    e.preventDefault();
    hideAuthError();
    
    authError.style.background = "rgba(231, 76, 60, 0.1)";
    authError.style.color = "#e74c3c";
    
    const email = emailInput.value.trim();
    const password = passInput.value.trim();
    
    if (!email) {
        showAuthError("Por favor, preencha o seu e-mail.");
        return;
    }
    
    if (!email.includes("@") || !email.includes(".")) {
        showAuthError("Por favor, digite um e-mail válido (ex: aluno@gmail.com).");
        return;
    }
    
    if (!password || password.length < 6) {
        showAuthError("A senha precisa ter no mínimo 6 caracteres.");
        return;
    }
    
    try {
        if (authMode === "login") {
            btnAuthSubmit.textContent = "Entrando...";
            btnAuthSubmit.disabled = true;
            
            const { data, error } = await supabaseClient.auth.signInWithPassword({ email, password });
            
            btnAuthSubmit.textContent = "Entrar";
            btnAuthSubmit.disabled = false;
            
            if (error) {
                if (error.message.includes("Email not confirmed")) {
                    showAuthError("E-mail não confirmado no Supabase.");
                } else if (error.message.includes("Invalid login credentials")) {
                    showAuthError("E-mail ou senha incorretos (ou a conta ainda não foi criada).");
                } else {
                    showAuthError("Erro no login. Verifique suas credenciais.");
                }
            }
        } else {
            btnAuthSubmit.textContent = "Criando...";
            btnAuthSubmit.disabled = true;
            
            const { data, error } = await supabaseClient.auth.signUp({ email, password });
            
            btnAuthSubmit.textContent = "Cadastrar";
            btnAuthSubmit.disabled = false;
            
            if (error) {
                showAuthError("Erro no cadastro. Tente novamente.");
            } else {
                if (data.session) {
                    authOverlay.classList.add("hidden");
                } else {
                    showAuthError("Conta criada! Confirme seu e-mail se necessário.");
                    authError.style.background = "rgba(46, 204, 113, 0.1)";
                    authError.style.color = "#27ae60";
                }
            }
        }
    } catch (err) {
        btnAuthSubmit.textContent = authMode === "login" ? "Entrar" : "Cadastrar";
        btnAuthSubmit.disabled = false;
        showAuthError("Falha de conexão com o banco de dados.");
    }
});

if (btnLogout) {
    btnLogout.addEventListener("click", async () => {
        await supabaseClient.auth.signOut();
        session = null;
        historyList.innerHTML = `<div style="font-size: 13px; color: var(--text-muted); text-align: center; padding: 12px;">Deslogado</div>`;
        messagesContainer.innerHTML = "";
        appendWelcomeMessage();
        handleSessionUpdate(null);
    });
}

/* ==========================================================================
   Histórico
   ========================================================================== */

async function loadHistory() {
    try {
        const headers = {};
        if (session && session.access_token) {
            headers["Authorization"] = `Bearer ${session.access_token}`;
        }

        const response = await fetch(`${API_URL}/historico`, { headers });
        
        if (response.status === 401) {
            // Token expirado ou invalido
            await supabaseClient.auth.signOut();
            handleSessionUpdate(null);
            return;
        }

        if (!response.ok) throw new Error("Erro ao carregar histórico");
        
        const historico = await response.json();
        
        historyList.innerHTML = "";
        
        if (historico.length === 0) {
            historyList.innerHTML = `<div style="font-size: 13px; color: var(--text-muted); text-align: center; padding: 12px;">Nenhuma redação ainda.</div>`;
            appendWelcomeMessage();
            return;
        }

        historico.forEach(item => {
            const li = document.createElement("li");
            li.className = "history-item";
            li.innerHTML = `
                <i class="ph ph-check-circle" style="color: var(--accent-gold);"></i>
                <div style="display: flex; flex-direction: column; overflow: hidden;">
                    <span class="history-text" style="font-weight: 500; font-size: 13px;">${item.tema}</span>
                    <span style="font-size: 11px; color: var(--text-muted);">Nota: ${item.nota_final} pontos</span>
                </div>
            `;
            
            li.addEventListener("click", () => {
                document.querySelectorAll(".history-item").forEach(i => i.classList.remove("active"));
                li.classList.add("active");
                messagesContainer.innerHTML = "";
                appendSystemMessage(item.resultado_json, null);
            });
            
            historyList.appendChild(li);
        });

    } catch (error) {
        historyList.innerHTML = `<div style="font-size: 13px; color: #e74c3c; text-align: center; padding: 12px;">Falha ao carregar.</div>`;
    }
}

/* ==========================================================================
   Interações do Chat (Input / Anexos / Botoes)
   ========================================================================== */

chatInput.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight) + "px";
    if (this.value.trim() === "" && !selectedFile) {
        sendBtn.disabled = true;
    } else {
        sendBtn.disabled = false;
    }
});

attachBtn.addEventListener("click", () => {
    fileUpload.click();
});

fileUpload.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreviewContainer.classList.remove("hidden");
            sendBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }
});

removeImageBtn.addEventListener("click", () => {
    selectedFile = null;
    fileUpload.value = "";
    imagePreview.src = "";
    imagePreviewContainer.classList.add("hidden");
    if (chatInput.value.trim() === "") sendBtn.disabled = true;
});

const newChatBtn = document.querySelector(".new-chat");
if (newChatBtn) {
    newChatBtn.addEventListener("click", () => {
        document.querySelectorAll(".history-item").forEach(i => i.classList.remove("active"));
        messagesContainer.innerHTML = "";
        appendWelcomeMessage();
        temaInput.value = "";
        chatInput.value = "";
        if(removeImageBtn) removeImageBtn.click();
    });
}

const exportBtn = document.querySelector(".header-actions .btn-ghost");
if (exportBtn) {
    exportBtn.addEventListener("click", () => {
        window.print();
    });
}

/* ==========================================================================
   Envio de Redação para API
   ========================================================================== */

sendBtn.addEventListener("click", handleSend);
chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
});

async function handleSend() {
    const text = chatInput.value.trim();
    const tema = temaInput.value.trim() || "Geral";
    
    if (!text && !selectedFile) return;

    appendUserMessage(text, selectedFile ? imagePreview.src : null);
    
    chatInput.value = "";
    chatInput.style.height = "auto";
    const fileToSend = selectedFile;
    if(removeImageBtn) removeImageBtn.click();
    sendBtn.disabled = true;

    const loadingId = appendLoading();

    try {
        let response;
        const headers = {};
        
        if (session && session.access_token) {
            headers["Authorization"] = `Bearer ${session.access_token}`;
        }
        
        if (fileToSend) {
            const formData = new FormData();
            formData.append("arquivo", fileToSend);
            formData.append("tema", tema);
            
            response = await fetch(`${API_URL}/corrigir/foto`, {
                method: "POST",
                headers: headers,
                body: formData
            });
        } else {
            headers["Content-Type"] = "application/json";
            response = await fetch(`${API_URL}/corrigir/texto`, {
                method: "POST",
                headers: headers,
                body: JSON.stringify({ texto_redacao: text, tema: tema })
            });
        }

        removeMessage(loadingId);
        
        if (response.status === 401) {
            await supabaseClient.auth.signOut();
            handleSessionUpdate(null);
            return;
        }

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Erro desconhecido na API.");
        }

        const data = await response.json();
        
        const correcao = fileToSend ? data.correcao : data;
        const textoReconhecido = fileToSend ? data.texto_reconhecido : null;
        
        appendSystemMessage(correcao, textoReconhecido);
        loadHistory();

    } catch (error) {
        removeMessage(loadingId);
        appendErrorMessage(error.message);
    }
}

/* ==========================================================================
   Funções de Renderização (UI)
   ========================================================================== */

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendUserMessage(text, imgSrc) {
    const div = document.createElement("div");
    div.className = "message user-message";
    
    let content = "";
    if (imgSrc) content += `<img src="${imgSrc}" style="max-width: 200px; border-radius: 8px; margin-bottom: 8px;"><br>`;
    if (text) content += `<p>${text.replace(/\n/g, '<br>')}</p>`;

    div.innerHTML = `
        <div class="message-content" style="background: var(--bg-bubble-user); padding: 16px; border-radius: 12px; margin-left: auto;">
            <div class="message-text">${content}</div>
        </div>
    `;
    messagesContainer.appendChild(div);
    scrollToBottom();
}

function appendWelcomeMessage() {
    if (document.querySelector('.welcome-card')) return;
    
    const div = document.createElement("div");
    div.className = "welcome-card";
    div.innerHTML = `
        <img src="VlwRe-removebg-preview.png" alt="Mascote Reda1000" class="welcome-mascot">
        <h3>Olá! Eu sou o Reda1000.</h3>
        <p>Envie sua redação do ENEM digitada ou tire uma foto da folha de papel. Eu farei a correção precisa baseada nas 5 competências oficiais do INEP.</p>
    `;
    messagesContainer.appendChild(div);
    scrollToBottom();
}

function appendLoading() {
    const id = "loading-" + Date.now();
    const div = document.createElement("div");
    div.className = "message system-message";
    div.id = id;
    div.innerHTML = `
        <div class="message-avatar sys-avatar"><img src="VlwRe-removebg-preview.png" class="mascot-avatar" alt="Reda1000"></div>
        <div class="message-content">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
            <span style="font-size: 12px; color: var(--text-muted); margin-left: 8px;">Lendo matriz do INEP e avaliando...</span>
        </div>
    `;
    messagesContainer.appendChild(div);
    scrollToBottom();
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function appendErrorMessage(errorMsg) {
    const div = document.createElement("div");
    div.className = "message system-message";
    div.innerHTML = `
        <div class="message-avatar sys-avatar" style="background: #e74c3c;"><i class="ph ph-warning"></i></div>
        <div class="message-content">
            <div class="message-text" style="color: #e74c3c;">
                <p><strong>Oops! Algo deu errado:</strong></p>
                <p>${errorMsg}</p>
                <p style="font-size: 12px; margin-top:8px;">Se o erro persistir, fale com o suporte.</p>
            </div>
        </div>
    `;
    messagesContainer.appendChild(div);
    scrollToBottom();
}

function appendSystemMessage(correcao, textoExtraido = null) {
    const div = document.createElement("div");
    div.className = "message system-message";
    
    let extraidoHtml = "";
    if (textoExtraido) {
        extraidoHtml = `
            <div style="background: var(--bg-input); padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; color: var(--text-sec);">
                <strong>Texto reconhecido pelo OCR:</strong><br>
                ${textoExtraido.substring(0, 150)}...
            </div>
        `;
    }

    const comps = ["C1", "C2", "C3", "C4", "C5"];
    let compsHtml = "";
    
    if (correcao.condicao_anulacao && correcao.condicao_anulacao !== "Nenhuma") {
        compsHtml = `
            <div style="color: #e74c3c; font-weight: 500; margin-bottom: 12px;">
                ⚠️ Condição de Anulação: ${correcao.condicao_anulacao}
            </div>
        `;
    }
    
    if (correcao.notas) {
        comps.forEach((c, idx) => {
            const compData = correcao.notas[c];
            if (!compData) return;
            
            const nota = compData.nota !== undefined ? compData.nota : 0;
            
            let desc = "";
            if (compData.pontos_fortes && compData.pontos_fortes.length > 0) {
                desc += `<div style="margin-top: 4px;"><strong>Pontos Fortes:</strong> ${compData.pontos_fortes.join("<br>")}</div>`;
            }
            if (compData.pontos_melhorar && compData.pontos_melhorar.length > 0) {
                desc += `<div style="margin-top: 4px;"><strong>A Melhorar:</strong> ${compData.pontos_melhorar.join("<br>")}</div>`;
            }
            if (compData.reescrita_sugerida) {
                desc += `<div style="margin-top: 6px; font-style: italic; color: var(--accent-gold); background: rgba(221, 162, 93, 0.1); padding: 8px; border-radius: 6px;">Sugestão: ${compData.reescrita_sugerida}</div>`;
            }
            
            compsHtml += `
                <div class="comp-item">
                    <div class="comp-score">${nota}</div>
                    <div class="comp-desc">
                        <strong>Competência ${idx + 1}</strong>
                        ${desc}
                    </div>
                </div>
            `;
        });
    }

    const feedbackGeral = correcao.analise_geral || correcao.feedback_geral || "";
    const prioridade = correcao.prioridade_estudo ? `<p style="color: var(--accent-gold); font-weight: 500;">Dica: ${correcao.prioridade_estudo}</p>` : "";

    div.innerHTML = `
        <div class="message-avatar sys-avatar"><img src="VlwRe-removebg-preview.png" class="mascot-avatar" alt="Reda1000"></div>
        <div class="message-content">
            <div class="message-text">
                ${extraidoHtml}
                <p>${feedbackGeral}</p>
                ${prioridade}
                
                <div class="score-card">
                    <div class="score-header">
                        <div>
                            <div class="score-title">Correção Oficial</div>
                            <div class="score-label">Modelo ENEM</div>
                        </div>
                        <div class="score-total-box">
                            <div class="score-title" style="font-size: 32px;">${correcao.nota_total}</div>
                            <div class="score-label">Pontos</div>
                        </div>
                    </div>
                    <div class="comp-list">
                        ${compsHtml}
                    </div>
                </div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(div);
    scrollToBottom();
}

// Inicia
initAuth();
