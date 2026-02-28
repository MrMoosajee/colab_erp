def get_calendar_grid(start_date, end_date):
    """
    Fetches bookings for calendar grid view with full details.
    Returns bookings expanded across all days in their date range.
    
    Args:
        start_date: Start of date range (datetime.date)
        end_date: End of date range (datetime.date)
    
    Returns:
        DataFrame with columns:
        - room_id, room_name, booking_date, booking_id
        - client_name, num_learners, num_facilitators, headcount
        - coffee_tea_station, morning_catering, lunch_catering, stationery_needed
        - devices_needed, device_count, status, tenant_id
    """
    sql = """
        WITH date_range AS (
            SELECT generate_series(%s::date, %s::date, '1 day'::interval)::date AS booking_date
        ),
        expanded_bookings AS (
            SELECT 
                r.id as room_id,
                r.name as room_name,
                dr.booking_date,
                b.id as booking_id,
                b.client_name,
                b.num_learners,
                b.num_facilitators,
                b.headcount,
                b.coffee_tea_station,
                b.morning_catering,
                b.lunch_catering,
                b.stationery_needed,
                b.devices_needed,
                b.status,
                b.tenant_id,
                COUNT(bda.device_id) as device_count
            FROM date_range dr
            CROSS JOIN rooms r
            LEFT JOIN bookings b ON b.room_id = r.id 
                AND dr.booking_date BETWEEN DATE(lower(b.booking_period)) AND DATE(upper(b.booking_period))
                AND b.status != 'Cancelled'
            LEFT JOIN booking_device_assignments bda ON b.id = bda.booking_id
            WHERE r.is_active = true
            GROUP BY r.id, r.name, dr.booking_date, b.id, b.client_name, 
                     b.num_learners, b.num_facilitators, b.headcount,
                     b.coffee_tea_station, b.morning_catering, b.lunch_catering, 
                     b.stationery_needed, b.devices_needed, b.status, b.tenant_id
        )
        SELECT * FROM expanded_bookings
        ORDER BY room_name, booking_date;
    """
    df = run_query(sql, (start_date, end_date))
    
    return df
