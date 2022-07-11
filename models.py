from mongoengine import Document
from mongoengine.fields import ListField, StringField, SequenceField, EmbeddedDocumentField, EmbeddedDocument


class Email(EmbeddedDocument):
    value = StringField(default='')


class Birthday(EmbeddedDocument):
    value = StringField(default='')


class Phone(EmbeddedDocument):
    value = StringField(default='')


class Contact(Document):
    id = SequenceField(primary_key=True)
    name = StringField(required=True)
    address = StringField(required=False)
    email = EmbeddedDocumentField(Email)
    birthday = EmbeddedDocumentField(Birthday)
    phones = ListField(EmbeddedDocumentField(Phone))