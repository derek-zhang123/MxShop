# trade/views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsOwnerOrReadOnly
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.authentication import SessionAuthentication
from .serializers import ShopCartSerializer,ShopCartDetailSerializer,OrderDetailSerializer,OrderGoodsSerialzier,OrderSerializer
from .models import ShoppingCart,OrderGoods,OrderInfo
from rest_framework import mixins
from django.shortcuts import render, redirect

from datetime import datetime
from utils.alipay import AliPay
from rest_framework.views import APIView
from MxShop.settings import ali_pub_key_path, private_key_path
from rest_framework.response import Response


class ShoppingCartViewset(viewsets.ModelViewSet):
    """
    购物车功能
    list:
        获取购物车详情
    create：
        加入购物车
    delete：
        删除购物记录
    """
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = ShopCartSerializer
    #商品的id
    lookup_field = "goods_id"

    def get_serializer_class(self):
        if self.action == 'list':
            return ShopCartDetailSerializer
        else:
            return ShopCartSerializer

    #获取购物车列表
    def get_queryset(self):
        return ShoppingCart.objects.filter(user=self.request.user)

    # 库存数-1
    def perform_create(self, serializer):
        shop_cart = serializer.save()
        goods = shop_cart.goods
        goods.goods_num -= shop_cart.nums
        goods.save()

    # 库存数+1
    def perform_destroy(self, instance):
        goods = instance.goods
        goods.goods_num += instance.nums
        goods.save()
        instance.delete()

    # 更新库存,修改可能是增加页可能是减少
    def perform_update(self, serializer):
        #首先获取修改之前的库存数量
        existed_record = ShoppingCart.objects.get(id=serializer.instance.id)
        existed_nums = existed_record.nums
        # 先保存之前的数据existed_nums
        saved_record = serializer.save()
        #变化的数量
        nums = saved_record.nums-existed_nums
        goods = saved_record.goods
        goods.goods_num -= nums
        goods.save()


class OrderViewset(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin,
                   viewsets.GenericViewSet):
    """
    订单管理
    list:
        获取个人订单
    delete:
        删除订单
    create：
        新增订单
    """
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = OrderSerializer
    #动态配置serializer
    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderDetailSerializer
        return OrderSerializer
    #获取订单列表
    def get_queryset(self):
        return OrderInfo.objects.filter(user=self.request.user)

    #在订单提交保存之前还需要多两步步骤，所以这里自定义perform_create方法
    #1.将购物车中的商品保存到OrderGoods中
    #2.情况购物车
    def perform_create(self, serializer):
        order = serializer.save()
        # 获取购物车所有商品
        shop_carts = ShoppingCart.objects.filter(user=self.request.user)
        for shop_cart in shop_carts:
            order_goods = OrderGoods()
            order_goods.goods = shop_cart.goods
            order_goods.goods_num = shop_cart.nums
            order_goods.order = order
            order_goods.save()
            #清空购物车
            shop_cart.delete()
        return order



class AlipayView(APIView):
    def get(self, request):
        """
        处理支付宝的return_url返回
        """
        processed_dict = {}
        # 1. 获取GET中参数
        for key, value in request.GET.items():
            processed_dict[key] = value
        # 2. 取出sign
        sign = processed_dict.pop("sign", None)

        # 3. 生成ALipay对象
        alipay = AliPay(
            appid="2016091500517456",
            app_notify_url="http://47.93.198.159:8000/alipay/return/",
            app_private_key_path=private_key_path,
            alipay_public_key_path=ali_pub_key_path,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            debug=True,  # 默认False,
            return_url="http://47.93.198.159:8000/alipay/return/"
        )

        verify_re = alipay.verify(processed_dict, sign)

        # 这里可以不做操作。因为不管发不发return url。notify url都会修改订单状态。
        if verify_re is True:
            order_sn = processed_dict.get('out_trade_no', None)
            trade_no = processed_dict.get('trade_no', None)
            trade_status = processed_dict.get('trade_status', None)

            existed_orders = OrderInfo.objects.filter(order_sn=order_sn)
            for existed_order in existed_orders:
                existed_order.pay_status = trade_status
                existed_order.trade_no = trade_no
                existed_order.pay_time = datetime.now()
                existed_order.save()

            response = redirect("/index/#/app/home/member/order")
            return response

        else:
            response = redirect("index")
            return response

    def post(self, request):
        """
        处理支付宝的notify_url
        """
        #存放post里面所有的数据
        processed_dict = {}
        #取出post里面的数据
        for key, value in request.POST.items():
            processed_dict[key] = value
        #把signpop掉，文档有说明
        sign = processed_dict.pop("sign", None)

        #生成一个Alipay对象
        alipay = AliPay(
            appid="2016091500517456",
            app_notify_url="http://47.93.198.159:8000/alipay/return/",
            app_private_key_path=private_key_path,
            alipay_public_key_path=ali_pub_key_path,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            debug=True,  # 默认False,
            return_url="http://47.93.198.159:8000/alipay/return/"
        )

        #进行验证
        verify_re = alipay.verify(processed_dict, sign)

        # 如果验签成功
        if verify_re is True:
            #商户网站唯一订单号
            order_sn = processed_dict.get('out_trade_no', None)
            #支付宝系统交易流水号
            trade_no = processed_dict.get('trade_no', None)
            #交易状态
            trade_status = processed_dict.get('trade_status', None)

            # 查询数据库中订单记录
            existed_orders = OrderInfo.objects.filter(order_sn=order_sn)
            for existed_order in existed_orders:
                # 订单商品项
                order_goods = existed_order.goods.all()
                # 商品销量增加订单中数值
                for order_good in order_goods:
                    goods = order_good.goods
                    goods.sold_num += order_good.goods_num
                    goods.save()

                # 更新订单状态
                existed_order.pay_status = trade_status
                existed_order.trade_no = trade_no
                existed_order.pay_time = datetime.now()
                existed_order.save()
            #需要返回一个'success'给支付宝，如果不返回，支付宝会一直发送订单支付成功的消息
            return Response("success")








