"""
Unit tests for numpy_type_converter module.

These tests verify that numpy types are properly converted to Python native types
to prevent psycopg2 "can't adapt type" errors.

Run with: pytest tests/test_numpy_type_converter.py -v
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, date, time
from decimal import Decimal

from src.numpy_type_converter import (
    convert_to_native,
    convert_params_to_native,
    deep_convert,
    is_numpy_type,
    validate_native_types,
    prepare_for_db,
)


class TestSingleValueConversion(unittest.TestCase):
    """Test conversion of single numpy values to native types."""
    
    def test_numpy_int64_to_int(self):
        """numpy.int64 should convert to Python int"""
        value = np.int64(42)
        result = convert_to_native(value)
        self.assertIsInstance(result, int)
        self.assertEqual(result, 42)
    
    def test_numpy_int32_to_int(self):
        """numpy.int32 should convert to Python int"""
        value = np.int32(42)
        result = convert_to_native(value)
        self.assertIsInstance(result, int)
        self.assertEqual(result, 42)
    
    def test_numpy_int16_to_int(self):
        """numpy.int16 should convert to Python int"""
        value = np.int16(42)
        result = convert_to_native(value)
        self.assertIsInstance(result, int)
        self.assertEqual(result, 42)
    
    def test_numpy_int8_to_int(self):
        """numpy.int8 should convert to Python int"""
        value = np.int8(42)
        result = convert_to_native(value)
        self.assertIsInstance(result, int)
        self.assertEqual(result, 42)
    
    def test_numpy_uint64_to_int(self):
        """numpy.uint64 should convert to Python int"""
        value = np.uint64(42)
        result = convert_to_native(value)
        self.assertIsInstance(result, int)
        self.assertEqual(result, 42)
    
    def test_numpy_float64_to_float(self):
        """numpy.float64 should convert to Python float"""
        value = np.float64(3.14159)
        result = convert_to_native(value)
        self.assertIsInstance(result, float)
        self.assertAlmostEqual(result, 3.14159, places=5)
    
    def test_numpy_float32_to_float(self):
        """numpy.float32 should convert to Python float"""
        value = np.float32(2.71828)
        result = convert_to_native(value)
        self.assertIsInstance(result, float)
        self.assertAlmostEqual(result, 2.71828, places=4)
    
    def test_numpy_bool_to_bool(self):
        """numpy.bool_ should convert to Python bool"""
        value = np.bool_(True)
        result = convert_to_native(value)
        self.assertIsInstance(result, bool)
        self.assertEqual(result, True)
    
    def test_numpy_str_to_str(self):
        """numpy.str_ should convert to Python str"""
        value = np.str_("test string")
        result = convert_to_native(value)
        self.assertIsInstance(result, str)
        self.assertEqual(result, "test string")
    
    def test_numpy_datetime64_to_datetime(self):
        """numpy.datetime64 with time should convert to Python datetime"""
        value = np.datetime64('2024-01-15 14:30:00')
        result = convert_to_native(value)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)
    
    def test_numpy_datetime64_to_date(self):
        """numpy.datetime64 without time should convert to Python date"""
        value = np.datetime64('2024-01-15')
        result = convert_to_native(value)
        self.assertIsInstance(result, date)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)
    
    def test_pandas_timestamp_to_datetime(self):
        """pandas.Timestamp should convert to Python datetime"""
        value = pd.Timestamp('2024-01-15 14:30:00')
        result = convert_to_native(value)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2024)
    
    def test_native_int_unchanged(self):
        """Python int should remain unchanged"""
        value = 42
        result = convert_to_native(value)
        self.assertIsInstance(result, int)
        self.assertEqual(result, 42)
    
    def test_native_float_unchanged(self):
        """Python float should remain unchanged"""
        value = 3.14
        result = convert_to_native(value)
        self.assertIsInstance(result, float)
        self.assertEqual(result, 3.14)
    
    def test_native_string_unchanged(self):
        """Python string should remain unchanged"""
        value = "hello"
        result = convert_to_native(value)
        self.assertIsInstance(result, str)
        self.assertEqual(result, "hello")
    
    def test_none_unchanged(self):
        """None should remain unchanged"""
        value = None
        result = convert_to_native(value)
        self.assertIsNone(result)
    
    def test_numpy_array_single_element(self):
        """Single-element numpy array should convert to scalar"""
        value = np.array([42])
        result = convert_to_native(value)
        # Should be int now
        self.assertIsInstance(result, (int, np.integer))
    
    def test_numpy_array_multiple_elements(self):
        """Multi-element numpy array should convert to list"""
        value = np.array([1, 2, 3, 4, 5])
        result = convert_to_native(value)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 5)
        # Each element should be converted to native type
        for item in result:
            self.assertIsInstance(item, int)
    
    def test_pandas_series_single_element(self):
        """Single-element pandas Series should convert to scalar"""
        value = pd.Series([42])
        result = convert_to_native(value)
        self.assertIsInstance(result, int)
        self.assertEqual(result, 42)
    
    def test_pandas_series_multiple_elements(self):
        """Multi-element pandas Series should convert to list"""
        value = pd.Series([1, 2, 3, 4, 5])
        result = convert_to_native(value)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 5)


class TestTupleConversion(unittest.TestCase):
    """Test conversion of tuples containing numpy types."""
    
    def test_tuple_with_numpy_int64(self):
        """Tuple with numpy.int64 should convert all elements"""
        params = (np.int64(42), "string", np.float64(3.14))
        result = convert_params_to_native(params)
        self.assertIsInstance(result, tuple)
        self.assertIsInstance(result[0], int)
        self.assertEqual(result[0], 42)
        self.assertIsInstance(result[1], str)
        self.assertIsInstance(result[2], float)
        self.assertAlmostEqual(result[2], 3.14)
    
    def test_tuple_mixed_types(self):
        """Complex tuple with various numpy types"""
        params = (
            np.int64(100),
            np.float64(99.99),
            np.bool_(True),
            "text",
            None,
            np.int32(50)
        )
        result = convert_params_to_native(params)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 6)
        
        # Verify each type
        self.assertIsInstance(result[0], int)
        self.assertIsInstance(result[1], float)
        self.assertIsInstance(result[2], bool)
        self.assertIsInstance(result[3], str)
        self.assertIsNone(result[4])
        self.assertIsInstance(result[5], int)
    
    def test_tuple_all_numpy_types(self):
        """Tuple containing all common numpy integer and float types"""
        params = (
            np.int8(1),
            np.int16(2),
            np.int32(3),
            np.int64(4),
            np.uint8(5),
            np.uint16(6),
            np.uint32(7),
            np.uint64(8),
            np.float16(1.5),
            np.float32(2.5),
            np.float64(3.5),
        )
        result = convert_params_to_native(params)
        self.assertIsInstance(result, tuple)
        
        # All should be converted to int or float
        for i in range(8):  # integers
            self.assertIsInstance(result[i], int, f"Element {i} should be int")
        for i in range(8, 11):  # floats
            self.assertIsInstance(result[i], float, f"Element {i} should be float")
    
    def test_empty_tuple(self):
        """Empty tuple should remain empty"""
        params = ()
        result = convert_params_to_native(params)
        self.assertEqual(result, ())
    
    def test_single_element_tuple(self):
        """Single element tuple should work correctly"""
        params = (np.int64(42),)
        result = convert_params_to_native(params)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], int)


class TestListConversion(unittest.TestCase):
    """Test conversion of lists containing numpy types."""
    
    def test_list_with_numpy_types(self):
        """List with numpy types should convert all elements"""
        params = [np.int64(1), np.int64(2), np.int64(3)]
        result = convert_params_to_native(params)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        for item in result:
            self.assertIsInstance(item, int)
    
    def test_nested_list(self):
        """Nested lists should be converted recursively"""
        params = [[np.int64(1), np.int64(2)], [np.int64(3), np.int64(4)]]
        result = convert_params_to_native(params)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        for sublist in result:
            self.assertIsInstance(sublist, list)
            for item in sublist:
                self.assertIsInstance(item, int)


class TestDictConversion(unittest.TestCase):
    """Test conversion of dictionaries containing numpy types."""
    
    def test_dict_with_numpy_values(self):
        """Dict with numpy values should convert all values"""
        params = {
            'id': np.int64(42),
            'price': np.float64(99.99),
            'count': np.int32(100),
            'active': np.bool_(True)
        }
        result = convert_params_to_native(params)
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result['id'], int)
        self.assertIsInstance(result['price'], float)
        self.assertIsInstance(result['count'], int)
        self.assertIsInstance(result['active'], bool)
    
    def test_nested_dict(self):
        """Nested dicts should be converted recursively"""
        params = {
            'user': {
                'id': np.int64(1),
                'age': np.int32(25)
            },
            'score': np.float64(95.5)
        }
        result = convert_params_to_native(params)
        self.assertIsInstance(result['user']['id'], int)
        self.assertIsInstance(result['user']['age'], int)
        self.assertIsInstance(result['score'], float)


class TestDeepConvert(unittest.TestCase):
    """Test the deep_convert function for complex nested structures."""
    
    def test_deeply_nested_structure(self):
        """Complex nested structure with numpy types at multiple levels"""
        data = {
            'booking_id': np.int64(12345),
            'room': {
                'id': np.int32(10),
                'capacity': np.int64(50),
                'price': np.float64(250.00)
            },
            'attendees': [
                {'id': np.int64(1), 'name': 'Alice'},
                {'id': np.int64(2), 'name': 'Bob'}
            ],
            'dates': {
                'start': pd.Timestamp('2024-01-15'),
                'end': np.datetime64('2024-01-16')  # No time component, becomes date
            },
            'counts': np.array([np.int64(5), np.int64(10)])
        }
        
        result = deep_convert(data)
        
        # Check top-level
        self.assertIsInstance(result['booking_id'], int)
        # Check nested dict
        self.assertIsInstance(result['room']['id'], int)
        self.assertIsInstance(result['room']['capacity'], int)
        self.assertIsInstance(result['room']['price'], float)
        # Check list of dicts
        for attendee in result['attendees']:
            self.assertIsInstance(attendee['id'], int)
        # Check dates
        self.assertIsInstance(result['dates']['start'], datetime)
        # numpy datetime64 without time becomes date
        self.assertIsInstance(result['dates']['end'], date)
        # Check array converted to list
        self.assertIsInstance(result['counts'], list)
        for count in result['counts']:
            self.assertIsInstance(count, int)


class TestValidation(unittest.TestCase):
    """Test the validation function."""
    
    def test_validate_clean_params(self):
        """Validation should pass for clean (native) params"""
        params = (42, "string", 3.14, True, None)
        is_valid, error = validate_native_types(params)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_numpy_params(self):
        """Validation should fail for params with numpy types"""
        params = (np.int64(42), "string")
        is_valid, error = validate_native_types(params)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("numpy", error.lower())
    
    def test_validate_none_params(self):
        """Validation should pass for None params"""
        is_valid, error = validate_native_types(None)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_after_conversion(self):
        """Validation should pass after conversion"""
        params = (np.int64(42), np.float64(3.14))
        clean_params = convert_params_to_native(params)
        is_valid, error = validate_native_types(clean_params)
        self.assertTrue(is_valid)
        self.assertIsNone(error)


class TestIsNumpyType(unittest.TestCase):
    """Test the is_numpy_type helper function."""
    
    def test_numpy_scalar_is_numpy_type(self):
        """numpy scalar types should return True"""
        self.assertTrue(is_numpy_type(np.int64(42)))
        self.assertTrue(is_numpy_type(np.float64(3.14)))
        self.assertTrue(is_numpy_type(np.bool_(True)))
    
    def test_numpy_array_is_numpy_type(self):
        """numpy arrays should return True"""
        # All numpy arrays are considered numpy types
        self.assertTrue(is_numpy_type(np.array([1, 2, 3])))
        self.assertTrue(is_numpy_type(np.array(42)))  # 0-d array
    
    def test_native_types_are_not_numpy(self):
        """Python native types should return False"""
        self.assertFalse(is_numpy_type(42))
        self.assertFalse(is_numpy_type(3.14))
        self.assertFalse(is_numpy_type(True))
        self.assertFalse(is_numpy_type("string"))
        self.assertFalse(is_numpy_type(None))
    
    def test_pandas_types_are_not_numpy(self):
        """pandas types should be considered as numpy (for our purposes)"""
        # Actually pandas Timestamp is not np.generic, so this tests current behavior
        self.assertFalse(is_numpy_type(pd.Timestamp('2024-01-15')))


class TestPrepareForDB(unittest.TestCase):
    """Test the prepare_for_db alias function."""
    
    def test_prepare_for_db_tuple(self):
        """prepare_for_db should work the same as convert_params_to_native"""
        params = (np.int64(42), np.float64(3.14), "string")
        result = prepare_for_db(params)
        self.assertIsInstance(result, tuple)
        self.assertIsInstance(result[0], int)
        self.assertIsInstance(result[1], float)
        self.assertEqual(result[2], "string")
    
    def test_prepare_for_db_dict(self):
        """prepare_for_db should work with dicts"""
        params = {'id': np.int64(42), 'name': 'test'}
        result = prepare_for_db(params)
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result['id'], int)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and potential issues."""
    
    def test_very_large_int64(self):
        """Very large int64 values should convert correctly"""
        value = np.int64(9223372036854775807)  # Max int64
        result = convert_to_native(value)
        self.assertIsInstance(result, int)
        self.assertEqual(result, 9223372036854775807)
    
    def test_negative_int64(self):
        """Negative int64 values should convert correctly"""
        value = np.int64(-1000)
        result = convert_to_native(value)
        self.assertIsInstance(result, int)
        self.assertEqual(result, -1000)
    
    def test_zero_values(self):
        """Zero values should convert correctly"""
        int_zero = convert_to_native(np.int64(0))
        float_zero = convert_to_native(np.float64(0.0))
        self.assertEqual(int_zero, 0)
        self.assertEqual(float_zero, 0.0)
    
    def test_special_float_values(self):
        """Special float values like inf and nan"""
        inf_val = convert_to_native(np.float64(np.inf))
        nan_val = convert_to_native(np.float64(np.nan))
        self.assertEqual(inf_val, float('inf'))
        self.assertTrue(isinstance(nan_val, float) and pd.isna(nan_val))
    
    def test_empty_dict(self):
        """Empty dict should remain empty"""
        result = convert_params_to_native({})
        self.assertEqual(result, {})
    
    def test_empty_list(self):
        """Empty list should remain empty"""
        result = convert_params_to_native([])
        self.assertEqual(result, [])


