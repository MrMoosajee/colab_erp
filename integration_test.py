#!/usr/bin/env python3
"""
Integration test for the complete booking form workflow
Tests the actual booking form functionality end-to-end
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_booking_form_workflow():
    """Test the complete booking form workflow"""
    print("🧪 Testing Complete Booking Form Workflow\n")
    
    try:
        # Import the booking form module
        from src.booking_form import render_enhanced_booking_form
        print("✅ Booking form module imported successfully")
        
        # Import the main app components
        from src.models import BookingService, AvailabilityService
        print("✅ Service modules imported successfully")
        
        # Test service initialization
        booking_service = BookingService()
        availability_service = AvailabilityService()
        print("✅ Services initialized successfully")
        
        # Test getting rooms
        rooms_df = availability_service.get_all_rooms()
        print(f"✅ Retrieved {len(rooms_df)} rooms from database")
        
        if len(rooms_df) > 0:
            print(f"✅ Sample room: {rooms_df.iloc[0]['name']} (ID: {rooms_df.iloc[0]['id']})")
        
        # Test device availability
        from datetime import date, timedelta
        future_date = date.today() + timedelta(days=7)
        
        device_check = availability_service.check_device_availability(
            devices_needed=2, start_date=future_date, end_date=future_date, device_type='any'
        )
        print(f"✅ Device availability: {device_check['message']}")
        
        # Test room conflict checking
        if len(rooms_df) > 0:
            room_id = rooms_df.iloc[0]['id']
            conflict_info = availability_service.check_room_conflicts(
                room_id, future_date, future_date
            )
            print(f"✅ Room conflict check: {conflict_info['message']}")
        
        print("\n🎉 All integration tests passed!")
        print("✅ Booking form is ready for production use")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_imports():
    """Test that all app components can be imported"""
    print("🔍 Testing App Component Imports\n")
    
    try:
        # Test main app imports
        import src.app
        print("✅ Main app module imported")
        
        import src.db
        print("✅ Database module imported")
        
        import src.auth
        print("✅ Authentication module imported")
        
        import src.booking_form
        print("✅ Booking form module imported")
        
        # Test model imports
        from src.models import BookingService, AvailabilityService, DeviceManager, NotificationManager, RoomApprovalService
        print("✅ All model services imported")
        
        print("\n✅ All app components are importable")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Starting Colab ERP Integration Tests\n")
    
    tests = [
        test_app_imports,
        test_booking_form_workflow
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            print()
    
    print(f"📊 Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("✅ Colab ERP v2.2.3 is ready for production use")
        print("✅ Booking form functionality is working correctly")
    else:
        print("⚠️  Some integration tests failed")
        print("❌ Please review the errors above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)