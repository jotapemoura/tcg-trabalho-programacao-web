// Arquivo: code/static/js/cart.js

// 1. FUNÇÃO PARA OBTER O TOKEN CSRF (SEGURANÇA DO DJANGO)
function getCookie(name) {
    var cookieArr = document.cookie.split(";");
    for(var i = 0; i < cookieArr.length; i++) {
        var cookiePair = cookieArr[i].split("=");
        if(name == cookiePair[0].trim()) {
            return decodeURIComponent(cookiePair[1]);
        }
    }
    return null;
}
var csrftoken = getCookie('csrftoken'); 

// 2. EVENT LISTENERS
var updateBtns = document.getElementsByClassName('update-cart');

// Uso de 'let i' para garantir escopo correto no loop
for (let i = 0; i < updateBtns.length; i++) {
    updateBtns[i].addEventListener('click', function() {
        var cartaId = this.dataset.carta;
        var action = this.dataset.action;
        console.log('Clique - CartaId:', cartaId, 'Action:', action);
        
        // Verifica se o usuário está logado antes de tentar o AJAX
        // (O Django também verifica, mas isso melhora a UX)
        if (user === 'AnonymousUser') {
            alert('Você precisa estar logado para adicionar itens ao carrinho!');
            window.location.href = '/login/'; 
            return;
        }
        
        updateUserOrder(cartaId, action);
    });
}

// 3. FUNÇÃO AJAX (Core da funcionalidade)
function updateUserOrder(cartaId, action) {
    var url = '/update_item/'; // A URL que definimos no urls.py

    fetch(
        url, 
        {
            method: 'POST',
            headers: {
                'Content-Type':'application/json',
                'X-CSRFToken': csrftoken, // Envia o token de segurança
            },
            body:JSON.stringify({'cartaId':cartaId, 'action':action})
        }
    )
    .then(async (response) => {
       if (!response.ok) {
           // Tenta ler o JSON de erro do Django (onde está a mensagem de estoque/UNIQUE)
           let errorData = {};
           try {
               errorData = await response.json();
           } catch (e) {
               // Se não for JSON, usa o status
               throw new Error(`Erro no servidor: ${response.statusText}`);
           }
           // Lança o erro personalizado que virá do servidor
           throw new Error(errorData.error || `Erro de Servidor: ${response.statusText}`);
       }
       return response.json();
    })
    .then((data) => {
        console.log('Resposta do Servidor:', data);
        // Ponto CRÍTICO: Recarrega a página após sucesso para refletir a nova contagem/total
        location.reload(); 
    })
    .catch((error) => {
        console.error('Erro na requisição AJAX:', error.message);
        // Alerta o usuário sobre o erro
        alert('Falha na atualização: ' + error.message); 
        
        // IMPORTANTE: Recarrega a página mesmo em caso de erro, 
        // para garantir que a quantidade exibida reflita o estado real do banco de dados 
        // (por exemplo, se uma operação falhou, a página pode estar desatualizada)
        location.reload(); 
    });
}