"""Test scripts for BSDGO1 Outlets."""

import pytest
from unittest.mock import patch
import logging
from pyvesync import VeSync
from pyvesync.vesyncoutlet import VeSyncOutletBSDGO1
from pyvesync.helpers import Helpers as helpers
import call_json
import call_json_outlets
from utils import Defaults, TestBase

DEVICE_TYPE = 'BSDOG01'

DEV_LIST_DETAIL = call_json.DeviceList.device_list_item(DEVICE_TYPE)

CORRECT_BSDGO1_LIST = call_json.DeviceList.device_list_response(DEVICE_TYPE)

CORRECT_BSDGO1_DETAILS = call_json_outlets.DETAILS_RESPONSES[DEVICE_TYPE]

BAD_BSDGO1_LIST = call_json.DETAILS_BADCODE


class TestVeSyncBSDGO1Switch(TestBase):
    """Test BSDGO1 outlet API."""

    def test_bsdgo1_conf(self):
        """Test initialization of BSDGO1 outlet."""
        self.mock_api.return_value = CORRECT_BSDGO1_LIST
        self.manager.get_devices()
        outlets = self.manager.outlets
        assert len(outlets) == 1
        bsdgo1_outlet = outlets[0]
        assert isinstance(bsdgo1_outlet, VeSyncOutletBSDGO1)
        assert bsdgo1_outlet.device_name == call_json.Defaults.name(DEVICE_TYPE)
        assert bsdgo1_outlet.device_type == DEVICE_TYPE
        assert bsdgo1_outlet.cid == call_json.Defaults.cid(DEVICE_TYPE)
        assert bsdgo1_outlet.uuid == call_json.Defaults.uuid(DEVICE_TYPE)

    def test_bsdgo1_details(self):
        """Test BSDGO1 get_details()."""
        self.mock_api.return_value = CORRECT_BSDGO1_DETAILS
        bsdgo1_outlet = VeSyncOutletBSDGO1(DEV_LIST_DETAIL, self.manager)
        assert bsdgo1_outlet.get_details()
        response = CORRECT_BSDGO1_DETAILS
        result = response.get('result', {})

        expected_status = 'on' if result.get('powerSwitch_1') == 1 else 'off'
        assert bsdgo1_outlet.device_status == expected_status

        assert result.get('active_time') == Defaults.active_time
        assert result.get('connectionStatus') == 'online'

    def test_bsdgo1_details_fail(self):
        """Test BSDGO1 get_details with bad response."""
        self.mock_api.return_value = BAD_BSDGO1_LIST
        bsdgo1_outlet = VeSyncOutletBSDGO1(DEV_LIST_DETAIL, self.manager)
        assert bsdgo1_outlet.get_details()==False
        assert len(self.caplog.records) == 1
        assert 'FAILED' in self.caplog.text

    def test_bsdgo1_onoff(self):
        """Test BSDGO1 Device On/Off Methods."""
        self.mock_api.return_value = {'code': 0, 'msg': 'success', 'result': {'code': 0}}
        bsdgo1_outlet = VeSyncOutletBSDGO1(DEV_LIST_DETAIL, self.manager)
        head = VeSync.req_header_bypass()
        body = {
            **self.manager.req_body_bypass_v2(),
            'cid': bsdgo1_outlet.cid,
            'configModule': bsdgo1_outlet.config_module,
            'payload': {
                'method': 'setProperty',
                'source': 'APP',
                'data': {'powerSwitch_1': 1}
            }
        }
        assert bsdgo1_outlet.turn_on()
        self.mock_api.assert_called_with(
            api='/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        # Test turn_off
        body['payload']['data']['powerSwitch_1'] = 0
        assert bsdgo1_outlet.turn_off()
        self.mock_api.assert_called_with(
            api='/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

    def test_bsdgo1_onoff_fail(self):
        """Test BSDGO1 On/Off Fail with bad response."""
        self.mock_api.return_value = BAD_BSDGO1_LIST
        bsdgo1_outlet = VeSyncOutletBSDGO1(DEV_LIST_DETAIL, self.manager)
        assert not bsdgo1_outlet.turn_on()
        assert not bsdgo1_outlet.turn_off()