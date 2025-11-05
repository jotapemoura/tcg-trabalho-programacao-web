from .models import Carrinho # Importa o modelo Carrinho

def cart_item_count_processor(request):
    """
    Este processador de contexto injeta a variável 'cart_item_count' 
    (contagem de itens no carrinho) em todas as views que usam base.html.
    
    Ele resolve o erro 'AttributeError: get_cart_items'.
    """
    # 1. Inicializa a contagem como 0 para garantir que a variável exista
    cart_item_count = 0
    
    # 2. Verifica se o usuário está autenticado
    if request.user.is_authenticated:
        try:
            # 3. Tenta encontrar o carrinho ativo ('aberto') do usuário logado
            carrinho = Carrinho.objects.get(usuario=request.user, status='aberto')
            
            # 4. CORREÇÃO: Usa o método .count() na relação reversa 'itens' (ForeignKey do ItemCarrinho)
            # Esta linha substitui a incorreta 'carrinho.get_cart_items()'
            cart_item_count = carrinho.itens.count() 
            
        except Carrinho.DoesNotExist:
            # Se o usuário não tem um carrinho 'aberto', a contagem permanece 0
            pass 
            
    # 5. Retorna o dicionário de contexto.
    return {'cart_item_count': cart_item_count}