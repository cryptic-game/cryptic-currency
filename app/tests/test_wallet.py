from unittest import TestCase
from unittest.mock import patch

from mock.mock_loader import mock
from models.wallet import Wallet
from resources import wallet
from schemes import (
    success_scheme,
    already_own_a_wallet,
    unknown_source_or_destination,
    permission_denied,
    not_enough_coins,
)


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

        expected_result = already_own_a_wallet
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

    @patch("resources.wallet.update_miner")
    @patch("resources.wallet.Transaction")
    def test__user_endpoint__get__successful(self, transaction_patch, update_miner_patch):
        test_wallet = mock.MagicMock()

        expected_result = {**test_wallet.serialize, "transactions": transaction_patch.get()}
        actual_result = wallet.get({}, "", test_wallet)

        self.assertEqual(expected_result, actual_result)
        update_miner_patch.assert_called_with(test_wallet)
        transaction_patch.get.assert_called_with(test_wallet.source_uuid)

    def test__user_endpoint__list(self):
        wallets = [mock.MagicMock() for _ in range(5)]

        self.query_wallet.filter_by.return_value = wallets

        expected_result = {"wallets": [w.source_uuid for w in wallets]}
        actual_result = wallet.list_wallets({}, "user")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(user_uuid="user")

    def test__user_endpoint__send__unknown_dest(self):
        source_wallet = mock.MagicMock()
        self.query_wallet.filter_by().first.return_value = None

        expected_result = unknown_source_or_destination
        actual_result = wallet.send({"destination_uuid": "dest"}, "", source_wallet)

        self.assertEqual(expected_result, actual_result)

    @patch("resources.wallet.update_miner")
    def test__user_endpoint__send__not_enough_coins(self, update_miner_patch):
        source_wallet = mock.MagicMock()
        source_wallet.amount = 31
        self.query_wallet.filter_by().first.return_value = mock.MagicMock()

        expected_result = not_enough_coins
        actual_result = wallet.send({"send_amount": 42, "destination_uuid": "dest"}, "", source_wallet)

        self.assertEqual(expected_result, actual_result)
        update_miner_patch.assert_called_with(source_wallet)

    @patch("resources.wallet.Transaction")
    @patch("resources.wallet.update_miner")
    def test__user_endpoint__send__successful(self, update_miner_patch, transaction_patch):
        source_wallet = mock.MagicMock()
        source_wallet.amount = 100
        dest_wallet = self.query_wallet.filter_by().first.return_value = mock.MagicMock()
        dest_wallet.amount = 50

        expected_calls = [
            (
                source_wallet.user_uuid,
                {
                    "notify-id": "outgoing-transaction",
                    "origin": "send",
                    "wallet_uuid": source_wallet.source_uuid,
                    "new_amount": 100 - 42,
                },
            ),
            (
                dest_wallet.user_uuid,
                {
                    "notify-id": "incoming-transaction",
                    "origin": "send",
                    "wallet_uuid": dest_wallet.source_uuid,
                    "new_amount": 50 + 42,
                },
            ),
        ]
        mock.m.contact_user.side_effect = lambda *args: self.assertEqual(expected_calls.pop(0), args)

        expected_result = success_scheme
        actual_result = wallet.send({"send_amount": 42, "destination_uuid": "dest", "usage": "text"}, "", source_wallet)

        self.assertEqual(expected_result, actual_result)
        update_miner_patch.assert_called_with(source_wallet)
        self.assertEqual(100 - 42, source_wallet.amount)
        self.assertEqual(50 + 42, dest_wallet.amount)
        mock.wrapper.session.commit.assert_called_with()
        transaction_patch.create.assert_called_with(source_wallet.source_uuid, 42, "dest", "text", origin=0)
        self.assertFalse(expected_calls)

    def test__user_endpoint__reset__permission_denied(self):
        test_wallet = mock.MagicMock()
        test_wallet.user_uuid = "the-user"

        expected_result = permission_denied
        actual_result = wallet.reset({}, "wrong-user", test_wallet)

        self.assertEqual(expected_result, actual_result)

    def test__user_endpoint__reset__successful(self):
        test_wallet = mock.MagicMock()
        test_wallet.user_uuid = "the-user"

        expected_result = success_scheme
        actual_result = wallet.reset({}, "the-user", test_wallet)

        self.assertEqual(expected_result, actual_result)
        mock.m.contact_microservice.assert_called_with(
            "service", ["miner", "stop"], {"wallet_uuid": test_wallet.source_uuid}
        )
        mock.wrapper.session.delete.assert_called_with(test_wallet)
        mock.wrapper.session.commit.assert_called_with()

    def test__user_endpoint__delete__successful(self):
        test_wallet = mock.MagicMock()

        expected_result = success_scheme
        actual_result = wallet.delete({}, "", test_wallet)

        self.assertEqual(expected_result, actual_result)
        mock.m.contact_microservice.assert_called_with(
            "service", ["miner", "stop"], {"wallet_uuid": test_wallet.source_uuid}
        )
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

        expected_result = unknown_source_or_destination
        actual_result = wallet.put({"destination_uuid": "destination", "amount": 42}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="destination")
        self.query_wallet.filter_by().first.assert_called_with()

    def test__ms_endpoint__put__without_transaction(self):
        test_wallet = mock.MagicMock()
        test_wallet.amount = 1295

        self.query_wallet.filter_by().first.return_value = test_wallet

        expected_result = success_scheme
        actual_result = wallet.put({"destination_uuid": "destination", "amount": 42, "create_transaction": False}, "")

        self.assertEqual(expected_result, actual_result)
        self.query_wallet.filter_by.assert_called_with(source_uuid="destination")
        self.query_wallet.filter_by().first.assert_called_with()
        self.assertEqual(1337, test_wallet.amount)
        mock.wrapper.session.commit.assert_called_with()
        mock.m.contact_user.assert_called_with(
            test_wallet.user_uuid,
            {
                "notify-id": "incoming-transaction",
                "origin": "put",
                "wallet_uuid": test_wallet.source_uuid,
                "new_amount": 1337,
            },
        )

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
        mock.m.contact_user.assert_called_with(
            test_wallet.user_uuid,
            {
                "notify-id": "incoming-transaction",
                "origin": "put",
                "wallet_uuid": test_wallet.source_uuid,
                "new_amount": 1337,
            },
        )
        transaction_patch.create.assert_called_with("source", 42, "destination", "the usage", 13)

    @patch("resources.wallet.update_miner")
    def test__ms_endpoint__dump__not_enough_coins(self, update_miner_patch):
        test_wallet = mock.MagicMock()
        test_wallet.amount = 10

        expected_result = not_enough_coins
        actual_result = wallet.dump({"amount": 1337}, "", test_wallet)

        self.assertEqual(expected_result, actual_result)
        update_miner_patch.assert_called_with(test_wallet)

    @patch("resources.wallet.update_miner")
    def test__ms_endpoint__dump__without_transaction(self, update_miner_patch):
        test_wallet = mock.MagicMock()
        test_wallet.amount = 1379

        expected_result = success_scheme
        actual_result = wallet.dump({"amount": 1337, "create_transaction": False}, "", test_wallet)

        self.assertEqual(expected_result, actual_result)
        update_miner_patch.assert_called_with(test_wallet)
        self.assertEqual(42, test_wallet.amount)
        mock.wrapper.session.commit.assert_called_with()
        mock.m.contact_user.assert_called_with(
            test_wallet.user_uuid,
            {
                "notify-id": "outgoing-transaction",
                "origin": "dump",
                "wallet_uuid": test_wallet.source_uuid,
                "new_amount": 42,
            },
        )

    @patch("resources.wallet.Transaction")
    @patch("resources.wallet.update_miner")
    def test__ms_endpoint__dump__with_transaction(self, update_miner_patch, transaction_patch):
        test_wallet = mock.MagicMock()
        test_wallet.amount = 1379

        expected_result = transaction_patch.create().serialize
        actual_result = wallet.dump(
            {
                "amount": 1337,
                "create_transaction": True,
                "destination_uuid": "dest",
                "usage": "the usage",
                "origin": 11,
            },
            "",
            test_wallet,
        )

        self.assertEqual(expected_result, actual_result)
        update_miner_patch.assert_called_with(test_wallet)
        self.assertEqual(42, test_wallet.amount)
        mock.wrapper.session.commit.assert_called_with()
        mock.m.contact_user.assert_called_with(
            test_wallet.user_uuid,
            {
                "notify-id": "outgoing-transaction",
                "origin": "dump",
                "wallet_uuid": test_wallet.source_uuid,
                "new_amount": 42,
            },
        )
        transaction_patch.create.assert_called_with(test_wallet.source_uuid, 1337, "dest", "the usage", 11)

    def test__ms_endpoint__delete_user(self):
        self.assertEqual(success_scheme, wallet.delete_user({"user_uuid": "the-user"}, "server"))

        self.query_wallet.filter_by.assert_called_with(user_uuid="the-user")
        self.query_wallet.filter_by().delete.assert_called_with()
        mock.wrapper.session.commit.assert_called_with()
