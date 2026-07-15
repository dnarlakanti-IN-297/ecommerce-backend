"""Unit tests for the core product/cart/checkout API routes."""
import json


# --- health ---------------------------------------------------------------

def test_health(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'healthy'


# --- products ---------------------------------------------------------------

def test_get_products_empty(client):
    resp = client.get('/api/products')
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_get_products_returns_seeded_product(client, sample_product):
    resp = client.get('/api/products')
    assert resp.status_code == 200
    products = resp.get_json()
    assert len(products) == 1
    assert products[0]['id'] == sample_product
    assert products[0]['name'] == "Running Shoes"


def test_get_products_filter_by_category(client, sample_product):
    resp = client.get('/api/products?category=running-shoes')
    assert len(resp.get_json()) == 1

    resp = client.get('/api/products?category=electronics')
    assert resp.get_json() == []


def test_get_products_filter_by_search(client, sample_product):
    resp = client.get('/api/products?search=running')
    assert len(resp.get_json()) == 1

    resp = client.get('/api/products?search=laptop')
    assert resp.get_json() == []


def test_get_product_detail(client, sample_product):
    resp = client.get(f'/api/products/{sample_product}')
    assert resp.status_code == 200
    assert resp.get_json()['name'] == "Running Shoes"


def test_get_product_detail_not_found(client):
    resp = client.get('/api/products/9999')
    assert resp.status_code == 404


# --- cart ---------------------------------------------------------------

def test_add_to_cart(client, sample_product):
    resp = client.post('/api/cart', json={'product_id': sample_product, 'quantity': 2})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert body['cart']['item_count'] == 2


def test_add_to_cart_insufficient_stock(client, sample_product):
    resp = client.post('/api/cart', json={'product_id': sample_product, 'quantity': 999})
    assert resp.status_code == 400
    assert 'error' in resp.get_json()


def test_get_cart_after_add(client, sample_product):
    client.post('/api/cart', json={'product_id': sample_product, 'quantity': 1})
    resp = client.get('/api/cart')
    body = resp.get_json()
    assert body['item_count'] == 1
    assert body['total'] == 89.99


def test_remove_from_cart(client, sample_product):
    client.post('/api/cart', json={'product_id': sample_product, 'quantity': 1})
    resp = client.delete(f'/api/cart/{sample_product}')
    assert resp.status_code == 200

    cart = client.get('/api/cart').get_json()
    assert cart['item_count'] == 0


# --- checkout / orders (integration: exercises cart + order + stock together) ---

import pytest  # noqa: E402


@pytest.mark.integration
def test_checkout_empty_cart_fails(client):
    resp = client.post('/api/checkout', json={'shipping_address': '123 Main St'})
    assert resp.status_code == 400


@pytest.mark.integration
def test_checkout_creates_order_and_decrements_stock(client, sample_product):
    client.post('/api/cart', json={'product_id': sample_product, 'quantity': 2})

    resp = client.post('/api/checkout', json={'shipping_address': '123 Main St'})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert body['status'] == 'confirmed'
    order_id = body['order_id']

    product_resp = client.get(f'/api/products/{sample_product}').get_json()
    assert product_resp['stock'] == 8  # started at 10, bought 2

    order_resp = client.get(f'/api/orders/{order_id}')
    assert order_resp.status_code == 200
    order = order_resp.get_json()
    assert order['total_amount'] == 89.99 * 2
    assert len(order['items']) == 1


@pytest.mark.integration
def test_checkout_clears_cart(client, sample_product):
    client.post('/api/cart', json={'product_id': sample_product, 'quantity': 1})
    client.post('/api/checkout', json={'shipping_address': '123 Main St'})

    cart = client.get('/api/cart').get_json()
    assert cart['item_count'] == 0


def test_get_order_not_found(client):
    resp = client.get('/api/orders/9999')
    assert resp.status_code == 404
