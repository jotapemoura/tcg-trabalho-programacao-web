from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.utils import timezone
from .models import *
import json
import re
from django.db import transaction, IntegrityError # Importação de IntegrityError e transaction
from django.utils import timezone # Importação de timezone
from decimal import Decimal # Importação de Decimal

def store(request):
    cartas = Carta.objects.all().order_by('nome')
    context = {'cartas': cartas}
    return render(request, 'store.html', context)

def detail(request, carta_id):
    carta = get_object_or_404(Carta, pk=carta_id)
    context = {'carta': carta}
    return render(request, 'detail.html', context)

@login_required(login_url='tcg:login') # Exige login para ver o carrinho
def cart(request):
    # Encontra o carrinho do usuário logado ou cria um se não existir
    carrinho, created = Carrinho.objects.get_or_create(usuario=request.user, status='aberto')
    itens = carrinho.itens.all()
    
    # Calcula o total
    total_carrinho = sum([item.subtotal() for item in itens])
    
    context = {
        'itens': itens, 
        'carrinho': carrinho, 
        'total_carrinho': total_carrinho,
        'taxa_entrega': Decimal(15.00)
    }
    return render(request, 'cart.html', context)

@login_required(login_url='tcg:login')
def checkout(request):
    carrinho, created = Carrinho.objects.get_or_create(usuario=request.user, status='aberto')
    itens = carrinho.itens.all()
    total_carrinho = sum([item.subtotal() for item in itens])
    
    # Busca endereços reais do usuário
    enderecos = Endereco.objects.filter(usuario=request.user)
    
    context = {
        'itens': itens,
        'valor_final': total_carrinho + Decimal(15.00), 
        'enderecos': enderecos
    }
    return render(request, 'checkout.html', context)

@login_required
@transaction.atomic()
def updateItem(request):
    data = json.loads(request.body)
    carta_id = data.get('cartaId')
    action = data.get('action')
    
    if not carta_id or not action:
        return JsonResponse({'error': 'Dados inválidos.'}, status=400)

    try:
        carta = Carta.objects.get(pk=carta_id)
        carrinho, created = Carrinho.objects.get_or_create(usuario=request.user, status='aberto')
        
        item, created = ItemCarrinho.objects.get_or_create(carrinho=carrinho, carta=carta, defaults={'preco_unitario': carta.preco})

        # Lógica de atualização (adicionar, remover, deletar)
        if action == 'add':
            if carta.estoque < item.quantidade + 1:
                return JsonResponse({'error': f'Estoque insuficiente. Apenas {carta.estoque} unidades disponíveis.'}, status=400)
            item.quantidade += 1
            item.save()
        
        elif action == 'remove':
            item.quantidade -= 1
            item.save()

        elif action == 'delete':
            item.delete()

        # Garante que o item não exista se a quantidade for 0
        if item.quantidade <= 0:
            item.delete()

        return JsonResponse('Item atualizado', safe=False)
    
    except Carta.DoesNotExist:
        return JsonResponse({'error': 'Carta não encontrada.'}, status=404)
    except Exception as e:
        # Captura qualquer outro erro e retorna um JSON com status 500
        return JsonResponse({'error': f'Erro no servidor ao processar item: {str(e)}'}, status=500)
    
