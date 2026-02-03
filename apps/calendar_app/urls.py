from django.urls import path
from .views import (
    CalendarEventListView,
    CalendarEventDetailView,
    EventRegisterView,
    EventUnregisterView,
    EventAttendeesListView,
    EventMarkAttendedView,
    EventFeedbackView,
)

urlpatterns = [
    # Calendar Events endpoints
    path('events/', CalendarEventListView.as_view(), name='event-list'),
    path('events/<uuid:event_id>/', CalendarEventDetailView.as_view(), name='event-detail'),
    
    # Event Attendee endpoints
    path('events/<uuid:event_id>/register/', EventRegisterView.as_view(), name='event-register'),
    path('events/<uuid:event_id>/unregister/', EventUnregisterView.as_view(), name='event-unregister'),
    path('events/<uuid:event_id>/attendees/', EventAttendeesListView.as_view(), name='event-attendees'),
    path('events/<uuid:event_id>/mark-attended/', EventMarkAttendedView.as_view(), name='event-mark-attended'),
    path('events/<uuid:event_id>/feedback/', EventFeedbackView.as_view(), name='event-feedback'),
]
