from django.db import models
from django.db import models
from django.contrib.auth.models import User


# ============================================================
# MODELOS PRINCIPAIS
# ============================================================

class Endereco(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enderecos")
    rua = models.CharField(max_length=255)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    cep = models.CharField(max_length=20)
    complemento = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.rua}, {self.cidade} - {self.estado}"


class Categoria(models.Model):
    TIPOS_CATEGORIA = [
        ('POKEMON', 'Pokémon'),
        ('MAGIC', 'Magic: The Gathering'),
        ('YUGIOH', 'Yu-Gi-Oh'),
    ]

    nome = models.CharField(
        max_length=20,
        choices=TIPOS_CATEGORIA,
        unique=True
    )

    def __str__(self):
        return self.get_nome_display()

class Carta(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name="cartas")
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.PositiveIntegerField()
    condicao = models.CharField(max_length=50, choices=[
        ("novo", "Novo"),
        ("usado", "Usado"),
    ])
    imagem_url = models.URLField(blank=True, null=True)
    tipo = models.CharField(max_length=50, choices=[
        ("carta", "Carta"),
    ])
    edicao = models.CharField(max_length=100, blank=True, null=True)
    raridade = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.nome} - {self.condicao})"






# ============================================================
# CARRINHO DE COMPRAS
# ============================================================

class Carrinho(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="carrinho")
    data_criacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[
        ("aberto", "Aberto"),
        ("finalizado", "Finalizado"),
    ], default="aberto")

    def __str__(self):
        return f"Carrinho de {self.usuario.username}"


class ItemCarrinho(models.Model):
    carrinho = models.ForeignKey(Carrinho, on_delete=models.CASCADE, related_name="itens")
    carta = models.ForeignKey(Carta, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.carta.nome} x {self.quantidade}"


# ============================================================
# PEDIDOS E PAGAMENTOS
# ============================================================

class Pedido(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pedidos")
    endereco = models.ForeignKey(Endereco, on_delete=models.PROTECT)
    data_pedido = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[
        ("pendente", "Pendente"),
        ("pago", "Pago"),
        ("enviado", "Enviado"),
        ("entregue", "Entregue"),
        ("cancelado", "Cancelado"),
    ], default="pendente")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    carta = models.ForeignKey(Carta, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.carta.nome} x {self.quantidade}"


class Pagamento(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name="pagamento")
    metodo = models.CharField(max_length=50, choices=[
        ("pix", "PIX"),
        ("cartao", "Cartão de Crédito"),
        ("boleto", "Boleto"),
    ])
    status_pagamento = models.CharField(max_length=50, choices=[
        ("pendente", "Pendente"),
        ("aprovado", "Aprovado"),
        ("recusado", "Recusado"),
    ], default="pendente")
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_pagamento = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Pagamento de {self.pedido}"


# ============================================================
# AVALIAÇÕES
# ============================================================

class Avaliacao(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="avaliacoes")
    carta = models.ForeignKey(Carta, on_delete=models.CASCADE, related_name="avaliacoes")
    nota = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comentario = models.TextField(blank=True)
    data_avaliacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.carta.nome} ({self.nota}/5)"

# Create your models here.