class TestPandasDataFrameIntegration(unittest.TestCase):
    """Test integration with pandas DataFrames."""
    
    def test_dataframe_to_dict_conversion(self):
        """DataFrame should convert to list of dicts"""
        df = pd.DataFrame({
            'id': [np.int64(1), np.int64(2), np.int64(3)],
            'value': [np.float64(1.5), np.float64(2.5), np.float64(3.5)]
        })
        result = convert_to_native(df)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        for item in result:
            self.assertIsInstance(item, dict)
            self.assertIsInstance(item['id'], int)
            self.assertIsInstance(item['value'], float)
    
    def test_dataframe_single_value_from_cell(self):
        """DataFrame cell values should convert correctly"""
        df = pd.DataFrame({
            'id': [np.int64(42)],
            'name': ['test']
        })
        # Get single value from DataFrame
        value = df['id'].iloc[0]
        result = convert_to_native(value)
        self.assertIsInstance(result, int)
        self.assertEqual(result, 42)


class TestRealWorldScenarios(unittest.TestCase):
    """Test scenarios that mirror real-world usage in the application."""
    
    def test_room_booking_params(self):
        """Simulate room booking database params"""
        # This mimics what might happen when processing a booking form
        params = (
            np.int64(1),  # room_id from pandas DataFrame
            "2024-01-15 09:00:00",  # start time
            "2024-01-15 17:00:00",  # end time
            "Training Session",  # purpose
            np.int64(25),  # num_learners
            np.int64(2),   # num_facilitators
            np.float64(250.00),  # price
            True,  # coffee_tea_station
            np.bool_(True),  # stationery_needed
        )
        
        result = convert_params_to_native(params)
        
        # Verify all types are now native
        self.assertIsInstance(result[0], int)
        self.assertIsInstance(result[4], int)
        self.assertIsInstance(result[5], int)
        self.assertIsInstance(result[6], float)
        self.assertIsInstance(result[7], bool)
        self.assertIsInstance(result[8], bool)
    
    def test_device_assignment_params(self):
        """Simulate device assignment database params"""
        params = {
            'booking_id': np.int64(12345),
            'device_id': np.int64(67890),
            'category_id': np.int32(1),
            'quantity': np.int64(5),
            'is_offsite': np.bool_(False),
            'assigned_by': 'admin_user',
            'notes': None
        }
        
        result = convert_params_to_native(params)
        
        self.assertIsInstance(result['booking_id'], int)
        self.assertIsInstance(result['device_id'], int)
        self.assertIsInstance(result['category_id'], int)
        self.assertIsInstance(result['quantity'], int)
        self.assertIsInstance(result['is_offsite'], bool)
        self.assertIsNone(result['notes'])
    
    def test_pricing_update_params(self):
        """Simulate pricing update database params"""
        params = (
            np.int64(42),  # pricing_id
            np.float64(299.99),  # daily_rate
            np.float64(1499.99),  # weekly_rate
            None,  # monthly_rate (not updating)
            "Updated pricing for 2024",  # notes
        )
        
        result = convert_params_to_native(params)
        
        self.assertIsInstance(result[0], int)
        self.assertIsInstance(result[1], float)
        self.assertIsInstance(result[2], float)
        self.assertIsNone(result[3])
        self.assertIsInstance(result[4], str)


if __name__ == '__main__':
    unittest.main(verbosity=2)
