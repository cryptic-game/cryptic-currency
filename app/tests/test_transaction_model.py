import datetime
from unittest import TestCase

from unittest.mock import patch

from mock.mock_loader import mock
from models.transaction import Transaction


class TestTransactionModel(TestCase):
    def setUp(self):
        mock.reset_mocks()

    def test__model__transaction__structure(self):
        self.assertEqual("transaction", Transaction.__tablename__)
        self.assertTrue(issubclass(Transaction, mock.wrapper.Base))
        for col in ["id", "time_stamp", "source_uuid", "send_amount", "destination_uuid", "usage", "origin"]:
            self.assertIn(col, dir(Transaction))

    def test__model__transaction__serialize(self):
        time_stamp = datetime.datetime.fromtimestamp(421337)
        transaction = Transaction(
            id=42,
            time_stamp=time_stamp,
            source_uuid="from",
            send_amount=7,
            destination_uuid="to",
            usage="text",
            origin=3,
        )

        expected_result = {
            "id": 42,
            "time_stamp": "1970-01-05 22:02:17",
            "source_uuid": "from",
            "send_amount": 7,
            "destination_uuid": "to",
            "usage": "text",
            "origin": 3,
        }
        serialized = transaction.serialize

        self.assertEqual(expected_result, serialized)

        serialized["send_amount"] = 1234
        self.assertEqual(expected_result, transaction.serialize)

    def test__model__transaction__create(self):
        now = datetime.datetime.now()
        actual_result = Transaction.create("source", 37, "dest", "the usage", 1)

        self.assertIsInstance(actual_result, Transaction)
        self.assertEqual("source", actual_result.source_uuid)
        self.assertEqual(37, actual_result.send_amount)
        self.assertEqual("dest", actual_result.destination_uuid)
        self.assertEqual("the usage", actual_result.usage)
        self.assertEqual(1, actual_result.origin)
        self.assertLess(abs((actual_result.time_stamp - now).total_seconds()), 0.01)
        mock.wrapper.session.add.assert_called_with(actual_result)
        mock.wrapper.session.commit.assert_called_with()

    @patch("models.transaction.Transaction.destination_uuid")
    @patch("models.transaction.Transaction.source_uuid")
    @patch("models.transaction.or_")
    def test__model__transaction__get(self, or_patch, source_uuid_patch, destination_uuid_patch):
        transactions = [mock.MagicMock() for _ in range(5)]

        query_transaction = mock.MagicMock()
        mock.wrapper.session.query.side_effect = {Transaction: query_transaction}.__getitem__
        query_transaction.filter.return_value = transactions
        source_uuid_patch.__eq__.return_value = "source-eq"
        destination_uuid_patch.__eq__.return_value = "dest-eq"

        expected_result = [transaction.serialize for transaction in transactions]
        actual_result = Transaction.get("test-uuid")

        self.assertEqual(expected_result, actual_result)
        source_uuid_patch.__eq__.assert_called_with("test-uuid")
        destination_uuid_patch.__eq__.assert_called_with("test-uuid")
        or_patch.assert_called_with("source-eq", "dest-eq")
        query_transaction.filter.assert_called_with(or_patch())
