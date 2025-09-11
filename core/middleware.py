from django.shortcuts import redirect
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone

class AutoLogoutMiddleware(MiddlewareMixin):
    INACTIVITY_TIMEOUT = 30 * 60  # 30 minutes in seconds

    def process_request(self, request):
        if not request.user.is_authenticated:
            return

        current_datetime = timezone.now()
        last_activity = request.session.get('last_activity')

        if last_activity:
            try:
                last_activity_time = timezone.datetime.fromisoformat(last_activity)
                last_activity_time = timezone.make_aware(last_activity_time, timezone.get_current_timezone())
            except ValueError:
                last_activity_time = current_datetime

            elapsed = (current_datetime - last_activity_time).total_seconds()
            if elapsed > self.INACTIVITY_TIMEOUT:
                from django.contrib.auth import logout
                logout(request)
                messages.info(request, "You have been logged out due to inactivity.")
                return redirect('login')

        request.session['last_activity'] = current_datetime.isoformat()
