# -*- coding: utf-8 -*-
from django.db.models.fields import BooleanField


class YesNoBooleanField(BooleanField):
    
    def to_python(self, value):
        if isinstance(value, str):
            if value.lower() == "yes":
                return True
            if value.lower() == "no":
                return False
        return super(YesNoBooleanField, self).to_python(value)

