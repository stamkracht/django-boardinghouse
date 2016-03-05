from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _

from boardinghouse.models import AbstractSchema


class School(AbstractSchema):
    pass
    # users = models.ManyToManyField(settings.AUTH_USER_MODEL,
    #     blank=True, related_name='schemata',
    #     help_text=_(u'Which users may access data from this schema.')
    # )


class StaffMember(models.Model):
    name = models.CharField(max_length=64)
    staff_id = models.CharField(unique=True, max_length=16)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.staff_id)


class Student(models.Model):
    name = models.CharField(max_length=64)
    student_id = models.CharField(unique=True, max_length=16)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.student_id)


class Subject(models.Model):
    name = models.CharField(unique=True, max_length=64)

    def __unicode__(self):
        return self.name

SEMESTERS = (
    (0, 'Summer Semester'),
    (1, 'Semester 1'),
    (2, 'Semester 2'),
)

GRADES = (
    ('HD', 'High Distinction'),
    ('D', 'Distinction'),
    ('C', 'Credit'),
    ('P1', 'Pass, Level 1'),
    ('P2', 'Pass, Level 2'),
    ('F1', 'Fail, Level 1'),
    ('F2', 'Fail, Level 2'),
    ('NGP', 'Non-Graded Pass'),
    ('NGF', 'Non-Graded Fail'),
)


class Enrolment(models.Model):
    student = models.ForeignKey(Student, related_name='enrolments')
    subject = models.ForeignKey(Subject, related_name='enrolments')
    enrolment_date = models.DateField()
    year = models.IntegerField()
    semester = models.IntegerField(choices=SEMESTERS)
    grade = models.CharField(choices=GRADES, max_length=3, null=True, blank=True)

    def __unicode__(self):
        if self.grade:
            return u'%s studied %s in %s %s. Grade was %s' % (
                self.student.name,
                self.subject.name,
                self.get_semester_display(),
                self.year,
                self.get_grade_display()
            )
        return u'%s enrolled in %s in %s %s.' % (
            self.student.name,
            self.subject.name,
            self.get_semester_display(),
            self.year,
        )