@login_required(login_url='tcg:login')
@transaction.atomic()
def addItem(request):
    """View que processa a adição de quantidade específica (POST do detail/store)"""
    if request.method == 'POST':
        try:
            # 1. Captura e valida os dados do formulário POST
            carta_id = request.POST.get('cartaId')
            quantity_str = request.POST.get('quantity', '1')
            quantity = int(quantity_str)
            
            if quantity < 1:
                messages.error(request, "A quantidade deve ser pelo menos 1.")
                return redirect(request.META.get('HTTP_REFERER', 'tcg:store')) # Volta para a página anterior

            carta = get_object_or_404(Carta, pk=carta_id)
            carrinho, created = Carrinho.objects.get_or_create(usuario=request.user, status='aberto')
            
            # 2. Obtém ou cria o item no carrinho
            item, created = ItemCarrinho.objects.get_or_create(
                carrinho=carrinho, 
                carta=carta, 
                defaults={'quantidade': 0, 'preco_unitario': carta.preco} # Inicializa com 0
            )

            # 3. Validação de estoque: calcula a nova quantidade total
            nova_quantidade = item.quantidade + quantity

            if nova_quantidade > carta.estoque:
                messages.error(request, f"Estoque insuficiente. Máximo que pode ser adicionado: {carta.estoque - item.quantidade} unidades.")
                # Usa redirect para o detalhe ou store, dependendo da origem
                return redirect(request.META.get('HTTP_REFERER', 'tcg:store')) 

            # 4. Atualiza e salva o item
            item.quantidade = nova_quantidade
            item.preco_unitario = carta.preco 
            item.save()
            
            messages.success(request, f"{quantity}x {carta.nome} adicionado(s) ao carrinho!")
            
            # Redireciona de volta para a página de onde veio
            return redirect(request.META.get('HTTP_REFERER', 'tcg:store'))

        except ValueError:
            messages.error(request, "Quantidade inválida.")
        except Carta.DoesNotExist:
             messages.error(request, "Carta não encontrada.")
        except Exception as e:
            messages.error(request, f"Erro ao adicionar item: {e}")
            print(f"Erro inesperado no addItem: {e}")
            
    # Redireciona para o store em caso de falha ou GET
    return redirect('tcg:store')

@login_required(login_url='tcg:login')
@transaction.atomic # Garante que todas as operações sejam feitas ou nenhuma
def processOrder(request):
    if request.method != 'POST':
        messages.error(request, 'Método de requisição inválido.')
        return redirect('tcg:checkout')
    
    try:
        # 1. Recupera o Carrinho aberto e o Endereço selecionado
        carrinho = Carrinho.objects.get(usuario=request.user, status='aberto')
        
        if not carrinho.itens.exists():
            messages.error(request, 'Seu carrinho está vazio. Não é possível finalizar a compra.')
            return redirect('tcg:store')
            
        endereco_id = request.POST.get('endereco_selecionado')
        if not endereco_id:
            messages.error(request, 'Endereço de entrega não selecionado.')
            return redirect('tcg:checkout')

        # Garante que o endereço selecionado pertence ao usuário
        endereco_obj = get_object_or_404(Endereco, pk=endereco_id, usuario=request.user)
        
        # O valor total já vem da view checkout, mas recalculamos por segurança
        taxa_entrega = Decimal('15.00')
        total_carrinho = sum(item.subtotal() for item in carrinho.itens.all())
        valor_final = total_carrinho + taxa_entrega
        
        # 2. Cria o Pedido (Pedido é a cópia final do Carrinho)
        # CORREÇÃO: Usamos 'endereco' (assumindo o nome do campo no seu modelo Pedido)
        # e 'valor_total' (assumindo o nome do campo do total).
        pedido = Pedido.objects.create(
            usuario=request.user,
            data_pedido=timezone.now(), 
            endereco=endereco_obj,     # <--- Mudei de 'endereco_entrega' para 'endereco'
            valor_total=valor_final,   # <--- Nome do campo total do pedido
            status='processando' 
        )
        
        # 3. Processa cada ItemCarrinho e move para ItemPedido
        itens_carrinho = list(carrinho.itens.all())
        for item_carrinho in itens_carrinho:
            # a) Cria o ItemPedido
            ItemPedido.objects.create(
                pedido=pedido,
                carta=item_carrinho.carta,
                quantidade=item_carrinho.quantidade,
                preco_unitario=item_carrinho.preco_unitario,
            )
            
            # b) Atualiza o estoque da Carta (CRÍTICO)
            carta = item_carrinho.carta
            if carta.estoque < item_carrinho.quantidade:
                # Se houver problema de estoque, a transação será desfeita pelo IntegrityError
                raise IntegrityError(f"Estoque insuficiente para a carta {carta.nome}.")

            carta.estoque -= item_carrinho.quantidade
            carta.save()
            
            # c) Deleta o ItemCarrinho (limpa o carrinho)
            item_carrinho.delete()
            
        # 4. Marca o Carrinho como concluído (para não ser reutilizado)
        carrinho.status = 'concluido'
        carrinho.save()
        
        messages.success(request, f'Pedido #{pedido.pk} realizado com sucesso! Você será redirecionado para a página de pedidos.')
        return redirect('tcg:orders')
    
    except Carrinho.DoesNotExist:
        messages.error(request, 'Carrinho não encontrado. Tente adicionar itens novamente.')
        return redirect('tcg:store')
    except Endereco.DoesNotExist:
        messages.error(request, 'Endereço de entrega inválido. Por favor, selecione um endereço válido.')
        return redirect('tcg:checkout')
    except IntegrityError as e:
        messages.error(request, f'Falha no estoque ou integridade de dados. Tente novamente.')
        return redirect('tcg:checkout')
    except Exception as e:
        messages.error(request, f'Ocorreu um erro inesperado ao finalizar o pedido. Erro: {e}')
        return redirect('tcg:checkout')

