from django.contrib.auth import get_user_model

from account.models import Address as AddressModel
from account.users import BaseUserModel
from project2.utils import IsId, getObject
from store.errors import handleError, BadRequest
from store.market import Market
from store.discount import Discount
from store.market_manager import BaseMarketObjectManager
from store.product import Option
from .models import Order as OrderModel, Card as CardModel, AdditionalOption as AdditionalOptionModel, \
    Delivery as DeliveryModel

User = get_user_model()


class Card:
    targetObject = CardModel

    def addNew(self, user, delivery, receive_time, address_to_send_good, discount=None, additional_option=None,
               address_to_send_invoice=None,
               payment_info=None, *args, **kwargs):
        card_structured_data = CardDataStructure(user=user, discount=discount, additional_option=additional_option,
                                                 delivery=delivery,
                                                 receive_time=receive_time,
                                                 address_to_send_good=address_to_send_good,
                                                 address_to_send_invoice=address_to_send_invoice,
                                                 payment_info=payment_info)
        newly_added_card = self.targetObject(**card_structured_data.__dict__)
        newly_added_card.save()
        return newly_added_card

    @handleError(targetObject)
    def addOrderToCard(self, card, orders):
        card_object = getObject(self.targetObject, card)
        if isinstance(orders, list):
            for order in orders:
                if isinstance(order, dict):
                    order_to_add = Order().addNew(**order)
                else:
                    order_to_add = getObject(Order(), order)
                card_object.orders.add(order_to_add)
        else:
            if isinstance(orders, dict):
                order_to_add = Order().addNew(**orders)
            else:
                order_to_add = getObject(Order(), orders)
            card_object.orders.add(order_to_add)
        card_object.save()

    @handleError(targetObject)
    def selectById(self, card_id):
        return self.targetObject.objects.get(pk=card_id)

    @handleError(targetObject)
    def addPaymentInfo(self, card, info):
        card_object = getObject(self.targetObject, card)
        card_object.payment_info = info
        card_object.save()
        return card_object

    @handleError(targetObject)
    def changeStatus(self, card, status):
        if self.isStatusValid(status):
            card_object = getObject(self.targetObject, card)
            card_object.status = status
        else:
            raise ValueError

    @staticmethod
    def isStatusValid(status):
        return True if 0 <= status <= 4 else False

    @handleError(targetObject)
    def selectByUser(self, user, how_many=False):
        user_to_select_with = getObject(User, user)
        if how_many:
            return self.targetObject.objects.filter(user=user_to_select_with)[0:int(how_many)]
        return self.targetObject.objects.filter(user=user_to_select_with)


class Order:
    targetObject = OrderModel

    @handleError(targetObject)
    def selectById(self, order_id):
        return self.targetObject.objects.get(pk=order_id)

    @handleError(targetObject)
    def addNew(self, product, quantity, option=None):
        order_structured_data = OrderDataStructure(product, option, quantity)
        newly_added_order = self.targetObject(**order_structured_data.__dict__)
        newly_added_order.save()
        return newly_added_order


class OrderDataStructure:
    def __init__(self, product, product_option, quantity):
        option = Option()
        market = Market()
        self.product = getObject(market.product, product)
        self.option = getObject(option, product_option)
        self.count = quantity


class CardDataStructure:
    def __init__(self, user, additional_option, delivery, receive_time, address_to_send_good, discount=None,
                 address_to_send_invoice=None,
                 payment_info=None, *args, **kwargs):
        discount_object = Discount()
        additional_option_object = AdditionalOption()
        delivery_object = Delivery()
        if IsId(user):
            try:
                user_id = int(user)
                self.user = BaseUserModel().getUserById(user_id)
            except ValueError:
                token = str(user)
                self.user = BaseUserModel().getUserByToken(token)
        else:
            self.user = user

        if discount:
            try:
                discount_instance = getObject(discount_object, discount)
            except BadRequest:
                discount_instance = discount_object.getByCode(discount)
            if discount_instance.is_valid(self.user):
                self.discount = discount_instance
            else:
                self.discount = None
        else:
            self.discount = None

        self.additional_option = getObject(additional_option_object, additional_option)
        self.delivery = getObject(delivery_object, delivery)
        self.receive_time = receive_time

        if isinstance(address_to_send_good, dict):
            newly_added_address = Address().addNew(user=self.user, **address_to_send_good)
            self.address_to_send_good = newly_added_address
        else:
            self.address_to_send_good = getObject(Address(), address_to_send_good)

        if isinstance(address_to_send_invoice, dict):
            newly_added_address = Address().addNew(user=self.user, **address_to_send_invoice)
            self.address_to_send_invoice = newly_added_address
        else:
            self.address_to_send_invoice = getObject(Address(), address_to_send_invoice)

        self.payment_info = payment_info


class AdditionalOption(BaseMarketObjectManager):
    targetObject = AdditionalOptionModel

    def addNew(self, name, description, option_type, cost):
        newly_added_addtional_option = self.targetObject(name=name, description=description, option_type=option_type,
                                                         cost=cost)
        newly_added_addtional_option.save()
        return newly_added_addtional_option


class Delivery(BaseMarketObjectManager):
    targetObject = DeliveryModel

    def addNew(self, name, price):
        newly_added_delivery = self.targetObject(name=name, price=price)
        newly_added_delivery.save()
        return newly_added_delivery


class Address(BaseMarketObjectManager):
    targetObject = AddressModel

    def addNew(self, user, address, postal_code):
        newly_added_address = self.targetObject(address=address, postal_code=postal_code, user=getObject(User, user))
        newly_added_address.save()
        return newly_added_address
