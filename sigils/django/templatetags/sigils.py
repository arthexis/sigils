# {% resolve sigil %} for Django, based on:
# https://docs.djangoproject.com/en/2.2/howto/custom-template-tags/

from __future__ import absolute_import

# noinspection PyUnresolvedReferences
from django import template
import sigils

register = template.Library()


@register.simple_tag
def resolve(text, **kwargs):
    return sigils.resolve(text, kwargs)
