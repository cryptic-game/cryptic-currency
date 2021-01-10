from unittest import TestCase

from mock.mock_loader import mock
from models.wallet import Wallet
from resources import errors
from resources.errors import MicroserviceException
from schemes import unknown_source_or_destination, permission_denied


class TestErrors(TestCase):
    def setUp(self):
        mock.reset_mocks()

        self.query_wallet = mock.MagicMock()
        mock.wrapper.session.query.side_effect = {Wallet: self.query_wallet}.__getitem__

    def test__wallet_exists__wallet_not_found(self):
        self.query_wallet.get.return_value = None

        with self.assertRaises(MicroserviceException) as context:
            errors.wallet_exists({"source_uuid": "source"}, "")

        self.assertEqual(unknown_source_or_destination, context.exception.error)
        self.query_wallet.get.assert_called_with("source")

    def test__wallet_exists__successful(self):
        mock_wallet = self.query_wallet.get.return_value = mock.MagicMock()

        self.assertEqual(mock_wallet, errors.wallet_exists({"source_uuid": "source"}, ""))
        self.query_wallet.get.assert_called_with("source")

    def test__can_access_wallet__permission_denied(self):
        mock_wallet = mock.MagicMock()
        mock_wallet.key = "s3cr3t"

        with self.assertRaises(MicroserviceException) as context:
            errors.can_access_wallet({"key": "wrong"}, "", mock_wallet)

        self.assertEqual(permission_denied, context.exception.error)

    def test__can_access_wallet__successful(self):
        mock_wallet = mock.MagicMock()
        mock_wallet.key = "s3cr3t"

        self.assertEqual(mock_wallet, errors.can_access_wallet({"key": "s3cr3t"}, "", mock_wallet))
