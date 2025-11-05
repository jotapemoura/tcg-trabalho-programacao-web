from django.urls import path
from . import views

app_name = 'tcg' 

urlpatterns = [
    # E-commerce e Navegação
    path('', views.store, name='store'), 
    path('carta/<int:carta_id>/', views.detail, name='detail'), 
    path('carrinho/', views.cart, name='cart'), 
    path('checkout/', views.checkout, name='checkout'), 
    path('pedidos/', views.user_orders, name='orders'),
    
    # FINALIZAR COMPRA
    path('process_order/', views.processOrder, name='process_order'),
    
    # AJAX (Funcionalidade do Carrinho)
    path('update_item/', views.updateItem, name='update_item'),
    path('add_item/', views.addItem, name='add_item'),
    
    # Autenticação e Usuário
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('perfil/', views.user_profile, name='profile'),
    
    # Endereços
    path('adicionar_endereco/', views.add_address, name='add_address'),
    path('editar_endereco/<int:address_id>/', views.edit_address_page, name='edit_address_page'), 
    path('salvar_edicao_endereco/<int:address_id>/', views.save_edit_address, name='save_edit_address'),

    # Teste
    path('teste/', views.teste, name='teste'),
]