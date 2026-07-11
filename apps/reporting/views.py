from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from apps.extraction.models import Screenshot
import calendar
from datetime import date, datetime

class CalendarStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year_str = request.query_params.get('year')
        month_str = request.query_params.get('month')
        
        now = timezone.localtime(timezone.now()).date()
        
        if not year_str or not month_str:
            year = now.year
            month = now.month
        else:
            try:
                year = int(year_str)
                month = int(month_str)
            except ValueError:
                return Response({"error": "Invalid year or month format"}, status=400)
                
        # Find first active month
        first_screenshot = Screenshot.objects.filter(user=request.user).order_by('uploaded_at').first()
        if first_screenshot:
            first_date = timezone.localtime(first_screenshot.uploaded_at).date()
            first_active_month = f"{first_date.year}-{first_date.month:02d}"
        else:
            # If no activity ever, the first active month is current month
            first_active_month = f"{now.year}-{now.month:02d}"
            
        # Get all days in the requested month
        try:
            num_days = calendar.monthrange(year, month)[1]
        except calendar.IllegalMonthError:
            return Response({"error": "Invalid month"}, status=400)
            
        # Get active dates in this month for the user
        active_dates_qs = Screenshot.objects.filter(
            user=request.user,
            uploaded_at__year=year,
            uploaded_at__month=month
        ).values_list('uploaded_at', flat=True)
        
        active_date_strings = set([
            timezone.localtime(dt).date().isoformat() for dt in active_dates_qs
        ])
        
        days_status = []
        for day in range(1, num_days + 1):
            current_date = date(year, month, day)
            date_str = current_date.isoformat()
            
            if current_date > now:
                status = "future"
            elif current_date == now:
                status = "today"
            else:
                if date_str in active_date_strings:
                    status = "completed"
                else:
                    status = "no_activity"
                    
            days_status.append({
                "date": date_str,
                "status": status,
                "day_of_week": current_date.weekday() # 0 = Monday, 6 = Sunday
            })
            
        return Response({
            "first_active_month": first_active_month,
            "year": year,
            "month": month,
            "days": days_status
        })
