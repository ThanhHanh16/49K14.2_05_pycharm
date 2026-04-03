from django.core.management.base import BaseCommand
from user.models import Customer, Court, CourtSlot, Booking
from datetime import date, datetime


class Command(BaseCommand):
    help = 'Populate sample data for testing'

    def handle(self, *args, **options):
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

        # Create sample courts
        courts = []
        for i in range(1, 4):
            court, created = Court.objects.get_or_create(
                court_name=f'Sân {i}',
                defaults={'description': f'Sân bóng chuyền số {i}'}
            )
            courts.append(court)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created court: {court.court_name}'))

        # Create court slots for each court
        times = ['07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00']

        for court in courts:
            for time_slot in times:
                slot, created = CourtSlot.objects.get_or_create(
                    court=court,
                    time=time_slot
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created slot: {court.court_name} - {time_slot}'))

        # Create sample bookings
        for i, customer in enumerate(customers):
            court = courts[i % len(courts)]
            slots = court.slots.all()[:2]

            for j, slot in enumerate(slots):
                booking, created = Booking.objects.get_or_create(
                    customer=customer,
                    court_slot=slot,
                    booking_date=date.today(),
                    defaults={'status': 'confirmed'}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'Created booking: {customer.full_name} - {slot.court.court_name} - {slot.time}'
                    ))

        self.stdout.write(self.style.SUCCESS('Sample data populated successfully!'))