def user_login(request):
    if request.method == 'POST':
        # Lógica de login
        nome_usuario = request.POST.get('username')
        senha_usuario = request.POST.get('password')
        
        user = authenticate(request, username=nome_usuario, password=senha_usuario)
        
        if user is not None:
            login(request, user)
            return redirect('tcg:store') # Redireciona para a loja
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
            return render(request, 'login.html', {})
            
    return render(request, 'login.html', {})

def user_register(request):
    if request.method == 'POST':
        # Lógica de cadastro
        email = request.POST.get('email')
        senha = request.POST.get('password')
        senha2 = request.POST.get('password2')

        if senha != senha2:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'register.html', {})
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Este e-mail já está cadastrado.')
            return render(request, 'register.html', {})
        
        # Cria o usuário (username=email por simplicidade)
        try:
            user = User.objects.create_user(username=email, email=email, password=senha)
            user.save()
            messages.success(request, 'Conta criada com sucesso! Faça o login.')
            return redirect('tcg:login')
        except Exception as e:
            messages.error(request, f'Erro ao criar conta: {e}')
            return render(request, 'register.html', {})

    return render(request, 'register.html', {})

def user_logout(request):
    logout(request)
    return redirect('tcg:store')

@login_required(login_url='tcg:login')
def user_profile(request):
    if request.method == 'POST':
        # Simplesmente atualiza o e-mail ou nome, se fornecido
        primeiro_nome = request.POST.get('first_name')
        ultimo_nome = request.POST.get('last_name')
        email = request.POST.get('email')

        request.user.first_name = primeiro_nome
        request.user.last_name = ultimo_nome
        
        # Garante que o e-mail não esteja sendo usado por outro usuário (exceto o próprio)
        if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
             messages.error(request, 'Este e-mail já está sendo usado por outra conta.')
        else:
            request.user.email = email
            request.user.username = email # Mantemos o username = email para login
            request.user.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            
        return redirect('tcg:profile')

    # GET: Apenas exibe a página
    # Busca endereços (se existirem) para o perfil
    enderecos = Endereco.objects.filter(usuario=request.user)
    
    context = {
        'enderecos': enderecos
    }
    return render(request, 'profile.html', context)

