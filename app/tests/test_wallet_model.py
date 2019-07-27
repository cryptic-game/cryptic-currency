import datetime
from unittest import TestCase
from unittest.mock import patch

from mock.mock_loader import mock
from models.wallet import Wallet


class TestWalletModel(TestCase):
    def setUp(self):
        mock.reset_mocks()

    def test__model__wallet__structure(self):
        self.assertEqual("wallet", Wallet.__tablename__)
        self.assertTrue(issubclass(Wallet, mock.wrapper.Base))
        for col in ["time_stamp", "source_uuid", "key", "amount", "user_uuid"]:
            self.assertIn(col, dir(Wallet))

    def test__model__wallet__serialize(self):
        time_stamp = datetime.datetime.fromtimestamp(12345678)
        wallet = Wallet(
            time_stamp=time_stamp, source_uuid="source uuid", key="the key!", amount=99999, user_uuid="foobar"
        )

        expected_result = {
            "time_stamp": "1970-05-23 22:21:18",
            "source_uuid": "source uuid",
            "key": "the key!",
            "amount": 99999,
            "user_uuid": "foobar",
        }
        serialized = wallet.serialize

        self.assertEqual(expected_result, serialized)

        serialized["key"] = "not the real key"
        self.assertEqual(expected_result, wallet.serialize)

    def test__model__wallet__create(self):
        now = datetime.datetime.now()
        actual_result = Wallet.create("the-user-uuid")

        self.assertEqual("the-user-uuid", actual_result.user_uuid)
        self.assertEqual(100, actual_result.amount)
        self.assertRegex(actual_result.source_uuid, r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")
        self.assertRegex(actual_result.key, r"[0-9a-f]{10}")
        self.assertLess(abs((actual_result.time_stamp - now).total_seconds()), 0.01)
        mock.wrapper.session.add.assert_called_with(actual_result)
        mock.wrapper.session.commit.assert_called_with()

    def test__model__wallet__create__different_uuid(self):
        first_element = Wallet.create("user-uuid").source_uuid
        second_element = Wallet.create("user-uuid").source_uuid
        self.assertNotEqual(first_element, second_element)

    @patch("models.wallet.Wallet.key")
    @patch("models.wallet.Wallet.source_uuid")
    def test__model__wallet__auth_user(self, source_uuid_patch, key_patch):
        query_wallet = mock.MagicMock()
        default = mock.MagicMock()
        mock.wrapper.session.query.side_effect = lambda a: {Wallet: query_wallet}.get(a, default)
        query_wallet.filter().exists.return_value = "exists?"
        source_uuid_patch.__eq__.return_value = "source-eq"
        key_patch.__eq__.return_value = "key-eq"

        expected_result = default.scalar()
        actual_result = Wallet.auth_user("source", "key")

        self.assertEqual(expected_result, actual_result)
        source_uuid_patch.__eq__.assert_called_with("source")
        key_patch.__eq__.assert_called_with("key")
        query_wallet.filter.assert_called_with("source-eq", "key-eq")
        mock.wrapper.session.query.assert_called_with("exists?")
