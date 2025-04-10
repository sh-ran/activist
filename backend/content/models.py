# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Models for the content app.
"""

import os
from typing import Any, Type
from uuid import uuid4

from django.contrib.postgres.fields import ArrayField
from django.core.validators import validate_image_file_extension
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from utils.models import ISO_CHOICES

# MARK: Main Tables


class Discussion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_by = models.ForeignKey("authentication.UserModel", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    deletion_date = models.DateTimeField(blank=True, null=True)
    tags = models.ManyToManyField("content.Tag", blank=True)

    def __str__(self) -> str:
        return str(self.id)


class Faq(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    iso = models.CharField(max_length=3, choices=ISO_CHOICES)
    primary = models.BooleanField(default=False)
    question = models.TextField(max_length=500)
    answer = models.TextField(max_length=500)
    order = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.question


# This is used to set the filename to the UUID of the model, in the Image model.
def set_filename_to_uuid(instance: Any, filename: str) -> str:
    """Generate a new filename using the model's UUID and keep the original extension."""
    ext = os.path.splitext(filename)[1]  # extract file extension
    # Note: Force extension to lowercase.
    new_filename = f"{instance.id}{ext.lower()}"  # use model UUID as filename

    return os.path.join("images/", new_filename)  # store in 'images/' folder


class Image(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    file_object = models.ImageField(
        upload_to=set_filename_to_uuid,
        validators=[validate_image_file_extension],
    )
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.id)


@receiver(post_delete, sender=Image)
def delete_image_file(sender: Type[Image], instance: Image, **kwargs: Any) -> None:
    """
    Delete the file from the filesystem when the Image instance is deleted.
    """
    if instance.file_object:
        instance.file_object.delete(save=False)


class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    lat = models.CharField(max_length=24)
    lon = models.CharField(max_length=24)
    bbox = ArrayField(
        base_field=models.CharField(max_length=24), size=4, blank=True, null=True
    )
    display_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return str(self.id)


class Resource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_by = models.ForeignKey("authentication.UserModel", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=500)
    category = models.CharField(max_length=255, blank=True)
    location = models.OneToOneField(
        "content.Location", on_delete=models.CASCADE, null=False, blank=False
    )
    url = models.URLField(max_length=255)
    is_private = models.BooleanField(default=True)
    terms_checked = models.BooleanField(default=False)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    tags = models.ManyToManyField("content.Tag", blank=True)
    topics = models.ManyToManyField("content.Topic", blank=True)

    def __str__(self) -> str:
        return self.name


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)
    is_custom = models.BooleanField(default=False)
    description = models.TextField(max_length=500)
    creation_date = models.DateTimeField(auto_now_add=True)
    deletion_date = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class SocialLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    link = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.label


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    text = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.id)


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=500)
    last_updated = models.DateTimeField(auto_now=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    deletion_date = models.DateTimeField(blank=True, null=True)
    tag = models.ManyToManyField("content.Tag", blank=True)

    def __str__(self) -> str:
        return self.name


class Topic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    description = models.TextField(max_length=500)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    deprecation_date = models.DateTimeField(blank=True, null=True)

    format = models.ManyToManyField("events.Format", blank=True)

    def __str__(self) -> str:
        return self.name


# MARK: Bridge Tables


class DiscussionEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    discussion = models.ForeignKey(
        "content.Discussion", on_delete=models.CASCADE, related_name="discussion_entry"
    )
    created_by = models.ForeignKey("authentication.UserModel", on_delete=models.CASCADE)
    text = models.CharField(max_length=255, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    deletion_date = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return str(self.id)
