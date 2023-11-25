from TDTK.core.tests import Tests
class Testing:
    # Tests that the wifi connection function successfully connects to a valid network.  
    def test_wifi_connection_successful(self, mocker):
        # Mocking the AdbDevice object
        mock_device = mocker.Mock()
        mock_device.shell.return_value = "Wifi is enabled"
        mock_device.shell2.return_value = "Success"
        mocker.patch.object(Tests, 'device', mock_device)

        # Mocking the logger object
        mock_logger = mocker.Mock()
        mocker.patch.object(Tests, 'logger', mock_logger)

        # Testing the wifi_connection function
        test_obj = Tests(logger=mock_logger)
        parameters = {
            "ssid": "test_ssid",
            "encryption": "WPA2",
            "password": "test_password"
        }
        assert test_obj.wifi_connection(parameters) == 0

        # Asserting that the logger was called with the correct messages
        mock_logger.log.assert_any_call("Command: cmd wifi connect-network test_ssid WPA2 test_password", type="debug")
        mock_logger.log.assert_any_call("Command Output: Success", type="debug")