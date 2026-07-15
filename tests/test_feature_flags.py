"""Tests for the CloudBees Unify feature-flag gated behavior.

These don't require a real ROX_SDK_KEY / Unify connection - conftest.py
leaves ROX_SDK_KEY unset, so the SDK fails soft and every flag stays on
its coded default (see feature_flags.py). Tests monkeypatch the flag's
is_enabled() directly to exercise both the on and off code paths
deterministically, rather than depending on Unify's actual live state.
"""
import app as app_module


def test_features_endpoint_reports_default_off(client):
    resp = client.get('/api/features')
    assert resp.status_code == 200
    assert resp.get_json() == {'enable_loyalty_points': False}


def test_order_excludes_loyalty_points_when_flag_off(client, sample_product, monkeypatch):
    monkeypatch.setattr(
        app_module.flags.enable_loyalty_points, 'is_enabled', lambda: False
    )
    client.post('/api/cart', json={'product_id': sample_product, 'quantity': 1})
    order_id = client.post(
        '/api/checkout', json={'shipping_address': '123 Main St'}
    ).get_json()['order_id']

    order = client.get(f'/api/orders/{order_id}').get_json()
    assert 'loyalty_points_earned' not in order


def test_order_includes_loyalty_points_when_flag_on(client, sample_product, monkeypatch):
    monkeypatch.setattr(
        app_module.flags.enable_loyalty_points, 'is_enabled', lambda: True
    )
    client.post('/api/cart', json={'product_id': sample_product, 'quantity': 1})
    order_id = client.post(
        '/api/checkout', json={'shipping_address': '123 Main St'}
    ).get_json()['order_id']

    order = client.get(f'/api/orders/{order_id}').get_json()
    assert order['loyalty_points_earned'] == int(89.99)
