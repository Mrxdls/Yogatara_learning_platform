from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import CalendarEvent, EventAttendee
from .serializers import (
    CalendarEventListSerializer,
    CalendarEventDetailSerializer,
    CalendarEventCreateUpdateSerializer,
    EventAttendeeSerializer,
    EventAttendeeCreateSerializer,
)


class BaseQueryParamsView(APIView):
    """Base class for extracting query parameters from request"""
    
    # Define filter parameters: (param_name, param_type)
    FILTER_PARAMS = []
    
    def get_query_param(self, key, default=None, param_type=str):
        """Extract and convert query parameter safely"""
        value = self.request.query_params.get(key, default)
        if value and param_type == bool and isinstance(value, str):
            return value.lower() in ['true', '1', 'yes']
        return value
    
    def extract_filters(self):
        """Automatically extract filters from defined FILTER_PARAMS"""
        return {
            key: self.get_query_param(key, param_type=param_type)
            for key, param_type in self.FILTER_PARAMS
        }
    
    def apply_filters(self, queryset, **filters):
        """Apply multiple filters to queryset dynamically"""
        for key, value in filters.items():
            if value is not None:
                if key == 'upcoming':
                    queryset = queryset.filter(start_time__gt=timezone.now())
                elif key == 'past':
                    queryset = queryset.filter(end_time__lt=timezone.now())
                elif key == 'start_date':
                    queryset = queryset.filter(start_time__gte=value)
                elif key == 'end_date':
                    queryset = queryset.filter(end_time__lte=value)
                elif key == 'my_events':
                    queryset = queryset.filter(attendees__user=self.request.user)
                elif key == 'my_created':
                    queryset = queryset.filter(instructor=self.request.user)
                else:
                    # Direct field mapping (status, event_type, course_id, instructor_id)
                    queryset = queryset.filter(**{key: value})
        return queryset


