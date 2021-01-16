from importlib import machinery, util
from unittest import TestCase

from mock.mock_loader import mock
from resources import wallet
from resources.errors import wallet_exists, can_access_wallet
from schemes import scheme_default, scheme_send, scheme_reset, scheme_transactions


def import_app(name: str = "app"):
    return machinery.SourceFileLoader(name, util.find_spec("app").origin).load_module()


def import_main(name: str = "main"):
    return machinery.SourceFileLoader(name, util.find_spec("main").origin).load_module()


class TestApp(TestCase):
    def setUp(self):
        mock.reset_mocks()

    def test__microservice_setup(self):
        app = import_app()

        mock.MicroService.assert_called_with("currency")
        self.assertEqual(mock.MicroService(), app.m)

        mock.m.get_wrapper.assert_called_with()
        self.assertEqual(mock.m.get_wrapper(), app.wrapper)

    def test__microservice_setup_called(self):
        main = import_main()
        self.assertEqual(import_app(), main.app)

    def test__run_as_main(self):
        import_main("__main__")

        mock.wrapper.Base.metadata.create_all.assert_called_with(bind=mock.wrapper.engine)
        mock.m.run.assert_called_with()

    def test__import_as_module(self):
        import_main()

        mock.wrapper.Base.metadata.create_all.assert_not_called()
        mock.m.run.assert_not_called()

    def test__endpoints_available(self):
        main = import_main("__main__")
        elements = [getattr(main, element_name) for element_name in dir(main)]

        registered_user_endpoints = mock.user_endpoints.copy()
        registered_ms_endpoints = mock.ms_endpoints.copy()

        expected_user_endpoints = [
            (["create"], {}, wallet.create),
            (["get"], scheme_default, wallet.get, wallet_exists, can_access_wallet),
            (["transactions"], scheme_transactions, wallet.transactions, wallet_exists, can_access_wallet),
            (["list"], {}, wallet.list_wallets),
            (["send"], scheme_send, wallet.send, wallet_exists, can_access_wallet),
            (["reset"], scheme_reset, wallet.reset, wallet_exists),
            (["delete"], scheme_default, wallet.delete, wallet_exists),
        ]

        expected_ms_endpoints = [
            (["exists"], wallet.exists),
            (["owner"], wallet.owner),
            (["put"], wallet.put),
            (["dump"], wallet.dump, wallet_exists, can_access_wallet),
            (["delete_user"], wallet.delete_user),
        ]

        for path, requires, func, *errors in expected_user_endpoints:
            self.assertIn((path, requires), registered_user_endpoints)
            endpoint_handler = mock.user_endpoint_handlers[tuple(path)]
            registered_user_endpoints.remove((path, requires))
            self.assertIn(endpoint_handler, elements)
            self.assertEqual(func, endpoint_handler)
            if errors:
                self.assertEqual(tuple(errors), endpoint_handler.__errors__)
            else:
                self.assertNotIn("__errors__", dir(endpoint_handler))

        for path, func, *errors in expected_ms_endpoints:
            self.assertIn(path, registered_ms_endpoints)
            endpoint_handler = mock.ms_endpoint_handlers[tuple(path)]
            registered_ms_endpoints.remove(path)
            self.assertIn(endpoint_handler, elements)
            self.assertEqual(func, endpoint_handler)
            if errors:
                self.assertEqual(tuple(errors), endpoint_handler.__errors__)
            else:
                self.assertNotIn("__errors__", dir(endpoint_handler))

        self.assertFalse(registered_user_endpoints)
        self.assertFalse(registered_ms_endpoints)