@login_required(login_url='tcg:login')
def user_orders(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-data_pedido')
    
    context = {
        'pedidos': pedidos
    }
    return render(request, 'orders.html', context)

@login_required(login_url='tcg:login')
def order_detail(request, pedido_id):
    # Garante que o pedido exista e pertença ao usuário logado
    pedido = get_object_or_404(
        Pedido.objects.select_related('endereco').prefetch_related('itempedido_set__carta'),
        pk=pedido_id, 
        usuario=request.user
    )
    
    context = {
        'pedido': pedido,
        # Você pode calcular totais se precisar de algo além do pedido.valor_total
        # total_itens = sum(item.subtotal() for item in pedido.itempedido_set.all()) 
    }
    
    return render(request, 'order_detail.html', context)

@login_required(login_url='tcg:login')
def add_address(request):
    if request.method == 'POST':
        # 1. Captura os dados do formulário
        rua = request.POST.get('rua')
        cidade = request.POST.get('cidade')
        estado = request.POST.get('estado')
        cep = request.POST.get('cep')
        complemento = request.POST.get('complemento', '')

        # 2. Validação simples de campos obrigatórios
        if not all([rua, cidade, estado, cep]):
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios (Rua, Cidade, Estado, CEP).')
            return redirect('tcg:profile')

        # 3. NOVA VALIDAÇÃO: Formato do CEP
        # Remove caracteres não numéricos para verificar apenas os dígitos
        cep_limpo = re.sub(r'[^0-9]', '', cep)
        
        if len(cep_limpo) != 8:
            messages.error(request, 'Formato de CEP inválido. O CEP deve ter 8 dígitos.')
            return redirect('tcg:profile')

        # Opcional: Salva o CEP padronizado (sem o hífen, para consistência no banco)
        cep = cep_limpo 
        
        # 4. Cria o objeto Endereco e salva no banco
        Endereco.objects.create(
            usuario=request.user,
            rua=rua,
            cidade=cidade,
            # Garante que o estado tenha no máximo 2 letras e seja maiúsculo
            estado=estado.upper()[:2], 
            cep=cep,
            complemento=complemento,
        )
        
        messages.success(request, 'Novo endereço cadastrado com sucesso!')
        # 5. Redireciona de volta para o perfil
        return redirect('tcg:profile')

    return redirect('tcg:profile')

@login_required(login_url='tcg:login')
def edit_address_page(request, address_id):
    """Nova view para exibir o formulário de edição de endereço (GET)"""
    # Garante que o endereço exista e pertença ao usuário logado.
    endereco = get_object_or_404(Endereco, pk=address_id, usuario=request.user)
    
    context = {
        'endereco': endereco
    }
    return render(request, 'edit_address.html', context)


@login_required(login_url='tcg:login')
def save_edit_address(request, address_id):
    """View que processa a submissão do formulário de edição (POST)"""
    # Tenta obter o endereço OU retorna 404.
    endereco = get_object_or_404(Endereco, pk=address_id, usuario=request.user)
    
    if request.method == 'POST':
        # 1. Captura e valida os dados (igual ao add_address)
        rua = request.POST.get('rua')
        cidade = request.POST.get('cidade')
        estado = request.POST.get('estado')
        cep = request.POST.get('cep')
        complemento = request.POST.get('complemento', '')
        
        # Validação simples
        if not all([rua, cidade, estado, cep]):
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
            # Redireciona para a página de edição para que o usuário veja o erro
            return redirect('tcg:edit_address_page', address_id=address_id) 

        # Validação do CEP
        cep_limpo = re.sub(r'[^0-9]', '', cep)
        if len(cep_limpo) != 8:
            messages.error(request, 'Formato de CEP inválido. O CEP deve ter 8 dígitos.')
            return redirect('tcg:edit_address_page', address_id=address_id)
        
        # 2. Atualiza o objeto Endereco existente
        endereco.rua = rua
        endereco.cidade = cidade
        endereco.estado = estado.upper()[:2]
        endereco.cep = cep_limpo
        endereco.complemento = complemento
        endereco.save()
        
        messages.success(request, 'Endereço atualizado com sucesso!')
        # Redireciona de volta para o perfil principal após o sucesso
        return redirect('tcg:profile')

    # Se alguém tentar acessar com GET (ou outro método), redireciona
    return redirect('tcg:profile')

# 7. VIEW DE TESTE
def teste(request):
    return render(request, 'teste.html', {})