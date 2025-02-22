"""
This tests requests made by switch devices.

All tests inherit from the TestBase class which contains the fixtures
and methods needed to run the tests.

The tests are automatically parametrized by `pytest_generate_tests` in
conftest.py. The two methods that are parametrized are `test_details`
and `test_methods`. The class variables are used to build the list of
devices, test methods and arguments.

The `helpers.call_api` method is patched to return a mock response.
The method, endpoint, headers and json arguments are recorded
in YAML files in the api directory, catagorized in folders by
module and files by the class name.

The default is to record requests that do not exist and compare requests
that already exist. If the API changes, set the overwrite argument to True
in order to overwrite the existing YAML file with the new request.

See Also
--------
`utils.TestBase` - Base class for all tests, containing mock objects
`confest.pytest_generate_tests` - Parametrizes tests based on
    method names & class attributes
`call_json_switches` - Contains API responses
"""

import logging
from utils import TestBase, assert_test, parse_args, Defaults
import call_json
import call_json_switches


_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

DEFAULT_COLOR = Defaults.color.rgb
COLOR_DICT = {
    'red': DEFAULT_COLOR.red,
    'blue': DEFAULT_COLOR.blue,
    'green': DEFAULT_COLOR.green,
}


class TestSwitches(TestBase):
    """Switches testing class.

    This class tests switch device details and methods. The methods are
    parametrized from the class variables using `pytest_generate_tests`.
    The call_json_switches module contains the responses for the API requests.
    The device is instantiated from the details provided by
    `call_json.DeviceList.device_list_item()`. Inherits from `utils.TestBase`.

    Instance Attributes
    -------------------
    self.manager : VeSync
        Instantiated VeSync object
    self.mock_api : Mock
        Mock with patched `helpers.call_api` method
    self.caplog : LogCaptureFixture
        Pytest fixture for capturing logs


    Class Variables
    ---------------
    device : str
        Name of device type - switches
    switches : list
        List of device types for switches, this variable is named
        after the device variable value
    base_methods : List[List[str, Dict[str, Any]]]
        List of common methods for all devices
    device_methods : Dict[List[List[str, Dict[str, Any]]]]
        Dictionary of methods specific to device types

    Methods
    --------
    test_details()
        Test the device details API request and response
    test_methods()
        Test device methods API request and response

    Examples
    --------
    >>> device = 'switches'
    >>> switches = call_json_switches.SWITCHES
    >>> base_methods = [['turn_on'], ['turn_off'], ['update']]
    >>> device_methods = {
        'ESWD16': [['method1'], ['method2', {'kwargs': 'value'}]]
        }

    """

    device = 'switches'
    switches = call_json_switches.SWITCHES
    base_methods = [['turn_on'], ['turn_off']]
    device_methods = {
        'ESWD16': [['indicator_light_on'],
                   ['rgb_color_on'],
                   ['rgb_color_set', COLOR_DICT],
                   ['set_brightness', {'brightness': Defaults.brightness}]],
    }

    def test_details(self, dev_type, method):
        """Test the device details API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of device type - switches),
        device name (switches) list of device types.

        Example:
            >>> device = 'switches'
            >>> switches = call_json_switches.SWITCHES

        See Also
        --------
        `utils.TestBase` class docstring
        `call_json_switches` module docstring

        Notes
        ------
        The device is instantiated using the `call_json.DeviceList.device_list_item()`
        method. The device details contain the default values set in `utils.Defaults`
        """
        # Set return value for call_api based on call_json_bulb.DETAILS_RESPONSES
        self.mock_api.return_value = call_json_switches.DETAILS_RESPONSES[dev_type]

        # Instantiate device from device list return item
        device_config = call_json.DeviceList.device_list_item(dev_type)

        # Instantiate device from device list return item
        switch_obj = self.manager.object_factory(device_config)

        # Get method from device object
        method_call = getattr(switch_obj, method)
        method_call()

        # Parse mock_api args tuple from arg, kwargs to kwargs
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recored request or write new records
        assert_test(method_call, all_kwargs, dev_type, self.write_api, self.overwrite)

        # Assert device details match expected values
        assert switch_obj.active_time == Defaults.active_time
        if switch_obj.is_dimmable():
            assert switch_obj.brightness == str(Defaults.brightness)
            assert switch_obj.indicator_light_status == 'on'
            assert switch_obj.rgb_light_status == 'on'
            assert switch_obj.rgb_light_value == COLOR_DICT
        self.mock_api.reset_mock()
        self.mock_api.return_value = call_json.DETAILS_BADCODE
        method_call()
        assert 'details' in self.caplog.records[-1].message

    def test_methods(self, dev_type, method):
        """Test switch methods API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of device type - switches),
        device name (switches) list of device types, `base_methods` - list of
        methods for all devices, and `device_methods` - list of methods for
        each device type.

        Example:
            >>> base_methods = [['turn_on'], ['turn_off'], ['update']]
            >>> device_methods = {
                'dev_type': [['method1'], ['method2', {'kwargs': 'value'}]]
                }

        Notes
        -----
        The response can be a callable that accepts the `kwargs` argument to
        sync the device response with the API response. In some cases the API
        returns data from the method call, such as `get_yearly_energy`, in other cases the
        API returns a simple confirmation the command was successful.

        See Also
        --------
        `TestBase` class method
        `call_json_switches` module

        """
        # Get method name and kwargs from method fixture
        method_name = method[0]
        if len(method) == 2 and isinstance(method[1], dict):
            method_kwargs = method[1]
        else:
            method_kwargs = {}

        # Set return value for call_api based on call_json_switches.METHOD_RESPONSES
        method_response = call_json_switches.METHOD_RESPONSES[dev_type][method_name]
        if callable(method_response):
            if method_kwargs:
                self.mock_api.return_value = method_response(**method_kwargs)
            else:
                self.mock_api.return_value = method_response()
        else:
            self.mock_api.return_value = method_response

        # Get device configuration from call_json.DeviceList.device_list_item()
        device_config = call_json.DeviceList.device_list_item(dev_type)

        # Instantiate device from device list return item
        switch_obj = self.manager.object_factory(device_config)

        # Get method from device object
        method_call = getattr(switch_obj, method[0])

        # Ensure method runs based on device configuration
        if method[0] == 'turn_on':
            switch_obj.device_status = 'off'
        elif method[0] == 'turn_off':
            switch_obj.device_status = 'on'

        # Call method with kwargs if defined
        if method_kwargs:
            method_call(**method_kwargs)
        else:
            method_call()

        # Parse arguments from mock_api call into a dictionary
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recored request or write new records
        assert_test(method_call, all_kwargs, dev_type, self.write_api, self.overwrite)

        self.mock_api.reset_mock()
        self.mock_api.return_value = call_json.DETAILS_BADCODE
        if method_kwargs:
            assert method_call(**method_kwargs) is False
        else:
            assert method_call() is False
