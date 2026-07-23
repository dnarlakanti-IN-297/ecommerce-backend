"""Bulk-generated test cases (~500) so Smart Tests' subset selection has
a large enough suite to show a meaningful efficiency gain. Uses
parametrize rather than 500 hand-written functions. Temporary - remove
after the demo.
"""
import pytest


# --- cheap repeated checks (all pass) ---------------------------------------

@pytest.mark.parametrize("i", range(150))
def test_health_repeated(client, i):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'healthy'


@pytest.mark.parametrize("i", range(150))
def test_product_detail_roundtrip(client, sample_product, i):
    resp = client.get(f'/api/products/{sample_product}')
    assert resp.status_code == 200
    assert resp.get_json()['name'] == "Running Shoes"


@pytest.mark.parametrize("i", range(150))
def test_add_to_cart_valid(client, sample_product, i):
    resp = client.post('/api/cart', json={'product_id': sample_product, 'quantity': 1})
    assert resp.status_code == 200
    assert resp.get_json()['cart']['item_count'] == 1


# --- intentionally failing bulk cases ---------------------------------------

@pytest.mark.parametrize("i", range(50))
def test_bulk_wrong_price(client, sample_product, i):
    resp = client.get(f'/api/products/{sample_product}')
    assert resp.get_json()['price'] == 1.23  # intentionally wrong