class CalendarEventListView(BaseQueryParamsView):
    """
    API View for listing and creating calendar events.
    - GET: List all calendar events with filtering options
    - POST: Create a new calendar event
    """
    permission_classes = [IsAuthenticated]
    
    # Define filter parameters: (param_name, param_type)
    FILTER_PARAMS = [
        ('status', str),
        ('event_type', str),
        ('course_id', str),
        ('instructor_id', str),
        ('upcoming', bool),
        ('past', bool),
        ('start_date', str),
        ('end_date', str),
        ('my_events', bool),
        ('my_created', bool),
    ]

    @extend_schema(
        tags=['Calendar Events'],
        description='List all calendar events with filtering options',
        parameters=[
            OpenApiParameter(
                name='status',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description='Filter by status: scheduled, ongoing, completed, cancelled, postponed'
            ),
            OpenApiParameter(
                name='event_type',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description='Filter by event type: class, workshop, webinar, assignment, exam, deadline, holiday, other'
            ),
            OpenApiParameter(
                name='course_id',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.UUID,
                description='Filter by course ID'
            ),
            OpenApiParameter(
                name='instructor_id',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.UUID,
                description='Filter by instructor ID'
            ),
            OpenApiParameter(
                name='upcoming',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
                description='Show only upcoming events'
            ),
            OpenApiParameter(
                name='past',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
                description='Show only past events'
            ),
            OpenApiParameter(
                name='start_date',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.DATETIME,
                description='Filter events starting from this date'
            ),
            OpenApiParameter(
                name='end_date',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.DATETIME,
                description='Filter events ending before this date'
            ),
            OpenApiParameter(
                name='my_events',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
                description='Show only events the user is registered for'
            ),
            OpenApiParameter(
                name='my_created',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
                description='Show only events created by the user'
            ),
        ]
    )
    def get(self, request):
        """List all calendar events with optional filtering"""
        queryset = CalendarEvent.objects.all()
        
        # Extract all filter parameters automatically
        filters = self.extract_filters()
        
        # Apply all filters at once
        queryset = self.apply_filters(queryset, **filters)
        queryset = queryset.order_by('start_time').distinct()
        
        serializer = CalendarEventListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Calendar Events'],
        description='Create a new calendar event',
        request=CalendarEventCreateUpdateSerializer,
        responses={201: CalendarEventDetailSerializer}
    )
    def post(self, request):
        """Create a new calendar event"""
        serializer = CalendarEventCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            event = serializer.save(instructor=request.user, created_by=request.user)
            return Response(
                CalendarEventDetailSerializer(event).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CalendarEventDetailView(APIView):
    """
    API View for retrieving, updating, and deleting a specific calendar event.
    - GET: Retrieve event details
    - PUT/PATCH: Update event
    - DELETE: Delete event
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, event_id):
        """Get event object or raise 404"""
        return get_object_or_404(CalendarEvent, id=event_id)

    @extend_schema(
        tags=['Calendar Events'],
        description='Retrieve a specific calendar event with all details',
        responses={200: CalendarEventDetailSerializer}
    )
    def get(self, request, event_id):
        """Retrieve a specific calendar event"""
        event = self.get_object(event_id)
        serializer = CalendarEventDetailSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Calendar Events'],
        description='Update a calendar event (event creator/admin only)',
        request=CalendarEventCreateUpdateSerializer,
        responses={200: CalendarEventDetailSerializer}
    )
    def put(self, request, event_id):
        """Update a calendar event"""
        event = self.get_object(event_id)
        
        # Check permission
        if event.instructor != request.user and not request.user.is_superuser:
            raise PermissionDenied("You can only update events you created.")
        
        serializer = CalendarEventCreateUpdateSerializer(
            event, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                CalendarEventDetailSerializer(event).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Calendar Events'],
        description='Partially update a calendar event (event creator/admin only)',
        request=CalendarEventCreateUpdateSerializer,
        responses={200: CalendarEventDetailSerializer}
    )
    def patch(self, request, event_id):
        """Partially update a calendar event"""
        event = self.get_object(event_id)
        
        # Check permission
        if event.instructor != request.user and not request.user.is_superuser:
            raise PermissionDenied("You can only update events you created.")
        
        serializer = CalendarEventCreateUpdateSerializer(
            event, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                CalendarEventDetailSerializer(event).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Calendar Events'],
        description='Delete a calendar event (event creator/admin only)',
        responses={204: None}
    )
    def delete(self, request, event_id):
        """Delete a calendar event"""
        event = self.get_object(event_id)
        
        # Check permission
        if event.instructor != request.user and not request.user.is_superuser:
            raise PermissionDenied("You can only delete events you created.")
        
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EventRegisterView(APIView):
    """
    API View for registering a user to an event.
    - POST: Register user for event
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Calendar Events - Attendees'],
        description='Register the current user for an event',
        request=None,
        responses={201: EventAttendeeSerializer}
    )
    def post(self, request, event_id):
        """Register user for a calendar event"""
        event = get_object_or_404(CalendarEvent, id=event_id)
        
        # Check if user is already registered
        attendee = EventAttendee.objects.filter(
            event=event,
            user=request.user
        ).first()
        
        if attendee:
            if attendee.attendance_status == 'cancelled':
                # Allow re-registration if previously cancelled
                attendee.attendance_status = 'registered'
                attendee.save()
                return Response(
                    EventAttendeeSerializer(attendee).data,
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'detail': 'You are already registered for this event.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check capacity
        if event.max_capacity and event.current_attendees >= event.max_capacity:
            # Add to waitlist
            attendee = EventAttendee.objects.create(
                event=event,
                user=request.user,
                attendance_status='waitlisted'
            )
            return Response(
                EventAttendeeSerializer(attendee).data,
                status=status.HTTP_201_CREATED
            )
        
        # Create attendance record
        attendee = EventAttendee.objects.create(
            event=event,
            user=request.user,
            attendance_status='registered'
        )
        event.current_attendees += 1
        event.save()
        
        return Response(
            EventAttendeeSerializer(attendee).data,
            status=status.HTTP_201_CREATED
        )


class EventUnregisterView(APIView):
    """
    API View for unregistering a user from an event.
    - POST: Unregister user from event
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Calendar Events - Attendees'],
        description='Unregister the current user from an event',
        request=None,
        responses={204: None}
    )
    def post(self, request, event_id):
        """Unregister user from a calendar event"""
        event = get_object_or_404(CalendarEvent, id=event_id)
        
        try:
            attendee = EventAttendee.objects.get(
                event=event,
                user=request.user
            )
        except EventAttendee.DoesNotExist:
            return Response(
                {'detail': 'You are not registered for this event.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update status instead of deleting
        if attendee.attendance_status != 'cancelled':
            if attendee.attendance_status in ['registered', 'attended']:
                event.current_attendees = max(0, event.current_attendees - 1)
                event.save()
            attendee.attendance_status = 'cancelled'
            attendee.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class EventAttendeesListView(BaseQueryParamsView):
    """
    API View for listing event attendees.
    - GET: Get list of attendees for an event
    """
    permission_classes = [IsAuthenticated]
    
    # Define filter parameters for attendees
    FILTER_PARAMS = [
        ('status', str),
    ]

    @extend_schema(
        tags=['Calendar Events - Attendees'],
        description='Get list of attendees for an event',
        responses={200: EventAttendeeSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='status',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description='Filter by attendance status: registered, attended, absent, cancelled, waitlisted'
            ),
        ]
    )
    def get(self, request, event_id):
        """Get list of attendees for an event"""
        event = get_object_or_404(CalendarEvent, id=event_id)
        attendees = event.attendees.filter(
            attendance_status__in=['registered', 'attended', 'absent']
        )
        
        # Apply filters automatically
        filters = self.extract_filters()
        if filters['status']:
            attendees = attendees.filter(attendance_status=filters['status'])
        
        serializer = EventAttendeeSerializer(attendees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventMarkAttendedView(APIView):
    """
    API View for marking attendance.
    - POST: Mark a user as attended
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Calendar Events - Attendees'],
        description='Mark a user as attended for an event (event creator/admin only)',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'format': 'uuid'}
                },
                'required': ['user_id']
            }
        },
        responses={200: EventAttendeeSerializer}
    )
    def post(self, request, event_id):
        """Mark a user as attended for an event"""
        event = get_object_or_404(CalendarEvent, id=event_id)
        
        # Check permission
        if event.instructor != request.user and not request.user.is_superuser:
            raise PermissionDenied("Only event creator can mark attendance.")
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'detail': 'user_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            attendee = EventAttendee.objects.get(
                event=event,
                user_id=user_id
            )
        except EventAttendee.DoesNotExist:
            return Response(
                {'detail': 'User is not registered for this event.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        attendee.attendance_status = 'attended'
        attendee.attended_at = timezone.now()
        attendee.save()
        
        return Response(
            EventAttendeeSerializer(attendee).data,
            status=status.HTTP_200_OK
        )


class EventFeedbackView(APIView):
    """
    API View for event feedback.
    - POST: Submit feedback and rating for an event
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Calendar Events - Attendees'],
        description='Submit feedback and rating for an event',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'rating': {'type': 'integer', 'minimum': 1, 'maximum': 5},
                    'feedback': {'type': 'string'}
                }
            }
        },
        responses={200: EventAttendeeSerializer}
    )
    def post(self, request, event_id):
        """Submit feedback and rating for an event"""
        event = get_object_or_404(CalendarEvent, id=event_id)
        
        try:
            attendee = EventAttendee.objects.get(
                event=event,
                user=request.user
            )
        except EventAttendee.DoesNotExist:
            return Response(
                {'detail': 'You are not registered for this event.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if event is completed
        if not event.is_past():
            return Response(
                {'detail': 'You can only submit feedback after event is completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rating = request.data.get('rating')
        feedback_text = request.data.get('feedback', '')
        
        if rating is not None:
            if rating < 1 or rating > 5:
                return Response(
                    {'detail': 'Rating must be between 1 and 5.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            attendee.rating = rating
        
        attendee.feedback = feedback_text
        attendee.save()
        
        return Response(
            EventAttendeeSerializer(attendee).data,
            status=status.HTTP_200_OK
        )
