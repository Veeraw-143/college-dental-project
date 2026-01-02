#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Newpro.settings')
django.setup()

from project.models import bookings
from datetime import date, time

# Create test bookings
test_date = date(2025, 1, 15)
test_time = time(10, 0)

# Clear existing test data
bookings.objects.filter(appointment_date=test_date).delete()

# Create a booking at 10:00
b1 = bookings.objects.create(
    Name='Test User 1',
    mail='test1@example.com',
    mobile='+919876543210',
    appointment_date=test_date,
    time=test_time,
    status=bookings.STATUS_ACCEPTED
)
print(f"Created booking 1 at {b1.get_time_12hr()}")

# Test 1: Try to book at 10:15 (should fail - within 30 min buffer)
b_test = bookings(
    Name='Test User 2',
    mail='test2@example.com',
    mobile='+919876543211',
    appointment_date=test_date,
    time=time(10, 15)
)
available = b_test.is_time_available(test_date, time(10, 15))
print(f"10:15 AM available? {available} (expected: False)")

# Test 2: Try to book at 10:30 (should fail - exactly 30 min before)
available = b_test.is_time_available(test_date, time(10, 30))
print(f"10:30 AM available? {available} (expected: False)")

# Test 3: Try to book at 10:31 (should pass - after 30 min buffer)
available = b_test.is_time_available(test_date, time(10, 31))
print(f"10:31 AM available? {available} (expected: True)")

# Test 4: Try to book at 9:30 (should fail - within 30 min before)
available = b_test.is_time_available(test_date, time(9, 30))
print(f"9:30 AM available? {available} (expected: False)")

# Test 5: Try to book at 9:29 (should pass - before 30 min buffer)
available = b_test.is_time_available(test_date, time(9, 29))
print(f"9:29 AM available? {available} (expected: True)")

print("\nAll tests completed!")
