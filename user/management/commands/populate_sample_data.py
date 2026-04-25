from django.core.management.base import BaseCommand
from user.models import CourtType, Court, PriceTable, PriceTableTimeSlot, Customer, Booking
from datetime import date, time, timedelta

class Command(BaseCommand):
    help = 'Populate sample data for testing court booking system'

    def handle(self, *args, **options):
        # 1. Create court types
        types_data = [
            {'code': 'CT001', 'name': 'San bong chuyen'},
            {'code': 'CT002', 'name': 'San bong da'},
        ]
        
        court_types = {}
        for td in types_data:
            ct, created = CourtType.objects.get_or_create(
                code=td['code'],
                defaults={'name': td['name'], 'status': 'ACTIVE'}
            )
            court_types[td['code']] = ct
            if created:
                self.stdout.write(f'Created court type: {td["code"]}')

        # 2. Create courts for each type
        for code, ct in court_types.items():
            for i in range(1, 4):
                court_code = f"{code}-S{i:02d}"
                court, created = Court.objects.get_or_create(
                    code=court_code,
                    defaults={
                        'name': f'{ct.name} - San {i}',
                        'court_type': ct,
                        'area': f'Khu {code[-1]}',
                        'status': 'READY'
                    }
                )
                if created:
                    self.stdout.write(f'Created court: {court_code}')

        # 3. Create price tables and slots for each type
        days = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
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
            {'start': '17:00', 'end': '18:00', 'price': 130000},
            {'start': '18:00', 'end': '19:00', 'price': 150000},
            {'start': '19:00', 'end': '20:00', 'price': 150000},
            {'start': '20:00', 'end': '21:00', 'price': 130000},
        ]

        for code, ct in court_types.items():
            pt_code = f"BG-{code}"
            price_table, created = PriceTable.objects.get_or_create(
                price_table_code=pt_code,
                defaults={
                    'price_table_name': f'Bang gia {code} tong hop',
                    'court_type': ct,
                    'apply_scope': 'ALL',
                    'effective_date': date.today() - timedelta(days=30),
                    'applied_days': days
                }
            )
            if created:
                self.stdout.write(f'Created price table: {pt_code}')

            for i, slot_data in enumerate(time_slots_data, 1):
                PriceTableTimeSlot.objects.get_or_create(
                    price_table=price_table,
                    start_time=time.fromisoformat(slot_data['start']),
                    end_time=time.fromisoformat(slot_data['end']),
                    defaults={
                        'unit_price': slot_data['price'] if code == 'CT001' else slot_data['price'] + 50000,
                        'order': i
                    }
                )

        # 4. Create sample customers
        for i in range(1, 4):
            Customer.objects.get_or_create(
                phone_number=f'091234567{i}',
                defaults={
                    'full_name': f'Khach hang {i}',
                    'email': f'user{i}@example.com'
                }
            )

        self.stdout.write('Sample data populated successfully!')
