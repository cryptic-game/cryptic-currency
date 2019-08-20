from unittest import TestCase
from unittest.mock import patch

from mock.mock_loader import mock
from models.wallet import Wallet
from resources import wallet


class TestWallet(TestCase):
    def setUp(self):
        mock.reset_mocks()

        self.query_wallet = mock.MagicMock()
        mock.wrapper.session.query.side_effect = {Wallet: self.query_wallet}.__getitem__

    def test__update_miner(self):
        mock.m.contact_microservice.return_value = {"coins": 31}

        test_wallet = mock.MagicMock()
        test_wallet.amount = 0

        wallet.update_miner(test_wallet)

        self.assertEqual(test_wallet.amount, 31)
        mock.m.contact_microservice.assert_called_with(
            "service", ["miner", "collect"], {"wallet_uuid": test_wallet.source_uuid}
        )
        mock.wrapper.session.commit.assert_called_with()

    def test__user_endpoint__create__already_own_a_wallet(self):
        self.query_wallet.filter_by().first.return_value = "something"

        expected_result = {"error": "already_own_a_wallet"}
        actual_result = wallet.create({}, "the-user")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(user_uuid="the-user")
        self.query_wallet.filter_by().first.assert_called_with()

    @patch("resources.wallet.Wallet.create")
    def test__user_endpoint__create__successful(self, wallet_create_patch):
        self.query_wallet.filter_by().first.return_value = None

        expected_result = wallet_create_patch().serialize
        actual_result = wallet.create({}, "the-user")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(user_uuid="the-user")
        self.query_wallet.filter_by().first.assert_called_with()
        wallet_create_patch.assert_called_with("the-user")

    def test__user_endpoint__get__unknown_wallet(self):
        self.query_wallet.get.return_value = None

        expected_result = {"error": "unknown_source_or_destination"}
        actual_result = wallet.get({"source_uuid": "source", "key": "the-key"}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.get.assert_called_with("source")

    def test__user_endpoint__get__permission_denied(self):
        test_wallet = mock.MagicMock()
        test_wallet.key = "correct-key"

        self.query_wallet.get.return_value = test_wallet

        expected_result = {"error": "permission_denied"}
        actual_result = wallet.get({"source_uuid": "source", "key": "wrong-key"}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.get.assert_called_with("source")

    @patch("resources.wallet.update_miner")
    @patch("resources.wallet.Transaction")
    def test__user_endpoint__get__successful(self, transaction_patch, update_miner_patch):
        test_wallet = mock.MagicMock()
        test_wallet.key = "key"
        test_wallet.serialize = {"wallet": "serialized"}

        self.query_wallet.get.return_value = test_wallet

        expected_result = {"wallet": "serialized", "transactions": transaction_patch.get()}
        actual_result = wallet.get({"source_uuid": "source", "key": "key"}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.get.assert_called_with("source")
        update_miner_patch.assert_called_with(test_wallet)
        transaction_patch.get.assert_called_with("source")

    def test__user_endpoint__list(self):
        wallets = [mock.MagicMock() for _ in range(5)]

        self.query_wallet.filter_by.return_value = wallets

        expected_result = {"wallets": [w.source_uuid for w in wallets]}
        actual_result = wallet.list_wallets({}, "user")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(user_uuid="user")

    @patch("resources.wallet.Wallet.auth_user")
    def test__user_endpoint__send__permission_denied(self, auth_user_patch):
        auth_user_patch.return_value = False

        expected_result = {"error": "permission_denied"}
        actual_result = wallet.send(
            {"source_uuid": "source", "key": "key", "send_amount": 42, "destination": "dest", "usage": "text"}, ""
        )

        self.assertEqual(expected_result, actual_result)
        auth_user_patch.assert_called_with("source", "key")

    @patch("resources.wallet.Wallet.auth_user")
    def test__user_endpoint__send__unknown_source(self, auth_user_patch):
        auth_user_patch.return_value = True

        def filter_by_handler(source_uuid):
            self.assertIn(source_uuid, ["source", "dest"])
            out = mock.MagicMock()
            if source_uuid == "source":
                out.first.return_value = None
            elif source_uuid == "dest":
                out.first.return_value = "dest"
            return out

        self.query_wallet.filter_by.side_effect = filter_by_handler

        expected_result = {"error": "unknown_source_or_destination"}
        actual_result = wallet.send(
            {"source_uuid": "source", "key": "key", "send_amount": 42, "destination_uuid": "dest", "usage": "text"}, ""
        )

        self.assertEqual(expected_result, actual_result)
        auth_user_patch.assert_called_with("source", "key")

    @patch("resources.wallet.Wallet.auth_user")
    def test__user_endpoint__send__unknown_dest(self, auth_user_patch):
        auth_user_patch.return_value = True

        def filter_by_handler(source_uuid):
            self.assertIn(source_uuid, ["source", "dest"])
            out = mock.MagicMock()
            if source_uuid == "source":
                out.first.return_value = "source"
            elif source_uuid == "dest":
                out.first.return_value = None
            return out

        self.query_wallet.filter_by.side_effect = filter_by_handler

        expected_result = {"error": "unknown_source_or_destination"}
        actual_result = wallet.send(
            {"source_uuid": "source", "key": "key", "send_amount": 42, "destination_uuid": "dest", "usage": "text"}, ""
        )

        self.assertEqual(expected_result, actual_result)
        auth_user_patch.assert_called_with("source", "key")

    @patch("resources.wallet.update_miner")
    @patch("resources.wallet.Wallet.auth_user")
    def test__user_endpoint__send__not_enough_coins(self, auth_user_patch, update_miner_patch):
        auth_user_patch.return_value = True

        source_wallet = mock.MagicMock()
        source_wallet.amount = 31
        dest_wallet = mock.MagicMock()

        def filter_by_handler(source_uuid):
            self.assertIn(source_uuid, ["source", "dest"])
            out = mock.MagicMock()
            if source_uuid == "source":
                out.first.return_value = source_wallet
            elif source_uuid == "dest":
                out.first.return_value = dest_wallet
            return out

        self.query_wallet.filter_by.side_effect = filter_by_handler

        expected_result = {"error": "not_enough_coins"}
        actual_result = wallet.send(
            {"source_uuid": "source", "key": "key", "send_amount": 42, "destination_uuid": "dest", "usage": "text"}, ""
        )

        self.assertEqual(expected_result, actual_result)
        auth_user_patch.assert_called_with("source", "key")
        update_miner_patch.assert_called_with(source_wallet)

    @patch("resources.wallet.Transaction")
    @patch("resources.wallet.update_miner")
    @patch("resources.wallet.Wallet.auth_user")
    def test__user_endpoint__send__successful(self, auth_user_patch, update_miner_patch, transaction_patch):
        auth_user_patch.return_value = True

        source_wallet = mock.MagicMock()
        source_wallet.amount = 100
        dest_wallet = mock.MagicMock()
        dest_wallet.amount = 50

        def filter_by_handler(source_uuid):
            self.assertIn(source_uuid, ["source", "dest"])
            out = mock.MagicMock()
            if source_uuid == "source":
                out.first.return_value = source_wallet
            elif source_uuid == "dest":
                out.first.return_value = dest_wallet
            return out

        self.query_wallet.filter_by.side_effect = filter_by_handler

        expected_result = {"ok": True}
        actual_result = wallet.send(
            {"source_uuid": "source", "key": "key", "send_amount": 42, "destination_uuid": "dest", "usage": "text"}, ""
        )

        self.assertEqual(expected_result, actual_result)
        auth_user_patch.assert_called_with("source", "key")
        update_miner_patch.assert_called_with(source_wallet)
        self.assertEqual(100 - 42, source_wallet.amount)
        self.assertEqual(50 + 42, dest_wallet.amount)
        mock.wrapper.session.commit.assert_called_with()
        transaction_patch.create.assert_called_with("source", 42, "dest", "text", origin=0)

    def test__user_endpoint__reset__unknown_wallet(self):
        self.query_wallet.filter_by().first.return_value = None

        expected_result = {"error": "unknown_source_or_destination"}
        actual_result = wallet.reset({"source_uuid": "the-source"}, "user-uuid")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="the-source")
        self.query_wallet.filter_by().first.assert_called_with()

    def test__user_endpoint__reset__permission_denied(self):
        test_wallet = mock.MagicMock()
        test_wallet.user_uuid = "the-user"

        self.query_wallet.filter_by().first.return_value = test_wallet

        expected_result = {"error": "permission_denied"}
        actual_result = wallet.reset({"source_uuid": "the-source"}, "wrong-user")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="the-source")
        self.query_wallet.filter_by().first.assert_called_with()

    def test__user_endpoint__reset__successful(self):
        test_wallet = mock.MagicMock()
        test_wallet.user_uuid = "the-user"

        self.query_wallet.filter_by().first.return_value = test_wallet

        expected_result = {"ok": True}
        actual_result = wallet.reset({"source_uuid": "the-source"}, "the-user")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="the-source")
        self.query_wallet.filter_by().first.assert_called_with()
        mock.wrapper.session.delete.assert_called_with(test_wallet)
        mock.wrapper.session.commit.assert_called_with()

    def test__user_endpoint__delete__unknown_wallet(self):
        self.query_wallet.filter_by().first.return_value = None

        expected_result = {"error": "unknown_source_or_destination"}
        actual_result = wallet.delete({"source_uuid": "source", "key": "the-key"}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="source", key="the-key")
        self.query_wallet.filter_by().first.assert_called_with()

    def test__user_endpoint__delete__successful(self):
        test_wallet = mock.MagicMock()

        self.query_wallet.filter_by().first.return_value = test_wallet

        expected_result = {"ok": True}
        actual_result = wallet.delete({"source_uuid": "source", "key": "the-key"}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="source", key="the-key")
        self.query_wallet.filter_by().first.assert_called_with()
        mock.wrapper.session.delete.assert_called_with(test_wallet)
        mock.wrapper.session.commit.assert_called_with()

    def test__ms_endpoint__exists__not_found(self):
        self.query_wallet.filter_by().first.return_value = None

        expected_result = {"exists": False}
        actual_result = wallet.exists({"source_uuid": "the-source"}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="the-source")
        self.query_wallet.filter_by().first.assert_called_with()

    def test__ms_endpoint__exists__successful(self):
        self.query_wallet.filter_by().first.return_value = "wallet"

        expected_result = {"exists": True}
        actual_result = wallet.exists({"source_uuid": "the-source"}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="the-source")
        self.query_wallet.filter_by().first.assert_called_with()

    def test__ms_endpoint__put__unknown_wallet(self):
        self.query_wallet.filter_by().first.return_value = None

        expected_result = {"error": "unknown_source_or_destination"}
        actual_result = wallet.put({"destination_uuid": "destination", "amount": 42}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="destination")
        self.query_wallet.filter_by().first.assert_called_with()

    def test__ms_endpoint__put__without_transaction(self):
        test_wallet = mock.MagicMock()
        test_wallet.amount = 1295

        self.query_wallet.filter_by().first.return_value = test_wallet

        expected_result = {"ok": True}
        actual_result = wallet.put({"destination_uuid": "destination", "amount": 42, "create_transaction": False}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="destination")
        self.query_wallet.filter_by().first.assert_called_with()
        self.assertEqual(1337, test_wallet.amount)
        mock.wrapper.session.commit.assert_called_with()

    @patch("resources.wallet.Transaction")
    def test__ms_endpoint__put__with_transaction(self, transaction_patch):
        test_wallet = mock.MagicMock()
        test_wallet.amount = 1295

        self.query_wallet.filter_by().first.return_value = test_wallet

        expected_result = transaction_patch.create().serialize
        actual_result = wallet.put(
            {
                "destination_uuid": "destination",
                "amount": 42,
                "create_transaction": True,
                "source_uuid": "source",
                "usage": "the usage",
                "origin": 13,
            },
            "",
        )

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="destination")
        self.query_wallet.filter_by().first.assert_called_with()
        self.assertEqual(1337, test_wallet.amount)
        mock.wrapper.session.commit.assert_called_with()
        transaction_patch.create.assert_called_with("source", 42, "destination", "the usage", 13)

    def test__ms_endpoint__dump__unknown_wallet(self):
        self.query_wallet.filter_by().first.return_value = None

        expected_result = {"error": "unknown_source_or_destination"}
        actual_result = wallet.dump({"source_uuid": "src", "key": "the-key", "amount": 1337}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="src")
        self.query_wallet.filter_by().first.assert_called_with()

    def test__ms_endpoint__dump__permission_denied(self):
        test_wallet = mock.MagicMock()
        test_wallet.key = "wallet-key"

        self.query_wallet.filter_by().first.return_value = test_wallet

        expected_result = {"error": "permission_denied"}
        actual_result = wallet.dump({"source_uuid": "src", "key": "the-key", "amount": 1337}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="src")
        self.query_wallet.filter_by().first.assert_called_with()

    @patch("resources.wallet.update_miner")
    def test__ms_endpoint__dump__not_enough_coins(self, update_miner_patch):
        test_wallet = mock.MagicMock()
        test_wallet.key = "wallet-key"
        test_wallet.amount = 10

        self.query_wallet.filter_by().first.return_value = test_wallet

        expected_result = {"error": "not_enough_coins"}
        actual_result = wallet.dump({"source_uuid": "src", "key": "wallet-key", "amount": 1337}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="src")
        self.query_wallet.filter_by().first.assert_called_with()
        update_miner_patch.assert_called_with(test_wallet)

    @patch("resources.wallet.update_miner")
    def test__ms_endpoint__dump__without_transaction(self, update_miner_patch):
        test_wallet = mock.MagicMock()
        test_wallet.key = "wallet-key"
        test_wallet.amount = 1379

        self.query_wallet.filter_by().first.return_value = test_wallet

        expected_result = {"ok": True}
        actual_result = wallet.dump(
            {"source_uuid": "src", "key": "wallet-key", "amount": 1337, "create_transaction": False}, ""
        )

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="src")
        self.query_wallet.filter_by().first.assert_called_with()
        update_miner_patch.assert_called_with(test_wallet)
        self.assertEqual(42, test_wallet.amount)
        mock.wrapper.session.commit.assert_called_with()

    @patch("resources.wallet.Transaction")
    @patch("resources.wallet.update_miner")
    def test__ms_endpoint__dump__with_transaction(self, update_miner_patch, transaction_patch):
        test_wallet = mock.MagicMock()
        test_wallet.key = "wallet-key"
        test_wallet.amount = 1379

        self.query_wallet.filter_by().first.return_value = test_wallet

        expected_result = transaction_patch.create().serialize
        actual_result = wallet.dump(
            {
                "source_uuid": "src",
                "key": "wallet-key",
                "amount": 1337,
                "create_transaction": True,
                "destination_uuid": "dest",
                "usage": "the usage",
                "origin": 11,
            },
            "",
        )

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="src")
        self.query_wallet.filter_by().first.assert_called_with()
        update_miner_patch.assert_called_with(test_wallet)
        self.assertEqual(42, test_wallet.amount)
        mock.wrapper.session.commit.assert_called_with()
        transaction_patch.create.assert_called_with("src", 1337, "dest", "the usage", 11)
