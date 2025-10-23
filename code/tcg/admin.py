from django.contrib import admin
from .models import Endereco
from .models import Categoria
from .models import Carta
from .models import Carrinho
from .models import ItemCarrinho
from .models import Pedido
from .models import ItemPedido
from .models import Pagamento
from .models import Avaliacao

admin.site.register(Endereco)
admin.site.register(Categoria)
admin.site.register(Carta)
admin.site.register(Carrinho)
admin.site.register(ItemCarrinho)
admin.site.register(Pedido)
admin.site.register(ItemPedido)
admin.site.register(Pagamento)
admin.site.register(Avaliacao)

# Register your models here.
