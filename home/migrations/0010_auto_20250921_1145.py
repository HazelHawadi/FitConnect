from django.db import migrations
import uuid

def populate_unique_tokens(apps, schema_editor):
    NewsletterSubscriber = apps.get_model('home', 'NewsletterSubscriber')
    for subscriber in NewsletterSubscriber.objects.all():
        subscriber.unsubscribe_token = uuid.uuid4()
        subscriber.save()

class Migration(migrations.Migration):

    dependencies = [
        ('home', '0007_newslettersubscriber_unsubscribe_token'),
    ]

    operations = [
        migrations.RunPython(populate_unique_tokens),
    ]
