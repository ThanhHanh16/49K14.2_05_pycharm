from django.core.management.base import BaseCommand
from user.models import CourtType, Court, PriceTable, PriceTableTimeSlot, Customer, Booking
from datetime import date, time


class Command(BaseCommand):
    help = 'Populate sample data for testing court booking system'

    def handle(self, *args, **options):
        # Create court types
        court_type1, created = CourtType.objects.get_or_create(
            code='CT001',
            defaults={
                'name': 'Sân bóng chuyền',
                'duration': 60,
                'status': 'ACTIVE'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created court type: {court_type1.name}'))

        court_type2, created = CourtType.objects.get_or_create(
            code='CT002',
            defaults={
                'name': 'Sân bóng đá',
                'duration': 90,
                'status': 'ACTIVE'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created court type: {court_type2.name}'))

        # Create courts
        courts = []
        for i in range(1, 4):
            court, created = Court.objects.get_or_create(
                code=f'S{i:03d}',
                defaults={
                    'name': f'Sân {i}',
                    'court_type': court_type1,
                    'area': f'Khu A{i}',
                    'status': 'READY'
                }
            )
            courts.append(court)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created court: {court.name}'))

        # Create price table
        price_table, created = PriceTable.objects.get_or_create(
            price_table_code='BG001',
            defaults={
                'price_table_name': 'Bảng giá sân bóng chuyền ngày thường',
                'court_type': court_type1,
                'apply_scope': 'ALL',
                'effective_date': date.today(),
                'applied_days': ['T2', 'T3', 'T4', 'T5', 'T6']
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created price table: {price_table.price_table_name}'))

        # Create time slots
        time_slots_data = [
            {'start': '07:00', 'end': '08:00', 'price': 100000},
            {'start': '08:00', 'end': '09:00', 'price': 120000},
            {'start': '09:00', 'end': '10:00', 'price': 120000},
            {'start': '10:00', 'end': '11:00', 'price': 150000},
            {'start': '11:00', 'end': '12:00', 'price': 150000},
            {'start': '13:00', 'end': '14:00', 'price': 150000},
            {'start': '14:00', 'end': '15:00', 'price': 120000},
            {'start': '15:00', 'end': '16:00', 'price': 120000},
            {'start': '16:00', 'end': '17:00', 'price': 100000},
        ]

        for i, slot_data in enumerate(time_slots_data, 1):
            slot, created = PriceTableTimeSlot.objects.get_or_create(
                price_table=price_table,
                start_time=time.fromisoformat(slot_data['start']),
                end_time=time.fromisoformat(slot_data['end']),
                defaults={
                    'unit_price': slot_data['price'],
                    'order': i
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'Created time slot: {slot.start_time} - {slot.end_time} ({slot.unit_price} VND)'
                ))

        # Create sample customers
        customers = []
        for i in range(1, 4):
            customer, created = Customer.objects.get_or_create(
                phone_number=f'090000000{i}',
                defaults={
                    'full_name': f'Khách hàng {i}',
                    'email': f'customer{i}@example.com'
                }
            )
            customers.append(customer)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created customer: {customer.full_name}'))

        # Create sample bookings
        for i, customer in enumerate(customers):
            court = courts[i % len(courts)]
            # Book first 2 slots for each customer
            slots = PriceTableTimeSlot.objects.filter(price_table=price_table)[:2]

            for slot in slots:
                booking, created = Booking.objects.get_or_create(
                    court=court,
                    date=date.today(),
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    defaults={
                        'customer_name': customer.full_name,
                        'phone': customer.phone_number,
                        'total_price': slot.unit_price,
                        'status': 'confirmed'
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'Created booking: {customer.full_name} - {court.name} - {slot.start_time}-{slot.end_time}'
                    ))

        self.stdout.write(self.style.SUCCESS('Sample data populated successfully!'))
        self.stdout.write(self.style.SUCCESS('You can now test the API at:'))
        self.stdout.write(self.style.SUCCESS('GET /api/courts/schedule/?date=2026-04-03&court_type_id=1'))
        self.stdout.write(self.style.SUCCESS('POST /api/bookings/create_booking/'))
