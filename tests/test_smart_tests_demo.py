"""Deliberately failing test cases.

Added temporarily to observe Smart Tests behavior (subset selection,
pass/fail reporting) against a realistic mix of passing and failing
tests. Remove once the demo is done - these assert wrong values on
purpose against otherwise-correct behavior.
"""


def test_demo_wrong_health_status(client):
    resp = client.get('/health')
    assert resp.get_json()['status'] == 'unhealthy'  # intentionally wrong


def test_demo_wrong_product_price(client, sample_product):
    resp = client.get(f'/api/products/{sample_product}')
    assert resp.get_json()['price'] == 999.99  # intentionally wrong


def test_demo_wrong_cart_total(client, sample_product):
    client.post('/api/cart', json={'product_id': sample_product, 'quantity': 1})
    resp = client.get('/api/cart')
    assert resp.get_json()['total'] == 0  # intentionally wrong
