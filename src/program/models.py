from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models
from django.utils.text import slugify
from django.conf import settings
from utils.models import CreatedUpdatedModel
from django.core.exceptions import ValidationError
from datetime import timedelta


class EventLocation(CreatedUpdatedModel):
    """ The places where stuff happens """
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    icon = models.CharField(max_length=100)
    camp = models.ForeignKey('camps.Camp', null=True, related_name="eventlocations")

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (('camp', 'slug'), ('camp', 'name'))


class EventType(CreatedUpdatedModel):
    """ Every event needs to have a type. """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField()
    color = models.CharField(max_length=50)
    light_text = models.BooleanField(default=False)
    notifications = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Event(CreatedUpdatedModel):
    """ Something that is on the program one or more times. """
    title = models.CharField(max_length=255)
    slug = models.SlugField(blank=True, max_length=255)
    abstract = models.TextField()
    event_type = models.ForeignKey(EventType)
    camp = models.ForeignKey('camps.Camp', null=True, related_name="events")

    class Meta:
        ordering = ['title']
        unique_together = (('camp', 'slug'), ('camp', 'title'))

    def __str__(self):
        return '%s (%s)' % (self.title, self.camp.title)

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Event, self).save(**kwargs)

    @property
    def speakers_list(self):
        if self.speakers.exists():
            return ", ".join(self.speakers.all().values_list('name', flat=True))
        return False


class EventInstance(CreatedUpdatedModel):
    """ An instance of an event """
    event = models.ForeignKey('program.event', related_name='instances')
    when = DateTimeRangeField()
    notifications_sent = models.BooleanField(default=False)
    location = models.ForeignKey('program.EventLocation', related_name='eventinstances')

    class Meta:
        ordering = ['when']

    def __str__(self):
        return '%s (%s)' % (self.event, self.when)

    def __clean__(self):
        errors = []
        if self.location.camp != self.event.camp:
            errors.append(ValidationError({'location', "Error: This location belongs to a different camp"}))

        if errors:
            raise ValidationError(errors)

    @property
    def schedule_date(self):
        """
            Returns the schedule date of this eventinstance. Schedule date is determined by substracting
            settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS from the eventinstance start time. This means that if
            an event is scheduled for 00:30 wednesday evening (technically thursday) then the date
            after substracting 5 hours would be wednesdays date, not thursdays
            (given settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS=5)
        """
        return (self.when.lower-timedelta(hours=settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS)).date()

    @property
    def timeslots(self):
        """
            Find the number of timeslots this eventinstance takes up
        """
        seconds = (self.when.upper-self.when.lower).seconds
        minutes = seconds / 60
        return minutes / settings.SCHEDULE_TIMESLOT_LENGTH_MINUTES


def get_speaker_picture_upload_path(instance, filename):
    """ We want speaker pictures are saved as MEDIA_ROOT/public/speakers/camp-slug/speaker-slug/filename """
    return 'public/speakers/%(campslug)s/%(speakerslug)s/%(filename)s' % {
        'campslug': instance.camp.slug,
        'speakerslug': instance.slug,
        'filename': filename
    }


class Speaker(CreatedUpdatedModel):
    """ A Person anchoring an event. """
    name = models.CharField(max_length=150)
    biography = models.TextField()
    picture_small = models.ImageField(null=True, blank=True, upload_to=get_speaker_picture_upload_path)
    picture_large = models.ImageField(null=True, blank=True, upload_to=get_speaker_picture_upload_path)
    slug = models.SlugField(blank=True, max_length=255)
    camp = models.ForeignKey('camps.Camp', null=True, related_name="speakers")
    events = models.ManyToManyField(
        Event,
        blank=True,
    )

    class Meta:
        ordering = ['name']
        unique_together = (('camp', 'name'), ('camp', 'slug'))

    def __str__(self):
        return '%s (%s)' % (self.name, self.camp)

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Speaker, self).save(**kwargs)

