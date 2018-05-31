# MxShop/urls.py
__author__ = 'derek'

from django.urls import path,include,re_path
import xadmin
from django.views.static import serve
from MxShop.settings import MEDIA_ROOT
# from goods.view_base import GoodsListView

from rest_framework.documentation import include_docs_urls
from goods.views import GoodsListViewSet,CategoryViewSet,BannerViewset,IndexCategoryViewset,HotSearchsViewset
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views
from rest_framework_jwt.views import obtain_jwt_token
from users.views import SmsCodeViewset,UserViewset
from user_operation.views import UserFavViewset,LeavingMessageViewset,AddressViewset
from trade.views import ShoppingCartViewset,OrderViewset,AlipayView
from django.views.generic import TemplateView

router = DefaultRouter()

#配置goods的url
router.register(r'goods', GoodsListViewSet,base_name='goods')
# 配置Category的url
router.register(r'categorys', CategoryViewSet, base_name="categorys")
# 配置codes的url
router.register(r'code', SmsCodeViewset, base_name="code")
#配置用户的url
router.register(r'users', UserViewset, base_name="users")
# 配置用户收藏的url
router.register(r'userfavs', UserFavViewset, base_name="userfavs")
# 配置用户留言的url
router.register(r'messages', LeavingMessageViewset, base_name="messages")
# 配置收货地址
router.register(r'address',AddressViewset , base_name="address")
# 配置购物车的url
router.register(r'shopcarts', ShoppingCartViewset, base_name="shopcarts")
# 配置订单的url
router.register(r'orders', OrderViewset, base_name="orders")
# 配置首页轮播图的url
router.register(r'banners', BannerViewset, base_name="banners")
# 热搜词
router.register(r'hotsearchs', HotSearchsViewset, base_name="hotsearchs")
# 首页系列商品展示url
router.register(r'indexgoods', IndexCategoryViewset, base_name="indexgoods")


urlpatterns = [
    path('xadmin/', xadmin.site.urls),
    path('api-auth/',include('rest_framework.urls')),
    path('ueditor/',include('DjangoUeditor.urls' )),
    #文件
    path('media/<path:path>',serve,{'document_root':MEDIA_ROOT}),
    #drf文档，title自定义
    path('docs',include_docs_urls(title='仙剑奇侠传')),
    #商品列表页
    re_path('^', include(router.urls)),
    # token
    path('api-token-auth/', views.obtain_auth_token),
    # jwt的认证接口
    path('login/', obtain_jwt_token ),
    # 首页
    path('index/', TemplateView.as_view(template_name='index.html'),name='index'),
    # 配置支付宝支付相关接口的url
    path('alipay/return/', AlipayView.as_view()),
    # 第三方登录
    path('', include('social_django.urls', namespace='social'))
]
