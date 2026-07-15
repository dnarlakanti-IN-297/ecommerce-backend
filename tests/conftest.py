"""Shared pytest fixtures for the ecommerce-backend test suite.

DATABASE_URL is pointed at a throwaway SQLite file *before* `app` is
imported, since Flask-SQLAlchemy reads SQLALCHEMY_DATABASE_URI once at
import time. A real file (not sqlite:///:memory:) is used so every
connection Flask-SQLAlchemy opens during a test sees the same data.
"""
import os
import tempfile

import pytest

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ['DATABASE_URL'] = f'sqlite:///{_db_path}'
os.environ.setdefault('ROX_SDK_KEY', '')  # feature flags fail soft to their coded defaults

from app import app as flask_app, db, Product  # noqa: E402
import app as app_module  # noqa: E402


def pytest_sessionfinish(session, exitstatus):
    os.close(_db_fd)
    os.remove(_db_path)


@pytest.fixture(autouse=True)
def _clean_cart_storage():
    """cart_storage is a module-level dict shared across requests - reset
    it between tests so one test's cart can't leak into another."""
    app_module.cart_storage.clear()
    yield
    app_module.cart_storage.clear()


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.app_context():
        db.create_all()
        yield flask_app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_product(client):
    product = Product(
        name="Running Shoes",
        description="Lightweight trainers",
        price=89.99,
        category="running-shoes",
        stock=10,
        rating=4.5,
    )
    db.session.add(product)
    db.session.commit()
    return product.id
